"""Signal-to-trade conversion and trading metrics.

Timing: a signal formed at the close of day s is traded at the open of day s+1 and held
for h trading days. Capital is split into h equal tranches, one opened per day, so the
book on day d averages the tranches opened over the previous h days. Returns are
open-to-open, which is what such a position earns.

Two trade rules share that engine:
- "rank" (primary): each day hold the top fraction of stocks by ranking score, equally
  weighted, so the book is fully invested and differs from buy and hold only in which
  stocks it holds.
- "buy_names" (secondary): hold the stocks the model labels BUY; the rest is cash.

Simplifications, all stated in the report: weights are not drifted between rebalances,
idle cash earns the risk-free rate, and one all-in cost per unit of turnover stands in
for commission, half-spread and slippage.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import BUY, SELL

RULES = ("rank", "buy_names")


def open_to_open_returns(prices: pd.DataFrame, market_ticker: str) -> tuple[pd.DataFrame, pd.Series]:
    """Wide (date x ticker) return from the open of each date to the next open, plus the market's."""
    adj_open = (prices["open"] * prices["adj_close"] / prices["close"]).rename("adj_open")
    wide = pd.concat([prices[["date", "ticker"]], adj_open], axis=1).pivot(
        index="date", columns="ticker", values="adj_open").sort_index()
    returns = wide.shift(-1) / wide - 1
    return returns.drop(columns=[market_ticker]), returns[market_ticker]


def tranche_weights(signals: pd.DataFrame, mode: str, max_weight: float) -> pd.DataFrame:
    """BUY-names rule: weights of the tranche opened on each signal date."""
    buy = (signals == BUY).astype(float)
    n_buy = buy.sum(axis=1)
    if mode == "long_only":
        return buy.mul(np.minimum(1 / n_buy.where(n_buy > 0), max_weight), axis=0).fillna(0.0)
    sell = (signals == SELL).astype(float)
    n_sell = sell.sum(axis=1)
    long = buy.mul(np.minimum(0.5 / n_buy.where(n_buy > 0), max_weight), axis=0).fillna(0.0)
    short = sell.mul(np.minimum(0.5 / n_sell.where(n_sell > 0), max_weight), axis=0).fillna(0.0)
    return long - short


def rank_weights(scores: pd.DataFrame, fraction: float, seed: int, mode: str = "long_only") -> pd.DataFrame:
    """Ranking rule: equal weight in the top `fraction` of stocks by score on each date.

    Stocks without a score are never held. Ties are broken at random with a fixed seed,
    so a model whose scores are all equal holds a random selection, which is the
    no-skill reference for this rule. long_short also shorts the bottom fraction.
    """
    values = scores.to_numpy(dtype=float)
    weights = np.zeros_like(values)
    tiebreak = np.random.default_rng(seed).random(values.shape)
    for i in range(values.shape[0]):
        valid = np.flatnonzero(np.isfinite(values[i]))
        if len(valid) == 0:
            continue
        k = max(1, int(round(len(valid) * fraction)))
        order = valid[np.lexsort((tiebreak[i, valid], -values[i, valid]))]   # best first
        if mode == "long_only":
            weights[i, order[:k]] = 1.0 / k
        elif len(valid) >= 2 * k:
            weights[i, order[:k]] = 0.5 / k
            weights[i, order[-k:]] = -0.5 / k
    return pd.DataFrame(weights, index=scores.index, columns=scores.columns)


def run_backtest(pred: pd.DataFrame, returns: pd.DataFrame, horizon: int, cfg: dict, rule: str = "buy_names",
                 mode: str | None = None, cost_bps: float | None = None,
                 risk_free: pd.Series | None = None, rank_fraction: float | None = None) -> pd.DataFrame:
    """Daily returns for one model. `pred` needs date, ticker and `pred` (or `score` for the rank rule).

    `risk_free` is a daily rate indexed by date; idle cash earns it. None means zero.
    """
    bt = cfg["backtest"]
    mode = mode or bt["mode"]
    value_col = "score" if rule == "rank" else "pred"
    wide = pred.pivot(index="date", columns="ticker", values=value_col)
    calendar = returns.index[returns.index >= wide.index.min()]
    wide = wide.reindex(index=calendar, columns=returns.columns)
    if rule == "rank":
        fraction = float(bt["rank_fraction"] if rank_fraction is None else rank_fraction)
        tranche = rank_weights(wide, fraction, int(cfg["seed"]), mode)
    elif rule == "buy_names":
        tranche = tranche_weights(wide, mode, float(bt["max_weight"]))
    else:
        raise ValueError(f"Unknown trade rule {rule!r}")

    # Book held from the open of day d: tranches from signal dates d-1 ... d-h.
    book = sum(tranche.shift(j, fill_value=0.0) for j in range(1, horizon + 1)) / horizon
    day_returns = returns.reindex(calendar)
    book = book.where(day_returns.notna(), 0.0)   # no position where there is no price

    rf = pd.Series(0.0, index=calendar) if risk_free is None else risk_free.reindex(calendar).ffill().fillna(0.0)
    cash = 1.0 - book.sum(axis=1)
    turnover = book.diff().abs().sum(axis=1)
    turnover.iloc[0] = book.iloc[0].abs().sum()
    short_exposure = book.clip(upper=0).abs().sum(axis=1)
    out = pd.DataFrame({
        "gross": (book * day_returns.fillna(0.0)).sum(axis=1) + cash * rf,
        "turnover": turnover,
        "borrow": short_exposure * float(bt["borrow_bps_per_year"]) / 1e4 / 252,
        "exposure": book.abs().sum(axis=1),
        "rf": rf,
        "positions_opened": (tranche != 0).sum(axis=1),
    })
    out = out.iloc[:-1] if day_returns.iloc[-1].isna().all() else out
    return with_cost(out, float(bt["cost_bps_per_side"] if cost_bps is None else cost_bps))


def with_cost(daily: pd.DataFrame, cost_bps: float) -> pd.DataFrame:
    """Apply an all-in trading cost per unit of turnover and derive net and excess returns."""
    out = daily.copy()
    out["cost"] = out["turnover"] * cost_bps / 1e4 + out["borrow"]
    out["net"] = out["gross"] - out["cost"]
    out["excess"] = out["net"] - out["rf"]
    return out


def passive_daily(returns: pd.Series, risk_free: pd.Series | None) -> pd.DataFrame:
    """A buy-and-hold series (for example the market proxy) in the same shape as a backtest."""
    rf = pd.Series(0.0, index=returns.index) if risk_free is None else risk_free.reindex(returns.index).ffill().fillna(0.0)
    net = returns.fillna(0.0)
    return pd.DataFrame({"gross": net, "turnover": 0.0, "borrow": 0.0, "exposure": 1.0, "rf": rf,
                         "positions_opened": 0, "cost": 0.0, "net": net, "excess": net - rf})


def annualised_sharpe(excess: np.ndarray) -> float:
    sd = excess.std(ddof=1)
    return float(excess.mean() / sd * np.sqrt(252)) if sd > 0 else 0.0


def alpha_beta(excess: np.ndarray, market_excess: np.ndarray) -> tuple[float, float]:
    """Annualised alpha and beta from regressing excess returns on the market's excess returns."""
    var = market_excess.var(ddof=1)
    if var <= 0:
        return float(excess.mean() * 252), 0.0
    beta = float(np.cov(excess, market_excess, ddof=1)[0, 1] / var)
    return float((excess.mean() - beta * market_excess.mean()) * 252), beta


def trading_stats(daily: pd.DataFrame, starting_capital: float, market_excess: np.ndarray | None = None) -> dict:
    """Performance summary. Sharpe and Sortino use returns in excess of the risk-free rate."""
    net = daily["net"].to_numpy()
    n = len(net)
    if n < 2:
        return {"days": n}
    excess = daily["excess"].to_numpy() if "excess" in daily else net
    equity = np.cumprod(1 + net)
    years = n / 252
    cagr = equity[-1] ** (1 / years) - 1 if equity[-1] > 0 else -1.0
    downside = np.sqrt(np.mean(np.minimum(excess, 0.0) ** 2))
    drawdown = equity / np.maximum.accumulate(np.maximum(equity, 1.0)) - 1
    max_dd = float(drawdown.min())
    stats = {
        "days": n,
        "cumulative_net_return": float(equity[-1] - 1),
        "cumulative_gross_return": float(np.prod(1 + daily["gross"].to_numpy()) - 1),
        "ending_capital": float(starting_capital * equity[-1]),
        "cagr": float(cagr),
        "sharpe": annualised_sharpe(excess),
        "sortino": float(excess.mean() / downside * np.sqrt(252)) if downside > 0 else 0.0,
        "max_drawdown": max_dd,
        "calmar": float(cagr / abs(max_dd)) if max_dd < 0 else float("nan"),
        "annual_turnover": float(daily["turnover"].mean() * 252),
        "total_cost": float(daily["cost"].sum()),
        "mean_exposure": float(daily["exposure"].mean()),
        "positions_opened": int(daily["positions_opened"].sum()),
    }
    if market_excess is not None:
        stats["alpha"], stats["beta"] = alpha_beta(excess, market_excess)
    return stats
