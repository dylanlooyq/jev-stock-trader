"""Common interface for every model in the benchmark."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score


def macro_f1(y_true, pred) -> float:
    return float(f1_score(y_true, pred, labels=[0, 1, 2], average="macro", zero_division=0))


class Model:
    """A model is fitted once per (fold, horizon).

    fit() receives `train`, `val` and `trainval` frames. Any tuning must use `val` only;
    the final fit may use `trainval`. It never sees test rows. predict() returns integer
    classes and, where the model has meaningful probabilities, an (n, 3) array ordered
    SELL, HOLD, BUY; otherwise None.
    """

    model_id: str = "model"
    family: str = "classifier"   # baseline | classifier | rule | jev
    has_proba: bool = True
    required_columns: tuple[str, ...] = ()

    def fit(self, frames: dict[str, pd.DataFrame], label_col: str, seed: int) -> dict:
        raise NotImplementedError

    def predict(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray | None]:
        raise NotImplementedError

    def rank_score(self, df: pd.DataFrame, pred: np.ndarray, proba: np.ndarray | None) -> np.ndarray:
        """How attractive each row is to hold; higher is better. Used by the ranking portfolio.

        Probabilistic models use P(BUY) - P(SELL). A missing score means the row is never held.
        """
        if proba is not None:
            return proba[:, 2] - proba[:, 0]
        return np.where(pred < 0, np.nan, pred.astype(float) - 1.0)
