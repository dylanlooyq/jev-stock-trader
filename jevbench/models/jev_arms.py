"""Jev arms of the benchmark. They read saved Jev outputs; they never call the API.

Signal arms use Jev's own class probabilities directly (zero training on our labels).
Head arms train a gradient-boosted model on Jev's outputs, with or without the
controlled features, using exactly the tuning procedure of the GBT baseline.
"""
from __future__ import annotations

import numpy as np

from .. import NO_PREDICTION
from ..features import FEATURES
from ..jev import VARIANTS, output_columns
from .base import Model, macro_f1
from .classical import GradientBoostedTrees


class JevSignal(Model):
    family = "jev"

    def __init__(self, model_id: str, variant: str):
        self.model_id = model_id
        self.prefix = VARIANTS[variant]
        self.required_columns = (f"{self.prefix}_status",)

    def _predict(self, df, horizon):
        proba = df[[f"{self.prefix}_{k}_{horizon}" for k in ("p_sell", "p_hold", "p_buy")]].to_numpy(dtype=float)
        valid = np.isfinite(proba).all(axis=1)
        pred = np.full(len(df), NO_PREDICTION)
        pred[valid] = proba[valid].argmax(axis=1)
        return pred, proba

    def fit(self, frames, label_col, seed):
        self.horizon_ = int(label_col.rsplit("_", 1)[1])
        val_pred, _ = self._predict(frames["val"], self.horizon_)
        return {"val_macro_f1": macro_f1(frames["val"][label_col], val_pred), "n_configs": 1}

    def predict(self, df):
        return self._predict(df, self.horizon_)


def make_jev_models(cfg: dict) -> dict:
    """Factories for the six Jev arms, keyed by the names used in models.enabled."""
    horizons = list(cfg["task"]["horizons"])
    section, n_jobs = cfg["models"]["gbt"], cfg["models"]["n_jobs"]
    factories = {}
    for variant, prefix in VARIANTS.items():
        jev_cols = output_columns(prefix, horizons)
        required = (f"{prefix}_status",)
        factories[f"jev_signal_{variant}"] = lambda v=variant: JevSignal(f"jev_signal_{v}", v)
        factories[f"jev_head_{variant}"] = lambda v=variant, c=jev_cols, r=required: GradientBoostedTrees(
            f"jev_head_{v}", section, c, n_jobs, family="jev", required_columns=r)
        factories[f"jev_plus_controlled_{variant}"] = lambda v=variant, c=jev_cols, r=required: GradientBoostedTrees(
            f"jev_plus_controlled_{v}", section, [*FEATURES, *c], n_jobs, family="jev", required_columns=r)
    return factories
