"""Write a self-contained HTML page of a run's backtests.

The page embeds its data and draws its own charts, so it opens from disk with no
network access. Every number comes from the run's saved metrics and daily returns.
"""
from __future__ import annotations

import ast
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .backtest import names_held, rank_weights, trade_rules, trading_stats, tranche_weights, with_cost
from .providers import PROVIDERS, describe_arm
from .report import detectable_effect
from .stats import holm, paired_sharpe_bootstrap

LABELS = {
    "gbt": "Gradient-boosted trees", "logreg": "Logistic regression", "random_forest": "Random forest",
    "momentum_rule": "Momentum rule", "ma_cross_rule": "Moving-average rule",
    "stratified_random": "Random signals", "majority": "Always HOLD",
    "always_buy": "Equal-weight buy and hold", "market_buy_and_hold": "Market index buy and hold",
}
KINDS = {"baseline": "Baseline"}
# Every traded model belongs to one group; benchmarks and no-skill baselines belong to none.
MODEL_GROUPS = {"index_ml": "Index ML Classifier", "rule": "Rule Based",
                "jev_ml": "ML Classifier with Jev", "jev": "Jev"}
# The "Strategies" filter on the page. `groups` lists the groups a choice shows (None for all of them).
# Strategies with no group always stay on screen.
STRATEGY_FILTERS = [
    {"id": "all", "label": "All strategies", "groups": None},
    {"id": "ml", "label": "ML classifiers", "groups": ["index_ml"]},
    {"id": "jev_related", "label": "Jev related", "groups": ["jev", "jev_ml"]},
]
# Statistics that change when the trading cost does; the page swaps these when costs are switched off.
COST_STATS = ("cumulative_net_return", "cagr", "sharpe", "max_drawdown", "alpha", "beta")
PASSIVE = ("always_buy", "market_buy_and_hold")
MAX_POINTS = 900   # per line; longer series are thinned for drawing only
ASSET_NAMES = {
    "IVV": "S&P 500", "GLD": "Gold", "BTC-USD": "Bitcoin", "TLT": "Long Treasuries", "EFA": "Developed stocks",
    "EEM": "Emerging stocks", "USO": "Crude oil", "VNQ": "Real estate", "UUP": "US dollar", "HYG": "High-yield bonds",
    "GOOGL": "Alphabet", "PG": "Procter & Gamble", "IBM": "IBM", "CVX": "Chevron", "WFC": "Wells Fargo", "CSCO": "Cisco",
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


def _lines(parts: dict[str, pd.DataFrame]) -> dict:
    """Growth of 1 and drawdown for each strategy, thinned for drawing only."""
    dates, growth, drawdown, thinned = [], {}, {}, 1
    for m, part in parts.items():
        equity = np.cumprod(1 + part["net"].to_numpy())
        dd = (equity / np.maximum(np.maximum.accumulate(equity), 1.0) - 1) * 100
        thinned = max(1, int(np.ceil(len(equity) / MAX_POINTS)))
        keep = np.unique(np.r_[np.arange(0, len(equity), thinned), len(equity) - 1])
        dates = part["date"].dt.strftime("%Y-%m-%d").to_numpy()[keep].tolist()
        growth[m] = np.round(equity[keep], 4).tolist()
        drawdown[m] = np.round(dd[keep], 2).tolist()
    return {"dates": dates, "growth": growth, "drawdown": drawdown, "thinned": thinned}


def _without_costs(parts: dict[str, pd.DataFrame], comparisons: list[dict], block: int, horizon: int, cfg: dict) -> dict:
    """The same view with the trading cost set to zero: a what-if, not part of the experiment's test.

    Lines, the statistics that depend on cost, and the Sharpe comparison against buy and hold,
    bootstrapped with the benchmark's own settings so the two versions differ only in the cost.
    """
    free = {m: with_cost(part, 0.0) for m, part in parts.items()}
    lines, market = _lines(free), free.get("market_buy_and_hold")
    stats = {}
    for m, d in free.items():
        aligned = market is not None and d["date"].reset_index(drop=True).equals(market["date"].reset_index(drop=True))
        s = trading_stats(d, 1.0, market["excess"].to_numpy() if aligned else None)
        stats[m] = {k: s.get(k) for k in COST_STATS}
    st, hold = cfg["stats"], free["always_buy"]["excess"].to_numpy()
    tested = [c["a"] for c in comparisons if "diff" in c]
    found = [paired_sharpe_bootstrap(free[m]["excess"].to_numpy(), hold, block, int(st["n_boot"]),
                                     int(cfg["seed"]) + 7 * horizon, float(st["alpha"])) for m in tested]
    return {
        "growth": lines["growth"], "drawdown": lines["drawdown"], "stats": stats,
        "diffs": [{"id": m, "diff": c["diff"], "lo": c["ci_low"], "hi": c["ci_high"], "p": p}
                  for m, c, p in zip(tested, found, holm([c["p_value"] for c in found]))],
        "power": detectable_effect(found),
    }


def _group(model: str, family: str) -> str | None:
    """Which model group a strategy belongs to; None for benchmarks and baselines."""
    if family == "classifier":
        return "index_ml"
    if family == "rule":
        return "rule"
    if family == "jev":   # other registered providers are reserved and have no group yet
        return "jev" if model.startswith("jev_signal_") else "jev_ml"
    return None


def _strategy(model: str, families: dict, rule: str) -> dict:
    family = families.get(model, "")
    if model in PASSIVE:
        return {"id": model, "label": LABELS[model], "kind": "Benchmark", "group": None, "chart": True}
    group = _group(model, family)
    if family in PROVIDERS:
        return {"id": model, "label": describe_arm(model), "group": group, "chart": True,
                "kind": MODEL_GROUPS[group] if group else PROVIDERS[family]["label"]}
    label, chart = LABELS.get(model, model), True
    ranked = rule != "buy_names"
    if ranked and model == "stratified_random":
        label = "Random selection"
    if model == "majority":
        # Under a ranking rule it is identical to random selection; under BUY-names it never trades.
        chart = False
        label = "Always HOLD (same as random selection)" if ranked else "Always HOLD (never trades)"
    return {"id": model, "label": label, "group": group, "chart": chart,
            "kind": MODEL_GROUPS[group] if group else KINDS.get(family, family)}


def _setting_label(model: str, params: dict) -> str:
    if model == "momentum_rule":
        return f"{int(params['lookback'])}-day return, dead band {float(params['band']):g}"
    if model == "ma_cross_rule":
        return f"{int(params['fast'])}/{int(params['slow'])}-day averages" + (", price must confirm" if params["confirm"] else "")
    return str(params)


def _grid_summary(grid: list[dict]) -> dict:
    """Distinct values of each tuned setting, in the order they first appear."""
    out: dict[str, list] = {}
    for config in grid:
        for key, value in config.items():
            seen = out.setdefault(key, [])
            if value not in seen:
                seen.append(value)
    return {k: ["none" if v is None else v for v in vs] for k, vs in out.items()}


def _models_info(run_dir: Path, cfg: dict, horizons: list[int]) -> dict:
    """Settings of every model, and which rule settings validation picked in each fold."""
    fit_path = run_dir / "fit_log.csv"
    fit = pd.read_csv(fit_path) if fit_path.exists() else None
    models = cfg["models"]
    rules = {}
    for model in ("momentum_rule", "ma_cross_rule"):
        grid = models[model]["grid"]
        chosen = {}
        if fit is not None:
            for h in horizons:
                part = fit[(fit["model"] == model) & (fit["horizon"] == h) & fit["params"].notna()]
                counts = Counter(_setting_label(model, ast.literal_eval(p)) for p in part["params"])
                chosen[str(h)] = {"folds": int(len(part)), "counts": [[k, v] for k, v in counts.most_common()]}
        rules[model] = {"grid": [_setting_label(model, g) for g in grid], "chosen": chosen}
    bt, label = cfg["backtest"], cfg["task"]["label"]
    return {
        "rules": rules,
        "classifiers": {m: {"n_configs": len(models[m]["grid"]), "grid": _grid_summary(models[m]["grid"])}
                        for m in ("logreg", "random_forest", "gbt")},
        "portfolio": {
            "assets": len(cfg["data"]["tickers"]), "held": names_held(cfg, "rank"),
            "held_check": names_held(cfg, "rank_check") if bt.get("rank_check_fraction") is not None else None,
            "cost_bps": bt["cost_bps_per_side"], "max_weight": bt["max_weight"],
            "label_k": label["k"], "vol_window": label["vol_window"], "horizons": horizons,
            "validation_months": cfg["splits"]["validation_months"], "test_months": cfg["splits"]["test_months"],
        },
    }


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
                parts = {m: sub[(sub["model"] == m) & (sub["rule"] == ("passive" if m in PASSIVE else rule))].sort_values("date")
                         for m in models}
                comparisons = block["trading_comparisons"][rule]["vs_buy_and_hold"]
                power = detectable_effect(comparisons)
                views[f"{segment}|{rule}|{h}"] = {
                    "strategies": strategies, **_lines(parts),
                    "first_date": block["first_date"], "last_date": block["last_date"],
                    "stats": {m: {k: stats[m].get(k) for k in (
                        "cumulative_net_return", "cagr", "sharpe", "max_drawdown", "annual_turnover",
                        "mean_exposure", "alpha", "beta", "sharpe_cost_10bps")} for m in models},
                    "diffs": [{"id": c["a"], "diff": c["diff"], "lo": c["ci_low"], "hi": c["ci_high"],
                               "p": c.get("p_holm", c["p_value"])} for c in comparisons if "diff" in c],
                    "power": power,
                    "free": _without_costs(parts, comparisons, int(block["block_length_days"]), h, cfg),
                    "holdings": _holdings(view_preds, cfg, rule, tickers) if view_preds is not None else None,
                }

    bt, n_assets = cfg["backtest"], len(cfg["data"]["tickers"])
    rule_labels = {r: ("BUY names only" if r == "buy_names" else f"Top {names_held(cfg, r) or '?'} of {n_assets} by score")
                   for r in rules}
    present = {s["group"] for v in views.values() for s in v["strategies"]}
    return {
        "filters": [{**f, "present": f["groups"] is None or any(g in present for g in f["groups"])}
                    for f in STRATEGY_FILTERS],
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
        "models": _models_info(run_dir, cfg, horizons),
    }


def write_page(run_dir: Path) -> Path:
    payload = json.dumps(build_payload(Path(run_dir)), separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    template = (Path(__file__).parent / "visualise_template.html").read_text(encoding="utf-8")
    out = Path(run_dir) / "backtests.html"
    out.write_text(template.replace("/*__DATA__*/null", payload), encoding="utf-8")
    return out
