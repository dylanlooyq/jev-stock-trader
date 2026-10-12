# Experiment report: mixed15_dev_traditional

Generated 2026-10-12T03:46:10+00:00 from commit `115d3d1-dirty`, config `da3ca53cf20c`, dataset `0b91d318b8c2`. Final two years of folds included: **False**.

## 1. Research question and method

Can Jev, used as a classifier, outperform traditional models for trading? Each model's predictions are turned into a portfolio by the same rule and compared on net Sharpe ratio with a traditional classifier, with equal-weight buy and hold, and with a traditional classifier that is given Jev's outputs as extra inputs. Every model is fitted and scored on identical observations in a purged walk-forward design. Classification metrics are reported as diagnostics. The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.

## 2. Data and labels

- Universe: `mixed_15_v2`, 16 tickers obtained including the market proxy SPY; failed downloads: none.
- Source: yfinance daily bars, 2010-01-04 to 2026-09-30, downloaded 2026-10-12T03:12:20+00:00.
- The universe is a fixed list chosen with hindsight, not point-in-time membership. Survivorship bias inflates every absolute return here, including buy and hold of the same assets.
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

- Primary rule: Ranking portfolio: each day hold the top 4 of 15 assets by score, fully invested.
- Also reported: Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.
- Also reported: BUY-names portfolio: hold the assets labelled BUY, the rest in cash.
- Positions open at the next open and are held for h days in h daily tranches. Cost 5.0 bps per unit of turnover. Idle cash earns the Treasury bill rate; Sharpe and Sortino use returns in excess of that rate.
- `always_buy` holds every asset equally through the same engine and costs. It is the buy-and-hold benchmark. `market_buy_and_hold` is SPY, shown for context only.
- Models without scores of their own (`majority`, `stratified_random`) hold a random selection under the ranking rule, which is that rule's no-skill reference.
- Alpha and beta are measured against the market proxy. Sharpe L/S is the long-short version of the rule.

### Folds before the final two years, primary rule

Ranking portfolio: each day hold the top 4 of 15 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a |
| momentum_rule | 74.1% | 5.7% | 0.37 | 0.51 | -21.4% | 0.27 | 50.2 | 100.0% | -1.1% (-7.2% to 5.1%) | 0.48 | 0.49 | 0.17 | -0.32 |
| ma_cross_rule | 74.8% | 5.8% | 0.35 | 0.48 | -31.8% | 0.18 | 15.4 | 100.0% | -1.6% (-8.4% to 5.4%) | 0.53 | 0.38 | 0.30 | -0.09 |
| logreg | -28.1% | -3.3% | -0.30 | -0.39 | -40.3% | -0.08 | 173.7 | 100.0% | -10.1% (-16.8% to -3.8%) | 0.50 | 0.09 | -0.94 | -1.00 |
| random_forest | -30.9% | -3.6% | -0.32 | -0.43 | -37.3% | -0.10 | 218.9 | 100.0% | -12.2% (-17.2% to -7.1%) | 0.64 | 0.16 | -1.11 | -1.46 |
| gbt | -35.5% | -4.3% | -0.34 | -0.44 | -42.3% | -0.10 | 244.8 | 100.0% | -13.3% (-19.0% to -7.8%) | 0.69 | 0.16 | -1.17 | -1.46 |
| majority | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| stratified_random | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.86 | -1.27 to -0.51 | 0.000 | 0.002 |
| logreg vs always_buy | -0.82 | -1.37 to -0.31 | 0.003 | 0.009 |
| ma_cross_rule vs always_buy | -0.17 | -0.66 to 0.27 | 0.473 | 0.946 |
| momentum_rule vs always_buy | -0.15 | -0.68 to 0.33 | 0.540 | 0.946 |
| random_forest vs always_buy | -0.84 | -1.27 to -0.48 | 0.000 | 0.002 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| random_forest | 83.8% | 6.3% | 0.40 | 0.55 | -23.3% | 0.27 | 50.6 | 99.8% | -3.0% (-7.1% to 1.4%) | 0.68 | 0.51 | 0.21 | -0.39 |
| momentum_rule | 55.9% | 4.5% | 0.29 | 0.39 | -25.3% | 0.18 | 20.5 | 99.8% | -2.0% (-7.8% to 4.0%) | 0.46 | 0.33 | 0.20 | -0.26 |
| gbt | 52.9% | 4.3% | 0.25 | 0.35 | -33.8% | 0.13 | 51.1 | 99.8% | -5.1% (-10.0% to -0.1%) | 0.71 | 0.36 | 0.08 | -0.59 |
| ma_cross_rule | 52.2% | 4.3% | 0.25 | 0.33 | -28.7% | 0.15 | 12.1 | 99.8% | -3.4% (-9.2% to 3.0%) | 0.57 | 0.28 | 0.21 | -0.22 |
| majority | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| stratified_random | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| logreg | -9.7% | -1.0% | -0.15 | -0.20 | -34.3% | -0.03 | 43.7 | 99.8% | -8.0% (-13.0% to -2.5%) | 0.50 | -0.05 | -0.33 | -0.76 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.27 | -0.58 to 0.01 | 0.080 | 0.322 |
| logreg vs always_buy | -0.67 | -1.14 to -0.27 | 0.002 | 0.012 |
| ma_cross_rule vs always_buy | -0.27 | -0.72 to 0.14 | 0.229 | 0.687 |
| momentum_rule vs always_buy | -0.24 | -0.73 to 0.23 | 0.338 | 0.687 |
| random_forest vs always_buy | -0.12 | -0.45 to 0.16 | 0.448 | 0.687 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.5% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.2% | -1.6% | 0.66 | n/a | n/a | n/a |
| majority | 107.1% | 7.6% | 0.51 | 0.70 | -27.2% | 0.28 | 18.2 | 99.2% | -1.7% (-5.4% to 2.2%) | 0.66 | 0.56 | 0.44 | 0.00 |
| stratified_random | 107.1% | 7.6% | 0.51 | 0.70 | -27.2% | 0.28 | 18.2 | 99.2% | -1.7% (-5.4% to 2.2%) | 0.66 | 0.56 | 0.44 | 0.00 |
| random_forest | 112.1% | 7.8% | 0.48 | 0.67 | -27.2% | 0.29 | 13.4 | 99.2% | -1.9% (-6.0% to 2.0%) | 0.72 | 0.51 | 0.44 | -0.14 |
| ma_cross_rule | 96.1% | 7.0% | 0.41 | 0.55 | -30.5% | 0.23 | 6.2 | 99.2% | -1.4% (-8.0% to 6.0%) | 0.62 | 0.43 | 0.39 | 0.06 |
| momentum_rule | 80.9% | 6.1% | 0.41 | 0.55 | -23.3% | 0.26 | 9.5 | 99.2% | -1.0% (-6.5% to 5.4%) | 0.50 | 0.43 | 0.37 | 0.02 |
| gbt | 79.1% | 6.0% | 0.38 | 0.53 | -30.6% | 0.20 | 15.0 | 99.2% | -3.2% (-7.8% to 1.5%) | 0.68 | 0.41 | 0.32 | -0.33 |
| logreg | 48.2% | 4.0% | 0.28 | 0.39 | -18.7% | 0.21 | 14.2 | 99.2% | -2.3% (-6.5% to 1.7%) | 0.41 | 0.33 | 0.21 | -0.38 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.14 | -0.50 to 0.18 | 0.421 | 1.000 |
| logreg vs always_buy | -0.24 | -0.68 to 0.17 | 0.275 | 1.000 |
| ma_cross_rule vs always_buy | -0.11 | -0.52 to 0.29 | 0.576 | 1.000 |
| momentum_rule vs always_buy | -0.11 | -0.55 to 0.29 | 0.592 | 1.000 |
| random_forest vs always_buy | -0.04 | -0.29 to 0.20 | 0.767 | 1.000 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a |
| ma_cross_rule | 19.5% | 1.8% | 0.13 | 0.18 | -48.9% | 0.04 | 23.9 | 100.0% | -4.3% (-15.7% to 8.7%) | 0.61 | 0.16 | 0.08 | -0.45 |
| gbt | -43.6% | -5.6% | -0.24 | -0.33 | -64.6% | -0.09 | 342.4 | 100.0% | -13.7% (-25.1% to -2.8%) | 0.70 | 0.24 | -1.04 | -0.76 |
| momentum_rule | -62.3% | -9.3% | -0.45 | -0.58 | -66.2% | -0.14 | 89.5 | 100.0% | -13.3% (-25.0% to -2.2%) | 0.33 | -0.32 | -0.67 | -0.32 |
| logreg | -76.3% | -13.4% | -0.54 | -0.72 | -76.3% | -0.18 | 271.4 | 100.0% | -19.2% (-33.5% to -5.1%) | 0.50 | -0.20 | -1.09 | -0.63 |
| random_forest | -61.8% | -9.2% | -0.55 | -0.74 | -63.0% | -0.15 | 324.5 | 100.0% | -16.4% (-25.1% to -7.5%) | 0.55 | 0.00 | -1.47 | -1.00 |
| majority | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| stratified_random | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.76 | -1.34 to -0.23 | 0.008 | 0.018 |
| logreg vs always_buy | -1.06 | -1.78 to -0.44 | 0.003 | 0.012 |
| ma_cross_rule vs always_buy | -0.39 | -1.02 to 0.16 | 0.191 | 0.191 |
| momentum_rule vs always_buy | -0.98 | -1.72 to -0.32 | 0.006 | 0.018 |
| random_forest vs always_buy | -1.08 | -1.77 to -0.46 | 0.001 | 0.005 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| gbt | 69.5% | 5.4% | 0.30 | 0.42 | -47.9% | 0.11 | 70.8 | 99.8% | -2.4% (-14.0% to 7.3%) | 0.62 | 0.42 | 0.09 | -0.36 |
| momentum_rule | 38.0% | 3.3% | 0.18 | 0.25 | -29.5% | 0.11 | 37.3 | 99.8% | -0.6% (-9.6% to 8.7%) | 0.31 | 0.24 | 0.07 | 0.11 |
| majority | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| stratified_random | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| random_forest | 1.6% | 0.2% | -0.02 | -0.02 | -48.4% | 0.00 | 74.2 | 99.8% | -8.2% (-16.2% to -0.5%) | 0.65 | 0.13 | -0.25 | -0.51 |
| ma_cross_rule | -27.5% | -3.2% | -0.08 | -0.11 | -51.3% | -0.06 | 19.5 | 99.8% | -9.5% (-20.7% to 3.7%) | 0.62 | -0.06 | -0.12 | -0.46 |
| logreg | -70.3% | -11.4% | -0.62 | -0.81 | -71.7% | -0.16 | 66.0 | 99.8% | -17.6% (-29.5% to -6.2%) | 0.47 | -0.51 | -0.79 | -0.43 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.23 | -0.91 to 0.38 | 0.496 | 0.589 |
| logreg vs always_buy | -1.14 | -1.84 to -0.43 | 0.004 | 0.020 |
| ma_cross_rule vs always_buy | -0.60 | -1.23 to -0.06 | 0.049 | 0.198 |
| momentum_rule vs always_buy | -0.34 | -1.03 to 0.26 | 0.294 | 0.589 |
| random_forest vs always_buy | -0.54 | -1.12 to -0.02 | 0.057 | 0.198 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.5% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.2% | -1.6% | 0.66 | n/a | n/a | n/a |
| majority | 93.2% | 6.8% | 0.44 | 0.59 | -31.5% | 0.22 | 23.3 | 99.2% | -2.4% (-7.7% to 2.6%) | 0.68 | 0.49 | 0.35 | -0.22 |
| stratified_random | 93.2% | 6.8% | 0.44 | 0.59 | -31.5% | 0.22 | 23.3 | 99.2% | -2.4% (-7.7% to 2.6%) | 0.68 | 0.49 | 0.35 | -0.22 |
| random_forest | 72.3% | 5.6% | 0.33 | 0.46 | -23.3% | 0.24 | 18.9 | 99.2% | -3.5% (-8.5% to 1.2%) | 0.69 | 0.37 | 0.27 | -0.40 |
| gbt | 69.3% | 5.4% | 0.32 | 0.47 | -30.4% | 0.18 | 18.8 | 99.2% | -2.9% (-9.1% to 3.3%) | 0.62 | 0.36 | 0.26 | -0.49 |
| logreg | 49.9% | 4.1% | 0.24 | 0.34 | -35.0% | 0.12 | 19.6 | 99.2% | -0.2% (-9.6% to 7.9%) | 0.30 | 0.28 | 0.17 | -0.17 |
| momentum_rule | 34.1% | 3.0% | 0.16 | 0.22 | -31.8% | 0.09 | 15.1 | 99.2% | -2.2% (-10.6% to 7.2%) | 0.39 | 0.19 | 0.11 | 0.05 |
| ma_cross_rule | -15.9% | -1.7% | -0.03 | -0.03 | -49.4% | -0.03 | 11.1 | 99.2% | -9.0% (-19.8% to 3.3%) | 0.69 | -0.01 | -0.05 | -0.13 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.20 | -0.76 to 0.30 | 0.479 | 1.000 |
| logreg vs always_buy | -0.28 | -1.03 to 0.45 | 0.452 | 1.000 |
| ma_cross_rule vs always_buy | -0.55 | -1.14 to -0.02 | 0.055 | 0.275 |
| momentum_rule vs always_buy | -0.36 | -1.02 to 0.25 | 0.265 | 1.000 |
| random_forest vs always_buy | -0.19 | -0.57 to 0.18 | 0.319 | 1.000 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 52.4% | 4.3% | 0.54 | 0.75 | -7.3% | 0.59 | 13.0 | 44.0% | 0.8% (-1.9% to 3.4%) | 0.16 | 0.62 | 0.41 | 0.05 | 0.58 | 0.0% |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| ma_cross_rule | 38.0% | 3.3% | 0.40 | 0.55 | -6.7% | 0.49 | 16.3 | 39.7% | 0.3% (-1.8% to 2.5%) | 0.11 | 0.52 | 0.20 | -0.31 | 0.44 | -0.1% |
| logreg | 21.2% | 1.9% | 0.08 | 0.10 | -21.0% | 0.09 | 32.2 | 27.5% | -3.3% (-6.6% to 0.1%) | 0.32 | 0.20 | -0.13 | -0.69 | 0.27 | -1.5% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| gbt | 9.2% | 0.9% | -0.06 | -0.08 | -26.8% | 0.03 | 54.7 | 28.6% | -4.2% (-7.6% to -0.7%) | 0.30 | 0.15 | -0.43 | -1.02 | 0.22 | -2.1% |
| random_forest | 7.3% | 0.7% | -0.08 | -0.11 | -23.3% | 0.03 | 39.2 | 28.6% | -4.8% (-8.3% to -1.5%) | 0.34 | 0.07 | -0.33 | -1.03 | 0.20 | -2.1% |
| stratified_random | -6.5% | -0.7% | -0.48 | -0.61 | -18.9% | -0.04 | 106.0 | 29.8% | -4.7% (-6.9% to -2.6%) | 0.20 | 0.21 | -1.62 | -2.01 | 0.45 | -4.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.59 | -1.02 to -0.16 | 0.010 | 0.040 |
| logreg vs always_buy | -0.45 | -0.91 to -0.02 | 0.047 | 0.141 |
| ma_cross_rule vs always_buy | -0.12 | -0.73 to 0.46 | 0.687 | 1.000 |
| momentum_rule vs always_buy | 0.02 | -0.55 to 0.61 | 0.937 | 1.000 |
| random_forest vs always_buy | -0.60 | -1.03 to -0.20 | 0.004 | 0.020 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 33.4% | 2.9% | 0.33 | 0.46 | -8.6% | 0.34 | 22.0 | 32.2% | -1.2% (-2.3% to 0.1%) | 0.20 | 0.50 | 0.06 | -0.86 | 0.53 | -0.7% |
| momentum_rule | 32.5% | 2.9% | 0.29 | 0.39 | -8.2% | 0.35 | 5.9 | 38.8% | -0.4% (-2.7% to 1.8%) | 0.14 | 0.33 | 0.22 | -0.26 | 0.32 | -0.0% |
| gbt | 35.3% | 3.1% | 0.23 | 0.31 | -16.5% | 0.19 | 13.5 | 32.8% | -2.4% (-4.8% to 0.2%) | 0.33 | 0.28 | 0.13 | -0.18 | 0.36 | -0.8% |
| ma_cross_rule | 25.1% | 2.3% | 0.17 | 0.22 | -8.7% | 0.26 | 8.7 | 39.9% | -0.9% (-3.0% to 1.2%) | 0.13 | 0.23 | 0.06 | -0.39 | 0.31 | -0.6% |
| random_forest | 30.3% | 2.7% | 0.16 | 0.22 | -22.8% | 0.12 | 11.2 | 31.7% | -3.1% (-6.8% to 0.4%) | 0.37 | 0.21 | 0.10 | -0.34 | 0.26 | -0.7% |
| logreg | 23.7% | 2.2% | 0.10 | 0.13 | -20.9% | 0.10 | 10.9 | 30.7% | -3.1% (-6.6% to 0.3%) | 0.31 | 0.15 | 0.03 | -0.34 | 0.20 | -0.7% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.29 | -0.68 to 0.06 | 0.124 | 0.372 |
| logreg vs always_buy | -0.42 | -0.81 to -0.01 | 0.041 | 0.207 |
| ma_cross_rule vs always_buy | -0.35 | -0.90 to 0.12 | 0.179 | 0.372 |
| momentum_rule vs always_buy | -0.23 | -0.78 to 0.25 | 0.395 | 0.395 |
| random_forest vs always_buy | -0.36 | -0.74 to 0.03 | 0.074 | 0.298 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.5% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.2% | -1.6% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| ma_cross_rule | 41.3% | 3.5% | 0.42 | 0.56 | -7.9% | 0.45 | 3.6 | 40.7% | -0.2% (-2.4% to 1.9%) | 0.17 | 0.44 | 0.38 | -0.01 | 0.40 | 0.1% |
| stratified_random | 40.2% | 3.4% | 0.41 | 0.56 | -11.2% | 0.31 | 5.7 | 35.1% | -1.1% (-2.4% to 0.2%) | 0.24 | 0.45 | 0.35 | -0.09 | 0.49 | -0.3% |
| momentum_rule | 37.4% | 3.2% | 0.35 | 0.45 | -13.0% | 0.25 | 2.9 | 40.7% | -0.5% (-3.1% to 2.1%) | 0.18 | 0.37 | 0.32 | -0.05 | 0.30 | 0.3% |
| random_forest | 45.4% | 3.8% | 0.33 | 0.46 | -15.1% | 0.25 | 4.3 | 37.6% | -1.5% (-3.7% to 0.7%) | 0.32 | 0.35 | 0.30 | 0.01 | 0.40 | -0.4% |
| logreg | 41.7% | 3.6% | 0.33 | 0.46 | -11.3% | 0.31 | 4.2 | 34.7% | -1.2% (-3.5% to 1.1%) | 0.26 | 0.35 | 0.30 | -0.06 | 0.41 | -0.7% |
| gbt | 38.6% | 3.3% | 0.27 | 0.39 | -13.9% | 0.24 | 4.4 | 37.5% | -1.9% (-4.0% to 0.5%) | 0.31 | 0.29 | 0.24 | -0.14 | 0.36 | -0.4% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.25 | -0.71 to 0.12 | 0.230 | 1.000 |
| logreg vs always_buy | -0.19 | -0.67 to 0.23 | 0.410 | 1.000 |
| ma_cross_rule vs always_buy | -0.10 | -0.53 to 0.28 | 0.611 | 1.000 |
| momentum_rule vs always_buy | -0.17 | -0.58 to 0.25 | 0.411 | 1.000 |
| random_forest vs always_buy | -0.19 | -0.63 to 0.18 | 0.331 | 1.000 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.43 (median of 5 comparisons). A true difference smaller than about 0.62 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

37,710 test observations on 2,514 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.372 | 0.372 | 0.396 | 1.087 | 0.658 | 0.005 | 0.501 | 27/45/28 | 0.0% |
| random_forest | 0.367 | 0.368 | 0.397 | 1.087 | 0.658 | 0.017 | 0.501 | 23/48/29 | 0.0% |
| gbt | 0.365 | 0.366 | 0.377 | 1.100 | 0.667 | 0.045 | 0.495 | 33/38/29 | 0.0% |
| momentum_rule | 0.340 | 0.345 | 0.357 | n/a | n/a | n/a | 0.523 | 18/38/44 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.352 | 1.073 | 0.649 | 0.005 | 0.510 | 26/44/30 | 0.0% |
| ma_cross_rule | 0.331 | 0.333 | 0.345 | n/a | n/a | n/a | 0.516 | 21/39/40 | 0.0% |
| majority | 0.204 | 0.333 | 0.440 | 1.073 | 0.649 | 0.005 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 26.1%, HOLD 44.0%, BUY 29.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.269 | 0.505 | 0.331 | 0.343 | 0.438 | 0.316 | 0.041% | 0.020% | 0.038% |
| logreg | 0.276 | 0.503 | 0.338 | 0.289 | 0.517 | 0.311 | 0.028% | 0.032% | 0.038% |
| ma_cross_rule | 0.287 | 0.434 | 0.288 | 0.232 | 0.386 | 0.382 | 0.069% | 0.013% | 0.031% |
| majority | 0.000 | 0.440 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.032% | n/a |
| momentum_rule | 0.294 | 0.455 | 0.299 | 0.206 | 0.389 | 0.441 | 0.027% | 0.029% | 0.037% |
| random_forest | 0.272 | 0.494 | 0.334 | 0.242 | 0.541 | 0.320 | 0.046% | 0.030% | 0.024% |
| stratified_random | 0.262 | 0.436 | 0.303 | 0.259 | 0.441 | 0.302 | 0.031% | 0.023% | 0.048% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0307 | 0.0213 to 0.0399 | 0.000 | 0.002 |
| logreg vs stratified_random | 0.0379 | 0.0281 to 0.0469 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | -0.0030 | -0.0120 to 0.0058 | 0.505 | 0.599 |
| momentum_rule vs stratified_random | 0.0055 | -0.0049 to 0.0156 | 0.299 | 0.599 |
| random_forest vs stratified_random | 0.0325 | 0.0237 to 0.0410 | 0.000 | 0.002 |

### 5-day horizon (primary)

37,650 test observations on 2,510 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.366 | 0.366 | 0.381 | 1.098 | 0.665 | 0.032 | 0.498 | 29/40/31 | 0.0% |
| random_forest | 0.364 | 0.364 | 0.376 | 1.095 | 0.664 | 0.028 | 0.499 | 30/39/32 | 0.0% |
| gbt | 0.355 | 0.358 | 0.359 | 1.128 | 0.685 | 0.097 | 0.500 | 35/33/33 | 0.0% |
| momentum_rule | 0.338 | 0.339 | 0.353 | n/a | n/a | n/a | 0.513 | 22/39/39 | 0.0% |
| stratified_random | 0.333 | 0.333 | 0.348 | 1.079 | 0.653 | 0.002 | 0.506 | 26/42/32 | 0.0% |
| ma_cross_rule | 0.330 | 0.331 | 0.346 | n/a | n/a | n/a | 0.512 | 20/40/40 | 0.0% |
| majority | 0.197 | 0.333 | 0.419 | 1.079 | 0.653 | 0.002 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.4%, HOLD 41.9%, BUY 32.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.256 | 0.474 | 0.355 | 0.349 | 0.368 | 0.356 | 0.150% | 0.163% | 0.169% |
| logreg | 0.256 | 0.484 | 0.363 | 0.293 | 0.465 | 0.341 | 0.197% | 0.168% | 0.116% |
| ma_cross_rule | 0.277 | 0.417 | 0.307 | 0.216 | 0.402 | 0.375 | 0.333% | 0.146% | 0.089% |
| majority | 0.000 | 0.419 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.160% | n/a |
| momentum_rule | 0.261 | 0.431 | 0.326 | 0.225 | 0.404 | 0.387 | 0.319% | 0.119% | 0.113% |
| random_forest | 0.257 | 0.481 | 0.359 | 0.299 | 0.444 | 0.349 | 0.180% | 0.155% | 0.148% |
| stratified_random | 0.249 | 0.420 | 0.331 | 0.251 | 0.423 | 0.326 | 0.183% | 0.130% | 0.182% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0216 | 0.0066 to 0.0356 | 0.003 | 0.010 |
| logreg vs stratified_random | 0.0329 | 0.0184 to 0.0465 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | -0.0037 | -0.0158 to 0.0077 | 0.554 | 0.997 |
| momentum_rule vs stratified_random | 0.0041 | -0.0077 to 0.0159 | 0.498 | 0.997 |
| random_forest vs stratified_random | 0.0306 | 0.0166 to 0.0443 | 0.000 | 0.002 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 3,334 | 2,762 | 3,463 | 0 |
| HOLD | 5,435 | 5,806 | 4,524 | 0 |
| BUY | 4,257 | 3,679 | 4,390 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,799 | 3,434 | 3,326 | 0 |
| HOLD | 4,377 | 7,325 | 4,063 | 0 |
| BUY | 3,742 | 4,379 | 4,205 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,062 | 3,818 | 3,679 | 0 |
| HOLD | 2,691 | 6,330 | 6,744 | 0 |
| BUY | 2,690 | 5,018 | 4,618 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 9,559 | 0 | 0 |
| HOLD | 0 | 15,765 | 0 | 0 |
| BUY | 0 | 12,326 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,149 | 3,721 | 3,689 | 0 |
| HOLD | 3,211 | 6,370 | 6,184 | 0 |
| BUY | 2,872 | 4,680 | 4,774 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,859 | 3,318 | 3,382 | 0 |
| HOLD | 4,474 | 7,001 | 4,290 | 0 |
| BUY | 3,798 | 4,229 | 4,299 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,400 | 4,063 | 3,096 | 0 |
| HOLD | 4,059 | 6,673 | 5,033 | 0 |
| BUY | 3,162 | 5,145 | 4,019 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.313 | 0.397 | 0.331 | 0.353 | 0.366 | 0.419 | 0.196 | 0.305 | 0.345 | 0.357 |
| logreg | 0.318 | 0.401 | 0.328 | 0.354 | 0.390 | 0.408 | 0.191 | 0.295 | 0.374 | 0.361 |
| ma_cross_rule | 0.334 | 0.317 | 0.302 | 0.346 | 0.305 | 0.353 | 0.314 | 0.325 | 0.319 | 0.294 |
| majority | 0.191 | 0.207 | 0.201 | 0.185 | 0.193 | 0.216 | 0.207 | 0.181 | 0.198 | 0.185 |
| momentum_rule | 0.347 | 0.350 | 0.328 | 0.340 | 0.315 | 0.380 | 0.307 | 0.328 | 0.313 | 0.296 |
| random_forest | 0.330 | 0.401 | 0.349 | 0.370 | 0.378 | 0.421 | 0.245 | 0.284 | 0.339 | 0.355 |
| stratified_random | 0.345 | 0.333 | 0.319 | 0.334 | 0.328 | 0.326 | 0.336 | 0.335 | 0.343 | 0.327 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.352 | 0.357 | 0.334 |
| logreg | 0.345 | 0.361 | 0.351 |
| ma_cross_rule | 0.331 | 0.336 | 0.313 |
| majority | 0.191 | 0.200 | 0.196 |
| momentum_rule | 0.326 | 0.342 | 0.325 |
| random_forest | 0.343 | 0.363 | 0.344 |
| stratified_random | 0.337 | 0.332 | 0.333 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.326 | 0.355 | 0.372 | 15 |
| logreg | 0.339 | 0.365 | 0.380 | 15 |
| ma_cross_rule | 0.309 | 0.322 | 0.351 | 15 |
| majority | 0.190 | 0.196 | 0.204 | 15 |
| momentum_rule | 0.307 | 0.335 | 0.355 | 15 |
| random_forest | 0.326 | 0.363 | 0.385 | 15 |
| stratified_random | 0.326 | 0.334 | 0.339 | 15 |

### 20-day horizon

37,425 test observations on 2,495 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.357 | 0.357 | 0.367 | 1.116 | 0.677 | 0.056 | 0.507 | 28/34/38 | 0.0% |
| logreg | 0.355 | 0.355 | 0.367 | 1.125 | 0.680 | 0.067 | 0.501 | 29/36/35 | 0.0% |
| momentum_rule | 0.345 | 0.346 | 0.364 | n/a | n/a | n/a | 0.541 | 20/39/41 | 0.0% |
| gbt | 0.344 | 0.345 | 0.353 | 1.174 | 0.710 | 0.136 | 0.498 | 30/32/38 | 0.0% |
| ma_cross_rule | 0.342 | 0.343 | 0.362 | n/a | n/a | n/a | 0.539 | 19/40/41 | 0.0% |
| stratified_random | 0.329 | 0.329 | 0.341 | 1.081 | 0.656 | 0.011 | 0.513 | 25/40/35 | 0.0% |
| majority | 0.189 | 0.333 | 0.396 | 1.081 | 0.656 | 0.011 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 24.6%, HOLD 39.6%, BUY 35.8%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.233 | 0.439 | 0.373 | 0.283 | 0.359 | 0.394 | 0.815% | 0.589% | 0.555% |
| logreg | 0.233 | 0.451 | 0.388 | 0.272 | 0.414 | 0.380 | 0.717% | 0.602% | 0.626% |
| ma_cross_rule | 0.261 | 0.409 | 0.362 | 0.201 | 0.413 | 0.415 | 0.966% | 0.600% | 0.536% |
| majority | 0.000 | 0.396 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.643% | n/a |
| momentum_rule | 0.257 | 0.414 | 0.369 | 0.207 | 0.410 | 0.423 | 0.973% | 0.644% | 0.484% |
| random_forest | 0.237 | 0.456 | 0.385 | 0.272 | 0.390 | 0.408 | 0.699% | 0.581% | 0.657% |
| stratified_random | 0.242 | 0.391 | 0.355 | 0.245 | 0.393 | 0.350 | 0.675% | 0.652% | 0.611% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0151 | -0.0121 to 0.0413 | 0.258 | 0.519 |
| logreg vs stratified_random | 0.0261 | -0.0010 to 0.0522 | 0.055 | 0.260 |
| ma_cross_rule vs stratified_random | 0.0125 | -0.0114 to 0.0352 | 0.284 | 0.519 |
| momentum_rule vs stratified_random | 0.0157 | -0.0075 to 0.0375 | 0.173 | 0.519 |
| random_forest vs stratified_random | 0.0274 | -0.0006 to 0.0546 | 0.052 | 0.260 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 30 | 8 | 807.2 | 2.1 | 112,785 |
| logreg | 30 | 8 | 90.8 | 0.1 | 112,785 |
| ma_cross_rule | 30 | 6 | 0.9 | 0.0 | 112,785 |
| majority | 30 | 1 | 0.2 | 0.0 | 112,785 |
| momentum_rule | 30 | 8 | 1.1 | 0.0 | 112,785 |
| random_forest | 30 | 8 | 522.1 | 3.3 | 112,785 |
| stratified_random | 30 | 1 | 0.2 | 0.0 | 112,785 |

Traditional models run locally at no marginal cost. External classifier status: jev/zero: not run: no saved outputs; jev/examples: not run: no saved outputs; openai/zero: not run: no saved outputs; openai/examples: not run: no saved outputs; local/zero: not run: no saved outputs; local/examples: not run: no saved outputs.

## 8. Limitations

- Survivorship and hindsight bias in the asset list.
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
- **Overall:** the evidence does not yet bear on whether Jev outperforms traditional models for trading.
