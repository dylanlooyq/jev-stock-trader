"""Classification metrics. Trading metrics live in backtest.py.

Confusion matrices are 3 x 4: rows are the true class, columns are SELL, HOLD, BUY and
"no prediction". A row for which a model failed to return a valid class counts as a
miss for its true class, so failures can never improve a score.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import BUY, CLASS_NAMES, NO_PREDICTION, SELL

PROBA_COLUMNS = ["p_sell", "p_hold", "p_buy"]


def confusion_matrix(y_true, pred) -> np.ndarray:
    y_true = np.asarray(y_true, dtype=int)
    pred = np.asarray(pred, dtype=int)
    col = np.where(pred == NO_PREDICTION, 3, pred)
    cm = np.zeros((3, 4), dtype=np.int64)
    np.add.at(cm, (y_true, col), 1)
    return cm


def _safe_div(num, den):
    num, den = np.asarray(num, dtype=float), np.asarray(den, dtype=float)
    return np.divide(num, den, out=np.zeros_like(num), where=den > 0)


def macro_f1_from_cm(cm: np.ndarray) -> np.ndarray:
    """Macro-F1 over the three classes. Accepts a batch of matrices shaped (..., 3, 4)."""
    cm = np.asarray(cm, dtype=float)
    tp = np.einsum("...ii->...i", cm[..., :3])
    predicted = cm[..., :3].sum(axis=-2)
    actual = cm.sum(axis=-1)
    return _safe_div(2 * tp, predicted + actual).mean(axis=-1)


def metrics_from_cm(cm: np.ndarray) -> dict:
    cm = np.asarray(cm, dtype=float)
    tp = np.diag(cm[:, :3])
    predicted = cm[:, :3].sum(axis=0)
    actual = cm.sum(axis=1)
    precision = _safe_div(tp, predicted)
    recall = _safe_div(tp, actual)
    f1 = _safe_div(2 * tp, predicted + actual)
    n = cm.sum()
    present = actual > 0
    return {
        "n": int(n),
        "macro_f1": float(f1.mean()),
        "balanced_accuracy": float(recall[present].mean()) if present.any() else float("nan"),
        "accuracy": float(tp.sum() / n) if n else float("nan"),
        "precision": dict(zip(CLASS_NAMES, precision.round(6).tolist())),
        "recall": dict(zip(CLASS_NAMES, recall.round(6).tolist())),
        "f1": dict(zip(CLASS_NAMES, f1.round(6).tolist())),
        "true_distribution": dict(zip(CLASS_NAMES, _safe_div(actual, n).round(6).tolist())),
        "predicted_distribution": dict(zip(CLASS_NAMES, _safe_div(predicted, n).round(6).tolist())),
        "no_prediction_rate": float(cm[:, 3].sum() / n) if n else float("nan"),
        "confusion_matrix": cm.astype(int).tolist(),
    }


def probability_metrics(y_true, proba) -> dict:
    """Log loss, multiclass Brier score and top-label ECE over rows with valid probabilities."""
    y_true = np.asarray(y_true, dtype=int)
    proba = np.asarray(proba, dtype=float)
    valid = np.isfinite(proba).all(axis=1)
    if not valid.any():
        return {"proba_coverage": 0.0}
    y, p = y_true[valid], proba[valid]
    p = p / p.sum(axis=1, keepdims=True)
    onehot = np.eye(3)[y]
    log_loss = -np.log(np.clip(p[np.arange(len(y)), y], 1e-12, 1.0)).mean()
    brier = ((p - onehot) ** 2).sum(axis=1).mean()
    confidence, top = p.max(axis=1), p.argmax(axis=1)
    correct = (top == y).astype(float)
    bins = np.minimum((confidence * 10).astype(int), 9)
    ece, reliability = 0.0, []
    for b in range(10):
        in_bin = bins == b
        if in_bin.any():
            gap = abs(correct[in_bin].mean() - confidence[in_bin].mean())
            ece += gap * in_bin.mean()
            reliability.append({
                "bin": f"{b / 10:.1f}-{(b + 1) / 10:.1f}", "n": int(in_bin.sum()),
                "mean_confidence": float(confidence[in_bin].mean()),
                "accuracy": float(correct[in_bin].mean()),
            })
    return {
        "proba_coverage": float(valid.mean()), "log_loss": float(log_loss),
        "brier": float(brier), "ece": float(ece), "reliability": reliability,
    }


def directional_metrics(y_true, pred, fwd_ret) -> dict:
    """Does the model separate up from down, as opposed to large from small moves?"""
    y_true, pred = np.asarray(y_true, dtype=int), np.asarray(pred, dtype=int)
    fwd_ret = np.asarray(fwd_ret, dtype=float)
    out = {}
    for name, cls in (("SELL", SELL), ("HOLD", 1), ("BUY", BUY)):
        mask = pred == cls
        out[f"mean_fwd_ret_pred_{name}"] = float(fwd_ret[mask].mean()) if mask.any() else float("nan")
    both = np.isin(pred, (SELL, BUY)) & np.isin(y_true, (SELL, BUY))
    out["directional_hit_rate"] = float((pred[both] == y_true[both]).mean()) if both.any() else float("nan")
    out["directional_n"] = int(both.sum())
    return out


def evaluate_predictions(df: pd.DataFrame) -> dict:
    """Full metric set for one model and horizon. Needs y_true, pred, fwd_ret and p_* columns."""
    result = metrics_from_cm(confusion_matrix(df["y_true"], df["pred"]))
    result.update(directional_metrics(df["y_true"], df["pred"], df["fwd_ret"]))
    if df[PROBA_COLUMNS].notna().any().any():
        result.update(probability_metrics(df["y_true"], df[PROBA_COLUMNS].to_numpy()))
    else:
        result["proba_coverage"] = 0.0
    return result


def macro_f1_by(df: pd.DataFrame, by: str) -> dict:
    return {
        str(key): float(macro_f1_from_cm(confusion_matrix(grp["y_true"], grp["pred"])))
        for key, grp in df.groupby(by, observed=True)
    }


def market_regimes(dataset: pd.DataFrame) -> pd.DataFrame:
    """Label each date by market trend and volatility, using information available that day.

    Trend: market above or below its 200-day average. Volatility: 20-day market
    volatility above or below its own expanding median up to that date.
    """
    daily = dataset.groupby("date")[["mkt_dist_sma_200", "mkt_vol_20"]].first().sort_index()
    median_so_far = daily["mkt_vol_20"].expanding(min_periods=1).median()
    trend = np.where(daily["mkt_dist_sma_200"] > 0, "uptrend", "downtrend")
    vol = np.where(daily["mkt_vol_20"] > median_so_far, "high_vol", "low_vol")
    return pd.DataFrame({"date": daily.index, "regime": [f"{t}/{v}" for t, v in zip(trend, vol)]})
