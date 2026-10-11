"""End-to-end run on synthetic data: outputs, report content and the full-window switch."""
import json

import pandas as pd
import pytest

from jevbench.run import main, run_benchmark

BASELINES = {"majority", "stratified_random", "logreg", "random_forest", "gbt", "momentum_rule", "ma_cross_rule"}


def test_locked_run_writes_everything_and_draws_no_conclusion_about_jev(cfg, prices, tmp_path):
    out = run_benchmark(cfg, "unit", prices=prices, results_dir=tmp_path / "results")
    out_dir = out["out_dir"]
    for name in ("predictions.parquet", "metrics.json", "manifest.json", "report.md", "config.yaml",
                 "fit_log.csv", "folds.csv", "per_stock_macro_f1.csv", "daily_returns.parquet"):
        assert (out_dir / name).exists(), name

    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert list(metrics["segments"]) == ["dev"]
    block = metrics["segments"]["dev"]["5"]
    assert block["reference_classifier"] in ("logreg", "random_forest", "gbt")
    assert set(block["classification"]) == BASELINES
    assert block["comparisons"]["providers"] == {}
    assert len(block["comparisons"]["skill_vs_stratified_random"]) == 5

    assert list(block["trading"]) == ["rank", "rank_check", "buy_names"]
    for rule in block["trading"]:
        stats = block["trading"][rule]
        assert set(stats) == BASELINES | {"always_buy", "market_buy_and_hold"}
        assert len(block["trading_comparisons"][rule]["vs_buy_and_hold"]) == 5
        assert block["trading_comparisons"][rule]["providers"] == {}
        assert {"alpha", "beta", "sharpe_cost_10bps", "sharpe_long_short"} <= set(stats["gbt"])
    rank = block["trading"]["rank"]
    assert rank["always_buy"]["mean_exposure"] > 0.95               # buy and hold is fully invested
    assert rank["gbt"]["mean_exposure"] > 0.95                      # and so is the ranking portfolio
    assert block["trading"]["buy_names"]["majority"]["positions_opened"] == 0   # always HOLD never trades
    assert rank["majority"] == rank["stratified_random"] or rank["majority"]["positions_opened"] > 0
    assert len(metrics["not_run"]) == 6 and all(k.startswith("jev") for k in metrics["not_run"])

    preds = pd.read_parquet(out_dir / "predictions.parquet")
    assert preds["date"].max() < pd.Timestamp(cfg["splits"]["holdout_start"])
    assert {"y_true", "fwd_ret", "pred", "score", "p_sell", "p_hold", "p_buy", "fold", "segment"} <= set(preds.columns)
    daily = pd.read_parquet(out_dir / "daily_returns.parquet")
    assert set(daily["rule"]) == {"rank", "rank_check", "buy_names", "passive"}

    report = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "insufficient evidence" in report
    assert "Partial window" in report
    assert "Trading results (primary test)" in report
    assert "What this run can detect" in report and "would be missed" in report

    registry = (tmp_path / "results" / "registry.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(registry) == 1 and json.loads(registry[0])["run_name"] == "unit"

    with pytest.raises(FileExistsError):
        run_benchmark(cfg, "unit", prices=prices, results_dir=tmp_path / "results")


def test_full_window_run_pools_all_folds_for_the_verdict(cfg, prices, tmp_path):
    out = run_benchmark(cfg, "full", unlock_holdout=True, prices=prices, results_dir=tmp_path / "results")
    segments = out["metrics"]["segments"]
    assert set(segments) == {"all", "dev", "holdout"}
    n = {name: segments[name]["5"]["n_observations"] for name in segments}
    assert n["all"] == n["dev"] + n["holdout"]
    preds = pd.read_parquet(out["out_dir"] / "predictions.parquet")
    holdout_start = pd.Timestamp(cfg["splits"]["holdout_start"])
    assert (preds.loc[preds["segment"] == "holdout", "date"] >= holdout_start).all()
    assert (preds.loc[preds["segment"] == "dev", "date"] < holdout_start).all()
    report = (out["out_dir"] / "report.md").read_text(encoding="utf-8")
    assert "Partial window" not in report and "All folds, primary rule" in report


def test_full_window_cannot_be_run_from_the_cli_without_confirmation(capsys):
    with pytest.raises(SystemExit):
        main(["benchmark", "--unlock-holdout"])
    assert "confirm-design-frozen" in capsys.readouterr().err


def test_local_backtest_page_is_self_contained(cfg, prices, tmp_path):
    from jevbench.visualise import build_payload, write_page

    out = run_benchmark(cfg, "page", prices=prices, results_dir=tmp_path / "results")
    payload = build_payload(out["out_dir"])
    assert payload["defaults"] == {"segment": "dev", "rule": "rank", "horizon": 5}
    assert payload["rule_labels"] == {"rank": "Top 2 of 6 by score", "rank_check": "Top 1 of 6 by score",
                                      "buy_names": "BUY names only"}
    view = payload["views"]["dev|rank|5"]
    assert {s["id"] for s in view["strategies"]} == BASELINES | {"always_buy", "market_buy_and_hold"}
    assert all(len(v) == len(view["dates"]) for v in view["growth"].values())
    # The drawn growth line ends at the same value as the stored statistic.
    stored = out["metrics"]["segments"]["dev"]["5"]["trading"]["rank"]["gbt"]["cumulative_net_return"]
    assert view["growth"]["gbt"][-1] - 1 == pytest.approx(stored, abs=1e-4)
    assert len(view["diffs"]) == 5 and view["power"]["mde_80"] > view["power"]["half_width"] > 0

    # Holdings are shares of the portfolio: a fully invested ranking rule sums to 100%.
    held = view["holdings"]
    assert len(held["gbt"]) == len(payload["tickers"]) == 6
    assert sum(held["gbt"]) == pytest.approx(100, abs=1.0) and sum(held["always_buy"]) == pytest.approx(100, abs=1.0)
    assert max(payload["views"]["dev|rank_check|5"]["holdings"]["gbt"]) <= 100

    page = write_page(out["out_dir"]).read_text(encoding="utf-8")
    assert "/*__DATA__*/null" not in page and '"name":"page"' in page
    assert "http://" not in page.replace("http://www.w3.org/2000/svg", "") and "https://" not in page   # opens offline
