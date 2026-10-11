# Experiment report: smoke_2026-10-11

> **Smoke run.** A small configuration used to validate the pipeline end to end. These numbers are not experimental findings.

Generated 2026-10-11T06:51:59+00:00 from commit `uncommitted`, config `fe756ad9dbb8`, dataset `72519f1d13e4`. Holdout unlocked: **False**.

## 1. Research question and method

Does Jev classify next-period stock moves as BUY / HOLD / SELL better than traditional classifiers given the same information, and does any advantage survive as trading performance net of costs? Every model is fitted and scored on identical observations in a purged walk-forward design. The full protocol and decision rule are in `EXPERIMENT_MEMORY.md`.

## 2. Data and labels

- Universe: `smoke_12`, 13 tickers obtained including the market proxy SPY; failed downloads: none.
- Source: yfinance daily bars, 2010-01-04 to 2026-09-30, downloaded 2026-10-11T06:47:08+00:00.
- The universe is a fixed list chosen with hindsight, not point-in-time membership. Survivorship bias is present and affects every model equally in direction but not necessarily in size.
- Prediction after the close of day t; execution at the open of t+1; label return is open(t+1) to open(t+1+h), dividend and split adjusted.
- Labels: BUY / SELL when the forward return is beyond ±0.5 × trailing 60-day volatility × √h, otherwise HOLD.
- Horizons: [1, 5, 20] trading days; primary: 5.

## 3. Leakage prevention

- Walk-forward folds of 12 months, expanding training window, 12-month validation tail used for all tuning.
- Rows whose label window reaches the next segment are purged, plus an embargo of h trading days.
- Scaling and all other preprocessing are fitted inside each model on fitting rows only.
- Data on or after 2024-10-01 is removed before features are computed unless the holdout is explicitly unlocked.
- Automated tests cover: features unchanged when future data is removed, labels unaffected by prices outside their window, purging at every boundary, the holdout lock, scaler isolation, trade timing, and causal construction of Jev's state and examples.

## 4. Classification results (dev folds)

### 1-day horizon

9,012 test observations on 751 dates, 2021-10-01 to 2024-09-26. Reference traditional classifier (chosen on validation data): **gbt**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.371 | 0.371 | 0.387 | 1.106 | 0.670 | 0.042 | 0.521 | 25/43/32 | 0.0% |
| logreg | 0.369 | 0.372 | 0.400 | 1.091 | 0.660 | 0.013 | 0.522 | 24/52/23 | 0.0% |
| random_forest | 0.363 | 0.365 | 0.388 | 1.093 | 0.662 | 0.009 | 0.516 | 20/47/33 | 0.0% |
| momentum_rule | 0.340 | 0.343 | 0.351 | n/a | n/a | n/a | 0.518 | 23/37/40 | 0.0% |
| ma_cross_rule | 0.334 | 0.335 | 0.346 | n/a | n/a | n/a | 0.525 | 23/42/35 | 0.0% |
| stratified_random | 0.332 | 0.332 | 0.346 | 1.081 | 0.655 | 0.016 | 0.505 | 26/43/31 | 0.0% |
| majority | 0.198 | 0.333 | 0.423 | 1.081 | 0.655 | 0.016 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 27.2%, HOLD 42.3%, BUY 30.5%. Log loss, Brier and ECE are shown only for models with real probabilities; trading rules have none. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY |
|---|---:|---:|---:|---:|---:|---:|
| gbt | 0.299 | 0.475 | 0.339 | 0.277 | 0.479 | 0.357 |
| logreg | 0.298 | 0.466 | 0.356 | 0.264 | 0.579 | 0.274 |
| ma_cross_rule | 0.290 | 0.412 | 0.305 | 0.243 | 0.407 | 0.354 |
| majority | 0.000 | 0.423 | 0.000 | 0.000 | 1.000 | 0.000 |
| momentum_rule | 0.292 | 0.432 | 0.308 | 0.248 | 0.381 | 0.400 |
| random_forest | 0.292 | 0.467 | 0.334 | 0.217 | 0.519 | 0.361 |
| stratified_random | 0.275 | 0.419 | 0.302 | 0.260 | 0.428 | 0.308 |

### 5-day horizon (primary)

8,964 test observations on 747 dates, 2021-10-01 to 2024-09-20. Reference traditional classifier (chosen on validation data): **random_forest**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gbt | 0.354 | 0.355 | 0.368 | 1.116 | 0.678 | 0.056 | 0.511 | 24/43/33 | 0.0% |
| logreg | 0.352 | 0.355 | 0.369 | 1.110 | 0.673 | 0.037 | 0.521 | 22/46/33 | 0.0% |
| random_forest | 0.348 | 0.354 | 0.372 | 1.107 | 0.671 | 0.028 | 0.524 | 19/50/31 | 0.0% |
| momentum_rule | 0.336 | 0.338 | 0.346 | n/a | n/a | n/a | 0.513 | 23/36/41 | 0.0% |
| stratified_random | 0.333 | 0.334 | 0.343 | 1.094 | 0.663 | 0.036 | 0.508 | 24/42/34 | 0.0% |
| ma_cross_rule | 0.331 | 0.332 | 0.340 | n/a | n/a | n/a | 0.506 | 24/39/36 | 0.0% |
| majority | 0.186 | 0.333 | 0.387 | 1.094 | 0.663 | 0.036 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 27.8%, HOLD 38.7%, BUY 33.4%. Log loss, Brier and ECE are shown only for models with real probabilities; trading rules have none. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY |
|---|---:|---:|---:|---:|---:|---:|
| gbt | 0.276 | 0.423 | 0.363 | 0.237 | 0.467 | 0.361 |
| logreg | 0.285 | 0.415 | 0.362 | 0.223 | 0.488 | 0.353 |
| ma_cross_rule | 0.275 | 0.387 | 0.333 | 0.242 | 0.394 | 0.359 |
| majority | 0.000 | 0.387 | 0.000 | 0.000 | 1.000 | 0.000 |
| momentum_rule | 0.281 | 0.397 | 0.336 | 0.229 | 0.370 | 0.414 |
| random_forest | 0.294 | 0.411 | 0.357 | 0.195 | 0.532 | 0.335 |
| stratified_random | 0.278 | 0.388 | 0.335 | 0.241 | 0.419 | 0.341 |

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

8,784 test observations on 732 dates, 2021-10-01 to 2024-08-29. Reference traditional classifier (chosen on validation data): **logreg**.

| Model | Macro-F1 | Bal. acc. | Accuracy | Log loss | Brier | ECE | Dir. hit rate | Pred. S/H/B % | No pred. |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 0.348 | 0.352 | 0.361 | 1.141 | 0.687 | 0.066 | 0.544 | 23/34/42 | 0.0% |
| momentum_rule | 0.338 | 0.339 | 0.347 | n/a | n/a | n/a | 0.523 | 23/39/38 | 0.0% |
| stratified_random | 0.336 | 0.338 | 0.347 | 1.104 | 0.669 | 0.032 | 0.520 | 22/40/38 | 0.0% |
| random_forest | 0.334 | 0.337 | 0.348 | 1.145 | 0.691 | 0.083 | 0.483 | 25/41/34 | 0.0% |
| gbt | 0.326 | 0.328 | 0.338 | 1.179 | 0.710 | 0.139 | 0.483 | 24/37/38 | 0.0% |
| ma_cross_rule | 0.314 | 0.316 | 0.326 | n/a | n/a | n/a | 0.482 | 24/41/35 | 0.0% |
| majority | 0.178 | 0.333 | 0.364 | 1.104 | 0.669 | 0.032 | n/a | 0/100/0 | 0.0% |

True class distribution: SELL 28.0%, HOLD 36.4%, BUY 35.6%. Log loss, Brier and ECE are shown only for models with real probabilities; trading rules have none. Directional hit rate counts only rows where both the prediction and the outcome are BUY or SELL.

Per-class precision and recall:

| Model | P SELL | P HOLD | P BUY | R SELL | R HOLD | R BUY |
|---|---:|---:|---:|---:|---:|---:|
| gbt | 0.231 | 0.382 | 0.364 | 0.198 | 0.393 | 0.393 |
| logreg | 0.272 | 0.381 | 0.394 | 0.225 | 0.360 | 0.470 |
| ma_cross_rule | 0.231 | 0.357 | 0.354 | 0.195 | 0.406 | 0.347 |
| majority | 0.000 | 0.364 | 0.000 | 0.000 | 1.000 | 0.000 |
| momentum_rule | 0.280 | 0.368 | 0.367 | 0.233 | 0.394 | 0.389 |
| random_forest | 0.233 | 0.391 | 0.378 | 0.206 | 0.446 | 0.359 |
| stratified_random | 0.283 | 0.369 | 0.361 | 0.221 | 0.403 | 0.389 |

## 5. Statistical uncertainty (dev folds)

Paired stationary block bootstrap over dates, 300 resamples. Differences are in pooled macro-F1 (first model minus second). Holm adjustment is applied within each table. A p-value here describes this sample; it does not account for choices made across separate runs.

### 1-day horizon (mean block 10 days)

Any skill: each model against stratified random guessing:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0388 | 0.0230 to 0.0553 | 0.003 | 0.017 |
| logreg vs stratified_random | 0.0366 | 0.0226 to 0.0493 | 0.003 | 0.017 |
| ma_cross_rule vs stratified_random | 0.0020 | -0.0135 to 0.0165 | 0.797 | 0.797 |
| momentum_rule vs stratified_random | 0.0083 | -0.0074 to 0.0240 | 0.289 | 0.578 |
| random_forest vs stratified_random | 0.0305 | 0.0173 to 0.0440 | 0.003 | 0.017 |

Jev arms against the reference traditional classifier:

_No comparison available: the Jev arms have not been run._

Does adding Jev outputs improve GBT?:

_No comparison available: the Jev arms have not been run._

### 5-day horizon (mean block 10 days)

Any skill: each model against stratified random guessing:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | 0.0207 | -0.0030 to 0.0430 | 0.073 | 0.365 |
| logreg vs stratified_random | 0.0193 | -0.0048 to 0.0416 | 0.106 | 0.425 |
| ma_cross_rule vs stratified_random | -0.0016 | -0.0213 to 0.0174 | 0.837 | 1.000 |
| momentum_rule vs stratified_random | 0.0027 | -0.0172 to 0.0228 | 0.794 | 1.000 |
| random_forest vs stratified_random | 0.0150 | -0.0138 to 0.0369 | 0.249 | 0.748 |

Jev arms against the reference traditional classifier:

_No comparison available: the Jev arms have not been run._

Does adding Jev outputs improve GBT?:

_No comparison available: the Jev arms have not been run._

### 20-day horizon (mean block 40 days)

Any skill: each model against stratified random guessing:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs stratified_random | -0.0100 | -0.0393 to 0.0130 | 0.449 | 1.000 |
| logreg vs stratified_random | 0.0123 | -0.0296 to 0.0428 | 0.561 | 1.000 |
| ma_cross_rule vs stratified_random | -0.0222 | -0.0490 to 0.0044 | 0.113 | 0.565 |
| momentum_rule vs stratified_random | 0.0014 | -0.0257 to 0.0316 | 0.934 | 1.000 |
| random_forest vs stratified_random | -0.0017 | -0.0350 to 0.0267 | 0.914 | 1.000 |

Jev arms against the reference traditional classifier:

_No comparison available: the Jev arms have not been run._

Does adding Jev outputs improve GBT?:

_No comparison available: the Jev arms have not been run._

## 6. Trading performance net of costs (dev folds)

Mode `long_only`: BUY names are held equally weighted (cap 10% per name per tranche), SELL and HOLD names are not held. Cost 5.0 bps per unit of turnover. Cash earns nothing and the Sharpe ratio uses a zero risk-free rate. `always_buy` holds every stock through the same engine and is the fair passive comparison.

### 1-day horizon

| Strategy | Net return | CAGR | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Exposure | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ma_cross_rule | 17.7% | 5.6% | 0.88 | 1.25 | -7.7% | 0.73 | 19.8 | 42.4% | 0.97 | 0.73 | 0.24 |
| market_buy_and_hold | 38.3% | 11.5% | 0.70 | 0.99 | -26.3% | 0.44 | 0.0 | 100.0% | n/a | n/a | n/a |
| gbt | 20.7% | 6.5% | 0.69 | 1.09 | -9.8% | 0.67 | 77.3 | 36.8% | 0.92 | 0.30 | -0.33 |
| always_buy | 32.6% | 9.9% | 0.69 | 0.97 | -21.5% | 0.46 | 0.3 | 99.9% | 0.69 | 0.68 | 0.69 |
| logreg | 16.1% | 5.1% | 0.61 | 0.93 | -8.5% | 0.60 | 44.2 | 26.8% | 0.76 | 0.36 | 0.09 |
| momentum_rule | 9.8% | 3.2% | 0.46 | 0.63 | -11.3% | 0.28 | 14.8 | 47.5% | 0.52 | 0.36 | 0.06 |
| random_forest | 5.2% | 1.7% | 0.21 | 0.31 | -13.9% | 0.12 | 60.7 | 37.9% | 0.38 | -0.07 | -0.55 |
| majority | 0.0% | 0.0% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.00 | 0.00 | 0.00 |
| stratified_random | -16.2% | -5.8% | -0.76 | -1.02 | -18.9% | -0.30 | 129.9 | 37.2% | -0.23 | -1.63 | -2.28 |

Mean realised forward return by predicted signal:

| Model | Pred. SELL | Pred. HOLD | Pred. BUY |
|---|---:|---:|---:|
| gbt | -0.004% | 0.011% | 0.121% |
| logreg | -0.012% | 0.033% | 0.118% |
| ma_cross_rule | 0.044% | 0.025% | 0.062% |
| majority | n/a | 0.042% | n/a |
| momentum_rule | 0.033% | 0.056% | 0.035% |
| random_forest | 0.002% | 0.051% | 0.055% |
| stratified_random | 0.042% | 0.067% | 0.009% |

Net Sharpe difference against `always_buy`:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | 0.0037 | -0.8101 to 1.0276 | 0.993 | 1.000 |
| logreg vs always_buy | -0.0779 | -1.1093 to 0.8982 | 0.897 | 1.000 |
| ma_cross_rule vs always_buy | 0.1956 | -0.6090 to 0.9197 | 0.645 | 1.000 |
| momentum_rule vs always_buy | -0.2281 | -1.0530 to 0.5778 | 0.591 | 1.000 |
| random_forest vs always_buy | -0.4742 | -1.4002 to 0.4990 | 0.332 | 1.000 |

### 5-day horizon

| Strategy | Net return | CAGR | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Exposure | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market_buy_and_hold | 38.3% | 11.5% | 0.70 | 0.99 | -26.3% | 0.44 | 0.0 | 100.0% | n/a | n/a | n/a |
| logreg | 20.5% | 6.4% | 0.69 | 1.04 | -10.0% | 0.64 | 15.1 | 36.4% | 0.74 | 0.61 | 0.25 |
| always_buy | 32.0% | 9.7% | 0.68 | 0.95 | -21.5% | 0.45 | 0.6 | 99.3% | 0.68 | 0.67 | 0.68 |
| momentum_rule | 12.8% | 4.1% | 0.58 | 0.80 | -9.9% | 0.42 | 7.8 | 49.1% | 0.61 | 0.53 | 0.04 |
| random_forest | 14.5% | 4.6% | 0.51 | 0.78 | -11.0% | 0.42 | 14.3 | 34.5% | 0.56 | 0.44 | 0.07 |
| ma_cross_rule | 8.9% | 2.9% | 0.46 | 0.63 | -8.7% | 0.33 | 9.7 | 43.0% | 0.51 | 0.39 | -0.24 |
| gbt | 12.5% | 4.0% | 0.45 | 0.66 | -11.3% | 0.36 | 14.5 | 36.7% | 0.49 | 0.37 | -0.16 |
| stratified_random | 3.7% | 1.2% | 0.21 | 0.29 | -10.7% | 0.11 | 27.2 | 40.6% | 0.33 | 0.01 | -0.65 |
| majority | 0.0% | 0.0% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.00 | 0.00 | 0.00 |

Mean realised forward return by predicted signal:

| Model | Pred. SELL | Pred. HOLD | Pred. BUY |
|---|---:|---:|---:|
| gbt | 0.207% | 0.140% | 0.306% |
| logreg | 0.101% | 0.110% | 0.426% |
| ma_cross_rule | 0.411% | 0.131% | 0.164% |
| majority | n/a | 0.211% | n/a |
| momentum_rule | 0.346% | 0.149% | 0.192% |
| random_forest | 0.106% | 0.168% | 0.343% |
| stratified_random | 0.178% | 0.284% | 0.145% |

Net Sharpe difference against `always_buy`:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.2317 | -0.9652 to 0.5091 | 0.548 | 1.000 |
| logreg vs always_buy | 0.0162 | -0.7028 to 0.7640 | 0.970 | 1.000 |
| ma_cross_rule vs always_buy | -0.2147 | -0.9235 to 0.4937 | 0.545 | 1.000 |
| momentum_rule vs always_buy | -0.0994 | -0.9100 to 0.6530 | 0.791 | 1.000 |
| random_forest vs always_buy | -0.1630 | -0.9997 to 0.6008 | 0.661 | 1.000 |

### 20-day horizon

| Strategy | Net return | CAGR | Sharpe | Sortino | Max DD | Calmar | Turnover/yr | Exposure | Sharpe @2bps | Sharpe @10bps | Sharpe L/S |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| logreg | 26.2% | 8.1% | 0.82 | 1.21 | -12.9% | 0.63 | 6.7 | 47.0% | 0.84 | 0.79 | 0.60 |
| market_buy_and_hold | 38.3% | 11.5% | 0.70 | 0.99 | -26.3% | 0.44 | 0.0 | 100.0% | n/a | n/a | n/a |
| stratified_random | 12.8% | 4.1% | 0.60 | 0.83 | -11.0% | 0.38 | 7.0 | 44.8% | 0.62 | 0.55 | 0.44 |
| always_buy | 26.5% | 8.2% | 0.59 | 0.82 | -21.5% | 0.38 | 0.7 | 97.3% | 0.59 | 0.59 | 0.59 |
| random_forest | 15.3% | 4.9% | 0.58 | 0.87 | -12.8% | 0.38 | 5.5 | 38.1% | 0.60 | 0.55 | -0.18 |
| ma_cross_rule | 8.4% | 2.8% | 0.45 | 0.60 | -10.6% | 0.26 | 4.2 | 40.8% | 0.47 | 0.42 | -0.32 |
| gbt | 12.4% | 4.0% | 0.45 | 0.66 | -14.2% | 0.28 | 5.7 | 43.3% | 0.46 | 0.42 | -0.34 |
| momentum_rule | 8.3% | 2.7% | 0.42 | 0.57 | -10.7% | 0.25 | 2.8 | 44.0% | 0.43 | 0.40 | -0.00 |
| majority | 0.0% | 0.0% | 0.00 | 0.00 | 0.0% | n/a | 0.0 | 0.0% | 0.00 | 0.00 | 0.00 |

Mean realised forward return by predicted signal:

| Model | Pred. SELL | Pred. HOLD | Pred. BUY |
|---|---:|---:|---:|
| gbt | 1.518% | 0.065% | 0.899% |
| logreg | 0.327% | 0.071% | 1.497% |
| ma_cross_rule | 1.879% | 0.212% | 0.580% |
| majority | n/a | 0.736% | n/a |
| momentum_rule | 0.876% | 0.840% | 0.541% |
| random_forest | 1.409% | -0.016% | 1.164% |
| stratified_random | 0.737% | 0.656% | 0.817% |

Net Sharpe difference against `always_buy`:

| Comparison | Difference | 95% interval | p | p (Holm) |
|---|---:|---:|---:|---:|
| gbt vs always_buy | -0.1417 | -0.6806 to 0.3155 | 0.551 | 1.000 |
| logreg vs always_buy | 0.2309 | -0.2903 to 0.7453 | 0.319 | 1.000 |
| ma_cross_rule vs always_buy | -0.1335 | -0.8311 to 0.4849 | 0.714 | 1.000 |
| momentum_rule vs always_buy | -0.1703 | -0.8403 to 0.3706 | 0.625 | 1.000 |
| random_forest vs always_buy | -0.0036 | -0.6016 to 0.5143 | 1.000 | 1.000 |

## 7. Runtime and cost

| Model | Fits | Configs per fit | Fit seconds | Predict seconds | Test rows |
|---|---:|---:|---:|---:|---:|
| gbt | 9 | 8 | 190.6 | 0.3 | 26,760 |
| logreg | 9 | 8 | 33.2 | 0.0 | 26,760 |
| ma_cross_rule | 9 | 6 | 0.3 | 0.0 | 26,760 |
| majority | 9 | 1 | 0.1 | 0.0 | 26,760 |
| momentum_rule | 9 | 8 | 0.4 | 0.0 | 26,760 |
| random_forest | 9 | 8 | 42.7 | 0.3 | 26,760 |
| stratified_random | 9 | 1 | 0.1 | 0.0 | 26,760 |

Traditional models run locally at no marginal cost. Jev API status: zero: not run: no saved Jev outputs; examples: not run: no saved Jev outputs.

Models that did not run:

- `jev_head_examples` (GBT on Jev outputs, with training examples): not run: no saved Jev outputs
- `jev_head_zero` (GBT on Jev outputs, zero-shot): not run: no saved Jev outputs
- `jev_plus_controlled_examples` (GBT on controlled features + Jev outputs, with examples): not run: no saved Jev outputs
- `jev_plus_controlled_zero` (GBT on controlled features + Jev outputs, zero-shot): not run: no saved Jev outputs
- `jev_signal_examples` (Jev as signal, with training examples): not run: no saved Jev outputs
- `jev_signal_zero` (Jev as signal, zero-shot): not run: no saved Jev outputs

## 8. Limitations

- Survivorship and hindsight bias in the stock list.
- Free vendor data: adjusted prices are revised after later corporate actions; opening prints may differ from achievable auction fills.
- Jev's training data and knowledge cutoff are undisclosed, so its historical results may reflect recall. Its state is anonymised to limit this, which cannot be proven sufficient.
- Jev is a hosted model that can change or be withdrawn; results are tied to the pinned version.
- Trading simulation ignores weight drift, market impact, borrow availability and taxes.
- Volatility-scaled labels make the size of a move partly predictable from volatility clustering. A model can score well on macro-F1 without predicting direction, so read macro-F1 together with the directional hit rate and the trading results.

## 9. Conclusion

**These are development-fold results. The locked final holdout has not been evaluated, so nothing below is a final finding.**

- **Classification performance:** insufficient evidence. No Jev arm has been run (not run: no saved Jev outputs).
- **Trading performance:** insufficient evidence, for the same reason.
- **Operational efficiency:** insufficient evidence. Jev runtime and cost have not been measured.
- **Overall:** the evidence does not yet bear on whether Jev is better than conventional classifiers.
