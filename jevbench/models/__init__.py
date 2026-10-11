"""Model registry: builds the models named in config `models.enabled`."""
from __future__ import annotations

from ..features import FEATURES
from .base import Model
from .classical import GradientBoostedTrees, LogReg, MajorityClass, RandomForest, StratifiedRandom
from .jev_arms import make_external_models
from .rules import MomentumRule, MovingAverageCrossRule


def make_models(cfg: dict) -> list[Model]:
    m, n_jobs = cfg["models"], cfg["models"]["n_jobs"]
    factories = {
        "majority": MajorityClass,
        "stratified_random": StratifiedRandom,
        "logreg": lambda: LogReg("logreg", m["logreg"], FEATURES, n_jobs),
        "random_forest": lambda: RandomForest("random_forest", m["random_forest"], FEATURES, n_jobs),
        "gbt": lambda: GradientBoostedTrees("gbt", m["gbt"], FEATURES, n_jobs),
        "momentum_rule": lambda: MomentumRule("momentum_rule", m["momentum_rule"]),
        "ma_cross_rule": lambda: MovingAverageCrossRule("ma_cross_rule", m["ma_cross_rule"]),
        **make_external_models(cfg),
    }
    unknown = [name for name in m["enabled"] if name not in factories]
    if unknown:
        raise ValueError(f"Unknown models in config: {unknown}")
    return [factories[name]() for name in m["enabled"]]
