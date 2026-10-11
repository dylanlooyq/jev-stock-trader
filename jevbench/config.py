"""Experiment configuration: one YAML file, optional override files."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "experiment.yaml"


def deep_update(base: dict, updates: dict) -> dict:
    """Recursively merge `updates` into a copy of `base`."""
    out = copy.deepcopy(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_update(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: str | Path | None = None, overrides: list[str | Path | dict] | None = None) -> dict:
    with open(path or DEFAULT_CONFIG, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    for item in overrides or []:
        if not isinstance(item, dict):
            with open(item, encoding="utf-8") as fh:
                item = yaml.safe_load(fh)
        cfg = deep_update(cfg, item)
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict) -> None:
    task, splits = cfg["task"], cfg["splits"]
    if task["primary_horizon"] not in task["horizons"]:
        raise ValueError("primary_horizon must be one of task.horizons")
    if task["label"]["method"] not in ("vol_adjusted", "fixed"):
        raise ValueError("task.label.method must be vol_adjusted or fixed")
    if cfg["jev"]["model"].endswith(("latest", "preview")):
        raise ValueError("jev.model must be a pinned version id, not an alias")
    if cfg["backtest"]["mode"] not in ("long_only", "long_short"):
        raise ValueError("backtest.mode must be long_only or long_short")
    if cfg["backtest"]["primary_rule"] not in ("rank", "buy_names"):
        raise ValueError("backtest.primary_rule must be rank or buy_names")
    if cfg["backtest"]["risk_free"] not in ("tbill", "zero"):
        raise ValueError("backtest.risk_free must be tbill or zero")
    if len(set(cfg["data"]["tickers"])) != len(cfg["data"]["tickers"]):
        raise ValueError("data.tickers contains duplicates")
    if splits["first_test_start"] >= splits["holdout_start"]:
        raise ValueError("first_test_start must precede holdout_start")


def config_hash(cfg: dict) -> str:
    blob = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def embargo_days(cfg: dict, horizon: int) -> int:
    value = cfg["splits"]["embargo"]
    return horizon if value == "horizon" else int(value)
