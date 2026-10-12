# Experiment report: mixed15_rolling_3m

Generated 2026-10-12T04:34:43+00:00 from commit `115d3d1-dirty`, config `726bd8dd3f98`, dataset `0b91d318b8c2`. Final two years of folds included: **False**.

## 1. Research question and method

Can Jev, used as a classifier, outperform traditional models for trading? Each model's predictions are turned into a portfolio by the same rule and compared on net Sharpe ratio with a traditional classifier, with equal-weight buy and hold, and with a traditional classifier that is given Jev's outputs as extra inputs. Every model is fitted and scored on identical observations in a purged walk-forward design. Classification metrics are reported as diagnostics. The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.

## 2. Data and labels

- Universe: `mixed_15_v2`, 16 tickers obtained including the market proxy SPY; failed downloads: none.
- Source: yfinance daily bars, 2010-01-04 to 2026-09-30, downloaded 2026-10-12T03:12:20+00:00.
- The universe is a fixed list chosen with hindsight, not point-in-time membership. Survivorship bias inflates every absolute return here, including buy and hold of the same assets.
- Prediction after the close of day t; execution at the open of t+1; label return is open(t+1) to open(t+1+h), dividend and split adjusted.
- Labels: BUY / SELL when the forward return is beyond ±0.5 × trailing 60-day volatility × √h, otherwise HOLD.
- Horizons: [1, 5] trading days; primary: 5. Configured but not evaluated: [20] (the validation window was too short after purging).

## 3. Leakage prevention

- Walk-forward folds of 3 months, rolling 3-month training window (exploratory variant), 1-month validation tail used for all tuning.
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
| ma_cross_rule | 100.3% | 7.2% | 0.44 | 0.61 | -30.6% | 0.24 | 15.4 | 100.0% | -0.8% (-7.4% to 5.5%) | 0.59 | 0.47 | 0.39 | 0.07 |
| momentum_rule | 73.7% | 5.7% | 0.38 | 0.52 | -22.2% | 0.26 | 55.1 | 100.0% | -0.4% (-6.5% to 5.8%) | 0.41 | 0.51 | 0.15 | -0.10 |
| logreg | 1.6% | 0.2% | -0.00 | -0.00 | -48.1% | 0.00 | 136.4 | 100.0% | -8.9% (-16.7% to -1.3%) | 0.73 | 0.24 | -0.40 | -0.92 |
| random_forest | -5.1% | -0.5% | -0.06 | -0.08 | -34.5% | -0.02 | 166.1 | 100.0% | -9.4% (-15.8% to -2.8%) | 0.69 | 0.26 | -0.59 | -0.86 |
| jev_plus_controlled_zero | -39.2% | -4.9% | -0.33 | -0.44 | -61.0% | -0.08 | 255.4 | 100.0% | -14.3% (-20.6% to -7.3%) | 0.73 | 0.15 | -1.13 | -1.47 |
| gbt | -38.5% | -4.8% | -0.34 | -0.44 | -63.4% | -0.08 | 215.5 | 100.0% | -13.9% (-20.6% to -7.1%) | 0.71 | 0.08 | -1.02 | -1.51 |
| jev_head_zero | -56.8% | -8.1% | -0.57 | -0.74 | -67.4% | -0.12 | 335.3 | 100.0% | -17.7% (-23.6% to -11.4%) | 0.72 | 0.08 | -1.65 | -2.12 |
| majority | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| stratified_random | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| jev_signal_zero | -69.3% | -11.2% | -0.89 | -1.21 | -72.5% | -0.15 | 346.1 | 100.0% | -18.9% (-25.7% to -12.1%) | 0.52 | -0.15 | -2.13 | -1.95 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.86 | -1.26 to -0.49 | 0.000 | 0.004 |
| jev_head_zero vs always_buy | -1.09 | -1.51 to -0.75 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.86 | -1.23 to -0.53 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -1.41 | -1.99 to -0.88 | 0.000 | 0.004 |
| logreg vs always_buy | -0.53 | -0.93 to -0.18 | 0.006 | 0.024 |
| ma_cross_rule vs always_buy | -0.08 | -0.53 to 0.33 | 0.697 | 1.000 |
| momentum_rule vs always_buy | -0.14 | -0.70 to 0.36 | 0.588 | 1.000 |
| random_forest vs always_buy | -0.58 | -1.01 to -0.18 | 0.006 | 0.024 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.23 | -0.69 to 0.18 | 0.286 | 0.573 |
| jev_plus_controlled_zero vs gbt | 0.00 | -0.28 to 0.29 | 0.983 | 0.983 |
| jev_signal_zero vs gbt | -0.56 | -1.16 to 0.01 | 0.066 | 0.198 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.00 | -0.28 to 0.29 | 0.983 | 0.983 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.56 | -1.13 to -0.01 | 0.054 | 0.054 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| ma_cross_rule | 77.0% | 5.9% | 0.35 | 0.47 | -28.3% | 0.21 | 12.6 | 99.8% | -2.1% (-8.5% to 4.6%) | 0.60 | 0.38 | 0.31 | -0.02 |
| momentum_rule | 62.9% | 5.0% | 0.33 | 0.45 | -15.0% | 0.33 | 22.0 | 99.8% | -1.3% (-6.8% to 4.5%) | 0.43 | 0.38 | 0.24 | -0.20 |
| logreg | 64.2% | 5.1% | 0.30 | 0.42 | -29.7% | 0.17 | 40.7 | 99.8% | -3.2% (-9.0% to 2.8%) | 0.62 | 0.39 | 0.16 | -0.22 |
| majority | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| stratified_random | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| jev_plus_controlled_zero | 42.6% | 3.6% | 0.20 | 0.27 | -34.3% | 0.11 | 51.5 | 99.8% | -5.8% (-11.7% to 0.0%) | 0.73 | 0.30 | 0.03 | -0.66 |
| gbt | 28.6% | 2.6% | 0.13 | 0.18 | -38.0% | 0.07 | 49.1 | 99.8% | -7.1% (-12.3% to -1.5%) | 0.75 | 0.23 | -0.02 | -0.66 |
| jev_signal_zero | 24.6% | 2.2% | 0.11 | 0.14 | -26.5% | 0.08 | 73.0 | 99.8% | -5.3% (-9.6% to -1.0%) | 0.53 | 0.30 | -0.21 | -0.76 |
| jev_head_zero | 16.1% | 1.5% | 0.06 | 0.08 | -37.1% | 0.04 | 67.7 | 99.8% | -7.6% (-13.0% to -2.5%) | 0.69 | 0.21 | -0.18 | -1.24 |
| random_forest | 13.6% | 1.3% | 0.05 | 0.07 | -39.9% | 0.03 | 42.9 | 99.8% | -7.7% (-13.5% to -1.9%) | 0.70 | 0.14 | -0.08 | -0.68 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.39 | -0.72 to -0.11 | 0.016 | 0.082 |
| jev_head_zero vs always_buy | -0.46 | -0.70 to -0.22 | 0.001 | 0.008 |
| jev_plus_controlled_zero vs always_buy | -0.32 | -0.65 to -0.02 | 0.046 | 0.186 |
| jev_signal_zero vs always_buy | -0.41 | -0.72 to -0.14 | 0.008 | 0.056 |
| logreg vs always_buy | -0.22 | -0.65 to 0.16 | 0.299 | 0.898 |
| ma_cross_rule vs always_buy | -0.17 | -0.62 to 0.23 | 0.437 | 0.898 |
| momentum_rule vs always_buy | -0.19 | -0.70 to 0.28 | 0.451 | 0.898 |
| random_forest vs always_buy | -0.47 | -0.83 to -0.13 | 0.009 | 0.056 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.07 | -0.39 to 0.30 | 0.669 | 1.000 |
| jev_plus_controlled_zero vs gbt | 0.07 | -0.11 to 0.25 | 0.451 | 1.000 |
| jev_signal_zero vs gbt | -0.03 | -0.45 to 0.42 | 0.906 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.07 | -0.11 to 0.25 | 0.451 | 0.451 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.10 | -0.53 to 0.35 | 0.668 | 0.668 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a |
| ma_cross_rule | -9.0% | -0.9% | 0.01 | 0.02 | -52.8% | -0.02 | 26.4 | 100.0% | -8.1% (-19.0% to 3.8%) | 0.68 | 0.04 | -0.04 | -0.27 |
| momentum_rule | -24.3% | -2.7% | -0.15 | -0.21 | -49.1% | -0.06 | 98.5 | 100.0% | -5.5% (-17.1% to 5.7%) | 0.22 | 0.01 | -0.43 | -0.21 |
| gbt | -65.1% | -10.0% | -0.43 | -0.58 | -79.4% | -0.13 | 324.5 | 100.0% | -17.9% (-29.0% to -6.0%) | 0.67 | 0.00 | -1.16 | -0.99 |
| logreg | -78.3% | -14.2% | -0.45 | -0.60 | -89.1% | -0.16 | 191.5 | 100.0% | -21.4% (-40.2% to -2.7%) | 0.70 | -0.25 | -0.78 | -1.00 |
| random_forest | -69.6% | -11.3% | -0.50 | -0.66 | -72.2% | -0.16 | 283.1 | 100.0% | -19.3% (-30.8% to -7.2%) | 0.67 | -0.12 | -1.13 | -0.80 |
| jev_plus_controlled_zero | -75.1% | -13.0% | -0.60 | -0.79 | -77.5% | -0.17 | 364.6 | 100.0% | -21.7% (-32.8% to -10.7%) | 0.70 | -0.10 | -1.43 | -0.83 |
| majority | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| stratified_random | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| jev_signal_zero | -88.2% | -19.3% | -0.96 | -1.33 | -89.0% | -0.22 | 456.6 | 100.0% | -26.1% (-38.8% to -13.9%) | 0.44 | -0.33 | -2.03 | -1.39 |
| jev_head_zero | -93.8% | -24.3% | -1.20 | -1.53 | -94.6% | -0.26 | 451.6 | 100.0% | -36.2% (-49.0% to -23.7%) | 0.76 | -0.60 | -2.21 | -1.90 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.96 | -1.60 to -0.37 | 0.004 | 0.016 |
| jev_head_zero vs always_buy | -1.73 | -2.32 to -1.19 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -1.13 | -1.74 to -0.55 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -1.49 | -2.28 to -0.74 | 0.000 | 0.004 |
| logreg vs always_buy | -0.97 | -1.65 to -0.30 | 0.005 | 0.016 |
| ma_cross_rule vs always_buy | -0.51 | -1.16 to 0.02 | 0.084 | 0.168 |
| momentum_rule vs always_buy | -0.68 | -1.50 to 0.06 | 0.088 | 0.168 |
| random_forest vs always_buy | -1.02 | -1.67 to -0.44 | 0.001 | 0.007 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.77 | -1.55 to 0.00 | 0.052 | 0.157 |
| jev_plus_controlled_zero vs gbt | -0.17 | -0.68 to 0.35 | 0.532 | 0.532 |
| jev_signal_zero vs gbt | -0.53 | -1.34 to 0.22 | 0.171 | 0.343 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.17 | -0.68 to 0.35 | 0.532 | 0.532 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.36 | -1.06 to 0.34 | 0.321 | 0.321 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| logreg | 53.5% | 4.4% | 0.23 | 0.32 | -57.2% | 0.08 | 59.8 | 99.8% | -2.1% (-15.7% to 11.8%) | 0.58 | 0.31 | 0.09 | -0.21 |
| ma_cross_rule | 36.3% | 3.2% | 0.18 | 0.25 | -41.9% | 0.08 | 20.0 | 99.8% | -3.7% (-15.0% to 8.8%) | 0.66 | 0.21 | 0.14 | -0.06 |
| gbt | 28.9% | 2.6% | 0.14 | 0.19 | -35.6% | 0.07 | 73.2 | 99.8% | -5.7% (-13.2% to 2.1%) | 0.68 | 0.26 | -0.06 | -0.31 |
| jev_plus_controlled_zero | 23.6% | 2.1% | 0.12 | 0.16 | -33.7% | 0.06 | 74.8 | 99.8% | -6.4% (-14.8% to 2.3%) | 0.71 | 0.24 | -0.08 | -0.41 |
| majority | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| stratified_random | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| random_forest | -8.2% | -0.9% | -0.02 | -0.03 | -59.2% | -0.01 | 69.2 | 99.8% | -9.1% (-18.4% to 0.3%) | 0.71 | 0.08 | -0.19 | -0.22 |
| momentum_rule | -16.4% | -1.8% | -0.12 | -0.16 | -45.8% | -0.04 | 40.1 | 99.8% | -4.6% (-14.2% to 5.8%) | 0.22 | -0.04 | -0.23 | -0.15 |
| jev_signal_zero | -12.8% | -1.4% | -0.18 | -0.24 | -36.1% | -0.04 | 93.2 | 99.8% | -7.5% (-13.7% to -1.4%) | 0.43 | 0.05 | -0.55 | -0.84 |
| jev_head_zero | -28.9% | -3.4% | -0.24 | -0.32 | -49.2% | -0.07 | 89.3 | 99.8% | -12.0% (-19.0% to -4.7%) | 0.67 | -0.07 | -0.52 | -1.05 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.38 | -0.89 to 0.07 | 0.123 | 0.497 |
| jev_head_zero vs always_buy | -0.76 | -1.18 to -0.36 | 0.001 | 0.008 |
| jev_plus_controlled_zero vs always_buy | -0.40 | -0.90 to 0.06 | 0.112 | 0.497 |
| jev_signal_zero vs always_buy | -0.70 | -1.19 to -0.26 | 0.004 | 0.028 |
| logreg vs always_buy | -0.29 | -1.02 to 0.36 | 0.435 | 0.501 |
| ma_cross_rule vs always_buy | -0.34 | -0.93 to 0.19 | 0.250 | 0.501 |
| momentum_rule vs always_buy | -0.64 | -1.39 to 0.08 | 0.099 | 0.497 |
| random_forest vs always_buy | -0.54 | -1.11 to -0.06 | 0.042 | 0.255 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.38 | -0.84 to 0.12 | 0.114 | 0.343 |
| jev_plus_controlled_zero vs gbt | -0.02 | -0.36 to 0.29 | 0.896 | 0.896 |
| jev_signal_zero vs gbt | -0.32 | -0.98 to 0.33 | 0.342 | 0.685 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.02 | -0.36 to 0.29 | 0.896 | 0.896 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.30 | -0.96 to 0.34 | 0.373 | 0.373 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| majority | 34.8% | 3.0% | 0.36 | 0.61 | -6.6% | 0.46 | 0.2 | 2.5% | 0.7% (-1.2% to 2.6%) | 0.06 | 0.36 | 0.36 | 0.04 | 0.36 | -0.0% |
| momentum_rule | 34.1% | 3.0% | 0.31 | 0.43 | -7.9% | 0.38 | 14.6 | 40.8% | -0.2% (-2.7% to 2.0%) | 0.13 | 0.41 | 0.15 | -0.13 | 0.45 | -0.5% |
| ma_cross_rule | 29.7% | 2.6% | 0.24 | 0.33 | -12.0% | 0.22 | 18.3 | 40.1% | -0.5% (-3.0% to 1.9%) | 0.13 | 0.37 | 0.03 | -0.32 | 0.40 | -0.6% |
| logreg | 15.4% | 1.4% | 0.01 | 0.02 | -29.3% | 0.05 | 21.8 | 24.6% | -3.5% (-8.7% to 1.2%) | 0.30 | 0.10 | -0.13 | -0.30 | 0.12 | -0.8% |
| jev_plus_controlled_zero | 7.4% | 0.7% | -0.10 | -0.13 | -24.2% | 0.03 | 55.3 | 27.9% | -4.2% (-7.4% to -0.7%) | 0.29 | 0.14 | -0.50 | -0.98 | 0.37 | -2.9% |
| random_forest | 5.4% | 0.5% | -0.10 | -0.13 | -26.6% | 0.02 | 29.1 | 27.5% | -4.6% (-9.1% to -0.4%) | 0.31 | 0.01 | -0.29 | -0.82 | 0.13 | -1.7% |
| gbt | -2.5% | -0.2% | -0.24 | -0.30 | -23.8% | -0.01 | 52.2 | 28.7% | -5.1% (-8.7% to -1.5%) | 0.28 | -0.01 | -0.61 | -1.07 | 0.24 | -3.1% |
| jev_head_zero | -10.4% | -1.1% | -0.54 | -0.72 | -19.6% | -0.06 | 89.1 | 28.0% | -5.3% (-7.2% to -3.4%) | 0.22 | 0.01 | -1.46 | -1.87 | 0.57 | -4.9% |
| jev_signal_zero | -5.3% | -0.5% | -0.72 | -0.87 | -14.1% | -0.04 | 35.8 | 8.5% | -3.0% (-5.0% to -1.1%) | 0.07 | -0.36 | -1.32 | -0.68 | -0.06 | -2.0% |
| stratified_random | -19.2% | -2.1% | -0.85 | -1.14 | -24.6% | -0.09 | 104.2 | 29.7% | -5.9% (-7.7% to -4.3%) | 0.18 | -0.13 | -2.05 | -2.50 | 0.41 | -5.2% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.76 | -1.19 to -0.39 | 0.002 | 0.015 |
| jev_head_zero vs always_buy | -1.07 | -1.53 to -0.62 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.62 | -1.05 to -0.22 | 0.004 | 0.022 |
| jev_signal_zero vs always_buy | -1.24 | -1.87 to -0.70 | 0.000 | 0.004 |
| logreg vs always_buy | -0.51 | -0.92 to 0.00 | 0.031 | 0.094 |
| ma_cross_rule vs always_buy | -0.28 | -0.88 to 0.32 | 0.370 | 0.741 |
| momentum_rule vs always_buy | -0.21 | -0.78 to 0.33 | 0.466 | 0.741 |
| random_forest vs always_buy | -0.63 | -1.06 to -0.17 | 0.005 | 0.022 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.30 | -0.80 to 0.13 | 0.194 | 0.389 |
| jev_plus_controlled_zero vs gbt | 0.14 | -0.08 to 0.36 | 0.216 | 0.389 |
| jev_signal_zero vs gbt | -0.48 | -1.14 to 0.10 | 0.124 | 0.373 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.14 | -0.08 to 0.36 | 0.216 | 0.216 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.62 | -1.35 to -0.01 | 0.061 | 0.061 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 42.9% | 3.6% | 0.42 | 0.57 | -8.0% | 0.46 | 6.2 | 42.1% | 0.1% (-2.4% to 2.4%) | 0.16 | 0.45 | 0.35 | -0.06 | 0.47 | -0.2% |
| ma_cross_rule | 41.9% | 3.6% | 0.39 | 0.55 | -7.6% | 0.47 | 7.7 | 43.4% | -0.0% (-2.5% to 2.3%) | 0.17 | 0.44 | 0.32 | -0.10 | 0.50 | -0.5% |
| stratified_random | 34.9% | 3.0% | 0.37 | 0.49 | -8.3% | 0.37 | 21.6 | 32.3% | -1.0% (-2.3% to 0.2%) | 0.20 | 0.53 | 0.09 | -0.74 | 0.63 | -1.0% |
| jev_signal_zero | 25.0% | 2.3% | 0.18 | 0.24 | -7.1% | 0.32 | 20.1 | 29.0% | -1.3% (-2.8% to 0.3%) | 0.16 | 0.34 | -0.09 | -0.44 | 0.57 | -1.4% |
| jev_head_zero | 23.9% | 2.2% | 0.14 | 0.18 | -9.8% | 0.22 | 19.1 | 30.8% | -2.0% (-3.5% to -0.4%) | 0.21 | 0.27 | -0.08 | -0.73 | 0.46 | -1.2% |
| random_forest | 23.1% | 2.1% | 0.10 | 0.12 | -24.4% | 0.09 | 9.7 | 30.4% | -2.8% (-6.8% to 0.9%) | 0.29 | 0.14 | 0.03 | -0.34 | 0.22 | -0.7% |
| logreg | 22.4% | 2.0% | 0.09 | 0.11 | -27.8% | 0.07 | 9.2 | 31.6% | -3.1% (-7.9% to 0.9%) | 0.31 | 0.12 | 0.03 | -0.31 | 0.22 | -0.9% |
| jev_plus_controlled_zero | 17.3% | 1.6% | 0.03 | 0.04 | -24.1% | 0.07 | 13.1 | 31.0% | -3.5% (-7.5% to 0.2%) | 0.31 | 0.09 | -0.06 | -0.43 | 0.16 | -0.8% |
| gbt | 16.6% | 1.5% | 0.02 | 0.03 | -23.5% | 0.07 | 12.4 | 31.3% | -3.7% (-7.4% to -0.1%) | 0.31 | 0.07 | -0.06 | -0.39 | 0.17 | -0.9% |
| majority | 12.0% | 1.1% | -0.11 | -0.14 | -10.8% | 0.11 | 0.6 | 9.9% | -1.3% (-3.7% to 0.9%) | 0.07 | -0.11 | -0.12 | -0.50 | -0.10 | -0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.50 | -0.86 to -0.10 | 0.012 | 0.088 |
| jev_head_zero vs always_buy | -0.38 | -0.69 to -0.10 | 0.011 | 0.088 |
| jev_plus_controlled_zero vs always_buy | -0.49 | -0.84 to -0.07 | 0.013 | 0.088 |
| jev_signal_zero vs always_buy | -0.34 | -0.72 to -0.01 | 0.056 | 0.280 |
| logreg vs always_buy | -0.43 | -0.83 to 0.06 | 0.057 | 0.280 |
| ma_cross_rule vs always_buy | -0.13 | -0.66 to 0.38 | 0.621 | 1.000 |
| momentum_rule vs always_buy | -0.10 | -0.64 to 0.38 | 0.708 | 1.000 |
| random_forest vs always_buy | -0.42 | -0.82 to 0.06 | 0.058 | 0.280 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.12 | -0.28 to 0.42 | 0.535 | 1.000 |
| jev_plus_controlled_zero vs gbt | 0.01 | -0.09 to 0.13 | 0.869 | 1.000 |
| jev_signal_zero vs gbt | 0.15 | -0.46 to 0.69 | 0.576 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.01 | -0.09 to 0.13 | 0.869 | 0.869 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.15 | -0.50 to 0.68 | 0.601 | 0.601 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.33 (median of 8 comparisons). A true difference smaller than about 0.47 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

37,710 test observations on 2,514 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.359 | 0.360 | 0.379 | 1.243 | 0.717 | 0.126 | 0.510 | 31/45/25 | 0.0% |
| random_forest | 0.353 | 0.357 | 0.391 | 1.091 | 0.661 | 0.017 | 0.509 | 20/52/28 | 0.0% |
| jev_plus_controlled_zero | 0.341 | 0.341 | 0.357 | 1.319 | 0.779 | 0.227 | 0.501 | 29/43/28 | 0.0% |
| jev_head_zero | 0.340 | 0.340 | 0.364 | 1.235 | 0.738 | 0.176 | 0.512 | 24/48/28 | 0.0% |
| gbt | 0.338 | 0.339 | 0.348 | 1.328 | 0.783 | 0.231 | 0.498 | 33/39/29 | 0.0% |
| momentum_rule | 0.336 | 0.339 | 0.351 | n/a | n/a | n/a | 0.514 | 20/39/41 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.351 | 1.082 | 0.655 | 0.020 | 0.502 | 26/44/30 | 0.0% |
| ma_cross_rule | 0.329 | 0.332 | 0.344 | n/a | n/a | n/a | 0.515 | 20/40/40 | 0.0% |
| jev_signal_zero | 0.290 | 0.341 | 0.419 | 1.513 | 0.807 | 0.257 | 0.505 | 9/82/8 | 0.0% |
| majority | 0.216 | 0.322 | 0.419 | 1.082 | 0.655 | 0.020 | 0.443 | 2/95/3 | 0.0% |

True class distribution: SELL 26.1%, HOLD 44.0%, BUY 29.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.256 | 0.451 | 0.313 | 0.319 | 0.397 | 0.300 | 0.041% | 0.035% | 0.019% |
| jev_head_zero | 0.272 | 0.445 | 0.304 | 0.249 | 0.487 | 0.285 | 0.038% | 0.029% | 0.032% |
| jev_plus_controlled_zero | 0.259 | 0.452 | 0.313 | 0.291 | 0.440 | 0.292 | 0.041% | 0.024% | 0.035% |
| jev_signal_zero | 0.300 | 0.446 | 0.295 | 0.108 | 0.833 | 0.083 | -0.017% | 0.042% | -0.011% |
| logreg | 0.273 | 0.476 | 0.336 | 0.321 | 0.483 | 0.277 | 0.020% | 0.046% | 0.024% |
| ma_cross_rule | 0.288 | 0.432 | 0.285 | 0.223 | 0.390 | 0.382 | 0.054% | 0.027% | 0.026% |
| majority | 0.160 | 0.432 | 0.200 | 0.015 | 0.933 | 0.017 | 0.211% | 0.023% | 0.228% |
| momentum_rule | 0.284 | 0.447 | 0.293 | 0.222 | 0.394 | 0.401 | 0.030% | 0.038% | 0.027% |
| random_forest | 0.269 | 0.471 | 0.328 | 0.206 | 0.562 | 0.302 | 0.063% | 0.030% | 0.014% |
| stratified_random | 0.263 | 0.440 | 0.298 | 0.266 | 0.439 | 0.296 | 0.033% | 0.035% | 0.027% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0038 | -0.0051 to 0.0126 | 0.382 | 0.931 |
| jev_head_zero vs stratified_random | 0.0061 | -0.0004 to 0.0125 | 0.064 | 0.322 |
| jev_plus_controlled_zero vs stratified_random | 0.0071 | -0.0022 to 0.0155 | 0.111 | 0.446 |
| jev_signal_zero vs stratified_random | -0.0440 | -0.0529 to -0.0353 | 0.000 | 0.004 |
| logreg vs stratified_random | 0.0256 | 0.0144 to 0.0364 | 0.000 | 0.004 |
| ma_cross_rule vs stratified_random | -0.0045 | -0.0137 to 0.0042 | 0.310 | 0.931 |
| momentum_rule vs stratified_random | 0.0019 | -0.0075 to 0.0116 | 0.705 | 0.931 |
| random_forest vs stratified_random | 0.0197 | 0.0093 to 0.0295 | 0.000 | 0.004 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.0022 | -0.0057 to 0.0109 | 0.598 | 0.598 |
| jev_plus_controlled_zero vs gbt | 0.0032 | -0.0018 to 0.0086 | 0.204 | 0.408 |
| jev_signal_zero vs gbt | -0.0478 | -0.0576 to -0.0374 | 0.000 | 0.001 |

### 5-day horizon (primary)

37,650 test observations on 2,510 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.349 | 0.349 | 0.359 | 1.392 | 0.756 | 0.190 | 0.504 | 30/38/32 | 0.0% |
| jev_plus_controlled_zero | 0.342 | 0.343 | 0.352 | 1.520 | 0.846 | 0.292 | 0.511 | 30/39/31 | 0.0% |
| random_forest | 0.342 | 0.342 | 0.357 | 1.122 | 0.682 | 0.091 | 0.507 | 27/42/30 | 0.0% |
| gbt | 0.340 | 0.340 | 0.349 | 1.552 | 0.859 | 0.306 | 0.509 | 30/39/31 | 0.0% |
| momentum_rule | 0.338 | 0.340 | 0.351 | n/a | n/a | n/a | 0.526 | 22/36/42 | 0.0% |
| jev_head_zero | 0.338 | 0.338 | 0.357 | 1.288 | 0.763 | 0.203 | 0.504 | 24/45/31 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.347 | 1.096 | 0.665 | 0.045 | 0.512 | 26/42/32 | 0.0% |
| jev_signal_zero | 0.331 | 0.333 | 0.355 | 1.375 | 0.786 | 0.246 | 0.507 | 22/49/29 | 0.0% |
| ma_cross_rule | 0.324 | 0.328 | 0.334 | n/a | n/a | n/a | 0.522 | 22/34/43 | 0.0% |
| majority | 0.253 | 0.317 | 0.381 | 1.096 | 0.665 | 0.045 | 0.461 | 7/83/10 | 0.0% |

True class distribution: SELL 25.4%, HOLD 41.9%, BUY 32.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.243 | 0.429 | 0.353 | 0.287 | 0.395 | 0.338 | 0.197% | 0.196% | 0.082% |
| jev_head_zero | 0.251 | 0.429 | 0.334 | 0.239 | 0.461 | 0.314 | 0.264% | 0.125% | 0.131% |
| jev_plus_controlled_zero | 0.244 | 0.432 | 0.357 | 0.289 | 0.400 | 0.339 | 0.210% | 0.180% | 0.088% |
| jev_signal_zero | 0.269 | 0.417 | 0.313 | 0.228 | 0.493 | 0.277 | 0.185% | 0.159% | 0.144% |
| logreg | 0.247 | 0.450 | 0.357 | 0.296 | 0.407 | 0.345 | 0.138% | 0.227% | 0.102% |
| ma_cross_rule | 0.272 | 0.402 | 0.313 | 0.239 | 0.329 | 0.415 | 0.228% | 0.144% | 0.138% |
| majority | 0.156 | 0.409 | 0.315 | 0.045 | 0.809 | 0.095 | 0.647% | 0.140% | -0.032% |
| momentum_rule | 0.271 | 0.426 | 0.327 | 0.231 | 0.369 | 0.421 | 0.261% | 0.120% | 0.144% |
| random_forest | 0.238 | 0.434 | 0.356 | 0.254 | 0.440 | 0.332 | 0.226% | 0.156% | 0.108% |
| stratified_random | 0.254 | 0.416 | 0.332 | 0.260 | 0.414 | 0.328 | 0.179% | 0.128% | 0.187% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0060 | -0.0061 to 0.0175 | 0.319 | 1.000 |
| jev_head_zero vs stratified_random | 0.0035 | -0.0045 to 0.0120 | 0.390 | 1.000 |
| jev_plus_controlled_zero vs stratified_random | 0.0084 | -0.0045 to 0.0211 | 0.190 | 1.000 |
| jev_signal_zero vs stratified_random | -0.0031 | -0.0134 to 0.0073 | 0.565 | 1.000 |
| logreg vs stratified_random | 0.0152 | -0.0007 to 0.0295 | 0.051 | 0.412 |
| ma_cross_rule vs stratified_random | -0.0096 | -0.0219 to 0.0025 | 0.109 | 0.763 |
| momentum_rule vs stratified_random | 0.0038 | -0.0080 to 0.0153 | 0.534 | 1.000 |
| random_forest vs stratified_random | 0.0080 | -0.0045 to 0.0198 | 0.206 | 1.000 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.0024 | -0.0130 to 0.0083 | 0.675 | 0.768 |
| jev_plus_controlled_zero vs gbt | 0.0024 | -0.0021 to 0.0071 | 0.302 | 0.768 |
| jev_signal_zero vs gbt | -0.0091 | -0.0243 to 0.0064 | 0.256 | 0.768 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,746 | 3,524 | 3,289 | 0 |
| HOLD | 5,178 | 6,229 | 4,358 | 0 |
| BUY | 3,384 | 4,770 | 4,172 | 0 |

`jev_head_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,284 | 4,208 | 3,067 | 0 |
| HOLD | 3,828 | 7,266 | 4,671 | 0 |
| BUY | 2,991 | 5,462 | 3,873 | 0 |

`jev_plus_controlled_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,765 | 3,588 | 3,206 | 0 |
| HOLD | 5,132 | 6,304 | 4,329 | 0 |
| BUY | 3,437 | 4,713 | 4,176 | 0 |

`jev_signal_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,180 | 4,739 | 2,640 | 0 |
| HOLD | 3,120 | 7,767 | 4,878 | 0 |
| BUY | 2,801 | 6,105 | 3,420 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,830 | 3,356 | 3,373 | 0 |
| HOLD | 5,058 | 6,419 | 4,288 | 0 |
| BUY | 3,591 | 4,481 | 4,254 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,285 | 3,372 | 3,902 | 0 |
| HOLD | 3,235 | 5,184 | 7,346 | 0 |
| BUY | 2,876 | 4,330 | 5,120 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 433 | 8,095 | 1,031 | 0 |
| HOLD | 1,493 | 12,756 | 1,516 | 0 |
| BUY | 849 | 10,304 | 1,173 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,212 | 3,508 | 3,839 | 0 |
| HOLD | 3,114 | 5,813 | 6,838 | 0 |
| BUY | 2,825 | 4,310 | 5,191 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,429 | 3,922 | 3,208 | 0 |
| HOLD | 4,656 | 6,932 | 4,177 | 0 |
| BUY | 3,132 | 5,107 | 4,087 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,488 | 4,051 | 3,020 | 0 |
| HOLD | 4,122 | 6,533 | 5,110 | 0 |
| BUY | 3,187 | 5,102 | 4,037 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 | Fold 10 | Fold 11 | Fold 12 | Fold 13 | Fold 14 | Fold 15 | Fold 16 | Fold 17 | Fold 18 | Fold 19 | Fold 20 | Fold 21 | Fold 22 | Fold 23 | Fold 24 | Fold 25 | Fold 26 | Fold 27 | Fold 28 | Fold 29 | Fold 30 | Fold 31 | Fold 32 | Fold 33 | Fold 34 | Fold 35 | Fold 36 | Fold 37 | Fold 38 | Fold 39 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.309 | 0.297 | 0.329 | 0.251 | 0.370 | 0.420 | 0.216 | 0.360 | 0.308 | 0.289 | 0.355 | 0.365 | 0.292 | 0.262 | 0.307 | 0.370 | 0.322 | 0.337 | 0.364 | 0.343 | 0.286 | 0.270 | 0.171 | 0.314 | 0.330 | 0.310 | 0.308 | 0.333 | 0.323 | 0.281 | 0.296 | 0.299 | 0.290 | 0.282 | 0.199 | 0.263 | 0.338 | 0.305 | 0.317 | 0.331 |
| jev_head_zero | 0.311 | 0.312 | 0.340 | 0.367 | 0.346 | 0.347 | 0.291 | 0.372 | 0.358 | 0.321 | 0.334 | 0.357 | 0.331 | 0.313 | 0.328 | 0.353 | 0.321 | 0.257 | 0.316 | 0.320 | 0.348 | 0.267 | 0.289 | 0.289 | 0.358 | 0.333 | 0.332 | 0.360 | 0.315 | 0.310 | 0.340 | 0.321 | 0.309 | 0.326 | 0.306 | 0.329 | 0.325 | 0.339 | 0.330 | 0.358 |
| jev_plus_controlled_zero | 0.324 | 0.317 | 0.304 | 0.295 | 0.359 | 0.399 | 0.211 | 0.332 | 0.315 | 0.288 | 0.364 | 0.377 | 0.300 | 0.259 | 0.329 | 0.368 | 0.332 | 0.341 | 0.345 | 0.364 | 0.276 | 0.300 | 0.181 | 0.349 | 0.309 | 0.297 | 0.307 | 0.330 | 0.323 | 0.271 | 0.276 | 0.306 | 0.269 | 0.297 | 0.257 | 0.240 | 0.385 | 0.324 | 0.305 | 0.370 |
| jev_signal_zero | 0.374 | 0.336 | 0.340 | 0.329 | 0.316 | 0.362 | 0.306 | 0.340 | 0.320 | 0.332 | 0.334 | 0.340 | 0.281 | 0.301 | 0.299 | 0.298 | 0.300 | 0.297 | 0.286 | 0.317 | 0.298 | 0.370 | 0.359 | 0.324 | 0.329 | 0.342 | 0.331 | 0.307 | 0.333 | 0.335 | 0.278 | 0.342 | 0.324 | 0.334 | 0.345 | 0.295 | 0.279 | 0.312 | 0.306 | 0.323 |
| logreg | 0.318 | 0.364 | 0.305 | 0.265 | 0.272 | 0.403 | 0.279 | 0.269 | 0.326 | 0.254 | 0.308 | 0.353 | 0.247 | 0.209 | 0.328 | 0.365 | 0.338 | 0.194 | 0.218 | 0.401 | 0.296 | 0.213 | 0.307 | 0.228 | 0.338 | 0.291 | 0.219 | 0.276 | 0.320 | 0.215 | 0.335 | 0.322 | 0.213 | 0.199 | 0.152 | 0.332 | 0.361 | 0.228 | 0.245 | 0.320 |
| ma_cross_rule | 0.358 | 0.305 | 0.197 | 0.309 | 0.326 | 0.366 | 0.254 | 0.189 | 0.305 | 0.312 | 0.333 | 0.367 | 0.300 | 0.328 | 0.316 | 0.327 | 0.313 | 0.306 | 0.268 | 0.245 | 0.288 | 0.311 | 0.165 | 0.370 | 0.313 | 0.341 | 0.280 | 0.270 | 0.237 | 0.333 | 0.333 | 0.321 | 0.325 | 0.291 | 0.290 | 0.323 | 0.308 | 0.278 | 0.207 | 0.285 |
| majority | 0.165 | 0.137 | 0.221 | 0.180 | 0.212 | 0.189 | 0.195 | 0.228 | 0.202 | 0.213 | 0.193 | 0.196 | 0.177 | 0.160 | 0.162 | 0.184 | 0.158 | 0.062 | 0.178 | 0.203 | 0.224 | 0.126 | 0.066 | 0.222 | 0.206 | 0.201 | 0.218 | 0.201 | 0.191 | 0.167 | 0.133 | 0.183 | 0.204 | 0.193 | 0.222 | 0.171 | 0.176 | 0.182 | 0.191 | 0.160 |
| momentum_rule | 0.381 | 0.348 | 0.318 | 0.361 | 0.374 | 0.361 | 0.363 | 0.309 | 0.321 | 0.296 | 0.300 | 0.339 | 0.358 | 0.328 | 0.293 | 0.345 | 0.322 | 0.289 | 0.236 | 0.304 | 0.262 | 0.358 | 0.118 | 0.357 | 0.325 | 0.375 | 0.296 | 0.304 | 0.277 | 0.354 | 0.337 | 0.383 | 0.335 | 0.310 | 0.261 | 0.293 | 0.302 | 0.292 | 0.226 | 0.302 |
| random_forest | 0.307 | 0.364 | 0.342 | 0.181 | 0.319 | 0.383 | 0.246 | 0.387 | 0.308 | 0.134 | 0.318 | 0.354 | 0.177 | 0.281 | 0.301 | 0.333 | 0.302 | 0.269 | 0.359 | 0.356 | 0.302 | 0.283 | 0.077 | 0.245 | 0.309 | 0.226 | 0.272 | 0.313 | 0.297 | 0.235 | 0.281 | 0.287 | 0.235 | 0.308 | 0.152 | 0.272 | 0.371 | 0.247 | 0.338 | 0.293 |
| stratified_random | 0.339 | 0.351 | 0.348 | 0.326 | 0.340 | 0.347 | 0.340 | 0.339 | 0.338 | 0.350 | 0.316 | 0.324 | 0.314 | 0.299 | 0.320 | 0.313 | 0.355 | 0.301 | 0.317 | 0.331 | 0.341 | 0.298 | 0.255 | 0.303 | 0.328 | 0.316 | 0.348 | 0.320 | 0.339 | 0.355 | 0.354 | 0.356 | 0.340 | 0.313 | 0.318 | 0.325 | 0.347 | 0.325 | 0.347 | 0.306 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.343 | 0.338 | 0.338 |
| jev_head_zero | 0.325 | 0.339 | 0.341 |
| jev_plus_controlled_zero | 0.340 | 0.346 | 0.338 |
| jev_signal_zero | 0.347 | 0.332 | 0.323 |
| logreg | 0.377 | 0.351 | 0.334 |
| ma_cross_rule | 0.315 | 0.323 | 0.317 |
| majority | 0.220 | 0.267 | 0.255 |
| momentum_rule | 0.334 | 0.348 | 0.321 |
| random_forest | 0.333 | 0.348 | 0.338 |
| stratified_random | 0.338 | 0.333 | 0.333 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.326 | 0.339 | 0.355 | 15 |
| jev_head_zero | 0.316 | 0.335 | 0.351 | 15 |
| jev_plus_controlled_zero | 0.331 | 0.341 | 0.356 | 15 |
| jev_signal_zero | 0.300 | 0.326 | 0.341 | 15 |
| logreg | 0.337 | 0.341 | 0.368 | 15 |
| ma_cross_rule | 0.302 | 0.318 | 0.342 | 15 |
| majority | 0.238 | 0.254 | 0.267 | 15 |
| momentum_rule | 0.316 | 0.331 | 0.350 | 15 |
| random_forest | 0.325 | 0.341 | 0.353 | 15 |
| stratified_random | 0.326 | 0.334 | 0.343 | 15 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 80 | 8 | 286.6 | 1.0 | 75,360 |
| jev_head_zero | 80 | 8 | 217.0 | 1.0 | 75,360 |
| jev_plus_controlled_zero | 80 | 8 | 361.0 | 1.0 | 75,360 |
| jev_signal_zero | 80 | 1 | 0.2 | 0.1 | 75,360 |
| logreg | 80 | 8 | 15.5 | 0.1 | 75,360 |
| ma_cross_rule | 80 | 6 | 0.9 | 0.0 | 75,360 |
| majority | 80 | 1 | 0.2 | 0.0 | 75,360 |
| momentum_rule | 80 | 8 | 1.3 | 0.0 | 75,360 |
| random_forest | 80 | 8 | 259.0 | 3.2 | 75,360 |
| stratified_random | 80 | 1 | 0.2 | 0.0 | 75,360 |

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

- **Used alone, against the traditional classifier `gbt`:**
  - `jev_signal_zero` vs `gbt`: -0.03 (95% interval -0.45 to +0.42, Holm p 1.000), **no reliable difference**
- **Used alone, against equal-weight buy and hold:**
  - `jev_signal_zero` vs `always_buy`: -0.41 (95% interval -0.72 to -0.14, Holm p 0.056), **no reliable difference**
- **Added to a traditional classifier (GBT with its outputs against GBT without):**
  - `jev_plus_controlled_zero` vs `gbt`: +0.07 (95% interval -0.11 to +0.25, Holm p 0.451), **no reliable difference**
- **Used alone against used as an added input:**
  - `jev_signal_zero` vs `jev_plus_controlled_zero`: -0.10 (95% interval -0.53 to +0.35, Holm p 0.668), **no reliable difference**
- **Classification (diagnostic, macro-F1, margin +0.02):**
  - `jev_head_zero` vs `gbt`: -0.00 (95% interval -0.01 to +0.01, Holm p 0.768), **no reliable difference**
  - `jev_plus_controlled_zero` vs `gbt`: +0.00 (95% interval -0.00 to +0.01, Holm p 0.768), **no reliable difference**
  - `jev_signal_zero` vs `gbt`: -0.01 (95% interval -0.02 to +0.01, Holm p 0.768), **no reliable difference**
- **Overall:** the thesis is not supported. No arm used alone reliably beats both the traditional classifier and buy and hold. Check the detectable-effect section before reading this as evidence of no difference.

- **Operational efficiency:** see the runtime and cost table; reported, not tested.
