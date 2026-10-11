"""Render a Markdown report from a run's metrics and manifest. Numbers come only from saved results."""
from __future__ import annotations

import statistics

from . import CLASS_NAMES
from .backtest import names_held, trade_rules
from .providers import PROVIDERS, describe_arm



def rule_descriptions(cfg: dict) -> dict[str, str]:
    """One plain sentence per portfolio rule in this configuration."""
    n = len(cfg["data"]["tickers"])
    out = {}
    for rule in trade_rules(cfg):
        held = names_held(cfg, rule)
        if rule == "buy_names":
            out[rule] = "BUY-names portfolio: hold the assets labelled BUY, the rest in cash"
        else:
            kind = "Ranking portfolio" if rule == "rank" else "Concentrated ranking portfolio (declared check)"
            out[rule] = f"{kind}: each day hold the top {held} of {n} assets by score, fully invested"
    return out


COMPARISON_HEADERS = ["Comparison", "Difference", "95% interval", "p", "p (Holm)"]


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


def _comparison_rows(items: list[dict], digits: int = 4) -> list[list]:
    rows = []
    for c in items:
        if "skipped" in c:
            rows.append([f"{c['a']} vs {c['b']}", "skipped", c["skipped"], "", ""])
        else:
            rows.append([f"{c['a']} vs {c['b']}", fmt(c["diff"], digits),
                         f"{fmt(c['ci_low'], digits)} to {fmt(c['ci_high'], digits)}",
                         fmt(c["p_value"]), fmt(c.get("p_holm"))])
    return rows


def _block(seg: dict, horizon: int) -> dict:
    return seg[horizon] if horizon in seg else seg[str(horizon)]


def verdict_segment(metrics: dict) -> str:
    """The segment the verdict rests on: every fold pooled when available."""
    return "all" if "all" in metrics["segments"] else next(iter(metrics["segments"]))


def detectable_effect(comparisons: list[dict]) -> dict | None:
    """Typical interval half-width and the difference detectable with 80% power at the 5% level."""
    widths = [(c["ci_high"] - c["ci_low"]) / 2 for c in comparisons if "diff" in c]
    if not widths:
        return None
    half = statistics.median(widths)
    return {"half_width": half, "mde_80": half * 2.8 / 1.96, "n": len(widths)}


def judge(c: dict, margin: float, alpha: float) -> str:
    if c["diff"] >= margin and c["ci_low"] > 0 and c.get("p_holm", 1.0) < alpha:
        return "better"
    if c["ci_high"] < 0 and c.get("p_holm", 1.0) < alpha:
        return "worse"
    return "no reliable difference"


def _describe(c: dict, margin: float, alpha: float) -> str:
    return (f"`{c['a']}` vs `{c['b']}`: {c['diff']:+.2f} (95% interval {c['ci_low']:+.2f} to {c['ci_high']:+.2f}, "
            f"Holm p {fmt(c.get('p_holm'))}), **{judge(c, margin, alpha)}**")


def conclusion(metrics: dict, cfg: dict) -> list[str]:
    """A direct verdict derived from the predefined decision rule. Trading is the primary test."""
    primary, rule = cfg["task"]["primary_horizon"], cfg["backtest"]["primary_rule"]
    stats = cfg["stats"]
    margin, alpha = float(stats["practical_margin_sharpe"]), float(stats["alpha"])
    segment = verdict_segment(metrics)
    block = _block(metrics["segments"][segment], primary)
    trading = block["trading_comparisons"][rule]
    lines = []
    if segment != "all":
        lines.append("**Partial window.** This run excludes the last two years of folds, so it is not the "
                     "verdict run. Nothing below is a final finding.\n")
    ran = {p: g for p, g in trading["providers"].items() if any("diff" in c for c in g["vs_reference"])}
    if not ran:
        status = "; ".join(sorted(set(metrics["external_status"].values())))
        return lines + [
            f"- **Trading performance (primary):** insufficient evidence. No external classifier has been run ({status}).",
            "- **Classification performance:** insufficient evidence, for the same reason.",
            "- **Operational efficiency:** insufficient evidence. No external classifier's runtime or cost has been measured.",
            "- **Overall:** the evidence does not yet bear on whether Jev outperforms traditional models for trading.",
        ]

    held = {c["a"]: c for c in trading["vs_buy_and_hold"] if "diff" in c}
    for provider, groups in ran.items():
        label = PROVIDERS[provider]["label"]
        lines.append(f"**{label}**, {primary}-day horizon, net Sharpe ratio of the "
                     f"{'BUY-names' if rule == 'buy_names' else 'ranking'} portfolio. A difference counts as better only "
                     f"if it is at least {margin:+.2f}, its interval excludes zero and Holm-adjusted p < {alpha}.\n")
        alone = [c for c in groups["vs_reference"] if "diff" in c and "_signal_" in c["a"]]
        lines.append(f"- **Used alone, against the traditional classifier `{block['reference_classifier']}`:**")
        lines += [f"  - {_describe(c, margin, alpha)}" for c in alone] or ["  - not run"]
        lines.append("- **Used alone, against equal-weight buy and hold:**")
        lines += [f"  - {_describe(held[c['a']], margin, alpha)}" for c in alone if c["a"] in held] or ["  - not run"]
        augmented = [c for c in groups["augmented_vs_gbt"] if "diff" in c]
        lines.append("- **Added to a traditional classifier (GBT with its outputs against GBT without):**")
        lines += [f"  - {_describe(c, margin, alpha)}" for c in augmented] or ["  - not run"]
        versus = [c for c in groups["alone_vs_augmented"] if "diff" in c]
        lines.append("- **Used alone against used as an added input:**")
        lines += [f"  - {_describe(c, margin, alpha)}" for c in versus] or ["  - not run"]
        f1_margin = float(stats["practical_margin_macro_f1"])
        cls = [c for c in block["comparisons"]["providers"].get(provider, {}).get("vs_reference", []) if "diff" in c]
        lines.append(f"- **Classification (diagnostic, macro-F1, margin {f1_margin:+.2f}):**")
        lines += [f"  - {_describe(c, f1_margin, alpha)}" for c in cls] or ["  - not run"]
        better = [c["a"] for c in alone if judge(c, margin, alpha) == "better"
                  and c["a"] in held and judge(held[c["a"]], margin, alpha) == "better"]
        lines.append("- **Overall:** " + (
            f"the thesis is supported for {', '.join(better)}: it beats both the traditional classifier and buy and hold."
            if better else
            "the thesis is not supported. No arm used alone reliably beats both the traditional classifier and "
            "buy and hold. Check the detectable-effect section before reading this as evidence of no difference."))
        lines.append("")
    lines.append("- **Operational efficiency:** see the runtime and cost table; reported, not tested.")
    return lines


def _trading_table(stats: dict, rule: str) -> str:
    headers = ["Strategy", "Net return", "Per year", "Sharpe", "Sortino", "Max DD", "Calmar", "Turnover/yr", "Invested",
               "Alpha/yr (95% interval)", "Beta", "Sharpe @2bps", "Sharpe @10bps", "Sharpe L/S"]
    if rule == "buy_names":
        headers += ["Sharpe, same exposure spread evenly", "Selection return/yr"]
    rows = []
    for name, t in sorted(stats.items(), key=lambda kv: -(kv[1].get("sharpe") or 0)):
        alpha = fmt(t.get("alpha"), pct=True)
        if t.get("alpha_ci_low") is not None:
            alpha += f" ({fmt(t['alpha_ci_low'], pct=True)} to {fmt(t['alpha_ci_high'], pct=True)})"
        row = [name, fmt(t.get("cumulative_net_return"), pct=True), fmt(t.get("cagr"), pct=True),
               fmt(t.get("sharpe"), 2), fmt(t.get("sortino"), 2), fmt(t.get("max_drawdown"), pct=True),
               fmt(t.get("calmar"), 2), fmt(t.get("annual_turnover"), 1), fmt(t.get("mean_exposure"), pct=True),
               alpha, fmt(t.get("beta"), 2), fmt(t.get("sharpe_cost_2bps"), 2), fmt(t.get("sharpe_cost_10bps"), 2),
               fmt(t.get("sharpe_long_short"), 2)]
        if rule == "buy_names":
            row += [fmt(t.get("sharpe_exposure_matched"), 2), fmt(t.get("selection_return_per_year"), pct=True)]
        rows.append(row)
    return table(headers, rows)


def render_report(metrics: dict, manifest: dict, cfg: dict) -> str:
    primary, primary_rule = cfg["task"]["primary_horizon"], cfg["backtest"]["primary_rule"]
    label, splits, data, bt = cfg["task"]["label"], cfg["splits"], manifest.get("dataset", {}), cfg["backtest"]
    rule_text = rule_descriptions(cfg)
    other_rules = [r for r in rule_text if r != primary_rule]
    out: list[str] = [f"# Experiment report: {manifest['run_name']}", ""]
    if cfg["experiment_id"] == "smoke":
        out += ["> **Smoke run.** A small configuration used to validate the pipeline end to end. "
                "These numbers are not experimental findings.", ""]
    out += [
        f"Generated {manifest['finished_at_utc']} from commit `{manifest['git_commit']}`, "
        f"config `{manifest['config_hash']}`, dataset `{str(data.get('sha256', 'n/a'))[:12]}`. "
        f"Final two years of folds included: **{manifest['holdout_unlocked']}**.",
        "",
        "## 1. Research question and method",
        "",
        "Can Jev, used as a classifier, outperform traditional models for trading? Each model's "
        "predictions are turned into a portfolio by the same rule and compared on net Sharpe ratio with a "
        "traditional classifier, with equal-weight buy and hold, and with a traditional classifier that is "
        "given Jev's outputs as extra inputs. Every model is fitted and scored on identical observations in "
        "a purged walk-forward design. Classification metrics are reported as diagnostics. The full protocol "
        "and decision rule are in `EXPERIMENT_MEMORY.md`.",
        "",
        "## 2. Data and labels",
        "",
        f"- Universe: `{cfg['data']['universe_name']}`, {data.get('tickers_obtained', 'n/a')} tickers obtained "
        f"including the market proxy {cfg['data']['market_ticker']}; failed downloads: "
        f"{data.get('tickers_failed') or 'none'}.",
        f"- Source: {cfg['data']['source']} daily bars, {data.get('first_date', 'n/a')} to "
        f"{data.get('last_date', 'n/a')}, downloaded {data.get('downloaded_at_utc', 'n/a')}.",
        "- The universe is a fixed list chosen with hindsight, not point-in-time membership. Survivorship "
        "bias inflates every absolute return here, including buy and hold of the same assets.",
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
        "full-window run is explicitly requested.",
        "- Automated tests cover: features unchanged when future data is removed, labels unaffected by "
        "prices outside their window, purging at every boundary, the data lock, scaler isolation, "
        "trade timing, and causal construction of the state and examples sent to external classifiers.",
        "",
        "## 4. Trading results (primary test)",
        "",
        f"- Primary rule: {rule_text[primary_rule]}.",
        *[f"- Also reported: {rule_text[r]}." for r in other_rules],
        f"- Positions open at the next open and are held for h days in h daily tranches. Cost "
        f"{bt['cost_bps_per_side']} bps per unit of turnover. Idle cash earns "
        f"{'the Treasury bill rate' if bt['risk_free'] == 'tbill' else 'nothing'}; Sharpe and Sortino use returns "
        "in excess of that rate.",
        "- `always_buy` holds every asset equally through the same engine and costs. It is the buy-and-hold "
        f"benchmark. `market_buy_and_hold` is {cfg['data']['market_ticker']}, shown for context only.",
        "- Models without scores of their own (`majority`, `stratified_random`) hold a random selection under "
        "the ranking rule, which is that rule's no-skill reference.",
        "- Alpha and beta are measured against the market proxy. Sharpe L/S is the long-short version of the rule.",
        "",
    ]

    order = sorted(metrics["segments"], key=lambda s: {"all": 0, "dev": 1, "holdout": 2}.get(s, 3))
    segment_names = {"all": "all folds", "dev": "folds before the final two years", "holdout": "final two years"}
    for segment in order:
        seg = metrics["segments"][segment]
        horizons = sorted(seg, key=int)
        for rule in (primary_rule, *other_rules):
            tag = "primary rule" if rule == primary_rule else f"`{rule}` rule"
            out += [f"### {segment_names.get(segment, segment).capitalize()}, {tag}", "", f"{rule_text[rule]}.", ""]
            for h in horizons:
                block = seg[h]
                comp = block["trading_comparisons"][rule]
                out += [f"**{h}-day horizon" + (" (primary)" if int(h) == primary else "") + "**, "
                        f"{block['first_date']} to {block['last_date']}", "",
                        _trading_table(block["trading"][rule], rule), "",
                        "Net Sharpe difference against equal-weight buy and hold:", "",
                        table(COMPARISON_HEADERS, _comparison_rows(comp["vs_buy_and_hold"], 2)), ""]
                for provider, groups in comp["providers"].items():
                    for title, key in (("against the reference traditional classifier", "vs_reference"),
                                       ("added to GBT, against GBT alone", "augmented_vs_gbt"),
                                       ("used alone against used as an added input", "alone_vs_augmented")):
                        if groups[key]:
                            out += [f"{PROVIDERS[provider]['label']}, {title} (net Sharpe difference):", "",
                                    table(COMPARISON_HEADERS, _comparison_rows(groups[key], 2)), ""]

    out += ["## 5. What this run can detect", ""]
    vseg = verdict_segment(metrics)
    power = detectable_effect(_block(metrics["segments"][vseg], primary)["trading_comparisons"][primary_rule]["vs_buy_and_hold"])
    if power:
        out += [f"At the {primary}-day horizon on {segment_names.get(vseg, vseg)}, the 95% interval on a net "
                f"Sharpe difference is typically ±{power['half_width']:.2f} (median of {power['n']} comparisons). "
                f"A true difference smaller than about {power['mde_80']:.2f} would be missed more often than one "
                "time in five, so a result of \"no reliable difference\" does not show that two strategies are "
                f"equal. The smallest difference treated as worth acting on is {cfg['stats']['practical_margin_sharpe']}.", ""]
    else:
        out += ["Not available for this run.", ""]

    for segment in order:
        seg = metrics["segments"][segment]
        horizons = sorted(seg, key=int)
        out += [f"## 6. Classification diagnostics ({segment_names.get(segment, segment)})", ""]
        for h in horizons:
            block = seg[h]
            out += [f"### {h}-day horizon" + (" (primary)" if int(h) == primary else ""), "",
                    f"{block['n_observations']:,} test observations on {block['n_dates']:,} dates. Reference "
                    f"traditional classifier (chosen on validation data): **{block['reference_classifier']}**.", ""]
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
            true = next(iter(block["classification"].values()))["true_distribution"]
            out += ["True class distribution: " + ", ".join(f"{c} {true[c] * 100:.1f}%" for c in CLASS_NAMES)
                    + ". Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, "
                    "Brier and ECE are shown only for models with real probabilities. Directional hit rate "
                    "counts only rows where both the prediction and the outcome are BUY or SELL.", ""]
            out += ["Per-class precision and recall, and mean realised forward return by predicted signal:", "",
                    table(["Model"] + [f"P {c}" for c in CLASS_NAMES] + [f"R {c}" for c in CLASS_NAMES]
                          + [f"Ret. {c}" for c in CLASS_NAMES], [
                        [name] + [fmt(m["precision"][c]) for c in CLASS_NAMES] + [fmt(m["recall"][c]) for c in CLASS_NAMES]
                        + [fmt(m[f"mean_fwd_ret_pred_{c}"], pct=True, pct_digits=3) for c in CLASS_NAMES]
                        for name, m in block["classification"].items()]), ""]
            comp = block["comparisons"]
            out += ["Macro-F1 difference against random guessing (paired block bootstrap over dates):", "",
                    table(COMPARISON_HEADERS, _comparison_rows(comp["skill_vs_stratified_random"])), ""]
            for provider, groups in comp["providers"].items():
                if groups["vs_reference"]:
                    out += [f"{PROVIDERS[provider]['label']} against the reference classifier (macro-F1 difference):", "",
                            table(COMPARISON_HEADERS, _comparison_rows(groups["vs_reference"])), ""]

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
                out += ["Macro-F1 across individual assets:", "", table(
                    ["Model", "10th pct", "Median", "90th pct", "Assets"],
                    [[name, fmt(m["by_stock"]["p10"]), fmt(m["by_stock"]["median"]), fmt(m["by_stock"]["p90"]),
                      m["by_stock"]["n_stocks"]] for name, m in block["classification"].items()]), ""]

    out += ["## 7. Runtime and cost", "",
            table(["Model", "Fits", "Configs per fit", "Fit seconds", "Predict seconds", "Test rows"], [
                [name, r["fits"], r["configs_per_fit"], fmt(r["fit_seconds"], 1), fmt(r["predict_seconds"], 1),
                 f"{r['test_rows']:,}"] for name, r in metrics["runtime"].items()]), "",
            "Traditional models run locally at no marginal cost. External classifier status: "
            + "; ".join(f"{k}: {v}" for k, v in metrics["external_status"].items()) + ".", ""]
    if metrics["not_run"]:
        out += ["Models that did not run:", ""] + [
            f"- `{name}` ({describe_arm(name)}): {reason}" for name, reason in metrics["not_run"].items()] + [""]

    out += ["## 8. Limitations", "",
            "- Survivorship and hindsight bias in the asset list.",
            "- Free vendor data: adjusted prices are revised after later corporate actions; opening prints "
            "may differ from achievable auction fills.",
            "- Jev's training data and knowledge cutoff are undisclosed, so its historical results may "
            "reflect recall. Its state is anonymised to limit this, which cannot be proven sufficient.",
            "- Jev is a hosted model that can change or be withdrawn; results are tied to the pinned version.",
            "- Trading simulation ignores weight drift, market impact, borrow availability and taxes.",
            "- Models are tuned for classification (validation macro-F1), not for trading performance.",
            "- Volatility-scaled labels make the size of a move partly predictable from volatility "
            "clustering, so macro-F1 can rise without any ability to predict direction.",
            "",
            "## 9. Conclusion", ""] + conclusion(metrics, cfg) + [""]
    return "\n".join(out)
