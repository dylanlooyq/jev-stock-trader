"""Run the walk-forward benchmark and compute every metric from saved predictions."""
from __future__ import annotations

import time

import numpy as np
import pandas as pd

from .backtest import (RULES, annualised_sharpe, open_to_open_returns, passive_daily, run_backtest, trading_stats,
                       with_cost)
from .data import lock_holdout
from .dataset import build_dataset
from .evaluate import evaluate_predictions, macro_f1_by, market_regimes
from .jev import attach_outputs
from .models import make_models
from .providers import PROVIDERS, VARIANTS, arm_name
from .splits import assert_holdout_locked, fold_frames, make_folds
from .stats import (alpha_bootstrap, block_length, holm, paired_macro_f1_bootstrap, paired_sharpe_bootstrap,
                    per_date_confusions)

MIN_OUTPUT_COVERAGE = 0.999   # share of a fold's rows that must have been sent to a provider
TRADED_FAMILIES = ("classifier", "rule", *PROVIDERS)


def walk_forward(prices: pd.DataFrame, cfg: dict, unlock_holdout: bool = False, log=print) -> dict:
    """Fit and predict every enabled model on every fold and horizon.

    Returns predictions (one row per model, horizon and test observation), a fit log,
    the modelling dataset and the availability status of each external provider.
    """
    if not unlock_holdout:
        prices = lock_holdout(prices, cfg)
    ds = build_dataset(prices, cfg)
    ds, external_status = attach_outputs(ds, cfg)

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
                score = model.rank_score(test, pred, proba)
                done = time.perf_counter()
                if proba is None:
                    proba = np.full((len(test), 3), np.nan)
                predictions.append(pd.DataFrame({
                    "model": model.model_id, "horizon": h, "fold": fold.fold_id, "segment": segment,
                    "date": test["date"].to_numpy(), "ticker": test["ticker"].to_numpy(),
                    "y_true": test[label_col].to_numpy(dtype=int),
                    "fwd_ret": test[f"fwd_ret_{h}"].to_numpy(), "pred": pred, "score": score,
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
            "fold_log": pd.DataFrame(fold_log), "dataset": ds, "external_status": external_status}


def _unavailable(model, frames: dict) -> str | None:
    """Reason a model cannot run on this fold, or None. Only external-provider arms can be unavailable."""
    for col in model.required_columns:
        if col not in frames["test"].columns:
            return "not run: no saved outputs"
        coverage = min(frames[k][col].notna().mean() for k in ("trainval", "test"))
        if coverage < MIN_OUTPUT_COVERAGE:
            return f"not run: saved outputs cover only {coverage:.1%} of this fold"
    return None


def reference_classifier(fit_log: pd.DataFrame, horizon: int) -> str | None:
    """The traditional classifier with the best mean validation macro-F1. Uses no test data."""
    ok = fit_log[(fit_log["status"] == "ok") & (fit_log["family"] == "classifier") & (fit_log["horizon"] == horizon)]
    if ok.empty:
        return None
    return str(ok.groupby("model")["val_macro_f1"].mean().idxmax())


def _same_rows(a: pd.DataFrame, b: pd.DataFrame) -> bool:
    key = ["date", "ticker"]
    return len(a) == len(b) and a[key].reset_index(drop=True).equals(b[key].reset_index(drop=True))


def _holm_in_place(group: list[dict]) -> list[dict]:
    tested = [c for c in group if "p_value" in c]
    for c, adjusted in zip(tested, holm([c["p_value"] for c in tested])):
        c["p_holm"] = adjusted
    return group


def _comparison_plan(models: list[str], families: dict, reference: str | None) -> dict:
    """Which pairs are compared. The plan is identical for classification and trading."""
    plan = {"providers": {}}
    for provider in PROVIDERS:
        arms = [m for m in models if families.get(m) == provider]
        if not arms:
            continue
        plan["providers"][provider] = {
            "vs_reference": [(m, reference) for m in arms if reference],
            "augmented_vs_gbt": [(arm_name(provider, "plus_controlled", v), "gbt") for v in VARIANTS],
            "alone_vs_augmented": [(arm_name(provider, "signal", v), arm_name(provider, "plus_controlled", v))
                                   for v in VARIANTS],
        }
    return plan


def _segments(preds: pd.DataFrame) -> list[tuple[str, pd.DataFrame]]:
    """With the holdout unlocked the verdict is on every fold pooled ("all"); parts are kept for robustness."""
    names = sorted(preds["segment"].unique())
    parts = [(name, preds[preds["segment"] == name]) for name in names]
    return [("all", preds), *parts] if len(names) > 1 else parts


def summarise(run: dict, prices: pd.DataFrame, cfg: dict,
              risk_free: pd.Series | None = None) -> tuple[dict, pd.DataFrame, pd.DataFrame]:
    """Compute classification, statistical and trading results. Returns metrics, per-stock table, daily returns."""
    preds, fit_log = run["predictions"], run["fit_log"]
    preds = preds.sort_values(["model", "horizon", "date", "ticker"]).reset_index(drop=True)
    preds = preds.merge(market_regimes(run["dataset"]), on="date", how="left")
    returns, market_returns = open_to_open_returns(prices, cfg["data"]["market_ticker"])
    families = fit_log.drop_duplicates("model").set_index("model")["family"].to_dict()
    stats_cfg, seed = cfg["stats"], int(cfg["seed"])
    n_boot, alpha, capital = int(stats_cfg["n_boot"]), float(stats_cfg["alpha"]), float(cfg["backtest"]["starting_capital"])

    metrics: dict = {"segments": {}}
    per_stock_rows, daily_frames = [], []
    for segment, seg_preds in _segments(preds):
        seg_out: dict = {}
        for h, h_preds in seg_preds.groupby("horizon"):
            h = int(h)
            by_model = {m: g.reset_index(drop=True) for m, g in h_preds.groupby("model")}
            dates = pd.DatetimeIndex(sorted(h_preds["date"].unique()))
            block = block_length(cfg, h)
            reference = reference_classifier(fit_log, h)
            plan = _comparison_plan(list(by_model), families, reference)
            traded = [m for m in by_model if families.get(m) in TRADED_FAMILIES]

            # ---- classification (diagnostic)
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

            def compare_f1(a: str, b: str | None) -> dict | None:
                if a not in by_model or b not in by_model or a == b:
                    return None
                if not _same_rows(by_model[a], by_model[b]):
                    return {"a": a, "b": b, "skipped": "models were not evaluated on identical rows"}
                return {"a": a, "b": b, **paired_macro_f1_bootstrap(confusions[a], confusions[b], block, n_boot,
                                                                    seed + h, alpha)}

            comparisons = {
                "skill_vs_stratified_random": _holm_in_place(
                    [c for c in (compare_f1(m, "stratified_random") for m in traded) if c]),
                "providers": {p: {k: _holm_in_place([c for c in (compare_f1(a, b) for a, b in pairs) if c])
                                  for k, pairs in groups.items()}
                              for p, groups in plan["providers"].items()},
            }

            # ---- trading (primary)
            template = next(iter(by_model.values()))
            hold_frame = template[["date", "ticker"]].assign(score=0.0)
            hold = run_backtest(hold_frame, returns, h, cfg, rule="rank", mode="long_only", risk_free=risk_free,
                                rank_fraction=1.0)
            market = passive_daily(market_returns.reindex(hold.index), risk_free)
            market_excess = market["excess"].to_numpy()
            trading, trading_comparisons = {}, {}
            for rule in RULES:
                daily = {"always_buy": hold, "market_buy_and_hold": market}
                stats = {"always_buy": trading_stats(hold, capital, market_excess),
                         "market_buy_and_hold": trading_stats(market, capital, market_excess)}
                for name, sub in by_model.items():
                    frame = sub[["date", "ticker", "pred", "score"]]
                    d = run_backtest(frame, returns, h, cfg, rule=rule, risk_free=risk_free)
                    aligned = d.index.equals(hold.index)
                    s = trading_stats(d, capital, market_excess if aligned else None)
                    s["sharpe_cost_2bps"] = annualised_sharpe(with_cost(d, 2.0)["excess"].to_numpy())
                    s["sharpe_cost_10bps"] = annualised_sharpe(with_cost(d, 10.0)["excess"].to_numpy())
                    s["sharpe_long_short"] = annualised_sharpe(run_backtest(
                        frame, returns, h, cfg, rule=rule, mode="long_short", risk_free=risk_free)["excess"].to_numpy())
                    if aligned:
                        ab = alpha_bootstrap(d["excess"].to_numpy(), market_excess, block, n_boot, seed + 13 * h, alpha)
                        s["alpha_ci_low"], s["alpha_ci_high"] = ab["ci_low"], ab["ci_high"]
                        # Same daily exposure spread over every stock: isolates stock selection from being invested.
                        matched = d["exposure"] * hold["gross"] + (1 - d["exposure"]) * d["rf"]
                        s["sharpe_exposure_matched"] = annualised_sharpe((matched - d["rf"]).to_numpy())
                        s["selection_return_per_year"] = float((d["net"] - matched).mean() * 252)
                    stats[name], daily[name] = s, d
                    daily_frames.append(d.reset_index().assign(model=name, horizon=h, segment=segment, rule=rule))
                if rule == RULES[0]:
                    for name in ("always_buy", "market_buy_and_hold"):
                        daily_frames.append(daily[name].reset_index().assign(
                            model=name, horizon=h, segment=segment, rule="passive"))

                def compare_sharpe(a: str, b: str | None) -> dict | None:
                    if a not in daily or b not in daily or a == b:
                        return None
                    if not daily[a].index.equals(daily[b].index):
                        return {"a": a, "b": b, "skipped": "return series cover different dates"}
                    return {"a": a, "b": b, **paired_sharpe_bootstrap(
                        daily[a]["excess"].to_numpy(), daily[b]["excess"].to_numpy(), block, n_boot, seed + 7 * h, alpha)}

                trading[rule] = stats
                trading_comparisons[rule] = {
                    "vs_buy_and_hold": _holm_in_place(
                        [c for c in (compare_sharpe(m, "always_buy") for m in traded) if c]),
                    "providers": {p: {k: _holm_in_place([c for c in (compare_sharpe(a, b) for a, b in pairs) if c])
                                      for k, pairs in groups.items()}
                                  for p, groups in plan["providers"].items()},
                }

            seg_out[h] = {
                "n_dates": len(dates), "n_observations": int(len(template)), "block_length_days": block,
                "first_date": str(dates[0].date()), "last_date": str(dates[-1].date()),
                "reference_classifier": reference,
                "classification": classification, "comparisons": comparisons,
                "trading": trading, "trading_comparisons": trading_comparisons,
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
    metrics["external_status"] = run["external_status"]
    metrics["families"] = families
    daily_all = pd.concat(daily_frames, ignore_index=True) if daily_frames else pd.DataFrame()
    return metrics, pd.DataFrame(per_stock_rows), daily_all
