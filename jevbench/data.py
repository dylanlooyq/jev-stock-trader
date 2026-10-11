"""Price data: download once, freeze to disk, load with the holdout locked by default.

The frozen parquet file plus its SHA-256 is the dataset version. Vendor-adjusted
prices are rewritten after later corporate actions, so re-downloading produces a
different dataset and must be recorded as a new version.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import REPO_ROOT

PRICE_COLUMNS = ["date", "ticker", "open", "high", "low", "close", "adj_close", "volume"]


def cache_paths(cfg: dict) -> tuple[Path, Path]:
    d = cfg["data"]
    stem = f"prices_{d['universe_name']}_{d['start']}_{d['end']}"
    base = REPO_ROOT / d["cache_dir"]
    return base / f"{stem}.parquet", base / f"{stem}.manifest.json"


def _to_long(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    frames = []
    if not isinstance(raw.columns, pd.MultiIndex):
        raw = pd.concat({tickers[0]: raw}, axis=1)
    available = set(raw.columns.get_level_values(0))
    for ticker in tickers:
        if ticker not in available:
            continue
        sub = raw[ticker].dropna(how="all")
        if sub.empty:
            continue
        sub = sub.rename(columns=lambda c: str(c).lower().replace(" ", "_")).reset_index()
        sub = sub.rename(columns={sub.columns[0]: "date"})
        sub["ticker"] = ticker
        frames.append(sub[PRICE_COLUMNS])
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=PRICE_COLUMNS)


def _fetch(tickers: list[str], start: str, end_exclusive: str) -> pd.DataFrame:
    import yfinance as yf

    raw = yf.download(
        tickers, start=start, end=end_exclusive, auto_adjust=False, actions=False,
        progress=False, group_by="ticker", threads=True,
    )
    return _to_long(raw, tickers)


def clean_prices(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Drop unusable rows. Nothing is filled or interpolated."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.normalize()
    price_cols = ["open", "high", "low", "close", "adj_close"]
    missing = df[price_cols].isna().any(axis=1)
    non_positive = (df[price_cols] <= 0).any(axis=1) & ~missing
    duplicated = df.duplicated(["date", "ticker"], keep="first")
    dropped = {
        "missing_price": int(missing.sum()),
        "non_positive_price": int(non_positive.sum()),
        "duplicate_date_ticker": int(duplicated.sum()),
    }
    df = df[~(missing | non_positive | duplicated)]
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)
    return df, dropped


def keep_market_days(prices: pd.DataFrame, market_ticker: str) -> tuple[pd.DataFrame, int]:
    """Drop rows dated when the market ticker did not trade (weekends and holidays of assets
    that trade every day), so every asset shares one calendar and a "trading day" means the same
    thing for all of them. Returns the kept rows and the number dropped."""
    on_calendar = prices["date"].isin(prices.loc[prices["ticker"] == market_ticker, "date"])
    return prices[on_calendar].reset_index(drop=True), int((~on_calendar).sum())


def download_prices(cfg: dict, force: bool = False, batch_size: int = 20, retries: int = 4) -> dict:
    """Download the configured universe plus the market ticker and freeze it to disk."""
    parquet_path, manifest_path = cache_paths(cfg)
    if parquet_path.exists() and not force:
        raise FileExistsError(
            f"{parquet_path} already exists. Re-downloading changes the dataset version; "
            "pass force=True only if that is intended and record it in EXPERIMENT_MEMORY.md."
        )
    d = cfg["data"]
    wanted = list(d["tickers"]) + [d["market_ticker"]]
    end_exclusive = (pd.Timestamp(d["end"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    frames, remaining = [], list(wanted)
    for attempt in range(retries):
        if not remaining:
            break
        size = batch_size if attempt == 0 else 1
        got = []
        for i in range(0, len(remaining), size):
            try:
                got.append(_fetch(remaining[i:i + size], d["start"], end_exclusive))
            except Exception as exc:  # network errors are retried ticker by ticker
                print(f"  fetch error for {remaining[i:i + size]}: {exc!r}"[:300])
        if got:
            frames.append(pd.concat(got, ignore_index=True))
        have = set(pd.concat(frames)["ticker"]) if frames else set()
        remaining = [t for t in wanted if t not in have]
        if remaining:
            time.sleep(2 * (attempt + 1))

    if not frames:
        raise RuntimeError("No price data could be downloaded.")
    prices, dropped = clean_prices(pd.concat(frames, ignore_index=True))
    if d["market_ticker"] not in set(prices["ticker"]):
        raise RuntimeError(f"Market ticker {d['market_ticker']} failed to download.")
    prices, dropped["off_market_calendar"] = keep_market_days(prices, d["market_ticker"])

    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(parquet_path, index=False)

    import yfinance as yf

    per_ticker = prices.groupby("ticker")["date"].agg(["min", "max", "count"])
    manifest = {
        "source": d["source"],
        "yfinance_version": yf.__version__,
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "universe_name": d["universe_name"],
        "requested_start": d["start"],
        "requested_end": d["end"],
        "tickers_requested": len(wanted),
        "tickers_obtained": int(prices["ticker"].nunique()),
        "tickers_failed": remaining,
        "rows": int(len(prices)),
        "rows_dropped": dropped,
        "first_date": str(prices["date"].min().date()),
        "last_date": str(prices["date"].max().date()),
        "late_starters": {
            t: str(r["min"].date()) for t, r in per_ticker.iterrows()
            if r["min"] > pd.Timestamp(d["start"]) + pd.Timedelta(days=10)
        },
        "sha256": file_sha256(parquet_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest(cfg: dict) -> dict:
    return json.loads(cache_paths(cfg)[1].read_text(encoding="utf-8"))


def lock_holdout(prices: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Remove every row on or after the holdout start."""
    return prices[prices["date"] < pd.Timestamp(cfg["splits"]["holdout_start"])].reset_index(drop=True)


def load_prices(cfg: dict, unlock_holdout: bool = False) -> pd.DataFrame:
    """Load the frozen prices. Holdout rows never enter memory unless explicitly unlocked."""
    parquet_path, _ = cache_paths(cfg)
    if not parquet_path.exists():
        raise FileNotFoundError(f"{parquet_path} not found. Run the `download` command first.")
    prices = pd.read_parquet(parquet_path)
    prices["date"] = pd.to_datetime(prices["date"])
    if not unlock_holdout:
        prices = lock_holdout(prices, cfg)
    return prices.sort_values(["ticker", "date"]).reset_index(drop=True)


def risk_free_paths(cfg: dict) -> tuple[Path, Path]:
    d = cfg["data"]
    base = REPO_ROOT / d["cache_dir"]
    stem = f"riskfree_{d['start']}_{d['end']}"
    return base / f"{stem}.parquet", base / f"{stem}.manifest.json"


def download_risk_free(cfg: dict, force: bool = False, retries: int = 4) -> dict:
    """Download the Treasury bill yield and freeze it. Stored as percent per year, as published."""
    import yfinance as yf

    parquet_path, manifest_path = risk_free_paths(cfg)
    if parquet_path.exists() and not force:
        raise FileExistsError(f"{parquet_path} already exists.")
    d = cfg["data"]
    end_exclusive = (pd.Timestamp(d["end"]) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    series = pd.Series(dtype=float)
    for attempt in range(retries):
        try:
            raw = yf.download(d["risk_free_ticker"], start=d["start"], end=end_exclusive, auto_adjust=False,
                              actions=False, progress=False)
            close = raw["Close"]
            series = (close.iloc[:, 0] if isinstance(close, pd.DataFrame) else close).dropna()
        except Exception as exc:
            print(f"  fetch error for {d['risk_free_ticker']}: {exc!r}"[:300])
        if len(series):
            break
        time.sleep(2 * (attempt + 1))
    if not len(series):
        raise RuntimeError(f"Risk-free series {d['risk_free_ticker']} could not be downloaded.")
    table = pd.DataFrame({"date": pd.to_datetime(series.index).tz_localize(None).normalize(),
                          "annual_yield_pct": series.to_numpy(dtype=float)})
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_parquet(parquet_path, index=False)
    manifest = {
        "ticker": d["risk_free_ticker"], "source": d["source"], "rows": int(len(table)),
        "first_date": str(table["date"].min().date()), "last_date": str(table["date"].max().date()),
        "min_yield_pct": float(table["annual_yield_pct"].min()), "max_yield_pct": float(table["annual_yield_pct"].max()),
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sha256": file_sha256(parquet_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_risk_free(cfg: dict) -> pd.Series | None:
    """Daily risk-free rate indexed by date (annual yield / 252), or None when configured as zero."""
    if cfg["backtest"]["risk_free"] == "zero":
        return None
    parquet_path, _ = risk_free_paths(cfg)
    if not parquet_path.exists():
        raise FileNotFoundError(f"{parquet_path} not found. Run the `download` command first.")
    table = pd.read_parquet(parquet_path)
    return pd.Series(table["annual_yield_pct"].to_numpy() / 100 / 252, index=pd.to_datetime(table["date"]), name="rf")


def quality_report(prices: pd.DataFrame, market_ticker: str) -> dict:
    """Descriptive data-quality checks. Reports problems; fixes nothing."""
    calendar = prices.loc[prices["ticker"] == market_ticker, "date"]
    stocks = prices[prices["ticker"] != market_ticker]
    ret = stocks.groupby("ticker")["adj_close"].pct_change(fill_method=None)
    gaps = {}
    for ticker, grp in stocks.groupby("ticker"):
        expected = calendar[(calendar >= grp["date"].min()) & (calendar <= grp["date"].max())]
        n_missing = len(expected) - int(grp["date"].isin(expected).sum())
        if n_missing:
            gaps[ticker] = n_missing
    return {
        "n_assets": int(stocks["ticker"].nunique()),
        "n_rows": int(len(stocks)),
        "trading_days": int(calendar.nunique()),
        "assets_with_missing_days": gaps,
        "zero_volume_rows": int((stocks["volume"] == 0).sum()),
        "abs_daily_return_over_25pct": int((ret.abs() > 0.25).sum()),
        "high_below_low_rows": int((stocks["high"] < stocks["low"]).sum()),
    }
