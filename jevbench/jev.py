"""Jev (TypeSafe System One) integration: state construction, API client, annotation.

STATUS: written from the vendor's published API reference and exercised only against a
mock transport. It has NOT been run against the live API. Verify with a small approved
pilot before any full run.

Design points that protect the experiment:
- The state carries no ticker, company name, calendar date or absolute price level.
- Numbers are bucketed in code against cut-points computed from strictly earlier dates,
  so a row's state never depends on the fold and never on the future.
- Worked examples, when used, are rows whose label window closed before the month began.
- Each request is cached by content hash, and the pinned model id is enforced.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import CLASS_NAMES
from .config import REPO_ROOT
from .features import FEATURES
from .models.jev_arms import output_columns
from .providers import PROVIDERS, prefix

BUCKET_LABELS = ["very low", "low", "typical", "high", "very high"]
OPTION_ORDERS = [("BUY", "HOLD", "SELL"), ("HOLD", "SELL", "BUY"), ("SELL", "BUY", "HOLD")]
VARIANTS = PROVIDERS["jev"]["prefix"]   # variant name -> column prefix

# feature -> (group, description, format)
FEATURE_TEXT = {
    **{f"ret_{n}": ("asset", f"return over the past {n} trading day{'s' if n > 1 else ''}", "pct")
       for n in (1, 5, 20, 60, 120, 250)},
    "vol_20": ("asset", "daily volatility over the past 20 trading days", "upct"),
    "vol_60": ("asset", "daily volatility over the past 60 trading days", "upct"),
    "rsi_14": ("asset", "14-day relative strength index, 0 to 100", "num"),
    "dist_sma_20": ("asset", "price versus its 20-day average", "pct"),
    "dist_sma_50": ("asset", "price versus its 50-day average", "pct"),
    "dist_sma_200": ("asset", "price versus its 200-day average", "pct"),
    "macd_hist": ("asset", "MACD histogram as a share of price", "pct"),
    "vol_ratio_20": ("asset", "trading volume today versus its 20-day average", "ratio"),
    "dist_52w_high": ("asset", "price versus its 52-week high", "pct"),
    "bb_z_20": ("asset", "distance from the 20-day average in standard deviations", "num"),
    "atr_14": ("asset", "average daily trading range over 14 days as a share of price", "upct"),
    "mkt_ret_5": ("market", "US stock market index return over the past 5 trading days", "pct"),
    "mkt_ret_20": ("market", "US stock market index return over the past 20 trading days", "pct"),
    "mkt_vol_20": ("market", "US stock market index daily volatility over the past 20 trading days", "upct"),
    "mkt_dist_sma_200": ("market", "US stock market index versus its 200-day average", "pct"),
    "rel_ret_20": ("asset", "return minus US stock market index return over the past 20 trading days", "pct"),
    "rel_ret_60": ("asset", "return minus US stock market index return over the past 60 trading days", "pct"),
    "xs_rank_ret_5": ("asset", "percentile of its 5-day return among the assets in its group today", "pctile"),
    "xs_rank_ret_20": ("asset", "percentile of its 20-day return among the assets in its group today", "pctile"),
    "xs_rank_ret_120": ("asset", "percentile of its 120-day return among the assets in its group today", "pctile"),
    "xs_rank_vol_20": ("asset", "percentile of its 20-day volatility among the assets in its group today", "pctile"),
}
assert set(FEATURE_TEXT) == set(FEATURES)

STATE_ABOUT = (
    "Technical snapshot of one traded asset taken at the market close. It belongs to a small "
    "group of assets of different kinds. Each reading gives its level compared with the recent "
    "range across that group, then the value."
)
EXAMPLES_ABOUT = (
    "Earlier snapshots of assets from the same group with what happened next. BUY means the price rose "
    "by more than the threshold, SELL means it fell by more than the threshold, HOLD means "
    "it stayed inside the threshold."
)


class JevError(Exception):
    pass


class JevModelMismatch(JevError):
    pass


class JevBudgetExceeded(JevError):
    pass


class JevMissingKey(JevError):
    pass


# --------------------------------------------------------------------------- state

def _format(value: float, kind: str) -> str:
    if kind == "pct":
        return f"{value * 100:+.1f}%"
    if kind == "upct":
        return f"{value * 100:.1f}%"
    if kind == "pctile":
        return f"{value * 100:.0f}th percentile"
    if kind == "ratio":
        return f"{value:.2f}x"
    return f"{value:.1f}"


def snapshot(values: np.ndarray, cutpoints: np.ndarray) -> dict:
    """Render one row's feature values as text. `cutpoints` has one row per feature."""
    out: dict[str, dict[str, str]] = {"asset": {}, "market": {}}
    for i, feature in enumerate(FEATURES):
        group, description, kind = FEATURE_TEXT[feature]
        bucket = BUCKET_LABELS[int(np.searchsorted(cutpoints[i], values[i], side="right"))]
        out[group][description] = f"{bucket} ({_format(float(values[i]), kind)})"
    return out


def move_threshold_text(cfg: dict, horizon: int) -> str:
    label = cfg["task"]["label"]
    if label["method"] == "vol_adjusted":
        return (f"{float(label['k']):g} times its typical {horizon}-day move, where the typical move "
                f"is its daily volatility over the past {int(label['vol_window'])} trading days "
                f"scaled to {horizon} trading day{'s' if horizon > 1 else ''}")
    return f"{float(label['fixed_thresholds'][horizon]) * 100:g}%"


def build_questions(cfg: dict) -> dict:
    """The fixed question set. Any edit here requires a new jev.wording_version."""
    questions = {}
    for h in cfg["task"]["horizons"]:
        days = f"{h} trading day{'s' if h > 1 else ''}"
        setup = (f"The asset is bought at the next market open and held for {days}. "
                 f"The threshold is {move_threshold_text(cfg, h)}.")
        criteria = {
            "BUY": "The price rises by more than the threshold.",
            "HOLD": "The price change stays within the threshold, up or down.",
            "SELL": "The price falls by more than the threshold.",
        }
        for i, order in enumerate(OPTION_ORDERS):
            questions[f"h{h}_signal_o{i}"] = {
                "type": "choice",
                "instructions": f"{setup} Which outcome is most likely for its price over that period?",
                "criteria": {name: criteria[name] for name in order},
            }
        questions[f"h{h}_up"] = {
            "type": "noul",
            "instructions": (f"The asset is bought at the next market open and held for {days}. "
                             "Will its price be higher at the end of that period than at the purchase?"),
        }
        questions[f"h{h}_big"] = {
            "type": "noul",
            "instructions": f"{setup} Will its price change over that period, up or down, be larger than the threshold?",
        }
    return questions


class JevContext:
    """Per-month causal cut-points and example sets for building states.

    `full` must be the dataset built with keep_burn_in=True so that the first
    modelling rows have earlier data to be bucketed against.
    """

    def __init__(self, full: pd.DataFrame, cfg: dict):
        self.cfg = cfg
        self.full = full.sort_values(["date", "ticker"]).reset_index(drop=True)
        self.dates = pd.DatetimeIndex(sorted(self.full["date"].unique()))
        self.horizons = list(cfg["task"]["horizons"])
        self._values = self.full[FEATURES].to_numpy(dtype=float)
        self._date_pos = self.dates.searchsorted(self.full["date"].to_numpy())
        self._cut_cache: dict[pd.Period, np.ndarray] = {}
        self._example_cache: dict[pd.Period, list[dict]] = {}

    def month_start_pos(self, month: pd.Period) -> int:
        """Index of the first trading date in `month`; everything before it is the past."""
        return int(self.dates.searchsorted(month.to_timestamp()))

    def cutpoints(self, month: pd.Period) -> np.ndarray:
        if month not in self._cut_cache:
            end = self.month_start_pos(month)
            start = max(0, end - int(self.cfg["jev"]["bucket_lookback_days"]))
            if end - start < 20:
                raise JevError(f"Fewer than 20 earlier trading days to bucket against for {month}.")
            window = self._values[(self._date_pos >= start) & (self._date_pos < end)]
            self._cut_cache[month] = np.quantile(window, self.cfg["jev"]["bucket_quantiles"], axis=0).T
        return self._cut_cache[month]

    def example_rows(self, month: pd.Period) -> pd.DataFrame:
        """Rows usable as examples in `month`: every horizon's label window closed before it began."""
        end = self.month_start_pos(month)
        if end == 0:
            return self.full.iloc[0:0]
        month_start = self.dates[end]
        start = max(0, end - int(self.cfg["jev"]["example_lookback_days"]))
        pool = self.full[(self._date_pos >= start) & (self._date_pos < end)]
        for h in self.horizons:
            pool = pool[pool[f"label_{h}"].notna() & (pool[f"label_end_{h}"] < month_start)]
        return pool

    def examples(self, month: pd.Period) -> list[dict]:
        if month not in self._example_cache:
            pool = self.example_rows(month)
            primary = f"label_{self.cfg['task']['primary_horizon']}"
            rng = np.random.default_rng([int(self.cfg["seed"]), month.year, month.month])
            picks = []
            for cls in range(3):
                candidates = pool.index[pool[primary] == cls].to_numpy()
                k = min(int(self.cfg["jev"]["examples_per_class"]), len(candidates))
                picks.extend(rng.choice(candidates, size=k, replace=False).tolist())
            rng.shuffle(picks)
            cut = self.cutpoints(month)
            self._example_cache[month] = [
                {
                    "snapshot": snapshot(self._values[i], cut),
                    "outcome": {
                        f"after {h} trading day{'s' if h > 1 else ''}":
                            CLASS_NAMES[int(self.full.at[i, f"label_{h}"])]
                        for h in self.horizons
                    },
                }
                for i in picks
            ]
        return self._example_cache[month]

    def state(self, row_index: int, with_examples: bool) -> dict:
        month = pd.Timestamp(self.full.at[row_index, "date"]).to_period("M")
        state = {"about": STATE_ABOUT, "snapshot": snapshot(self._values[row_index], self.cutpoints(month))}
        if with_examples:
            state["past_examples"] = {"about": EXAMPLES_ABOUT, "cases": self.examples(month)}
        return state


# --------------------------------------------------------------------------- client

def load_api_key() -> str | None:
    key = os.environ.get("TYPESAFE_API_KEY")
    env_file = REPO_ROOT / ".env"
    if not key and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "TYPESAFE_API_KEY":
                key = value.strip().strip("'\"")
    return key or None


def approx_tokens(payload: dict) -> int:
    """Rough offline token estimate (about 3.5 characters per token). Not the vendor's tokenizer."""
    return int(len(json.dumps(payload, ensure_ascii=False)) / 3.5)


def http_transport(endpoint: str, api_key: str, timeout: float):
    import requests

    session_local = threading.local()

    def send(payload: dict) -> tuple[int, dict, dict]:
        if not hasattr(session_local, "session"):
            session_local.session = requests.Session()
        resp = session_local.session.post(
            endpoint, json=payload, timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        try:
            body = resp.json()
        except ValueError:
            body = {"error": resp.text[:500]}
        return resp.status_code, body, dict(resp.headers)

    return send


class RateLimiter:
    """Spaces requests so both the request rate and the token rate stay under their limits."""

    def __init__(self, requests_per_s: float, tokens_per_s: float, safety: float = 0.8):
        self.requests_per_s = requests_per_s * safety
        self.tokens_per_s = tokens_per_s * safety
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self, tokens: int) -> None:
        interval = max(1.0 / self.requests_per_s, tokens / self.tokens_per_s)
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + interval
        if start > now:
            time.sleep(start - now)


class JevClient:
    """Cached, budget-guarded client for POST /v1/systemone.

    `transport` is a callable(payload) -> (status, body, headers); tests inject a mock.
    `approved_cost_usd` is a hard ceiling on spend for this client instance.
    """

    def __init__(self, cfg: dict, approved_cost_usd: float, transport=None, cache_path=None,
                 sleep=time.sleep, rate_limited: bool = True):
        self.jev = cfg["jev"]
        self._rate_limited = rate_limited
        self.model = self.jev["model"]
        self.approved_cost_usd = float(approved_cost_usd)
        self._sleep = sleep
        if transport is None:
            key = load_api_key()
            if not key:
                raise JevMissingKey("TYPESAFE_API_KEY is not set (environment or .env).")
            transport = http_transport(self.jev["endpoint"], key, float(self.jev["timeout_s"]))
        self._transport = transport
        self._limiter = RateLimiter(self.jev["rate_limit_requests_per_s"], self.jev["rate_limit_tokens_per_s"])
        path = Path(cache_path) if cache_path else REPO_ROOT / self.jev["cache_path"]
        if str(path) != ":memory:":
            path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, response TEXT, created_at TEXT)")
        self._lock = threading.Lock()
        self.stats = {"requests": 0, "cache_hits": 0, "input_tokens": 0, "failures": 0, "latency_s": 0.0}

    @property
    def spent_usd(self) -> float:
        return self.stats["input_tokens"] * float(self.jev["price_usd_per_mtok"]) / 1e6

    def _cost(self, tokens: int) -> float:
        return tokens * float(self.jev["price_usd_per_mtok"]) / 1e6

    def evaluate(self, state, questions: dict) -> dict:
        """Return the API response body. Raises JevError on an unrecoverable failure."""
        payload = {"state": state, "model": self.model, "questions": questions}
        key = hashlib.sha256(json.dumps(payload, ensure_ascii=False).encode("utf-8")).hexdigest()
        with self._lock:
            hit = self._db.execute("SELECT response FROM cache WHERE key = ?", (key,)).fetchone()
            if hit:
                self.stats["cache_hits"] += 1
                return json.loads(hit[0])
            estimate = approx_tokens(payload)
            if self.spent_usd + self._cost(estimate) > self.approved_cost_usd:
                raise JevBudgetExceeded(
                    f"Approved budget ${self.approved_cost_usd:.2f} would be exceeded "
                    f"(spent ${self.spent_usd:.4f})."
                )

        body = None
        for attempt in range(int(self.jev["max_retries"]) + 1):
            if self._rate_limited:
                self._limiter.wait(estimate)
            started = time.monotonic()
            try:
                status, body, headers = self._transport(payload)
            except Exception as exc:  # connection errors and timeouts are retried
                status, body, headers = 599, {"error": repr(exc)}, {}
            elapsed = time.monotonic() - started
            if status == 200:
                break
            if status in (408, 429) or status >= 500:
                retry_after = headers.get("retry-after") or headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(30.0, 0.5 * 2 ** attempt)
                self._sleep(delay)
                continue
            break
        if status != 200:
            with self._lock:
                self.stats["failures"] += 1
            raise JevError(f"HTTP {status}: {json.dumps(body)[:300]}")

        if body.get("model") != self.model:
            raise JevModelMismatch(f"Requested {self.model} but {body.get('model')!r} answered.")
        with self._lock:
            self.stats["requests"] += 1
            self.stats["latency_s"] += elapsed
            self.stats["input_tokens"] += int((body.get("usage") or {}).get("input_tokens") or estimate)
            self._db.execute(
                "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
                (key, json.dumps(body), datetime.now(timezone.utc).isoformat(timespec="seconds")),
            )
            self._db.commit()
        return body


# --------------------------------------------------------------------------- parsing

def _valid_probability(x) -> bool:
    return isinstance(x, (int, float)) and np.isfinite(x) and -1e-9 <= x <= 1 + 1e-9


def parse_answers(answers: dict, horizons: list[int]) -> dict:
    """Turn one response's answers into flat numeric outputs. Invalid answers become NaN.

    Choice probabilities are averaged over the option orders that returned a valid
    distribution, which offsets Jev's documented lean toward the first-listed option.
    """
    out = {}
    for h in horizons:
        distributions = []
        for i in range(len(OPTION_ORDERS)):
            probs = (answers.get(f"h{h}_signal_o{i}") or {}).get("probabilities")
            if (isinstance(probs, dict) and set(probs) == set(CLASS_NAMES)
                    and all(_valid_probability(v) for v in probs.values())
                    and abs(sum(probs.values()) - 1.0) <= 0.02):
                distributions.append([probs[name] for name in CLASS_NAMES])
        if distributions:
            mean = np.mean(distributions, axis=0)
            mean = mean / mean.sum()
            spread = float(np.ptp(distributions, axis=0).max())
        else:
            mean, spread = np.full(3, np.nan), np.nan
        out[f"p_sell_{h}"], out[f"p_hold_{h}"], out[f"p_buy_{h}"] = (float(x) for x in mean)
        out[f"orders_ok_{h}"] = len(distributions)
        out[f"order_spread_{h}"] = spread
        for name in ("up", "big"):
            value = (answers.get(f"h{h}_{name}") or {}).get("noul")
            out[f"{name}_{h}"] = float(value) if _valid_probability(value) else np.nan
    return out


# --------------------------------------------------------------------------- annotation

def outputs_paths(cfg: dict, variant: str, provider: str = "jev") -> tuple[Path, Path]:
    stem = f"{provider}_outputs_{cfg['data']['universe_name']}_{cfg['jev']['wording_version']}_{variant}"
    base = REPO_ROOT / cfg["data"]["cache_dir"]
    return base / f"{stem}.parquet", base / f"{stem}.manifest.json"


def request_fingerprint(cfg: dict) -> dict:
    """Everything that determines what Jev was asked. Stored with outputs and checked on load."""
    return {
        "model": cfg["jev"]["model"],
        "wording_version": cfg["jev"]["wording_version"],
        "questions_sha256": hashlib.sha256(
            json.dumps(build_questions(cfg), ensure_ascii=False).encode("utf-8")).hexdigest(),
        "bucket_lookback_days": cfg["jev"]["bucket_lookback_days"],
        "bucket_quantiles": cfg["jev"]["bucket_quantiles"],
        "examples_per_class": cfg["jev"]["examples_per_class"],
        "example_lookback_days": cfg["jev"]["example_lookback_days"],
        "seed": cfg["seed"],
        "features": FEATURES,
    }


def matches_saved_outputs(manifest: dict, cfg: dict) -> bool:
    """True if saved outputs were produced by the same requests and label definition as `cfg`."""
    current = json.loads(json.dumps({"fingerprint": request_fingerprint(cfg), "label": cfg["task"]["label"]}))
    return manifest.get("fingerprint") == current["fingerprint"] and manifest.get("label") == current["label"]


def select_rows(full: pd.DataFrame, modelling: pd.DataFrame, date_from=None, date_to=None,
                sample: int | None = None, seed: int = 0) -> np.ndarray:
    """Indices into `full` of the modelling rows to annotate."""
    keys = set(zip(modelling["date"], modelling["ticker"]))
    mask = np.fromiter(((d, t) in keys for d, t in zip(full["date"], full["ticker"])), bool, len(full))
    if date_from is not None:
        mask &= (full["date"] >= pd.Timestamp(date_from)).to_numpy()
    if date_to is not None:
        mask &= (full["date"] <= pd.Timestamp(date_to)).to_numpy()
    idx = np.flatnonzero(mask)
    if sample is not None and sample < len(idx):
        idx = np.sort(np.random.default_rng(seed).choice(idx, size=sample, replace=False))
    return idx


def estimate_cost(ctx: JevContext, rows: np.ndarray, cfg: dict, n_probe: int = 200) -> dict:
    """Offline estimate of requests, tokens, cost and minimum wall time. Sends nothing."""
    questions = build_questions(cfg)
    probe = np.random.default_rng(int(cfg["seed"])).choice(rows, size=min(n_probe, len(rows)), replace=False)
    out = {"requests_per_variant": int(len(rows))}
    total_tokens = 0
    for variant in VARIANTS:
        tokens = np.mean([
            approx_tokens({"state": ctx.state(int(i), variant == "examples"), "model": cfg["jev"]["model"],
                           "questions": questions})
            for i in probe
        ])
        variant_tokens = float(tokens) * len(rows)
        total_tokens += variant_tokens
        out[variant] = {
            "approx_tokens_per_request": int(tokens),
            "approx_total_tokens": int(variant_tokens),
            "approx_cost_usd": round(variant_tokens * float(cfg["jev"]["price_usd_per_mtok"]) / 1e6, 2),
            "min_hours_at_rate_limit": round(max(
                variant_tokens / float(cfg["jev"]["rate_limit_tokens_per_s"]),
                len(rows) / float(cfg["jev"]["rate_limit_requests_per_s"])) / 3600, 2),
        }
    out["approx_total_cost_usd"] = round(total_tokens * float(cfg["jev"]["price_usd_per_mtok"]) / 1e6, 2)
    out["note"] = ("Token counts use a rough 3.5 characters per token; actual billing uses the vendor's "
                   "tokenizer. Treat as an order-of-magnitude estimate until a pilot reports real usage.")
    return out


def annotate(ctx: JevContext, rows: np.ndarray, variant: str, client: JevClient, cfg: dict,
             dataset_sha: str) -> tuple[pd.DataFrame, dict]:
    """Query Jev for each row and return a table of outputs plus a manifest. Writes nothing."""
    col = VARIANTS[variant]
    questions = build_questions(cfg)
    horizons = list(cfg["task"]["horizons"])
    started = time.time()

    def one(i: int) -> dict:
        record = {"date": ctx.full.at[i, "date"], "ticker": ctx.full.at[i, "ticker"]}
        try:
            body = client.evaluate(ctx.state(i, variant == "examples"), questions)
            parsed = parse_answers(body.get("answers") or {}, horizons)
            ok = all(parsed[f"orders_ok_{h}"] > 0 for h in horizons)
            record.update({f"{col}_{k}": v for k, v in parsed.items()})
            record[f"{col}_status"] = "ok" if ok else "invalid_answer"
        except (JevBudgetExceeded, JevModelMismatch):
            raise
        except JevError as exc:
            record[f"{col}_status"] = f"error: {exc}"[:200]
        return record

    with ThreadPoolExecutor(max_workers=int(cfg["jev"]["max_workers"])) as pool:
        records = list(pool.map(one, [int(i) for i in rows]))
    table = pd.DataFrame.from_records(records)
    for name in output_columns(col, horizons):
        if name not in table:
            table[name] = np.nan
    status = table[f"{col}_status"]
    manifest = {
        "variant": variant, "fingerprint": request_fingerprint(cfg), "dataset_sha256": dataset_sha,
        "label": cfg["task"]["label"], "horizons": horizons,
        "rows": int(len(table)), "rows_ok": int((status == "ok").sum()),
        "rows_failed": int((status != "ok").sum()),
        "new_requests": client.stats["requests"], "cache_hits": client.stats["cache_hits"],
        "input_tokens_billed": client.stats["input_tokens"], "cost_usd": round(client.spent_usd, 4),
        "mean_latency_s": round(client.stats["latency_s"] / max(1, client.stats["requests"]), 4),
        "wall_time_s": round(time.time() - started, 1),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return table, manifest


def expected_fingerprint_matches(provider: str, manifest: dict, cfg: dict) -> bool:
    """Whether saved outputs of `provider` were produced under the current configuration."""
    if provider == "jev":
        return matches_saved_outputs(manifest, cfg)
    return False   # no other provider has a client yet, so nothing it saved can be trusted


def attach_outputs(ds: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """Merge any saved provider outputs into the dataset. Returns the dataset and a status per provider variant.

    Outputs produced under a different model, wording, question set or label definition
    are refused, never silently reused.
    """
    status = {}
    for provider in PROVIDERS:
        for variant in PROVIDERS[provider]["prefix"]:
            key = f"{provider}/{variant}"
            parquet_path, manifest_path = outputs_paths(cfg, variant, provider)
            if not parquet_path.exists():
                status[key] = "not run: no saved outputs"
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if not expected_fingerprint_matches(provider, manifest, cfg):
                status[key] = "refused: saved outputs were produced under a different configuration"
                continue
            table = pd.read_parquet(parquet_path)
            table["date"] = pd.to_datetime(table["date"])
            ds = ds.merge(table, on=["date", "ticker"], how="left", validate="one_to_one")
            coverage = float(ds[f"{prefix(provider, variant)}_status"].notna().mean())
            status[key] = f"available: {coverage:.1%} of rows annotated"
    return ds, status
