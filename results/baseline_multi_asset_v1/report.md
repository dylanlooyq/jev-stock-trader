# Experiment report: baseline_multi_asset_v1

Generated 2026-10-11T11:48:08+00:00 from commit `3988057`, config `0f51059d80ca`, dataset `4df028245fc7`. Final two years of folds included: **True**.

## 1. Research question and method

Can Jev, used as a classifier, outperform traditional models for trading? Each model's predictions are turned into a portfolio by the same rule and compared on net Sharpe ratio with a traditional classifier, with equal-weight buy and hold, and with a traditional classifier that is given Jev's outputs as extra inputs. Every model is fitted and scored on identical observations in a purged walk-forward design. Classification metrics are reported as diagnostics. The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.

## 2. Data and labels

- Universe: `multi_asset_10_v1`, 11 tickers obtained including the market proxy SPY; failed downloads: none.
- Source: yfinance daily bars, 2010-01-04 to 2026-09-30, downloaded 2026-10-11T10:53:06+00:00.
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

### All folds, primary rule

Ranking portfolio: each day hold the top 3 of 10 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2026-09-28

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 2826.9% | 32.6% | 1.37 | 2.06 | -30.5% | 1.07 | 15.2 | 100.0% | 24.7% (13.9% to 36.9%) | 0.29 | 1.39 | 1.33 | 0.89 |
| momentum_rule | 983.3% | 22.0% | 1.10 | 1.68 | -25.9% | 0.85 | 56.9 | 100.0% | 16.2% (6.2% to 26.5%) | 0.26 | 1.19 | 0.94 | 0.39 |
| always_buy | 337.2% | 13.1% | 0.94 | 1.34 | -26.2% | 0.50 | 0.1 | 100.0% | 4.8% | 0.49 | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| gbt | 110.3% | 6.4% | 0.32 | 0.45 | -53.4% | 0.12 | 219.4 | 100.0% | -0.7% (-10.8% to 9.6%) | 0.53 | 0.68 | -0.28 | -0.73 |
| logreg | 104.2% | 6.1% | 0.30 | 0.44 | -44.5% | 0.14 | 165.6 | 100.0% | 1.9% (-9.6% to 13.6%) | 0.31 | 0.57 | -0.14 | -0.57 |
| random_forest | 39.4% | 2.8% | 0.12 | 0.18 | -41.0% | 0.07 | 172.9 | 100.0% | -3.0% (-10.9% to 4.7%) | 0.39 | 0.48 | -0.46 | -0.71 |
| majority | -24.3% | -2.3% | -0.17 | -0.25 | -56.6% | -0.04 | 352.5 | 100.0% | -8.8% (-17.7% to 0.2%) | 0.47 | 0.45 | -1.22 | -1.18 |
| stratified_random | -24.3% | -2.3% | -0.17 | -0.25 | -56.6% | -0.04 | 352.5 | 100.0% | -8.8% (-17.7% to 0.2%) | 0.47 | 0.45 | -1.22 | -1.18 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.62 | -1.10 to -0.15 | 0.009 | 0.038 |
| logreg vs always_buy | -0.63 | -1.12 to -0.19 | 0.009 | 0.038 |
| ma_cross_rule vs always_buy | 0.43 | -0.05 to 0.89 | 0.076 | 0.153 |
| momentum_rule vs always_buy | 0.16 | -0.41 to 0.68 | 0.585 | 0.585 |
| random_forest vs always_buy | -0.82 | -1.37 to -0.27 | 0.004 | 0.022 |

**5-day horizon (primary)**, 2014-10-01 to 2026-09-22

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 3013.6% | 33.3% | 1.40 | 2.13 | -30.3% | 1.10 | 13.4 | 99.8% | 24.9% (12.7% to 37.3%) | 0.31 | 1.42 | 1.37 | 0.91 |
| momentum_rule | 1415.0% | 25.5% | 1.26 | 1.90 | -19.1% | 1.33 | 22.6 | 99.8% | 19.0% (8.4% to 29.4%) | 0.26 | 1.29 | 1.19 | 0.74 |
| always_buy | 337.5% | 13.1% | 0.94 | 1.34 | -26.2% | 0.50 | 0.2 | 99.8% | 4.8% | 0.49 | n/a | n/a | n/a |
| random_forest | 435.0% | 15.0% | 0.86 | 1.26 | -33.1% | 0.45 | 41.8 | 99.8% | 6.4% (-1.4% to 14.4%) | 0.54 | 0.94 | 0.72 | -0.00 |
| logreg | 516.7% | 16.4% | 0.85 | 1.26 | -27.3% | 0.60 | 34.2 | 99.8% | 10.7% (0.4% to 20.9%) | 0.32 | 0.91 | 0.75 | 0.18 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| gbt | 248.8% | 11.0% | 0.60 | 0.86 | -40.6% | 0.27 | 45.5 | 99.8% | 2.7% (-5.9% to 11.3%) | 0.56 | 0.68 | 0.46 | -0.21 |
| majority | 116.4% | 6.7% | 0.41 | 0.56 | -29.2% | 0.23 | 70.0 | 99.8% | -0.7% (-7.0% to 5.2%) | 0.48 | 0.57 | 0.14 | -0.87 |
| stratified_random | 116.4% | 6.7% | 0.41 | 0.56 | -29.2% | 0.23 | 70.0 | 99.8% | -0.7% (-7.0% to 5.2%) | 0.48 | 0.57 | 0.14 | -0.87 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.34 | -0.77 to 0.09 | 0.120 | 0.480 |
| logreg vs always_buy | -0.09 | -0.55 to 0.40 | 0.724 | 1.000 |
| ma_cross_rule vs always_buy | 0.46 | -0.01 to 0.90 | 0.047 | 0.237 |
| momentum_rule vs always_buy | 0.32 | -0.21 to 0.81 | 0.240 | 0.720 |
| random_forest vs always_buy | -0.08 | -0.52 to 0.36 | 0.702 | 1.000 |

**20-day horizon**, 2014-10-01 to 2026-08-31

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1906.4% | 28.5% | 1.22 | 1.81 | -29.3% | 0.97 | 6.9 | 99.3% | 20.3% (7.8% to 34.6%) | 0.39 | 1.23 | 1.21 | 0.84 |
| momentum_rule | 1045.2% | 22.6% | 1.15 | 1.73 | -27.2% | 0.83 | 9.8 | 99.3% | 15.9% (4.8% to 28.6%) | 0.31 | 1.17 | 1.12 | 0.73 |
| always_buy | 339.8% | 13.2% | 0.95 | 1.35 | -26.2% | 0.50 | 0.2 | 99.3% | 4.9% | 0.49 | n/a | n/a | n/a |
| logreg | 508.1% | 16.3% | 0.90 | 1.32 | -32.4% | 0.50 | 11.9 | 99.3% | 10.7% (1.3% to 21.3%) | 0.29 | 0.92 | 0.86 | 0.14 |
| majority | 286.1% | 11.9% | 0.84 | 1.20 | -26.2% | 0.46 | 17.3 | 99.3% | 3.9% (-1.4% to 9.8%) | 0.48 | 0.89 | 0.77 | -0.24 |
| stratified_random | 286.1% | 11.9% | 0.84 | 1.20 | -26.2% | 0.46 | 17.3 | 99.3% | 3.9% (-1.4% to 9.8%) | 0.48 | 0.89 | 0.77 | -0.24 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| random_forest | 170.5% | 8.7% | 0.60 | 0.85 | -22.1% | 0.39 | 11.0 | 99.3% | 0.8% (-3.3% to 5.2%) | 0.50 | 0.63 | 0.55 | -0.76 |
| gbt | 128.0% | 7.1% | 0.39 | 0.55 | -34.0% | 0.21 | 12.3 | 99.3% | -0.8% (-7.7% to 7.0%) | 0.56 | 0.41 | 0.35 | -0.87 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.56 | -1.09 to -0.12 | 0.024 | 0.120 |
| logreg vs always_buy | -0.05 | -0.58 to 0.42 | 0.856 | 0.856 |
| ma_cross_rule vs always_buy | 0.28 | -0.17 to 0.70 | 0.216 | 0.648 |
| momentum_rule vs always_buy | 0.21 | -0.31 to 0.67 | 0.403 | 0.806 |
| random_forest vs always_buy | -0.35 | -0.81 to 0.05 | 0.110 | 0.440 |

### All folds, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 10 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2026-09-28

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 72046.2% | 73.3% | 1.28 | 2.01 | -63.4% | 1.16 | 18.6 | 100.0% | 64.4% (34.7% to 97.1%) | 0.15 | 1.29 | 1.26 | 0.94 |
| always_buy | 337.2% | 13.1% | 0.94 | 1.34 | -26.2% | 0.50 | 0.1 | 100.0% | 4.8% | 0.49 | n/a | n/a | n/a |
| momentum_rule | 1799.2% | 27.9% | 0.76 | 1.19 | -66.3% | 0.42 | 88.5 | 100.0% | 29.8% (8.0% to 53.5%) | 0.05 | 0.83 | 0.65 | 0.37 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 158.7% | 8.3% | 0.36 | 0.54 | -88.3% | 0.09 | 216.5 | 100.0% | 14.5% (-14.0% to 45.9%) | 0.22 | 0.50 | 0.13 | -0.13 |
| random_forest | 59.3% | 4.0% | 0.20 | 0.30 | -49.5% | 0.08 | 258.8 | 100.0% | 0.7% (-12.5% to 15.2%) | 0.36 | 0.50 | -0.30 | -0.09 |
| gbt | -38.3% | -4.0% | 0.02 | 0.03 | -81.9% | -0.05 | 318.3 | 100.0% | -6.0% (-28.1% to 17.3%) | 0.53 | 0.28 | -0.42 | -0.52 |
| majority | -39.5% | -4.1% | -0.08 | -0.12 | -66.9% | -0.06 | 454.3 | 100.0% | -8.7% (-23.5% to 6.7%) | 0.52 | 0.40 | -0.87 | -0.77 |
| stratified_random | -39.5% | -4.1% | -0.08 | -0.12 | -66.9% | -0.06 | 454.3 | 100.0% | -8.7% (-23.5% to 6.7%) | 0.52 | 0.40 | -0.87 | -0.77 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.92 | -1.58 to -0.35 | 0.004 | 0.020 |
| logreg vs always_buy | -0.58 | -1.21 to -0.01 | 0.059 | 0.177 |
| ma_cross_rule vs always_buy | 0.34 | -0.28 to 0.93 | 0.270 | 0.541 |
| momentum_rule vs always_buy | -0.18 | -0.88 to 0.52 | 0.622 | 0.622 |
| random_forest vs always_buy | -0.74 | -1.41 to -0.08 | 0.030 | 0.120 |

**5-day horizon (primary)**, 2014-10-01 to 2026-09-22

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 96097.6% | 77.5% | 1.34 | 2.12 | -56.8% | 1.37 | 16.8 | 99.8% | 66.3% (35.2% to 97.6%) | 0.16 | 1.35 | 1.33 | 1.02 |
| always_buy | 337.5% | 13.1% | 0.94 | 1.34 | -26.2% | 0.50 | 0.2 | 99.8% | 4.8% | 0.49 | n/a | n/a | n/a |
| momentum_rule | 3323.0% | 34.3% | 0.91 | 1.42 | -43.3% | 0.79 | 37.8 | 99.8% | 34.1% (12.4% to 56.0%) | 0.05 | 0.94 | 0.86 | 0.51 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 1056.1% | 22.7% | 0.65 | 0.98 | -76.9% | 0.30 | 43.4 | 99.8% | 24.0% (-2.6% to 50.6%) | 0.23 | 0.69 | 0.60 | 0.31 |
| random_forest | 543.7% | 16.8% | 0.62 | 0.92 | -56.5% | 0.30 | 60.9 | 99.8% | 10.9% (-6.4% to 27.8%) | 0.54 | 0.69 | 0.51 | 0.14 |
| gbt | 270.9% | 11.6% | 0.45 | 0.69 | -71.2% | 0.16 | 63.7 | 99.8% | 6.1% (-13.4% to 25.9%) | 0.55 | 0.52 | 0.34 | -0.04 |
| majority | 165.2% | 8.5% | 0.45 | 0.68 | -33.3% | 0.26 | 90.8 | 99.8% | 1.1% (-7.2% to 9.3%) | 0.51 | 0.61 | 0.18 | -0.52 |
| stratified_random | 165.2% | 8.5% | 0.45 | 0.68 | -33.3% | 0.26 | 90.8 | 99.8% | 1.1% (-7.2% to 9.3%) | 0.51 | 0.61 | 0.18 | -0.52 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.49 | -1.16 to 0.15 | 0.149 | 0.747 |
| logreg vs always_buy | -0.29 | -0.87 to 0.30 | 0.340 | 0.936 |
| ma_cross_rule vs always_buy | 0.40 | -0.18 to 0.96 | 0.169 | 0.747 |
| momentum_rule vs always_buy | -0.03 | -0.70 to 0.62 | 0.916 | 0.936 |
| random_forest vs always_buy | -0.32 | -0.93 to 0.32 | 0.312 | 0.936 |

**20-day horizon**, 2014-10-01 to 2026-08-31

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 22717.9% | 57.4% | 1.11 | 1.68 | -63.5% | 0.90 | 8.5 | 99.3% | 53.2% (19.0% to 92.4%) | 0.26 | 1.11 | 1.10 | 0.98 |
| always_buy | 339.8% | 13.2% | 0.95 | 1.35 | -26.2% | 0.50 | 0.2 | 99.3% | 4.9% | 0.49 | n/a | n/a | n/a |
| momentum_rule | 2035.5% | 29.1% | 0.86 | 1.29 | -45.5% | 0.64 | 15.0 | 99.3% | 27.4% (7.7% to 50.1%) | 0.16 | 0.87 | 0.84 | 0.60 |
| majority | 302.4% | 12.3% | 0.82 | 1.17 | -28.0% | 0.44 | 22.4 | 99.3% | 4.3% (-1.8% to 10.3%) | 0.49 | 0.87 | 0.73 | -0.02 |
| stratified_random | 302.4% | 12.3% | 0.82 | 1.17 | -28.0% | 0.44 | 22.4 | 99.3% | 4.3% (-1.8% to 10.3%) | 0.49 | 0.87 | 0.73 | -0.02 |
| logreg | 1803.7% | 27.9% | 0.78 | 1.16 | -74.9% | 0.37 | 15.1 | 99.3% | 27.8% (3.7% to 55.3%) | 0.19 | 0.79 | 0.76 | 0.35 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| random_forest | 155.8% | 8.2% | 0.53 | 0.77 | -14.7% | 0.56 | 16.2 | 99.3% | 1.5% (-2.8% to 6.0%) | 0.41 | 0.57 | 0.47 | -0.92 |
| gbt | 18.8% | 1.4% | 0.08 | 0.12 | -52.4% | 0.03 | 17.9 | 99.3% | -4.8% (-15.0% to 6.8%) | 0.53 | 0.11 | 0.04 | -1.01 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.86 | -1.51 to -0.30 | 0.007 | 0.037 |
| logreg vs always_buy | -0.17 | -0.79 to 0.43 | 0.599 | 1.000 |
| ma_cross_rule vs always_buy | 0.16 | -0.38 to 0.65 | 0.541 | 1.000 |
| momentum_rule vs always_buy | -0.08 | -0.65 to 0.47 | 0.779 | 1.000 |
| random_forest vs always_buy | -0.41 | -1.02 to 0.18 | 0.196 | 0.784 |

### All folds, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2026-09-28

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 170.6% | 8.7% | 1.10 | 1.66 | -7.7% | 1.13 | 19.1 | 41.7% | 5.5% (2.1% to 9.3%) | 0.08 | 1.19 | 0.93 | 0.58 | 1.03 | 1.6% |
| momentum_rule | 163.2% | 8.4% | 1.02 | 1.57 | -7.4% | 1.13 | 17.5 | 41.7% | 5.2% (1.9% to 8.9%) | 0.08 | 1.10 | 0.87 | 0.59 | 1.03 | 1.3% |
| always_buy | 337.2% | 13.1% | 0.94 | 1.34 | -26.2% | 0.50 | 0.1 | 100.0% | 4.8% | 0.49 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| gbt | 72.5% | 4.7% | 0.44 | 0.65 | -15.4% | 0.30 | 51.4 | 27.9% | 0.2% (-2.8% to 3.2%) | 0.20 | 0.69 | 0.02 | -0.37 | 0.62 | -0.6% |
| logreg | 54.0% | 3.7% | 0.26 | 0.37 | -20.3% | 0.18 | 35.1 | 25.7% | -0.8% (-4.6% to 2.9%) | 0.21 | 0.42 | 0.01 | -0.40 | 0.46 | -1.1% |
| random_forest | 29.9% | 2.2% | 0.06 | 0.08 | -14.9% | 0.15 | 38.2 | 27.0% | -1.9% (-4.6% to 0.8%) | 0.17 | 0.27 | -0.30 | -0.53 | 0.44 | -2.0% |
| majority | 27.5% | 2.0% | 0.00 | 0.00 | -0.0% | 1405.91 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| stratified_random | -18.3% | -1.7% | -0.63 | -0.84 | -23.9% | -0.07 | 104.7 | 30.0% | -5.5% (-8.8% to -2.4%) | 0.16 | -0.07 | -1.56 | -1.72 | 0.75 | -6.6% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.50 | -1.01 to 0.01 | 0.057 | 0.172 |
| logreg vs always_buy | -0.67 | -1.14 to -0.23 | 0.005 | 0.020 |
| ma_cross_rule vs always_buy | 0.16 | -0.45 to 0.76 | 0.612 | 1.000 |
| momentum_rule vs always_buy | 0.08 | -0.50 to 0.63 | 0.797 | 1.000 |
| random_forest vs always_buy | -0.88 | -1.39 to -0.40 | 0.000 | 0.002 |

**5-day horizon (primary)**, 2014-10-01 to 2026-09-22

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 203.6% | 9.7% | 1.24 | 1.88 | -8.0% | 1.21 | 7.1 | 39.3% | 6.4% (2.7% to 10.0%) | 0.08 | 1.28 | 1.18 | 0.73 | 1.06 | 2.6% |
| ma_cross_rule | 179.0% | 9.0% | 1.20 | 1.84 | -4.9% | 1.82 | 9.8 | 40.1% | 5.6% (2.2% to 9.0%) | 0.09 | 1.26 | 1.12 | 0.67 | 1.03 | 1.9% |
| always_buy | 337.5% | 13.1% | 0.94 | 1.34 | -26.2% | 0.50 | 0.2 | 99.8% | 4.8% | 0.49 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 66.0% | 4.3% | 0.54 | 0.74 | -11.2% | 0.39 | 22.4 | 32.6% | 0.3% (-1.8% to 2.2%) | 0.16 | 0.69 | 0.28 | -0.64 | 0.88 | -1.1% |
| gbt | 77.5% | 4.9% | 0.49 | 0.73 | -13.0% | 0.38 | 13.0 | 30.8% | 0.1% (-2.4% to 2.7%) | 0.23 | 0.56 | 0.38 | -0.10 | 0.59 | -0.2% |
| random_forest | 68.5% | 4.5% | 0.39 | 0.56 | -18.0% | 0.25 | 11.7 | 30.5% | -0.6% (-3.6% to 2.4%) | 0.25 | 0.45 | 0.30 | -0.07 | 0.46 | -0.2% |
| logreg | 39.0% | 2.8% | 0.14 | 0.20 | -18.3% | 0.15 | 11.3 | 30.0% | -2.0% (-5.3% to 1.3%) | 0.23 | 0.20 | 0.06 | -0.41 | 0.30 | -0.9% |
| majority | 27.5% | 2.0% | 0.00 | 0.00 | -0.0% | 1405.91 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.45 | -0.90 to -0.02 | 0.044 | 0.132 |
| logreg vs always_buy | -0.80 | -1.24 to -0.35 | 0.001 | 0.005 |
| ma_cross_rule vs always_buy | 0.26 | -0.30 to 0.81 | 0.326 | 0.596 |
| momentum_rule vs always_buy | 0.30 | -0.27 to 0.87 | 0.298 | 0.596 |
| random_forest vs always_buy | -0.55 | -1.02 to -0.07 | 0.025 | 0.100 |

**20-day horizon**, 2014-10-01 to 2026-08-31

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 213.3% | 10.0% | 1.30 | 1.96 | -8.5% | 1.18 | 3.8 | 42.7% | 6.1% (2.4% to 10.3%) | 0.12 | 1.32 | 1.27 | 0.87 | 0.97 | 2.8% |
| momentum_rule | 209.1% | 9.9% | 1.18 | 1.73 | -12.0% | 0.83 | 3.2 | 44.0% | 5.8% (1.8% to 10.2%) | 0.14 | 1.19 | 1.15 | 0.75 | 0.96 | 2.4% |
| always_buy | 339.8% | 13.2% | 0.95 | 1.35 | -26.2% | 0.50 | 0.2 | 99.3% | 4.9% | 0.49 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 98.8% | 5.9% | 0.92 | 1.31 | -9.3% | 0.63 | 5.7 | 35.3% | 1.7% (-0.2% to 3.6%) | 0.17 | 0.96 | 0.85 | 0.45 | 0.99 | -0.3% |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| logreg | 87.2% | 5.4% | 0.57 | 0.82 | -10.7% | 0.50 | 4.4 | 36.3% | 0.8% (-2.0% to 3.9%) | 0.21 | 0.59 | 0.53 | -0.02 | 0.68 | -0.6% |
| random_forest | 65.5% | 4.3% | 0.40 | 0.57 | -11.8% | 0.37 | 4.3 | 36.4% | -0.5% (-2.8% to 2.0%) | 0.23 | 0.43 | 0.37 | -0.43 | 0.75 | -1.9% |
| gbt | 51.9% | 3.6% | 0.29 | 0.41 | -13.3% | 0.27 | 4.3 | 35.9% | -0.9% (-3.3% to 1.4%) | 0.21 | 0.31 | 0.25 | -0.62 | 0.69 | -1.9% |
| majority | 27.5% | 2.0% | 0.00 | 0.00 | -0.0% | 1405.91 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.66 | -1.15 to -0.20 | 0.006 | 0.032 |
| logreg vs always_buy | -0.38 | -0.92 to 0.13 | 0.162 | 0.367 |
| ma_cross_rule vs always_buy | 0.36 | -0.13 to 0.79 | 0.122 | 0.367 |
| momentum_rule vs always_buy | 0.23 | -0.24 to 0.68 | 0.308 | 0.367 |
| random_forest vs always_buy | -0.54 | -0.99 to -0.09 | 0.023 | 0.094 |

### Folds before the final two years, primary rule

Ranking portfolio: each day hold the top 3 of 10 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1530.8% | 26.3% | 1.18 | 1.79 | -30.5% | 0.86 | 11.9 | 83.4% | 20.0% (9.7% to 32.3%) | 0.26 | 1.20 | 1.15 | 0.79 |
| momentum_rule | 771.3% | 19.8% | 1.05 | 1.63 | -25.9% | 0.76 | 46.7 | 83.4% | 14.6% (5.3% to 24.9%) | 0.23 | 1.14 | 0.91 | 0.40 |
| always_buy | 249.2% | 11.0% | 0.82 | 1.18 | -26.2% | 0.42 | 0.2 | 83.4% | 3.8% | 0.42 | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 105.0% | 6.2% | 0.31 | 0.45 | -44.5% | 0.14 | 137.6 | 83.4% | 2.3% (-9.3% to 13.6%) | 0.26 | 0.55 | -0.07 | -0.44 |
| gbt | 81.7% | 5.1% | 0.26 | 0.36 | -53.4% | 0.10 | 183.8 | 83.4% | -1.2% (-11.1% to 9.2%) | 0.45 | 0.58 | -0.27 | -0.68 |
| random_forest | 47.9% | 3.3% | 0.16 | 0.23 | -33.9% | 0.10 | 142.3 | 83.4% | -1.9% (-9.0% to 5.6%) | 0.33 | 0.47 | -0.36 | -0.64 |
| majority | -22.0% | -2.1% | -0.18 | -0.26 | -52.7% | -0.04 | 295.4 | 83.4% | -7.8% (-16.1% to 1.3%) | 0.40 | 0.38 | -1.11 | -1.01 |
| stratified_random | -22.0% | -2.1% | -0.18 | -0.26 | -52.7% | -0.04 | 295.4 | 83.4% | -7.8% (-16.1% to 1.3%) | 0.40 | 0.38 | -1.11 | -1.01 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.56 | -1.07 to -0.13 | 0.021 | 0.087 |
| logreg vs always_buy | -0.51 | -0.99 to -0.06 | 0.033 | 0.099 |
| ma_cross_rule vs always_buy | 0.36 | -0.12 to 0.82 | 0.141 | 0.283 |
| momentum_rule vs always_buy | 0.23 | -0.34 to 0.78 | 0.418 | 0.418 |
| random_forest vs always_buy | -0.66 | -1.23 to -0.12 | 0.017 | 0.087 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1692.3% | 27.3% | 1.24 | 1.88 | -30.3% | 0.90 | 10.7 | 83.4% | 20.6% (8.9% to 32.0%) | 0.27 | 1.25 | 1.21 | 0.83 |
| momentum_rule | 1125.3% | 23.3% | 1.22 | 1.86 | -19.1% | 1.22 | 16.4 | 83.4% | 17.5% (6.9% to 27.7%) | 0.22 | 1.25 | 1.17 | 0.71 |
| always_buy | 247.9% | 11.0% | 0.82 | 1.17 | -26.2% | 0.42 | 0.2 | 83.4% | 3.7% | 0.42 | n/a | n/a | n/a |
| random_forest | 334.1% | 13.1% | 0.77 | 1.13 | -33.1% | 0.39 | 34.8 | 83.4% | 5.5% (-2.5% to 13.5%) | 0.47 | 0.84 | 0.65 | 0.03 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 358.1% | 13.6% | 0.73 | 1.09 | -27.3% | 0.50 | 28.2 | 83.4% | 8.5% (-1.9% to 18.8%) | 0.28 | 0.79 | 0.65 | 0.22 |
| gbt | 182.7% | 9.1% | 0.51 | 0.74 | -40.6% | 0.22 | 37.8 | 83.4% | 1.9% (-6.7% to 10.2%) | 0.48 | 0.58 | 0.39 | -0.26 |
| majority | 83.7% | 5.2% | 0.31 | 0.43 | -29.2% | 0.18 | 58.6 | 83.4% | -1.3% (-7.7% to 5.0%) | 0.41 | 0.46 | 0.07 | -0.85 |
| stratified_random | 83.7% | 5.2% | 0.31 | 0.43 | -29.2% | 0.18 | 58.6 | 83.4% | -1.3% (-7.7% to 5.0%) | 0.41 | 0.46 | 0.07 | -0.85 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.31 | -0.74 to 0.11 | 0.169 | 0.554 |
| logreg vs always_buy | -0.09 | -0.55 to 0.40 | 0.731 | 1.000 |
| ma_cross_rule vs always_buy | 0.42 | -0.06 to 0.85 | 0.072 | 0.360 |
| momentum_rule vs always_buy | 0.40 | -0.13 to 0.89 | 0.138 | 0.554 |
| random_forest vs always_buy | -0.05 | -0.49 to 0.39 | 0.821 | 1.000 |

**20-day horizon**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 1392.9% | 25.3% | 1.15 | 1.73 | -29.3% | 0.86 | 5.7 | 83.4% | 18.5% (5.5% to 33.0%) | 0.32 | 1.16 | 1.14 | 0.89 |
| momentum_rule | 728.0% | 19.3% | 1.04 | 1.57 | -27.2% | 0.71 | 8.1 | 83.4% | 13.6% (2.2% to 26.6%) | 0.27 | 1.05 | 1.01 | 0.65 |
| logreg | 413.7% | 14.7% | 0.84 | 1.24 | -32.4% | 0.45 | 10.1 | 83.4% | 9.6% (0.1% to 20.3%) | 0.26 | 0.86 | 0.81 | 0.14 |
| always_buy | 248.8% | 11.0% | 0.82 | 1.18 | -26.2% | 0.42 | 0.2 | 83.4% | 3.8% | 0.42 | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| majority | 206.9% | 9.8% | 0.72 | 1.02 | -26.2% | 0.37 | 14.6 | 83.4% | 2.8% (-2.8% to 8.9%) | 0.42 | 0.76 | 0.65 | -0.29 |
| stratified_random | 206.9% | 9.8% | 0.72 | 1.02 | -26.2% | 0.37 | 14.6 | 83.4% | 2.8% (-2.8% to 8.9%) | 0.42 | 0.76 | 0.65 | -0.29 |
| random_forest | 143.4% | 7.7% | 0.55 | 0.78 | -22.1% | 0.35 | 9.5 | 83.4% | 0.5% (-3.7% to 5.3%) | 0.44 | 0.58 | 0.51 | -0.69 |
| gbt | 111.0% | 6.4% | 0.36 | 0.52 | -34.0% | 0.19 | 10.4 | 83.4% | -0.7% (-7.6% to 6.8%) | 0.48 | 0.38 | 0.33 | -0.79 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.46 | -0.97 to -0.05 | 0.046 | 0.232 |
| logreg vs always_buy | 0.02 | -0.51 to 0.50 | 0.960 | 0.960 |
| ma_cross_rule vs always_buy | 0.33 | -0.12 to 0.77 | 0.152 | 0.608 |
| momentum_rule vs always_buy | 0.21 | -0.33 to 0.68 | 0.400 | 0.801 |
| random_forest vs always_buy | -0.27 | -0.73 to 0.10 | 0.224 | 0.673 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 10 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 21493.3% | 56.7% | 1.12 | 1.76 | -63.4% | 0.89 | 15.5 | 83.4% | 52.5% (23.7% to 84.3%) | 0.18 | 1.13 | 1.10 | 0.84 |
| always_buy | 249.2% | 11.0% | 0.82 | 1.18 | -26.2% | 0.42 | 0.2 | 83.4% | 3.8% | 0.42 | n/a | n/a | n/a |
| momentum_rule | 1885.9% | 28.4% | 0.80 | 1.27 | -66.3% | 0.43 | 71.4 | 83.4% | 28.9% (8.0% to 51.8%) | 0.08 | 0.85 | 0.70 | 0.44 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 143.0% | 7.7% | 0.35 | 0.52 | -88.3% | 0.09 | 177.1 | 83.4% | 13.2% (-15.8% to 43.8%) | 0.21 | 0.46 | 0.15 | -0.07 |
| random_forest | 95.4% | 5.8% | 0.27 | 0.41 | -49.5% | 0.12 | 209.6 | 83.4% | 2.8% (-9.9% to 16.6%) | 0.29 | 0.53 | -0.17 | -0.03 |
| gbt | 26.6% | 2.0% | 0.17 | 0.25 | -80.8% | 0.02 | 266.0 | 83.4% | 0.2% (-21.6% to 23.4%) | 0.46 | 0.41 | -0.21 | -0.37 |
| majority | -11.8% | -1.0% | 0.02 | 0.03 | -60.3% | -0.02 | 378.8 | 83.4% | -4.7% (-18.5% to 10.0%) | 0.42 | 0.44 | -0.69 | -0.53 |
| stratified_random | -11.8% | -1.0% | 0.02 | 0.03 | -60.3% | -0.02 | 378.8 | 83.4% | -4.7% (-18.5% to 10.0%) | 0.42 | 0.44 | -0.69 | -0.53 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.65 | -1.31 to -0.11 | 0.037 | 0.185 |
| logreg vs always_buy | -0.48 | -1.11 to 0.09 | 0.125 | 0.458 |
| ma_cross_rule vs always_buy | 0.30 | -0.29 to 0.88 | 0.335 | 0.671 |
| momentum_rule vs always_buy | -0.03 | -0.73 to 0.66 | 0.935 | 0.935 |
| random_forest vs always_buy | -0.56 | -1.24 to 0.12 | 0.114 | 0.458 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 27481.2% | 59.9% | 1.17 | 1.86 | -56.8% | 1.06 | 13.9 | 83.4% | 54.1% (24.7% to 84.3%) | 0.18 | 1.18 | 1.16 | 0.91 |
| momentum_rule | 2311.6% | 30.5% | 0.85 | 1.35 | -43.3% | 0.70 | 28.9 | 83.4% | 30.0% (9.2% to 50.6%) | 0.09 | 0.88 | 0.82 | 0.50 |
| always_buy | 247.9% | 11.0% | 0.82 | 1.17 | -26.2% | 0.42 | 0.2 | 83.4% | 3.7% | 0.42 | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 681.6% | 18.7% | 0.58 | 0.87 | -76.9% | 0.24 | 35.2 | 83.4% | 19.9% (-6.5% to 46.4%) | 0.23 | 0.61 | 0.54 | 0.30 |
| random_forest | 420.1% | 14.8% | 0.57 | 0.84 | -56.5% | 0.26 | 50.3 | 83.4% | 9.7% (-7.4% to 26.7%) | 0.47 | 0.62 | 0.47 | 0.13 |
| majority | 153.0% | 8.1% | 0.45 | 0.68 | -33.3% | 0.24 | 76.2 | 83.4% | 1.8% (-6.3% to 10.0%) | 0.41 | 0.60 | 0.20 | -0.49 |
| stratified_random | 153.0% | 8.1% | 0.45 | 0.68 | -33.3% | 0.24 | 76.2 | 83.4% | 1.8% (-6.3% to 10.0%) | 0.41 | 0.60 | 0.20 | -0.49 |
| gbt | 207.8% | 9.8% | 0.40 | 0.61 | -71.2% | 0.14 | 52.9 | 83.4% | 5.4% (-13.8% to 25.2%) | 0.46 | 0.46 | 0.31 | -0.05 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.42 | -1.11 to 0.25 | 0.223 | 1.000 |
| logreg vs always_buy | -0.24 | -0.81 to 0.35 | 0.440 | 1.000 |
| ma_cross_rule vs always_buy | 0.35 | -0.21 to 0.89 | 0.229 | 1.000 |
| momentum_rule vs always_buy | 0.03 | -0.64 to 0.69 | 0.924 | 1.000 |
| random_forest vs always_buy | -0.26 | -0.88 to 0.37 | 0.415 | 1.000 |

**20-day horizon**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 11187.2% | 48.4% | 1.01 | 1.54 | -63.5% | 0.76 | 7.0 | 83.4% | 46.4% (11.3% to 85.9%) | 0.25 | 1.01 | 1.00 | 0.95 |
| always_buy | 248.8% | 11.0% | 0.82 | 1.18 | -26.2% | 0.42 | 0.2 | 83.4% | 3.8% | 0.42 | n/a | n/a | n/a |
| momentum_rule | 1425.1% | 25.6% | 0.80 | 1.21 | -45.5% | 0.56 | 12.7 | 83.4% | 23.8% (4.3% to 45.8%) | 0.18 | 0.81 | 0.78 | 0.59 |
| majority | 249.1% | 11.0% | 0.76 | 1.09 | -28.0% | 0.39 | 18.8 | 83.4% | 4.0% (-2.2% to 10.3%) | 0.42 | 0.81 | 0.69 | 0.01 |
| stratified_random | 249.1% | 11.0% | 0.76 | 1.09 | -28.0% | 0.39 | 18.8 | 83.4% | 4.0% (-2.2% to 10.3%) | 0.42 | 0.81 | 0.69 | 0.01 |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 1363.3% | 25.1% | 0.73 | 1.10 | -74.9% | 0.34 | 12.4 | 83.4% | 25.0% (0.3% to 52.1%) | 0.19 | 0.74 | 0.72 | 0.32 |
| random_forest | 106.7% | 6.3% | 0.42 | 0.60 | -14.7% | 0.43 | 13.5 | 83.4% | 0.1% (-4.2% to 4.4%) | 0.37 | 0.45 | 0.36 | -0.97 |
| gbt | 43.2% | 3.0% | 0.15 | 0.21 | -52.4% | 0.06 | 15.0 | 83.4% | -2.8% (-12.5% to 8.3%) | 0.47 | 0.17 | 0.11 | -0.91 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.67 | -1.28 to -0.15 | 0.021 | 0.105 |
| logreg vs always_buy | -0.09 | -0.73 to 0.52 | 0.790 | 1.000 |
| ma_cross_rule vs always_buy | 0.19 | -0.36 to 0.68 | 0.481 | 1.000 |
| momentum_rule vs always_buy | -0.02 | -0.61 to 0.53 | 0.936 | 1.000 |
| random_forest vs always_buy | -0.40 | -1.07 to 0.20 | 0.219 | 0.878 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 139.4% | 7.6% | 0.98 | 1.50 | -7.7% | 0.99 | 15.2 | 34.3% | 4.5% (1.3% to 8.3%) | 0.07 | 1.07 | 0.85 | 0.58 | 0.98 | 1.0% |
| momentum_rule | 145.0% | 7.8% | 0.98 | 1.53 | -7.4% | 1.04 | 14.0 | 34.8% | 4.7% (1.4% to 8.4%) | 0.08 | 1.05 | 0.86 | 0.58 | 0.94 | 1.3% |
| always_buy | 249.2% | 11.0% | 0.82 | 1.18 | -26.2% | 0.42 | 0.2 | 83.4% | 3.8% | 0.42 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| gbt | 63.4% | 4.2% | 0.40 | 0.58 | -15.4% | 0.27 | 41.9 | 22.0% | 0.1% (-2.9% to 3.1%) | 0.17 | 0.62 | 0.02 | -0.39 | 0.47 | -0.1% |
| logreg | 43.0% | 3.0% | 0.18 | 0.26 | -20.3% | 0.15 | 27.4 | 20.8% | -1.0% (-4.7% to 2.7%) | 0.17 | 0.32 | -0.03 | -0.42 | 0.31 | -0.6% |
| majority | 27.5% | 2.0% | 0.00 | 0.00 | -0.0% | 1405.91 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| random_forest | 24.3% | 1.8% | -0.02 | -0.03 | -14.9% | 0.12 | 30.7 | 21.4% | -1.9% (-4.5% to 0.7%) | 0.14 | 0.17 | -0.34 | -0.53 | 0.30 | -1.5% |
| stratified_random | -11.6% | -1.0% | -0.55 | -0.73 | -23.9% | -0.04 | 87.3 | 24.9% | -4.6% (-8.0% to -1.5%) | 0.14 | -0.06 | -1.38 | -1.64 | 0.68 | -5.5% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.43 | -0.94 to 0.08 | 0.098 | 0.294 |
| logreg vs always_buy | -0.64 | -1.11 to -0.18 | 0.007 | 0.028 |
| ma_cross_rule vs always_buy | 0.16 | -0.44 to 0.79 | 0.604 | 1.000 |
| momentum_rule vs always_buy | 0.16 | -0.44 to 0.74 | 0.616 | 1.000 |
| random_forest vs always_buy | -0.84 | -1.34 to -0.35 | 0.001 | 0.005 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 179.3% | 9.0% | 1.19 | 1.82 | -8.0% | 1.12 | 5.1 | 32.8% | 5.8% (2.2% to 9.2%) | 0.08 | 1.22 | 1.14 | 0.73 | 0.97 | 2.5% |
| ma_cross_rule | 145.1% | 7.8% | 1.08 | 1.66 | -4.9% | 1.58 | 8.1 | 32.8% | 4.6% (1.3% to 7.8%) | 0.08 | 1.12 | 1.00 | 0.65 | 0.96 | 1.5% |
| always_buy | 247.9% | 11.0% | 0.82 | 1.17 | -26.2% | 0.42 | 0.2 | 83.4% | 3.7% | 0.42 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 55.1% | 3.7% | 0.43 | 0.59 | -11.2% | 0.33 | 18.6 | 27.1% | -0.0% (-2.2% to 1.9%) | 0.14 | 0.57 | 0.20 | -0.67 | 0.76 | -1.1% |
| gbt | 62.0% | 4.1% | 0.39 | 0.57 | -13.0% | 0.32 | 10.5 | 24.8% | -0.3% (-2.8% to 2.4%) | 0.20 | 0.44 | 0.29 | -0.13 | 0.45 | -0.1% |
| random_forest | 53.4% | 3.6% | 0.28 | 0.40 | -18.0% | 0.20 | 9.4 | 25.2% | -0.9% (-4.1% to 2.1%) | 0.21 | 0.33 | 0.21 | -0.10 | 0.34 | -0.2% |
| logreg | 32.9% | 2.4% | 0.09 | 0.12 | -18.3% | 0.13 | 9.3 | 24.8% | -1.8% (-5.1% to 1.4%) | 0.18 | 0.14 | 0.01 | -0.38 | 0.18 | -0.5% |
| majority | 27.5% | 2.0% | 0.00 | 0.00 | -0.0% | 1405.91 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.43 | -0.87 to -0.01 | 0.048 | 0.145 |
| logreg vs always_buy | -0.73 | -1.20 to -0.27 | 0.002 | 0.010 |
| ma_cross_rule vs always_buy | 0.26 | -0.29 to 0.81 | 0.351 | 0.437 |
| momentum_rule vs always_buy | 0.37 | -0.21 to 0.94 | 0.218 | 0.437 |
| random_forest vs always_buy | -0.54 | -1.01 to -0.04 | 0.033 | 0.132 |

**20-day horizon**, 2014-10-01 to 2024-09-30

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 179.8% | 9.0% | 1.21 | 1.85 | -8.5% | 1.06 | 3.1 | 34.7% | 5.4% (1.6% to 9.6%) | 0.11 | 1.23 | 1.18 | 0.84 | 0.90 | 2.5% |
| momentum_rule | 173.9% | 8.8% | 1.12 | 1.66 | -12.0% | 0.73 | 2.6 | 35.7% | 5.3% (1.1% to 9.8%) | 0.11 | 1.13 | 1.09 | 0.71 | 0.91 | 2.2% |
| always_buy | 248.8% | 11.0% | 0.82 | 1.18 | -26.2% | 0.42 | 0.2 | 83.4% | 3.8% | 0.42 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 83.1% | 5.2% | 0.81 | 1.15 | -9.3% | 0.56 | 4.8 | 29.6% | 1.3% (-0.7% to 3.4%) | 0.15 | 0.84 | 0.74 | 0.33 | 0.86 | -0.3% |
| market_buy_and_hold | 375.5% | 13.9% | 0.74 | 1.02 | -32.0% | 0.43 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| logreg | 78.8% | 5.0% | 0.54 | 0.79 | -10.7% | 0.46 | 3.7 | 30.6% | 0.9% (-1.9% to 4.2%) | 0.17 | 0.56 | 0.51 | 0.05 | 0.57 | -0.0% |
| random_forest | 52.5% | 3.6% | 0.30 | 0.42 | -11.8% | 0.31 | 3.6 | 31.0% | -0.8% (-3.2% to 1.7%) | 0.20 | 0.32 | 0.26 | -0.48 | 0.62 | -1.7% |
| gbt | 41.9% | 3.0% | 0.19 | 0.28 | -13.3% | 0.22 | 3.6 | 30.3% | -1.2% (-3.6% to 1.3%) | 0.18 | 0.21 | 0.16 | -0.65 | 0.57 | -1.7% |
| majority | 27.5% | 2.0% | 0.00 | 0.00 | -0.0% | 1405.91 | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.63 | -1.12 to -0.19 | 0.010 | 0.052 |
| logreg vs always_buy | -0.28 | -0.84 to 0.22 | 0.306 | 0.435 |
| ma_cross_rule vs always_buy | 0.39 | -0.11 to 0.84 | 0.104 | 0.313 |
| momentum_rule vs always_buy | 0.29 | -0.18 to 0.74 | 0.217 | 0.435 |
| random_forest vs always_buy | -0.53 | -1.02 to -0.05 | 0.036 | 0.146 |

### Final two years, primary rule

Ranking portfolio: each day hold the top 3 of 10 assets by score, fully invested.

**1-day horizon**, 2024-10-01 to 2026-09-28

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 94.0% | 39.6% | 1.87 | 2.77 | -9.2% | 4.32 | 20.7 | 99.8% | 28.0% (7.6% to 51.1%) | 0.22 | 1.91 | 1.81 | 1.06 |
| always_buy | 35.3% | 16.4% | 1.18 | 1.64 | -10.6% | 1.55 | 0.5 | 99.8% | 6.0% | 0.44 | n/a | n/a | n/a |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| momentum_rule | 34.4% | 16.1% | 0.78 | 1.09 | -9.8% | 1.64 | 62.3 | 99.8% | 9.8% (-6.5% to 28.2%) | 0.18 | 0.90 | 0.58 | 0.08 |
| gbt | 25.2% | 12.0% | 0.57 | 0.89 | -19.1% | 0.63 | 215.2 | 99.8% | 2.6% (-16.5% to 23.5%) | 0.44 | 1.01 | -0.16 | -0.71 |
| logreg | 7.7% | 3.8% | 0.05 | 0.08 | -13.6% | 0.28 | 169.8 | 99.8% | -2.9% (-18.8% to 15.6%) | 0.27 | 0.42 | -0.55 | -1.14 |
| random_forest | 1.9% | 0.9% | -0.15 | -0.21 | -20.8% | 0.04 | 185.3 | 99.8% | -7.2% (-22.4% to 10.3%) | 0.39 | 0.25 | -0.82 | -0.80 |
| majority | -2.3% | -1.2% | -0.24 | -0.33 | -14.9% | -0.08 | 357.0 | 99.8% | -9.5% (-27.0% to 8.1%) | 0.43 | 0.43 | -1.34 | -1.67 |
| stratified_random | -2.3% | -1.2% | -0.24 | -0.33 | -14.9% | -0.08 | 357.0 | 99.8% | -9.5% (-27.0% to 8.1%) | 0.43 | 0.43 | -1.34 | -1.67 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.60 | -2.11 to 0.60 | 0.381 | 0.763 |
| logreg vs always_buy | -1.12 | -2.47 to 0.04 | 0.075 | 0.300 |
| ma_cross_rule vs always_buy | 0.70 | -0.52 to 1.71 | 0.228 | 0.685 |
| momentum_rule vs always_buy | -0.39 | -1.63 to 0.63 | 0.482 | 0.763 |
| random_forest vs always_buy | -1.33 | -2.78 to -0.17 | 0.047 | 0.235 |

**5-day horizon (primary)**, 2024-10-01 to 2026-09-22

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 87.7% | 37.4% | 1.76 | 2.61 | -11.0% | 3.40 | 16.9 | 99.0% | 26.0% (5.0% to 49.9%) | 0.24 | 1.79 | 1.70 | 0.93 |
| logreg | 45.5% | 20.8% | 1.24 | 1.83 | -9.9% | 2.09 | 37.1 | 99.0% | 13.1% (0.5% to 27.6%) | 0.20 | 1.33 | 1.10 | -0.15 |
| always_buy | 35.9% | 16.7% | 1.20 | 1.67 | -10.6% | 1.57 | 0.9 | 99.0% | 6.2% | 0.43 | n/a | n/a | n/a |
| majority | 33.1% | 15.5% | 1.01 | 1.40 | -10.7% | 1.45 | 67.6 | 99.0% | 5.8% (-6.0% to 17.6%) | 0.40 | 1.19 | 0.70 | -0.82 |
| stratified_random | 33.1% | 15.5% | 1.01 | 1.40 | -10.7% | 1.45 | 67.6 | 99.0% | 5.8% (-6.0% to 17.6%) | 0.40 | 1.19 | 0.70 | -0.82 |
| random_forest | 33.3% | 15.6% | 0.98 | 1.44 | -10.6% | 1.47 | 42.2 | 99.0% | 5.1% (-5.6% to 15.9%) | 0.46 | 1.09 | 0.79 | -0.28 |
| gbt | 33.4% | 15.6% | 0.84 | 1.21 | -12.7% | 1.22 | 47.0 | 99.0% | 4.5% (-12.4% to 20.8%) | 0.53 | 0.94 | 0.67 | 0.33 |
| momentum_rule | 33.7% | 15.7% | 0.80 | 1.11 | -11.4% | 1.38 | 37.9 | 99.0% | 8.9% (-8.1% to 27.7%) | 0.21 | 0.88 | 0.67 | 0.48 |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.36 | -1.37 to 0.46 | 0.451 | 1.000 |
| logreg vs always_buy | 0.04 | -1.32 to 1.17 | 0.948 | 1.000 |
| ma_cross_rule vs always_buy | 0.55 | -0.68 to 1.57 | 0.337 | 1.000 |
| momentum_rule vs always_buy | -0.40 | -1.56 to 0.57 | 0.433 | 1.000 |
| random_forest vs always_buy | -0.22 | -1.24 to 0.61 | 0.654 | 1.000 |

**20-day horizon**, 2024-10-01 to 2026-08-31

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 49.5% | 22.5% | 1.32 | 1.88 | -8.1% | 2.77 | 11.0 | 96.0% | 13.8% (2.3% to 26.1%) | 0.26 | 1.35 | 1.28 | 0.84 |
| majority | 39.0% | 18.0% | 1.30 | 1.81 | -10.3% | 1.75 | 17.0 | 96.0% | 7.6% (-0.1% to 15.7%) | 0.42 | 1.35 | 1.21 | 0.29 |
| stratified_random | 39.0% | 18.0% | 1.30 | 1.81 | -10.3% | 1.75 | 17.0 | 96.0% | 7.6% (-0.1% to 15.7%) | 0.42 | 1.35 | 1.21 | 0.29 |
| always_buy | 36.3% | 16.9% | 1.22 | 1.71 | -10.6% | 1.59 | 1.0 | 96.0% | 6.4% | 0.43 | n/a | n/a | n/a |
| ma_cross_rule | 45.3% | 20.7% | 0.99 | 1.38 | -13.1% | 1.59 | 7.9 | 96.0% | 10.6% (-5.5% to 26.4%) | 0.42 | 1.01 | 0.97 | -0.03 |
| logreg | 28.0% | 13.2% | 0.79 | 1.13 | -10.9% | 1.22 | 11.8 | 96.0% | 6.8% (-5.1% to 21.0%) | 0.18 | 0.82 | 0.74 | 0.07 |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| random_forest | 20.2% | 9.7% | 0.57 | 0.80 | -11.5% | 0.84 | 9.5 | 96.0% | 1.0% (-6.5% to 8.7%) | 0.37 | 0.60 | 0.52 | -0.83 |
| gbt | 16.8% | 8.2% | 0.35 | 0.49 | -18.1% | 0.45 | 12.3 | 96.0% | -0.9% (-17.8% to 18.9%) | 0.43 | 0.38 | 0.31 | -0.91 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.87 | -2.09 to 0.32 | 0.170 | 0.852 |
| logreg vs always_buy | -0.44 | -1.37 to 0.44 | 0.331 | 0.994 |
| ma_cross_rule vs always_buy | -0.23 | -1.14 to 0.61 | 0.581 | 1.000 |
| momentum_rule vs always_buy | 0.10 | -0.85 to 0.86 | 0.808 | 1.000 |
| random_forest vs always_buy | -0.65 | -1.78 to 0.29 | 0.216 | 0.864 |

### Final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 10 assets by score, fully invested.

**1-day horizon**, 2024-10-01 to 2026-09-28

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 261.0% | 91.0% | 1.65 | 2.60 | -20.6% | 4.41 | 19.7 | 99.8% | 72.2% (17.7% to 136.9%) | -0.19 | 1.67 | 1.63 | 1.05 |
| always_buy | 35.3% | 16.4% | 1.18 | 1.64 | -10.6% | 1.55 | 0.5 | 99.8% | 6.0% | 0.44 | n/a | n/a | n/a |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| majority | 21.5% | 10.3% | 0.35 | 0.50 | -25.8% | 0.40 | 448.1 | 99.8% | 5.1% (-27.4% to 37.9%) | 0.32 | 0.86 | -0.49 | -0.88 |
| stratified_random | 21.5% | 10.3% | 0.35 | 0.50 | -25.8% | 0.40 | 448.1 | 99.8% | 5.1% (-27.4% to 37.9%) | 0.32 | 0.86 | -0.49 | -0.88 |
| logreg | 15.0% | 7.3% | 0.26 | 0.36 | -40.2% | 0.18 | 238.4 | 99.8% | 8.0% (-28.0% to 54.3%) | 0.03 | 0.48 | -0.11 | -0.51 |
| momentum_rule | 3.3% | 1.7% | 0.10 | 0.14 | -22.0% | 0.08 | 104.3 | 99.8% | 6.1% (-32.6% to 52.1%) | -0.22 | 0.19 | -0.06 | -0.26 |
| random_forest | -11.9% | -6.2% | -0.31 | -0.40 | -36.9% | -0.17 | 297.9 | 99.8% | -13.6% (-38.3% to 10.9%) | 0.46 | 0.06 | -0.94 | -0.48 |
| gbt | -47.3% | -27.6% | -1.10 | -1.41 | -49.0% | -0.56 | 315.0 | 99.8% | -37.8% (-69.6% to -5.6%) | 0.44 | -0.77 | -1.64 | -1.17 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -2.27 | -3.86 to -1.00 | 0.002 | 0.010 |
| logreg vs always_buy | -0.92 | -2.61 to 0.60 | 0.255 | 0.636 |
| ma_cross_rule vs always_buy | 0.48 | -1.17 to 1.99 | 0.542 | 0.636 |
| momentum_rule vs always_buy | -1.08 | -2.91 to 0.53 | 0.212 | 0.636 |
| random_forest vs always_buy | -1.49 | -3.08 to -0.09 | 0.054 | 0.216 |

**5-day horizon (primary)**, 2024-10-01 to 2026-09-22

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 276.9% | 95.2% | 1.73 | 2.70 | -18.8% | 5.06 | 18.0 | 99.0% | 73.8% (24.8% to 131.2%) | -0.17 | 1.74 | 1.71 | 1.15 |
| always_buy | 35.9% | 16.7% | 1.20 | 1.67 | -10.6% | 1.57 | 0.9 | 99.0% | 6.2% | 0.43 | n/a | n/a | n/a |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 59.9% | 26.7% | 0.78 | 1.13 | -18.8% | 1.42 | 50.5 | 99.0% | 25.0% (-5.7% to 62.2%) | -0.01 | 0.83 | 0.70 | 0.22 |
| random_forest | 33.9% | 15.8% | 0.76 | 1.13 | -12.4% | 1.28 | 64.2 | 99.0% | 6.8% (-9.2% to 24.7%) | 0.39 | 0.88 | 0.55 | 0.16 |
| momentum_rule | 53.5% | 24.1% | 0.75 | 1.04 | -22.1% | 1.09 | 53.7 | 99.0% | 24.8% (-5.3% to 60.9%) | -0.21 | 0.80 | 0.66 | 0.30 |
| gbt | 30.3% | 14.2% | 0.59 | 0.90 | -17.4% | 0.82 | 65.6 | 99.0% | 3.4% (-21.8% to 28.7%) | 0.58 | 0.70 | 0.42 | 0.08 |
| majority | 11.6% | 5.7% | 0.19 | 0.25 | -10.0% | 0.57 | 89.2 | 99.0% | -2.4% (-15.3% to 10.8%) | 0.37 | 0.39 | -0.15 | -0.92 |
| stratified_random | 11.6% | 5.7% | 0.19 | 0.25 | -10.0% | 0.57 | 89.2 | 99.0% | -2.4% (-15.3% to 10.8%) | 0.37 | 0.39 | -0.15 | -0.92 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.61 | -1.78 to 0.35 | 0.272 | 1.000 |
| logreg vs always_buy | -0.42 | -2.01 to 0.99 | 0.579 | 1.000 |
| ma_cross_rule vs always_buy | 0.53 | -1.25 to 1.95 | 0.485 | 1.000 |
| momentum_rule vs always_buy | -0.45 | -2.13 to 1.01 | 0.554 | 1.000 |
| random_forest vs always_buy | -0.44 | -1.94 to 0.79 | 0.524 | 1.000 |

**20-day horizon**, 2024-10-01 to 2026-08-31

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_buy | 36.3% | 16.9% | 1.22 | 1.71 | -10.6% | 1.59 | 1.0 | 96.0% | 6.4% | 0.43 | n/a | n/a | n/a |
| ma_cross_rule | 118.6% | 48.3% | 1.19 | 1.75 | -32.7% | 1.48 | 9.4 | 96.0% | 40.8% (1.2% to 84.5%) | 0.07 | 1.19 | 1.17 | 0.58 |
| random_forest | 33.8% | 15.8% | 0.90 | 1.29 | -8.9% | 1.78 | 16.9 | 96.0% | 8.3% (0.4% to 19.7%) | 0.25 | 0.94 | 0.84 | 0.14 |
| momentum_rule | 51.4% | 23.2% | 0.82 | 1.12 | -17.0% | 1.36 | 14.5 | 96.0% | 21.3% (0.6% to 50.1%) | -0.10 | 0.84 | 0.79 | 0.31 |
| majority | 27.3% | 12.9% | 0.81 | 1.10 | -11.0% | 1.17 | 21.9 | 96.0% | 2.7% (-6.6% to 12.6%) | 0.46 | 0.87 | 0.71 | 0.26 |
| stratified_random | 27.3% | 12.9% | 0.81 | 1.10 | -11.0% | 1.17 | 21.9 | 96.0% | 2.7% (-6.6% to 12.6%) | 0.46 | 0.87 | 0.71 | 0.26 |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| logreg | 40.7% | 18.8% | 0.62 | 0.88 | -21.2% | 0.89 | 16.7 | 96.0% | 17.2% (-6.9% to 54.4%) | -0.01 | 0.64 | 0.59 | 0.35 |
| gbt | -10.4% | -5.4% | -0.43 | -0.55 | -33.8% | -0.16 | 18.1 | 96.0% | -12.3% (-42.4% to 10.9%) | 0.34 | -0.40 | -0.48 | -1.23 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -1.65 | -2.98 to -0.12 | 0.016 | 0.080 |
| logreg vs always_buy | -0.60 | -1.65 to 0.24 | 0.206 | 0.824 |
| ma_cross_rule vs always_buy | -0.04 | -1.36 to 1.22 | 0.955 | 1.000 |
| momentum_rule vs always_buy | -0.40 | -1.77 to 0.76 | 0.492 | 1.000 |
| random_forest vs always_buy | -0.32 | -1.42 to 0.60 | 0.507 | 1.000 |

### Final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2024-10-01 to 2026-09-28

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 22.2% | 10.6% | 1.21 | 1.75 | -2.6% | 4.03 | 24.3 | 44.6% | 5.8% (-0.4% to 12.5%) | 0.04 | 1.35 | 0.97 | 0.30 | 0.78 | 3.3% |
| always_buy | 35.3% | 16.4% | 1.18 | 1.64 | -10.6% | 1.55 | 0.5 | 99.8% | 6.0% | 0.44 | n/a | n/a | n/a | n/a | n/a |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 16.2% | 7.8% | 0.70 | 0.98 | -4.0% | 1.94 | 21.2 | 41.4% | 3.0% (-3.2% to 9.9%) | 0.05 | 0.82 | 0.50 | 0.30 | 1.08 | -0.4% |
| logreg | 16.5% | 8.0% | 0.58 | 0.85 | -8.6% | 0.93 | 46.5 | 29.8% | 0.5% (-6.0% to 7.6%) | 0.27 | 0.78 | 0.24 | -0.04 | 1.08 | -2.9% |
| gbt | 14.2% | 6.9% | 0.47 | 0.75 | -3.8% | 1.82 | 57.0 | 35.3% | 0.4% (-5.4% to 7.1%) | 0.19 | 0.75 | 0.01 | -0.11 | 1.16 | -3.1% |
| random_forest | 13.0% | 6.4% | 0.40 | 0.59 | -5.4% | 1.18 | 45.5 | 33.6% | -0.1% (-6.0% to 6.2%) | 0.19 | 0.63 | 0.02 | -0.20 | 0.98 | -3.0% |
| majority | 8.1% | 4.0% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |
| stratified_random | -0.1% | -0.0% | -0.82 | -1.06 | -4.9% | -0.01 | 105.4 | 30.4% | -5.5% (-11.2% to 0.2%) | 0.13 | -0.15 | -1.93 | -1.30 | 0.78 | -6.7% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.70 | -2.08 to 0.37 | 0.282 | 1.000 |
| logreg vs always_buy | -0.60 | -1.73 to 0.61 | 0.277 | 1.000 |
| ma_cross_rule vs always_buy | 0.03 | -1.16 to 1.01 | 0.957 | 1.000 |
| momentum_rule vs always_buy | -0.48 | -1.72 to 0.50 | 0.390 | 1.000 |
| random_forest vs always_buy | -0.77 | -2.14 to 0.35 | 0.223 | 1.000 |

**5-day horizon (primary)**, 2024-10-01 to 2026-09-22

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 23.0% | 11.0% | 1.35 | 1.97 | -2.6% | 4.23 | 11.0 | 44.3% | 6.1% (0.3% to 12.2%) | 0.04 | 1.42 | 1.24 | 0.42 | 0.93 | 3.0% |
| always_buy | 35.9% | 16.7% | 1.20 | 1.67 | -10.6% | 1.57 | 0.9 | 99.0% | 6.2% | 0.43 | n/a | n/a | n/a | n/a | n/a |
| stratified_random | 15.7% | 7.6% | 0.95 | 1.35 | -3.7% | 2.06 | 22.8 | 33.0% | 1.7% (-1.7% to 5.5%) | 0.13 | 1.14 | 0.64 | -0.04 | 1.18 | -0.6% |
| gbt | 18.5% | 8.9% | 0.89 | 1.36 | -3.0% | 3.02 | 15.0 | 36.6% | 1.9% (-2.9% to 7.2%) | 0.21 | 0.98 | 0.75 | 0.21 | 1.10 | -0.7% |
| random_forest | 18.7% | 9.0% | 0.89 | 1.39 | -4.7% | 1.95 | 14.0 | 31.9% | 1.8% (-2.4% to 6.9%) | 0.23 | 0.97 | 0.76 | 0.23 | 1.00 | -0.5% |
| momentum_rule | 17.5% | 8.5% | 0.89 | 1.22 | -3.7% | 2.28 | 12.5 | 38.7% | 3.7% (-2.4% to 10.0%) | 0.05 | 0.96 | 0.76 | 0.31 | 1.09 | 0.4% |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| logreg | 13.0% | 6.4% | 0.39 | 0.56 | -7.8% | 0.82 | 12.5 | 31.4% | -1.3% (-6.8% to 4.7%) | 0.28 | 0.45 | 0.29 | -0.41 | 0.76 | -2.6% |
| majority | 8.1% | 4.0% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.31 | -1.47 to 0.62 | 0.561 | 1.000 |
| logreg vs always_buy | -0.81 | -1.96 to 0.47 | 0.162 | 0.810 |
| ma_cross_rule vs always_buy | 0.15 | -1.11 to 1.15 | 0.784 | 1.000 |
| momentum_rule vs always_buy | -0.31 | -1.63 to 0.73 | 0.599 | 1.000 |
| random_forest vs always_buy | -0.31 | -1.46 to 0.72 | 0.556 | 1.000 |

**20-day horizon**, 2024-10-01 to 2026-08-31

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| always_buy | 36.3% | 16.9% | 1.22 | 1.71 | -10.6% | 1.59 | 1.0 | 96.0% | 6.4% | 0.43 | n/a | n/a | n/a | n/a | n/a |
| ma_cross_rule | 21.1% | 10.1% | 1.19 | 1.64 | -3.0% | 3.37 | 4.3 | 48.5% | 4.3% (0.4% to 8.6%) | 0.11 | 1.22 | 1.15 | 0.56 | 0.87 | 1.8% |
| stratified_random | 17.4% | 8.4% | 1.16 | 1.61 | -3.4% | 2.49 | 5.7 | 34.5% | 2.2% (-0.4% to 4.6%) | 0.15 | 1.20 | 1.08 | 0.95 | 1.24 | -0.2% |
| random_forest | 17.3% | 8.4% | 1.03 | 1.47 | -4.5% | 1.87 | 3.9 | 32.8% | 2.0% (-0.7% to 4.9%) | 0.17 | 1.06 | 0.98 | 0.32 | 1.27 | -1.6% |
| momentum_rule | 22.0% | 10.5% | 0.95 | 1.32 | -7.5% | 1.41 | 4.3 | 50.1% | 3.2% (-1.9% to 9.9%) | 0.23 | 0.97 | 0.92 | 0.59 | 0.77 | 1.8% |
| gbt | 15.7% | 7.6% | 0.83 | 1.15 | -3.6% | 2.14 | 4.5 | 33.5% | 1.5% (-3.0% to 6.5%) | 0.15 | 0.86 | 0.77 | 0.06 | 1.20 | -1.3% |
| market_buy_and_hold | 36.8% | 17.1% | 0.79 | 1.17 | -19.8% | 0.86 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| logreg | 13.2% | 6.4% | 0.42 | 0.58 | -7.9% | 0.82 | 4.5 | 34.6% | -1.0% (-4.3% to 3.1%) | 0.26 | 0.45 | 0.39 | -0.55 | 0.92 | -3.3% |
| majority | 8.1% | 4.0% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.0% (0.0% to 0.0%) | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.40 | -1.45 to 0.74 | 0.483 | 1.000 |
| logreg vs always_buy | -0.80 | -1.59 to 0.32 | 0.084 | 0.422 |
| ma_cross_rule vs always_buy | -0.03 | -1.03 to 0.85 | 0.946 | 1.000 |
| momentum_rule vs always_buy | -0.27 | -0.95 to 0.44 | 0.420 | 1.000 |
| random_forest vs always_buy | -0.19 | -0.99 to 0.75 | 0.647 | 1.000 |

## 5. What this run can detect

At the 5-day horizon on all folds, the 95% interval on a net Sharpe difference is typically ±0.45 (median of 5 comparisons). A true difference smaller than about 0.65 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (all folds)

### 1-day horizon

29,909 test observations on 3,015 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.374 | 0.375 | 0.400 | 1.090 | 0.659 | 0.016 | 0.508 | 27/47/26 | 0.0% |
| gbt | 0.370 | 0.371 | 0.383 | 1.095 | 0.663 | 0.035 | 0.513 | 32/40/28 | 0.0% |
| random_forest | 0.370 | 0.370 | 0.398 | 1.088 | 0.659 | 0.026 | 0.513 | 24/48/27 | 0.0% |
| momentum_rule | 0.342 | 0.346 | 0.356 | n/a | n/a | n/a | 0.521 | 21/37/42 | 0.0% |
| stratified_random | 0.332 | 0.332 | 0.350 | 1.072 | 0.648 | 0.001 | 0.503 | 26/44/30 | 0.0% |
| ma_cross_rule | 0.330 | 0.334 | 0.343 | n/a | n/a | n/a | 0.526 | 20/38/42 | 0.0% |
| majority | 0.204 | 0.333 | 0.441 | 1.072 | 0.648 | 0.001 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.8%, HOLD 44.1%, BUY 30.0%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.274 | 0.500 | 0.343 | 0.341 | 0.450 | 0.321 | 0.035% | 0.044% | 0.084% |
| logreg | 0.282 | 0.502 | 0.341 | 0.296 | 0.534 | 0.294 | 0.024% | 0.063% | 0.063% |
| ma_cross_rule | 0.293 | 0.430 | 0.289 | 0.229 | 0.367 | 0.405 | 0.015% | 0.043% | 0.079% |
| majority | 0.000 | 0.441 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.052% | n/a |
| momentum_rule | 0.294 | 0.457 | 0.297 | 0.237 | 0.385 | 0.416 | 0.002% | 0.054% | 0.076% |
| random_forest | 0.285 | 0.491 | 0.334 | 0.270 | 0.539 | 0.303 | 0.025% | 0.072% | 0.041% |
| stratified_random | 0.259 | 0.439 | 0.298 | 0.260 | 0.436 | 0.300 | 0.061% | 0.062% | 0.030% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0378 | 0.0284 to 0.0470 | 0.000 | 0.002 |
| logreg vs stratified_random | 0.0420 | 0.0328 to 0.0510 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | -0.0018 | -0.0114 to 0.0076 | 0.711 | 0.711 |
| momentum_rule vs stratified_random | 0.0106 | 0.0012 to 0.0198 | 0.024 | 0.049 |
| random_forest vs stratified_random | 0.0377 | 0.0289 to 0.0460 | 0.000 | 0.002 |

### 5-day horizon (primary)

29,869 test observations on 3,011 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.366 | 0.366 | 0.379 | 1.093 | 0.663 | 0.016 | 0.507 | 29/41/31 | 0.0% |
| logreg | 0.365 | 0.365 | 0.385 | 1.102 | 0.665 | 0.020 | 0.499 | 26/44/30 | 0.0% |
| gbt | 0.360 | 0.361 | 0.368 | 1.124 | 0.682 | 0.088 | 0.506 | 32/37/31 | 0.0% |
| momentum_rule | 0.346 | 0.347 | 0.357 | n/a | n/a | n/a | 0.535 | 23/37/40 | 0.0% |
| ma_cross_rule | 0.335 | 0.336 | 0.349 | n/a | n/a | n/a | 0.528 | 20/39/41 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.346 | 1.079 | 0.654 | 0.006 | 0.506 | 26/41/33 | 0.0% |
| majority | 0.196 | 0.333 | 0.416 | 1.079 | 0.654 | 0.006 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.3%, HOLD 41.6%, BUY 33.1%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.258 | 0.467 | 0.364 | 0.325 | 0.416 | 0.343 | 0.220% | 0.300% | 0.273% |
| logreg | 0.260 | 0.474 | 0.361 | 0.262 | 0.503 | 0.331 | 0.293% | 0.336% | 0.143% |
| ma_cross_rule | 0.287 | 0.413 | 0.317 | 0.230 | 0.388 | 0.389 | 0.123% | 0.195% | 0.406% |
| majority | 0.000 | 0.416 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.266% | n/a |
| momentum_rule | 0.283 | 0.427 | 0.335 | 0.262 | 0.379 | 0.402 | 0.109% | 0.181% | 0.438% |
| random_forest | 0.263 | 0.473 | 0.365 | 0.296 | 0.461 | 0.340 | 0.190% | 0.339% | 0.240% |
| stratified_random | 0.253 | 0.418 | 0.331 | 0.260 | 0.413 | 0.329 | 0.281% | 0.268% | 0.252% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0262 | 0.0115 to 0.0402 | 0.000 | 0.002 |
| logreg vs stratified_random | 0.0309 | 0.0179 to 0.0427 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | 0.0011 | -0.0110 to 0.0130 | 0.862 | 0.862 |
| momentum_rule vs stratified_random | 0.0123 | -0.0003 to 0.0255 | 0.065 | 0.131 |
| random_forest vs stratified_random | 0.0318 | 0.0171 to 0.0456 | 0.000 | 0.002 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,457 | 2,594 | 2,513 | 0 |
| HOLD | 3,858 | 5,164 | 3,406 | 0 |
| BUY | 3,194 | 3,298 | 3,385 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,981 | 3,009 | 2,574 | 0 |
| HOLD | 2,952 | 6,257 | 3,219 | 0 |
| BUY | 2,686 | 3,924 | 3,267 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,740 | 2,955 | 2,869 | 0 |
| HOLD | 2,208 | 4,828 | 5,392 | 0 |
| BUY | 2,113 | 3,921 | 3,843 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 7,564 | 0 | 0 |
| HOLD | 0 | 12,428 | 0 | 0 |
| BUY | 0 | 9,877 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,980 | 2,806 | 2,778 | 0 |
| HOLD | 2,622 | 4,709 | 5,097 | 0 |
| BUY | 2,390 | 3,521 | 3,966 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,240 | 2,782 | 2,542 | 0 |
| HOLD | 3,384 | 5,734 | 3,310 | 0 |
| BUY | 2,904 | 3,615 | 3,358 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,965 | 3,099 | 2,500 | 0 |
| HOLD | 3,221 | 5,129 | 4,078 | 0 |
| BUY | 2,592 | 4,031 | 3,254 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 | Fold 10 | Fold 11 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.333 | 0.364 | 0.359 | 0.387 | 0.346 | 0.422 | 0.178 | 0.302 | 0.356 | 0.349 | 0.387 | 0.344 |
| logreg | 0.335 | 0.384 | 0.351 | 0.352 | 0.386 | 0.404 | 0.197 | 0.287 | 0.366 | 0.353 | 0.354 | 0.370 |
| ma_cross_rule | 0.348 | 0.332 | 0.331 | 0.352 | 0.313 | 0.351 | 0.336 | 0.328 | 0.321 | 0.279 | 0.316 | 0.317 |
| majority | 0.186 | 0.206 | 0.198 | 0.182 | 0.193 | 0.213 | 0.202 | 0.182 | 0.204 | 0.183 | 0.210 | 0.189 |
| momentum_rule | 0.356 | 0.335 | 0.343 | 0.368 | 0.317 | 0.374 | 0.324 | 0.353 | 0.300 | 0.305 | 0.339 | 0.337 |
| random_forest | 0.336 | 0.363 | 0.353 | 0.380 | 0.379 | 0.449 | 0.199 | 0.285 | 0.345 | 0.352 | 0.390 | 0.354 |
| stratified_random | 0.345 | 0.340 | 0.326 | 0.338 | 0.338 | 0.334 | 0.338 | 0.320 | 0.326 | 0.333 | 0.330 | 0.329 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.364 | 0.356 | 0.348 |
| logreg | 0.348 | 0.363 | 0.357 |
| ma_cross_rule | 0.332 | 0.340 | 0.321 |
| majority | 0.190 | 0.202 | 0.193 |
| momentum_rule | 0.318 | 0.347 | 0.339 |
| random_forest | 0.355 | 0.364 | 0.356 |
| stratified_random | 0.333 | 0.331 | 0.336 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.327 | 0.350 | 0.384 | 10 |
| logreg | 0.340 | 0.350 | 0.376 | 10 |
| ma_cross_rule | 0.306 | 0.325 | 0.360 | 10 |
| majority | 0.189 | 0.195 | 0.204 | 10 |
| momentum_rule | 0.317 | 0.347 | 0.358 | 10 |
| random_forest | 0.323 | 0.351 | 0.389 | 10 |
| stratified_random | 0.325 | 0.331 | 0.344 | 10 |

### 20-day horizon

29,719 test observations on 2,996 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.362 | 0.362 | 0.372 | 1.179 | 0.686 | 0.056 | 0.513 | 29/34/37 | 0.0% |
| random_forest | 0.355 | 0.357 | 0.361 | 1.110 | 0.674 | 0.045 | 0.515 | 32/31/37 | 0.0% |
| ma_cross_rule | 0.350 | 0.351 | 0.367 | n/a | n/a | n/a | 0.570 | 20/37/43 | 0.0% |
| momentum_rule | 0.347 | 0.349 | 0.367 | n/a | n/a | n/a | 0.567 | 19/36/45 | 0.0% |
| gbt | 0.343 | 0.344 | 0.352 | 1.165 | 0.706 | 0.126 | 0.492 | 30/34/36 | 0.0% |
| stratified_random | 0.336 | 0.336 | 0.348 | 1.079 | 0.654 | 0.005 | 0.524 | 25/39/36 | 0.0% |
| majority | 0.188 | 0.333 | 0.393 | 1.079 | 0.654 | 0.005 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 23.9%, HOLD 39.3%, BUY 36.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.228 | 0.436 | 0.376 | 0.284 | 0.374 | 0.373 | 1.704% | 1.160% | 0.593% |
| logreg | 0.239 | 0.458 | 0.398 | 0.289 | 0.397 | 0.400 | 1.203% | 1.166% | 1.002% |
| ma_cross_rule | 0.283 | 0.399 | 0.377 | 0.235 | 0.373 | 0.446 | 0.534% | 0.711% | 1.726% |
| majority | 0.000 | 0.393 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 1.116% | n/a |
| momentum_rule | 0.262 | 0.403 | 0.384 | 0.213 | 0.368 | 0.467 | 0.694% | 0.658% | 1.668% |
| random_forest | 0.238 | 0.445 | 0.399 | 0.320 | 0.349 | 0.402 | 1.386% | 1.310% | 0.719% |
| stratified_random | 0.244 | 0.394 | 0.371 | 0.259 | 0.389 | 0.362 | 1.037% | 1.138% | 1.148% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0071 | -0.0164 to 0.0289 | 0.539 | 0.819 |
| logreg vs stratified_random | 0.0259 | -0.0007 to 0.0489 | 0.041 | 0.207 |
| ma_cross_rule vs stratified_random | 0.0140 | -0.0092 to 0.0373 | 0.243 | 0.729 |
| momentum_rule vs stratified_random | 0.0108 | -0.0149 to 0.0369 | 0.409 | 0.819 |
| random_forest vs stratified_random | 0.0185 | -0.0075 to 0.0440 | 0.144 | 0.576 |

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

24,919 test observations on 2,516 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.369 | 0.370 | 0.394 | 1.091 | 0.660 | 0.008 | 0.500 | 28/46/25 | 0.0% |
| random_forest | 0.367 | 0.368 | 0.394 | 1.090 | 0.660 | 0.023 | 0.509 | 26/48/26 | 0.0% |
| gbt | 0.366 | 0.367 | 0.379 | 1.098 | 0.666 | 0.042 | 0.506 | 34/40/27 | 0.0% |
| momentum_rule | 0.341 | 0.345 | 0.353 | n/a | n/a | n/a | 0.520 | 21/36/42 | 0.0% |
| stratified_random | 0.333 | 0.333 | 0.350 | 1.074 | 0.650 | 0.003 | 0.503 | 26/44/30 | 0.0% |
| ma_cross_rule | 0.333 | 0.336 | 0.345 | n/a | n/a | n/a | 0.528 | 20/38/42 | 0.0% |
| majority | 0.203 | 0.333 | 0.437 | 1.074 | 0.650 | 0.003 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 26.2%, HOLD 43.7%, BUY 30.1%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.273 | 0.493 | 0.342 | 0.351 | 0.447 | 0.303 | 0.043% | 0.033% | 0.085% |
| logreg | 0.281 | 0.496 | 0.335 | 0.305 | 0.526 | 0.279 | 0.028% | 0.061% | 0.055% |
| ma_cross_rule | 0.300 | 0.427 | 0.291 | 0.234 | 0.372 | 0.402 | -0.001% | 0.047% | 0.078% |
| majority | 0.000 | 0.437 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.050% | n/a |
| momentum_rule | 0.295 | 0.452 | 0.298 | 0.242 | 0.375 | 0.418 | -0.001% | 0.048% | 0.079% |
| random_forest | 0.287 | 0.486 | 0.331 | 0.285 | 0.535 | 0.285 | 0.026% | 0.072% | 0.033% |
| stratified_random | 0.261 | 0.437 | 0.302 | 0.261 | 0.437 | 0.302 | 0.074% | 0.050% | 0.030% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0323 | 0.0221 to 0.0425 | 0.000 | 0.002 |
| logreg vs stratified_random | 0.0359 | 0.0253 to 0.0451 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | -0.0007 | -0.0121 to 0.0102 | 0.900 | 0.900 |
| momentum_rule vs stratified_random | 0.0079 | -0.0031 to 0.0181 | 0.162 | 0.325 |
| random_forest vs stratified_random | 0.0339 | 0.0244 to 0.0426 | 0.000 | 0.002 |

### 5-day horizon (primary)

24,919 test observations on 2,516 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.364 | 0.365 | 0.383 | 1.107 | 0.667 | 0.027 | 0.499 | 26/44/30 | 0.0% |
| random_forest | 0.364 | 0.364 | 0.375 | 1.096 | 0.665 | 0.022 | 0.504 | 30/40/31 | 0.0% |
| gbt | 0.358 | 0.359 | 0.366 | 1.131 | 0.686 | 0.095 | 0.502 | 33/37/30 | 0.0% |
| momentum_rule | 0.347 | 0.349 | 0.356 | n/a | n/a | n/a | 0.538 | 24/36/40 | 0.0% |
| ma_cross_rule | 0.338 | 0.339 | 0.351 | n/a | n/a | n/a | 0.532 | 21/40/40 | 0.0% |
| stratified_random | 0.335 | 0.335 | 0.347 | 1.081 | 0.655 | 0.004 | 0.507 | 26/41/33 | 0.0% |
| majority | 0.195 | 0.333 | 0.414 | 1.081 | 0.655 | 0.004 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 25.6%, HOLD 41.4%, BUY 33.1%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.258 | 0.462 | 0.365 | 0.335 | 0.412 | 0.331 | 0.214% | 0.298% | 0.251% |
| logreg | 0.263 | 0.470 | 0.360 | 0.271 | 0.496 | 0.327 | 0.285% | 0.334% | 0.118% |
| ma_cross_rule | 0.296 | 0.411 | 0.319 | 0.238 | 0.395 | 0.382 | 0.060% | 0.206% | 0.408% |
| majority | 0.000 | 0.414 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.256% | n/a |
| momentum_rule | 0.287 | 0.423 | 0.338 | 0.272 | 0.369 | 0.405 | 0.086% | 0.146% | 0.460% |
| random_forest | 0.263 | 0.469 | 0.363 | 0.306 | 0.451 | 0.335 | 0.185% | 0.348% | 0.205% |
| stratified_random | 0.256 | 0.416 | 0.332 | 0.262 | 0.413 | 0.329 | 0.284% | 0.258% | 0.232% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0234 | 0.0081 to 0.0387 | 0.003 | 0.009 |
| logreg vs stratified_random | 0.0294 | 0.0152 to 0.0436 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | 0.0037 | -0.0098 to 0.0170 | 0.595 | 0.595 |
| momentum_rule vs stratified_random | 0.0124 | -0.0021 to 0.0274 | 0.105 | 0.210 |
| random_forest vs stratified_random | 0.0290 | 0.0132 to 0.0446 | 0.000 | 0.002 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 2,131 | 2,179 | 2,057 | 0 |
| HOLD | 3,366 | 4,251 | 2,689 | 0 |
| BUY | 2,757 | 2,763 | 2,726 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,723 | 2,499 | 2,145 | 0 |
| HOLD | 2,542 | 5,116 | 2,648 | 0 |
| BUY | 2,290 | 3,260 | 2,696 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,517 | 2,510 | 2,340 | 0 |
| HOLD | 1,833 | 4,076 | 4,397 | 0 |
| BUY | 1,769 | 3,323 | 3,154 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 6,367 | 0 | 0 |
| HOLD | 0 | 10,306 | 0 | 0 |
| BUY | 0 | 8,246 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,730 | 2,328 | 2,309 | 0 |
| HOLD | 2,254 | 3,799 | 4,253 | 0 |
| BUY | 2,045 | 2,858 | 3,343 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,946 | 2,281 | 2,140 | 0 |
| HOLD | 2,947 | 4,648 | 2,711 | 0 |
| BUY | 2,494 | 2,989 | 2,763 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 1,666 | 2,606 | 2,095 | 0 |
| HOLD | 2,678 | 4,257 | 3,371 | 0 |
| BUY | 2,170 | 3,359 | 2,717 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.333 | 0.364 | 0.359 | 0.387 | 0.346 | 0.422 | 0.178 | 0.302 | 0.356 | 0.349 |
| logreg | 0.335 | 0.384 | 0.351 | 0.352 | 0.386 | 0.404 | 0.197 | 0.287 | 0.366 | 0.353 |
| ma_cross_rule | 0.348 | 0.332 | 0.331 | 0.352 | 0.313 | 0.351 | 0.336 | 0.328 | 0.321 | 0.279 |
| majority | 0.186 | 0.206 | 0.198 | 0.182 | 0.193 | 0.213 | 0.202 | 0.182 | 0.204 | 0.183 |
| momentum_rule | 0.356 | 0.335 | 0.343 | 0.368 | 0.317 | 0.374 | 0.324 | 0.353 | 0.300 | 0.305 |
| random_forest | 0.336 | 0.363 | 0.353 | 0.380 | 0.379 | 0.449 | 0.199 | 0.285 | 0.345 | 0.352 |
| stratified_random | 0.345 | 0.340 | 0.326 | 0.338 | 0.338 | 0.334 | 0.338 | 0.320 | 0.326 | 0.333 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.357 | 0.354 | 0.345 |
| logreg | 0.348 | 0.361 | 0.358 |
| ma_cross_rule | 0.339 | 0.345 | 0.321 |
| majority | 0.192 | 0.199 | 0.193 |
| momentum_rule | 0.323 | 0.348 | 0.337 |
| random_forest | 0.345 | 0.362 | 0.354 |
| stratified_random | 0.336 | 0.329 | 0.338 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.328 | 0.347 | 0.378 | 10 |
| logreg | 0.340 | 0.350 | 0.377 | 10 |
| ma_cross_rule | 0.316 | 0.328 | 0.358 | 10 |
| majority | 0.189 | 0.193 | 0.202 | 10 |
| momentum_rule | 0.317 | 0.343 | 0.357 | 10 |
| random_forest | 0.321 | 0.349 | 0.383 | 10 |
| stratified_random | 0.326 | 0.333 | 0.351 | 10 |

### 20-day horizon

24,919 test observations on 2,516 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.364 | 0.364 | 0.372 | 1.197 | 0.692 | 0.066 | 0.517 | 30/33/37 | 0.0% |
| ma_cross_rule | 0.359 | 0.360 | 0.373 | n/a | n/a | n/a | 0.570 | 21/37/42 | 0.0% |
| random_forest | 0.351 | 0.354 | 0.357 | 1.115 | 0.677 | 0.052 | 0.512 | 33/29/37 | 0.0% |
| momentum_rule | 0.349 | 0.351 | 0.365 | n/a | n/a | n/a | 0.569 | 21/36/43 | 0.0% |
| gbt | 0.337 | 0.338 | 0.343 | 1.180 | 0.714 | 0.139 | 0.488 | 32/31/37 | 0.0% |
| stratified_random | 0.334 | 0.334 | 0.344 | 1.083 | 0.656 | 0.001 | 0.520 | 25/39/36 | 0.0% |
| majority | 0.186 | 0.333 | 0.387 | 1.083 | 0.656 | 0.001 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 24.7%, HOLD 38.7%, BUY 36.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.232 | 0.422 | 0.373 | 0.302 | 0.340 | 0.373 | 1.732% | 1.098% | 0.488% |
| logreg | 0.250 | 0.450 | 0.400 | 0.304 | 0.384 | 0.404 | 1.158% | 1.058% | 1.032% |
| ma_cross_rule | 0.299 | 0.403 | 0.384 | 0.251 | 0.389 | 0.439 | 0.364% | 0.630% | 1.829% |
| majority | 0.000 | 0.387 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 1.078% | n/a |
| momentum_rule | 0.275 | 0.390 | 0.387 | 0.236 | 0.359 | 0.457 | 0.569% | 0.573% | 1.744% |
| random_forest | 0.241 | 0.435 | 0.398 | 0.323 | 0.331 | 0.407 | 1.488% | 1.208% | 0.614% |
| stratified_random | 0.247 | 0.385 | 0.369 | 0.255 | 0.385 | 0.360 | 1.024% | 1.086% | 1.109% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0038 | -0.0244 to 0.0282 | 0.771 | 0.771 |
| logreg vs stratified_random | 0.0300 | 0.0002 to 0.0557 | 0.035 | 0.177 |
| ma_cross_rule vs stratified_random | 0.0259 | 0.0000 to 0.0520 | 0.054 | 0.216 |
| momentum_rule vs stratified_random | 0.0154 | -0.0128 to 0.0435 | 0.297 | 0.717 |
| random_forest vs stratified_random | 0.0179 | -0.0137 to 0.0460 | 0.239 | 0.717 |

## 6. Classification diagnostics (final two years)

### 1-day horizon

4,990 test observations on 499 dates. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.394 | 0.394 | 0.431 | 1.080 | 0.653 | 0.056 | 0.551 | 21/49/30 | 0.0% |
| gbt | 0.386 | 0.388 | 0.406 | 1.076 | 0.651 | 0.010 | 0.545 | 25/40/35 | 0.0% |
| random_forest | 0.375 | 0.379 | 0.418 | 1.079 | 0.653 | 0.042 | 0.538 | 17/50/34 | 0.0% |
| momentum_rule | 0.347 | 0.349 | 0.371 | n/a | n/a | n/a | 0.527 | 17/41/41 | 0.0% |
| stratified_random | 0.324 | 0.324 | 0.346 | 1.062 | 0.642 | 0.021 | 0.499 | 25/44/30 | 0.0% |
| ma_cross_rule | 0.316 | 0.323 | 0.333 | n/a | n/a | n/a | 0.517 | 19/36/45 | 0.0% |
| majority | 0.210 | 0.333 | 0.461 | 1.062 | 0.642 | 0.021 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 24.1%, HOLD 46.1%, BUY 29.8%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.280 | 0.534 | 0.348 | 0.285 | 0.464 | 0.414 | -0.020% | 0.097% | 0.080% |
| logreg | 0.287 | 0.530 | 0.367 | 0.247 | 0.568 | 0.368 | -0.005% | 0.068% | 0.100% |
| ma_cross_rule | 0.254 | 0.441 | 0.281 | 0.202 | 0.346 | 0.421 | 0.098% | 0.019% | 0.082% |
| majority | 0.000 | 0.461 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.063% | n/a |
| momentum_rule | 0.290 | 0.483 | 0.293 | 0.208 | 0.431 | 0.408 | 0.019% | 0.082% | 0.062% |
| random_forest | 0.271 | 0.518 | 0.345 | 0.189 | 0.557 | 0.390 | 0.016% | 0.073% | 0.071% |
| stratified_random | 0.245 | 0.449 | 0.280 | 0.255 | 0.432 | 0.287 | -0.003% | 0.120% | 0.034% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0613 | 0.0383 to 0.0826 | 0.000 | 0.002 |
| logreg vs stratified_random | 0.0695 | 0.0467 to 0.0889 | 0.000 | 0.002 |
| ma_cross_rule vs stratified_random | -0.0079 | -0.0282 to 0.0104 | 0.446 | 0.446 |
| momentum_rule vs stratified_random | 0.0222 | -0.0020 to 0.0422 | 0.052 | 0.105 |
| random_forest vs stratified_random | 0.0510 | 0.0281 to 0.0736 | 0.000 | 0.002 |

### 5-day horizon (primary)

4,950 test observations on 495 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.374 | 0.374 | 0.399 | 1.081 | 0.655 | 0.012 | 0.523 | 23/45/32 | 0.0% |
| gbt | 0.368 | 0.369 | 0.383 | 1.088 | 0.659 | 0.055 | 0.524 | 25/38/37 | 0.0% |
| logreg | 0.366 | 0.368 | 0.398 | 1.082 | 0.654 | 0.022 | 0.501 | 21/47/32 | 0.0% |
| momentum_rule | 0.339 | 0.340 | 0.360 | n/a | n/a | n/a | 0.517 | 19/41/39 | 0.0% |
| stratified_random | 0.330 | 0.330 | 0.345 | 1.073 | 0.650 | 0.016 | 0.503 | 26/41/33 | 0.0% |
| ma_cross_rule | 0.317 | 0.321 | 0.336 | n/a | n/a | n/a | 0.511 | 19/36/45 | 0.0% |
| majority | 0.200 | 0.333 | 0.429 | 1.073 | 0.650 | 0.016 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 24.2%, HOLD 42.9%, BUY 32.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.260 | 0.490 | 0.360 | 0.272 | 0.430 | 0.404 | 0.258% | 0.308% | 0.365% |
| logreg | 0.242 | 0.493 | 0.363 | 0.216 | 0.538 | 0.350 | 0.341% | 0.342% | 0.262% |
| ma_cross_rule | 0.237 | 0.419 | 0.311 | 0.186 | 0.354 | 0.422 | 0.466% | 0.136% | 0.400% |
| majority | 0.000 | 0.429 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 0.317% | n/a |
| momentum_rule | 0.260 | 0.444 | 0.322 | 0.209 | 0.429 | 0.382 | 0.254% | 0.335% | 0.328% |
| random_forest | 0.258 | 0.491 | 0.373 | 0.246 | 0.512 | 0.365 | 0.227% | 0.299% | 0.405% |
| stratified_random | 0.237 | 0.428 | 0.326 | 0.250 | 0.411 | 0.329 | 0.270% | 0.317% | 0.351% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0383 | 0.0059 to 0.0701 | 0.019 | 0.068 |
| logreg vs stratified_random | 0.0365 | 0.0068 to 0.0654 | 0.017 | 0.068 |
| ma_cross_rule vs stratified_random | -0.0129 | -0.0363 to 0.0108 | 0.254 | 0.508 |
| momentum_rule vs stratified_random | 0.0091 | -0.0195 to 0.0367 | 0.494 | 0.508 |
| random_forest vs stratified_random | 0.0438 | 0.0138 to 0.0730 | 0.004 | 0.022 |

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

`gbt`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 326 | 415 | 456 | 0 |
| HOLD | 492 | 913 | 717 | 0 |
| BUY | 437 | 535 | 659 | 0 |

`logreg`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 258 | 510 | 429 | 0 |
| HOLD | 410 | 1,141 | 571 | 0 |
| BUY | 396 | 664 | 571 | 0 |

`ma_cross_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 223 | 445 | 529 | 0 |
| HOLD | 375 | 752 | 995 | 0 |
| BUY | 344 | 598 | 689 | 0 |

`majority`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 0 | 1,197 | 0 | 0 |
| HOLD | 0 | 2,122 | 0 | 0 |
| BUY | 0 | 1,631 | 0 | 0 |

`momentum_rule`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 250 | 478 | 469 | 0 |
| HOLD | 368 | 910 | 844 | 0 |
| BUY | 345 | 663 | 623 | 0 |

`random_forest`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 294 | 501 | 402 | 0 |
| HOLD | 437 | 1,086 | 599 | 0 |
| BUY | 410 | 626 | 595 | 0 |

`stratified_random`

| True | SELL | HOLD | BUY | none |
|---|---:|---:|---:|---:|
| SELL | 299 | 493 | 405 | 0 |
| HOLD | 543 | 872 | 707 | 0 |
| BUY | 422 | 672 | 537 | 0 |

Macro-F1 by walk-forward fold:

| Model | Fold 10 | Fold 11 |
|---|---:|---:|
| gbt | 0.387 | 0.344 |
| logreg | 0.354 | 0.370 |
| ma_cross_rule | 0.316 | 0.317 |
| majority | 0.210 | 0.189 |
| momentum_rule | 0.339 | 0.337 |
| random_forest | 0.390 | 0.354 |
| stratified_random | 0.330 | 0.329 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| gbt | 0.383 | 0.361 | 0.359 |
| logreg | 0.334 | 0.366 | 0.349 |
| ma_cross_rule | 0.273 | 0.319 | 0.320 |
| majority | 0.173 | 0.212 | 0.195 |
| momentum_rule | 0.264 | 0.342 | 0.348 |
| random_forest | 0.396 | 0.367 | 0.360 |
| stratified_random | 0.306 | 0.341 | 0.323 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| gbt | 0.306 | 0.354 | 0.416 | 10 |
| logreg | 0.316 | 0.356 | 0.379 | 10 |
| ma_cross_rule | 0.269 | 0.315 | 0.350 | 10 |
| majority | 0.187 | 0.202 | 0.210 | 10 |
| momentum_rule | 0.304 | 0.326 | 0.360 | 10 |
| random_forest | 0.298 | 0.350 | 0.414 | 10 |
| stratified_random | 0.310 | 0.324 | 0.343 | 10 |

### 20-day horizon

4,800 test observations on 480 dates. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random_forest | 0.366 | 0.368 | 0.384 | 1.084 | 0.657 | 0.009 | 0.529 | 28/38/34 | 0.0% |
| gbt | 0.356 | 0.357 | 0.399 | 1.093 | 0.664 | 0.070 | 0.515 | 18/47/35 | 0.0% |
| stratified_random | 0.349 | 0.351 | 0.366 | 1.061 | 0.643 | 0.040 | 0.548 | 25/39/36 | 0.0% |
| logreg | 0.346 | 0.344 | 0.376 | 1.085 | 0.657 | 0.026 | 0.489 | 24/40/36 | 0.0% |
| momentum_rule | 0.318 | 0.331 | 0.380 | n/a | n/a | n/a | 0.551 | 10/38/52 | 0.0% |
| ma_cross_rule | 0.295 | 0.302 | 0.331 | n/a | n/a | n/a | 0.571 | 15/34/50 | 0.0% |
| majority | 0.200 | 0.333 | 0.428 | 1.061 | 0.643 | 0.040 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 20.1%, HOLD 42.8%, BUY 37.1%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.188 | 0.487 | 0.391 | 0.170 | 0.534 | 0.368 | 1.441% | 1.374% | 1.164% |
| logreg | 0.164 | 0.490 | 0.390 | 0.194 | 0.460 | 0.379 | 1.495% | 1.628% | 0.842% |
| ma_cross_rule | 0.172 | 0.372 | 0.351 | 0.129 | 0.298 | 0.478 | 1.737% | 1.168% | 1.284% |
| majority | 0.000 | 0.428 | 0.000 | 0.000 | 1.000 | 0.000 | n/a | 1.313% | n/a |
| momentum_rule | 0.128 | 0.467 | 0.368 | 0.065 | 0.410 | 0.517 | 2.040% | 1.073% | 1.342% |
| random_forest | 0.216 | 0.486 | 0.407 | 0.300 | 0.430 | 0.375 | 0.759% | 1.722% | 1.313% |
| stratified_random | 0.228 | 0.440 | 0.380 | 0.281 | 0.404 | 0.368 | 1.110% | 1.406% | 1.351% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0068 | -0.0384 to 0.0483 | 0.748 | 1.000 |
| logreg vs stratified_random | -0.0033 | -0.0483 to 0.0337 | 0.872 | 1.000 |
| ma_cross_rule vs stratified_random | -0.0543 | -0.0890 to -0.0192 | 0.003 | 0.017 |
| momentum_rule vs stratified_random | -0.0312 | -0.0729 to 0.0157 | 0.164 | 0.656 |
| random_forest vs stratified_random | 0.0172 | -0.0317 to 0.0595 | 0.462 | 1.000 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 36 | 8 | 281.2 | 0.5 | 89,497 |
| logreg | 36 | 8 | 43.5 | 0.1 | 89,497 |
| ma_cross_rule | 36 | 6 | 0.5 | 0.0 | 89,497 |
| majority | 36 | 1 | 0.1 | 0.0 | 89,497 |
| momentum_rule | 36 | 8 | 0.7 | 0.0 | 89,497 |
| random_forest | 36 | 8 | 230.9 | 1.9 | 89,497 |
| stratified_random | 36 | 1 | 0.1 | 0.0 | 89,497 |

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

- **Trading performance (primary):** insufficient evidence. No external classifier has been run (not run: no saved outputs).
- **Classification performance:** insufficient evidence, for the same reason.
- **Operational efficiency:** insufficient evidence. No external classifier's runtime or cost has been measured.
- **Overall:** the evidence does not yet bear on whether Jev outperforms traditional models for trading.
