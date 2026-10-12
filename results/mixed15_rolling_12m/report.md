# Experiment report: mixed15_rolling_12m

Generated 2026-10-12T05:12:59+00:00 from commit `115d3d1-dirty`, config `9e944fb1b0ef`, dataset `0b91d318b8c2`. Final two years of folds included: **False**.

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

- Walk-forward folds of 12 months, rolling 12-month training window (exploratory variant), 4-month validation tail used for all tuning.
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
| ma_cross_rule | 112.5% | 7.8% | 0.48 | 0.66 | -23.7% | 0.33 | 16.1 | 100.0% | 0.2% (-6.8% to 6.9%) | 0.55 | 0.51 | 0.42 | 0.04 |
| momentum_rule | 63.9% | 5.1% | 0.34 | 0.47 | -26.4% | 0.19 | 46.8 | 100.0% | -0.7% (-6.9% to 5.7%) | 0.38 | 0.46 | 0.14 | -0.29 |
| gbt | -16.1% | -1.7% | -0.14 | -0.18 | -42.0% | -0.04 | 226.6 | 100.0% | -10.6% (-17.1% to -4.1%) | 0.69 | 0.30 | -0.86 | -1.48 |
| logreg | -25.3% | -2.9% | -0.26 | -0.35 | -41.0% | -0.07 | 160.6 | 100.0% | -10.1% (-16.2% to -4.3%) | 0.53 | 0.09 | -0.85 | -1.00 |
| jev_plus_controlled_zero | -37.9% | -4.7% | -0.32 | -0.43 | -58.9% | -0.08 | 251.5 | 100.0% | -13.7% (-20.3% to -7.0%) | 0.70 | 0.15 | -1.10 | -1.50 |
| random_forest | -48.8% | -6.5% | -0.48 | -0.64 | -57.3% | -0.11 | 196.7 | 100.0% | -15.3% (-21.3% to -9.1%) | 0.66 | -0.09 | -1.14 | -1.78 |
| jev_head_zero | -55.7% | -7.8% | -0.59 | -0.78 | -65.6% | -0.12 | 334.7 | 100.0% | -16.6% (-23.2% to -10.0%) | 0.65 | 0.09 | -1.71 | -1.96 |
| majority | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| stratified_random | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| jev_signal_zero | -69.3% | -11.2% | -0.89 | -1.21 | -72.5% | -0.15 | 346.1 | 100.0% | -18.9% (-25.7% to -12.1%) | 0.52 | -0.15 | -2.13 | -1.95 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.66 | -1.04 to -0.32 | 0.002 | 0.008 |
| jev_head_zero vs always_buy | -1.11 | -1.51 to -0.74 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.84 | -1.24 to -0.48 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -1.41 | -1.99 to -0.88 | 0.000 | 0.004 |
| logreg vs always_buy | -0.79 | -1.27 to -0.32 | 0.002 | 0.008 |
| ma_cross_rule vs always_buy | -0.05 | -0.55 to 0.43 | 0.841 | 1.000 |
| momentum_rule vs always_buy | -0.19 | -0.79 to 0.39 | 0.514 | 1.000 |
| random_forest vs always_buy | -1.01 | -1.46 to -0.61 | 0.000 | 0.004 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.45 | -0.94 to 0.06 | 0.072 | 0.145 |
| jev_plus_controlled_zero vs gbt | -0.18 | -0.55 to 0.16 | 0.317 | 0.317 |
| jev_signal_zero vs gbt | -0.75 | -1.36 to -0.17 | 0.015 | 0.045 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.18 | -0.55 to 0.16 | 0.317 | 0.317 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.57 | -1.14 to -0.01 | 0.046 | 0.046 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| ma_cross_rule | 69.1% | 5.4% | 0.32 | 0.43 | -26.1% | 0.21 | 12.1 | 99.8% | -2.1% (-8.4% to 4.3%) | 0.55 | 0.35 | 0.28 | -0.09 |
| momentum_rule | 47.8% | 4.0% | 0.25 | 0.34 | -26.8% | 0.15 | 19.8 | 99.8% | -2.0% (-7.7% to 3.7%) | 0.41 | 0.31 | 0.17 | -0.33 |
| majority | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| stratified_random | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| jev_head_zero | 39.6% | 3.4% | 0.19 | 0.26 | -31.2% | 0.11 | 69.5 | 99.8% | -5.8% (-10.0% to -1.6%) | 0.69 | 0.35 | -0.06 | -0.67 |
| jev_signal_zero | 24.6% | 2.2% | 0.11 | 0.14 | -26.5% | 0.08 | 73.0 | 99.8% | -5.3% (-9.6% to -1.0%) | 0.53 | 0.30 | -0.21 | -0.76 |
| jev_plus_controlled_zero | 0.7% | 0.1% | -0.02 | -0.02 | -40.8% | 0.00 | 51.5 | 99.8% | -9.3% (-15.8% to -3.1%) | 0.74 | 0.08 | -0.18 | -0.80 |
| gbt | 0.6% | 0.1% | -0.02 | -0.03 | -39.7% | 0.00 | 49.1 | 99.8% | -9.2% (-15.8% to -3.2%) | 0.73 | 0.07 | -0.18 | -0.92 |
| random_forest | -0.5% | -0.1% | -0.04 | -0.05 | -37.8% | -0.00 | 45.7 | 99.8% | -9.2% (-15.2% to -3.5%) | 0.71 | 0.05 | -0.19 | -0.83 |
| logreg | -9.2% | -1.0% | -0.13 | -0.17 | -31.2% | -0.03 | 44.7 | 99.8% | -8.6% (-14.2% to -3.1%) | 0.57 | -0.03 | -0.29 | -0.86 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.54 | -0.85 to -0.26 | 0.000 | 0.004 |
| jev_head_zero vs always_buy | -0.33 | -0.58 to -0.10 | 0.008 | 0.032 |
| jev_plus_controlled_zero vs always_buy | -0.54 | -0.83 to -0.27 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -0.41 | -0.72 to -0.14 | 0.008 | 0.032 |
| logreg vs always_buy | -0.65 | -1.06 to -0.28 | 0.002 | 0.010 |
| ma_cross_rule vs always_buy | -0.20 | -0.65 to 0.22 | 0.378 | 0.698 |
| momentum_rule vs always_buy | -0.27 | -0.81 to 0.24 | 0.349 | 0.698 |
| random_forest vs always_buy | -0.56 | -0.88 to -0.23 | 0.000 | 0.004 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs random_forest | 0.23 | -0.10 to 0.54 | 0.140 | 0.421 |
| jev_plus_controlled_zero vs random_forest | 0.02 | -0.22 to 0.26 | 0.886 | 1.000 |
| jev_signal_zero vs random_forest | 0.14 | -0.34 to 0.60 | 0.543 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.00 | -0.13 to 0.14 | 0.978 | 0.978 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.13 | -0.33 to 0.56 | 0.566 | 0.566 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.5% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.2% | -1.6% | 0.66 | n/a | n/a | n/a |
| majority | 107.1% | 7.6% | 0.51 | 0.70 | -27.2% | 0.28 | 18.2 | 99.2% | -1.7% (-5.4% to 2.2%) | 0.66 | 0.56 | 0.44 | 0.00 |
| stratified_random | 107.1% | 7.6% | 0.51 | 0.70 | -27.2% | 0.28 | 18.2 | 99.2% | -1.7% (-5.4% to 2.2%) | 0.66 | 0.56 | 0.44 | 0.00 |
| jev_signal_zero | 87.9% | 6.5% | 0.47 | 0.63 | -20.0% | 0.33 | 18.0 | 99.2% | -1.4% (-5.2% to 2.3%) | 0.55 | 0.51 | 0.39 | -0.17 |
| ma_cross_rule | 103.9% | 7.4% | 0.44 | 0.59 | -27.0% | 0.27 | 6.1 | 99.2% | -0.9% (-7.4% to 6.6%) | 0.61 | 0.46 | 0.42 | 0.06 |
| logreg | 71.9% | 5.6% | 0.39 | 0.54 | -19.2% | 0.29 | 13.0 | 99.2% | -0.9% (-5.8% to 4.3%) | 0.43 | 0.42 | 0.33 | -0.13 |
| momentum_rule | 69.0% | 5.4% | 0.36 | 0.48 | -23.1% | 0.23 | 8.5 | 99.2% | -1.5% (-6.5% to 3.8%) | 0.48 | 0.38 | 0.32 | 0.04 |
| jev_head_zero | 59.2% | 4.8% | 0.30 | 0.40 | -30.4% | 0.16 | 18.0 | 99.2% | -4.4% (-8.6% to -0.2%) | 0.68 | 0.34 | 0.23 | -0.52 |
| gbt | 51.3% | 4.2% | 0.26 | 0.35 | -25.8% | 0.16 | 14.8 | 99.2% | -4.3% (-9.0% to 0.5%) | 0.62 | 0.29 | 0.20 | -0.41 |
| jev_plus_controlled_zero | 42.3% | 3.6% | 0.21 | 0.28 | -26.7% | 0.13 | 14.5 | 99.2% | -4.8% (-9.7% to -0.0%) | 0.62 | 0.24 | 0.15 | -0.54 |
| random_forest | 35.3% | 3.1% | 0.17 | 0.23 | -26.5% | 0.12 | 13.5 | 99.2% | -5.2% (-9.4% to -1.3%) | 0.61 | 0.20 | 0.12 | -0.58 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.27 | -0.62 to 0.02 | 0.096 | 0.482 |
| jev_head_zero vs always_buy | -0.23 | -0.45 to -0.04 | 0.034 | 0.272 |
| jev_plus_controlled_zero vs always_buy | -0.31 | -0.68 to -0.02 | 0.067 | 0.402 |
| jev_signal_zero vs always_buy | -0.06 | -0.38 to 0.25 | 0.717 | 1.000 |
| logreg vs always_buy | -0.13 | -0.69 to 0.35 | 0.631 | 1.000 |
| ma_cross_rule vs always_buy | -0.08 | -0.48 to 0.31 | 0.696 | 1.000 |
| momentum_rule vs always_buy | -0.16 | -0.62 to 0.28 | 0.460 | 1.000 |
| random_forest vs always_buy | -0.35 | -0.74 to -0.02 | 0.052 | 0.367 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.04 | -0.24 to 0.35 | 0.782 | 0.858 |
| jev_plus_controlled_zero vs gbt | -0.05 | -0.14 to 0.04 | 0.286 | 0.858 |
| jev_signal_zero vs gbt | 0.21 | -0.23 to 0.68 | 0.364 | 0.858 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.05 | -0.14 to 0.04 | 0.286 | 0.286 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.26 | -0.18 to 0.75 | 0.273 | 0.273 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a |
| ma_cross_rule | 88.2% | 6.5% | 0.31 | 0.44 | -48.9% | 0.13 | 27.8 | 100.0% | 1.4% (-11.6% to 14.3%) | 0.52 | 0.35 | 0.26 | 0.03 |
| momentum_rule | -7.5% | -0.8% | -0.03 | -0.04 | -38.9% | -0.02 | 81.3 | 100.0% | -3.4% (-14.0% to 7.7%) | 0.23 | 0.10 | -0.24 | -0.12 |
| gbt | -43.8% | -5.6% | -0.20 | -0.26 | -62.6% | -0.09 | 335.6 | 100.0% | -13.0% (-27.5% to 1.0%) | 0.68 | 0.23 | -0.92 | -1.01 |
| logreg | -54.5% | -7.6% | -0.29 | -0.40 | -63.7% | -0.12 | 252.8 | 100.0% | -13.1% (-26.7% to -1.0%) | 0.51 | 0.03 | -0.83 | -0.60 |
| jev_plus_controlled_zero | -59.8% | -8.7% | -0.32 | -0.48 | -72.6% | -0.12 | 364.6 | 100.0% | -16.5% (-29.9% to -2.7%) | 0.71 | 0.13 | -1.08 | -0.90 |
| jev_head_zero | -68.2% | -10.8% | -0.41 | -0.59 | -83.5% | -0.13 | 442.0 | 100.0% | -18.3% (-31.9% to -5.7%) | 0.67 | 0.13 | -1.31 | -1.21 |
| random_forest | -76.1% | -13.4% | -0.64 | -0.85 | -86.3% | -0.15 | 307.1 | 100.0% | -21.4% (-33.4% to -9.5%) | 0.63 | -0.21 | -1.36 | -1.36 |
| majority | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| stratified_random | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| jev_signal_zero | -88.2% | -19.3% | -0.96 | -1.33 | -89.0% | -0.22 | 456.6 | 100.0% | -26.1% (-38.8% to -13.9%) | 0.44 | -0.33 | -2.03 | -1.39 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.72 | -1.27 to -0.19 | 0.011 | 0.045 |
| jev_head_zero vs always_buy | -0.94 | -1.55 to -0.40 | 0.002 | 0.015 |
| jev_plus_controlled_zero vs always_buy | -0.85 | -1.61 to -0.18 | 0.024 | 0.072 |
| jev_signal_zero vs always_buy | -1.49 | -2.28 to -0.74 | 0.000 | 0.004 |
| logreg vs always_buy | -0.82 | -1.46 to -0.22 | 0.009 | 0.045 |
| ma_cross_rule vs always_buy | -0.21 | -0.85 to 0.35 | 0.486 | 0.486 |
| momentum_rule vs always_buy | -0.55 | -1.31 to 0.17 | 0.142 | 0.285 |
| random_forest vs always_buy | -1.17 | -1.85 to -0.57 | 0.002 | 0.014 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.21 | -0.99 to 0.48 | 0.591 | 1.000 |
| jev_plus_controlled_zero vs gbt | -0.13 | -0.94 to 0.62 | 0.751 | 1.000 |
| jev_signal_zero vs gbt | -0.77 | -1.67 to 0.12 | 0.100 | 0.300 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.13 | -0.94 to 0.62 | 0.751 | 0.751 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.64 | -1.44 to 0.13 | 0.108 | 0.108 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| majority | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| stratified_random | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| jev_head_zero | 8.9% | 0.9% | 0.04 | 0.05 | -45.9% | 0.02 | 91.0 | 99.8% | -8.1% (-15.8% to -0.8%) | 0.72 | 0.20 | -0.23 | -0.28 |
| ma_cross_rule | -9.3% | -1.0% | 0.01 | 0.01 | -51.3% | -0.02 | 20.9 | 99.8% | -6.6% (-18.4% to 6.1%) | 0.55 | 0.04 | -0.03 | -0.04 |
| jev_signal_zero | -12.8% | -1.4% | -0.18 | -0.24 | -36.1% | -0.04 | 93.2 | 99.8% | -7.5% (-13.7% to -1.4%) | 0.43 | 0.05 | -0.55 | -0.84 |
| logreg | -31.1% | -3.7% | -0.18 | -0.24 | -60.5% | -0.06 | 67.6 | 99.8% | -9.8% (-21.4% to 1.2%) | 0.52 | -0.07 | -0.35 | -0.59 |
| random_forest | -43.4% | -5.5% | -0.27 | -0.34 | -61.8% | -0.09 | 70.8 | 99.8% | -14.3% (-25.5% to -3.1%) | 0.73 | -0.16 | -0.45 | -0.86 |
| gbt | -52.9% | -7.3% | -0.28 | -0.37 | -70.1% | -0.10 | 72.3 | 99.8% | -15.4% (-29.8% to -2.7%) | 0.74 | -0.18 | -0.43 | -0.69 |
| jev_plus_controlled_zero | -48.2% | -6.4% | -0.28 | -0.37 | -65.2% | -0.10 | 73.8 | 99.8% | -14.9% (-27.7% to -3.5%) | 0.73 | -0.17 | -0.45 | -0.63 |
| momentum_rule | -37.2% | -4.6% | -0.28 | -0.37 | -45.2% | -0.10 | 37.5 | 99.8% | -8.0% (-16.7% to 0.7%) | 0.26 | -0.21 | -0.39 | -0.26 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.80 | -1.38 to -0.29 | 0.004 | 0.024 |
| jev_head_zero vs always_buy | -0.48 | -0.91 to -0.08 | 0.027 | 0.081 |
| jev_plus_controlled_zero vs always_buy | -0.80 | -1.39 to -0.30 | 0.003 | 0.024 |
| jev_signal_zero vs always_buy | -0.70 | -1.19 to -0.26 | 0.004 | 0.024 |
| logreg vs always_buy | -0.70 | -1.39 to -0.10 | 0.031 | 0.081 |
| ma_cross_rule vs always_buy | -0.51 | -1.14 to 0.01 | 0.084 | 0.084 |
| momentum_rule vs always_buy | -0.80 | -1.52 to -0.13 | 0.019 | 0.078 |
| random_forest vs always_buy | -0.79 | -1.26 to -0.30 | 0.001 | 0.008 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs random_forest | 0.31 | -0.20 to 0.83 | 0.254 | 0.762 |
| jev_plus_controlled_zero vs random_forest | -0.01 | -0.57 to 0.51 | 0.967 | 1.000 |
| jev_signal_zero vs random_forest | 0.09 | -0.64 to 0.74 | 0.792 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.00 | -0.24 to 0.23 | 0.986 | 0.986 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.10 | -0.60 to 0.78 | 0.790 | 0.790 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.5% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.2% | -1.6% | 0.66 | n/a | n/a | n/a |
| jev_signal_zero | 81.7% | 6.2% | 0.44 | 0.61 | -28.7% | 0.22 | 22.7 | 99.2% | -0.2% (-5.8% to 4.7%) | 0.42 | 0.50 | 0.34 | -0.18 |
| majority | 93.2% | 6.8% | 0.44 | 0.59 | -31.5% | 0.22 | 23.3 | 99.2% | -2.4% (-7.7% to 2.6%) | 0.68 | 0.49 | 0.35 | -0.22 |
| stratified_random | 93.2% | 6.8% | 0.44 | 0.59 | -31.5% | 0.22 | 23.3 | 99.2% | -2.4% (-7.7% to 2.6%) | 0.68 | 0.49 | 0.35 | -0.22 |
| random_forest | 41.1% | 3.5% | 0.20 | 0.27 | -32.9% | 0.11 | 19.5 | 99.2% | -3.8% (-10.4% to 2.0%) | 0.54 | 0.24 | 0.13 | -0.15 |
| ma_cross_rule | 24.2% | 2.2% | 0.14 | 0.19 | -40.8% | 0.05 | 9.6 | 99.2% | -4.9% (-15.8% to 7.2%) | 0.68 | 0.15 | 0.12 | -0.22 |
| jev_head_zero | 23.6% | 2.1% | 0.10 | 0.14 | -34.0% | 0.06 | 23.1 | 99.2% | -6.3% (-12.4% to -0.7%) | 0.63 | 0.15 | 0.02 | -0.24 |
| momentum_rule | 17.3% | 1.6% | 0.08 | 0.10 | -38.4% | 0.04 | 14.5 | 99.2% | -3.6% (-11.1% to 4.9%) | 0.39 | 0.10 | 0.03 | 0.09 |
| logreg | 13.2% | 1.3% | 0.06 | 0.08 | -39.2% | 0.03 | 19.4 | 99.2% | -4.2% (-13.6% to 4.5%) | 0.42 | 0.09 | -0.00 | -0.12 |
| jev_plus_controlled_zero | -19.9% | -2.2% | -0.16 | -0.22 | -43.7% | -0.05 | 20.4 | 99.2% | -9.5% (-17.5% to -2.1%) | 0.57 | -0.12 | -0.23 | -0.55 |
| gbt | -21.1% | -2.3% | -0.20 | -0.26 | -44.9% | -0.05 | 19.9 | 99.2% | -9.8% (-16.4% to -3.3%) | 0.56 | -0.16 | -0.26 | -0.46 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.72 | -1.28 to -0.22 | 0.011 | 0.080 |
| jev_head_zero vs always_buy | -0.42 | -0.87 to -0.08 | 0.038 | 0.231 |
| jev_plus_controlled_zero vs always_buy | -0.68 | -1.23 to -0.25 | 0.009 | 0.076 |
| jev_signal_zero vs always_buy | -0.08 | -0.61 to 0.41 | 0.745 | 0.745 |
| logreg vs always_buy | -0.46 | -1.15 to 0.16 | 0.190 | 0.732 |
| ma_cross_rule vs always_buy | -0.38 | -0.96 to 0.13 | 0.161 | 0.732 |
| momentum_rule vs always_buy | -0.45 | -1.11 to 0.13 | 0.146 | 0.732 |
| random_forest vs always_buy | -0.32 | -0.84 to 0.13 | 0.195 | 0.732 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.30 | -0.17 to 0.80 | 0.241 | 0.482 |
| jev_plus_controlled_zero vs gbt | 0.03 | -0.21 to 0.29 | 0.799 | 0.799 |
| jev_signal_zero vs gbt | 0.64 | 0.02 to 1.28 | 0.050 | 0.150 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.03 | -0.21 to 0.29 | 0.799 | 0.799 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.60 | -0.06 to 1.28 | 0.080 | 0.080 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 46.0% | 3.9% | 0.48 | 0.65 | -8.8% | 0.44 | 11.4 | 42.4% | 0.5% (-2.0% to 2.9%) | 0.15 | 0.55 | 0.36 | -0.10 | 0.48 | 0.0% |
| logreg | 29.8% | 2.6% | 0.17 | 0.23 | -14.3% | 0.18 | 26.7 | 33.3% | -2.2% (-5.1% to 0.7%) | 0.28 | 0.28 | -0.01 | -0.55 | 0.32 | -1.1% |
| ma_cross_rule | 26.0% | 2.3% | 0.17 | 0.23 | -8.2% | 0.28 | 18.4 | 40.6% | -0.9% (-3.7% to 1.5%) | 0.14 | 0.29 | -0.03 | -0.28 | 0.36 | -0.8% |
| random_forest | 17.4% | 1.6% | 0.03 | 0.04 | -13.9% | 0.12 | 39.4 | 34.7% | -3.4% (-6.0% to -0.8%) | 0.30 | 0.19 | -0.24 | -0.79 | 0.40 | -2.5% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| gbt | 8.0% | 0.8% | -0.09 | -0.11 | -27.2% | 0.03 | 55.8 | 29.1% | -3.9% (-8.0% to 0.0%) | 0.27 | 0.15 | -0.48 | -1.20 | 0.26 | -2.3% |
| jev_plus_controlled_zero | -0.8% | -0.1% | -0.20 | -0.26 | -27.1% | -0.00 | 56.7 | 28.5% | -4.8% (-8.9% to -1.0%) | 0.27 | 0.03 | -0.60 | -1.32 | 0.21 | -2.9% |
| jev_head_zero | -14.2% | -1.5% | -0.57 | -0.71 | -23.1% | -0.07 | 90.3 | 29.9% | -5.8% (-8.2% to -3.5%) | 0.23 | -0.06 | -1.41 | -1.90 | 0.18 | -3.9% |
| jev_signal_zero | -5.3% | -0.5% | -0.72 | -0.87 | -14.1% | -0.04 | 35.8 | 8.5% | -3.0% (-5.0% to -1.1%) | 0.07 | -0.36 | -1.32 | -0.68 | -0.06 | -2.0% |
| stratified_random | -23.6% | -2.7% | -0.93 | -1.20 | -32.2% | -0.08 | 104.9 | 29.7% | -6.7% (-8.9% to -4.7%) | 0.20 | -0.24 | -2.09 | -2.64 | 0.39 | -5.8% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.61 | -1.08 to -0.14 | 0.011 | 0.057 |
| jev_head_zero vs always_buy | -1.09 | -1.45 to -0.75 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.73 | -1.22 to -0.28 | 0.002 | 0.015 |
| jev_signal_zero vs always_buy | -1.24 | -1.87 to -0.70 | 0.000 | 0.004 |
| logreg vs always_buy | -0.36 | -0.86 to 0.11 | 0.163 | 0.490 |
| ma_cross_rule vs always_buy | -0.36 | -0.94 to 0.23 | 0.245 | 0.490 |
| momentum_rule vs always_buy | -0.05 | -0.61 to 0.49 | 0.849 | 0.849 |
| random_forest vs always_buy | -0.49 | -0.95 to -0.10 | 0.028 | 0.114 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.48 | -0.98 to -0.02 | 0.054 | 0.162 |
| jev_plus_controlled_zero vs gbt | -0.12 | -0.37 to 0.11 | 0.350 | 0.350 |
| jev_signal_zero vs gbt | -0.63 | -1.38 to -0.02 | 0.073 | 0.162 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.12 | -0.37 to 0.11 | 0.350 | 0.350 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.52 | -1.26 to 0.08 | 0.132 | 0.132 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 49.0% | 4.1% | 0.51 | 0.69 | -6.9% | 0.59 | 5.2 | 43.5% | 0.6% (-1.7% to 2.9%) | 0.16 | 0.55 | 0.46 | -0.06 | 0.49 | 0.1% |
| jev_head_zero | 30.7% | 2.7% | 0.25 | 0.35 | -9.8% | 0.28 | 19.7 | 31.7% | -1.6% (-2.9% to -0.2%) | 0.22 | 0.38 | 0.03 | -0.53 | 0.57 | -1.2% |
| ma_cross_rule | 29.3% | 2.6% | 0.24 | 0.32 | -7.3% | 0.36 | 8.6 | 40.1% | -0.6% (-2.9% to 1.5%) | 0.13 | 0.30 | 0.14 | -0.22 | 0.35 | -0.4% |
| stratified_random | 27.1% | 2.4% | 0.20 | 0.26 | -11.5% | 0.21 | 21.8 | 32.0% | -1.9% (-3.5% to -0.4%) | 0.22 | 0.35 | -0.06 | -0.84 | 0.42 | -1.0% |
| jev_signal_zero | 25.0% | 2.3% | 0.18 | 0.24 | -7.1% | 0.32 | 20.1 | 29.0% | -1.3% (-2.8% to 0.3%) | 0.16 | 0.34 | -0.09 | -0.44 | 0.57 | -1.4% |
| random_forest | 23.7% | 2.2% | 0.10 | 0.13 | -23.1% | 0.09 | 10.9 | 34.7% | -3.6% (-7.5% to -0.2%) | 0.36 | 0.14 | 0.03 | -0.42 | 0.25 | -1.2% |
| gbt | 21.0% | 1.9% | 0.07 | 0.10 | -21.9% | 0.09 | 13.7 | 36.8% | -3.7% (-7.0% to -0.6%) | 0.35 | 0.13 | -0.01 | -0.43 | 0.29 | -1.5% |
| jev_plus_controlled_zero | 17.7% | 1.6% | 0.04 | 0.05 | -23.0% | 0.07 | 14.0 | 36.5% | -4.0% (-7.4% to -0.9%) | 0.35 | 0.09 | -0.05 | -0.45 | 0.21 | -1.2% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| logreg | 7.9% | 0.8% | -0.07 | -0.09 | -22.2% | 0.03 | 7.9 | 31.5% | -4.5% (-8.2% to -0.8%) | 0.32 | -0.04 | -0.12 | -0.57 | 0.03 | -0.8% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.45 | -0.79 to -0.09 | 0.012 | 0.075 |
| jev_head_zero vs always_buy | -0.27 | -0.57 to -0.01 | 0.063 | 0.224 |
| jev_plus_controlled_zero vs always_buy | -0.48 | -0.80 to -0.15 | 0.005 | 0.040 |
| jev_signal_zero vs always_buy | -0.34 | -0.72 to -0.01 | 0.056 | 0.224 |
| logreg vs always_buy | -0.59 | -1.02 to -0.16 | 0.007 | 0.049 |
| ma_cross_rule vs always_buy | -0.28 | -0.82 to 0.19 | 0.282 | 0.564 |
| momentum_rule vs always_buy | -0.01 | -0.53 to 0.48 | 0.974 | 0.974 |
| random_forest vs always_buy | -0.42 | -0.79 to -0.03 | 0.032 | 0.160 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs random_forest | 0.15 | -0.25 to 0.47 | 0.431 | 1.000 |
| jev_plus_controlled_zero vs random_forest | -0.06 | -0.25 to 0.11 | 0.479 | 1.000 |
| jev_signal_zero vs random_forest | 0.08 | -0.53 to 0.62 | 0.801 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.04 | -0.15 to 0.08 | 0.509 | 0.509 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.14 | -0.44 to 0.64 | 0.616 | 0.616 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.5% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.2% | -1.6% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| jev_signal_zero | 42.2% | 3.6% | 0.51 | 0.69 | -7.1% | 0.51 | 5.4 | 32.1% | -0.2% (-1.6% to 1.2%) | 0.18 | 0.55 | 0.44 | -0.00 | 0.52 | -0.1% |
| momentum_rule | 46.0% | 3.9% | 0.44 | 0.58 | -10.8% | 0.36 | 2.5 | 43.4% | -0.1% (-2.5% to 2.5%) | 0.20 | 0.46 | 0.42 | 0.08 | 0.32 | 0.6% |
| stratified_random | 38.6% | 3.3% | 0.38 | 0.51 | -11.7% | 0.28 | 5.7 | 35.1% | -1.2% (-2.7% to 0.2%) | 0.24 | 0.42 | 0.32 | -0.21 | 0.41 | -0.2% |
| jev_head_zero | 37.3% | 3.2% | 0.36 | 0.49 | -10.8% | 0.30 | 5.3 | 32.7% | -1.2% (-2.5% to 0.1%) | 0.23 | 0.40 | 0.31 | 0.10 | 0.51 | -0.7% |
| random_forest | 45.7% | 3.8% | 0.35 | 0.48 | -12.7% | 0.30 | 4.3 | 40.9% | -1.2% (-3.2% to 0.9%) | 0.29 | 0.37 | 0.32 | 0.09 | 0.47 | -0.9% |
| ma_cross_rule | 33.1% | 2.9% | 0.23 | 0.28 | -21.8% | 0.13 | 3.1 | 45.8% | -1.7% (-5.6% to 1.8%) | 0.25 | 0.24 | 0.20 | -0.05 | 0.25 | -0.2% |
| gbt | 34.1% | 3.0% | 0.23 | 0.30 | -16.0% | 0.19 | 4.4 | 39.9% | -2.2% (-4.3% to 0.1%) | 0.30 | 0.25 | 0.19 | -0.16 | 0.32 | -0.6% |
| jev_plus_controlled_zero | 31.7% | 2.8% | 0.20 | 0.27 | -15.4% | 0.18 | 4.5 | 38.2% | -2.3% (-4.4% to -0.1%) | 0.30 | 0.22 | 0.17 | -0.16 | 0.33 | -0.9% |
| logreg | 28.8% | 2.6% | 0.17 | 0.23 | -14.3% | 0.18 | 3.2 | 33.0% | -2.1% (-4.4% to 0.2%) | 0.26 | 0.18 | 0.14 | -0.31 | 0.23 | -0.5% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.30 | -0.71 to 0.02 | 0.095 | 0.684 |
| jev_head_zero vs always_buy | -0.16 | -0.40 to 0.06 | 0.182 | 0.861 |
| jev_plus_controlled_zero vs always_buy | -0.32 | -0.76 to 0.00 | 0.085 | 0.684 |
| jev_signal_zero vs always_buy | -0.02 | -0.35 to 0.27 | 0.916 | 1.000 |
| logreg vs always_buy | -0.35 | -0.88 to 0.06 | 0.143 | 0.861 |
| ma_cross_rule vs always_buy | -0.29 | -0.63 to 0.14 | 0.144 | 0.861 |
| momentum_rule vs always_buy | -0.08 | -0.47 to 0.30 | 0.690 | 1.000 |
| random_forest vs always_buy | -0.18 | -0.63 to 0.19 | 0.390 | 1.000 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.14 | -0.11 to 0.46 | 0.338 | 0.732 |
| jev_plus_controlled_zero vs gbt | -0.03 | -0.11 to 0.04 | 0.504 | 0.732 |
| jev_signal_zero vs gbt | 0.28 | -0.21 to 0.78 | 0.244 | 0.732 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.03 | -0.11 to 0.04 | 0.504 | 0.504 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.31 | -0.19 to 0.81 | 0.199 | 0.199 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.31 (median of 8 comparisons). A true difference smaller than about 0.44 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

37,710 test observations on 2,514 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.360 | 0.360 | 0.376 | 1.113 | 0.674 | 0.041 | 0.500 | 26/40/33 | 0.0% |
| random_forest | 0.351 | 0.356 | 0.386 | 1.091 | 0.661 | 0.011 | 0.504 | 18/48/35 | 0.0% |
| jev_head_zero | 0.349 | 0.349 | 0.366 | 1.115 | 0.677 | 0.056 | 0.500 | 28/43/30 | 0.0% |
| gbt | 0.348 | 0.349 | 0.373 | 1.162 | 0.701 | 0.126 | 0.500 | 24/47/29 | 0.0% |
| jev_plus_controlled_zero | 0.348 | 0.348 | 0.374 | 1.140 | 0.688 | 0.098 | 0.496 | 25/47/28 | 0.0% |
| momentum_rule | 0.340 | 0.345 | 0.355 | n/a | n/a | n/a | 0.520 | 20/37/42 | 0.0% |
| stratified_random | 0.335 | 0.335 | 0.352 | 1.075 | 0.650 | 0.003 | 0.505 | 26/44/30 | 0.0% |
| ma_cross_rule | 0.328 | 0.330 | 0.343 | n/a | n/a | n/a | 0.514 | 20/40/41 | 0.0% |
| jev_signal_zero | 0.290 | 0.341 | 0.419 | 1.513 | 0.807 | 0.257 | 0.505 | 9/82/8 | 0.0% |
| majority | 0.204 | 0.333 | 0.440 | 1.075 | 0.650 | 0.003 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 26.1%, HOLD 44.0%, BUY 29.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.253 | 0.467 | 0.325 | 0.236 | 0.494 | 0.316 | 0.078% | 0.006% | 0.036% |
| jev_head_zero | 0.272 | 0.468 | 0.308 | 0.287 | 0.453 | 0.308 | 0.039% | 0.033% | 0.026% |
| jev_plus_controlled_zero | 0.258 | 0.468 | 0.319 | 0.242 | 0.500 | 0.304 | 0.072% | 0.015% | 0.026% |
| jev_signal_zero | 0.300 | 0.446 | 0.295 | 0.108 | 0.833 | 0.083 | -0.017% | 0.042% | -0.011% |
| logreg | 0.263 | 0.493 | 0.326 | 0.266 | 0.452 | 0.363 | 0.036% | 0.026% | 0.037% |
| ma_cross_rule | 0.290 | 0.430 | 0.282 | 0.219 | 0.388 | 0.383 | 0.043% | 0.036% | 0.023% |
| majority | 0.000 | 0.440 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.032% | n/a |
| momentum_rule | 0.286 | 0.454 | 0.301 | 0.223 | 0.384 | 0.427 | 0.044% | 0.025% | 0.033% |
| random_forest | 0.261 | 0.480 | 0.321 | 0.175 | 0.520 | 0.373 | 0.060% | 0.023% | 0.031% |
| stratified_random | 0.267 | 0.440 | 0.297 | 0.269 | 0.440 | 0.295 | 0.032% | 0.041% | 0.020% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0136 | 0.0043 to 0.0222 | 0.002 | 0.008 |
| jev_head_zero vs stratified_random | 0.0147 | 0.0083 to 0.0211 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs stratified_random | 0.0133 | 0.0040 to 0.0232 | 0.005 | 0.015 |
| jev_signal_zero vs stratified_random | -0.0448 | -0.0534 to -0.0363 | 0.000 | 0.004 |
| logreg vs stratified_random | 0.0251 | 0.0146 to 0.0352 | 0.000 | 0.004 |
| ma_cross_rule vs stratified_random | -0.0069 | -0.0163 to 0.0017 | 0.141 | 0.282 |
| momentum_rule vs stratified_random | 0.0054 | -0.0046 to 0.0148 | 0.292 | 0.292 |
| random_forest vs stratified_random | 0.0167 | 0.0074 to 0.0258 | 0.001 | 0.007 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.0010 | -0.0065 to 0.0092 | 0.806 | 1.000 |
| jev_plus_controlled_zero vs gbt | -0.0003 | -0.0049 to 0.0046 | 0.919 | 1.000 |
| jev_signal_zero vs gbt | -0.0584 | -0.0675 to -0.0482 | 0.000 | 0.001 |

### 5-day horizon (primary)

37,650 test observations on 2,510 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| jev_head_zero | 0.348 | 0.348 | 0.361 | 1.130 | 0.685 | 0.076 | 0.502 | 28/41/32 | 0.0% |
| logreg | 0.343 | 0.344 | 0.366 | 1.200 | 0.715 | 0.122 | 0.484 | 24/45/32 | 0.0% |
| momentum_rule | 0.343 | 0.346 | 0.359 | n/a | n/a | n/a | 0.529 | 20/36/44 | 0.0% |
| jev_plus_controlled_zero | 0.342 | 0.343 | 0.352 | 1.291 | 0.763 | 0.209 | 0.499 | 28/35/37 | 0.0% |
| random_forest | 0.341 | 0.341 | 0.354 | 1.118 | 0.679 | 0.079 | 0.493 | 27/38/35 | 0.0% |
| gbt | 0.338 | 0.339 | 0.349 | 1.263 | 0.755 | 0.199 | 0.495 | 28/35/37 | 0.0% |
| stratified_random | 0.336 | 0.336 | 0.350 | 1.084 | 0.657 | 0.024 | 0.511 | 25/43/32 | 0.0% |
| ma_cross_rule | 0.333 | 0.334 | 0.350 | n/a | n/a | n/a | 0.517 | 20/40/40 | 0.0% |
| jev_signal_zero | 0.331 | 0.333 | 0.355 | 1.375 | 0.786 | 0.246 | 0.507 | 22/49/29 | 0.0% |
| majority | 0.197 | 0.333 | 0.419 | 1.084 | 0.657 | 0.024 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.4%, HOLD 41.9%, BUY 32.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.235 | 0.447 | 0.341 | 0.259 | 0.376 | 0.384 | 0.264% | 0.142% | 0.099% |
| jev_head_zero | 0.259 | 0.447 | 0.338 | 0.280 | 0.435 | 0.328 | 0.169% | 0.150% | 0.166% |
| jev_plus_controlled_zero | 0.241 | 0.449 | 0.342 | 0.267 | 0.380 | 0.382 | 0.254% | 0.164% | 0.086% |
| jev_signal_zero | 0.269 | 0.417 | 0.313 | 0.228 | 0.493 | 0.277 | 0.185% | 0.159% | 0.144% |
| logreg | 0.232 | 0.454 | 0.342 | 0.217 | 0.485 | 0.331 | 0.326% | 0.173% | 0.018% |
| ma_cross_rule | 0.280 | 0.421 | 0.312 | 0.217 | 0.404 | 0.382 | 0.275% | 0.160% | 0.105% |
| majority | 0.000 | 0.419 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.160% | n/a |
| momentum_rule | 0.274 | 0.438 | 0.332 | 0.218 | 0.379 | 0.441 | 0.257% | 0.110% | 0.157% |
| random_forest | 0.234 | 0.449 | 0.344 | 0.248 | 0.410 | 0.365 | 0.304% | 0.106% | 0.109% |
| stratified_random | 0.256 | 0.420 | 0.331 | 0.256 | 0.427 | 0.324 | 0.171% | 0.159% | 0.154% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0028 | -0.0111 to 0.0156 | 0.677 | 1.000 |
| jev_head_zero vs stratified_random | 0.0121 | 0.0028 to 0.0213 | 0.015 | 0.124 |
| jev_plus_controlled_zero vs stratified_random | 0.0061 | -0.0072 to 0.0189 | 0.351 | 1.000 |
| jev_signal_zero vs stratified_random | -0.0048 | -0.0140 to 0.0046 | 0.314 | 1.000 |
| logreg vs stratified_random | 0.0076 | -0.0066 to 0.0215 | 0.301 | 1.000 |
| ma_cross_rule vs stratified_random | -0.0022 | -0.0151 to 0.0101 | 0.734 | 1.000 |
| momentum_rule vs stratified_random | 0.0071 | -0.0064 to 0.0200 | 0.288 | 1.000 |
| random_forest vs stratified_random | 0.0056 | -0.0080 to 0.0184 | 0.410 | 1.000 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs random_forest | 0.0065 | -0.0053 to 0.0183 | 0.278 | 0.556 |
| jev_plus_controlled_zero vs random_forest | 0.0006 | -0.0072 to 0.0090 | 0.887 | 0.887 |
| jev_signal_zero vs random_forest | -0.0103 | -0.0250 to 0.0042 | 0.176 | 0.528 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,472 | 3,249 | 3,838 | 0 |
| HOLD | 4,524 | 5,921 | 5,320 | 0 |
| BUY | 3,523 | 4,072 | 4,731 | 0 |

`jev_head_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,681 | 3,740 | 3,138 | 0 |
| HOLD | 4,130 | 6,854 | 4,781 | 0 |
| BUY | 3,545 | 4,734 | 4,047 | 0 |

`jev_plus_controlled_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,548 | 3,217 | 3,794 | 0 |
| HOLD | 4,508 | 5,986 | 5,271 | 0 |
| BUY | 3,498 | 4,122 | 4,706 | 0 |

`jev_signal_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,180 | 4,739 | 2,640 | 0 |
| HOLD | 3,120 | 7,767 | 4,878 | 0 |
| BUY | 2,801 | 6,105 | 3,420 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,073 | 3,986 | 3,500 | 0 |
| HOLD | 3,794 | 7,645 | 4,326 | 0 |
| BUY | 3,053 | 5,198 | 4,075 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,072 | 3,763 | 3,724 | 0 |
| HOLD | 2,710 | 6,374 | 6,681 | 0 |
| BUY | 2,624 | 4,989 | 4,713 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 9,559 | 0 | 0 |
| HOLD | 0 | 15,765 | 0 | 0 |
| BUY | 0 | 12,326 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,088 | 3,456 | 4,015 | 0 |
| HOLD | 2,843 | 5,974 | 6,948 | 0 |
| BUY | 2,688 | 4,197 | 5,441 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,375 | 3,569 | 3,615 | 0 |
| HOLD | 4,332 | 6,461 | 4,972 | 0 |
| BUY | 3,464 | 4,357 | 4,505 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,448 | 4,048 | 3,063 | 0 |
| HOLD | 4,030 | 6,731 | 5,004 | 0 |
| BUY | 3,099 | 5,232 | 3,995 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.299 | 0.353 | 0.333 | 0.343 | 0.349 | 0.387 | 0.201 | 0.279 | 0.320 | 0.329 |
| jev_head_zero | 0.321 | 0.354 | 0.342 | 0.337 | 0.341 | 0.391 | 0.347 | 0.330 | 0.338 | 0.347 |
| jev_plus_controlled_zero | 0.297 | 0.362 | 0.346 | 0.345 | 0.366 | 0.389 | 0.208 | 0.271 | 0.322 | 0.336 |
| jev_signal_zero | 0.352 | 0.334 | 0.334 | 0.302 | 0.313 | 0.366 | 0.330 | 0.328 | 0.327 | 0.306 |
| logreg | 0.266 | 0.323 | 0.300 | 0.316 | 0.351 | 0.338 | 0.161 | 0.249 | 0.231 | 0.353 |
| ma_cross_rule | 0.334 | 0.311 | 0.341 | 0.332 | 0.315 | 0.359 | 0.315 | 0.325 | 0.319 | 0.294 |
| majority | 0.191 | 0.207 | 0.201 | 0.185 | 0.193 | 0.216 | 0.207 | 0.181 | 0.198 | 0.185 |
| momentum_rule | 0.337 | 0.350 | 0.302 | 0.340 | 0.315 | 0.384 | 0.292 | 0.333 | 0.313 | 0.299 |
| random_forest | 0.278 | 0.350 | 0.347 | 0.321 | 0.335 | 0.385 | 0.167 | 0.293 | 0.326 | 0.350 |
| stratified_random | 0.349 | 0.337 | 0.336 | 0.332 | 0.331 | 0.347 | 0.333 | 0.322 | 0.339 | 0.324 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.315 | 0.331 | 0.342 |
| jev_head_zero | 0.355 | 0.355 | 0.339 |
| jev_plus_controlled_zero | 0.323 | 0.332 | 0.348 |
| jev_signal_zero | 0.347 | 0.332 | 0.323 |
| logreg | 0.317 | 0.337 | 0.337 |
| ma_cross_rule | 0.339 | 0.333 | 0.320 |
| majority | 0.191 | 0.200 | 0.196 |
| momentum_rule | 0.343 | 0.344 | 0.327 |
| random_forest | 0.312 | 0.340 | 0.339 |
| stratified_random | 0.318 | 0.343 | 0.337 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.309 | 0.341 | 0.355 | 15 |
| jev_head_zero | 0.328 | 0.347 | 0.365 | 15 |
| jev_plus_controlled_zero | 0.314 | 0.343 | 0.362 | 15 |
| jev_signal_zero | 0.300 | 0.326 | 0.341 | 15 |
| logreg | 0.318 | 0.342 | 0.362 | 15 |
| ma_cross_rule | 0.302 | 0.327 | 0.357 | 15 |
| majority | 0.190 | 0.196 | 0.204 | 15 |
| momentum_rule | 0.316 | 0.340 | 0.356 | 15 |
| random_forest | 0.313 | 0.342 | 0.361 | 15 |
| stratified_random | 0.322 | 0.333 | 0.353 | 15 |

### 20-day horizon

37,425 test observations on 2,495 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 0.352 | 0.355 | 0.374 | n/a | n/a | n/a | 0.544 | 18/38/44 | 0.0% |
| gbt | 0.338 | 0.339 | 0.352 | 1.464 | 0.833 | 0.288 | 0.512 | 25/35/40 | 0.0% |
| jev_plus_controlled_zero | 0.336 | 0.336 | 0.349 | 1.402 | 0.811 | 0.266 | 0.509 | 24/37/39 | 0.0% |
| ma_cross_rule | 0.335 | 0.339 | 0.351 | n/a | n/a | n/a | 0.538 | 22/32/46 | 0.0% |
| random_forest | 0.334 | 0.337 | 0.360 | 1.133 | 0.688 | 0.090 | 0.523 | 19/40/41 | 0.0% |
| jev_head_zero | 0.332 | 0.334 | 0.352 | 1.170 | 0.707 | 0.125 | 0.511 | 22/46/33 | 0.0% |
| jev_signal_zero | 0.332 | 0.333 | 0.341 | 1.382 | 0.802 | 0.261 | 0.518 | 27/41/32 | 0.0% |
| stratified_random | 0.328 | 0.328 | 0.341 | 1.094 | 0.663 | 0.037 | 0.509 | 25/40/35 | 0.0% |
| logreg | 0.324 | 0.326 | 0.347 | 1.240 | 0.729 | 0.156 | 0.481 | 22/45/33 | 0.0% |
| majority | 0.189 | 0.333 | 0.396 | 1.094 | 0.663 | 0.037 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 24.6%, HOLD 39.6%, BUY 35.8%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.233 | 0.419 | 0.366 | 0.235 | 0.371 | 0.411 | 1.044% | 0.558% | 0.470% |
| jev_head_zero | 0.243 | 0.402 | 0.355 | 0.213 | 0.462 | 0.327 | 0.533% | 0.742% | 0.579% |
| jev_plus_controlled_zero | 0.234 | 0.412 | 0.362 | 0.232 | 0.385 | 0.390 | 0.948% | 0.645% | 0.448% |
| jev_signal_zero | 0.259 | 0.387 | 0.351 | 0.280 | 0.401 | 0.318 | 0.642% | 0.625% | 0.668% |
| logreg | 0.211 | 0.410 | 0.351 | 0.185 | 0.468 | 0.326 | 1.261% | 0.532% | 0.395% |
| ma_cross_rule | 0.248 | 0.403 | 0.365 | 0.224 | 0.321 | 0.471 | 0.924% | 0.798% | 0.403% |
| majority | 0.000 | 0.396 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.643% | n/a |
| momentum_rule | 0.263 | 0.431 | 0.372 | 0.198 | 0.411 | 0.455 | 0.810% | 0.648% | 0.568% |
| random_forest | 0.220 | 0.415 | 0.369 | 0.166 | 0.422 | 0.424 | 0.730% | 0.649% | 0.599% |
| stratified_random | 0.236 | 0.393 | 0.355 | 0.237 | 0.397 | 0.351 | 0.751% | 0.626% | 0.588% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0102 | -0.0090 to 0.0270 | 0.278 | 1.000 |
| jev_head_zero vs stratified_random | 0.0043 | -0.0061 to 0.0150 | 0.415 | 1.000 |
| jev_plus_controlled_zero vs stratified_random | 0.0074 | -0.0112 to 0.0233 | 0.397 | 1.000 |
| jev_signal_zero vs stratified_random | 0.0041 | -0.0105 to 0.0189 | 0.588 | 1.000 |
| logreg vs stratified_random | -0.0042 | -0.0249 to 0.0155 | 0.691 | 1.000 |
| ma_cross_rule vs stratified_random | 0.0065 | -0.0175 to 0.0286 | 0.587 | 1.000 |
| momentum_rule vs stratified_random | 0.0239 | -0.0001 to 0.0462 | 0.041 | 0.332 |
| random_forest vs stratified_random | 0.0059 | -0.0137 to 0.0235 | 0.530 | 1.000 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.0059 | -0.0242 to 0.0165 | 0.577 | 1.000 |
| jev_plus_controlled_zero vs gbt | -0.0028 | -0.0085 to 0.0034 | 0.360 | 1.000 |
| jev_signal_zero vs gbt | -0.0062 | -0.0296 to 0.0197 | 0.628 | 1.000 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 30 | 8 | 161.5 | 0.9 | 112,785 |
| jev_head_zero | 30 | 8 | 108.9 | 1.0 | 112,785 |
| jev_plus_controlled_zero | 30 | 8 | 205.9 | 1.1 | 112,785 |
| jev_signal_zero | 30 | 1 | 0.1 | 0.0 | 112,785 |
| logreg | 30 | 8 | 11.3 | 0.1 | 112,785 |
| ma_cross_rule | 30 | 6 | 0.4 | 0.0 | 112,785 |
| majority | 30 | 1 | 0.1 | 0.0 | 112,785 |
| momentum_rule | 30 | 8 | 0.5 | 0.0 | 112,785 |
| random_forest | 30 | 8 | 123.4 | 2.0 | 112,785 |
| stratified_random | 30 | 1 | 0.1 | 0.0 | 112,785 |

Traditional models run locally at no marginal cost. External classifier status: jev/zero: available: 100.0% of rows annotated; jev/examples: not run: no saved outputs; openai/zero: not run: no saved outputs; openai/examples: not run: no saved outputs; local/zero: not run: no saved outputs; local/examples: not run: no saved outputs.

Models that did not run:

- `jev_head_examples` (GBT on Jev (TypeSafe jev-1.13.0) outputs, with training examples): not run: no saved outputs
- `jev_plus_controlled_examples` (GBT on controlled features + Jev (TypeSafe jev-1.13.0) outputs, with training examples): not run: no saved outputs
- `jev_signal_examples` (Jev (TypeSafe jev-1.13.0) as signal, with training examples): not run: no saved outputs

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

**Jev (TypeSafe jev-1.13.0)**, 5-day horizon, net Sharpe ratio of the ranking portfolio. A difference counts as better only if it is at least +0.20, its interval excludes zero and Holm-adjusted p < 0.05.

- **Used alone, against the traditional classifier `random_forest`:**
  - `jev_signal_zero` vs `random_forest`: +0.14 (95% interval -0.34 to +0.60, Holm p 1.000), **no reliable difference**
- **Used alone, against equal-weight buy and hold:**
  - `jev_signal_zero` vs `always_buy`: -0.41 (95% interval -0.72 to -0.14, Holm p 0.032), **worse**
- **Added to a traditional classifier (GBT with its outputs against GBT without):**
  - `jev_plus_controlled_zero` vs `gbt`: +0.00 (95% interval -0.13 to +0.14, Holm p 0.978), **no reliable difference**
- **Used alone against used as an added input:**
  - `jev_signal_zero` vs `jev_plus_controlled_zero`: +0.13 (95% interval -0.33 to +0.56, Holm p 0.566), **no reliable difference**
- **Classification (diagnostic, macro-F1, margin +0.02):**
  - `jev_head_zero` vs `random_forest`: +0.01 (95% interval -0.01 to +0.02, Holm p 0.556), **no reliable difference**
  - `jev_plus_controlled_zero` vs `random_forest`: +0.00 (95% interval -0.01 to +0.01, Holm p 0.887), **no reliable difference**
  - `jev_signal_zero` vs `random_forest`: -0.01 (95% interval -0.02 to +0.00, Holm p 0.528), **no reliable difference**
- **Overall:** the thesis is not supported. No arm used alone reliably beats both the traditional classifier and buy and hold. Check the detectable-effect section before reading this as evidence of no difference.

- **Operational efficiency:** see the runtime and cost table; reported, not tested.
