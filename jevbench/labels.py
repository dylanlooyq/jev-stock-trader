"""Target labels.

Prediction is made after the close of day t and executed at the open of day t+1.
The label return is therefore open(t+1) -> open(t+1+h), dividend and split adjusted,
so it is a return that could have been traded.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import BUY, HOLD, SELL


def compute_labels(prices: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Return per (date, ticker): fwd_ret_h, thr_h, label_h, label_end_h for each horizon h.

    label_end_h is the last date whose prices the label depends on. It drives purging.
    Rows without enough future data get NaN labels; nothing is imputed.
    """
    label_cfg = cfg["task"]["label"]
    df = prices.sort_values(["ticker", "date"]).reset_index(drop=True)
    adj_open = df["open"] * df["adj_close"] / df["close"]
    work = pd.DataFrame({"ticker": df["ticker"], "date": df["date"], "adj_open": adj_open,
                         "adj_close": df["adj_close"]})
    g = work.groupby("ticker", sort=False)

    daily_ret = g["adj_close"].pct_change(fill_method=None)
    window = int(label_cfg["vol_window"])
    sigma = daily_ret.groupby(work["ticker"], sort=False).transform(
        lambda s: s.rolling(window, min_periods=window).std()
    )

    out = work[["date", "ticker"]].copy()
    out["sigma"] = sigma
    entry = g["adj_open"].shift(-1)
    for h in cfg["task"]["horizons"]:
        fwd = g["adj_open"].shift(-(1 + h)) / entry - 1
        if label_cfg["method"] == "vol_adjusted":
            thr = float(label_cfg["k"]) * sigma * np.sqrt(h)
        else:
            thr = pd.Series(float(label_cfg["fixed_thresholds"][h]), index=work.index)
        label = pd.Series(np.nan, index=work.index)
        valid = fwd.notna() & thr.notna()
        label[valid] = HOLD
        label[valid & (fwd > thr)] = BUY
        label[valid & (fwd < -thr)] = SELL
        out[f"fwd_ret_{h}"] = fwd
        out[f"thr_{h}"] = thr
        out[f"label_{h}"] = label
        out[f"label_end_{h}"] = g["date"].shift(-(1 + h))
    return out
