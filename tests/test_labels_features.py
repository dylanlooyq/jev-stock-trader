"""Label construction and the no-look-ahead property of features and labels."""
import numpy as np
import pandas as pd
import pytest

from jevbench import BUY, HOLD, SELL
from jevbench.config import deep_update
from jevbench.data import keep_market_days
from jevbench.dataset import build_dataset
from jevbench.features import FEATURES, compute_features
from jevbench.labels import compute_labels

from .conftest import MARKET


def _single_ticker(opens, closes=None):
    dates = pd.bdate_range("2020-01-01", periods=len(opens))
    closes = opens if closes is None else closes
    return pd.DataFrame({"date": dates, "ticker": "X", "open": opens, "high": opens, "low": opens,
                         "close": closes, "adj_close": closes, "volume": 1.0})


def test_labels_match_hand_calculation(cfg):
    cfg = deep_update(cfg, {"task": {"horizons": [1, 2], "label": {
        "method": "fixed", "fixed_thresholds": {1: 0.05, 2: 0.05}}}})
    opens = np.array([100.0, 100.0, 110.0, 99.0, 100.0, 100.0])
    labels = compute_labels(_single_ticker(opens), cfg)

    # Row 0: enter at open[1]=100. h=1 exits at open[2]=110 (+10% -> BUY); h=2 at open[3]=99 (-1% -> HOLD).
    assert labels.loc[0, "fwd_ret_1"] == pytest.approx(0.10)
    assert labels.loc[0, "label_1"] == BUY
    assert labels.loc[0, "fwd_ret_2"] == pytest.approx(-0.01)
    assert labels.loc[0, "label_2"] == HOLD
    # Row 1: enter at open[2]=110, exit at open[3]=99 (-10% -> SELL).
    assert labels.loc[1, "label_1"] == SELL
    # The label window for row 0, h=2 closes on the date of row 3.
    assert labels.loc[0, "label_end_2"] == labels.loc[3, "date"]


def test_no_label_without_enough_future(cfg):
    cfg = deep_update(cfg, {"task": {"horizons": [1, 2], "label": {
        "method": "fixed", "fixed_thresholds": {1: 0.05, 2: 0.05}}}})
    labels = compute_labels(_single_ticker(np.linspace(100, 105, 6)), cfg)
    assert labels["label_1"].isna().tolist() == [False] * 4 + [True] * 2
    assert labels["label_2"].isna().tolist() == [False] * 3 + [True] * 3


def test_label_uses_next_open_not_same_day_prices(cfg):
    """Changing the open of the prediction day itself must not change that day's label return."""
    cfg = deep_update(cfg, {"task": {"horizons": [1], "label": {"method": "fixed", "fixed_thresholds": {1: 0.05}}}})
    opens = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
    base = compute_labels(_single_ticker(opens), cfg)
    bumped = opens.copy()
    bumped[0] = 500.0
    changed = compute_labels(_single_ticker(bumped, closes=opens), cfg)
    assert changed.loc[0, "fwd_ret_1"] == pytest.approx(base.loc[0, "fwd_ret_1"])


def test_vol_adjusted_threshold_uses_only_past_returns(cfg, prices):
    labels = compute_labels(prices[prices["ticker"] != MARKET], cfg)
    one = labels[labels["ticker"] == "AAA"].reset_index(drop=True)
    closes = prices[prices["ticker"] == "AAA"].sort_values("date")["adj_close"].reset_index(drop=True)
    window, k, t = cfg["task"]["label"]["vol_window"], cfg["task"]["label"]["k"], 400
    expected_sigma = closes.pct_change().iloc[t - window + 1:t + 1].std()
    assert one.loc[t, "thr_5"] == pytest.approx(k * expected_sigma * np.sqrt(5))


def test_labels_ignore_prices_after_their_window(cfg, prices):
    stocks = prices[prices["ticker"] != MARKET]
    base = compute_labels(stocks, cfg)
    cutoff = stocks["date"].sort_values().unique()[700]
    shocked = stocks.copy()
    later = shocked["date"] > cutoff
    shocked.loc[later, ["open", "high", "low", "close", "adj_close"]] *= 3.0
    new = compute_labels(shocked, cfg)
    for h in cfg["task"]["horizons"]:
        settled = base[f"label_end_{h}"] <= cutoff
        assert settled.sum() > 1000
        pd.testing.assert_series_equal(base.loc[settled, f"label_{h}"], new.loc[settled, f"label_{h}"])
        pd.testing.assert_series_equal(base.loc[settled, f"fwd_ret_{h}"], new.loc[settled, f"fwd_ret_{h}"])


def test_features_are_unchanged_when_the_future_is_removed(prices):
    full = compute_features(prices, MARKET)
    cutoff = prices["date"].sort_values().unique()[800]
    truncated = compute_features(prices[prices["date"] <= cutoff], MARKET)
    past = full[full["date"] <= cutoff].reset_index(drop=True)
    pd.testing.assert_frame_equal(past, truncated.reset_index(drop=True))


def test_features_are_unchanged_when_the_future_is_altered(prices):
    full = compute_features(prices, MARKET)
    cutoff = prices["date"].sort_values().unique()[800]
    shocked = prices.copy()
    later = shocked["date"] > cutoff
    shocked.loc[later, ["open", "high", "low", "close", "adj_close", "volume"]] *= 5.0
    new = compute_features(shocked, MARKET)
    keep = full["date"] <= cutoff
    pd.testing.assert_frame_equal(full[keep], new[keep])


def test_feature_table_shape_and_ranges(prices):
    feats = compute_features(prices, MARKET)
    assert list(feats.columns) == ["date", "ticker", *FEATURES]
    assert MARKET not in set(feats["ticker"])
    complete = feats.dropna()
    assert len(complete) > 4000
    assert complete["rsi_14"].between(0, 100).all()
    assert complete["xs_rank_ret_5"].between(0, 1).all()
    assert (complete["dist_52w_high"] <= 1e-12).all()
    assert np.isfinite(complete[FEATURES].to_numpy()).all()


def test_features_are_invariant_to_a_constant_adjustment_factor(prices):
    """Back-adjustment rescales history by a constant; ratio features must not move."""
    rescaled = prices.copy()
    rescaled["adj_close"] = rescaled["adj_close"] * 0.5
    pd.testing.assert_frame_equal(compute_features(prices, MARKET), compute_features(rescaled, MARKET))


def test_dataset_drops_warm_up_and_burn_in_for_every_model(cfg, prices):
    with_burn_in = build_dataset(prices, cfg, keep_burn_in=True)
    ds = build_dataset(prices, cfg)
    assert ds[FEATURES].notna().all().all()
    dates_all = sorted(with_burn_in["date"].unique())
    assert ds["date"].min() == dates_all[cfg["dataset"]["burn_in_days"]]
    assert not ds.duplicated(["date", "ticker"]).any()


def test_assets_that_trade_every_day_keep_only_market_days(prices):
    saturday = prices["date"].max() + pd.offsets.Week(weekday=5)
    extra = prices[prices["ticker"] == "AAA"].tail(1).assign(date=saturday)
    kept, dropped = keep_market_days(pd.concat([prices, extra], ignore_index=True), MARKET)
    assert dropped == 1 and saturday not in set(kept["date"])
    pd.testing.assert_frame_equal(kept, prices.reset_index(drop=True))
