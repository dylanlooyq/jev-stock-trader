"""Signal-to-trade conversion and trading metrics.

Timing: a signal formed at the close of day s is traded at the open of day s+1 and held
for h trading days. Capital is split into h equal tranches, one opened per day, so the
book on day d averages the tranches opened over the previous h days. Returns are
open-to-open, which is what such a position earns.

Simplifications, all stated in the report: weights are not drifted between rebalances,
cash earns nothing, and one all-in cost per unit of turnover stands in for commission,
half-spread and slippage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import BUY, SELL


def open_to_open_returns(prices: pd.DataFrame, market_ticker: str) -> tuple[pd.DataFrame, pd.Series]:
    """Wide (date x ticker) return from the open of each date to the next open, plus the market's."""
    adj_open = (prices["open"] * prices["adj_close"] / prices["close"]).rename("adj_open")
    wide = pd.concat([prices[["date", "ticker"]], adj_open], axis=1).pivot(
        index="date", columns="ticker", values="adj_open").sort_index()
    returns = wide.shift(-1) / wide - 1
    return returns.drop(columns=[market_ticker]), returns[market_ticker]


def tranche_weights(signals: pd.DataFrame, mode: str, max_weight: float) -> pd.DataFrame:
    """Weights of the tranche opened on each signal date. `signals` is wide (date x ticker) of classes."""
    buy = (signals == BUY).astype(float)
    n_buy = buy.sum(axis=1)
    if mode == "long_only":
        return buy.mul(np.minimum(1 / n_buy.where(n_buy > 0), max_weight), axis=0).fillna(0.0)
    sell = (signals == SELL).astype(float)
    n_sell = sell.sum(axis=1)
    long = buy.mul(np.minimum(0.5 / n_buy.where(n_buy > 0), max_weight), axis=0).fillna(0.0)
    short = sell.mul(np.minimum(0.5 / n_sell.where(n_sell > 0), max_weight), axis=0).fillna(0.0)
    return long - short


def run_backtest(pred: pd.DataFrame, returns: pd.DataFrame, horizon: int, cfg: dict,
                 mode: str | None = None, cost_bps: float | None = None) -> pd.DataFrame:
    """Daily gross and net returns for one model's predictions (columns date, ticker, pred)."""
    bt = cfg["backtest"]
    mode = mode or bt["mode"]
    cost_bps = float(bt["cost_bps_per_side"] if cost_bps is None else cost_bps)

    signals = pred.pivot(index="date", columns="ticker", values="pred")
    first_signal = signals.index.min()
    calendar = returns.index[returns.index >= first_signal]
    signals = signals.reindex(index=calendar, columns=returns.columns)
    tranche = tranche_weights(signals, mode, float(bt["max_weight"]))

    # Book held from the open of day d: tranches from signal dates d-1 ... d-h.
    book = sum(tranche.shift(j, fill_value=0.0) for j in range(1, horizon + 1)) / horizon
    day_returns = returns.reindex(calendar)
    book = book.where(day_returns.notna(), 0.0)   # no position where there is no price

    gross = (book * day_returns.fillna(0.0)).sum(axis=1)
    turnover = book.diff().abs().sum(axis=1)
    turnover.iloc[0] = book.iloc[0].abs().sum()
    cost = turnover * cost_bps / 1e4
    short_exposure = book.clip(upper=0).abs().sum(axis=1)
    borrow = short_exposure * float(bt["borrow_bps_per_year"]) / 1e4 / 252
    out = pd.DataFrame({
        "gross": gross, "cost": cost + borrow, "net": gross - cost - borrow,
        "turnover": turnover, "exposure": book.abs().sum(axis=1),
        "positions_opened": (tranche != 0).sum(axis=1),
    })
    return out.iloc[:-1] if day_returns.iloc[-1].isna().all() else out


def trading_stats(daily: pd.DataFrame, starting_capital: float) -> dict:
    net = daily["net"].to_numpy()
    n = len(net)
    if n < 2:
        return {"days": n}
    equity = np.cumprod(1 + net)
    years = n / 252
    cagr = equity[-1] ** (1 / years) - 1 if equity[-1] > 0 else -1.0
    sd = net.std(ddof=1)
    downside = np.sqrt(np.mean(np.minimum(net, 0.0) ** 2))
    drawdown = equity / np.maximum.accumulate(np.maximum(equity, 1.0)) - 1
    max_dd = float(drawdown.min())
    return {
        "days": n,
        "cumulative_net_return": float(equity[-1] - 1),
        "cumulative_gross_return": float(np.prod(1 + daily["gross"].to_numpy()) - 1),
        "ending_capital": float(starting_capital * equity[-1]),
        "cagr": float(cagr),
        "sharpe": float(net.mean() / sd * np.sqrt(252)) if sd > 0 else 0.0,
        "sortino": float(net.mean() / downside * np.sqrt(252)) if downside > 0 else 0.0,
        "max_drawdown": max_dd,
        "calmar": float(cagr / abs(max_dd)) if max_dd < 0 else float("nan"),
        "annual_turnover": float(daily["turnover"].mean() * 252),
        "total_cost": float(daily["cost"].sum()),
        "mean_exposure": float(daily["exposure"].mean()),
        "positions_opened": int(daily["positions_opened"].sum()),
    }
