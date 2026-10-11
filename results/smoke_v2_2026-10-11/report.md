# Experiment report: smoke_v2_2026-10-11

> **Smoke run.** A small configuration used to validate the pipeline end to end. These numbers are not experimental findings.

Generated 2026-10-11T08:22:16+00:00 from commit `8e9de43-dirty`, config `cec0a07c728d`, dataset `72519f1d13e4`. Final two years of folds included: **False**.

## 1. Research question and method

Can Jev, used as a classifier, outperform traditional models for stock trading? Each model's predictions are turned into a portfolio by the same rule and compared on net Sharpe ratio with a traditional classifier, with equal-weight buy and hold, and with a traditional classifier that is given Jev's outputs as extra inputs. Every model is fitted and scored on identical observations in a purged walk-forward design. Classification metrics are reported as diagnostics. The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.

## 2. Data and labels

- Universe: `smoke_12`, 13 tickers obtained including the market proxy SPY; failed downloads: none.
- Source: yfinance daily bars, 2010-01-04 to 2026-09-30, downloaded 2026-10-11T06:47:08+00:00.
- The universe is a fixed list chosen with hindsight, not point-in-time membership. Survivorship bias inflates every absolute return here, including buy and hold of the same stocks.
- Prediction after the close of day t; execution at the open of t+1; label return is open(t+1) to open(t+1+h), dividend and split adjusted.
- Labels: BUY / SELL when the forward return is beyond ±0.5 × trailing 60-day volatility × √h, otherwise HOLD.
- Horizons: [1, 5, 20] trading days; primary: 5.

## 3. Leakage prevention

- Walk-forward folds of 12 months, expanding training window, 12-month validation tail used for all tuning.
- Rows whose label window reaches the next segment are purged, plus an embargo of h trading days.
- Scaling and all other preprocessing are fitted inside each model on fitting rows only.
- Data on or after 2024-10-01 is removed before features are computed unless the full-window run is explicitly requested.
- Automated tests cover: features unchanged when future data is removed, labels unaffected by prices outside their window, purging at every boundary, the data lock, scaler isolation, trade timing, and causal construction of the state and examples sent to external classifiers.

## 4. Trading results (primary test)

- Primary rule: Ranking portfolio: each day hold the top 20% of stocks by score, fully invested.
- Secondary rule: BUY-names portfolio: hold the stocks labelled BUY, the rest in cash.
- Positions open at the next open and are held for h days in h daily tranches. Cost 5.0 bps per unit of turnover. Idle cash earns the Treasury bill rate; Sharpe and Sortino use returns in excess of that rate.
- `always_buy` holds every stock equally through the same engine and costs. It is the buy-and-hold benchmark. `market_buy_and_hold` is SPY, shown for context only.
- Models without scores of their own (`majority`, `stratified_random`) hold a random selection under the ranking rule, which is that rule's no-skill reference.
- Alpha and beta are measured against the market proxy. Sharpe L/S is the long-short version of the rule.

### Folds before the final two years, primary rule

**1-day horizon**, 2021-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 38.3% | 11.5% | 0.50 | 0.70 | -26.3% | 0.44 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 32.6% | 9.9% | 0.45 | 0.63 | -21.5% | 0.46 | 0.3 | 99.9% | -0.0% | 0.80 | n/a | n/a | n/a |
| ma_cross_rule | 34.7% | 10.5% | 0.40 | 0.54 | -24.3% | 0.43 | 16.1 | 99.9% | 2.5% (-15.4% to 23.8%) | 0.70 | 0.42 | 0.37 | 0.44 |
| momentum_rule | 27.5% | 8.5% | 0.32 | 0.45 | -20.6% | 0.41 | 60.3 | 99.9% | 0.8% (-17.3% to 18.8%) | 0.67 | 0.41 | 0.18 | 0.04 |
| logreg | 2.1% | 0.7% | -0.03 | -0.04 | -40.7% | 0.02 | 194.7 | 99.9% | -7.6% (-28.7% to 15.1%) | 0.79 | 0.24 | -0.49 | -0.15 |
| gbt | -7.7% | -2.6% | -0.19 | -0.26 | -45.1% | -0.06 | 307.6 | 99.9% | -11.3% (-30.4% to 6.6%) | 0.82 | 0.24 | -0.91 | -0.62 |
| random_forest | -31.2% | -11.8% | -0.71 | -0.93 | -44.6% | -0.26 | 309.0 | 99.9% | -20.7% (-35.5% to -3.8%) | 0.75 | -0.24 | -1.47 | -1.49 |
| majority | -43.4% | -17.4% | -0.97 | -1.30 | -59.1% | -0.29 | 421.2 | 99.9% | -27.5% (-47.4% to -9.8%) | 0.79 | -0.37 | -1.97 | -2.61 |
| stratified_random | -43.4% | -17.4% | -0.97 | -1.30 | -59.1% | -0.29 | 421.2 | 99.9% | -27.5% (-47.4% to -9.8%) | 0.79 | -0.37 | -1.97 | -2.61 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.64 | -1.40 to 0.11 | 0.100 | 0.399 |
| logreg vs always_buy | -0.48 | -1.39 to 0.50 | 0.289 | 0.867 |
| ma_cross_rule vs always_buy | -0.05 | -1.10 to 0.78 | 0.910 | 1.000 |
| momentum_rule vs always_buy | -0.13 | -1.17 to 0.88 | 0.801 | 1.000 |
| random_forest vs always_buy | -1.16 | -1.99 to -0.36 | 0.003 | 0.017 |

**5-day horizon (primary)**, 2021-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| majority | 38.7% | 11.6% | 0.53 | 0.76 | -20.6% | 0.56 | 85.9 | 99.3% | 1.9% (-8.9% to 13.1%) | 0.77 | 0.68 | 0.27 | -0.52 |
| stratified_random | 38.7% | 11.6% | 0.53 | 0.76 | -20.6% | 0.56 | 85.9 | 99.3% | 1.9% (-8.9% to 13.1%) | 0.77 | 0.68 | 0.27 | -0.52 |
| market_buy_and_hold | 38.3% | 11.5% | 0.50 | 0.70 | -26.3% | 0.44 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 39.3% | 11.8% | 0.48 | 0.70 | -32.4% | 0.36 | 60.0 | 99.3% | 2.4% (-12.2% to 16.4%) | 0.79 | 0.57 | 0.33 | -0.03 |
| always_buy | 32.0% | 9.8% | 0.44 | 0.62 | -21.5% | 0.45 | 0.6 | 99.3% | -0.2% | 0.80 | n/a | n/a | n/a |
| ma_cross_rule | 29.6% | 9.1% | 0.34 | 0.47 | -31.1% | 0.29 | 17.0 | 99.3% | 1.3% (-15.9% to 21.0%) | 0.69 | 0.37 | 0.30 | 0.27 |
| random_forest | 20.9% | 6.6% | 0.24 | 0.33 | -30.1% | 0.22 | 66.4 | 99.3% | -2.0% (-18.6% to 11.0%) | 0.71 | 0.36 | 0.05 | -0.09 |
| momentum_rule | 15.2% | 4.9% | 0.16 | 0.21 | -23.5% | 0.21 | 26.5 | 99.3% | -3.2% (-23.0% to 13.0%) | 0.71 | 0.20 | 0.09 | 0.24 |
| gbt | 5.9% | 1.9% | 0.01 | 0.01 | -29.0% | 0.07 | 53.8 | 99.3% | -7.0% (-23.5% to 8.4%) | 0.82 | 0.09 | -0.13 | 0.12 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.43 | -1.13 to 0.27 | 0.196 | 0.980 |
| logreg vs always_buy | 0.04 | -0.61 to 0.66 | 0.920 | 1.000 |
| ma_cross_rule vs always_buy | -0.10 | -0.88 to 0.64 | 0.781 | 1.000 |
| momentum_rule vs always_buy | -0.29 | -1.40 to 0.64 | 0.525 | 1.000 |
| random_forest vs always_buy | -0.20 | -0.95 to 0.56 | 0.551 | 1.000 |

**20-day horizon**, 2021-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 59.1% | 16.8% | 0.71 | 1.01 | -28.1% | 0.60 | 17.6 | 97.3% | 6.3% (-3.1% to 16.3%) | 0.86 | 0.74 | 0.66 | 0.62 |
| market_buy_and_hold | 38.3% | 11.5% | 0.50 | 0.70 | -26.3% | 0.44 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 26.7% | 8.2% | 0.36 | 0.49 | -21.5% | 0.38 | 0.7 | 97.3% | -1.5% | 0.79 | n/a | n/a | n/a |
| majority | 22.4% | 7.0% | 0.28 | 0.39 | -20.0% | 0.35 | 20.9 | 97.3% | -2.6% (-9.3% to 3.3%) | 0.80 | 0.32 | 0.21 | -0.51 |
| stratified_random | 22.4% | 7.0% | 0.28 | 0.39 | -20.0% | 0.35 | 20.9 | 97.3% | -2.6% (-9.3% to 3.3%) | 0.80 | 0.32 | 0.21 | -0.51 |
| ma_cross_rule | -6.2% | -2.1% | -0.16 | -0.21 | -32.4% | -0.07 | 10.7 | 97.3% | -9.8% (-24.8% to 2.8%) | 0.72 | -0.15 | -0.19 | -0.04 |
| gbt | -5.5% | -1.9% | -0.18 | -0.25 | -38.1% | -0.05 | 15.1 | 97.3% | -11.0% (-20.7% to 0.0%) | 0.85 | -0.16 | -0.22 | -0.49 |
| momentum_rule | -5.1% | -1.8% | -0.19 | -0.25 | -30.0% | -0.06 | 10.9 | 97.3% | -9.6% (-22.3% to 2.3%) | 0.68 | -0.17 | -0.22 | -0.21 |
| random_forest | -9.9% | -3.4% | -0.28 | -0.38 | -33.8% | -0.10 | 16.8 | 97.3% | -12.6% (-20.8% to -2.9%) | 0.82 | -0.26 | -0.33 | -0.59 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.53 | -0.91 to -0.16 | 0.003 | 0.017 |
| logreg vs always_buy | 0.35 | -0.12 to 0.82 | 0.133 | 0.209 |
| ma_cross_rule vs always_buy | -0.52 | -1.16 to 0.04 | 0.090 | 0.209 |
| momentum_rule vs always_buy | -0.55 | -1.22 to -0.03 | 0.070 | 0.209 |
| random_forest vs always_buy | -0.64 | -0.99 to -0.29 | 0.003 | 0.017 |

### Folds before the final two years, secondary rule

**1-day horizon**, 2021-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 24.6% | 7.7% | 0.62 | 0.86 | -6.3% | 1.22 | 19.8 | 42.4% | 2.2% (-3.6% to 7.5%) | 0.20 | 0.71 | 0.46 | 0.16 | 0.16 | 3.0% |
| gbt | 29.4% | 9.0% | 0.56 | 0.87 | -9.7% | 0.93 | 77.3 | 36.8% | 2.0% (-7.0% to 10.3%) | 0.39 | 0.79 | 0.17 | -0.31 | 1.04 | -4.3% |
| logreg | 26.0% | 8.0% | 0.51 | 0.77 | -8.0% | 1.01 | 44.2 | 26.8% | 1.6% (-5.7% to 8.4%) | 0.33 | 0.66 | 0.26 | 0.17 | 0.81 | -2.5% |
| market_buy_and_hold | 38.3% | 11.5% | 0.50 | 0.70 | -26.3% | 0.44 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 32.6% | 9.9% | 0.45 | 0.63 | -21.5% | 0.46 | 0.3 | 99.9% | -0.0% | 0.80 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 15.6% | 5.0% | 0.20 | 0.28 | -9.5% | 0.53 | 14.8 | 47.5% | -0.8% (-7.1% to 5.6%) | 0.26 | 0.26 | 0.10 | -0.04 | 0.28 | -0.4% |
| random_forest | 13.2% | 4.2% | 0.10 | 0.15 | -13.6% | 0.31 | 60.7 | 37.9% | -2.9% (-10.6% to 5.3%) | 0.45 | 0.27 | -0.18 | -0.54 | 0.48 | -3.8% |
| majority | 11.4% | 3.7% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| stratified_random | -10.3% | -3.6% | -0.94 | -1.26 | -17.1% | -0.21 | 129.9 | 37.2% | -9.8% (-14.7% to -4.5%) | 0.32 | -0.41 | -1.81 | -2.31 | 0.15 | -8.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | 0.11 | -0.69 to 1.11 | 0.841 | 1.000 |
| logreg vs always_buy | 0.05 | -0.95 to 1.01 | 0.927 | 1.000 |
| ma_cross_rule vs always_buy | 0.16 | -0.63 to 0.89 | 0.698 | 1.000 |
| momentum_rule vs always_buy | -0.25 | -1.06 to 0.54 | 0.548 | 1.000 |
| random_forest vs always_buy | -0.35 | -1.26 to 0.62 | 0.439 | 1.000 |

**5-day horizon (primary)**, 2021-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 29.6% | 9.1% | 0.57 | 0.85 | -10.0% | 0.91 | 15.1 | 36.4% | 2.0% (-4.1% to 7.7%) | 0.41 | 0.62 | 0.49 | 0.28 | 0.68 | -1.0% |
| market_buy_and_hold | 38.3% | 11.5% | 0.50 | 0.70 | -26.3% | 0.44 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 32.0% | 9.8% | 0.44 | 0.62 | -21.5% | 0.45 | 0.6 | 99.3% | -0.2% | 0.80 | n/a | n/a | n/a | n/a | n/a |
| random_forest | 23.5% | 7.3% | 0.40 | 0.60 | -11.0% | 0.67 | 14.3 | 34.5% | 0.4% (-6.2% to 6.4%) | 0.40 | 0.44 | 0.33 | 0.10 | 0.51 | -1.0% |
| gbt | 21.2% | 6.6% | 0.33 | 0.48 | -11.2% | 0.59 | 14.5 | 36.7% | -0.4% (-6.8% to 6.0%) | 0.42 | 0.37 | 0.26 | -0.11 | 0.52 | -1.8% |
| momentum_rule | 18.5% | 5.9% | 0.31 | 0.43 | -8.6% | 0.68 | 7.8 | 49.1% | -0.1% (-5.9% to 5.6%) | 0.27 | 0.34 | 0.26 | -0.07 | 0.35 | -0.1% |
| ma_cross_rule | 15.2% | 4.9% | 0.20 | 0.27 | -6.4% | 0.76 | 9.7 | 43.0% | -0.7% (-5.7% to 4.9%) | 0.23 | 0.25 | 0.13 | -0.32 | -0.04 | 1.6% |
| majority | 11.4% | 3.7% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| stratified_random | 10.6% | 3.4% | -0.01 | -0.01 | -10.1% | 0.34 | 27.2 | 40.6% | -2.9% (-6.6% to 0.9%) | 0.33 | 0.12 | -0.21 | -0.74 | 0.45 | -3.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.11 | -0.85 to 0.61 | 0.744 | 1.000 |
| logreg vs always_buy | 0.13 | -0.58 to 0.86 | 0.734 | 1.000 |
| ma_cross_rule vs always_buy | -0.24 | -0.94 to 0.47 | 0.498 | 1.000 |
| momentum_rule vs always_buy | -0.13 | -0.93 to 0.63 | 0.718 | 1.000 |
| random_forest vs always_buy | -0.04 | -0.89 to 0.71 | 0.920 | 1.000 |

**20-day horizon**, 2021-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 34.3% | 10.4% | 0.67 | 0.98 | -12.6% | 0.82 | 6.7 | 47.0% | 2.7% (-2.7% to 8.4%) | 0.46 | 0.69 | 0.63 | 0.59 | 0.65 | 0.2% |
| market_buy_and_hold | 38.3% | 11.5% | 0.50 | 0.70 | -26.3% | 0.44 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| random_forest | 23.9% | 7.4% | 0.45 | 0.66 | -12.5% | 0.59 | 5.5 | 38.1% | 0.6% (-4.4% to 5.8%) | 0.38 | 0.46 | 0.41 | -0.15 | 0.51 | -0.5% |
| stratified_random | 19.8% | 6.2% | 0.37 | 0.51 | -10.5% | 0.60 | 7.0 | 44.8% | -0.6% (-3.4% to 2.3%) | 0.37 | 0.40 | 0.32 | 0.26 | 0.32 | 0.4% |
| always_buy | 26.7% | 8.2% | 0.36 | 0.49 | -21.5% | 0.38 | 0.7 | 97.3% | -1.5% | 0.79 | n/a | n/a | n/a | n/a | n/a |
| gbt | 20.1% | 6.3% | 0.30 | 0.45 | -14.0% | 0.45 | 5.7 | 43.3% | -1.0% (-6.1% to 4.9%) | 0.45 | 0.32 | 0.28 | -0.35 | 0.45 | -1.2% |
| ma_cross_rule | 15.0% | 4.8% | 0.20 | 0.26 | -8.7% | 0.55 | 4.2 | 40.8% | -0.8% (-5.6% to 4.2%) | 0.24 | 0.22 | 0.17 | -0.41 | -0.09 | 1.8% |
| momentum_rule | 14.5% | 4.6% | 0.17 | 0.22 | -9.5% | 0.49 | 2.8 | 44.0% | -1.2% (-6.2% to 3.9%) | 0.27 | 0.18 | 0.15 | -0.07 | -0.02 | 1.3% |
| majority | 11.4% | 3.7% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.05 | -0.56 to 0.40 | 0.821 | 1.000 |
| logreg vs always_buy | 0.31 | -0.19 to 0.83 | 0.206 | 1.000 |
| ma_cross_rule vs always_buy | -0.16 | -0.85 to 0.46 | 0.668 | 1.000 |
| momentum_rule vs always_buy | -0.19 | -0.85 to 0.35 | 0.568 | 1.000 |
| random_forest vs always_buy | 0.09 | -0.50 to 0.60 | 0.751 | 1.000 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.76 (median of 5 comparisons). A true difference smaller than about 1.08 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

9,012 test observations on 751 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.371 | 0.371 | 0.387 | 1.106 | 0.670 | 0.042 | 0.521 | 25/43/32 | 0.0% |
| logreg | 0.369 | 0.372 | 0.400 | 1.091 | 0.660 | 0.013 | 0.522 | 24/52/23 | 0.0% |
| random_forest | 0.363 | 0.365 | 0.388 | 1.093 | 0.662 | 0.009 | 0.516 | 20/47/33 | 0.0% |
| momentum_rule | 0.340 | 0.343 | 0.351 | n/a | n/a | n/a | 0.518 | 23/37/40 | 0.0% |
| ma_cross_rule | 0.334 | 0.335 | 0.346 | n/a | n/a | n/a | 0.525 | 23/42/35 | 0.0% |
| stratified_random | 0.332 | 0.332 | 0.346 | 1.081 | 0.655 | 0.016 | 0.505 | 26/43/31 | 0.0% |
| majority | 0.198 | 0.333 | 0.423 | 1.081 | 0.655 | 0.016 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 27.2%, HOLD 42.3%, BUY 30.5%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.299 | 0.475 | 0.339 | 0.277 | 0.479 | 0.357 | -0.004% | 0.011% | 0.121% |
| logreg | 0.298 | 0.466 | 0.356 | 0.264 | 0.579 | 0.274 | -0.012% | 0.033% | 0.118% |
| ma_cross_rule | 0.290 | 0.412 | 0.305 | 0.243 | 0.407 | 0.354 | 0.044% | 0.025% | 0.062% |
| majority | 0.000 | 0.423 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.042% | n/a |
| momentum_rule | 0.292 | 0.432 | 0.308 | 0.248 | 0.381 | 0.400 | 0.033% | 0.056% | 0.035% |
| random_forest | 0.292 | 0.467 | 0.334 | 0.217 | 0.519 | 0.361 | 0.002% | 0.051% | 0.055% |
| stratified_random | 0.275 | 0.419 | 0.302 | 0.260 | 0.428 | 0.308 | 0.042% | 0.067% | 0.009% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0388 | 0.0230 to 0.0553 | 0.003 | 0.017 |
| logreg vs stratified_random | 0.0366 | 0.0226 to 0.0493 | 0.003 | 0.017 |
| ma_cross_rule vs stratified_random | 0.0020 | -0.0135 to 0.0165 | 0.797 | 0.797 |
| momentum_rule vs stratified_random | 0.0083 | -0.0074 to 0.0240 | 0.289 | 0.578 |
| random_forest vs stratified_random | 0.0305 | 0.0173 to 0.0440 | 0.003 | 0.017 |

### 5-day horizon (primary)

8,964 test observations on 747 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.354 | 0.355 | 0.368 | 1.116 | 0.678 | 0.056 | 0.511 | 24/43/33 | 0.0% |
| logreg | 0.352 | 0.355 | 0.369 | 1.110 | 0.673 | 0.037 | 0.521 | 22/46/33 | 0.0% |
| random_forest | 0.348 | 0.354 | 0.372 | 1.107 | 0.671 | 0.028 | 0.524 | 19/50/31 | 0.0% |
| momentum_rule | 0.336 | 0.338 | 0.346 | n/a | n/a | n/a | 0.513 | 23/36/41 | 0.0% |
| stratified_random | 0.333 | 0.334 | 0.343 | 1.094 | 0.663 | 0.036 | 0.508 | 24/42/34 | 0.0% |
| ma_cross_rule | 0.331 | 0.332 | 0.340 | n/a | n/a | n/a | 0.506 | 24/39/36 | 0.0% |
| majority | 0.186 | 0.333 | 0.387 | 1.094 | 0.663 | 0.036 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 27.8%, HOLD 38.7%, BUY 33.4%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.276 | 0.423 | 0.363 | 0.237 | 0.467 | 0.361 | 0.207% | 0.140% | 0.306% |
| logreg | 0.285 | 0.415 | 0.362 | 0.223 | 0.488 | 0.353 | 0.101% | 0.110% | 0.426% |
| ma_cross_rule | 0.275 | 0.387 | 0.333 | 0.242 | 0.394 | 0.359 | 0.411% | 0.131% | 0.164% |
| majority | 0.000 | 0.387 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.211% | n/a |
| momentum_rule | 0.281 | 0.397 | 0.336 | 0.229 | 0.370 | 0.414 | 0.346% | 0.149% | 0.192% |
| random_forest | 0.294 | 0.411 | 0.357 | 0.195 | 0.532 | 0.335 | 0.106% | 0.168% | 0.343% |
| stratified_random | 0.278 | 0.388 | 0.335 | 0.241 | 0.419 | 0.341 | 0.178% | 0.284% | 0.145% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0207 | -0.0030 to 0.0430 | 0.073 | 0.365 |
| logreg vs stratified_random | 0.0193 | -0.0048 to 0.0416 | 0.106 | 0.425 |
| ma_cross_rule vs stratified_random | -0.0016 | -0.0213 to 0.0174 | 0.837 | 1.000 |
| momentum_rule vs stratified_random | 0.0027 | -0.0172 to 0.0228 | 0.794 | 1.000 |
| random_forest vs stratified_random | 0.0150 | -0.0138 to 0.0369 | 0.249 | 0.748 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 592 | 1,043 | 859 | 0 |
| HOLD | 815 | 1,622 | 1,036 | 0 |
| BUY | 741 | 1,174 | 1,082 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 557 | 1,125 | 812 | 0 |
| HOLD | 722 | 1,696 | 1,055 | 0 |
| BUY | 673 | 1,266 | 1,058 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 603 | 1,008 | 883 | 0 |
| HOLD | 833 | 1,370 | 1,270 | 0 |
| BUY | 758 | 1,162 | 1,077 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 2,494 | 0 | 0 |
| HOLD | 0 | 3,473 | 0 | 0 |
| BUY | 0 | 2,997 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 572 | 903 | 1,019 | 0 |
| HOLD | 757 | 1,286 | 1,430 | 0 |
| BUY | 704 | 1,052 | 1,241 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 487 | 1,211 | 796 | 0 |
| HOLD | 612 | 1,848 | 1,013 | 0 |
| BUY | 560 | 1,434 | 1,003 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 600 | 1,024 | 870 | 0 |
| HOLD | 855 | 1,456 | 1,162 | 0 |
| BUY | 703 | 1,272 | 1,022 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 |
|---|---:|---:|---:|
| gbt | 0.285 | 0.363 | 0.365 |
| logreg | 0.289 | 0.377 | 0.343 |
| ma_cross_rule | 0.331 | 0.318 | 0.322 |
| majority | 0.181 | 0.199 | 0.178 |
| momentum_rule | 0.314 | 0.328 | 0.331 |
| random_forest | 0.281 | 0.364 | 0.358 |
| stratified_random | 0.328 | 0.333 | 0.336 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.313 | 0.351 | 0.337 |
| logreg | 0.305 | 0.350 | 0.330 |
| ma_cross_rule | 0.328 | 0.332 | 0.320 |
| majority | 0.184 | 0.186 | 0.188 |
| momentum_rule | 0.323 | 0.332 | 0.330 |
| random_forest | 0.307 | 0.347 | 0.330 |
| stratified_random | 0.332 | 0.332 | 0.335 |

Macro-F1 across individual stocks:

| Model | 10th pct | Median | 90th pct | Stocks |
|---|---:|---:|---:|---:|
| gbt | 0.330 | 0.343 | 0.369 | 12 |
| logreg | 0.332 | 0.346 | 0.375 | 12 |
| ma_cross_rule | 0.294 | 0.322 | 0.355 | 12 |
| majority | 0.179 | 0.185 | 0.193 | 12 |
| momentum_rule | 0.271 | 0.317 | 0.339 | 12 |
| random_forest | 0.327 | 0.344 | 0.369 | 12 |
| stratified_random | 0.314 | 0.332 | 0.355 | 12 |

### 20-day horizon

8,784 test observations on 732 dates. Reference traditional classifier (chosen on validation data): **logreg**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.348 | 0.352 | 0.361 | 1.141 | 0.687 | 0.066 | 0.544 | 23/34/42 | 0.0% |
| momentum_rule | 0.338 | 0.339 | 0.347 | n/a | n/a | n/a | 0.523 | 23/39/38 | 0.0% |
| stratified_random | 0.336 | 0.338 | 0.347 | 1.104 | 0.669 | 0.032 | 0.520 | 22/40/38 | 0.0% |
| random_forest | 0.334 | 0.337 | 0.348 | 1.145 | 0.691 | 0.083 | 0.483 | 25/41/34 | 0.0% |
| gbt | 0.326 | 0.328 | 0.338 | 1.179 | 0.710 | 0.139 | 0.483 | 24/37/38 | 0.0% |
| ma_cross_rule | 0.314 | 0.316 | 0.326 | n/a | n/a | n/a | 0.482 | 24/41/35 | 0.0% |
| majority | 0.178 | 0.333 | 0.364 | 1.104 | 0.669 | 0.032 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 28.0%, HOLD 36.4%, BUY 35.6%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.231 | 0.382 | 0.364 | 0.198 | 0.393 | 0.393 | 1.518% | 0.065% | 0.899% |
| logreg | 0.272 | 0.381 | 0.394 | 0.225 | 0.360 | 0.470 | 0.327% | 0.071% | 1.497% |
| ma_cross_rule | 0.231 | 0.357 | 0.354 | 0.195 | 0.406 | 0.347 | 1.879% | 0.212% | 0.580% |
| majority | 0.000 | 0.364 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.736% | n/a |
| momentum_rule | 0.280 | 0.368 | 0.367 | 0.233 | 0.394 | 0.389 | 0.876% | 0.840% | 0.541% |
| random_forest | 0.233 | 0.391 | 0.378 | 0.206 | 0.446 | 0.359 | 1.409% | -0.016% | 1.164% |
| stratified_random | 0.283 | 0.369 | 0.361 | 0.221 | 0.403 | 0.389 | 0.737% | 0.656% | 0.817% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | -0.0100 | -0.0393 to 0.0130 | 0.449 | 1.000 |
| logreg vs stratified_random | 0.0123 | -0.0296 to 0.0428 | 0.561 | 1.000 |
| ma_cross_rule vs stratified_random | -0.0222 | -0.0490 to 0.0044 | 0.113 | 0.565 |
| momentum_rule vs stratified_random | 0.0014 | -0.0257 to 0.0316 | 0.934 | 1.000 |
| random_forest vs stratified_random | -0.0017 | -0.0350 to 0.0267 | 0.914 | 1.000 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 9 | 8 | 103.5 | 0.1 | 26,760 |
| logreg | 9 | 8 | 20.0 | 0.0 | 26,760 |
| ma_cross_rule | 9 | 6 | 0.1 | 0.0 | 26,760 |
| majority | 9 | 1 | 0.0 | 0.0 | 26,760 |
| momentum_rule | 9 | 8 | 0.2 | 0.0 | 26,760 |
| random_forest | 9 | 8 | 23.7 | 0.2 | 26,760 |
| stratified_random | 9 | 1 | 0.0 | 0.0 | 26,760 |

Traditional models run locally at no marginal cost. External classifier status: jev/zero: not run: no saved outputs; jev/examples: not run: no saved outputs; openai/zero: not run: no saved outputs; openai/examples: not run: no saved outputs; local/zero: not run: no saved outputs; local/examples: not run: no saved outputs.

Models that did not run:

- `jev_head_examples` (GBT on Jev (TypeSafe jev-1.13.0) outputs, with training examples): not run: no saved outputs
- `jev_head_zero` (GBT on Jev (TypeSafe jev-1.13.0) outputs, zero-shot): not run: no saved outputs
- `jev_plus_controlled_examples` (GBT on controlled features + Jev (TypeSafe jev-1.13.0) outputs, with training examples): not run: no saved outputs
- `jev_plus_controlled_zero` (GBT on controlled features + Jev (TypeSafe jev-1.13.0) outputs, zero-shot): not run: no saved outputs
- `jev_signal_examples` (Jev (TypeSafe jev-1.13.0) as signal, with training examples): not run: no saved outputs
- `jev_signal_zero` (Jev (TypeSafe jev-1.13.0) as signal, zero-shot): not run: no saved outputs

## 8. Limitations

- Survivorship and hindsight bias in the stock list.
- Free vendor data: adjusted prices are revised after later corporate actions; opening prints may differ from achievable auction fills.
- Jev's training data and knowledge cutoff are undisclosed, so its historical results may reflect recall. Its state is anonymised to limit this, which cannot be proven sufficient.
- Jev is a hosted model that can change or be withdrawn; results are tied to the pinned version.
- Trading simulation ignores weight drift, market impact, borrow availability and taxes.
- Models are tuned for classification (validation macro-F1), not for trading performance.
- Volatility-scaled labels make the size of a move partly predictable from volatility clustering, so macro-F1 can rise without any ability to predict direction.

## 9. Conclusion

**Partial window.** This run excludes the last two years of folds, so it is not the verdict run. Nothing below is a final finding.

- **Trading performance (primary):** insufficient evidence. No external classifier has been run (not run: no saved outputs).
- **Classification performance:** insufficient evidence, for the same reason.
- **Operational efficiency:** insufficient evidence. No external classifier's runtime or cost has been measured.
- **Overall:** the evidence does not yet bear on whether Jev outperforms traditional models for stock trading.
