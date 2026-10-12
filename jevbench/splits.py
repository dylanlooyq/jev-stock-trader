"""Chronological walk-forward folds with purging and an embargo.

For a row at trading-day index i and horizon h, the label uses prices up to index
i + 1 + h. A row may be used for fitting only if its label window closes before the
next segment starts. `gap = h + 1 + embargo` trading days are dropped before each
boundary, and the label end date is checked again per row in case a stock's own
calendar has holes.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .config import embargo_days


@dataclass(frozen=True)
class Fold:
    fold_id: int
    train_end: pd.Timestamp   # exclusive
    val_start: pd.Timestamp
    val_end: pd.Timestamp     # exclusive
    test_start: pd.Timestamp
    test_end: pd.Timestamp    # exclusive
    is_holdout: bool
    train_start: pd.Timestamp | None = None   # inclusive; None means the window expands from the first row

    def to_dict(self) -> dict:
        return {k: (str(v.date()) if isinstance(v, pd.Timestamp) else v) for k, v in asdict(self).items()}


def make_folds(dates, cfg: dict, horizon: int) -> list[Fold]:
    """Yearly (by default) test folds from first_test_start to the end of `dates`.

    By default the training window expands from the first row. With
    `splits.train_window_months = W` it is instead the W months before the validation
    window (a rolling window), and each fold's test period is `test_months` long.
    A rolling fold whose validation window has fewer than `splits.min_val_days` trading
    days after purging is skipped, so a horizon can have no folds at all: the purge
    gap grows with the horizon and eats short windows.
    """
    s = cfg["splits"]
    window = s.get("train_window_months")
    min_val_days = int(s.get("min_val_days") or 0)
    dates = pd.DatetimeIndex(sorted(pd.unique(pd.DatetimeIndex(dates))))
    gap = horizon + 1 + embargo_days(cfg, horizon)
    holdout_start = pd.Timestamp(s["holdout_start"])
    step = pd.DateOffset(months=int(s["test_months"]))

    boundary = pd.Timestamp(s["first_test_start"])
    while boundary < holdout_start:
        boundary = boundary + step
    if boundary != holdout_start:
        raise ValueError("holdout_start must coincide with a fold boundary")

    folds: list[Fold] = []
    boundaries = []
    boundary = pd.Timestamp(s["first_test_start"])
    while boundary <= dates[-1]:
        boundaries.append(boundary)
        boundary = boundary + step

    for test_start in boundaries:
        test_end = test_start + step
        ts_idx = dates.searchsorted(test_start)
        if ts_idx >= len(dates):
            break
        vs_idx = dates.searchsorted(test_start - pd.DateOffset(months=int(s["validation_months"])))
        train_end_idx = vs_idx - gap
        val_end_idx = ts_idx - gap
        train_start = None
        if window:
            if val_end_idx - vs_idx < min_val_days:
                continue   # validation window too short once purged; this fold cannot be tuned
            tr_idx = dates.searchsorted(dates[vs_idx] - pd.DateOffset(months=int(window)))
            if train_end_idx - tr_idx < int(s["min_train_days"]):
                continue
            train_start = dates[tr_idx]
        elif train_end_idx < int(s["min_train_days"]):
            raise ValueError(
                f"Fold starting {test_start.date()} has fewer than {s['min_train_days']} training days."
            )
        if val_end_idx <= vs_idx:
            raise ValueError("Validation window is empty after purging.")
        folds.append(Fold(
            fold_id=len(folds),
            train_end=dates[train_end_idx], val_start=dates[vs_idx], val_end=dates[val_end_idx],
            test_start=dates[ts_idx], test_end=test_end,
            is_holdout=bool(test_start >= holdout_start), train_start=train_start,
        ))
    return folds


def fold_frames(ds: pd.DataFrame, fold: Fold, horizon: int) -> dict[str, pd.DataFrame]:
    """Slice the dataset into train / val / trainval / test for one fold and horizon."""
    labelled = ds[ds[f"label_{horizon}"].notna()]
    date, label_end = labelled["date"], labelled[f"label_end_{horizon}"]
    from_start = (date >= fold.train_start) if fold.train_start is not None else True
    train = labelled[from_start & (date < fold.train_end) & (label_end < fold.val_start)]
    val = labelled[(date >= fold.val_start) & (date < fold.val_end) & (label_end < fold.test_start)]
    trainval = labelled[from_start & (date < fold.val_end) & (label_end < fold.test_start)]
    test = labelled[(date >= fold.test_start) & (date < fold.test_end)]
    return {"train": train, "val": val, "trainval": trainval, "test": test}


def assert_holdout_locked(ds: pd.DataFrame, folds: list[Fold], cfg: dict) -> None:
    holdout_start = pd.Timestamp(cfg["splits"]["holdout_start"])
    if any(f.is_holdout for f in folds) or ds["date"].max() >= holdout_start:
        raise RuntimeError("Holdout data is present in a run that did not unlock it.")
    for h in cfg["task"]["horizons"]:
        ends = ds[f"label_end_{h}"].dropna()
        if len(ends) and ends.max() >= holdout_start:
            raise RuntimeError("A development label depends on holdout-period prices.")
