"""Arms for external decision models (Jev, and any provider registered later).

They read saved provider outputs; they never call an API. Signal arms use the
provider's own class probabilities directly (zero training on our labels). Head arms
train a gradient-boosted model on the provider's outputs, with or without the
controlled features, using exactly the tuning procedure of the GBT baseline.
"""
from __future__ import annotations

import numpy as np

from .. import NO_PREDICTION
from ..features import FEATURES
from ..providers import PROVIDERS, VARIANTS, arm_name, prefix
from .base import Model, macro_f1
from .classical import GradientBoostedTrees

OUTPUT_KINDS = ("p_sell", "p_hold", "p_buy", "up", "big")


def output_columns(col_prefix: str, horizons: list[int], kinds=OUTPUT_KINDS) -> list[str]:
    return [f"{col_prefix}_{kind}_{h}" for h in horizons for kind in kinds]


class ExternalSignal(Model):
    def __init__(self, model_id: str, provider: str, variant: str):
        self.model_id = model_id
        self.family = provider
        self.prefix = prefix(provider, variant)
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


def make_external_models(cfg: dict) -> dict:
    """Factories for the six arms of every registered provider, keyed by arm name."""
    horizons = list(cfg["task"]["horizons"])
    section, n_jobs = cfg["models"]["gbt"], cfg["models"]["n_jobs"]
    factories = {}
    for provider in PROVIDERS:
        for variant in VARIANTS:
            cols = output_columns(prefix(provider, variant), horizons)
            required = (f"{prefix(provider, variant)}_status",)
            signal, head, plus = (arm_name(provider, k, variant) for k in ("signal", "head", "plus_controlled"))
            factories[signal] = lambda n=signal, p=provider, v=variant: ExternalSignal(n, p, v)
            factories[head] = lambda n=head, p=provider, c=cols, r=required: GradientBoostedTrees(
                n, section, c, n_jobs, family=p, required_columns=r)
            factories[plus] = lambda n=plus, p=provider, c=cols, r=required: GradientBoostedTrees(
                n, section, [*FEATURES, *c], n_jobs, family=p, required_columns=r)
    return factories
