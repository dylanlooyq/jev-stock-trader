"""Metric calculations and the block bootstrap."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import balanced_accuracy_score, f1_score, log_loss, precision_score, recall_score

from jevbench import NO_PREDICTION
from jevbench.evaluate import (confusion_matrix, directional_metrics, evaluate_predictions, macro_f1_from_cm,
                               metrics_from_cm, probability_metrics)
from jevbench.stats import (holm, paired_macro_f1_bootstrap, paired_sharpe_bootstrap, per_date_confusions,
                            stationary_bootstrap_indices)


@pytest.fixture()
def sample():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 3, 2000)
    pred = np.where(rng.random(2000) < 0.5, y, rng.integers(0, 3, 2000))
    return y, pred


def test_metrics_match_scikit_learn(sample):
    y, pred = sample
    m = metrics_from_cm(confusion_matrix(y, pred))
    assert m["macro_f1"] == pytest.approx(f1_score(y, pred, average="macro"))
    assert m["balanced_accuracy"] == pytest.approx(balanced_accuracy_score(y, pred))
    assert m["accuracy"] == pytest.approx((y == pred).mean())
    precision = precision_score(y, pred, average=None)
    recall = recall_score(y, pred, average=None)
    for i, name in enumerate(("SELL", "HOLD", "BUY")):
        assert m["precision"][name] == pytest.approx(precision[i], abs=1e-6)
        assert m["recall"][name] == pytest.approx(recall[i], abs=1e-6)
    assert np.array(m["confusion_matrix"]).sum() == len(y)


def test_macro_f1_counts_a_never_predicted_class_as_zero():
    y = np.array([0, 1, 2, 1, 1, 0])
    pred = np.ones(6, dtype=int)
    expected = f1_score(y, pred, labels=[0, 1, 2], average="macro", zero_division=0)
    assert float(macro_f1_from_cm(confusion_matrix(y, pred))) == pytest.approx(expected)


def test_a_failed_prediction_counts_as_a_miss(sample):
    y, pred = sample
    base = metrics_from_cm(confusion_matrix(y, pred))
    failed = pred.copy()
    correct = np.flatnonzero(pred == y)[:200]
    failed[correct] = NO_PREDICTION
    m = metrics_from_cm(confusion_matrix(y, failed))
    assert m["no_prediction_rate"] == pytest.approx(200 / len(y))
    assert m["macro_f1"] < base["macro_f1"]
    assert m["accuracy"] == pytest.approx(base["accuracy"] - 200 / len(y))


def test_probability_metrics_match_definitions():
    y = np.array([0, 1, 2, 2])
    proba = np.array([[0.7, 0.2, 0.1], [0.2, 0.5, 0.3], [0.1, 0.3, 0.6], [0.5, 0.3, 0.2]])
    m = probability_metrics(y, proba)
    assert m["log_loss"] == pytest.approx(log_loss(y, proba, labels=[0, 1, 2]))
    assert m["brier"] == pytest.approx(((proba - np.eye(3)[y]) ** 2).sum(axis=1).mean())
    assert m["proba_coverage"] == 1.0
    assert 0.0 <= m["ece"] <= 1.0


def test_rows_without_probabilities_are_excluded_and_reported():
    y = np.array([0, 1, 2, 2])
    proba = np.array([[0.7, 0.2, 0.1], [np.nan] * 3, [0.1, 0.3, 0.6], [np.nan] * 3])
    m = probability_metrics(y, proba)
    assert m["proba_coverage"] == 0.5
    assert m["log_loss"] == pytest.approx(-(np.log(0.7) + np.log(0.6)) / 2)


def test_models_without_probabilities_get_no_calibration_metrics():
    df = pd.DataFrame({"y_true": [0, 1, 2], "pred": [0, 1, 1], "fwd_ret": [-0.02, 0.0, 0.03],
                       "p_sell": np.nan, "p_hold": np.nan, "p_buy": np.nan})
    m = evaluate_predictions(df)
    assert m["proba_coverage"] == 0.0
    assert "log_loss" not in m and "brier" not in m


def test_directional_hit_rate_ignores_hold():
    y = np.array([2, 0, 2, 1, 0])
    pred = np.array([2, 2, 1, 2, 0])
    d = directional_metrics(y, pred, np.array([0.05, -0.05, 0.04, 0.0, -0.03]))
    assert d["directional_n"] == 3          # rows 0, 1, 4
    assert d["directional_hit_rate"] == pytest.approx(2 / 3)
    assert d["mean_fwd_ret_pred_BUY"] == pytest.approx(0.0)


def test_bootstrap_indices_form_blocks():
    idx = stationary_bootstrap_indices(500, 20, 50, np.random.default_rng(1))
    assert idx.shape == (50, 500) and idx.min() >= 0 and idx.max() < 500
    consecutive = (np.diff(idx, axis=1) % 500 == 1).mean()
    assert 0.90 < consecutive < 0.98        # expected 1 - 1/20 = 0.95


def _frame(y, pred, n_dates):
    dates = pd.bdate_range("2020-01-01", periods=n_dates)
    return pd.DataFrame({"date": np.repeat(dates, len(y) // n_dates), "y_true": y, "pred": pred}), dates


def test_identical_models_have_zero_difference(sample):
    y, pred = sample
    df, dates = _frame(y, pred, 200)
    cm = per_date_confusions(df, dates)
    assert cm.sum() == len(y)
    out = paired_macro_f1_bootstrap(cm, cm, 10, 200, seed=0)
    assert out["diff"] == 0 and out["ci_low"] == 0 and out["ci_high"] == 0 and out["p_value"] == 1.0


def test_bootstrap_detects_a_real_difference_and_not_a_null_one():
    rng = np.random.default_rng(3)
    y = rng.integers(0, 3, 6000)
    strong = np.where(rng.random(6000) < 0.6, y, rng.integers(0, 3, 6000))
    noise_a, noise_b = rng.integers(0, 3, 6000), rng.integers(0, 3, 6000)
    df_y, dates = _frame(y, strong, 300)
    cm_strong = per_date_confusions(df_y, dates)
    cm_a = per_date_confusions(_frame(y, noise_a, 300)[0], dates)
    cm_b = per_date_confusions(_frame(y, noise_b, 300)[0], dates)

    real = paired_macro_f1_bootstrap(cm_strong, cm_a, 10, 500, seed=0)
    assert real["ci_low"] > 0.2 and real["p_value"] < 0.01
    null = paired_macro_f1_bootstrap(cm_a, cm_b, 10, 500, seed=0)
    assert null["ci_low"] < 0 < null["ci_high"] and null["p_value"] > 0.05


def test_bootstrap_requires_identical_dates(sample):
    y, pred = sample
    cm = per_date_confusions(*_frame(y, pred, 200))
    with pytest.raises(ValueError):
        paired_macro_f1_bootstrap(cm, cm[:-1], 10, 50, seed=0)


def test_sharpe_bootstrap():
    rng = np.random.default_rng(5)
    base = rng.normal(0.0, 0.01, 1500)
    out = paired_sharpe_bootstrap(base + 0.002, base, 10, 500, seed=0)
    assert out["diff"] > 0 and out["ci_low"] > 0
    same = paired_sharpe_bootstrap(base, base, 10, 200, seed=0)
    assert same["diff"] == 0 and same["p_value"] == 1.0


def test_holm_adjustment():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert holm([0.5]) == pytest.approx([0.5])
    assert holm([]) == []
