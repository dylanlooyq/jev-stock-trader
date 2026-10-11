"""Reference baselines and tuned traditional classifiers."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .base import Model, macro_f1


def class_prior(y) -> np.ndarray:
    counts = np.bincount(np.asarray(y, dtype=int), minlength=3).astype(float)
    return counts / counts.sum()


class MajorityClass(Model):
    """Always predicts the most frequent training class; probabilities are the class prior."""

    model_id, family = "majority", "baseline"

    def fit(self, frames, label_col, seed):
        train_prior = class_prior(frames["train"][label_col])
        val_pred = np.full(len(frames["val"]), train_prior.argmax())
        self.prior_ = class_prior(frames["trainval"][label_col])
        return {"val_macro_f1": macro_f1(frames["val"][label_col], val_pred), "n_configs": 1}

    def predict(self, df):
        return np.full(len(df), self.prior_.argmax()), np.tile(self.prior_, (len(df), 1))


class StratifiedRandom(Model):
    """Draws a class at random with the training class frequencies.

    This is the no-skill reference for macro-F1: it scores about 1/3 on balanced
    classes, far above the majority baseline, without using any feature.
    """

    model_id, family = "stratified_random", "baseline"

    def fit(self, frames, label_col, seed):
        self.rng_ = np.random.default_rng(seed)
        train_prior = class_prior(frames["train"][label_col])
        val_pred = self.rng_.choice(3, size=len(frames["val"]), p=train_prior)
        self.prior_ = class_prior(frames["trainval"][label_col])
        return {"val_macro_f1": macro_f1(frames["val"][label_col], val_pred), "n_configs": 1}

    def predict(self, df):
        pred = self.rng_.choice(3, size=len(df), p=self.prior_)
        return pred, np.tile(self.prior_, (len(df), 1))


class TunedClassifier(Model):
    """Grid of configurations scored by validation macro-F1, then refit on train + validation.

    All preprocessing lives inside the estimator, so it is fitted on fitting rows only.
    """

    def __init__(self, model_id: str, section: dict, feature_cols: list[str], n_jobs: int = -1,
                 family: str = "classifier", required_columns: tuple[str, ...] = ()):
        self.model_id = model_id
        self.section = section
        self.feature_cols = list(feature_cols)
        self.n_jobs = n_jobs
        self.family = family
        self.required_columns = required_columns

    def build(self, params: dict, seed: int):
        raise NotImplementedError

    def _xy(self, df: pd.DataFrame, label_col: str):
        return df[self.feature_cols].to_numpy(dtype=float), df[label_col].to_numpy(dtype=int)

    def fit(self, frames, label_col, seed):
        x_train, y_train = self._xy(frames["train"], label_col)
        x_val, y_val = self._xy(frames["val"], label_col)
        scores = []
        for params in self.section["grid"]:
            estimator = self.build(params, seed).fit(x_train, y_train)
            scores.append(macro_f1(y_val, self._predict_with(estimator, x_val)[0]))
        best = int(np.argmax(scores))
        self.estimator_ = self.build(self.section["grid"][best], seed).fit(*self._xy(frames["trainval"], label_col))
        return {"params": self.section["grid"][best], "val_macro_f1": float(scores[best]),
                "n_configs": len(scores)}

    @staticmethod
    def _predict_with(estimator, x):
        proba = np.zeros((len(x), 3))
        proba[:, np.asarray(estimator.classes_, dtype=int)] = estimator.predict_proba(x)
        return proba.argmax(axis=1), proba

    def predict(self, df):
        return self._predict_with(self.estimator_, df[self.feature_cols].to_numpy(dtype=float))


class LogReg(TunedClassifier):
    def build(self, params, seed):
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(C=params["C"], class_weight=params["class_weight"],
                               max_iter=int(self.section["max_iter"])),
        )


class RandomForest(TunedClassifier):
    def build(self, params, seed):
        return RandomForestClassifier(
            n_estimators=int(self.section["n_estimators"]), max_samples=self.section["max_samples"],
            max_depth=params["max_depth"], min_samples_leaf=params["min_samples_leaf"],
            class_weight=params["class_weight"], max_features="sqrt",
            n_jobs=self.n_jobs, random_state=seed,
        )


class GradientBoostedTrees(TunedClassifier):
    """LightGBM. Missing feature values are handled natively, which the Jev arms rely on."""

    def build(self, params, seed):
        from lightgbm import LGBMClassifier

        return LGBMClassifier(
            objective="multiclass", num_leaves=params["num_leaves"],
            learning_rate=params["learning_rate"], n_estimators=params["n_estimators"],
            class_weight=params["class_weight"],
            min_child_samples=int(self.section["min_child_samples"]),
            subsample=self.section["subsample"], subsample_freq=1,
            colsample_bytree=self.section["colsample_bytree"],
            random_state=seed, n_jobs=self.n_jobs, verbose=-1,
            deterministic=True, force_row_wise=True,
        )
