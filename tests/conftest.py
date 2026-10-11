"""Shared fixtures: synthetic prices and a small configuration. No network access."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from jevbench.config import load_config  # noqa: E402

TICKERS = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]
MARKET = "MKT"


def make_prices(n_days: int = 1100, seed: int = 0, start: str = "2018-01-02") -> pd.DataFrame:
    """Random-walk daily bars. One ticker carries a constant dividend adjustment factor."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n_days)
    frames = []
    for j, ticker in enumerate([*TICKERS, MARKET]):
        ret = rng.normal(0.0003, 0.012 + 0.002 * j, n_days)
        close = 50.0 * (1 + j) * np.cumprod(1 + ret)
        open_ = np.r_[close[0], close[:-1]] * (1 + rng.normal(0, 0.004, n_days))
        high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.003, n_days)))
        low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.003, n_days)))
        factor = 0.9 if ticker == "BBB" else 1.0
        frames.append(pd.DataFrame({
            "date": dates, "ticker": ticker, "open": open_, "high": high, "low": low, "close": close,
            "adj_close": close * factor, "volume": rng.integers(1_000_000, 5_000_000, n_days).astype(float),
        }))
    return pd.concat(frames, ignore_index=True)


TEST_OVERRIDES = {
    "experiment_id": "unit-test",
    "data": {"universe_name": "synthetic", "tickers": TICKERS, "market_ticker": MARKET},
    "task": {"horizons": [1, 5], "primary_horizon": 5},
    "splits": {"first_test_start": "2020-07-01", "test_months": 6, "validation_months": 6,
               "holdout_start": "2021-07-01", "min_train_days": 100},
    "models": {
        "n_jobs": 1,
        "logreg": {"grid": [{"C": 0.1, "class_weight": None}, {"C": 1.0, "class_weight": "balanced"}]},
        "random_forest": {"n_estimators": 20, "grid": [
            {"max_depth": 3, "min_samples_leaf": 20, "class_weight": None},
            {"max_depth": 5, "min_samples_leaf": 20, "class_weight": "balanced_subsample"}]},
        "gbt": {"min_child_samples": 20, "grid": [
            {"num_leaves": 7, "learning_rate": 0.1, "n_estimators": 20, "class_weight": None},
            {"num_leaves": 7, "learning_rate": 0.1, "n_estimators": 20, "class_weight": "balanced"}]},
    },
    "jev": {"max_workers": 2, "bucket_lookback_days": 200, "example_lookback_days": 120},
    "stats": {"n_boot": 200},
}


@pytest.fixture(scope="session")
def prices() -> pd.DataFrame:
    return make_prices()


@pytest.fixture()
def cfg(tmp_path) -> dict:
    overrides = {**TEST_OVERRIDES, "data": {**TEST_OVERRIDES["data"], "cache_dir": str(tmp_path / "data")}}
    return load_config(overrides=[overrides])
