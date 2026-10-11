"""Write a self-contained HTML page of a run's backtests.

The page embeds its data and draws its own charts, so it opens from disk with no
network access. Every number comes from the run's saved metrics and daily returns.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .backtest import names_held, rank_weights, trade_rules, tranche_weights
from .providers import PROVIDERS, describe_arm
from .report import detectable_effect

LABELS = {
    "gbt": "Gradient-boosted trees", "logreg": "Logistic regression", "random_forest": "Random forest",
    "momentum_rule": "Momentum rule", "ma_cross_rule": "Moving-average rule",
    "stratified_random": "Random signals", "majority": "Always HOLD",
    "always_buy": "Equal-weight buy and hold", "market_buy_and_hold": "Market index buy and hold",
}
KINDS = {"classifier": "Model", "rule": "Rule", "baseline": "Baseline"}
PASSIVE = ("always_buy", "market_buy_and_hold")
MAX_POINTS = 900   # per line; longer series are thinned for drawing only
ASSET_NAMES = {
    "IVV": "S&P 500", "GLD": "Gold", "BTC-USD": "Bitcoin", "TLT": "Long Treasuries", "EFA": "Developed stocks",
    "EEM": "Emerging stocks", "USO": "Crude oil", "VNQ": "Real estate", "UUP": "US dollar", "HYG": "High-yield bonds",
}


def _holdings(preds: pd.DataFrame, cfg: dict, rule: str, tickers: list[str]) -> dict:
    """Average share of each strategy's newly opened positions held in each asset, in percent.

    Recomputed from the saved predictions with the same weighting functions the backtest uses.
    """
    spec, bt = trade_rules(cfg)[rule], cfg["backtest"]
    out = {}
    for model, sub in preds.groupby("model"):
        if spec["rule"] == "rank":
            wide = sub.pivot(index="date", columns="ticker", values="score").reindex(columns=tickers)
            weights = rank_weights(wide, spec["rank_fraction"], int(cfg["seed"]), "long_only")
        else:
            wide = sub.pivot(index="date", columns="ticker", values="pred").reindex(columns=tickers)
            weights = tranche_weights(wide, "long_only", float(bt["max_weight"]))
        out[model] = np.round(weights.mean(axis=0).to_numpy() * 100, 1).tolist()
    available = preds[preds["model"] == preds["model"].iloc[0]].pivot(
        index="date", columns="ticker", values="pred").reindex(columns=tickers).notna()
    equal = available.div(available.sum(axis=1), axis=0)
    out["always_buy"] = np.round(equal.mean(axis=0).to_numpy() * 100, 1).tolist()
    return out


def _strategy(model: str, families: dict, rule: str) -> dict:
    family = families.get(model, "")
    if model in PASSIVE:
        return {"id": model, "label": LABELS[model], "kind": "Benchmark", "chart": True}
    if family in PROVIDERS:
        return {"id": model, "label": describe_arm(model), "kind": PROVIDERS[family]["label"], "chart": True}
    label, chart = LABELS.get(model, model), True
    ranked = rule != "buy_names"
    if ranked and model == "stratified_random":
        label = "Random selection"
    if model == "majority":
        # Under a ranking rule it is identical to random selection; under BUY-names it never trades.
        chart = False
        label = "Always HOLD (same as random selection)" if ranked else "Always HOLD (never trades)"
    return {"id": model, "label": label, "kind": KINDS.get(family, family), "chart": chart}


def build_payload(run_dir: Path) -> dict:
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    cfg = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    daily = pd.read_parquet(run_dir / "daily_returns.parquet")
    families = metrics.get("families", {})
    folds = pd.read_csv(run_dir / "folds.csv")
    tickers = list(cfg["data"]["tickers"])
    preds_path = run_dir / "predictions.parquet"   # kept locally, not in the repository
    preds = pd.read_parquet(preds_path, columns=["model", "horizon", "segment", "date", "ticker", "pred", "score"]) \
        if preds_path.exists() else None

    order = [m for m in LABELS if m not in PASSIVE]
    views, segments = {}, sorted(metrics["segments"], key=lambda s: {"all": 0, "dev": 1, "holdout": 2}.get(s, 3))
    rules = list(next(iter(next(iter(metrics["segments"].values())).values()))["trading"])
    horizons = sorted(int(h) for h in next(iter(metrics["segments"].values())))
    for segment in segments:
        for h in horizons:
            block = metrics["segments"][segment][str(h)]
            sub = daily[(daily["segment"] == segment) & (daily["horizon"] == h)]
            view_preds = None
            if preds is not None:
                view_preds = preds[(preds["horizon"] == h) & ((preds["segment"] == segment) | (segment == "all"))]
            for rule in rules:
                stats = block["trading"][rule]
                models = sorted(stats, key=lambda m: (m in PASSIVE, order.index(m) if m in order else len(order), m))
                strategies = [_strategy(m, families, rule) for m in models]
                dates, growth, drawdown, thinned = [], {}, {}, 1
                for m in models:
                    part = sub[(sub["model"] == m) & (sub["rule"] == ("passive" if m in PASSIVE else rule))].sort_values("date")
                    equity = np.cumprod(1 + part["net"].to_numpy())
                    dd = (equity / np.maximum(np.maximum.accumulate(equity), 1.0) - 1) * 100
                    thinned = max(1, int(np.ceil(len(equity) / MAX_POINTS)))
                    keep = np.unique(np.r_[np.arange(0, len(equity), thinned), len(equity) - 1])
                    dates = part["date"].dt.strftime("%Y-%m-%d").to_numpy()[keep].tolist()
                    growth[m] = np.round(equity[keep], 4).tolist()
                    drawdown[m] = np.round(dd[keep], 2).tolist()
                comparisons = block["trading_comparisons"][rule]["vs_buy_and_hold"]
                power = detectable_effect(comparisons)
                views[f"{segment}|{rule}|{h}"] = {
                    "strategies": strategies, "dates": dates, "growth": growth, "drawdown": drawdown,
                    "thinned": thinned, "first_date": block["first_date"], "last_date": block["last_date"],
                    "stats": {m: {k: stats[m].get(k) for k in (
                        "cumulative_net_return", "cagr", "sharpe", "max_drawdown", "annual_turnover",
                        "mean_exposure", "alpha", "beta", "sharpe_cost_10bps")} for m in models},
                    "diffs": [{"id": c["a"], "diff": c["diff"], "lo": c["ci_low"], "hi": c["ci_high"],
                               "p": c.get("p_holm", c["p_value"])} for c in comparisons if "diff" in c],
                    "power": power,
                    "holdings": _holdings(view_preds, cfg, rule, tickers) if view_preds is not None else None,
                }

    bt, n_assets = cfg["backtest"], len(cfg["data"]["tickers"])
    rule_labels = {r: ("BUY names only" if r == "buy_names" else f"Top {names_held(cfg, r) or '?'} of {n_assets} by score")
                   for r in rules}
    return {
        "run": {
            "name": manifest["run_name"], "smoke": cfg["experiment_id"] == "smoke",
            "full_window": bool(manifest["holdout_unlocked"]), "generated": manifest["finished_at_utc"],
            "commit": manifest["git_commit"], "assets": len(cfg["data"]["tickers"]),
            "folds": int(folds["fold_id"].nunique()), "cost_bps": bt["cost_bps_per_side"],
            "held": {r: names_held(cfg, r) for r in rules}, "risk_free": manifest.get("risk_free", "zero"),
            "market": cfg["data"]["market_ticker"],
            "hindsight": "The asset list was chosen with hindsight, which flatters every line here, buy and hold included.",
            "external": metrics.get("external_status", {}),
            "external_ran": sorted({families[m] for m in manifest["models_run"] if families.get(m) in PROVIDERS}),
        },
        "segments": segments, "rules": rules, "rule_labels": rule_labels, "horizons": horizons,
        "tickers": [{"id": t, "name": ASSET_NAMES.get(t, t)} for t in tickers],
        "defaults": {"segment": segments[0], "rule": bt["primary_rule"], "horizon": cfg["task"]["primary_horizon"]},
        "views": views,
    }


def write_page(run_dir: Path) -> Path:
    payload = json.dumps(build_payload(Path(run_dir)), separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    template = (Path(__file__).parent / "visualise_template.html").read_text(encoding="utf-8")
    out = Path(run_dir) / "backtests.html"
    out.write_text(template.replace("/*__DATA__*/null", payload), encoding="utf-8")
    return out
