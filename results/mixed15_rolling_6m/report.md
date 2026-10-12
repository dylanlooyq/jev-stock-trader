# Experiment report: mixed15_rolling_6m

Generated 2026-10-12T04:47:18+00:00 from commit `115d3d1-dirty`, config `4d01eb9992d4`, dataset `0b91d318b8c2`. Final two years of folds included: **False**.

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

- Walk-forward folds of 6 months, rolling 6-month training window (exploratory variant), 2-month validation tail used for all tuning.
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
| ma_cross_rule | 89.2% | 6.6% | 0.40 | 0.55 | -23.0% | 0.29 | 17.2 | 100.0% | -0.9% (-8.0% to 5.6%) | 0.55 | 0.43 | 0.34 | 0.01 |
| momentum_rule | 75.2% | 5.8% | 0.38 | 0.52 | -20.9% | 0.28 | 65.1 | 100.0% | -0.6% (-7.1% to 5.8%) | 0.44 | 0.53 | 0.12 | -0.39 |
| random_forest | 1.1% | 0.1% | -0.02 | -0.02 | -48.7% | 0.00 | 179.0 | 100.0% | -8.9% (-14.9% to -2.5%) | 0.70 | 0.32 | -0.58 | -0.78 |
| logreg | -32.5% | -3.9% | -0.26 | -0.35 | -48.9% | -0.08 | 133.0 | 100.0% | -12.7% (-20.2% to -5.3%) | 0.70 | -0.01 | -0.66 | -1.15 |
| jev_plus_controlled_zero | -44.9% | -5.8% | -0.38 | -0.49 | -57.7% | -0.10 | 262.2 | 100.0% | -15.2% (-21.7% to -8.1%) | 0.73 | 0.10 | -1.17 | -1.78 |
| gbt | -50.5% | -6.8% | -0.46 | -0.61 | -59.2% | -0.11 | 225.3 | 100.0% | -16.1% (-22.2% to -9.7%) | 0.71 | -0.04 | -1.17 | -1.90 |
| jev_head_zero | -63.4% | -9.6% | -0.68 | -0.88 | -70.9% | -0.14 | 333.7 | 100.0% | -19.0% (-25.7% to -12.7%) | 0.70 | -0.03 | -1.75 | -2.47 |
| majority | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| stratified_random | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-25.9% to -12.5%) | 0.69 | 0.02 | -1.89 | -2.51 |
| jev_signal_zero | -69.3% | -11.2% | -0.89 | -1.21 | -72.5% | -0.15 | 346.1 | 100.0% | -18.9% (-25.7% to -12.1%) | 0.52 | -0.15 | -2.13 | -1.95 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.99 | -1.38 to -0.65 | 0.000 | 0.004 |
| jev_head_zero vs always_buy | -1.20 | -1.60 to -0.85 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.90 | -1.28 to -0.56 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -1.41 | -1.99 to -0.88 | 0.000 | 0.004 |
| logreg vs always_buy | -0.78 | -1.26 to -0.36 | 0.001 | 0.004 |
| ma_cross_rule vs always_buy | -0.12 | -0.62 to 0.36 | 0.609 | 1.000 |
| momentum_rule vs always_buy | -0.15 | -0.70 to 0.38 | 0.605 | 1.000 |
| random_forest vs always_buy | -0.54 | -0.95 to -0.16 | 0.010 | 0.030 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.21 | -0.66 to 0.23 | 0.342 | 0.685 |
| jev_plus_controlled_zero vs gbt | 0.09 | -0.21 to 0.40 | 0.582 | 0.685 |
| jev_signal_zero vs gbt | -0.43 | -1.03 to 0.16 | 0.143 | 0.429 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.09 | -0.21 to 0.40 | 0.582 | 0.582 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.51 | -1.15 to 0.07 | 0.098 | 0.098 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| momentum_rule | 117.3% | 8.1% | 0.53 | 0.74 | -21.5% | 0.38 | 21.2 | 99.8% | 1.1% (-5.3% to 7.7%) | 0.48 | 0.58 | 0.45 | -0.14 |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| ma_cross_rule | 105.3% | 7.5% | 0.45 | 0.62 | -21.2% | 0.35 | 12.6 | 99.8% | -0.3% (-6.6% to 6.2%) | 0.57 | 0.48 | 0.41 | 0.14 |
| gbt | 76.9% | 5.9% | 0.35 | 0.49 | -26.9% | 0.22 | 48.6 | 99.8% | -2.9% (-8.4% to 2.6%) | 0.66 | 0.46 | 0.19 | -0.37 |
| random_forest | 50.4% | 4.2% | 0.25 | 0.34 | -22.6% | 0.18 | 44.9 | 99.8% | -4.3% (-8.9% to 0.3%) | 0.63 | 0.35 | 0.08 | -0.28 |
| jev_plus_controlled_zero | 44.8% | 3.8% | 0.22 | 0.29 | -29.4% | 0.13 | 49.8 | 99.8% | -5.0% (-10.7% to 0.3%) | 0.66 | 0.32 | 0.04 | -0.51 |
| majority | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| stratified_random | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-9.7% to -1.5%) | 0.68 | 0.37 | -0.07 | -1.37 |
| logreg | 40.6% | 3.5% | 0.20 | 0.27 | -23.8% | 0.15 | 38.3 | 99.8% | -4.4% (-9.9% to 1.0%) | 0.58 | 0.28 | 0.06 | -0.34 |
| jev_head_zero | 35.0% | 3.1% | 0.17 | 0.23 | -35.9% | 0.09 | 68.7 | 99.8% | -6.1% (-10.9% to -1.5%) | 0.69 | 0.32 | -0.08 | -0.83 |
| jev_signal_zero | 24.6% | 2.2% | 0.11 | 0.14 | -26.5% | 0.08 | 73.0 | 99.8% | -5.3% (-9.6% to -1.0%) | 0.53 | 0.30 | -0.21 | -0.76 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.17 | -0.55 to 0.17 | 0.378 | 1.000 |
| jev_head_zero vs always_buy | -0.35 | -0.57 to -0.13 | 0.002 | 0.016 |
| jev_plus_controlled_zero vs always_buy | -0.31 | -0.69 to 0.02 | 0.092 | 0.555 |
| jev_signal_zero vs always_buy | -0.41 | -0.72 to -0.14 | 0.008 | 0.056 |
| logreg vs always_buy | -0.32 | -0.74 to 0.04 | 0.103 | 0.555 |
| ma_cross_rule vs always_buy | -0.07 | -0.51 to 0.34 | 0.753 | 1.000 |
| momentum_rule vs always_buy | 0.01 | -0.54 to 0.54 | 0.975 | 1.000 |
| random_forest vs always_buy | -0.27 | -0.65 to 0.06 | 0.133 | 0.555 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.03 | -0.41 to 0.41 | 0.896 | 1.000 |
| jev_plus_controlled_zero vs logreg | 0.02 | -0.37 to 0.39 | 0.921 | 1.000 |
| jev_signal_zero vs logreg | -0.09 | -0.55 to 0.38 | 0.708 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.14 | -0.29 to 0.04 | 0.096 | 0.096 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.11 | -0.59 to 0.38 | 0.659 | 0.659 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a |
| random_forest | 34.4% | 3.0% | 0.17 | 0.24 | -51.4% | 0.06 | 285.9 | 100.0% | -4.1% (-14.8% to 6.8%) | 0.65 | 0.55 | -0.47 | -0.44 |
| ma_cross_rule | 29.5% | 2.6% | 0.16 | 0.22 | -43.0% | 0.06 | 27.2 | 100.0% | -2.4% (-14.5% to 9.4%) | 0.50 | 0.19 | 0.10 | -0.23 |
| momentum_rule | -23.9% | -2.7% | -0.12 | -0.17 | -48.2% | -0.06 | 107.3 | 100.0% | -5.9% (-17.3% to 4.7%) | 0.28 | 0.04 | -0.40 | -0.36 |
| jev_plus_controlled_zero | -60.4% | -8.9% | -0.33 | -0.45 | -79.0% | -0.11 | 374.4 | 100.0% | -16.9% (-29.4% to -3.8%) | 0.74 | 0.14 | -1.09 | -1.30 |
| logreg | -74.6% | -12.8% | -0.40 | -0.56 | -75.4% | -0.17 | 195.1 | 100.0% | -19.6% (-35.8% to -3.8%) | 0.68 | -0.19 | -0.74 | -0.95 |
| jev_head_zero | -71.5% | -11.8% | -0.47 | -0.63 | -76.0% | -0.16 | 437.4 | 100.0% | -20.1% (-32.7% to -7.3%) | 0.72 | 0.08 | -1.37 | -1.27 |
| gbt | -82.7% | -16.1% | -0.63 | -0.84 | -85.5% | -0.19 | 334.6 | 100.0% | -25.2% (-38.3% to -11.6%) | 0.75 | -0.24 | -1.29 | -1.07 |
| majority | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| stratified_random | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.9% to -13.5%) | 0.70 | -0.09 | -1.78 | -1.98 |
| jev_signal_zero | -88.2% | -19.3% | -0.96 | -1.33 | -89.0% | -0.22 | 456.6 | 100.0% | -26.1% (-38.8% to -13.9%) | 0.44 | -0.33 | -2.03 | -1.39 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -1.16 | -1.77 to -0.59 | 0.000 | 0.004 |
| jev_head_zero vs always_buy | -0.99 | -1.64 to -0.41 | 0.003 | 0.018 |
| jev_plus_controlled_zero vs always_buy | -0.85 | -1.47 to -0.34 | 0.004 | 0.020 |
| jev_signal_zero vs always_buy | -1.49 | -2.28 to -0.74 | 0.000 | 0.004 |
| logreg vs always_buy | -0.92 | -1.61 to -0.28 | 0.010 | 0.040 |
| ma_cross_rule vs always_buy | -0.36 | -1.01 to 0.19 | 0.233 | 0.419 |
| momentum_rule vs always_buy | -0.65 | -1.39 to 0.05 | 0.079 | 0.237 |
| random_forest vs always_buy | -0.35 | -0.98 to 0.16 | 0.209 | 0.419 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | 0.16 | -0.48 to 0.81 | 0.620 | 0.847 |
| jev_plus_controlled_zero vs gbt | 0.31 | -0.23 to 0.87 | 0.282 | 0.847 |
| jev_signal_zero vs gbt | -0.33 | -1.10 to 0.41 | 0.409 | 0.847 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | 0.31 | -0.23 to 0.87 | 0.282 | 0.282 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.64 | -1.48 to 0.19 | 0.142 | 0.142 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| gbt | 124.5% | 8.4% | 0.44 | 0.66 | -35.5% | 0.24 | 71.0 | 99.8% | 1.4% (-7.3% to 10.5%) | 0.55 | 0.56 | 0.25 | 0.10 |
| random_forest | 84.5% | 6.3% | 0.34 | 0.47 | -37.3% | 0.17 | 68.8 | 99.8% | -0.8% (-9.8% to 7.9%) | 0.57 | 0.45 | 0.15 | 0.20 |
| logreg | 64.3% | 5.1% | 0.26 | 0.38 | -47.9% | 0.11 | 58.0 | 99.8% | -0.4% (-13.6% to 11.4%) | 0.50 | 0.34 | 0.13 | 0.13 |
| momentum_rule | 48.4% | 4.0% | 0.22 | 0.30 | -37.4% | 0.11 | 36.2 | 99.8% | -0.6% (-10.7% to 9.5%) | 0.39 | 0.27 | 0.12 | -0.07 |
| jev_plus_controlled_zero | 28.3% | 2.5% | 0.14 | 0.20 | -35.9% | 0.07 | 73.0 | 99.8% | -4.9% (-13.7% to 3.5%) | 0.61 | 0.26 | -0.06 | -0.21 |
| majority | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| stratified_random | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-14.8% to -1.3%) | 0.69 | 0.23 | -0.26 | -1.02 |
| ma_cross_rule | -11.4% | -1.2% | -0.00 | -0.00 | -42.0% | -0.03 | 21.3 | 99.8% | -7.2% (-18.8% to 4.8%) | 0.58 | 0.02 | -0.05 | -0.07 |
| jev_head_zero | -18.9% | -2.1% | -0.12 | -0.16 | -54.5% | -0.04 | 91.0 | 99.8% | -11.0% (-19.9% to -2.5%) | 0.72 | 0.03 | -0.37 | -0.58 |
| jev_signal_zero | -12.8% | -1.4% | -0.18 | -0.24 | -36.1% | -0.04 | 93.2 | 99.8% | -7.5% (-13.7% to -1.4%) | 0.43 | 0.05 | -0.55 | -0.84 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.08 | -0.69 to 0.52 | 0.808 | 1.000 |
| jev_head_zero vs always_buy | -0.64 | -1.03 to -0.24 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.38 | -0.94 to 0.14 | 0.172 | 0.862 |
| jev_signal_zero vs always_buy | -0.70 | -1.19 to -0.26 | 0.004 | 0.028 |
| logreg vs always_buy | -0.26 | -0.96 to 0.43 | 0.453 | 1.000 |
| ma_cross_rule vs always_buy | -0.52 | -1.14 to 0.03 | 0.079 | 0.474 |
| momentum_rule vs always_buy | -0.30 | -0.96 to 0.32 | 0.367 | 1.000 |
| random_forest vs always_buy | -0.18 | -0.80 to 0.42 | 0.557 | 1.000 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.38 | -1.11 to 0.38 | 0.328 | 0.784 |
| jev_plus_controlled_zero vs logreg | -0.12 | -0.74 to 0.51 | 0.696 | 0.784 |
| jev_signal_zero vs logreg | -0.44 | -1.19 to 0.36 | 0.261 | 0.784 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.31 | -0.65 to 0.03 | 0.072 | 0.072 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.31 | -0.97 to 0.35 | 0.354 | 0.354 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| ma_cross_rule | 31.8% | 2.8% | 0.27 | 0.37 | -7.8% | 0.36 | 17.6 | 40.4% | -0.4% (-3.2% to 2.0%) | 0.14 | 0.38 | 0.08 | -0.18 | 0.37 | -0.4% |
| momentum_rule | 30.5% | 2.7% | 0.23 | 0.31 | -8.8% | 0.31 | 17.4 | 42.1% | -0.9% (-3.4% to 1.6%) | 0.17 | 0.33 | 0.06 | -0.26 | 0.41 | -0.8% |
| random_forest | 28.0% | 2.5% | 0.14 | 0.18 | -26.6% | 0.09 | 37.3 | 32.8% | -3.3% (-7.5% to 0.7%) | 0.37 | 0.27 | -0.08 | -0.38 | 0.29 | -1.2% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| logreg | 0.9% | 0.1% | -0.16 | -0.20 | -28.9% | 0.00 | 24.8 | 26.7% | -5.0% (-9.4% to -0.7%) | 0.30 | -0.06 | -0.32 | -0.56 | 0.04 | -1.5% |
| gbt | -16.2% | -1.8% | -0.42 | -0.52 | -35.4% | -0.05 | 53.7 | 27.4% | -6.9% (-10.8% to -3.1%) | 0.30 | -0.21 | -0.79 | -1.26 | -0.02 | -3.0% |
| jev_plus_controlled_zero | -18.5% | -2.0% | -0.46 | -0.56 | -34.4% | -0.06 | 60.1 | 27.7% | -7.2% (-11.2% to -3.4%) | 0.31 | -0.22 | -0.87 | -1.45 | -0.04 | -3.1% |
| stratified_random | -8.6% | -0.9% | -0.55 | -0.72 | -17.0% | -0.05 | 104.7 | 29.6% | -4.9% (-6.8% to -3.0%) | 0.20 | 0.15 | -1.71 | -1.89 | 0.45 | -4.3% |
| jev_head_zero | -14.5% | -1.6% | -0.57 | -0.72 | -25.6% | -0.06 | 91.7 | 29.0% | -5.9% (-8.3% to -3.6%) | 0.23 | -0.06 | -1.42 | -1.96 | 0.31 | -4.5% |
| jev_signal_zero | -5.3% | -0.5% | -0.72 | -0.87 | -14.1% | -0.04 | 35.8 | 8.5% | -3.0% (-5.0% to -1.1%) | 0.07 | -0.36 | -1.32 | -0.68 | -0.06 | -2.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.95 | -1.38 to -0.57 | 0.000 | 0.004 |
| jev_head_zero vs always_buy | -1.09 | -1.49 to -0.74 | 0.000 | 0.004 |
| jev_plus_controlled_zero vs always_buy | -0.99 | -1.40 to -0.60 | 0.000 | 0.004 |
| jev_signal_zero vs always_buy | -1.24 | -1.87 to -0.70 | 0.000 | 0.004 |
| logreg vs always_buy | -0.68 | -1.09 to -0.27 | 0.002 | 0.008 |
| ma_cross_rule vs always_buy | -0.26 | -0.85 to 0.34 | 0.398 | 0.510 |
| momentum_rule vs always_buy | -0.30 | -0.82 to 0.20 | 0.255 | 0.510 |
| random_forest vs always_buy | -0.38 | -0.77 to 0.04 | 0.059 | 0.178 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.15 | -0.58 to 0.27 | 0.519 | 1.000 |
| jev_plus_controlled_zero vs gbt | -0.04 | -0.30 to 0.22 | 0.753 | 1.000 |
| jev_signal_zero vs gbt | -0.30 | -0.96 to 0.30 | 0.352 | 1.000 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.04 | -0.30 to 0.22 | 0.753 | 0.753 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | -0.26 | -0.94 to 0.31 | 0.389 | 0.389 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 47.4% | 4.0% | 0.46 | 0.63 | -7.0% | 0.57 | 6.3 | 43.8% | 0.2% (-2.4% to 2.8%) | 0.18 | 0.50 | 0.40 | -0.13 | 0.41 | 0.4% |
| ma_cross_rule | 35.9% | 3.1% | 0.34 | 0.46 | -6.5% | 0.48 | 9.0 | 41.6% | -0.3% (-2.6% to 1.8%) | 0.15 | 0.40 | 0.24 | 0.14 | 0.43 | -0.4% |
| logreg | 39.0% | 3.4% | 0.31 | 0.42 | -14.4% | 0.23 | 8.7 | 28.3% | -1.0% (-3.8% to 1.6%) | 0.23 | 0.35 | 0.23 | -0.16 | 0.30 | -0.0% |
| majority | 23.4% | 2.1% | 0.29 | 0.45 | -2.4% | 0.91 | 0.2 | 5.0% | 0.3% (-0.3% to 1.0%) | 0.01 | 0.30 | 0.29 | 0.29 | 0.30 | -0.0% |
| jev_signal_zero | 25.0% | 2.3% | 0.18 | 0.24 | -7.1% | 0.32 | 20.1 | 29.0% | -1.3% (-2.8% to 0.3%) | 0.16 | 0.34 | -0.09 | -0.44 | 0.57 | -1.4% |
| jev_head_zero | 24.7% | 2.2% | 0.15 | 0.20 | -12.4% | 0.18 | 19.9 | 31.4% | -2.1% (-3.7% to -0.6%) | 0.23 | 0.27 | -0.07 | -0.70 | 0.48 | -1.4% |
| gbt | 25.7% | 2.3% | 0.13 | 0.16 | -21.1% | 0.11 | 13.0 | 33.3% | -2.9% (-6.2% to 0.1%) | 0.31 | 0.18 | 0.04 | -0.33 | 0.21 | -0.5% |
| jev_plus_controlled_zero | 24.7% | 2.2% | 0.11 | 0.15 | -24.0% | 0.09 | 12.6 | 32.9% | -3.1% (-6.7% to 0.4%) | 0.32 | 0.17 | 0.03 | -0.38 | 0.21 | -0.6% |
| random_forest | 23.3% | 2.1% | 0.10 | 0.12 | -25.7% | 0.08 | 10.3 | 31.3% | -3.2% (-7.4% to 0.5%) | 0.32 | 0.14 | 0.03 | -0.34 | 0.12 | -0.2% |
| stratified_random | 12.9% | 1.2% | -0.08 | -0.11 | -11.4% | 0.11 | 21.8 | 32.2% | -2.9% (-4.5% to -1.6%) | 0.21 | 0.07 | -0.35 | -1.58 | 0.35 | -1.8% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.39 | -0.74 to -0.01 | 0.040 | 0.269 |
| jev_head_zero vs always_buy | -0.38 | -0.65 to -0.13 | 0.007 | 0.056 |
| jev_plus_controlled_zero vs always_buy | -0.41 | -0.75 to 0.00 | 0.038 | 0.269 |
| jev_signal_zero vs always_buy | -0.34 | -0.72 to -0.01 | 0.056 | 0.269 |
| logreg vs always_buy | -0.22 | -0.67 to 0.26 | 0.359 | 1.000 |
| ma_cross_rule vs always_buy | -0.18 | -0.72 to 0.29 | 0.459 | 1.000 |
| momentum_rule vs always_buy | -0.06 | -0.60 to 0.43 | 0.823 | 1.000 |
| random_forest vs always_buy | -0.42 | -0.80 to 0.03 | 0.048 | 0.269 |

Jev (TypeSafe jev-1.13.0), against the reference traditional classifier (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.16 | -0.59 to 0.27 | 0.473 | 0.947 |
| jev_plus_controlled_zero vs logreg | -0.19 | -0.53 to 0.21 | 0.298 | 0.894 |
| jev_signal_zero vs logreg | -0.13 | -0.80 to 0.48 | 0.679 | 0.947 |

Jev (TypeSafe jev-1.13.0), added to GBT, against GBT alone (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_plus_controlled_zero vs gbt | -0.01 | -0.14 to 0.13 | 0.854 | 0.854 |

Jev (TypeSafe jev-1.13.0), used alone against used as an added input (net Sharpe difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_signal_zero vs jev_plus_controlled_zero | 0.06 | -0.57 to 0.58 | 0.823 | 0.823 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.36 (median of 8 comparisons). A true difference smaller than about 0.51 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

37,710 test observations on 2,514 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.362 | 0.363 | 0.384 | 1.093 | 0.662 | 0.009 | 0.510 | 24/43/33 | 0.0% |
| logreg | 0.361 | 0.362 | 0.390 | 1.121 | 0.674 | 0.060 | 0.497 | 25/48/27 | 0.0% |
| gbt | 0.347 | 0.348 | 0.362 | 1.201 | 0.724 | 0.155 | 0.499 | 31/41/27 | 0.0% |
| jev_plus_controlled_zero | 0.346 | 0.347 | 0.359 | 1.205 | 0.727 | 0.162 | 0.497 | 32/40/28 | 0.0% |
| jev_head_zero | 0.342 | 0.342 | 0.366 | 1.163 | 0.703 | 0.124 | 0.504 | 24/47/29 | 0.0% |
| stratified_random | 0.336 | 0.336 | 0.354 | 1.077 | 0.652 | 0.018 | 0.511 | 26/44/30 | 0.0% |
| momentum_rule | 0.336 | 0.340 | 0.349 | n/a | n/a | n/a | 0.515 | 21/37/42 | 0.0% |
| ma_cross_rule | 0.329 | 0.331 | 0.342 | n/a | n/a | n/a | 0.516 | 21/39/40 | 0.0% |
| jev_signal_zero | 0.290 | 0.341 | 0.419 | 1.513 | 0.807 | 0.257 | 0.505 | 9/82/8 | 0.0% |
| majority | 0.204 | 0.333 | 0.440 | 1.077 | 0.652 | 0.018 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 26.1%, HOLD 44.0%, BUY 29.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.260 | 0.466 | 0.321 | 0.310 | 0.438 | 0.295 | 0.045% | 0.044% | -0.001% |
| jev_head_zero | 0.266 | 0.453 | 0.307 | 0.241 | 0.488 | 0.297 | 0.043% | 0.030% | 0.027% |
| jev_plus_controlled_zero | 0.262 | 0.466 | 0.317 | 0.322 | 0.427 | 0.293 | 0.052% | 0.039% | -0.000% |
| jev_signal_zero | 0.300 | 0.446 | 0.295 | 0.108 | 0.833 | 0.083 | -0.017% | 0.042% | -0.011% |
| logreg | 0.274 | 0.486 | 0.325 | 0.260 | 0.536 | 0.291 | 0.027% | 0.050% | 0.006% |
| ma_cross_rule | 0.289 | 0.430 | 0.284 | 0.227 | 0.383 | 0.383 | 0.035% | 0.036% | 0.027% |
| majority | 0.000 | 0.440 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.032% | n/a |
| momentum_rule | 0.287 | 0.448 | 0.293 | 0.233 | 0.374 | 0.413 | 0.045% | 0.032% | 0.026% |
| random_forest | 0.269 | 0.488 | 0.331 | 0.246 | 0.481 | 0.363 | 0.042% | 0.019% | 0.042% |
| stratified_random | 0.265 | 0.440 | 0.305 | 0.265 | 0.442 | 0.302 | 0.014% | 0.035% | 0.044% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0107 | 0.0017 to 0.0189 | 0.014 | 0.072 |
| jev_head_zero vs stratified_random | 0.0051 | -0.0032 to 0.0130 | 0.203 | 0.406 |
| jev_plus_controlled_zero vs stratified_random | 0.0099 | 0.0005 to 0.0188 | 0.032 | 0.130 |
| jev_signal_zero vs stratified_random | -0.0468 | -0.0555 to -0.0382 | 0.000 | 0.004 |
| logreg vs stratified_random | 0.0246 | 0.0141 to 0.0345 | 0.000 | 0.004 |
| ma_cross_rule vs stratified_random | -0.0079 | -0.0175 to 0.0011 | 0.098 | 0.294 |
| momentum_rule vs stratified_random | -0.0006 | -0.0096 to 0.0075 | 0.891 | 0.891 |
| random_forest vs stratified_random | 0.0260 | 0.0157 to 0.0352 | 0.000 | 0.004 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs gbt | -0.0057 | -0.0130 to 0.0022 | 0.153 | 0.306 |
| jev_plus_controlled_zero vs gbt | -0.0009 | -0.0067 to 0.0047 | 0.761 | 0.761 |
| jev_signal_zero vs gbt | -0.0575 | -0.0662 to -0.0478 | 0.000 | 0.001 |

### 5-day horizon (primary)

37,650 test observations on 2,510 dates. Reference traditional classifier (chosen on validation data): **logreg**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.350 | 0.355 | 0.356 | 1.231 | 0.723 | 0.148 | 0.503 | 36/35/28 | 0.0% |
| random_forest | 0.345 | 0.344 | 0.359 | 1.115 | 0.678 | 0.079 | 0.502 | 27/41/31 | 0.0% |
| jev_head_zero | 0.344 | 0.344 | 0.360 | 1.199 | 0.723 | 0.156 | 0.505 | 25/43/31 | 0.0% |
| jev_plus_controlled_zero | 0.341 | 0.342 | 0.348 | 1.304 | 0.773 | 0.217 | 0.508 | 31/36/33 | 0.0% |
| gbt | 0.338 | 0.340 | 0.343 | 1.364 | 0.801 | 0.250 | 0.500 | 33/34/33 | 0.0% |
| ma_cross_rule | 0.335 | 0.336 | 0.347 | n/a | n/a | n/a | 0.530 | 20/38/42 | 0.0% |
| momentum_rule | 0.333 | 0.337 | 0.348 | n/a | n/a | n/a | 0.523 | 21/35/44 | 0.0% |
| jev_signal_zero | 0.331 | 0.333 | 0.355 | 1.375 | 0.786 | 0.246 | 0.507 | 22/49/29 | 0.0% |
| stratified_random | 0.330 | 0.330 | 0.344 | 1.085 | 0.657 | 0.036 | 0.496 | 26/42/32 | 0.0% |
| majority | 0.224 | 0.334 | 0.414 | 1.085 | 0.657 | 0.036 | 0.581 | 0/95/5 | 0.0% |

True class distribution: SELL 25.4%, HOLD 41.9%, BUY 32.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.245 | 0.436 | 0.345 | 0.318 | 0.350 | 0.352 | 0.217% | 0.145% | 0.120% |
| jev_head_zero | 0.257 | 0.438 | 0.336 | 0.258 | 0.450 | 0.323 | 0.176% | 0.168% | 0.138% |
| jev_plus_controlled_zero | 0.248 | 0.434 | 0.348 | 0.304 | 0.372 | 0.350 | 0.228% | 0.139% | 0.119% |
| jev_signal_zero | 0.269 | 0.417 | 0.313 | 0.228 | 0.493 | 0.277 | 0.185% | 0.159% | 0.144% |
| logreg | 0.265 | 0.453 | 0.350 | 0.377 | 0.384 | 0.303 | 0.099% | 0.205% | 0.182% |
| ma_cross_rule | 0.295 | 0.413 | 0.312 | 0.236 | 0.375 | 0.397 | 0.071% | 0.246% | 0.126% |
| majority | 0.000 | 0.419 | 0.336 | 0.000 | 0.949 | 0.052 | n/a | 0.157% | 0.229% |
| momentum_rule | 0.266 | 0.425 | 0.325 | 0.221 | 0.356 | 0.436 | 0.322% | 0.071% | 0.154% |
| random_forest | 0.239 | 0.443 | 0.353 | 0.257 | 0.438 | 0.338 | 0.263% | 0.134% | 0.106% |
| stratified_random | 0.250 | 0.421 | 0.321 | 0.256 | 0.419 | 0.316 | 0.186% | 0.209% | 0.077% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0075 | -0.0063 to 0.0212 | 0.277 | 1.000 |
| jev_head_zero vs stratified_random | 0.0132 | 0.0055 to 0.0208 | 0.001 | 0.008 |
| jev_plus_controlled_zero vs stratified_random | 0.0106 | -0.0030 to 0.0246 | 0.121 | 0.607 |
| jev_signal_zero vs stratified_random | 0.0005 | -0.0095 to 0.0100 | 0.932 | 1.000 |
| logreg vs stratified_random | 0.0199 | 0.0044 to 0.0356 | 0.013 | 0.091 |
| ma_cross_rule vs stratified_random | 0.0043 | -0.0078 to 0.0157 | 0.470 | 1.000 |
| momentum_rule vs stratified_random | 0.0030 | -0.0093 to 0.0154 | 0.612 | 1.000 |
| random_forest vs stratified_random | 0.0141 | 0.0006 to 0.0274 | 0.041 | 0.249 |

Jev (TypeSafe jev-1.13.0) against the reference classifier (macro-F1 difference):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| jev_head_zero vs logreg | -0.0068 | -0.0206 to 0.0078 | 0.352 | 0.450 |
| jev_plus_controlled_zero vs logreg | -0.0093 | -0.0244 to 0.0054 | 0.225 | 0.450 |
| jev_signal_zero vs logreg | -0.0195 | -0.0365 to -0.0029 | 0.022 | 0.067 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 3,041 | 3,078 | 3,440 | 0 |
| HOLD | 5,457 | 5,525 | 4,783 | 0 |
| BUY | 3,930 | 4,059 | 4,337 | 0 |

`jev_head_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,463 | 3,963 | 3,133 | 0 |
| HOLD | 3,925 | 7,101 | 4,739 | 0 |
| BUY | 3,182 | 5,161 | 3,983 | 0 |

`jev_plus_controlled_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,910 | 3,343 | 3,306 | 0 |
| HOLD | 5,128 | 5,866 | 4,771 | 0 |
| BUY | 3,704 | 4,304 | 4,318 | 0 |

`jev_signal_zero`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,180 | 4,739 | 2,640 | 0 |
| HOLD | 3,120 | 7,767 | 4,878 | 0 |
| BUY | 2,801 | 6,105 | 3,420 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 3,606 | 3,104 | 2,849 | 0 |
| HOLD | 5,634 | 6,050 | 4,081 | 0 |
| BUY | 4,389 | 4,205 | 3,732 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,257 | 3,557 | 3,745 | 0 |
| HOLD | 2,797 | 5,905 | 7,063 | 0 |
| BUY | 2,591 | 4,845 | 4,890 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 9,096 | 463 | 0 |
| HOLD | 0 | 14,964 | 801 | 0 |
| BUY | 0 | 11,685 | 641 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,108 | 3,444 | 4,007 | 0 |
| HOLD | 2,993 | 5,608 | 7,164 | 0 |
| BUY | 2,825 | 4,133 | 5,368 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,454 | 3,802 | 3,303 | 0 |
| HOLD | 4,531 | 6,903 | 4,331 | 0 |
| BUY | 3,271 | 4,884 | 4,171 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,448 | 3,890 | 3,221 | 0 |
| HOLD | 4,130 | 6,609 | 5,026 | 0 |
| BUY | 3,213 | 5,217 | 3,896 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 | Fold 10 | Fold 11 | Fold 12 | Fold 13 | Fold 14 | Fold 15 | Fold 16 | Fold 17 | Fold 18 | Fold 19 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.355 | 0.290 | 0.336 | 0.191 | 0.343 | 0.346 | 0.371 | 0.314 | 0.369 | 0.311 | 0.348 | 0.285 | 0.188 | 0.295 | 0.331 | 0.302 | 0.274 | 0.226 | 0.334 | 0.334 |
| jev_head_zero | 0.334 | 0.346 | 0.344 | 0.325 | 0.344 | 0.350 | 0.331 | 0.330 | 0.333 | 0.343 | 0.346 | 0.325 | 0.335 | 0.347 | 0.323 | 0.336 | 0.330 | 0.329 | 0.337 | 0.325 |
| jev_plus_controlled_zero | 0.370 | 0.308 | 0.330 | 0.210 | 0.353 | 0.358 | 0.342 | 0.294 | 0.369 | 0.319 | 0.337 | 0.262 | 0.221 | 0.300 | 0.332 | 0.343 | 0.278 | 0.217 | 0.324 | 0.327 |
| jev_signal_zero | 0.359 | 0.340 | 0.342 | 0.323 | 0.328 | 0.339 | 0.302 | 0.299 | 0.324 | 0.302 | 0.366 | 0.345 | 0.338 | 0.320 | 0.341 | 0.310 | 0.329 | 0.322 | 0.297 | 0.315 |
| logreg | 0.351 | 0.331 | 0.289 | 0.234 | 0.374 | 0.317 | 0.245 | 0.297 | 0.385 | 0.273 | 0.317 | 0.445 | 0.278 | 0.273 | 0.270 | 0.259 | 0.256 | 0.268 | 0.306 | 0.370 |
| ma_cross_rule | 0.337 | 0.319 | 0.344 | 0.264 | 0.311 | 0.342 | 0.355 | 0.262 | 0.351 | 0.254 | 0.351 | 0.340 | 0.339 | 0.284 | 0.331 | 0.336 | 0.314 | 0.319 | 0.304 | 0.278 |
| majority | 0.180 | 0.201 | 0.201 | 0.212 | 0.208 | 0.195 | 0.172 | 0.168 | 0.195 | 0.191 | 0.181 | 0.246 | 0.203 | 0.210 | 0.180 | 0.183 | 0.199 | 0.198 | 0.192 | 0.177 |
| momentum_rule | 0.354 | 0.324 | 0.338 | 0.256 | 0.333 | 0.332 | 0.346 | 0.292 | 0.341 | 0.301 | 0.320 | 0.340 | 0.319 | 0.246 | 0.322 | 0.328 | 0.277 | 0.294 | 0.305 | 0.270 |
| random_forest | 0.348 | 0.302 | 0.293 | 0.236 | 0.323 | 0.357 | 0.266 | 0.305 | 0.357 | 0.356 | 0.309 | 0.268 | 0.189 | 0.338 | 0.330 | 0.265 | 0.266 | 0.291 | 0.318 | 0.351 |
| stratified_random | 0.312 | 0.311 | 0.325 | 0.326 | 0.340 | 0.349 | 0.332 | 0.344 | 0.314 | 0.337 | 0.312 | 0.332 | 0.328 | 0.334 | 0.314 | 0.328 | 0.325 | 0.336 | 0.331 | 0.327 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.309 | 0.328 | 0.350 |
| jev_head_zero | 0.338 | 0.344 | 0.345 |
| jev_plus_controlled_zero | 0.325 | 0.335 | 0.347 |
| jev_signal_zero | 0.347 | 0.332 | 0.323 |
| logreg | 0.387 | 0.339 | 0.339 |
| ma_cross_rule | 0.342 | 0.332 | 0.321 |
| majority | 0.191 | 0.218 | 0.238 |
| momentum_rule | 0.328 | 0.341 | 0.315 |
| random_forest | 0.312 | 0.351 | 0.346 |
| stratified_random | 0.315 | 0.334 | 0.333 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.326 | 0.337 | 0.349 | 15 |
| jev_head_zero | 0.330 | 0.342 | 0.357 | 15 |
| jev_plus_controlled_zero | 0.328 | 0.339 | 0.358 | 15 |
| jev_signal_zero | 0.300 | 0.326 | 0.341 | 15 |
| logreg | 0.336 | 0.347 | 0.366 | 15 |
| ma_cross_rule | 0.309 | 0.331 | 0.352 | 15 |
| majority | 0.214 | 0.225 | 0.232 | 15 |
| momentum_rule | 0.314 | 0.327 | 0.342 | 15 |
| random_forest | 0.330 | 0.340 | 0.354 | 15 |
| stratified_random | 0.317 | 0.332 | 0.339 | 15 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 40 | 8 | 179.2 | 0.9 | 75,360 |
| jev_head_zero | 40 | 8 | 132.4 | 1.0 | 75,360 |
| jev_plus_controlled_zero | 40 | 8 | 223.5 | 0.8 | 75,360 |
| jev_signal_zero | 40 | 1 | 0.1 | 0.0 | 75,360 |
| logreg | 40 | 8 | 9.9 | 0.1 | 75,360 |
| ma_cross_rule | 40 | 6 | 0.5 | 0.0 | 75,360 |
| majority | 40 | 1 | 0.1 | 0.0 | 75,360 |
| momentum_rule | 40 | 8 | 0.7 | 0.0 | 75,360 |
| random_forest | 40 | 8 | 135.7 | 1.8 | 75,360 |
| stratified_random | 40 | 1 | 0.1 | 0.0 | 75,360 |

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
  - `jev_signal_zero` vs `logreg`: -0.09 (95% interval -0.55 to +0.38, Holm p 1.000), **no reliable difference**
- **Used alone, against equal-weight buy and hold:**
  - `jev_signal_zero` vs `always_buy`: -0.41 (95% interval -0.72 to -0.14, Holm p 0.056), **no reliable difference**
- **Added to a traditional classifier (GBT with its outputs against GBT without):**
  - `jev_plus_controlled_zero` vs `gbt`: -0.14 (95% interval -0.29 to +0.04, Holm p 0.096), **no reliable difference**
- **Used alone against used as an added input:**
  - `jev_signal_zero` vs `jev_plus_controlled_zero`: -0.11 (95% interval -0.59 to +0.38, Holm p 0.659), **no reliable difference**
- **Classification (diagnostic, macro-F1, margin +0.02):**
  - `jev_head_zero` vs `logreg`: -0.01 (95% interval -0.02 to +0.01, Holm p 0.450), **no reliable difference**
  - `jev_plus_controlled_zero` vs `logreg`: -0.01 (95% interval -0.02 to +0.01, Holm p 0.450), **no reliable difference**
  - `jev_signal_zero` vs `logreg`: -0.02 (95% interval -0.04 to -0.00, Holm p 0.067), **no reliable difference**
- **Overall:** the thesis is not supported. No arm used alone reliably beats both the traditional classifier and buy and hold. Check the detectable-effect section before reading this as evidence of no difference.

- **Operational efficiency:** see the runtime and cost table; reported, not tested.
