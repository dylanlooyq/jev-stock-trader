# Experiment report: pipeline_check_rolling_3m

Generated 2026-10-12T03:41:00+00:00 from commit `115d3d1-dirty`, config `b71764480c07`, dataset `0b91d318b8c2`. Final two years of folds included: **False**.

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
| momentum_rule | 73.7% | 5.7% | 0.38 | 0.52 | -22.2% | 0.26 | 55.1 | 100.0% | -0.4% (-6.2% to 4.6%) | 0.41 | 0.51 | 0.15 | -0.10 |
| majority | -64.2% | -9.8% | -0.70 | -0.91 | -72.7% | -0.13 | 368.8 | 100.0% | -19.2% (-27.5% to -13.6%) | 0.69 | 0.02 | -1.89 | -2.51 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| momentum_rule vs always_buy | -0.14 | -0.69 to 0.32 | 0.604 | 0.604 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| momentum_rule | 62.9% | 5.0% | 0.33 | 0.45 | -15.0% | 0.33 | 22.0 | 99.8% | -1.3% (-7.7% to 2.7%) | 0.43 | 0.38 | 0.24 | -0.20 |
| majority | 42.0% | 3.6% | 0.21 | 0.28 | -27.7% | 0.13 | 73.5 | 99.8% | -5.6% (-10.8% to -1.2%) | 0.68 | 0.37 | -0.07 | -1.37 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| momentum_rule vs always_buy | -0.19 | -0.67 to 0.29 | 0.505 | 0.505 |

### Folds before the final two years, `rank_check` rule

Concentrated ranking portfolio (declared check): each day hold the top 1 of 15 assets by score, fully invested.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a |
| momentum_rule | -24.3% | -2.7% | -0.15 | -0.21 | -49.1% | -0.06 | 98.5 | 100.0% | -5.5% (-15.1% to 4.6%) | 0.22 | 0.01 | -0.43 | -0.21 |
| majority | -81.7% | -15.6% | -0.72 | -0.99 | -84.6% | -0.19 | 471.4 | 100.0% | -24.8% (-36.6% to -11.7%) | 0.70 | -0.09 | -1.78 | -1.98 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| momentum_rule vs always_buy | -0.68 | -1.45 to 0.05 | 0.099 | 0.099 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a |
| majority | 11.8% | 1.1% | 0.04 | 0.06 | -37.2% | 0.03 | 94.4 | 99.8% | -7.8% (-15.6% to -1.0%) | 0.69 | 0.23 | -0.26 | -1.02 |
| momentum_rule | -16.4% | -1.8% | -0.12 | -0.16 | -45.8% | -0.04 | 40.1 | 99.8% | -4.6% (-13.7% to 4.5%) | 0.22 | -0.04 | -0.23 | -0.15 |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| momentum_rule vs always_buy | -0.64 | -1.24 to -0.02 | 0.050 | 0.050 |

### Folds before the final two years, `buy_names` rule

BUY-names portfolio: hold the assets labelled BUY, the rest in cash.

**1-day horizon**, 2014-10-01 to 2024-09-26

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 108.3% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.1 | 100.0% | -1.7% | 0.67 | n/a | n/a | n/a | n/a | n/a |
| majority | 34.8% | 3.0% | 0.36 | 0.61 | -6.6% | 0.46 | 0.2 | 2.5% | 0.7% (-1.2% to 2.7%) | 0.06 | 0.36 | 0.36 | 0.04 | 0.36 | -0.0% |
| momentum_rule | 34.1% | 3.0% | 0.31 | 0.43 | -7.9% | 0.38 | 14.6 | 40.8% | -0.2% (-2.9% to 2.2%) | 0.13 | 0.41 | 0.15 | -0.13 | 0.45 | -0.5% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| momentum_rule vs always_buy | -0.21 | -0.83 to 0.28 | 0.525 | 0.525 |

**5-day horizon (primary)**, 2014-10-01 to 2024-09-20

| Strategy | Net return | Per year | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Invested | Alpha/yr (95% interval) | Beta | Sharpe @2bps | Sharpe @10bps | Sharpe L/S | Sharpe, same exposure spread evenly | Selection return/yr |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 245.9% | 13.2% | 0.72 | 0.99 | -32.0% | 0.41 | 0.0 | 100.0% | 0.0% | 1.00 | n/a | n/a | n/a | n/a | n/a |
| always_buy | 107.6% | 7.6% | 0.52 | 0.71 | -28.4% | 0.27 | 0.2 | 99.8% | -1.7% | 0.66 | n/a | n/a | n/a | n/a | n/a |
| momentum_rule | 42.9% | 3.6% | 0.42 | 0.57 | -8.0% | 0.46 | 6.2 | 42.1% | 0.1% (-2.1% to 2.1%) | 0.16 | 0.45 | 0.35 | -0.06 | 0.47 | -0.2% |
| majority | 12.0% | 1.1% | -0.11 | -0.14 | -10.8% | 0.11 | 0.6 | 9.9% | -1.3% (-3.7% to 0.5%) | 0.07 | -0.11 | -0.12 | -0.50 | -0.10 | -0.0% |

Net Sharpe difference against equal-weight buy and hold:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| momentum_rule vs always_buy | -0.10 | -0.54 to 0.37 | 0.653 | 0.653 |

## 5. What this run can detect

At the 5-day horizon on folds before the final two years, the 95% interval on a net Sharpe difference is typically ±0.48 (median of 1 comparisons). A true difference smaller than about 0.68 would be missed more often than one time in five, so a result of "no reliable difference" does not show that two strategies are equal. The smallest difference treated as worth acting on is 0.2.

## 6. Classification diagnostics (folds before the final two years)

### 1-day horizon

37,710 test observations on 2,514 dates. Reference traditional classifier (chosen on validation data): **None**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 0.336 | 0.339 | 0.351 | n/a | n/a | n/a | 0.514 | 20/39/41 | 0.0% |
| majority | 0.216 | 0.322 | 0.419 | 1.082 | 0.655 | 0.020 | 0.443 | 2/95/3 | 0.0% |

True class distribution: SELL 26.1%, HOLD 44.0%, BUY 29.9%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| majority | 0.160 | 0.432 | 0.200 | 0.015 | 0.933 | 0.017 | 0.211% | 0.023% | 0.228% |
| momentum_rule | 0.284 | 0.447 | 0.293 | 0.222 | 0.394 | 0.401 | 0.030% | 0.038% | 0.027% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|

### 5-day horizon (primary)

37,650 test observations on 2,510 dates. Reference traditional classifier (chosen on validation data): **None**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| momentum_rule | 0.338 | 0.340 | 0.351 | n/a | n/a | n/a | 0.526 | 22/36/42 | 0.0% |
| majority | 0.253 | 0.317 | 0.381 | 1.096 | 0.665 | 0.045 | 0.461 | 7/83/10 | 0.0% |

True class distribution: SELL 25.4%, HOLD 41.9%, BUY 32.7%. Random guessing scores about 0.33 macro-F1 and the majority class about 0.19. Log loss, Brier and ECE are shown only for models with real probabilities. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall, and mean realised forward return by predicted signal:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY | Ret. SELL | Ret. HOLD | Ret. BUY |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| majority | 0.156 | 0.409 | 0.315 | 0.045 | 0.809 | 0.095 | 0.647% | 0.140% | -0.032% |
| momentum_rule | 0.271 | 0.426 | 0.327 | 0.231 | 0.369 | 0.421 | 0.261% | 0.120% | 0.144% |

Macro-F1 difference against random guessing (paired block bootstrap over dates):

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|

Confusion matrices (rows: true class; columns: predicted SELL, HOLD, BUY, none):

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

Macro-F1 by walk-forward fold:

| Model | Fold 0 | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Fold 6 | Fold 7 | Fold 8 | Fold 9 | Fold 10 | Fold 11 | Fold 12 | Fold 13 | Fold 14 | Fold 15 | Fold 16 | Fold 17 | Fold 18 | Fold 19 | Fold 20 | Fold 21 | Fold 22 | Fold 23 | Fold 24 | Fold 25 | Fold 26 | Fold 27 | Fold 28 | Fold 29 | Fold 30 | Fold 31 | Fold 32 | Fold 33 | Fold 34 | Fold 35 | Fold 36 | Fold 37 | Fold 38 | Fold 39 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| majority | 0.165 | 0.137 | 0.221 | 0.180 | 0.212 | 0.189 | 0.195 | 0.228 | 0.202 | 0.213 | 0.193 | 0.196 | 0.177 | 0.160 | 0.162 | 0.184 | 0.158 | 0.062 | 0.178 | 0.203 | 0.224 | 0.126 | 0.066 | 0.222 | 0.206 | 0.201 | 0.218 | 0.201 | 0.191 | 0.167 | 0.133 | 0.183 | 0.204 | 0.193 | 0.222 | 0.171 | 0.176 | 0.182 | 0.191 | 0.160 |
| momentum_rule | 0.381 | 0.348 | 0.318 | 0.361 | 0.374 | 0.361 | 0.363 | 0.309 | 0.321 | 0.296 | 0.300 | 0.339 | 0.358 | 0.328 | 0.293 | 0.345 | 0.322 | 0.289 | 0.236 | 0.304 | 0.262 | 0.358 | 0.118 | 0.357 | 0.325 | 0.375 | 0.296 | 0.304 | 0.277 | 0.354 | 0.337 | 0.383 | 0.335 | 0.310 | 0.261 | 0.293 | 0.302 | 0.292 | 0.226 | 0.302 |

Macro-F1 by market regime:

| Model | downtrend/high_vol | uptrend/high_vol | uptrend/low_vol |
|---|---:|---:|---:|
| majority | 0.220 | 0.267 | 0.255 |
| momentum_rule | 0.334 | 0.348 | 0.321 |

Macro-F1 across individual assets:

| Model | 10th pct | Median | 90th pct | Assets |
|---|---:|---:|---:|---:|
| majority | 0.238 | 0.254 | 0.267 | 15 |
| momentum_rule | 0.316 | 0.331 | 0.350 | 15 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| majority | 80 | 1 | 0.3 | 0.0 | 75,360 |
| momentum_rule | 80 | 8 | 1.6 | 0.0 | 75,360 |

Traditional models run locally at no marginal cost. External classifier status: jev/zero: available: 100.0% of rows annotated; jev/examples: not run: no saved outputs; openai/zero: not run: no saved outputs; openai/examples: not run: no saved outputs; local/zero: not run: no saved outputs; local/examples: not run: no saved outputs.

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

- **Trading performance (primary):** insufficient evidence. No external classifier has been run (available: 100.0% of rows annotated; not run: no saved outputs).
- **Classification performance:** insufficient evidence, for the same reason.
- **Operational efficiency:** insufficient evidence. No external classifier's runtime or cost has been measured.
- **Overall:** the evidence does not yet bear on whether Jev outperforms traditional models for trading.
