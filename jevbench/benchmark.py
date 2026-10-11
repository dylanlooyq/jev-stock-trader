"""Run the walk-forward benchmark and compute every metric from saved predictions."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from . import BUY
from .backtest import open_to_open_returns, run_backtest, trading_stats
from .data import lock_holdout
from .dataset import build_dataset
from .evaluate import evaluate_predictions, macro_f1_by, market_regimes
from .jev import attach_jev_outputs
from .models import make_models
from .splits import assert_holdout_locked, fold_frames, make_folds
from .stats import block_length, holm, paired_macro_f1_bootstrap, paired_sharpe_bootstrap, per_date_confusions

MIN_JEV_COVERAGE = 0.999   # share of a fold's rows that must have been sent to Jev


def walk_forward(prices: pd.DataFrame, cfg: dict, unlock_holdout: bool = False, log=print) -> dict:
    """Fit and predict every enabled model on every fold and horizon.

    Returns predictions (one row per model, horizon and test observation), a fit log,
    the modelling dataset and the Jev availability status.
    """
    if not unlock_holdout:
        prices = lock_holdout(prices, cfg)
    ds = build_dataset(prices, cfg)
    ds, jev_status = attach_jev_outputs(ds, cfg)

    predictions, fit_log, fold_log = [], [], []
    for h in cfg["task"]["horizons"]:
        label_col = f"label_{h}"
        folds = make_folds(ds["date"], cfg, h)
        if not unlock_holdout:
            assert_holdout_locked(ds, folds, cfg)
        for fold in folds:
            frames = fold_frames(ds, fold, h)
            test = frames["test"]
            if test.empty:
                continue
            fold_log.append({"horizon": h, **fold.to_dict(),
                             **{f"n_{k}": len(v) for k, v in frames.items()}})
            segment = "holdout" if fold.is_holdout else "dev"
            for model in make_models(cfg):
                entry = {"model": model.model_id, "family": model.family, "horizon": h,
                         "fold": fold.fold_id, "segment": segment}
                reason = _unavailable(model, frames)
                if reason:
                    fit_log.append({**entry, "status": reason})
                    continue
                seed = int(cfg["seed"]) + 1000 * h + fold.fold_id
                started = time.perf_counter()
                info = model.fit(frames, label_col, seed)
                fitted = time.perf_counter()
                pred, proba = model.predict(test)
                done = time.perf_counter()
                if proba is None:
                    proba = np.full((len(test), 3), np.nan)
                predictions.append(pd.DataFrame({
                    "model": model.model_id, "horizon": h, "fold": fold.fold_id, "segment": segment,
                    "date": test["date"].to_numpy(), "ticker": test["ticker"].to_numpy(),
                    "y_true": test[label_col].to_numpy(dtype=int),
                    "fwd_ret": test[f"fwd_ret_{h}"].to_numpy(), "pred": pred,
                    "p_sell": proba[:, 0], "p_hold": proba[:, 1], "p_buy": proba[:, 2],
                }))
                fit_log.append({**entry, "status": "ok", "fit_seconds": fitted - started,
                                "predict_seconds": done - fitted, "n_test": len(test),
                                "val_macro_f1": info.get("val_macro_f1"),
                                "n_configs": info.get("n_configs"), "params": str(info.get("params", ""))})
            log(f"  horizon {h:>2}  fold {fold.fold_id} ({segment})  test {fold.test_start.date()} "
                f"n_trainval={len(frames['trainval']):,} n_test={len(test):,}")
    if not predictions:
        raise RuntimeError("No predictions were produced.")
    return {"predictions": pd.concat(predictions, ignore_index=True), "fit_log": pd.DataFrame(fit_log),
            "fold_log": pd.DataFrame(fold_log), "dataset": ds, "jev_status": jev_status}


def _unavailable(model, frames: dict) -> str | None:
    """Reason a model cannot run on this fold, or None. Only Jev arms can be unavailable."""
    for col in model.required_columns:
        if col not in frames["test"].columns:
            return "not run: no saved Jev outputs"
        coverage = min(frames[k][col].notna().mean() for k in ("trainval", "test"))
        if coverage < MIN_JEV_COVERAGE:
            return f"not run: Jev outputs cover only {coverage:.1%} of this fold"
    return None


def reference_classifier(fit_log: pd.DataFrame, horizon: int) -> str | None:
    """The traditional classifier with the best mean validation macro-F1. Uses no test data."""
    ok = fit_log[(fit_log["status"] == "ok") & (fit_log["family"] == "classifier")
                 & (fit_log["horizon"] == horizon) & (fit_log["segment"] == "dev")]
    if ok.empty:
        return None
    return str(ok.groupby("model")["val_macro_f1"].mean().idxmax())


def _same_rows(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    key = ["date", "ticker"]
    return len(a) == len(b) and a[key].reset_index(drop=True).equals(b[key].reset_index(drop=True))


def summarise(run: dict, prices: pd.DataFrame, cfg: dict) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Compute classification, statistical and trading results. Returns metrics, per-stock table, daily returns."""
    preds, fit_log = run["predictions"], run["fit_log"]
    preds = preds.sort_values(["model", "horizon", "date", "ticker"]).reset_index(drop=True)
    preds = preds.merge(market_regimes(run["dataset"]), on="date", how="left")
    returns, market_returns = open_to_open_returns(prices, cfg["data"]["market_ticker"])
    families = fit_log.drop_duplicates("model").set_index("model")["family"].to_dict()
    stats_cfg, seed = cfg["stats"], int(cfg["seed"])

    metrics: dict = {"segments": {}}
    per_stock_rows, daily_frames = [], []
    for segment, seg_preds in preds.groupby("segment"):
        seg_out: dict = {}
        for h, h_preds in seg_preds.groupby("horizon"):
            by_model = {m: g.reset_index(drop=True) for m, g in h_preds.groupby("model")}
            dates = pd.DatetimeIndex(sorted(h_preds["date"].unique()))
            block = block_length(cfg, int(h))
            reference = reference_classifier(fit_log, int(h))

            classification, confusions = {}, {}
            for name, sub in by_model.items():
                result = evaluate_predictions(sub)
                result["by_fold"] = macro_f1_by(sub, "fold")
                result["by_regime"] = macro_f1_by(sub, "regime")
                stock_f1 = macro_f1_by(sub, "ticker")
                values = np.array(list(stock_f1.values()))
                result["by_stock"] = {"n_stocks": len(values), "p10": float(np.quantile(values, 0.1)),
                                      "median": float(np.median(values)), "p90": float(np.quantile(values, 0.9))}
                per_stock_rows += [{"segment": segment, "horizon": h, "model": name, "ticker": t, "macro_f1": v}
                                   for t, v in stock_f1.items()]
                classification[name] = result
                confusions[name] = per_date_confusions(sub, dates)

            def compare(a: str, b: str) -> dict | None:
                if a not in by_model or b not in by_model or a == b:
                    return None
                if not _same_rows(by_model[a], by_model[b]):
                    return {"a": a, "b": b, "skipped": "models were not evaluated on identical rows"}
                out = paired_macro_f1_bootstrap(confusions[a], confusions[b], block, int(stats_cfg["n_boot"]),
                                                seed + int(h), float(stats_cfg["alpha"]))
                return {"a": a, "b": b, **out}

            def family_of(name: str) -> str:
                return families.get(name, "")

            skill = [c for c in (compare(m, "stratified_random") for m in by_model
                                 if family_of(m) in ("classifier", "rule", "jev")) if c]
            jev_vs_ref = [c for c in (compare(m, reference) for m in by_model
                                      if family_of(m) == "jev" and reference) if c]
            ablation = [c for c in (compare(f"jev_plus_controlled_{v}", "gbt") for v in ("zero", "examples")) if c]
            for group in (skill, jev_vs_ref, ablation):
                tested = [c for c in group if "p_value" in c]
                for c, adjusted in zip(tested, holm([c["p_value"] for c in tested])):
                    c["p_holm"] = adjusted

            trading, daily_by_model = {}, {}
            template = next(iter(by_model.values()))
            always_buy = template[["date", "ticker"]].assign(pred=BUY)
            for name, sub in {**by_model, "always_buy": always_buy}.items():
                daily = run_backtest(sub[["date", "ticker", "pred"]], returns, int(h), cfg)
                stats = trading_stats(daily, float(cfg["backtest"]["starting_capital"]))
                stats["sharpe_cost_2bps"] = trading_stats(
                    run_backtest(sub[["date", "ticker", "pred"]], returns, int(h), cfg, cost_bps=2.0), 1.0).get("sharpe")
                stats["sharpe_cost_10bps"] = trading_stats(
                    run_backtest(sub[["date", "ticker", "pred"]], returns, int(h), cfg, cost_bps=10.0), 1.0).get("sharpe")
                stats["sharpe_long_short"] = trading_stats(
                    run_backtest(sub[["date", "ticker", "pred"]], returns, int(h), cfg, mode="long_short"), 1.0).get("sharpe")
                trading[name] = stats
                daily_by_model[name] = daily
                daily_frames.append(daily.reset_index().assign(model=name, horizon=h, segment=segment))
            market = market_returns.reindex(daily_by_model["always_buy"].index).fillna(0.0)
            trading["market_buy_and_hold"] = trading_stats(pd.DataFrame({
                "net": market, "gross": market, "cost": 0.0, "turnover": 0.0, "exposure": 1.0,
                "positions_opened": 0}), float(cfg["backtest"]["starting_capital"]))

            def compare_sharpe(a: str, b: str) -> dict | None:
                if a not in daily_by_model or b not in daily_by_model or a == b:
                    return None
                ra, rb = daily_by_model[a]["net"], daily_by_model[b]["net"]
                if not ra.index.equals(rb.index):
                    return {"a": a, "b": b, "skipped": "return series cover different dates"}
                out = paired_sharpe_bootstrap(ra.to_numpy(), rb.to_numpy(), block, int(stats_cfg["n_boot"]),
                                              seed + 7 * int(h), float(stats_cfg["alpha"]))
                return {"a": a, "b": b, **out}

            trading_vs_buy = [c for c in (compare_sharpe(m, "always_buy") for m in by_model
                                          if family_of(m) in ("classifier", "rule", "jev")) if c]
            trading_jev = [c for c in (compare_sharpe(m, reference) for m in by_model
                                       if family_of(m) == "jev" and reference) if c]
            for group in (trading_vs_buy, trading_jev):
                tested = [c for c in group if "p_value" in c]
                for c, adjusted in zip(tested, holm([c["p_value"] for c in tested])):
                    c["p_holm"] = adjusted

            seg_out[int(h)] = {
                "n_dates": len(dates), "n_observations": int(len(template)), "block_length_days": block,
                "first_date": str(dates[0].date()), "last_date": str(dates[-1].date()),
                "reference_classifier": reference,
                "classification": classification,
                "comparisons": {"skill_vs_stratified_random": skill, "jev_vs_reference": jev_vs_ref,
                                "jev_plus_controlled_vs_gbt": ablation},
                "trading": trading,
                "trading_comparisons": {"vs_always_buy": trading_vs_buy, "jev_vs_reference": trading_jev},
            }
        metrics["segments"][segment] = seg_out

    ok = fit_log[fit_log["status"] == "ok"]
    metrics["runtime"] = {
        m: {"fit_seconds": float(g["fit_seconds"].sum()), "predict_seconds": float(g["predict_seconds"].sum()),
            "fits": int(len(g)), "configs_per_fit": int(g["n_configs"].max()),
            "test_rows": int(g["n_test"].sum())}
        for m, g in ok.groupby("model")
    }
    metrics["not_run"] = (fit_log[fit_log["status"] != "ok"].groupby("model")["status"]
                          .agg(lambda s: s.iloc[0]).to_dict())
    metrics["jev_status"] = run["jev_status"]
    daily_all = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()
    return metrics, pd.DataFrame(per_stock_rows), daily_all
