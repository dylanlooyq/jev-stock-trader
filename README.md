# jev-stock-trader

A controlled experiment to test whether Jev (TypeSafe's hosted System One model) can
outperform traditional machine-learning classifiers and simple trading rules at
BUY / HOLD / SELL stock-price classification.

The aim is a reproducible, statistically defensible answer, including "no" or "insufficient
evidence".

## Status

The benchmark pipeline is implemented and tested. Baselines run; the Jev arms are built but
have not been run, because no API key is available yet. There are no experimental results.

## Read this first

[EXPERIMENT_MEMORY.md](EXPERIMENT_MEMORY.md) is the authoritative record of the research
question, the rules the experiment must follow, data and label definitions, the evaluation
protocol, every model and every result. Read it before changing the methodology or
interpreting results, and update it whenever a decision changes.

## How it works

- 100 large US stocks, daily bars from yfinance, 2010 to 2026.
- Prediction after each close; trade at the next open; labels from volatility-scaled
  forward returns over 1, 5 and 20 trading days.
- Every model sees the same 27 price and volume features and is scored on identical rows in
  a purged walk-forward design. The last two years are a locked holdout.
- Jev receives the same features as anonymised text, with no ticker, date or price level.
- Results cover classification quality, trading performance net of costs, and block-bootstrap
  uncertainty.

## Running it

Use Python 3.11 with the packages in `requirements.txt`.

```
python -m pytest -q                              # 64 tests
python -m jevbench.run download                  # download and freeze the dataset
python -m jevbench.run benchmark --name my_run   # development folds; holdout stays locked
python -m jevbench.run report --name my_run
```

Add `--overrides config/smoke.yaml` to any command for a 12-stock check that runs in about
five minutes. Jev commands (`jev-estimate`, `jev-annotate`) and the remaining options are
listed in `EXPERIMENT_MEMORY.md` section 9. Jev calls are billed and need
`TYPESAFE_API_KEY` in a local `.env` file (see `.env.example`).

Each run writes its configuration, metrics, fit log and report to `results/<run name>/`.
