"""Signal-to-trade conversion: timing, costs and position constraints."""
import numpy as np
import pandas as pd
import pytest

from jevbench import BUY, HOLD, SELL
from jevbench.backtest import open_to_open_returns, run_backtest, tranche_weights, trading_stats
from jevbench.config import deep_update


def _prices(opens_by_ticker: dict) -> pd.DataFrame:
    n = len(next(iter(opens_by_ticker.values())))
    dates = pd.bdate_range("2021-01-04", periods=n)
    return pd.concat([
        pd.DataFrame({"date": dates, "ticker": t, "open": o, "high": o, "low": o, "close": o,
                      "adj_close": o, "volume": 1.0})
        for t, o in opens_by_ticker.items()
    ], ignore_index=True)


@pytest.fixture()
def bt_cfg(cfg):
    return deep_update(cfg, {"backtest": {"max_weight": 1.0, "cost_bps_per_side": 10.0, "mode": "long_only"}})


def test_position_starts_at_the_next_open_and_misses_the_overnight_gap(bt_cfg):
    # Stock A jumps 50% between the open of day 1 and the open of day 2, then 10%, then is flat.
    opens_a = np.array([100.0, 100.0, 150.0, 165.0, 165.0, 165.0])
    prices = _prices({"A": opens_a, "MKT": np.full(6, 100.0)})
    returns, _ = open_to_open_returns(prices, "MKT")
    dates = returns.index
    assert returns.loc[dates[1], "A"] == pytest.approx(0.5)

    # BUY signal formed at the close of day 1. It can only trade at the open of day 2.
    pred = pd.DataFrame({"date": [dates[1]], "ticker": ["A"], "pred": [BUY]})
    daily = run_backtest(pred, returns, horizon=1, cfg=bt_cfg)
    assert daily.loc[dates[1], "gross"] == 0.0                       # the 50% jump is not captured
    assert daily.loc[dates[2], "gross"] == pytest.approx(0.10)       # open(day 2) -> open(day 3)
    assert daily.loc[dates[3], "gross"] == 0.0                       # position closed after one day
    assert daily.loc[dates[2], "exposure"] == pytest.approx(1.0)


def test_costs_are_charged_on_entry_and_exit(bt_cfg):
    prices = _prices({"A": np.full(6, 100.0), "MKT": np.full(6, 100.0)})
    returns, _ = open_to_open_returns(prices, "MKT")
    dates = returns.index
    pred = pd.DataFrame({"date": [dates[1]], "ticker": ["A"], "pred": [BUY]})
    daily = run_backtest(pred, returns, horizon=1, cfg=bt_cfg)
    assert daily.loc[dates[2], "turnover"] == pytest.approx(1.0)     # buy
    assert daily.loc[dates[3], "turnover"] == pytest.approx(1.0)     # sell
    assert daily["cost"].sum() == pytest.approx(2 * 10.0 / 1e4)
    assert daily["net"].sum() == pytest.approx(-0.002)
    zero_cost = run_backtest(pred, returns, horizon=1, cfg=bt_cfg, cost_bps=0.0)
    assert zero_cost["net"].sum() == 0.0


def test_multi_day_holding_builds_exposure_in_tranches(bt_cfg):
    prices = _prices({"A": np.full(12, 100.0), "MKT": np.full(12, 100.0)})
    returns, _ = open_to_open_returns(prices, "MKT")
    dates = returns.index
    pred = pd.DataFrame({"date": dates[:8], "ticker": "A", "pred": BUY})
    daily = run_backtest(pred, returns, horizon=5, cfg=bt_cfg)
    np.testing.assert_allclose(daily["exposure"].to_numpy()[:6], [0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    # A stock held continuously is not re-traded once the book is full.
    assert daily.loc[dates[6], "turnover"] == pytest.approx(0.0)


def test_long_only_ignores_sell_and_respects_the_weight_cap(cfg):
    signals = pd.DataFrame([[BUY, SELL, HOLD, BUY], [SELL, SELL, HOLD, HOLD]], columns=list("ABCD"))
    weights = tranche_weights(signals, "long_only", max_weight=0.3)
    np.testing.assert_allclose(weights.iloc[0].to_numpy(), [0.3, 0.0, 0.0, 0.3])   # 1/2 capped at 0.3
    np.testing.assert_allclose(weights.iloc[1].to_numpy(), [0.0, 0.0, 0.0, 0.0])
    assert (weights >= 0).all().all()


def test_long_short_is_dollar_neutral_when_both_sides_exist():
    signals = pd.DataFrame([[BUY, SELL, HOLD, BUY], [BUY, HOLD, HOLD, HOLD]], columns=list("ABCD"))
    weights = tranche_weights(signals, "long_short", max_weight=1.0)
    np.testing.assert_allclose(weights.iloc[0].to_numpy(), [0.25, -0.5, 0.0, 0.25])
    assert weights.iloc[0].sum() == pytest.approx(0.0)
    np.testing.assert_allclose(weights.iloc[1].to_numpy(), [0.5, 0.0, 0.0, 0.0])


def test_short_positions_pay_borrow_cost(bt_cfg):
    prices = _prices({"A": np.full(6, 100.0), "MKT": np.full(6, 100.0)})
    returns, _ = open_to_open_returns(prices, "MKT")
    dates = returns.index
    pred = pd.DataFrame({"date": [dates[1]], "ticker": ["A"], "pred": [SELL]})
    cfg = deep_update(bt_cfg, {"backtest": {"borrow_bps_per_year": 252.0}})
    daily = run_backtest(pred, returns, horizon=1, cfg=cfg, mode="long_short", cost_bps=0.0)
    assert daily.loc[dates[2], "cost"] == pytest.approx(0.5 * 252.0 / 1e4 / 252)
    assert run_backtest(pred, returns, horizon=1, cfg=cfg, mode="long_only")["exposure"].sum() == 0.0


def test_trading_stats_on_a_known_series():
    net = np.array([0.10, -0.50, 0.10, 0.0])
    daily = pd.DataFrame({"net": net, "gross": net, "cost": 0.0, "turnover": 0.5, "exposure": 1.0,
                          "positions_opened": 1})
    s = trading_stats(daily, starting_capital=1000.0)
    assert s["cumulative_net_return"] == pytest.approx(1.1 * 0.5 * 1.1 - 1)
    assert s["max_drawdown"] == pytest.approx(-0.5)
    assert s["ending_capital"] == pytest.approx(1000 * 1.1 * 0.5 * 1.1)
    assert s["sharpe"] == pytest.approx(net.mean() / net.std(ddof=1) * np.sqrt(252))
    assert s["annual_turnover"] == pytest.approx(0.5 * 252)
    assert s["positions_opened"] == 4
