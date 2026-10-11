"""Assemble the modelling table: one row per (date, stock) with features and labels."""
from __future__ import annotations

import pandas as pd

from .features import FEATURES, compute_features
from .labels import compute_labels


def build_dataset(prices: pd.DataFrame, cfg: dict, keep_burn_in: bool = False) -> pd.DataFrame:
    """Join features and labels. Every model sees exactly the rows returned here.

    Rows with any missing feature (indicator warm-up) are dropped, then the first
    `burn_in_days` trading days are dropped so causal bucket cut-points exist for Jev.
    Rows with a missing label for a horizon are kept and excluded per horizon later.

    keep_burn_in=True keeps the burn-in rows. Only the Jev state builder uses it, as the
    earlier history that the first modelling rows are bucketed against.
    """
    market = cfg["data"]["market_ticker"]
    features = compute_features(prices, market)
    labels = compute_labels(prices[prices["ticker"] != market], cfg)
    ds = features.merge(labels, on=["date", "ticker"], how="inner", validate="one_to_one")
    ds = ds.dropna(subset=FEATURES)

    dates = pd.DatetimeIndex(sorted(ds["date"].unique()))
    burn_in = int(cfg["dataset"]["burn_in_days"])
    if len(dates) <= burn_in:
        raise ValueError("Not enough history after feature warm-up for the burn-in period.")
    if not keep_burn_in:
        ds = ds[ds["date"] >= dates[burn_in]]
    return ds.sort_values(["date", "ticker"]).reset_index(drop=True)
