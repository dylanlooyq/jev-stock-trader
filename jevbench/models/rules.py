"""Simple trading rules. They use columns of the controlled feature set only.

Rules have no probabilities. A small fixed set of lookbacks is scored on validation
data, with the same selection procedure as the tuned classifiers.
"""
from __future__ import annotations

import numpy as np

from .. import BUY, HOLD, SELL
from .base import Model, macro_f1


class RuleModel(Model):
    family, has_proba = "rule", False

    def __init__(self, model_id: str, section: dict):
        self.model_id = model_id
        self.section = section

    def signal(self, df, params) -> np.ndarray:
        raise NotImplementedError

    def fit(self, frames, label_col, seed):
        y_val = frames["val"][label_col].to_numpy(dtype=int)
        scores = [macro_f1(y_val, self.signal(frames["val"], p)) for p in self.section["grid"]]
        best = int(np.argmax(scores))
        self.params_ = self.section["grid"][best]
        return {"params": self.params_, "val_macro_f1": float(scores[best]), "n_configs": len(scores)}

    def predict(self, df):
        return self.signal(df, self.params_), None

    def strength(self, df, params) -> np.ndarray:
        raise NotImplementedError

    def rank_score(self, df, pred, proba):
        return self.strength(df, self.params_)


class MomentumRule(RuleModel):
    """BUY after a strong trailing return, SELL after a weak one.

    The trailing return is scaled by the stock's own volatility; `band` is the
    dead zone, in volatility units, inside which the rule says HOLD.
    """

    def strength(self, df, params):
        lookback = int(params["lookback"])
        return df[f"ret_{lookback}"].to_numpy() / (df["vol_60"].to_numpy() * np.sqrt(lookback))

    def signal(self, df, params):
        z, band = self.strength(df, params), float(params["band"])
        return np.where(z > band, BUY, np.where(z < -band, SELL, HOLD))


class MovingAverageCrossRule(RuleModel):
    """BUY when the fast average is above the slow one, SELL when below.

    dist_sma_n = close / sma_n - 1, so sma_fast > sma_slow exactly when
    dist_sma_slow > dist_sma_fast. With `confirm`, price must also be on the same
    side of the fast average, otherwise the rule says HOLD.
    """

    def strength(self, df, params):
        """Gap between the fast and slow averages: positive when the fast one is higher."""
        return (df[f"dist_sma_{int(params['slow'])}"] - df[f"dist_sma_{int(params['fast'])}"]).to_numpy()

    def signal(self, df, params):
        fast = df[f"dist_sma_{int(params['fast'])}"].to_numpy()
        slow = df[f"dist_sma_{int(params['slow'])}"].to_numpy()
        up, down = slow > fast, slow < fast
        if params["confirm"]:
            up, down = up & (fast > 0), down & (fast < 0)
        return np.where(up, BUY, np.where(down, SELL, HOLD))
