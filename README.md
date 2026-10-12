# jev-stock-trader

A controlled experiment to test whether Jev (TypeSafe's hosted System One model), used as
a classifier, can outperform traditional machine-learning models for trading. Each
model's BUY / HOLD / SELL predictions are turned into a portfolio by the same rule and
compared with a traditional classifier, with buy and hold, and with a traditional
classifier that is given Jev's outputs as extra inputs.

The aim is a reproducible, statistically defensible answer, including "no" or "insufficient
evidence".

## Status

On 2026-10-12 the universe changed from ten assets to fifteen (bitcoin removed, six stocks
added; decision D13). **The published baseline report and chart below describe the earlier
ten-asset universe and are superseded.** The baseline on the fifteen assets is being re-run,
and the Jev zero-shot run is being re-made for the new universe. Until they finish there is
no result on Jev. Slots are reserved for an OpenAI classifier and a local open model.

- Earlier (ten-asset) report: [EXPERIMENT_REPORT.md](EXPERIMENT_REPORT.md)
- Earlier charts: `results/baseline_multi_asset_v1/backtests.html` (open in a browser; works offline)

## Read this first

[EXPERIMENT_MEMORY.md](EXPERIMENT_MEMORY.md) is the authoritative record of the research
question, the rules the experiment must follow, data and label definitions, the evaluation
protocol, every model and every result. Read it before changing the methodology or
interpreting results, and update it whenever a decision changes. The design is frozen.

## How it works

- Fifteen assets: nine funds of different kinds (S&P 500, gold, long Treasuries, developed
  and emerging stocks, oil, real estate, the US dollar, high-yield bonds) and six large US
  stocks (Alphabet, Procter & Gamble, IBM, Chevron, Wells Fargo, Cisco), daily bars from
  yfinance, 2010 to 2026. The funds were chosen with hindsight; the stocks are the largest
  by 2009 market cap outside the smoke-test set (decision D13).
- Prediction after each close; trade at the next open; labels from volatility-scaled
  forward returns over 1, 5 and 20 trading days.
- Every model sees the same 27 price and volume features and is scored on identical rows in
  a purged walk-forward design of twelve yearly folds.
- Jev receives the same features as anonymised text, with no ticker, date or price level.
- Primary test: net Sharpe ratio of a portfolio holding each model's top 4 of the 15 assets,
  against a traditional classifier and against equal-weight buy and hold, with
  block-bootstrap intervals. Classification metrics are reported as diagnostics.

## Running it

Use Python 3.11 with the packages in `requirements.txt`.

```
python -m pytest -q                               # 80 tests
python -m jevbench.run download                   # download and freeze prices and the T-bill rate
python -m jevbench.run benchmark --name my_run    # first ten folds only
python -m jevbench.run visualise --name my_run    # results/my_run/backtests.html, opens offline
```

Add `--overrides config/smoke.yaml` to any command for a pipeline check that runs in about
three minutes. It uses 12 stocks outside the experiment's universe on purpose, so testing
the code reveals nothing about the fifteen assets. The verdict-window run, the Jev commands (`jev-estimate`, `jev-annotate`)
and the remaining options are listed in `EXPERIMENT_MEMORY.md` section 9. Jev calls are
billed and need `TYPESAFE_API_KEY` in a local `.env` file (see `.env.example`).

Each run writes its configuration, metrics, fit log, `report.md` and `backtests.html` to
`results/<run name>/`.
