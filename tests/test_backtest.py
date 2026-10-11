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


# ----------------------------------------------------------------- ranking rule, cash and excess returns

from jevbench.backtest import alpha_beta, passive_daily, rank_weights, with_cost  # noqa: E402
from jevbench.stats import alpha_bootstrap  # noqa: E402


def test_rank_weights_hold_the_top_fraction_equally():
    scores = pd.DataFrame([[0.9, 0.1, 0.5, 0.3, 0.7, np.nan, 0.2, 0.4, 0.6, 0.8, 0.0]], columns=list("ABCDEFGHIJK"))
    w = rank_weights(scores, fraction=0.2, seed=1)
    assert w.loc[0, "A"] == pytest.approx(0.5) and w.loc[0, "J"] == pytest.approx(0.5)   # top 2 of 10 scored
    assert w.loc[0].sum() == pytest.approx(1.0) and (w.loc[0] > 0).sum() == 2
    assert w.loc[0, "F"] == 0.0                                                          # no score, never held
    everything = rank_weights(scores, fraction=1.0, seed=1)
    np.testing.assert_allclose(everything.loc[0].drop("F").to_numpy(), 0.1)


def test_rank_weights_long_short_is_dollar_neutral():
    scores = pd.DataFrame([np.arange(10.0)], columns=list("ABCDEFGHIJ"))
    w = rank_weights(scores, fraction=0.2, seed=1, mode="long_short")
    assert w.loc[0, ["I", "J"]].tolist() == [0.25, 0.25] and w.loc[0, ["A", "B"]].tolist() == [-0.25, -0.25]
    assert w.loc[0].sum() == pytest.approx(0.0)


def test_tied_scores_give_a_reproducible_random_selection():
    tied = pd.DataFrame(np.zeros((200, 10)), columns=list("ABCDEFGHIJ"))
    a, b = rank_weights(tied, 0.2, seed=7), rank_weights(tied, 0.2, seed=7)
    pd.testing.assert_frame_equal(a, b)
    assert ((a > 0).sum(axis=1) == 2).all()
    held_share = (a > 0).mean()
    assert held_share.between(0.1, 0.3).all()          # no stock is favoured: each held about 20% of days
    assert not a.equals(rank_weights(tied, 0.2, seed=8))


def test_ranking_portfolio_is_fully_invested_and_trades_next_open(bt_cfg):
    opens = {"A": np.array([100.0, 100.0, 110.0, 110.0, 110.0, 110.0]), "B": np.full(6, 100.0),
             "MKT": np.full(6, 100.0)}
    returns, _ = open_to_open_returns(_prices(opens), "MKT")
    dates = returns.index
    cfg = deep_update(bt_cfg, {"backtest": {"rank_fraction": 0.5}})
    pred = pd.DataFrame({"date": [dates[1]] * 2, "ticker": ["A", "B"], "score": [0.9, 0.1]})
    daily = run_backtest(pred, returns, horizon=1, cfg=cfg, rule="rank")
    assert daily.loc[dates[1], "gross"] == 0.0                     # A's jump from day 1 to day 2 is missed
    assert daily.loc[dates[2], "exposure"] == pytest.approx(1.0)   # all capital in the top half: stock A
    assert daily.loc[dates[2], "gross"] == pytest.approx(0.0)      # A is flat from day 2 to day 3


def test_idle_cash_earns_the_risk_free_rate_and_sharpe_uses_excess_returns(bt_cfg):
    prices = _prices({"A": np.full(8, 100.0), "MKT": np.full(8, 100.0)})
    returns, _ = open_to_open_returns(prices, "MKT")
    dates = returns.index
    rf = pd.Series(0.0002, index=dates)
    pred = pd.DataFrame({"date": [dates[1]], "ticker": ["A"], "pred": [BUY]})
    daily = run_backtest(pred, returns, horizon=1, cfg=bt_cfg, risk_free=rf, cost_bps=0.0)
    assert daily.loc[dates[1], "gross"] == pytest.approx(0.0002)   # signal day: still all cash
    assert daily.loc[dates[2], "gross"] == pytest.approx(0.0)      # fully in a flat stock: no cash interest
    assert (daily["excess"] == daily["net"] - daily["rf"]).all()
    # Sitting in cash earns the risk-free rate, which is zero excess return and so zero Sharpe.
    cash_only = run_backtest(pred.assign(pred=HOLD), returns, horizon=1, cfg=bt_cfg, risk_free=rf)
    assert trading_stats(cash_only, 1.0)["sharpe"] == 0.0
    assert trading_stats(cash_only, 1.0)["cumulative_net_return"] > 0


def test_with_cost_rescales_only_the_cost(bt_cfg):
    prices = _prices({"A": np.full(6, 100.0), "MKT": np.full(6, 100.0)})
    returns, _ = open_to_open_returns(prices, "MKT")
    pred = pd.DataFrame({"date": [returns.index[1]], "ticker": ["A"], "pred": [BUY]})
    base = run_backtest(pred, returns, horizon=1, cfg=bt_cfg, cost_bps=5.0)
    direct = run_backtest(pred, returns, horizon=1, cfg=bt_cfg, cost_bps=10.0)
    pd.testing.assert_frame_equal(with_cost(base, 10.0), direct)


def test_alpha_and_beta_recover_known_values():
    rng = np.random.default_rng(0)
    market = rng.normal(0.0004, 0.01, 4000)
    strategy = 0.0002 + 1.5 * market + rng.normal(0, 0.002, 4000)
    alpha, beta = alpha_beta(strategy, market)
    assert beta == pytest.approx(1.5, abs=0.02)
    assert alpha == pytest.approx(0.0002 * 252, abs=0.02)
    boot = alpha_bootstrap(strategy, market, 10, 300, seed=0)
    assert boot["alpha"] == pytest.approx(alpha) and boot["ci_low"] < alpha < boot["ci_high"]
    assert boot["ci_low"] > 0                                       # a real alpha of 5% a year is detected
    assert alpha_beta(market, market) == pytest.approx((0.0, 1.0), abs=1e-9)


def test_passive_series_has_the_backtest_shape():
    idx = pd.bdate_range("2021-01-04", periods=4)
    out = passive_daily(pd.Series([0.01, np.nan, -0.01, 0.0], index=idx), pd.Series(0.0001, index=idx))
    assert out["net"].tolist() == [0.01, 0.0, -0.01, 0.0]
    assert out["excess"].tolist() == pytest.approx([0.0099, -0.0001, -0.0101, -0.0001])
    assert (out["exposure"] == 1.0).all() and out["cost"].sum() == 0.0


def test_configured_rules_hold_three_and_one_of_ten_assets():
    """Decision D11: top 3 is the primary rule and top 1 is a declared check; both hold whole assets."""
    from jevbench.backtest import names_held, trade_rules
    from jevbench.config import load_config

    cfg = load_config()
    assert list(trade_rules(cfg)) == ["rank", "rank_check", "buy_names"]
    assert cfg["backtest"]["primary_rule"] == "rank" and len(cfg["data"]["tickers"]) == 10
    assert names_held(cfg, "rank") == 3 and names_held(cfg, "rank_check") == 1 and names_held(cfg, "buy_names") is None
    # Before bitcoin has history only nine assets are scored; the counts must not change.
    nine = pd.DataFrame([np.arange(9.0)], columns=list("ABCDEFGHI"))
    assert (rank_weights(nine, cfg["backtest"]["rank_fraction"], seed=1).loc[0] > 0).sum() == 3
    assert (rank_weights(nine, cfg["backtest"]["rank_check_fraction"], seed=1).loc[0] > 0).sum() == 1
