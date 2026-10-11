"""Time-aware uncertainty: paired stationary block bootstrap over dates, Holm correction.

Whole dates are resampled, so the cross-section on a date stays together, and blocks of
consecutive dates preserve serial dependence from overlapping forward-return labels.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .evaluate import confusion_matrix, macro_f1_from_cm


def block_length(cfg: dict, horizon: int) -> int:
    return max(int(cfg["stats"]["min_block_days"]), 2 * horizon)


def stationary_bootstrap_indices(n: int, block_len: float, n_boot: int, rng: np.random.Generator) -> np.ndarray:
    """Politis-Romano stationary bootstrap. Returns an (n_boot, n) array of indices into range(n)."""
    new_block = rng.random((n_boot, n)) < 1.0 / block_len
    new_block[:, 0] = True
    starts = rng.integers(0, n, size=(n_boot, n))
    pos = np.arange(n)
    block_pos = np.maximum.accumulate(np.where(new_block, pos, 0), axis=1)
    block_start = np.take_along_axis(starts, block_pos, axis=1)
    return (block_start + pos - block_pos) % n


def per_date_confusions(df: pd.DataFrame, dates: pd.DatetimeIndex) -> np.ndarray:
    """Stack one 3 x 4 confusion matrix per date, aligned to `dates`."""
    out = np.zeros((len(dates), 3, 4), dtype=np.int32)
    position = pd.Series(np.arange(len(dates)), index=dates)
    for date, grp in df.groupby("date"):
        out[position[date]] = confusion_matrix(grp["y_true"], grp["pred"])
    return out


def _ci_and_p(observed: float, boot: np.ndarray, alpha: float) -> dict:
    low, high = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    # Two-sided p-value from the bootstrap distribution centred on the null of no difference.
    extreme = np.abs(boot - boot.mean()) >= abs(observed)
    return {
        "diff": float(observed), "ci_low": float(low), "ci_high": float(high),
        "p_value": float((1 + extreme.sum()) / (len(boot) + 1)),
    }


def paired_macro_f1_bootstrap(cm_a: np.ndarray, cm_b: np.ndarray, block_len: float,
                              n_boot: int, seed: int, alpha: float = 0.05, chunk: int = 200) -> dict:
    """Difference in pooled macro-F1 (A minus B) with a paired block-bootstrap interval."""
    if cm_a.shape != cm_b.shape:
        raise ValueError("Both models must be evaluated on the same dates.")
    rng = np.random.default_rng(seed)
    observed = float(macro_f1_from_cm(cm_a.sum(axis=0)) - macro_f1_from_cm(cm_b.sum(axis=0)))
    boot = np.empty(n_boot)
    for start in range(0, n_boot, chunk):
        size = min(chunk, n_boot - start)
        idx = stationary_bootstrap_indices(len(cm_a), block_len, size, rng)
        boot[start:start + size] = (
            macro_f1_from_cm(cm_a[idx].sum(axis=1)) - macro_f1_from_cm(cm_b[idx].sum(axis=1))
        )
    return _ci_and_p(observed, boot, alpha)


def sharpe(returns: np.ndarray, axis: int = -1) -> np.ndarray:
    sd = returns.std(axis=axis, ddof=1)
    return np.divide(returns.mean(axis=axis), sd, out=np.zeros_like(sd, dtype=float), where=sd > 0) * np.sqrt(252)


def paired_sharpe_bootstrap(ret_a: np.ndarray, ret_b: np.ndarray, block_len: float,
                            n_boot: int, seed: int, alpha: float = 0.05) -> dict:
    """Difference in annualised Sharpe ratio (A minus B) on the same dates."""
    ret_a, ret_b = np.asarray(ret_a, dtype=float), np.asarray(ret_b, dtype=float)
    if ret_a.shape != ret_b.shape:
        raise ValueError("Both return series must cover the same dates.")
    rng = np.random.default_rng(seed)
    idx = stationary_bootstrap_indices(len(ret_a), block_len, n_boot, rng)
    boot = sharpe(ret_a[idx]) - sharpe(ret_b[idx])
    return _ci_and_p(float(sharpe(ret_a) - sharpe(ret_b)), boot, alpha)


def holm(p_values: list[float]) -> list[float]:
    """Holm step-down adjusted p-values, returned in the input order."""
    m = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p_values[i])
        adjusted[i] = min(1.0, running)
    return adjusted.tolist()
