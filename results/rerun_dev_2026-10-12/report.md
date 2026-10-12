# Experiment report: rerun_dev_2026-10-12

Generated 2026-10-12T02:38:29+00:00 from commit `115d3d1`, config `0f51059d80ca`, dataset `9d73476df405`. Final two years of folds included: **False**.

## 1. Research question and method

Can Jev, used as a classifier, outperform traditional models for trading? Each model's predictions are turned into a portfolio by the same rule and compared on net Sharpe ratio with a traditional classifier, with equal-weight buy and hold, and with a traditional classifier that is given Jev's outputs as extra inputs. Every model is fitted and scored on identical observations in a purged walk-forward design. Classification metrics are reported as diagnostics. The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.

## 2. Data and labels

- Universe: `multi_asset_10_v1`, 11 tickers obtained including the market proxy SPY; failed downloads: none.
- Source: yfinance daily bars, 2010-01-04 to 2026-09-30, downloaded 2026-10-12T02:25:44+00:00.
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

- Primary rule: Ranking portfolio: each day hold the top 3 of 10 assets by score, fully invested.
- Also reported: Concentrated ranking portfolio (declared check): each day hold the top 1 of 10 assets by score, fully invested.
- Also reported: BUY-names portfolio: hold the assets labelled BUY, the rest in cash.
- Positions open at the next open and are held for h days in h daily tranches. Cost 5.0 bps per unit of turnover. Idle cash earns the Treasury bill rate; Sharpe and Sortino use returns in excess of that rate.
- `always_buy` holds every asset equally through the same engine and costs. It is the buy-and-hold benchmark. `market_buy_and_hold` is SPY, shown for context only.
- Models without scores of their own (`majority`, `stratified_random`) hold a random selection under the ranking rule, which is that rule's no-skill reference.
- Alpha and beta are measured against the market proxy. Sharpe L/S is the long-short version of the rule.

### Folds before the final two years, primary rule

Ranking portfolio: each day hold the top 3 of 10 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1410.6% | 31.3% | 1.30 | 1.96 | -30.5% | 1.03 | 14.1 | 100.0% | 24.1% (11.0% to 38.2%) | 0.31 | 1.31 | 1.26 | 0.87 |
| momentum_rule | 700.6% | 23.2% | 1.15 | 1.78 | -25.9% | 0.89 | 55.9 | 100.0% | 17.4% (6.1% to 30.0%) | 0.28 | 1.24 | 0.99 | 0.44 |
| always_buy | 223.7% | 12.5% | 0.90 | 1.29 | -26.2% | 0.48 | 0.1 | 100.0% | 4.7% | 0.51 | n/a | n/a | n/a |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 89.5% | 6.6% | 0.34 | 0.49 | -45.2% | 0.15 | 165.0 | 100.0% | 2.8% (-10.2% to 15.4%) | 0.31 | 0.60 | -0.08 | -0.48 |
| random_forest | 56.4% | 4.6% | 0.26 | 0.39 | -34.8% | 0.13 | 170.8 | 100.0% | -1.0% (-9.6% to 7.3%) | 0.41 | 0.61 | -0.30 | -0.73 |
| gbt | 46.1% | 3.9% | 0.21 | 0.30 | -57.4% | 0.07 | 215.1 | 100.0% | -2.7% (-13.3% to 8.5%) | 0.53 | 0.56 | -0.38 | -0.56 |
| majority | -27.2% | -3.1% | -0.19 | -0.28 | -52.7% | -0.06 | 353.9 | 100.0% | -9.1% (-19.4% to 1.0%) | 0.48 | 0.42 | -1.21 | -1.10 |
| stratified_random | -27.2% | -3.1% | -0.19 | -0.28 | -52.7% | -0.06 | 353.9 | 100.0% | -9.1% (-19.4% to 1.0%) | 0.48 | 0.42 | -1.21 | -1.10 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.69 | -1.23 to -0.21 | 0.009 | 0.045 |
| logreg vs always_buy | -0.56 | -1.10 to -0.07 | 0.030 | 0.120 |
| ma_cross_rule vs always_buy | 0.39 | -0.11 to 0.90 | 0.126 | 0.252 |
| momentum_rule vs always_buy | 0.24 | -0.35 to 0.83 | 0.408 | 0.408 |
| random_forest vs always_buy | -0.64 | -1.26 to -0.09 | 0.030 | 0.120 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1574.7% | 32.6% | 1.36 | 2.07 | -30.3% | 1.08 | 12.8 | 99.8% | 24.9% (11.5% to 39.0%) | 0.33 | 1.38 | 1.33 | 0.92 |
| momentum_rule | 1044.2% | 27.7% | 1.34 | 2.05 | -19.1% | 1.45 | 19.7 | 99.8% | 21.2% (9.4% to 33.5%) | 0.27 | 1.37 | 1.28 | 0.79 |
| always_buy | 222.4% | 12.4% | 0.90 | 1.29 | -26.2% | 0.47 | 0.2 | 99.8% | 4.6% | 0.51 | n/a | n/a | n/a |
| random_forest | 331.8% | 15.8% | 0.90 | 1.33 | -33.5% | 0.47 | 41.3 | 99.8% | 7.5% (-1.2% to 17.5%) | 0.55 | 0.98 | 0.77 | 0.06 |
| logreg | 365.2% | 16.7% | 0.87 | 1.30 | -27.5% | 0.60 | 33.5 | 99.8% | 11.2% (-0.7% to 23.5%) | 0.33 | 0.92 | 0.77 | 0.25 |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| gbt | 176.6% | 10.7% | 0.59 | 0.86 | -36.1% | 0.30 | 43.3 | 99.8% | 3.1% (-6.9% to 13.5%) | 0.56 | 0.67 | 0.46 | -0.30 |
| majority | 72.3% | 5.6% | 0.35 | 0.48 | -29.2% | 0.19 | 70.0 | 99.8% | -1.3% (-8.0% to 5.9%) | 0.49 | 0.51 | 0.09 | -0.92 |
| stratified_random | 72.3% | 5.6% | 0.35 | 0.48 | -29.2% | 0.19 | 70.0 | 99.8% | -1.3% (-8.0% to 5.9%) | 0.49 | 0.51 | 0.09 | -0.92 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.31 | -0.84 to 0.13 | 0.203 | 0.609 |
| logreg vs always_buy | -0.03 | -0.60 to 0.49 | 0.904 | 1.000 |
| ma_cross_rule vs always_buy | 0.46 | -0.04 to 0.91 | 0.061 | 0.305 |
| momentum_rule vs always_buy | 0.44 | -0.14 to 0.96 | 0.133 | 0.534 |
| random_forest vs always_buy | -0.00 | -0.50 to 0.42 | 0.990 | 1.000 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1256.3% | 29.9% | 1.26 | 1.88 | -29.3% | 1.02 | 6.7 | 99.2% | 22.1% (7.2% to 39.6%) | 0.38 | 1.26 | 1.24 | 0.99 |
| momentum_rule | 665.3% | 22.6% | 1.14 | 1.72 | -27.2% | 0.83 | 9.6 | 99.2% | 16.4% (3.3% to 31.8%) | 0.33 | 1.15 | 1.11 | 0.74 |
| logreg | 387.2% | 17.2% | 0.94 | 1.40 | -29.1% | 0.59 | 11.7 | 99.2% | 12.0% (1.6% to 25.3%) | 0.29 | 0.96 | 0.91 | 0.14 |
| always_buy | 216.7% | 12.2% | 0.89 | 1.27 | -26.2% | 0.47 | 0.2 | 99.2% | 4.5% | 0.50 | n/a | n/a | n/a |
| majority | 177.7% | 10.8% | 0.77 | 1.09 | -26.2% | 0.41 | 17.3 | 99.2% | 3.3% (-2.7% to 10.0%) | 0.50 | 0.81 | 0.70 | -0.33 |
| stratified_random | 177.7% | 10.8% | 0.77 | 1.09 | -26.2% | 0.41 | 17.3 | 99.2% | 3.3% (-2.7% to 10.0%) | 0.50 | 0.81 | 0.70 | -0.33 |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| random_forest | 127.5% | 8.6% | 0.60 | 0.86 | -23.8% | 0.36 | 11.2 | 99.2% | 0.9% (-4.2% to 6.8%) | 0.53 | 0.63 | 0.56 | -0.78 |
| gbt | 109.6% | 7.7% | 0.45 | 0.64 | -31.8% | 0.24 | 13.0 | 99.2% | 0.2% (-7.3% to 9.6%) | 0.56 | 0.47 | 0.40 | -0.82 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.44 | -0.98 to 0.01 | 0.077 | 0.387 |
| logreg vs always_buy | 0.05 | -0.60 to 0.61 | 0.874 | 0.874 |
| ma_cross_rule vs always_buy | 0.37 | -0.17 to 0.81 | 0.139 | 0.556 |
| momentum_rule vs always_buy | 0.25 | -0.35 to 0.73 | 0.370 | 0.741 |
| random_forest vs always_buy | -0.29 | -0.78 to 0.15 | 0.229 | 0.688 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 10 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 19983.7% | 70.1% | 1.23 | 1.92 | -63.4% | 1.11 | 18.5 | 100.0% | 63.0% (29.0% to 100.0%) | 0.22 | 1.24 | 1.21 | 0.93 |
| always_buy | 223.7% | 12.5% | 0.90 | 1.29 | -26.2% | 0.48 | 0.1 | 100.0% | 4.7% | 0.51 | n/a | n/a | n/a |
| momentum_rule | 1743.1% | 33.9% | 0.87 | 1.39 | -66.3% | 0.51 | 85.3 | 100.0% | 34.7% (8.8% to 61.8%) | 0.10 | 0.94 | 0.77 | 0.49 |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| random_forest | 135.3% | 9.0% | 0.40 | 0.63 | -50.7% | 0.18 | 256.2 | 100.0% | 5.7% (-9.1% to 21.5%) | 0.36 | 0.70 | -0.11 | -0.06 |
| logreg | 126.2% | 8.5% | 0.38 | 0.57 | -88.3% | 0.10 | 211.7 | 100.0% | 15.9% (-17.8% to 50.8%) | 0.25 | 0.51 | 0.17 | -0.07 |
| majority | -20.3% | -2.3% | 0.01 | 0.02 | -60.3% | -0.04 | 453.8 | 100.0% | -5.8% (-22.9% to 10.7%) | 0.50 | 0.48 | -0.76 | -0.59 |
| stratified_random | -20.3% | -2.3% | 0.01 | 0.02 | -60.3% | -0.04 | 453.8 | 100.0% | -5.8% (-22.9% to 10.7%) | 0.50 | 0.48 | -0.76 | -0.59 |
| gbt | -37.2% | -4.6% | 0.00 | 0.01 | -87.1% | -0.05 | 311.9 | 100.0% | -6.1% (-28.4% to 16.7%) | 0.51 | 0.27 | -0.43 | -0.72 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.90 | -1.62 to -0.28 | 0.007 | 0.037 |
| logreg vs always_buy | -0.52 | -1.22 to 0.09 | 0.123 | 0.494 |
| ma_cross_rule vs always_buy | 0.32 | -0.30 to 0.97 | 0.331 | 0.663 |
| momentum_rule vs always_buy | -0.03 | -0.82 to 0.66 | 0.947 | 0.947 |
| random_forest vs always_buy | -0.51 | -1.27 to 0.16 | 0.151 | 0.494 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 26013.1% | 74.6% | 1.29 | 2.04 | -56.8% | 1.32 | 16.7 | 99.8% | 65.1% (30.6% to 103.1%) | 0.22 | 1.30 | 1.28 | 1.01 |
| momentum_rule | 2137.7% | 36.5% | 0.94 | 1.49 | -43.3% | 0.84 | 34.6 | 99.8% | 36.1% (11.1% to 62.1%) | 0.11 | 0.96 | 0.89 | 0.55 |
| always_buy | 222.4% | 12.4% | 0.90 | 1.29 | -26.2% | 0.47 | 0.2 | 99.8% | 4.6% | 0.51 | n/a | n/a | n/a |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 904.1% | 26.0% | 0.72 | 1.10 | -70.1% | 0.37 | 42.1 | 99.8% | 27.0% (-4.3% to 60.7%) | 0.27 | 0.75 | 0.67 | 0.38 |
| random_forest | 443.7% | 18.5% | 0.67 | 0.99 | -55.2% | 0.33 | 60.1 | 99.8% | 12.9% (-5.9% to 33.6%) | 0.55 | 0.73 | 0.56 | 0.26 |
| majority | 136.3% | 9.0% | 0.50 | 0.76 | -33.3% | 0.27 | 91.1 | 99.8% | 2.3% (-7.0% to 12.5%) | 0.49 | 0.66 | 0.23 | -0.55 |
| stratified_random | 136.3% | 9.0% | 0.50 | 0.76 | -33.3% | 0.27 | 91.1 | 99.8% | 2.3% (-7.0% to 12.5%) | 0.49 | 0.66 | 0.23 | -0.55 |
| gbt | 222.9% | 12.5% | 0.48 | 0.73 | -70.6% | 0.18 | 60.7 | 99.8% | 8.2% (-14.4% to 32.9%) | 0.53 | 0.54 | 0.38 | -0.21 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.42 | -1.23 to 0.30 | 0.281 | 1.000 |
| logreg vs always_buy | -0.18 | -0.87 to 0.48 | 0.614 | 1.000 |
| ma_cross_rule vs always_buy | 0.39 | -0.24 to 0.98 | 0.200 | 1.000 |
| momentum_rule vs always_buy | 0.04 | -0.66 to 0.76 | 0.919 | 1.000 |
| random_forest vs always_buy | -0.23 | -0.98 to 0.42 | 0.530 | 1.000 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 10306.8% | 59.3% | 1.11 | 1.69 | -63.5% | 0.93 | 8.2 | 99.2% | 55.7% (14.3% to 103.5%) | 0.30 | 1.11 | 1.10 | 1.05 |
| always_buy | 216.7% | 12.2% | 0.89 | 1.27 | -26.2% | 0.47 | 0.2 | 99.2% | 4.5% | 0.50 | n/a | n/a | n/a |
| momentum_rule | 1324.7% | 30.5% | 0.88 | 1.33 | -45.5% | 0.67 | 15.1 | 99.2% | 28.8% (5.2% to 56.1%) | 0.21 | 0.89 | 0.86 | 0.65 |
| logreg | 1572.9% | 32.6% | 0.86 | 1.29 | -71.9% | 0.45 | 14.5 | 99.2% | 32.3% (3.3% to 67.9%) | 0.21 | 0.87 | 0.84 | 0.38 |
| majority | 215.7% | 12.2% | 0.82 | 1.17 | -28.0% | 0.44 | 22.4 | 99.2% | 4.6% (-2.3% to 12.2%) | 0.50 | 0.87 | 0.74 | -0.02 |
| stratified_random | 215.7% | 12.2% | 0.82 | 1.17 | -28.0% | 0.44 | 22.4 | 99.2% | 4.6% (-2.3% to 12.2%) | 0.50 | 0.87 | 0.74 | -0.02 |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| random_forest | 68.8% | 5.4% | 0.36 | 0.51 | -16.9% | 0.32 | 15.8 | 99.2% | -1.0% (-6.3% to 4.5%) | 0.43 | 0.41 | 0.30 | -1.11 |
| gbt | 53.5% | 4.4% | 0.23 | 0.33 | -47.6% | 0.09 | 18.9 | 99.2% | -1.4% (-14.0% to 14.6%) | 0.54 | 0.26 | 0.19 | -0.77 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.66 | -1.35 to -0.08 | 0.044 | 0.220 |
| logreg vs always_buy | -0.03 | -0.82 to 0.68 | 0.940 | 1.000 |
| ma_cross_rule vs always_buy | 0.22 | -0.38 to 0.74 | 0.447 | 1.000 |
| momentum_rule vs always_buy | -0.01 | -0.67 to 0.62 | 0.980 | 1.000 |
| random_forest vs always_buy | -0.52 | -1.25 to 0.13 | 0.134 | 0.538 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 122.2% | 8.3% | 1.09 | 1.65 | -7.7% | 1.09 | 18.1 | 41.1% | 5.5% (1.5% to 9.7%) | 0.09 | 1.18 | 0.94 | 0.65 | 1.07 | 1.3% |
| momentum_rule | 127.2% | 8.6% | 1.08 | 1.68 | -7.4% | 1.15 | 16.7 | 41.7% | 5.7% (1.6% to 9.8%) | 0.09 | 1.16 | 0.94 | 0.65 | 1.03 | 1.6% |
| always_buy | 223.7% | 12.5% | 0.90 | 1.29 | -26.2% | 0.48 | 0.1 | 100.0% | 4.7% | 0.51 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| gbt | 42.5% | 3.6% | 0.33 | 0.47 | -21.5% | 0.17 | 46.9 | 26.3% | -0.5% (-4.4% to 3.1%) | 0.21 | 0.55 | -0.04 | -0.45 | 0.31 | 0.3% |
| logreg | 33.5% | 2.9% | 0.22 | 0.30 | -20.3% | 0.15 | 32.9 | 24.9% | -1.0% (-5.1% to 3.0%) | 0.20 | 0.36 | -0.02 | -0.44 | 0.34 | -0.7% |
| random_forest | 19.5% | 1.8% | 0.05 | 0.07 | -14.8% | 0.12 | 36.5 | 25.7% | -1.8% (-4.6% to 1.1%) | 0.17 | 0.26 | -0.29 | -0.49 | 0.31 | -1.3% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| stratified_random | -18.1% | -2.0% | -0.60 | -0.80 | -23.9% | -0.08 | 104.5 | 29.9% | -5.5% (-9.4% to -2.0%) | 0.16 | -0.06 | -1.50 | -1.79 | 0.75 | -6.6% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.57 | -1.14 to 0.00 | 0.050 | 0.150 |
| logreg vs always_buy | -0.69 | -1.23 to -0.18 | 0.010 | 0.040 |
| ma_cross_rule vs always_buy | 0.18 | -0.49 to 0.87 | 0.602 | 1.000 |
| momentum_rule vs always_buy | 0.17 | -0.47 to 0.80 | 0.588 | 1.000 |
| random_forest vs always_buy | -0.85 | -1.40 to -0.32 | 0.004 | 0.020 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 159.9% | 10.0% | 1.31 | 2.02 | -8.0% | 1.25 | 6.0 | 39.2% | 7.0% (3.0% to 11.1%) | 0.09 | 1.34 | 1.26 | 0.82 | 1.06 | 3.1% |
| ma_cross_rule | 128.5% | 8.6% | 1.20 | 1.85 | -4.9% | 1.77 | 9.7 | 39.2% | 5.6% (2.0% to 9.5%) | 0.10 | 1.25 | 1.11 | 0.73 | 1.05 | 1.8% |
| always_buy | 222.4% | 12.4% | 0.90 | 1.29 | -26.2% | 0.47 | 0.2 | 99.8% | 4.6% | 0.51 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 43.7% | 3.7% | 0.47 | 0.65 | -11.2% | 0.33 | 22.3 | 32.4% | 0.0% (-2.2% to 2.2%) | 0.17 | 0.63 | 0.22 | -0.73 | 0.84 | -1.2% |
| gbt | 51.7% | 4.3% | 0.44 | 0.66 | -12.7% | 0.34 | 12.4 | 29.8% | -0.1% (-2.7% to 2.8%) | 0.23 | 0.50 | 0.34 | -0.08 | 0.48 | 0.1% |
| random_forest | 43.0% | 3.6% | 0.32 | 0.46 | -18.0% | 0.20 | 11.3 | 30.2% | -1.0% (-4.3% to 2.6%) | 0.26 | 0.37 | 0.24 | -0.12 | 0.38 | -0.2% |
| logreg | 21.2% | 1.9% | 0.08 | 0.10 | -19.4% | 0.10 | 11.1 | 29.8% | -2.3% (-6.3% to 1.5%) | 0.23 | 0.13 | -0.01 | -0.43 | 0.18 | -0.7% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.46 | -0.97 to -0.01 | 0.061 | 0.183 |
| logreg vs always_buy | -0.82 | -1.34 to -0.30 | 0.002 | 0.010 |
| ma_cross_rule vs always_buy | 0.30 | -0.34 to 0.89 | 0.334 | 0.390 |
| momentum_rule vs always_buy | 0.41 | -0.26 to 1.01 | 0.195 | 0.390 |
| random_forest vs always_buy | -0.58 | -1.09 to -0.05 | 0.031 | 0.126 |

**20-day horizon**, 2014-10-01 to 2024-08-29

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 157.5% | 9.9% | 1.32 | 2.02 | -8.5% | 1.17 | 3.7 | 41.1% | 6.5% (2.0% to 11.4%) | 0.13 | 1.34 | 1.29 | 0.92 | 0.95 | 3.1% |
| momentum_rule | 154.4% | 9.8% | 1.23 | 1.83 | -12.0% | 0.82 | 3.1 | 42.4% | 6.4% (1.6% to 11.9%) | 0.13 | 1.24 | 1.21 | 0.80 | 0.98 | 2.8% |
| always_buy | 216.7% | 12.2% | 0.89 | 1.27 | -26.2% | 0.47 | 0.2 | 99.2% | 4.5% | 0.50 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 68.2% | 5.3% | 0.87 | 1.24 | -9.3% | 0.57 | 5.7 | 35.1% | 1.5% (-0.6% to 3.8%) | 0.18 | 0.91 | 0.80 | 0.36 | 0.92 | -0.3% |
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| logreg | 62.6% | 5.0% | 0.54 | 0.78 | -11.5% | 0.43 | 4.4 | 36.9% | 0.8% (-2.3% to 4.5%) | 0.22 | 0.56 | 0.50 | 0.01 | 0.58 | -0.1% |
| random_forest | 38.5% | 3.3% | 0.30 | 0.42 | -11.9% | 0.28 | 4.4 | 37.5% | -1.1% (-3.7% to 1.4%) | 0.24 | 0.32 | 0.26 | -0.57 | 0.67 | -2.2% |
| gbt | 33.0% | 2.9% | 0.23 | 0.34 | -14.0% | 0.21 | 4.4 | 36.6% | -1.3% (-3.9% to 1.6%) | 0.22 | 0.26 | 0.20 | -0.66 | 0.61 | -1.9% |
| majority | 17.8% | 1.7% | 0.00 | 0.00 | -0.0% | 1138.05 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.65 | -1.20 to -0.16 | 0.011 | 0.055 |
| logreg vs always_buy | -0.35 | -0.93 to 0.16 | 0.211 | 0.384 |
| ma_cross_rule vs always_buy | 0.44 | -0.10 to 0.93 | 0.091 | 0.274 |
| momentum_rule vs always_buy | 0.34 | -0.20 to 0.82 | 0.192 | 0.384 |
| random_forest vs always_buy | -0.59 | -1.14 to -0.07 | 0.032 | 0.130 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.48 (median of 5 comparisons). A true difference smaller than about 0.69 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

24,899 test observations on 2,514 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.369 | 0.370 | 0.394 | 1.091 | 0.660 | 0.008 | 0.500 | 28/46/25 | 0.0% |
| random_forest | 0.368 | 0.369 | 0.395 | 1.090 | 0.660 | 0.023 | 0.509 | 26/48/26 | 0.0% |
| gbt | 0.366 | 0.367 | 0.381 | 1.096 | 0.664 | 0.031 | 0.507 | 32/41/27 | 0.0% |
| momentum_rule | 0.341 | 0.345 | 0.353 | n/a | n/a | n/a | 0.520 | 22/36/42 | 0.0% |
| stratified_random | 0.333 | 0.333 | 0.350 | 1.074 | 0.650 | 0.003 | 0.503 | 26/44/30 | 0.0% |
| ma_cross_rule | 0.333 | 0.336 | 0.345 | n/a | n/a | n/a | 0.528 | 20/38/42 | 0.0% |
| majority | 0.203 | 0.333 | 0.438 | 1.074 | 0.650 | 0.003 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 26.2%, HOLD 43.8%, BUY 30.1%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.272 | 0.490 | 0.342 | 0.334 | 0.464 | 0.302 | 0.041% | 0.042% | 0.074% |
| logreg | 0.281 | 0.496 | 0.335 | 0.306 | 0.526 | 0.280 | 0.027% | 0.061% | 0.056% |
| ma_cross_rule | 0.300 | 0.427 | 0.291 | 0.234 | 0.372 | 0.401 | -0.002% | 0.048% | 0.079% |
| majority | 0.000 | 0.438 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.050% | n/a |
| momentum_rule | 0.295 | 0.452 | 0.298 | 0.242 | 0.375 | 0.418 | -0.002% | 0.048% | 0.079% |
| random_forest | 0.287 | 0.487 | 0.332 | 0.284 | 0.536 | 0.286 | 0.024% | 0.071% | 0.039% |
| stratified_random | 0.261 | 0.437 | 0.301 | 0.261 | 0.437 | 0.302 | 0.075% | 0.050% | 0.030% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0326 | 0.0231 to 0.0422 | 0.000 | 0.002 |
| logreg vs stratified_random | 0.0362 | 0.0260 to 0.0460 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | -0.0006 | -0.0118 to 0.0105 | 0.931 | 0.931 |
| momentum_rule vs stratified_random | 0.0081 | -0.0025 to 0.0181 | 0.145 | 0.290 |
| random_forest vs stratified_random | 0.0345 | 0.0252 to 0.0435 | 0.000 | 0.002 |

### 5-day horizon (primary)

24,859 test observations on 2,510 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.364 | 0.364 | 0.382 | 1.107 | 0.668 | 0.027 | 0.499 | 26/43/30 | 0.0% |
| random_forest | 0.363 | 0.363 | 0.375 | 1.096 | 0.665 | 0.023 | 0.504 | 30/40/31 | 0.0% |
| gbt | 0.361 | 0.363 | 0.366 | 1.131 | 0.686 | 0.094 | 0.507 | 35/35/30 | 0.0% |
| momentum_rule | 0.348 | 0.349 | 0.357 | n/a | n/a | n/a | 0.539 | 24/36/40 | 0.0% |
| ma_cross_rule | 0.339 | 0.339 | 0.352 | n/a | n/a | n/a | 0.533 | 21/40/40 | 0.0% |
| stratified_random | 0.335 | 0.335 | 0.347 | 1.081 | 0.655 | 0.004 | 0.507 | 26/41/33 | 0.0% |
| majority | 0.195 | 0.333 | 0.414 | 1.081 | 0.655 | 0.004 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.5%, HOLD 41.4%, BUY 33.1%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.264 | 0.466 | 0.367 | 0.360 | 0.395 | 0.334 | 0.198% | 0.319% | 0.253% |
| logreg | 0.263 | 0.470 | 0.359 | 0.272 | 0.494 | 0.327 | 0.284% | 0.343% | 0.109% |
| ma_cross_rule | 0.297 | 0.411 | 0.320 | 0.239 | 0.396 | 0.383 | 0.052% | 0.207% | 0.413% |
| majority | 0.000 | 0.414 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.257% | n/a |
| momentum_rule | 0.287 | 0.423 | 0.338 | 0.272 | 0.369 | 0.406 | 0.079% | 0.148% | 0.464% |
| random_forest | 0.262 | 0.467 | 0.364 | 0.303 | 0.450 | 0.336 | 0.192% | 0.341% | 0.211% |
| stratified_random | 0.255 | 0.416 | 0.332 | 0.262 | 0.413 | 0.329 | 0.284% | 0.258% | 0.234% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0259 | 0.0103 to 0.0411 | 0.001 | 0.004 |
| logreg vs stratified_random | 0.0292 | 0.0147 to 0.0422 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | 0.0043 | -0.0095 to 0.0173 | 0.518 | 0.518 |
| momentum_rule vs stratified_random | 0.0130 | -0.0020 to 0.0273 | 0.081 | 0.163 |
| random_forest vs stratified_random | 0.0283 | 0.0127 to 0.0427 | 0.000 | 0.002 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,284 | 2,029 | 2,035 | 0 |
| HOLD | 3,505 | 4,056 | 2,720 | 0 |
| BUY | 2,862 | 2,617 | 2,751 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,727 | 2,473 | 2,148 | 0 |
| HOLD | 2,549 | 5,081 | 2,651 | 0 |
| BUY | 2,288 | 3,253 | 2,689 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,517 | 2,506 | 2,325 | 0 |
| HOLD | 1,833 | 4,073 | 4,375 | 0 |
| BUY | 1,762 | 3,319 | 3,149 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 6,348 | 0 | 0 |
| HOLD | 0 | 10,281 | 0 | 0 |
| BUY | 0 | 8,230 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,729 | 2,325 | 2,294 | 0 |
| HOLD | 2,254 | 3,795 | 4,232 | 0 |
| BUY | 2,034 | 2,857 | 3,339 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,925 | 2,283 | 2,140 | 0 |
| HOLD | 2,963 | 4,622 | 2,696 | 0 |
| BUY | 2,471 | 2,990 | 2,769 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,662 | 2,600 | 2,086 | 0 |
| HOLD | 2,676 | 4,244 | 3,361 | 0 |
| BUY | 2,168 | 3,352 | 2,710 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.321 | 0.375 | 0.356 | 0.388 | 0.351 | 0.442 | 0.176 | 0.305 | 0.358 | 0.362 |
| logreg | 0.335 | 0.383 | 0.351 | 0.354 | 0.387 | 0.402 | 0.197 | 0.287 | 0.365 | 0.352 |
| ma_cross_rule | 0.348 | 0.332 | 0.331 | 0.351 | 0.313 | 0.351 | 0.336 | 0.328 | 0.321 | 0.283 |
| majority | 0.186 | 0.206 | 0.198 | 0.182 | 0.193 | 0.213 | 0.202 | 0.182 | 0.204 | 0.183 |
| momentum_rule | 0.356 | 0.335 | 0.343 | 0.368 | 0.317 | 0.374 | 0.324 | 0.353 | 0.300 | 0.309 |
| random_forest | 0.336 | 0.362 | 0.353 | 0.383 | 0.381 | 0.451 | 0.202 | 0.285 | 0.332 | 0.350 |
| stratified_random | 0.345 | 0.340 | 0.326 | 0.338 | 0.338 | 0.334 | 0.338 | 0.320 | 0.326 | 0.332 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.366 | 0.359 | 0.344 |
| logreg | 0.347 | 0.361 | 0.357 |
| ma_cross_rule | 0.339 | 0.347 | 0.321 |
| majority | 0.192 | 0.199 | 0.193 |
| momentum_rule | 0.323 | 0.350 | 0.337 |
| random_forest | 0.346 | 0.362 | 0.353 |
| stratified_random | 0.336 | 0.329 | 0.338 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.327 | 0.349 | 0.378 | 10 |
| logreg | 0.338 | 0.350 | 0.376 | 10 |
| ma_cross_rule | 0.316 | 0.329 | 0.359 | 10 |
| majority | 0.189 | 0.193 | 0.202 | 10 |
| momentum_rule | 0.318 | 0.344 | 0.357 | 10 |
| random_forest | 0.323 | 0.346 | 0.385 | 10 |
| stratified_random | 0.326 | 0.333 | 0.350 | 10 |

### 20-day horizon

24,709 test observations on 2,495 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.362 | 0.362 | 0.370 | 1.199 | 0.693 | 0.065 | 0.516 | 30/32/38 | 0.0% |
| ma_cross_rule | 0.360 | 0.360 | 0.374 | n/a | n/a | n/a | 0.571 | 21/37/42 | 0.0% |
| random_forest | 0.351 | 0.353 | 0.356 | 1.115 | 0.677 | 0.050 | 0.516 | 33/29/38 | 0.0% |
| momentum_rule | 0.350 | 0.352 | 0.365 | n/a | n/a | n/a | 0.572 | 21/36/43 | 0.0% |
| gbt | 0.334 | 0.335 | 0.340 | 1.198 | 0.723 | 0.149 | 0.484 | 31/31/37 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.344 | 1.083 | 0.657 | 0.001 | 0.520 | 26/39/36 | 0.0% |
| majority | 0.186 | 0.333 | 0.387 | 1.083 | 0.657 | 0.001 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 24.7%, HOLD 38.7%, BUY 36.6%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.230 | 0.420 | 0.367 | 0.292 | 0.339 | 0.374 | 1.662% | 1.138% | 0.514% |
| logreg | 0.249 | 0.450 | 0.398 | 0.305 | 0.374 | 0.409 | 1.170% | 1.065% | 0.993% |
| ma_cross_rule | 0.300 | 0.404 | 0.384 | 0.253 | 0.390 | 0.439 | 0.348% | 0.611% | 1.839% |
| majority | 0.000 | 0.387 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 1.070% | n/a |
| momentum_rule | 0.277 | 0.390 | 0.388 | 0.238 | 0.360 | 0.458 | 0.537% | 0.544% | 1.766% |
| random_forest | 0.243 | 0.432 | 0.396 | 0.323 | 0.323 | 0.414 | 1.484% | 1.266% | 0.565% |
| stratified_random | 0.248 | 0.385 | 0.368 | 0.256 | 0.386 | 0.360 | 1.012% | 1.080% | 1.101% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0006 | -0.0265 to 0.0264 | 0.972 | 0.972 |
| logreg vs stratified_random | 0.0281 | -0.0024 to 0.0553 | 0.054 | 0.218 |
| ma_cross_rule vs stratified_random | 0.0263 | 0.0010 to 0.0514 | 0.042 | 0.210 |
| momentum_rule vs stratified_random | 0.0163 | -0.0121 to 0.0449 | 0.269 | 0.808 |
| random_forest vs stratified_random | 0.0169 | -0.0140 to 0.0460 | 0.288 | 0.808 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 30 | 8 | 370.6 | 1.0 | 74,467 |
| logreg | 30 | 8 | 37.4 | 0.1 | 74,467 |
| ma_cross_rule | 30 | 6 | 0.6 | 0.0 | 74,467 |
| majority | 30 | 1 | 0.1 | 0.0 | 74,467 |
| momentum_rule | 30 | 8 | 0.8 | 0.0 | 74,467 |
| random_forest | 30 | 8 | 255.7 | 2.2 | 74,467 |
| stratified_random | 30 | 1 | 0.1 | 0.0 | 74,467 |

Traditional models run locally at no marginal cost. External classifier status: jev/zero: not run: no saved outputs; jev/examples: not run: no saved outputs; openai/zero: not run: no saved outputs; openai/examples: not run: no saved outputs; local/zero: not run: no saved outputs; local/examples: not run: no saved outputs.

Models that did not run:

- `jev_head_examples` (GBT on Jev (TypeSafe jev-1.13.0) outputs, with training examples): not run: no saved outputs
- `jev_head_zero` (GBT on Jev (TypeSafe jev-1.13.0) outputs, zero-shot): not run: no saved outputs
- `jev_plus_controlled_examples` (GBT on controlled features + Jev (TypeSafe jev-1.13.0) outputs, with training examples): not run: no saved outputs
- `jev_plus_controlled_zero` (GBT on controlled features + Jev (TypeSafe jev-1.13.0) outputs, zero-shot): not run: no saved outputs
- `jev_signal_examples` (Jev (TypeSafe jev-1.13.0) as signal, with training examples): not run: no saved outputs
- `jev_signal_zero` (Jev (TypeSafe jev-1.13.0) as signal, zero-shot): not run: no saved outputs

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
