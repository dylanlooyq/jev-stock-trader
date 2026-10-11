"""Command-line entry point.  Usage: python -m jevbench.run <command> [options]

  download       Download and freeze the price dataset and the risk-free rate.
  quality        Print data-quality checks for the frozen dataset.
  benchmark      Run the walk-forward benchmark and write a report.
  sensitivity    Run every predefined sensitivity variant as its own logged run.
  jev-estimate   Estimate Jev request count, tokens and cost. Sends nothing.
  jev-annotate   Query Jev and save its outputs. Billed; needs an approved budget.
  report         Re-render the report of an existing run.
  visualise      Write a self-contained HTML page of a run's backtests.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from .benchmark import summarise, walk_forward
from .config import REPO_ROOT, config_hash, deep_update, load_config
from .data import (cache_paths, download_prices, download_risk_free, load_manifest, load_prices, load_risk_free,
                   lock_holdout, quality_report, risk_free_paths)
from .dataset import build_dataset
from .report import render_report

RESULTS_DIR = REPO_ROOT / "results"


def _git_commit() -> str:
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO_ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True,
                               text=True, check=True).stdout.strip()
        return commit + ("-dirty" if dirty else "")
    except Exception:
        return "uncommitted"


def _versions() -> dict:
    import lightgbm
    import numpy
    import sklearn

    return {"python": platform.python_version(), "pandas": pd.__version__, "numpy": numpy.__version__,
            "scikit-learn": sklearn.__version__, "lightgbm": lightgbm.__version__}


def _clean(obj):
    """Make results JSON-safe: NaN and infinities become null, keys become strings."""
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


def run_benchmark(cfg: dict, run_name: str, unlock_holdout: bool = False, prices: pd.DataFrame | None = None,
                  results_dir: Path | None = None, dataset_manifest: dict | None = None,
                  risk_free: pd.Series | None = None) -> dict:
    """Run one benchmark end to end and write predictions, metrics, manifest and report.

    When `prices` is passed in (tests), `risk_free` is used as given; otherwise both are
    loaded from the frozen files named by the configuration.
    """
    results_dir = results_dir or RESULTS_DIR
    out_dir = results_dir / run_name
    if out_dir.exists():
        raise FileExistsError(f"{out_dir} exists. Runs are never overwritten; choose another name.")
    started, t0 = datetime.now(timezone.utc), time.perf_counter()
    if prices is None:
        prices = load_prices(cfg, unlock_holdout=unlock_holdout)
        dataset_manifest = load_manifest(cfg)
        risk_free = load_risk_free(cfg)
    if not unlock_holdout:
        prices = lock_holdout(prices, cfg)

    print(f"Run {run_name}: {prices['ticker'].nunique() - 1} assets, full window: {unlock_holdout}")
    run = walk_forward(prices, cfg, unlock_holdout=unlock_holdout)
    metrics, per_stock, daily = summarise(run, prices, cfg, risk_free)
    metrics = _clean(metrics)

    manifest = {
        "run_name": run_name, "experiment_id": cfg["experiment_id"],
        "started_at_utc": started.isoformat(timespec="seconds"),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runtime_seconds": round(time.perf_counter() - t0, 1),
        "git_commit": _git_commit(), "config_hash": config_hash(cfg), "holdout_unlocked": unlock_holdout,
        "dataset": dataset_manifest or {"sha256": "in-memory"}, "versions": _versions(),
        "label": cfg["task"]["label"], "horizons": cfg["task"]["horizons"],
        "n_dataset_rows": int(len(run["dataset"])), "external_status": run["external_status"],
        "risk_free": cfg["backtest"]["risk_free"] if risk_free is not None else "zero",
        "primary_rule": cfg["backtest"]["primary_rule"],
        "models_run": sorted(run["predictions"]["model"].unique().tolist()),
        "models_not_run": metrics["not_run"],
    }

    out_dir.mkdir(parents=True)
    run["predictions"].to_parquet(out_dir / "predictions.parquet", index=False)
    run["fit_log"].to_csv(out_dir / "fit_log.csv", index=False)
    run["fold_log"].to_csv(out_dir / "folds.csv", index=False)
    per_stock.to_csv(out_dir / "per_stock_macro_f1.csv", index=False)
    daily.to_parquet(out_dir / "daily_returns.parquet", index=False)
    (out_dir / "config.yaml").write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=1), encoding="utf-8")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (out_dir / "report.md").write_text(render_report(metrics, manifest, cfg), encoding="utf-8")

    # Append-only registry: every run ever made, so the number of configurations tried is known.
    with open(results_dir / "registry.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({k: manifest[k] for k in (
            "run_name", "experiment_id", "finished_at_utc", "git_commit", "config_hash", "holdout_unlocked",
            "label", "horizons", "models_run", "runtime_seconds")}) + "\n")
    print(f"Wrote {out_dir} in {manifest['runtime_seconds']}s")
    return {"metrics": metrics, "manifest": manifest, "out_dir": out_dir}


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jevbench", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["download", "quality", "benchmark", "sensitivity",
                                            "jev-estimate", "jev-annotate", "report", "visualise"])
    parser.add_argument("--config", default=None, help="base config (default config/experiment.yaml)")
    parser.add_argument("--overrides", nargs="*", default=[], help="override YAML files applied in order")
    parser.add_argument("--name", default=None, help="run name (default: experiment id + UTC timestamp)")
    parser.add_argument("--force", action="store_true", help="download: replace the frozen dataset")
    parser.add_argument("--unlock-holdout", action="store_true", help="evaluate the final holdout")
    parser.add_argument("--confirm-design-frozen", action="store_true",
                        help="required with --unlock-holdout; the design must be recorded as frozen first")
    parser.add_argument("--publish", action="store_true",
                        help="report: also write the report to EXPERIMENT_REPORT.md at the repository root")
    parser.add_argument("--variant", choices=["zero", "examples"], help="jev-annotate: which Jev variant")
    parser.add_argument("--approved-cost-usd", type=float, help="jev-annotate: hard spending ceiling")
    parser.add_argument("--date-from", default=None)
    parser.add_argument("--date-to", default=None)
    parser.add_argument("--sample", type=int, default=None, help="jev-annotate: random subset of rows")
    parser.add_argument("--pilot", type=int, default=None,
                        help="jev-annotate: N random rows dated before the first test fold, for a sanity check "
                             "that cannot touch any evaluated date")
    args = parser.parse_args(argv)
    cfg = load_config(args.config, args.overrides)

    if args.unlock_holdout and not args.confirm_design_frozen:
        parser.error("--unlock-holdout also needs --confirm-design-frozen. Record the freeze in "
                     "EXPERIMENT_MEMORY.md section 4 before running this.")

    if args.command == "download":
        if cache_paths(cfg)[0].exists() and not args.force:
            print(f"Prices already frozen at {cache_paths(cfg)[0]}; not downloaded again.")
        else:
            print(json.dumps(download_prices(cfg, force=args.force), indent=2))
        if cfg["backtest"]["risk_free"] == "tbill":
            if risk_free_paths(cfg)[0].exists() and not args.force:
                print(f"Risk-free rate already frozen at {risk_free_paths(cfg)[0]}; not downloaded again.")
            else:
                print(json.dumps(download_risk_free(cfg, force=args.force), indent=2))
    elif args.command == "quality":
        prices = load_prices(cfg, unlock_holdout=False)
        print(json.dumps(quality_report(prices, cfg["data"]["market_ticker"]), indent=2))
    elif args.command == "benchmark":
        run_benchmark(cfg, args.name or f"{cfg['experiment_id']}_{_timestamp()}", args.unlock_holdout)
    elif args.command == "sensitivity":
        stamp = _timestamp()
        for variant in cfg["sensitivity"]:
            run_benchmark(deep_update(cfg, variant["overrides"]),
                          f"{cfg['experiment_id']}_{variant['name']}_{stamp}", args.unlock_holdout)
    elif args.command == "report":
        out_dir = RESULTS_DIR / args.name
        run_cfg = yaml.safe_load((out_dir / "config.yaml").read_text(encoding="utf-8"))
        metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
        manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
        text = render_report(metrics, manifest, run_cfg)
        (out_dir / "report.md").write_text(text, encoding="utf-8")
        print(f"Wrote {out_dir / 'report.md'}")
        if args.publish:
            (REPO_ROOT / "EXPERIMENT_REPORT.md").write_text(text, encoding="utf-8")
            print("Wrote EXPERIMENT_REPORT.md")
    elif args.command == "visualise":
        from .visualise import write_page

        print(f"Wrote {write_page(RESULTS_DIR / args.name)}")
    else:
        return _jev_command(args, cfg)
    return 0


def _jev_command(args, cfg: dict) -> int:
    from . import jev

    prices = load_prices(cfg, unlock_holdout=args.unlock_holdout)
    full = build_dataset(prices, cfg, keep_burn_in=True)
    modelling = build_dataset(prices, cfg)
    ctx = jev.JevContext(full, cfg)
    date_to, sample = args.date_to, args.sample
    if args.pilot is not None:
        # Strictly before the first test fold: these dates are only ever training data.
        date_to = pd.Timestamp(cfg["splits"]["first_test_start"]) - pd.Timedelta(days=1)
        sample = args.pilot
    rows = jev.select_rows(ctx.full, modelling, args.date_from, date_to, sample, int(cfg["seed"]))

    if args.command == "jev-estimate":
        print(json.dumps(jev.estimate_cost(ctx, rows, cfg), indent=2))
        return 0

    if not args.variant or args.approved_cost_usd is None:
        print("jev-annotate needs --variant and --approved-cost-usd.", file=sys.stderr)
        return 2
    parquet_path, manifest_path = jev.outputs_paths(cfg, args.variant)
    if parquet_path.exists():
        saved = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not jev.matches_saved_outputs(saved, cfg):
            print(f"{parquet_path} was produced under a different configuration. Bump jev.wording_version "
                  "or move the old file; outputs are never mixed.", file=sys.stderr)
            return 2
    try:
        client = jev.JevClient(cfg, approved_cost_usd=args.approved_cost_usd)
        table, manifest = jev.annotate(ctx, rows, args.variant, client, cfg, load_manifest(cfg)["sha256"])
    except (jev.JevMissingKey, jev.JevBudgetExceeded, jev.JevModelMismatch) as exc:
        # Completed requests stay in the cache, so a rerun resumes without paying twice.
        print(f"Jev annotation stopped: {exc}", file=sys.stderr)
        return 2
    if parquet_path.exists():
        # Extend earlier output for this variant; newly returned rows replace older ones.
        previous = pd.read_parquet(parquet_path)
        table = pd.concat([previous, table]).drop_duplicates(["date", "ticker"], keep="last")
    table.sort_values(["date", "ticker"]).to_parquet(parquet_path, index=False)
    manifest["rows_saved_total"] = int(len(table))
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
