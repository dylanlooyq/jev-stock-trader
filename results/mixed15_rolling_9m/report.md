# Experiment report: mixed15_rolling_9m

Generated 2026-10-12T05:01:11+00:00 from commit `115d3d1-dirty`, config `05a4cdb862c7`, dataset `0b91d318b8c2`. Final two years of folds included: **False**.

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

- Walk-forward folds of 9 months, rolling 9-month training window (exploratory variant), 3-month validation tail used for all tuning.
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

**1-day horizon**, 2015-01-02 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 112.7% | 8.1% | 0.55 | 0.75 | -28.4% | 0.28 | 0.1 | 100.0% | -1.1% | 0.67 | n/a | n/a | n/a |
| momentum_rule | 94.4% | 7.1% | 0.45 | 0.63 | -16.4% | 0.43 | 58.6 | 100.0% | 0.4% (-6.5% to 6.6%) | 0.47 | 0.58 | 0.23 | -0.54 |
| ma_cross_rule | 95.9% | 7.2% | 0.42 | 0.58 | -18.2% | 0.39 | 16.1 | 100.0% | -0.5% (-7.8% to 6.0%) | 0.57 | 0.45 | 0.37 | -0.07 |
| random_forest | -9.1% | -1.0% | -0.11 | -0.15 | -38.3% | -0.03 | 187.6 | 100.0% | -8.8% (-15.3% to -2.6%) | 0.60 | 0.28 | -0.77 | -0.84 |
| logreg | -11.9% | -1.3% | -0.13 | -0.17 | -29.9% | -0.04 | 143.1 | 100.0% | -8.7% (-15.3% to -1.9%) | 0.57 | 0.16 | -0.61 | -0.69 |
| gbt | -14.8% | -1.6% | -0.14 | -0.18 | -48.1% | -0.03 | 228.6 | 100.0% | -10.3% (-17.5% to -3.6%) | 0.68 | 0.31 | -0.88 | -1.52 |
| jev_plus_controlled_zero | -41.2% | -5.3% | -0.37 | -0.49 | -54.9% | -0.10 | 255.0 | 100.0% | -14.2% (-21.7% to -7.1%) | 0.69 | 0.11 | -1.18 | -1.66 |
| jev_head_zero | -52.5% | -7.4% | -0.55 | -0.75 | -57.8% | -0.13 | 336.7 | 100.0% | -16.1% (-22.2% to -10.2%) | 0.66 | 0.13 | -1.68 | -1.82 |
| majority | -63.1% | -9.7% | -0.75 | -0.97 | -67.6% | -0.14 | 368.1 | 100.0% | -18.8% (-25.3% to -12.3%) | 0.66 | 0.01 | -2.02 | -2.76 |
| stratified_random | -63.1% | -9.7% | -0.75 | -0.97 | -67.6% | -0.14 | 368.1 | 100.0% | -18.8% (-25.3% to -12.3%) | 0.66 | 0.01 | -2.02 | -2.76 |
| jev_signal_zero | -70.2% | -11.7% | -0.93 | -1.26 | -72.7% | -0.16 | 345.7 | 100.0% | -19.4% (-26.2% to -12.8%) | 0.52 | -0.20 | -2.16 | -2.08 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.69 | -1.05 to -0.36 | 0.000 | 0.004 |
| jev_head_zero vs always_buy | -1.10 | -1.57 to -0.73 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.92 | -1.33 to -0.56 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -1.48 | -2.06 to -0.97 | 0.000 | 0.004 |
| logreg vs always_buy | -0.68 | -1.28 to -0.16 | 0.015 | 0.046 |
| ma_cross_rule vs always_buy | -0.13 | -0.61 to 0.30 | 0.584 | 1.000 |
| momentum_rule vs always_buy | -0.10 | -0.65 to 0.38 | 0.711 | 1.000 |
| random_forest vs always_buy | -0.67 | -1.10 to -0.27 | 0.003 | 0.014 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.43 | -0.94 to 0.11 | 0.114 | 0.229 |
| jev_plus_controlled_zero vs logreg | -0.25 | -0.74 to 0.31 | 0.343 | 0.343 |
| jev_signal_zero vs logreg | -0.81 | -1.37 to -0.25 | 0.005 | 0.015 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.23 | -0.55 to 0.07 | 0.151 | 0.151 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.56 | -1.16 to -0.01 | 0.061 | 0.061 |

**5-day horizon (primary)**, 2015-01-02 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| momentum_rule | 131.1% | 9.0% | 0.59 | 0.83 | -15.3% | 0.59 | 20.9 | 99.8% | 2.0% (-4.5% to 7.9%) | 0.48 | 0.64 | 0.51 | -0.10 |
| ma_cross_rule | 145.4% | 9.7% | 0.59 | 0.82 | -21.2% | 0.46 | 13.1 | 99.8% | 1.9% (-4.5% to 8.5%) | 0.56 | 0.62 | 0.55 | 0.18 |
| always_buy | 113.4% | 8.1% | 0.55 | 0.75 | -28.4% | 0.29 | 0.2 | 99.8% | -1.1% | 0.67 | n/a | n/a | n/a |
| logreg | 66.0% | 5.3% | 0.34 | 0.46 | -23.9% | 0.22 | 43.3 | 99.8% | -1.8% (-6.7% to 3.6%) | 0.51 | 0.45 | 0.17 | -0.15 |
| jev_head_zero | 55.6% | 4.7% | 0.28 | 0.38 | -33.7% | 0.14 | 68.1 | 99.8% | -4.3% (-9.0% to 0.5%) | 0.68 | 0.43 | 0.03 | -0.57 |
| majority | 37.4% | 3.3% | 0.19 | 0.25 | -30.1% | 0.11 | 73.5 | 99.8% | -5.6% (-9.5% to -1.8%) | 0.68 | 0.35 | -0.09 | -1.52 |
| stratified_random | 37.4% | 3.3% | 0.19 | 0.25 | -30.1% | 0.11 | 73.5 | 99.8% | -5.6% (-9.5% to -1.8%) | 0.68 | 0.35 | -0.09 | -1.52 |
| random_forest | 34.5% | 3.1% | 0.17 | 0.22 | -31.1% | 0.10 | 44.2 | 99.8% | -4.9% (-9.5% to -0.1%) | 0.60 | 0.27 | 0.00 | -0.33 |
| jev_signal_zero | 20.6% | 1.9% | 0.08 | 0.11 | -26.5% | 0.07 | 73.1 | 99.8% | -5.5% (-9.9% to -1.3%) | 0.54 | 0.27 | -0.24 | -0.90 |
| gbt | 17.8% | 1.7% | 0.07 | 0.10 | -38.5% | 0.04 | 46.7 | 99.8% | -6.8% (-13.5% to 0.0%) | 0.66 | 0.17 | -0.09 | -0.59 |
| jev_plus_controlled_zero | 5.6% | 0.6% | -0.00 | -0.00 | -42.0% | 0.01 | 49.6 | 99.8% | -7.9% (-15.4% to -0.8%) | 0.66 | 0.10 | -0.17 | -0.76 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.48 | -0.80 to -0.15 | 0.004 | 0.024 |
| jev_head_zero vs always_buy | -0.27 | -0.52 to -0.04 | 0.029 | 0.120 |
| jev_plus_controlled_zero vs always_buy | -0.55 | -0.88 to -0.20 | 0.002 | 0.016 |
| jev_signal_zero vs always_buy | -0.48 | -0.80 to -0.19 | 0.002 | 0.017 |
| logreg vs always_buy | -0.21 | -0.60 to 0.18 | 0.289 | 0.867 |
| ma_cross_rule vs always_buy | 0.04 | -0.41 to 0.46 | 0.883 | 1.000 |
| momentum_rule vs always_buy | 0.04 | -0.48 to 0.55 | 0.884 | 1.000 |
| random_forest vs always_buy | -0.39 | -0.74 to -0.06 | 0.024 | 0.120 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.06 | -0.49 to 0.34 | 0.755 | 0.755 |
| jev_plus_controlled_zero vs logreg | -0.35 | -0.77 to 0.10 | 0.122 | 0.366 |
| jev_signal_zero vs logreg | -0.27 | -0.76 to 0.18 | 0.273 | 0.546 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.07 | -0.24 to 0.11 | 0.412 | 0.412 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.08 | -0.46 to 0.54 | 0.774 | 0.774 |

**20-day horizon**, 2015-01-02 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 121.7% | 8.5% | 0.60 | 0.83 | -25.7% | 0.33 | 13.5 | 99.2% | 1.5% (-4.6% to 7.3%) | 0.48 | 0.64 | 0.55 | 0.12 |
| always_buy | 109.4% | 7.9% | 0.54 | 0.73 | -28.4% | 0.28 | 0.2 | 99.2% | -1.2% | 0.66 | n/a | n/a | n/a |
| ma_cross_rule | 103.5% | 7.6% | 0.45 | 0.60 | -27.7% | 0.27 | 7.7 | 99.2% | -0.7% (-7.4% to 6.9%) | 0.62 | 0.47 | 0.43 | 0.14 |
| jev_head_zero | 88.8% | 6.8% | 0.44 | 0.59 | -32.1% | 0.21 | 17.7 | 99.2% | -2.4% (-6.7% to 2.1%) | 0.67 | 0.48 | 0.37 | -0.10 |
| majority | 85.8% | 6.6% | 0.43 | 0.59 | -29.3% | 0.22 | 18.2 | 99.2% | -2.5% (-6.2% to 1.3%) | 0.67 | 0.48 | 0.36 | -0.98 |
| stratified_random | 85.8% | 6.6% | 0.43 | 0.59 | -29.3% | 0.22 | 18.2 | 99.2% | -2.5% (-6.2% to 1.3%) | 0.67 | 0.48 | 0.36 | -0.98 |
| jev_signal_zero | 76.5% | 6.0% | 0.42 | 0.57 | -20.0% | 0.30 | 18.1 | 99.2% | -1.8% (-5.9% to 2.0%) | 0.56 | 0.46 | 0.34 | -0.31 |
| gbt | 73.9% | 5.9% | 0.35 | 0.48 | -26.2% | 0.22 | 13.4 | 99.2% | -2.7% (-8.2% to 3.0%) | 0.65 | 0.38 | 0.31 | -0.20 |
| jev_plus_controlled_zero | 73.6% | 5.8% | 0.35 | 0.48 | -24.5% | 0.24 | 13.1 | 99.2% | -2.6% (-7.9% to 2.9%) | 0.64 | 0.38 | 0.31 | -0.19 |
| random_forest | 66.5% | 5.4% | 0.34 | 0.47 | -24.2% | 0.22 | 13.0 | 99.2% | -2.6% (-6.6% to 1.9%) | 0.58 | 0.38 | 0.29 | -0.38 |
| momentum_rule | 59.8% | 4.9% | 0.31 | 0.42 | -22.6% | 0.22 | 9.5 | 99.2% | -2.5% (-7.8% to 2.9%) | 0.54 | 0.33 | 0.27 | -0.22 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.19 | -0.49 to 0.10 | 0.206 | 1.000 |
| jev_head_zero vs always_buy | -0.10 | -0.24 to 0.04 | 0.149 | 1.000 |
| jev_plus_controlled_zero vs always_buy | -0.19 | -0.51 to 0.10 | 0.237 | 1.000 |
| jev_signal_zero vs always_buy | -0.12 | -0.47 to 0.17 | 0.473 | 1.000 |
| logreg vs always_buy | 0.06 | -0.45 to 0.52 | 0.814 | 1.000 |
| ma_cross_rule vs always_buy | -0.09 | -0.49 to 0.29 | 0.659 | 1.000 |
| momentum_rule vs always_buy | -0.23 | -0.70 to 0.20 | 0.337 | 1.000 |
| random_forest vs always_buy | -0.20 | -0.62 to 0.15 | 0.327 | 1.000 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.08 | -0.20 to 0.40 | 0.602 | 1.000 |
| jev_plus_controlled_zero vs gbt | -0.00 | -0.10 to 0.08 | 0.999 | 1.000 |
| jev_signal_zero vs gbt | 0.07 | -0.40 to 0.48 | 0.783 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.00 | -0.10 to 0.08 | 0.999 | 0.999 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.07 | -0.37 to 0.47 | 0.754 | 0.754 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.

**1-day horizon**, 2015-01-02 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 112.7% | 8.1% | 0.55 | 0.75 | -28.4% | 0.28 | 0.1 | 100.0% | -1.1% | 0.67 | n/a | n/a | n/a |
| ma_cross_rule | -10.2% | -1.1% | 0.01 | 0.02 | -51.4% | -0.02 | 26.8 | 100.0% | -6.0% (-18.6% to 7.5%) | 0.53 | 0.05 | -0.04 | -0.27 |
| jev_plus_controlled_zero | -33.9% | -4.2% | -0.15 | -0.21 | -72.2% | -0.06 | 364.5 | 100.0% | -11.1% (-22.8% to 1.9%) | 0.64 | 0.34 | -0.97 | -1.11 |
| momentum_rule | -37.7% | -4.8% | -0.20 | -0.28 | -58.1% | -0.08 | 102.9 | 100.0% | -7.9% (-20.4% to 3.6%) | 0.30 | -0.06 | -0.45 | -0.71 |
| gbt | -51.1% | -7.1% | -0.27 | -0.37 | -72.5% | -0.10 | 339.4 | 100.0% | -14.5% (-27.8% to -1.7%) | 0.68 | 0.17 | -1.00 | -0.98 |
| random_forest | -48.8% | -6.6% | -0.33 | -0.44 | -69.4% | -0.10 | 306.1 | 100.0% | -12.7% (-24.0% to -0.7%) | 0.51 | 0.13 | -1.09 | -0.99 |
| logreg | -63.5% | -9.8% | -0.33 | -0.47 | -67.9% | -0.14 | 228.6 | 100.0% | -15.3% (-30.3% to -0.8%) | 0.55 | -0.07 | -0.77 | -0.64 |
| jev_head_zero | -77.8% | -14.4% | -0.59 | -0.81 | -82.9% | -0.17 | 439.3 | 100.0% | -22.5% (-37.4% to -9.2%) | 0.69 | -0.05 | -1.51 | -0.99 |
| majority | -75.0% | -13.3% | -0.65 | -0.87 | -79.3% | -0.17 | 471.2 | 100.0% | -20.4% (-31.9% to -9.5%) | 0.56 | 0.02 | -1.77 | -1.59 |
| stratified_random | -75.0% | -13.3% | -0.65 | -0.87 | -79.3% | -0.17 | 471.2 | 100.0% | -20.4% (-31.9% to -9.5%) | 0.56 | 0.02 | -1.77 | -1.59 |
| jev_signal_zero | -88.1% | -19.7% | -0.98 | -1.35 | -88.5% | -0.22 | 456.8 | 100.0% | -26.4% (-39.2% to -13.9%) | 0.44 | -0.35 | -2.04 | -1.40 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.82 | -1.44 to -0.27 | 0.004 | 0.027 |
| jev_head_zero vs always_buy | -1.15 | -1.83 to -0.52 | 0.001 | 0.010 |
| jev_plus_controlled_zero vs always_buy | -0.71 | -1.32 to -0.15 | 0.022 | 0.066 |
| jev_signal_zero vs always_buy | -1.53 | -2.30 to -0.80 | 0.000 | 0.004 |
| logreg vs always_buy | -0.88 | -1.66 to -0.24 | 0.012 | 0.057 |
| ma_cross_rule vs always_buy | -0.54 | -1.20 to 0.06 | 0.090 | 0.090 |
| momentum_rule vs always_buy | -0.76 | -1.46 to -0.10 | 0.030 | 0.066 |
| random_forest vs always_buy | -0.88 | -1.62 to -0.21 | 0.011 | 0.057 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.26 | -0.95 to 0.46 | 0.467 | 0.934 |
| jev_plus_controlled_zero vs logreg | 0.18 | -0.52 to 0.91 | 0.621 | 0.934 |
| jev_signal_zero vs logreg | -0.65 | -1.45 to 0.19 | 0.123 | 0.369 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.12 | -0.52 to 0.80 | 0.745 | 0.745 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.83 | -1.65 to -0.05 | 0.044 | 0.044 |

**5-day horizon (primary)**, 2015-01-02 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 113.4% | 8.1% | 0.55 | 0.75 | -28.4% | 0.29 | 0.2 | 99.8% | -1.1% | 0.67 | n/a | n/a | n/a |
| momentum_rule | 88.0% | 6.7% | 0.35 | 0.49 | -31.7% | 0.21 | 34.9 | 99.8% | 2.5% (-7.9% to 12.3%) | 0.34 | 0.40 | 0.26 | -0.24 |
| ma_cross_rule | 43.3% | 3.8% | 0.20 | 0.28 | -46.9% | 0.08 | 20.5 | 99.8% | -2.2% (-14.4% to 10.3%) | 0.59 | 0.23 | 0.16 | -0.01 |
| jev_plus_controlled_zero | 19.1% | 1.8% | 0.10 | 0.14 | -40.5% | 0.04 | 70.3 | 99.8% | -4.9% (-14.1% to 4.9%) | 0.56 | 0.21 | -0.09 | -0.43 |
| majority | 14.8% | 1.4% | 0.06 | 0.08 | -37.4% | 0.04 | 94.4 | 99.8% | -7.2% (-13.7% to -0.6%) | 0.68 | 0.24 | -0.25 | -1.07 |
| stratified_random | 14.8% | 1.4% | 0.06 | 0.08 | -37.4% | 0.04 | 94.4 | 99.8% | -7.2% (-13.7% to -0.6%) | 0.68 | 0.24 | -0.25 | -1.07 |
| jev_head_zero | 1.1% | 0.1% | -0.01 | -0.01 | -47.1% | 0.00 | 90.7 | 99.8% | -8.7% (-17.6% to -0.1%) | 0.72 | 0.15 | -0.27 | -0.67 |
| gbt | -4.5% | -0.5% | -0.03 | -0.03 | -46.1% | -0.01 | 67.3 | 99.8% | -7.2% (-16.7% to 2.8%) | 0.56 | 0.08 | -0.21 | -0.28 |
| logreg | -5.6% | -0.6% | -0.04 | -0.06 | -29.7% | -0.02 | 63.5 | 99.8% | -6.2% (-14.9% to 2.8%) | 0.46 | 0.07 | -0.22 | -0.03 |
| jev_signal_zero | -14.3% | -1.6% | -0.20 | -0.26 | -37.6% | -0.04 | 93.1 | 99.8% | -7.6% (-13.8% to -1.7%) | 0.43 | 0.03 | -0.56 | -1.03 |
| random_forest | -26.0% | -3.0% | -0.20 | -0.26 | -54.9% | -0.06 | 67.3 | 99.8% | -10.2% (-18.4% to -1.8%) | 0.57 | -0.08 | -0.40 | -0.17 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.58 | -1.11 to -0.07 | 0.028 | 0.140 |
| jev_head_zero vs always_buy | -0.56 | -0.93 to -0.17 | 0.006 | 0.036 |
| jev_plus_controlled_zero vs always_buy | -0.46 | -0.95 to 0.01 | 0.066 | 0.264 |
| jev_signal_zero vs always_buy | -0.75 | -1.25 to -0.31 | 0.002 | 0.016 |
| logreg vs always_buy | -0.59 | -1.26 to 0.06 | 0.079 | 0.264 |
| ma_cross_rule vs always_buy | -0.35 | -0.96 to 0.28 | 0.272 | 0.545 |
| momentum_rule vs always_buy | -0.21 | -0.89 to 0.44 | 0.529 | 0.545 |
| random_forest vs always_buy | -0.75 | -1.27 to -0.27 | 0.003 | 0.021 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | 0.03 | -0.69 to 0.80 | 0.923 | 1.000 |
| jev_plus_controlled_zero vs logreg | 0.14 | -0.56 to 0.80 | 0.689 | 1.000 |
| jev_signal_zero vs logreg | -0.16 | -0.87 to 0.58 | 0.673 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.12 | -0.18 to 0.44 | 0.431 | 0.431 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.29 | -0.95 to 0.35 | 0.377 | 0.377 |

**20-day horizon**, 2015-01-02 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 109.4% | 7.9% | 0.54 | 0.73 | -28.4% | 0.28 | 0.2 | 99.2% | -1.2% | 0.66 | n/a | n/a | n/a |
| jev_signal_zero | 68.5% | 5.5% | 0.38 | 0.53 | -28.7% | 0.19 | 22.7 | 99.2% | -0.8% (-6.5% to 4.5%) | 0.43 | 0.44 | 0.28 | -0.35 |
| logreg | 82.9% | 6.4% | 0.34 | 0.48 | -32.6% | 0.20 | 18.4 | 99.2% | 1.5% (-7.5% to 11.0%) | 0.39 | 0.37 | 0.29 | 0.20 |
| majority | 67.4% | 5.4% | 0.33 | 0.45 | -34.5% | 0.16 | 23.3 | 99.2% | -3.7% (-9.4% to 1.9%) | 0.69 | 0.38 | 0.25 | -0.81 |
| stratified_random | 67.4% | 5.4% | 0.33 | 0.45 | -34.5% | 0.16 | 23.3 | 99.2% | -3.7% (-9.4% to 1.9%) | 0.69 | 0.38 | 0.25 | -0.81 |
| ma_cross_rule | 42.4% | 3.7% | 0.20 | 0.27 | -40.8% | 0.09 | 11.2 | 99.2% | -3.4% (-14.6% to 8.6%) | 0.67 | 0.22 | 0.18 | -0.07 |
| jev_head_zero | 27.5% | 2.5% | 0.13 | 0.17 | -32.2% | 0.08 | 22.7 | 99.2% | -5.7% (-11.5% to -0.1%) | 0.63 | 0.18 | 0.05 | -0.34 |
| momentum_rule | 8.7% | 0.9% | 0.03 | 0.05 | -37.5% | 0.02 | 15.5 | 99.2% | -5.1% (-13.2% to 3.1%) | 0.48 | 0.06 | -0.01 | -0.07 |
| jev_plus_controlled_zero | 1.9% | 0.2% | 0.00 | 0.00 | -34.5% | 0.01 | 19.5 | 99.2% | -6.8% (-14.6% to 1.4%) | 0.58 | 0.04 | -0.05 | -0.21 |
| random_forest | 1.9% | 0.2% | -0.01 | -0.02 | -35.6% | 0.01 | 18.1 | 99.2% | -6.4% (-13.4% to 0.7%) | 0.51 | 0.02 | -0.07 | -0.36 |
| gbt | -12.4% | -1.4% | -0.09 | -0.12 | -33.9% | -0.04 | 19.4 | 99.2% | -8.8% (-16.4% to -0.6%) | 0.61 | -0.05 | -0.14 | -0.39 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.63 | -1.17 to -0.13 | 0.016 | 0.115 |
| jev_head_zero vs always_buy | -0.41 | -0.68 to -0.16 | 0.004 | 0.032 |
| jev_plus_controlled_zero vs always_buy | -0.54 | -1.08 to -0.06 | 0.039 | 0.195 |
| jev_signal_zero vs always_buy | -0.16 | -0.74 to 0.35 | 0.552 | 1.000 |
| logreg vs always_buy | -0.20 | -0.88 to 0.42 | 0.560 | 1.000 |
| ma_cross_rule vs always_buy | -0.34 | -0.87 to 0.13 | 0.202 | 0.607 |
| momentum_rule vs always_buy | -0.51 | -1.17 to 0.07 | 0.121 | 0.486 |
| random_forest vs always_buy | -0.55 | -1.07 to -0.13 | 0.023 | 0.141 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.21 | -0.23 to 0.73 | 0.397 | 0.620 |
| jev_plus_controlled_zero vs gbt | 0.09 | -0.10 to 0.27 | 0.310 | 0.620 |
| jev_signal_zero vs gbt | 0.47 | -0.23 to 1.15 | 0.180 | 0.541 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.09 | -0.10 to 0.27 | 0.310 | 0.310 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.38 | -0.25 to 1.02 | 0.255 | 0.255 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2015-01-02 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 112.7% | 8.1% | 0.55 | 0.75 | -28.4% | 0.28 | 0.1 | 100.0% | -1.1% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 36.1% | 3.2% | 0.32 | 0.44 | -9.1% | 0.35 | 16.1 | 42.7% | -0.1% (-3.0% to 2.6%) | 0.15 | 0.41 | 0.16 | -0.33 | 0.61 | -1.1% |
| random_forest | 37.8% | 3.3% | 0.26 | 0.36 | -14.3% | 0.23 | 37.3 | 33.1% | -1.6% (-4.6% to 1.4%) | 0.29 | 0.42 | -0.00 | -0.37 | 0.51 | -1.5% |
| ma_cross_rule | 29.1% | 2.7% | 0.22 | 0.30 | -8.2% | 0.33 | 17.4 | 41.0% | -0.6% (-3.4% to 2.0%) | 0.14 | 0.33 | 0.04 | -0.21 | 0.53 | -1.2% |
| logreg | 23.2% | 2.2% | 0.10 | 0.13 | -13.9% | 0.16 | 24.3 | 29.7% | -2.2% (-5.1% to 0.5%) | 0.24 | 0.21 | -0.08 | -0.42 | 0.27 | -1.1% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1167.77 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| gbt | -0.8% | -0.1% | -0.19 | -0.24 | -33.2% | -0.00 | 53.3 | 29.8% | -5.4% (-9.6% to -1.6%) | 0.33 | 0.02 | -0.53 | -1.27 | 0.10 | -2.2% |
| jev_plus_controlled_zero | -2.0% | -0.2% | -0.20 | -0.25 | -27.7% | -0.01 | 54.1 | 29.6% | -5.5% (-9.8% to -1.7%) | 0.32 | 0.00 | -0.55 | -1.04 | 0.02 | -1.8% |
| jev_head_zero | 1.3% | 0.1% | -0.27 | -0.34 | -19.3% | 0.01 | 92.6 | 30.4% | -4.0% (-6.6% to -1.6%) | 0.22 | 0.26 | -1.16 | -1.30 | 0.47 | -3.6% |
| stratified_random | -7.8% | -0.8% | -0.52 | -0.69 | -19.6% | -0.04 | 105.6 | 30.1% | -4.8% (-6.6% to -3.1%) | 0.20 | 0.16 | -1.67 | -1.98 | 0.60 | -4.9% |
| jev_signal_zero | -4.0% | -0.4% | -0.69 | -0.83 | -13.5% | -0.03 | 35.6 | 8.4% | -2.9% (-4.8% to -1.1%) | 0.07 | -0.33 | -1.28 | -0.72 | -0.07 | -1.9% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.74 | -1.20 to -0.31 | 0.003 | 0.015 |
| jev_head_zero vs always_buy | -0.83 | -1.26 to -0.44 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.76 | -1.22 to -0.33 | 0.002 | 0.012 |
| jev_signal_zero vs always_buy | -1.24 | -1.86 to -0.70 | 0.000 | 0.004 |
| logreg vs always_buy | -0.45 | -1.00 to 0.03 | 0.088 | 0.352 |
| ma_cross_rule vs always_buy | -0.33 | -0.94 to 0.26 | 0.289 | 0.652 |
| momentum_rule vs always_buy | -0.23 | -0.86 to 0.37 | 0.476 | 0.652 |
| random_forest vs always_buy | -0.29 | -0.78 to 0.17 | 0.217 | 0.652 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.38 | -0.88 to 0.14 | 0.156 | 0.250 |
| jev_plus_controlled_zero vs logreg | -0.31 | -0.66 to 0.12 | 0.125 | 0.250 |
| jev_signal_zero vs logreg | -0.79 | -1.46 to -0.17 | 0.016 | 0.048 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.02 | -0.25 to 0.21 | 0.888 | 0.888 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.49 | -1.20 to 0.07 | 0.124 | 0.124 |

**5-day horizon (primary)**, 2015-01-02 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 113.4% | 8.1% | 0.55 | 0.75 | -28.4% | 0.29 | 0.2 | 99.8% | -1.1% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 51.1% | 4.3% | 0.53 | 0.72 | -7.0% | 0.62 | 6.0 | 43.0% | 0.6% (-1.9% to 3.0%) | 0.18 | 0.56 | 0.47 | -0.06 | 0.39 | 0.8% |
| jev_head_zero | 41.7% | 3.6% | 0.44 | 0.61 | -10.8% | 0.34 | 19.1 | 30.4% | -0.7% (-2.2% to 0.8%) | 0.22 | 0.57 | 0.23 | -0.14 | 0.69 | -0.9% |
| logreg | 38.0% | 3.4% | 0.34 | 0.47 | -7.7% | 0.44 | 8.0 | 27.4% | -0.3% (-2.6% to 1.9%) | 0.18 | 0.38 | 0.26 | -0.09 | 0.37 | -0.2% |
| ma_cross_rule | 34.3% | 3.1% | 0.31 | 0.43 | -6.0% | 0.51 | 8.7 | 40.6% | -0.3% (-2.8% to 2.1%) | 0.15 | 0.37 | 0.22 | -0.06 | 0.50 | -0.7% |
| jev_signal_zero | 24.7% | 2.3% | 0.17 | 0.24 | -7.1% | 0.32 | 20.1 | 28.9% | -1.2% (-2.8% to 0.3%) | 0.16 | 0.33 | -0.09 | -0.52 | 0.61 | -1.5% |
| random_forest | 23.3% | 2.2% | 0.10 | 0.12 | -23.3% | 0.09 | 10.5 | 32.1% | -3.0% (-7.1% to 0.7%) | 0.32 | 0.14 | 0.03 | -0.20 | 0.22 | -0.8% |
| gbt | 22.6% | 2.1% | 0.10 | 0.12 | -18.0% | 0.12 | 11.8 | 31.9% | -2.6% (-5.7% to 0.5%) | 0.27 | 0.15 | 0.00 | -0.48 | 0.37 | -1.6% |
| stratified_random | 21.0% | 2.0% | 0.08 | 0.11 | -11.6% | 0.17 | 22.1 | 32.2% | -2.2% (-3.8% to -0.9%) | 0.22 | 0.24 | -0.17 | -1.47 | 0.51 | -1.8% |
| jev_plus_controlled_zero | 19.7% | 1.9% | 0.06 | 0.07 | -18.8% | 0.10 | 12.5 | 30.8% | -2.8% (-6.1% to 0.4%) | 0.26 | 0.12 | -0.04 | -0.48 | 0.31 | -1.5% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1167.77 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.46 | -0.87 to 0.00 | 0.037 | 0.262 |
| jev_head_zero vs always_buy | -0.11 | -0.40 to 0.16 | 0.429 | 1.000 |
| jev_plus_controlled_zero vs always_buy | -0.50 | -0.88 to -0.04 | 0.021 | 0.172 |
| jev_signal_zero vs always_buy | -0.38 | -0.77 to -0.04 | 0.044 | 0.262 |
| logreg vs always_buy | -0.22 | -0.78 to 0.30 | 0.454 | 1.000 |
| ma_cross_rule vs always_buy | -0.24 | -0.79 to 0.30 | 0.375 | 1.000 |
| momentum_rule vs always_buy | -0.03 | -0.57 to 0.47 | 0.919 | 1.000 |
| random_forest vs always_buy | -0.45 | -0.84 to 0.01 | 0.038 | 0.262 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | 0.10 | -0.41 to 0.64 | 0.722 | 1.000 |
| jev_plus_controlled_zero vs logreg | -0.28 | -0.71 to 0.22 | 0.226 | 0.678 |
| jev_signal_zero vs logreg | -0.16 | -0.74 to 0.42 | 0.600 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.04 | -0.13 to 0.08 | 0.464 | 0.464 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.12 | -0.49 to 0.63 | 0.699 | 0.699 |

**20-day horizon**, 2015-01-02 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 227.9% | 13.0% | 0.71 | 0.96 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 109.4% | 7.9% | 0.54 | 0.73 | -28.4% | 0.28 | 0.2 | 99.2% | -1.2% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 42.9% | 3.7% | 0.47 | 0.64 | -9.3% | 0.40 | 5.7 | 35.2% | -0.7% (-1.9% to 0.5%) | 0.24 | 0.51 | 0.40 | 0.15 | 0.53 | -0.3% |
| jev_signal_zero | 39.5% | 3.5% | 0.46 | 0.63 | -7.1% | 0.49 | 5.4 | 32.2% | -0.4% (-1.9% to 1.1%) | 0.18 | 0.51 | 0.40 | -0.11 | 0.53 | -0.3% |
| ma_cross_rule | 42.2% | 3.7% | 0.43 | 0.58 | -7.9% | 0.47 | 3.7 | 41.4% | -0.1% (-2.3% to 2.2%) | 0.18 | 0.46 | 0.39 | 0.08 | 0.41 | 0.1% |
| jev_head_zero | 38.7% | 3.4% | 0.38 | 0.51 | -10.3% | 0.33 | 5.3 | 33.2% | -1.1% (-2.3% to 0.2%) | 0.24 | 0.41 | 0.32 | 0.07 | 0.52 | -0.6% |
| momentum_rule | 40.5% | 3.6% | 0.31 | 0.41 | -16.5% | 0.22 | 2.8 | 48.6% | -1.3% (-4.4% to 1.7%) | 0.28 | 0.33 | 0.29 | -0.10 | 0.37 | -0.4% |
| jev_plus_controlled_zero | 37.1% | 3.3% | 0.29 | 0.40 | -12.9% | 0.26 | 3.6 | 28.9% | -1.2% (-3.0% to 0.8%) | 0.25 | 0.31 | 0.26 | -0.01 | 0.37 | -0.4% |
| gbt | 35.4% | 3.2% | 0.26 | 0.36 | -12.8% | 0.25 | 3.6 | 30.3% | -1.6% (-3.5% to 0.5%) | 0.27 | 0.28 | 0.23 | -0.03 | 0.37 | -0.5% |
| logreg | 28.9% | 2.6% | 0.20 | 0.27 | -12.1% | 0.22 | 2.8 | 25.1% | -1.2% (-4.1% to 1.4%) | 0.19 | 0.21 | 0.17 | -0.06 | 0.22 | -0.2% |
| random_forest | 30.0% | 2.7% | 0.19 | 0.26 | -11.7% | 0.23 | 3.2 | 29.7% | -1.7% (-4.0% to 0.5%) | 0.24 | 0.21 | 0.17 | 0.01 | 0.26 | -0.4% |
| majority | 28.8% | 2.6% | 0.16 | 0.22 | -13.4% | 0.20 | 0.8 | 30.8% | -1.8% (-5.4% to 1.6%) | 0.25 | 0.16 | 0.15 | 0.08 | 0.16 | -0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.28 | -0.71 to 0.09 | 0.175 | 1.000 |
| jev_head_zero vs always_buy | -0.16 | -0.44 to 0.09 | 0.232 | 1.000 |
| jev_plus_controlled_zero vs always_buy | -0.25 | -0.66 to 0.11 | 0.214 | 1.000 |
| jev_signal_zero vs always_buy | -0.08 | -0.41 to 0.20 | 0.647 | 1.000 |
| logreg vs always_buy | -0.34 | -0.99 to 0.29 | 0.332 | 1.000 |
| ma_cross_rule vs always_buy | -0.11 | -0.53 to 0.27 | 0.581 | 1.000 |
| momentum_rule vs always_buy | -0.23 | -0.56 to 0.09 | 0.145 | 1.000 |
| random_forest vs always_buy | -0.35 | -0.87 to 0.08 | 0.164 | 1.000 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.12 | -0.16 to 0.44 | 0.418 | 1.000 |
| jev_plus_controlled_zero vs gbt | 0.03 | -0.06 to 0.15 | 0.534 | 1.000 |
| jev_signal_zero vs gbt | 0.21 | -0.23 to 0.65 | 0.392 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.03 | -0.06 to 0.15 | 0.534 | 0.534 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.17 | -0.26 to 0.63 | 0.455 | 0.455 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.34 (median of 8 comparisons). A true difference smaller than about 0.48 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

36,750 test observations on 2,450 dates. Reference traditional classifier (chosen on validation data): **logreg**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.360 | 0.361 | 0.382 | 1.095 | 0.664 | 0.017 | 0.511 | 23/44/33 | 0.0% |
| logreg | 0.355 | 0.360 | 0.361 | 1.118 | 0.678 | 0.070 | 0.493 | 37/33/30 | 0.0% |
| jev_head_zero | 0.349 | 0.349 | 0.366 | 1.123 | 0.681 | 0.070 | 0.511 | 27/43/30 | 0.0% |
| gbt | 0.342 | 0.344 | 0.352 | 1.200 | 0.728 | 0.162 | 0.491 | 33/38/30 | 0.0% |
| jev_plus_controlled_zero | 0.342 | 0.345 | 0.350 | 1.187 | 0.721 | 0.148 | 0.490 | 35/35/30 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.351 | 1.075 | 0.650 | 0.007 | 0.504 | 27/43/30 | 0.0% |
| momentum_rule | 0.331 | 0.335 | 0.344 | n/a | n/a | n/a | 0.511 | 21/36/43 | 0.0% |
| ma_cross_rule | 0.327 | 0.330 | 0.342 | n/a | n/a | n/a | 0.516 | 19/40/41 | 0.0% |
| jev_signal_zero | 0.289 | 0.341 | 0.420 | 1.515 | 0.807 | 0.257 | 0.504 | 9/82/8 | 0.0% |
| majority | 0.204 | 0.333 | 0.441 | 1.075 | 0.650 | 0.007 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 26.0%, HOLD 44.1%, BUY 29.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.254 | 0.469 | 0.314 | 0.319 | 0.399 | 0.313 | 0.067% | 0.015% | 0.021% |
| jev_head_zero | 0.276 | 0.462 | 0.309 | 0.284 | 0.449 | 0.315 | 0.016% | 0.035% | 0.048% |
| jev_plus_controlled_zero | 0.256 | 0.473 | 0.313 | 0.344 | 0.380 | 0.310 | 0.049% | 0.031% | 0.020% |
| jev_signal_zero | 0.296 | 0.447 | 0.296 | 0.106 | 0.834 | 0.083 | -0.004% | 0.042% | -0.008% |
| logreg | 0.268 | 0.504 | 0.320 | 0.386 | 0.376 | 0.318 | 0.018% | 0.055% | 0.031% |
| ma_cross_rule | 0.290 | 0.430 | 0.283 | 0.217 | 0.386 | 0.388 | 0.039% | 0.040% | 0.025% |
| majority | 0.000 | 0.441 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.034% | n/a |
| momentum_rule | 0.279 | 0.445 | 0.290 | 0.226 | 0.365 | 0.415 | 0.053% | 0.029% | 0.029% |
| random_forest | 0.273 | 0.484 | 0.324 | 0.245 | 0.479 | 0.358 | 0.026% | 0.026% | 0.050% |
| stratified_random | 0.261 | 0.441 | 0.301 | 0.267 | 0.433 | 0.302 | 0.019% | 0.035% | 0.044% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0085 | -0.0009 to 0.0174 | 0.063 | 0.254 |
| jev_head_zero vs stratified_random | 0.0150 | 0.0081 to 0.0222 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs stratified_random | 0.0083 | -0.0022 to 0.0174 | 0.094 | 0.283 |
| jev_signal_zero vs stratified_random | -0.0448 | -0.0533 to -0.0361 | 0.000 | 0.004 |
| logreg vs stratified_random | 0.0212 | 0.0093 to 0.0335 | 0.001 | 0.005 |
| ma_cross_rule vs stratified_random | -0.0067 | -0.0166 to 0.0035 | 0.205 | 0.411 |
| momentum_rule vs stratified_random | -0.0032 | -0.0131 to 0.0070 | 0.531 | 0.531 |
| random_forest vs stratified_random | 0.0259 | 0.0164 to 0.0351 | 0.000 | 0.004 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.0062 | -0.0170 to 0.0046 | 0.261 | 0.261 |
| jev_plus_controlled_zero vs logreg | -0.0129 | -0.0234 to -0.0025 | 0.013 | 0.026 |
| jev_signal_zero vs logreg | -0.0660 | -0.0764 to -0.0552 | 0.000 | 0.001 |

### 5-day horizon (primary)

36,690 test observations on 2,446 dates. Reference traditional classifier (chosen on validation data): **logreg**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.353 | 0.353 | 0.368 | 1.107 | 0.672 | 0.056 | 0.508 | 26/41/32 | 0.0% |
| logreg | 0.353 | 0.363 | 0.355 | 1.177 | 0.708 | 0.124 | 0.492 | 43/30/27 | 0.0% |
| jev_head_zero | 0.346 | 0.347 | 0.366 | 1.141 | 0.691 | 0.100 | 0.510 | 24/45/30 | 0.0% |
| momentum_rule | 0.336 | 0.339 | 0.353 | n/a | n/a | n/a | 0.527 | 20/37/43 | 0.0% |
| stratified_random | 0.332 | 0.332 | 0.345 | 1.083 | 0.656 | 0.024 | 0.506 | 26/41/32 | 0.0% |
| jev_plus_controlled_zero | 0.332 | 0.339 | 0.333 | 1.355 | 0.799 | 0.247 | 0.487 | 40/29/31 | 0.0% |
| gbt | 0.331 | 0.337 | 0.332 | 1.350 | 0.795 | 0.239 | 0.486 | 38/30/32 | 0.0% |
| ma_cross_rule | 0.330 | 0.331 | 0.345 | n/a | n/a | n/a | 0.519 | 20/39/41 | 0.0% |
| jev_signal_zero | 0.329 | 0.331 | 0.355 | 1.378 | 0.787 | 0.246 | 0.504 | 21/50/29 | 0.0% |
| majority | 0.198 | 0.333 | 0.421 | 1.083 | 0.656 | 0.024 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.2%, HOLD 42.1%, BUY 32.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.246 | 0.443 | 0.334 | 0.374 | 0.312 | 0.327 | 0.201% | 0.204% | 0.099% |
| jev_head_zero | 0.260 | 0.441 | 0.338 | 0.251 | 0.474 | 0.315 | 0.153% | 0.143% | 0.222% |
| jev_plus_controlled_zero | 0.247 | 0.444 | 0.337 | 0.389 | 0.309 | 0.319 | 0.186% | 0.233% | 0.088% |
| jev_signal_zero | 0.264 | 0.419 | 0.310 | 0.224 | 0.494 | 0.275 | 0.217% | 0.163% | 0.145% |
| logreg | 0.267 | 0.488 | 0.348 | 0.450 | 0.347 | 0.292 | 0.092% | 0.273% | 0.177% |
| ma_cross_rule | 0.280 | 0.416 | 0.308 | 0.221 | 0.390 | 0.383 | 0.183% | 0.212% | 0.122% |
| majority | 0.000 | 0.421 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.170% | n/a |
| momentum_rule | 0.270 | 0.428 | 0.325 | 0.208 | 0.380 | 0.428 | 0.317% | 0.096% | 0.167% |
| random_forest | 0.256 | 0.456 | 0.349 | 0.268 | 0.448 | 0.344 | 0.192% | 0.208% | 0.102% |
| stratified_random | 0.248 | 0.419 | 0.328 | 0.258 | 0.413 | 0.324 | 0.202% | 0.185% | 0.123% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | -0.0008 | -0.0140 to 0.0120 | 0.902 | 1.000 |
| jev_head_zero vs stratified_random | 0.0145 | 0.0058 to 0.0230 | 0.002 | 0.014 |
| jev_plus_controlled_zero vs stratified_random | -0.0002 | -0.0136 to 0.0125 | 0.976 | 1.000 |
| jev_signal_zero vs stratified_random | -0.0024 | -0.0121 to 0.0073 | 0.621 | 1.000 |
| logreg vs stratified_random | 0.0212 | 0.0043 to 0.0369 | 0.009 | 0.057 |
| ma_cross_rule vs stratified_random | -0.0014 | -0.0139 to 0.0111 | 0.814 | 1.000 |
| momentum_rule vs stratified_random | 0.0039 | -0.0090 to 0.0167 | 0.536 | 1.000 |
| random_forest vs stratified_random | 0.0215 | 0.0079 to 0.0337 | 0.001 | 0.008 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.0067 | -0.0213 to 0.0095 | 0.395 | 0.395 |
| jev_plus_controlled_zero vs logreg | -0.0214 | -0.0358 to -0.0074 | 0.004 | 0.008 |
| jev_signal_zero vs logreg | -0.0236 | -0.0381 to -0.0070 | 0.002 | 0.007 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 3,457 | 2,577 | 3,219 | 0 |
| HOLD | 6,037 | 4,818 | 4,595 | 0 |
| BUY | 4,575 | 3,493 | 3,919 | 0 |

`jev_head_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,324 | 4,067 | 2,862 | 0 |
| HOLD | 3,606 | 7,319 | 4,525 | 0 |
| BUY | 3,001 | 5,208 | 3,778 | 0 |

`jev_plus_controlled_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 3,604 | 2,533 | 3,116 | 0 |
| HOLD | 6,285 | 4,781 | 4,384 | 0 |
| BUY | 4,719 | 3,448 | 3,820 | 0 |

`jev_signal_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,075 | 4,616 | 2,562 | 0 |
| HOLD | 3,049 | 7,632 | 4,769 | 0 |
| BUY | 2,732 | 5,954 | 3,301 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 4,168 | 2,364 | 2,721 | 0 |
| HOLD | 6,234 | 5,366 | 3,850 | 0 |
| BUY | 5,215 | 3,266 | 3,506 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,049 | 3,622 | 3,582 | 0 |
| HOLD | 2,682 | 6,020 | 6,748 | 0 |
| BUY | 2,576 | 4,822 | 4,589 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 9,253 | 0 | 0 |
| HOLD | 0 | 15,450 | 0 | 0 |
| BUY | 0 | 11,987 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,929 | 3,562 | 3,762 | 0 |
| HOLD | 2,661 | 5,873 | 6,916 | 0 |
| BUY | 2,566 | 4,289 | 5,132 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,478 | 3,525 | 3,250 | 0 |
| HOLD | 4,078 | 6,923 | 4,449 | 0 |
| BUY | 3,136 | 4,732 | 4,119 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,388 | 3,829 | 3,036 | 0 |
| HOLD | 4,150 | 6,379 | 4,921 | 0 |
| BUY | 3,095 | 5,004 | 3,888 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 | Fold 10 | Fold 11 | Fold 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.340 | 0.348 | 0.322 | 0.338 | 0.335 | 0.343 | 0.323 | 0.271 | 0.286 | 0.318 | 0.299 | 0.233 | 0.315 |
| jev_head_zero | 0.361 | 0.354 | 0.349 | 0.344 | 0.316 | 0.330 | 0.353 | 0.335 | 0.344 | 0.317 | 0.321 | 0.308 | 0.343 |
| jev_plus_controlled_zero | 0.327 | 0.351 | 0.302 | 0.343 | 0.337 | 0.358 | 0.316 | 0.274 | 0.301 | 0.303 | 0.285 | 0.240 | 0.318 |
| jev_signal_zero | 0.341 | 0.331 | 0.333 | 0.321 | 0.305 | 0.311 | 0.352 | 0.344 | 0.329 | 0.322 | 0.338 | 0.310 | 0.315 |
| logreg | 0.349 | 0.338 | 0.326 | 0.310 | 0.299 | 0.343 | 0.388 | 0.344 | 0.244 | 0.309 | 0.266 | 0.274 | 0.279 |
| ma_cross_rule | 0.329 | 0.320 | 0.270 | 0.338 | 0.349 | 0.333 | 0.336 | 0.335 | 0.298 | 0.336 | 0.316 | 0.312 | 0.292 |
| majority | 0.199 | 0.199 | 0.215 | 0.189 | 0.188 | 0.190 | 0.188 | 0.233 | 0.207 | 0.181 | 0.193 | 0.191 | 0.187 |
| momentum_rule | 0.350 | 0.350 | 0.294 | 0.328 | 0.306 | 0.315 | 0.334 | 0.327 | 0.292 | 0.333 | 0.340 | 0.312 | 0.304 |
| random_forest | 0.346 | 0.327 | 0.314 | 0.364 | 0.304 | 0.322 | 0.346 | 0.285 | 0.317 | 0.276 | 0.269 | 0.299 | 0.333 |
| stratified_random | 0.316 | 0.330 | 0.341 | 0.337 | 0.328 | 0.324 | 0.326 | 0.326 | 0.330 | 0.327 | 0.339 | 0.336 | 0.337 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.309 | 0.339 | 0.327 |
| jev_head_zero | 0.341 | 0.347 | 0.346 |
| jev_plus_controlled_zero | 0.314 | 0.337 | 0.329 |
| jev_signal_zero | 0.348 | 0.328 | 0.322 |
| logreg | 0.373 | 0.356 | 0.339 |
| ma_cross_rule | 0.345 | 0.325 | 0.314 |
| majority | 0.192 | 0.201 | 0.197 |
| momentum_rule | 0.341 | 0.340 | 0.314 |
| random_forest | 0.316 | 0.364 | 0.352 |
| stratified_random | 0.325 | 0.326 | 0.338 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.309 | 0.331 | 0.346 | 15 |
| jev_head_zero | 0.329 | 0.345 | 0.358 | 15 |
| jev_plus_controlled_zero | 0.307 | 0.332 | 0.343 | 15 |
| jev_signal_zero | 0.299 | 0.325 | 0.336 | 15 |
| logreg | 0.330 | 0.353 | 0.369 | 15 |
| ma_cross_rule | 0.308 | 0.328 | 0.346 | 15 |
| majority | 0.192 | 0.197 | 0.206 | 15 |
| momentum_rule | 0.310 | 0.332 | 0.343 | 15 |
| random_forest | 0.323 | 0.348 | 0.379 | 15 |
| stratified_random | 0.325 | 0.331 | 0.338 | 15 |

### 20-day horizon

36,465 test observations on 2,431 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.356 | 0.361 | 0.361 | 1.142 | 0.692 | 0.102 | 0.495 | 34/36/30 | 0.0% |
| ma_cross_rule | 0.347 | 0.347 | 0.359 | n/a | n/a | n/a | 0.540 | 22/36/42 | 0.0% |
| jev_plus_controlled_zero | 0.344 | 0.349 | 0.348 | 1.486 | 0.833 | 0.279 | 0.497 | 35/36/29 | 0.0% |
| gbt | 0.342 | 0.346 | 0.346 | 1.547 | 0.852 | 0.297 | 0.492 | 34/36/31 | 0.0% |
| logreg | 0.341 | 0.358 | 0.344 | 1.239 | 0.739 | 0.171 | 0.470 | 44/31/25 | 0.0% |
| jev_head_zero | 0.339 | 0.340 | 0.350 | 1.176 | 0.710 | 0.131 | 0.504 | 27/39/33 | 0.0% |
| momentum_rule | 0.335 | 0.340 | 0.355 | n/a | n/a | n/a | 0.530 | 20/31/49 | 0.0% |
| stratified_random | 0.332 | 0.332 | 0.343 | 1.095 | 0.664 | 0.056 | 0.516 | 25/39/35 | 0.0% |
| jev_signal_zero | 0.331 | 0.331 | 0.341 | 1.386 | 0.804 | 0.262 | 0.514 | 26/41/32 | 0.0% |
| majority | 0.285 | 0.307 | 0.344 | 1.095 | 0.664 | 0.056 | 0.486 | 8/61/31 | 0.0% |

True class distribution: SELL 24.5%, HOLD 39.8%, BUY 35.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.258 | 0.424 | 0.353 | 0.355 | 0.381 | 0.302 | 0.536% | 0.871% | 0.563% |
| jev_head_zero | 0.250 | 0.413 | 0.355 | 0.277 | 0.410 | 0.333 | 0.508% | 0.813% | 0.616% |
| jev_plus_controlled_zero | 0.261 | 0.422 | 0.360 | 0.370 | 0.384 | 0.294 | 0.528% | 0.833% | 0.616% |
| jev_signal_zero | 0.257 | 0.389 | 0.346 | 0.276 | 0.404 | 0.314 | 0.734% | 0.643% | 0.634% |
| logreg | 0.266 | 0.455 | 0.345 | 0.480 | 0.349 | 0.244 | 0.319% | 1.347% | 0.443% |
| ma_cross_rule | 0.277 | 0.412 | 0.357 | 0.251 | 0.373 | 0.418 | 0.758% | 0.735% | 0.554% |
| majority | 0.252 | 0.384 | 0.289 | 0.080 | 0.591 | 0.251 | 0.969% | 0.797% | 0.328% |
| momentum_rule | 0.248 | 0.421 | 0.356 | 0.203 | 0.328 | 0.488 | 1.164% | 0.636% | 0.476% |
| random_forest | 0.273 | 0.447 | 0.356 | 0.379 | 0.406 | 0.299 | 0.365% | 1.129% | 0.443% |
| stratified_random | 0.247 | 0.395 | 0.355 | 0.255 | 0.390 | 0.353 | 0.630% | 0.694% | 0.655% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0095 | -0.0105 to 0.0286 | 0.346 | 1.000 |
| jev_head_zero vs stratified_random | 0.0069 | -0.0036 to 0.0174 | 0.188 | 1.000 |
| jev_plus_controlled_zero vs stratified_random | 0.0117 | -0.0080 to 0.0303 | 0.226 | 1.000 |
| jev_signal_zero vs stratified_random | -0.0016 | -0.0173 to 0.0128 | 0.839 | 1.000 |
| logreg vs stratified_random | 0.0089 | -0.0202 to 0.0381 | 0.549 | 1.000 |
| ma_cross_rule vs stratified_random | 0.0146 | -0.0095 to 0.0361 | 0.196 | 1.000 |
| momentum_rule vs stratified_random | 0.0023 | -0.0211 to 0.0219 | 0.831 | 1.000 |
| random_forest vs stratified_random | 0.0236 | -0.0023 to 0.0496 | 0.071 | 0.572 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.0026 | -0.0199 to 0.0158 | 0.780 | 1.000 |
| jev_plus_controlled_zero vs gbt | 0.0022 | -0.0056 to 0.0108 | 0.586 | 1.000 |
| jev_signal_zero vs gbt | -0.0111 | -0.0325 to 0.0121 | 0.338 | 1.000 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 39 | 8 | 189.9 | 1.0 | 109,905 |
| jev_head_zero | 39 | 8 | 137.5 | 1.2 | 109,905 |
| jev_plus_controlled_zero | 39 | 8 | 248.8 | 1.1 | 109,905 |
| jev_signal_zero | 39 | 1 | 0.1 | 0.0 | 109,905 |
| logreg | 39 | 8 | 12.2 | 0.1 | 109,905 |
| ma_cross_rule | 39 | 6 | 0.5 | 0.0 | 109,905 |
| majority | 39 | 1 | 0.1 | 0.0 | 109,905 |
| momentum_rule | 39 | 8 | 0.7 | 0.0 | 109,905 |
| random_forest | 39 | 8 | 144.7 | 2.1 | 109,905 |
| stratified_random | 39 | 1 | 0.1 | 0.0 | 109,905 |

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

- **Used alone, against the traditional classifier `logreg`:**
  - `jev_signal_zero` vs `logreg`: -0.27 (95% interval -0.76 to +0.18, Holm p 0.546), **no reliable difference**
- **Used alone, against equal-weight buy and hold:**
  - `jev_signal_zero` vs `always_buy`: -0.48 (95% interval -0.80 to -0.19, Holm p 0.017), **worse**
- **Added to a traditional classifier (GBT with its outputs against GBT without):**
  - `jev_plus_controlled_zero` vs `gbt`: -0.07 (95% interval -0.24 to +0.11, Holm p 0.412), **no reliable difference**
- **Used alone against used as an added input:**
  - `jev_signal_zero` vs `jev_plus_controlled_zero`: +0.08 (95% interval -0.46 to +0.54, Holm p 0.774), **no reliable difference**
- **Classification (diagnostic, macro-F1, margin +0.02):**
  - `jev_head_zero` vs `logreg`: -0.01 (95% interval -0.02 to +0.01, Holm p 0.395), **no reliable difference**
  - `jev_plus_controlled_zero` vs `logreg`: -0.02 (95% interval -0.04 to -0.01, Holm p 0.008), **worse**
  - `jev_signal_zero` vs `logreg`: -0.02 (95% interval -0.04 to -0.01, Holm p 0.007), **worse**
- **Overall:** the thesis is not supported. No arm used alone reliably beats both the traditional classifier and buy and hold. Check the detectable-effect section before reading this as evidence of no difference.

- **Operational efficiency:** see the runtime and cost table; reported, not tested.
