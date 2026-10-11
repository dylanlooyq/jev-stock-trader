"""Render a Markdown report from a run's metrics and manifest. Numbers come only from saved results."""
from __future__ import annotations

from . import CLASS_NAMES

JEV_ARMS = {
    "jev_signal_zero": "Jev as signal, zero-shot",
    "jev_signal_examples": "Jev as signal, with training examples",
    "jev_head_zero": "GBT on Jev outputs, zero-shot",
    "jev_head_examples": "GBT on Jev outputs, with training examples",
    "jev_plus_controlled_zero": "GBT on controlled features + Jev outputs, zero-shot",
    "jev_plus_controlled_examples": "GBT on controlled features + Jev outputs, with examples",
}


def fmt(value, digits: int = 3, pct: bool = False, pct_digits: int = 1) -> str:
    if value is None or value != value:
        return "n/a"
    if pct:
        return f"{value * 100:.{pct_digits}f}%"
    if isinstance(value, int):
        return f"{value:,}"
    return f"{value:.{digits}f}"


def table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] + ["---:"] * (len(headers) - 1)) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _comparison_rows(items: list[dict]) -> list[list]:
    rows = []
    for c in items:
        if "skipped" in c:
            rows.append([f"{c['a']} vs {c['b']}", "skipped", c["skipped"], "", ""])
        else:
            rows.append([f"{c['a']} vs {c['b']}", fmt(c["diff"], 4), f"{fmt(c['ci_low'], 4)} to {fmt(c['ci_high'], 4)}",
                         fmt(c["p_value"]), fmt(c.get("p_holm"))])
    return rows


def conclusion(metrics: dict, cfg: dict) -> list[str]:
    """A direct verdict on each of the four questions, derived from the predefined decision rule."""
    primary = cfg["task"]["primary_horizon"]
    margin, alpha = cfg["stats"]["practical_margin_macro_f1"], cfg["stats"]["alpha"]
    segment = "holdout" if "holdout" in metrics["segments"] else "dev"
    block = metrics["segments"][segment].get(primary) or metrics["segments"][segment].get(str(primary))
    lines = []
    if segment == "dev":
        lines.append("**These are development-fold results. The locked final holdout has not been evaluated, "
                     "so nothing below is a final finding.**\n")
    jev_cls = [c for c in block["comparisons"]["jev_vs_reference"] if "diff" in c]
    if not jev_cls:
        lines += [
            "- **Classification performance:** insufficient evidence. No Jev arm has been run "
            f"({'; '.join(sorted(set(metrics['jev_status'].values())))}).",
            "- **Trading performance:** insufficient evidence, for the same reason.",
            "- **Operational efficiency:** insufficient evidence. Jev runtime and cost have not been measured.",
            "- **Overall:** the evidence does not yet bear on whether Jev is better than conventional classifiers.",
        ]
        return lines
    ref = block["reference_classifier"]
    wins = [c for c in jev_cls if c["diff"] >= margin and c["ci_low"] > 0 and c.get("p_holm", 1) < alpha]
    losses = [c for c in jev_cls if c["ci_high"] < 0 and c.get("p_holm", 1) < alpha]
    if wins:
        names = ", ".join(c["a"] for c in wins)
        lines.append(f"- **Classification performance:** supported for {names} at the {primary}-day horizon "
                     f"(at least +{margin} macro-F1 over {ref}, Holm-adjusted p < {alpha}). "
                     "Check the other horizons, folds and sensitivity runs before generalising.")
    elif losses and len(losses) == len(jev_cls):
        lines.append(f"- **Classification performance:** evidence against. Every Jev arm is worse than {ref} "
                     f"at the {primary}-day horizon with Holm-adjusted p < {alpha}.")
    else:
        lines.append(f"- **Classification performance:** not supported. No Jev arm beats {ref} by the predefined "
                     f"margin of +{margin} macro-F1 with a Holm-adjusted p < {alpha} at the {primary}-day horizon.")
    jev_trd = [c for c in block["trading_comparisons"]["jev_vs_reference"] if "diff" in c]
    trd_wins = [c for c in jev_trd if c["ci_low"] > 0 and c.get("p_holm", 1) < alpha]
    if trd_wins:
        lines.append(f"- **Trading performance:** supported for {', '.join(c['a'] for c in trd_wins)} "
                     f"(net Sharpe above {ref}, Holm-adjusted p < {alpha}).")
    else:
        lines.append(f"- **Trading performance:** not supported. No Jev arm has a net Sharpe ratio reliably above {ref}.")
    lines.append("- **Operational efficiency:** see the runtime and cost table; this is reported, not tested.")
    return lines


def render_report(metrics: dict, manifest: dict, cfg: dict) -> str:
    primary = cfg["task"]["primary_horizon"]
    label, splits, data = cfg["task"]["label"], cfg["splits"], manifest.get("dataset", {})
    out: list[str] = [f"# Experiment report: {manifest['run_name']}", ""]
    if cfg["experiment_id"] == "smoke":
        out += ["> **Smoke run.** A small configuration used to validate the pipeline end to end. "
                "These numbers are not experimental findings.", ""]
    out += [
        f"Generated {manifest['finished_at_utc']} from commit `{manifest['git_commit']}`, "
        f"config `{manifest['config_hash']}`, dataset `{str(data.get('sha256', 'n/a'))[:12]}`. "
        f"Holdout unlocked: **{manifest['holdout_unlocked']}**.",
        "",
        "## 1. Research question and method",
        "",
        "Does Jev classify next-period stock moves as BUY / HOLD / SELL better than traditional classifiers "
        "given the same information, and does any advantage survive as trading performance net of costs? "
        "Every model is fitted and scored on identical observations in a purged walk-forward design. "
        "The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.",
        "",
        "## 2. Data and labels",
        "",
        f"- Universe: `{cfg['data']['universe_name']}`, {data.get('tickers_obtained', 'n/a')} tickers obtained "
        f"including the market proxy {cfg['data']['market_ticker']}; failed downloads: "
        f"{data.get('tickers_failed') or 'none'}.",
        f"- Source: {cfg['data']['source']} daily bars, {data.get('first_date', 'n/a')} to "
        f"{data.get('last_date', 'n/a')}, downloaded {data.get('downloaded_at_utc', 'n/a')}.",
        "- The universe is a fixed list chosen with hindsight, not point-in-time membership. "
        "Survivorship bias is present and affects every model equally in direction but not necessarily in size.",
        "- Prediction after the close of day t; execution at the open of t+1; label return is "
        "open(t+1) to open(t+1+h), dividend and split adjusted.",
        (f"- Labels: BUY / SELL when the forward return is beyond ±{label['k']} × trailing "
         f"{label['vol_window']}-day volatility × √h, otherwise HOLD."
         if label["method"] == "vol_adjusted" else
         f"- Labels: BUY / SELL when the forward return is beyond ± the fixed threshold {label['fixed_thresholds']}."),
        f"- Horizons: {cfg['task']['horizons']} trading days; primary: {primary}.",
        "",
        "## 3. Leakage prevention",
        "",
        f"- Walk-forward folds of {splits['test_months']} months, expanding training window, "
        f"{splits['validation_months']}-month validation tail used for all tuning.",
        "- Rows whose label window reaches the next segment are purged, plus an embargo of h trading days.",
        "- Scaling and all other preprocessing are fitted inside each model on fitting rows only.",
        f"- Data on or after {splits['holdout_start']} is removed before features are computed unless the "
        "holdout is explicitly unlocked.",
        "- Automated tests cover: features unchanged when future data is removed, labels unaffected by "
        "prices outside their window, purging at every boundary, the holdout lock, scaler isolation, "
        "trade timing, and causal construction of Jev's state and examples.",
        "",
    ]

    for segment, seg in metrics["segments"].items():
        horizons = sorted(seg, key=int)
        out += [f"## 4. Classification results ({segment} folds)", ""]
        for h in horizons:
            block = seg[h]
            out += [f"### {h}-day horizon" + (" (primary)" if int(h) == primary else ""), "",
                    f"{block['n_observations']:,} test observations on {block['n_dates']:,} dates, "
                    f"{block['first_date']} to {block['last_date']}. Reference traditional classifier "
                    f"(chosen on validation data): **{block['reference_classifier']}**.", ""]
            rows = []
            for name, m in sorted(block["classification"].items(), key=lambda kv: -kv[1]["macro_f1"]):
                dist = m["predicted_distribution"]
                rows.append([name, fmt(m["macro_f1"]), fmt(m["balanced_accuracy"]), fmt(m["accuracy"]),
                             fmt(m.get("log_loss")), fmt(m.get("brier")), fmt(m.get("ece")),
                             fmt(m["directional_hit_rate"]),
                             "/".join(f"{dist[c] * 100:.0f}" for c in CLASS_NAMES),
                             fmt(m["no_prediction_rate"], pct=True)])
            out += [table(["Model", "Macro-F1", "Bal. acc.", "Accuracy", "Log loss", "Brier", "ECE",
                           "Dir. hit rate", "Pred. S/H/B %", "No pred."], rows), ""]
            any_model = next(iter(block["classification"].values()))
            true = any_model["true_distribution"]
            out += ["True class distribution: " + ", ".join(f"{c} {true[c] * 100:.1f}%" for c in CLASS_NAMES)
                    + ". Log loss, Brier and ECE are shown only for models with real probabilities; "
                    "trading rules have none. Directional hit rate counts only rows where both the "
                    "prediction and the outcome are BUY or SELL.", ""]

            rows = []
            for name, m in block["classification"].items():
                rows.append([name] + [fmt(m["precision"][c]) for c in CLASS_NAMES]
                            + [fmt(m["recall"][c]) for c in CLASS_NAMES])
            out += ["Per-class precision and recall:", "",
                    table(["Model"] + [f"P {c}" for c in CLASS_NAMES] + [f"R {c}" for c in CLASS_NAMES], rows), ""]

            if int(h) == primary:
                out += ["Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):", ""]
                for name, m in block["classification"].items():
                    out += [f"`{name}`", "", table(["True", "SELL", "HOLD", "BUY", "none"], [
                        [CLASS_NAMES[i]] + [f"{v:,}" for v in row] for i, row in enumerate(m["confusion_matrix"])
                    ]), ""]
                folds = sorted({f for m in block["classification"].values() for f in m["by_fold"]}, key=int)
                out += ["Macro-F1 by walk-forward fold:", "", table(["Model"] + [f"Fold {f}" for f in folds], [
                    [name] + [fmt(m["by_fold"].get(f)) for f in folds] for name, m in block["classification"].items()
                ]), ""]
                regimes = sorted({r for m in block["classification"].values() for r in m["by_regime"]})
                out += ["Macro-F1 by market regime:", "", table(["Model"] + regimes, [
                    [name] + [fmt(m["by_regime"].get(r)) for r in regimes] for name, m in block["classification"].items()
                ]), ""]
                out += ["Macro-F1 across individual stocks:", "", table(
                    ["Model", "10th pct", "Median", "90th pct", "Stocks"],
                    [[name, fmt(m["by_stock"]["p10"]), fmt(m["by_stock"]["median"]), fmt(m["by_stock"]["p90"]),
                      m["by_stock"]["n_stocks"]] for name, m in block["classification"].items()]), ""]

        out += [f"## 5. Statistical uncertainty ({segment} folds)", "",
                f"Paired stationary block bootstrap over dates, {cfg['stats']['n_boot']:,} resamples. "
                "Differences are in pooled macro-F1 (first model minus second). Holm adjustment is applied "
                "within each table. A p-value here describes this sample; it does not account for choices "
                "made across separate runs.", ""]
        for h in horizons:
            block = seg[h]
            out += [f"### {h}-day horizon (mean block {block['block_length_days']} days)", ""]
            for title, key in (("Any skill: each model against stratified random guessing", "skill_vs_stratified_random"),
                               ("Jev arms against the reference traditional classifier", "jev_vs_reference"),
                               ("Does adding Jev outputs improve GBT?", "jev_plus_controlled_vs_gbt")):
                items = block["comparisons"][key]
                out += [f"{title}:", ""]
                out += [table(["Comparison", "Difference", "95% interval", "p", "p (Holm)"], _comparison_rows(items))
                        if items else "_No comparison available: the Jev arms have not been run._", ""]

        out += [f"## 6. Trading performance net of costs ({segment} folds)", "",
                f"Mode `{cfg['backtest']['mode']}`: BUY names are held equally weighted (cap "
                f"{cfg['backtest']['max_weight'] * 100:.0f}% per name per tranche), SELL and HOLD names are not held. "
                f"Cost {cfg['backtest']['cost_bps_per_side']} bps per unit of turnover. Cash earns nothing and the "
                "Sharpe ratio uses a zero risk-free rate. `always_buy` holds every stock through the same "
                "engine and is the fair passive comparison.", ""]
        for h in horizons:
            block = seg[h]
            rows = []
            for name, t in sorted(block["trading"].items(), key=lambda kv: -(kv[1].get("sharpe") or 0)):
                rows.append([name, fmt(t.get("cumulative_net_return"), pct=True), fmt(t.get("cagr"), pct=True),
                             fmt(t.get("sharpe"), 2), fmt(t.get("sortino"), 2), fmt(t.get("max_drawdown"), pct=True),
                             fmt(t.get("calmar"), 2), fmt(t.get("annual_turnover"), 1),
                             fmt(t.get("mean_exposure"), pct=True), fmt(t.get("sharpe_cost_2bps"), 2),
                             fmt(t.get("sharpe_cost_10bps"), 2), fmt(t.get("sharpe_long_short"), 2)])
            out += [f"### {h}-day horizon", "",
                    table(["Strategy", "Net return", "CAGR", "Sharpe", "Sortino", "Max DD", "Calmar",
                           "Turnover/yr", "Exposure", "Sharpe @2bps", "Sharpe @10bps", "Sharpe L/S"], rows), "",
                    "Mean realised forward return by predicted signal:", "",
                    table(["Model", "Pred. SELL", "Pred. HOLD", "Pred. BUY"], [
                        [name] + [fmt(m[f"mean_fwd_ret_pred_{c}"], pct=True, pct_digits=3) for c in CLASS_NAMES]
                        for name, m in block["classification"].items()]), "",
                    "Net Sharpe difference against `always_buy`:", "",
                    table(["Comparison", "Difference", "95% interval", "p", "p (Holm)"],
                          _comparison_rows(block["trading_comparisons"]["vs_always_buy"])), ""]
            jev_items = block["trading_comparisons"]["jev_vs_reference"]
            if jev_items:
                out += ["Net Sharpe difference, Jev arms against the reference classifier:", "",
                        table(["Comparison", "Difference", "95% interval", "p", "p (Holm)"],
                              _comparison_rows(jev_items)), ""]

    out += ["## 7. Runtime and cost", "",
            table(["Model", "Fits", "Configs per fit", "Fit seconds", "Predict seconds", "Test rows"], [
                [name, r["fits"], r["configs_per_fit"], fmt(r["fit_seconds"], 1), fmt(r["predict_seconds"], 1),
                 f"{r['test_rows']:,}"] for name, r in metrics["runtime"].items()]), "",
            "Traditional models run locally at no marginal cost. Jev API status: "
            + "; ".join(f"{k}: {v}" for k, v in metrics["jev_status"].items()) + ".", ""]
    if metrics["not_run"]:
        out += ["Models that did not run:", ""] + [
            f"- `{name}` ({JEV_ARMS.get(name, name)}): {reason}" for name, reason in metrics["not_run"].items()] + [""]

    out += ["## 8. Limitations", "",
            "- Survivorship and hindsight bias in the stock list.",
            "- Free vendor data: adjusted prices are revised after later corporate actions; opening prints "
            "may differ from achievable auction fills.",
            "- Jev's training data and knowledge cutoff are undisclosed, so its historical results may "
            "reflect recall. Its state is anonymised to limit this, which cannot be proven sufficient.",
            "- Jev is a hosted model that can change or be withdrawn; results are tied to the pinned version.",
            "- Trading simulation ignores weight drift, market impact, borrow availability and taxes.",
            "- Volatility-scaled labels make the size of a move partly predictable from volatility "
            "clustering. A model can score well on macro-F1 without predicting direction, so read macro-F1 "
            "together with the directional hit rate and the trading results.",
            "",
            "## 9. Conclusion", ""] + conclusion(metrics, cfg) + [""]
    return "\n".join(out)
