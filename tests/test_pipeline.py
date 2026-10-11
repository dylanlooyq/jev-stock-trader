"""End-to-end run on synthetic data: outputs, report content and the holdout switch."""
import json

import pandas as pd
import pytest

from jevbench.run import main, run_benchmark


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
    assert set(block["classification"]) == {"majority", "stratified_random", "logreg", "random_forest", "gbt",
                                            "momentum_rule", "ma_cross_rule"}
    assert block["comparisons"]["jev_vs_reference"] == []
    assert len(block["comparisons"]["skill_vs_stratified_random"]) == 5
    assert {"always_buy", "market_buy_and_hold"} <= set(block["trading"])
    assert block["trading"]["majority"]["positions_opened"] == 0 or block["classification"]["majority"][
        "predicted_distribution"]["BUY"] == 1.0
    assert len(metrics["not_run"]) == 6 and all(k.startswith("jev") for k in metrics["not_run"])

    preds = pd.read_parquet(out_dir / "predictions.parquet")
    assert preds["date"].max() < pd.Timestamp(cfg["splits"]["holdout_start"])
    assert {"y_true", "fwd_ret", "pred", "p_sell", "p_hold", "p_buy", "fold", "segment"} <= set(preds.columns)

    report = (out_dir / "report.md").read_text(encoding="utf-8")
    assert "insufficient evidence" in report
    assert "development-fold results" in report
    assert "Holdout unlocked: **False**" in report

    registry = (tmp_path / "results" / "registry.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(registry) == 1 and json.loads(registry[0])["run_name"] == "unit"

    with pytest.raises(FileExistsError):
        run_benchmark(cfg, "unit", prices=prices, results_dir=tmp_path / "results")


def test_unlocked_run_reports_dev_and_holdout_separately(cfg, prices, tmp_path):
    out = run_benchmark(cfg, "unlocked", unlock_holdout=True, prices=prices, results_dir=tmp_path / "results")
    assert set(out["metrics"]["segments"]) == {"dev", "holdout"}
    preds = pd.read_parquet(out["out_dir"] / "predictions.parquet")
    holdout_start = pd.Timestamp(cfg["splits"]["holdout_start"])
    assert (preds.loc[preds["segment"] == "holdout", "date"] >= holdout_start).all()
    assert (preds.loc[preds["segment"] == "dev", "date"] < holdout_start).all()


def test_holdout_cannot_be_unlocked_from_the_cli_without_confirmation(capsys):
    with pytest.raises(SystemExit):
        main(["benchmark", "--unlock-holdout"])
    assert "confirm-design-frozen" in capsys.readouterr().err
