"""Controlled feature set, shared by every model.

Each feature at date t uses only rows dated t or earlier (the close of day t is the
prediction timestamp). All features are returns or ratios, so they are unaffected by
the back-adjustment of historical prices for later dividends and splits.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RETURN_WINDOWS = (1, 5, 20, 60, 120, 250)

FEATURES = [
    *[f"ret_{n}" for n in RETURN_WINDOWS],
    "vol_20", "vol_60", "rsi_14",
    "dist_sma_20", "dist_sma_50", "dist_sma_200",
    "macd_hist", "vol_ratio_20", "dist_52w_high", "bb_z_20", "atr_14",
    "mkt_ret_5", "mkt_ret_20", "mkt_vol_20", "mkt_dist_sma_200",
    "rel_ret_20", "rel_ret_60",
    "xs_rank_ret_5", "xs_rank_ret_20", "xs_rank_ret_120", "xs_rank_vol_20",
]

MARKET_FEATURES = {
    "mkt_ret_5": "ret_5", "mkt_ret_20": "ret_20",
    "mkt_vol_20": "vol_20", "mkt_dist_sma_200": "dist_sma_200",
}


def compute_features(prices: pd.DataFrame, market_ticker: str) -> pd.DataFrame:
    """Return one row per (date, stock) with the FEATURES columns. Market ticker rows are dropped."""
    df = prices.sort_values(["ticker", "date"]).reset_index(drop=True).copy()
    factor = df["adj_close"] / df["close"]
    df["ac"] = df["adj_close"]
    df["ah"] = df["high"] * factor
    df["al"] = df["low"] * factor
    g = df.groupby("ticker", sort=False)

    def roll(col: str, n: int, fn: str) -> pd.Series:
        return g[col].transform(lambda s: getattr(s.rolling(n, min_periods=n), fn)())

    def ewm(col: str, min_periods: int, **kw) -> pd.Series:
        return g[col].transform(lambda s: s.ewm(adjust=False, min_periods=min_periods, **kw).mean())

    out = df[["date", "ticker"]].copy()
    for n in RETURN_WINDOWS:
        out[f"ret_{n}"] = g["ac"].pct_change(n, fill_method=None)

    df["r1"] = out["ret_1"]
    out["vol_20"] = roll("r1", 20, "std")
    out["vol_60"] = roll("r1", 60, "std")

    delta = g["ac"].diff()
    df["gain"] = delta.clip(lower=0)
    df["loss"] = -delta.clip(upper=0)
    avg_gain = ewm("gain", 14, alpha=1 / 14)
    avg_loss = ewm("loss", 14, alpha=1 / 14)
    out["rsi_14"] = 100 - 100 / (1 + avg_gain / avg_loss)

    for n in (20, 50, 200):
        out[f"dist_sma_{n}"] = df["ac"] / roll("ac", n, "mean") - 1

    df["macd"] = ewm("ac", 26, span=12) - ewm("ac", 26, span=26)
    out["macd_hist"] = (df["macd"] - ewm("macd", 9, span=9)) / df["ac"]

    df["volume_f"] = df["volume"].astype(float)
    mean_volume = roll("volume_f", 20, "mean")
    out["vol_ratio_20"] = df["volume_f"] / mean_volume.where(mean_volume > 0)

    out["dist_52w_high"] = df["ac"] / roll("ac", 252, "max") - 1
    out["bb_z_20"] = (df["ac"] - roll("ac", 20, "mean")) / roll("ac", 20, "std")

    prev_close = g["ac"].shift(1)
    true_range = np.maximum(df["ah"], prev_close) - np.minimum(df["al"], prev_close)
    df["tr_pct"] = true_range / df["ac"]
    out["atr_14"] = roll("tr_pct", 14, "mean")

    is_market = out["ticker"] == market_ticker
    market_cols = {**MARKET_FEATURES, "mkt_ret_60": "ret_60"}
    market = out.loc[is_market, ["date", *market_cols.values()]].rename(
        columns={v: k for k, v in market_cols.items()}
    )
    out = out.loc[~is_market].merge(market, on="date", how="left")
    out["rel_ret_20"] = out["ret_20"] - out["mkt_ret_20"]
    out["rel_ret_60"] = out["ret_60"] - out["mkt_ret_60"]

    by_date = out.groupby("date")
    for col in ("ret_5", "ret_20", "ret_120", "vol_20"):
        out[f"xs_rank_{col}"] = by_date[col].rank(pct=True)

    out = out.replace([np.inf, -np.inf], np.nan)
    return out[["date", "ticker", *FEATURES]].sort_values(["date", "ticker"]).reset_index(drop=True)
