# EXPERIMENT_MEMORY.md

Authoritative record of the research decisions for this project. Read it before changing
methodology or interpreting results. Update it incrementally; never silently overwrite a
prior decision or result (see section 11).

Status markers: **DECIDED** (approved by the project owner), **PROVISIONAL** (proposed
default, implemented, not explicitly approved), **OPEN** (needs a decision or evidence).

Last updated: 2026-10-12. **The universe changed on 2026-10-12 (D13, below): bitcoin was
removed and six stocks added, fifteen assets in all. Everything in this file that speaks of
"ten assets", bitcoin, `multi_asset_10_v1` or "top 3 of 10" describes the superseded
universe and is kept as history.** The baseline run in section 7 (traditional models and
rules, twelve folds) was made on the ten assets and is superseded; it is being repeated on
the fifteen. Jev calls have been made (a 50-row pilot, then a zero-shot annotation) but **no
Jev result has been scored yet, so there is still no result on the thesis.**

Two sessions worked on this repository in parallel on 2026-10-11; their work was combined
into one design at the freeze commit named in section 4.

---

## 1. Research Objective

**Thesis (owner's words, 2026-10-11):** can Jev as a classifier outperform traditional
models for stock trading, compared against buy and hold and against a Jev-augmented
classifier.

Three comparisons answer it, all on the net Sharpe ratio of the same portfolio rule:
1. **Jev alone** (J1, J2) versus the reference traditional classifier.
2. **Jev-augmented classifier** (J5, J6) versus the same classifier without Jev (B3).
3. **Jev alone versus Jev-augmented.**
Each is also compared with equal-weight buy and hold.

**Evidence for the thesis** (all required): a Jev-alone arm beats both the reference
classifier and buy and hold by at least the predefined margin, the paired time-aware
interval excludes zero after multiple-comparison correction, and the advantage is not
confined to one horizon, fold, regime or sensitivity variant.

**Evidence against:** no reliable difference, or Jev worse, on the primary test.
"Insufficient evidence" is a valid and likely conclusion: section 5 of every report states
the smallest difference the run could have detected.

The thesis says "stock trading". Since decision D10 the universe is ten assets of
different kinds, only some of them stocks (section 3); the question and the test are
otherwise unchanged.

*Superseded 2026-10-11:* the first version of this section framed the question as
classification quality (macro-F1). Classification is now a diagnostic.

## 2. Non-Negotiable Research Rules

1. No look-ahead bias or data leakage. Every feature uses only information available at
   the prediction timestamp.
2. No random splitting of time-dependent observations as the primary evaluation.
3. No tuning on test folds: hyperparameters, thresholds, calibration, question wording,
   feature representation and model selection use training and validation data only.
4. No unequal-information comparison presented as an equivalent comparison.
5. No unsupported claims of statistical significance.
6. No claims of profitability based on classification accuracy alone.
7. No fabricated data or results. Missing or failed outputs are recorded as missing.
8. Question wording and state layout are hyperparameters. Every variant tried counts
   toward the multiple-testing budget, gets a new `jev.wording_version`, and is logged in
   section 5.
9. Every benchmark run is appended to `results/registry.jsonl`. Runs are never overwritten.
10. No billed API call without a stated cost estimate and an owner-approved budget.
11. After the design freeze (section 4), any change to features, labels, grids, trade
    rules or wording makes later results exploratory, and must be logged as such.

## 3. Data and Label Definitions

### What Jev is — **DECIDED 2026-10-11** (owner confirmed)

Jev is **TypeSafe's hosted "System One" model**, pinned to `jev-1.13.0`. The owner has no
API key yet. Facts below come from the vendor's documentation (index:
https://docs.typesafe.ai/llms.txt) as read on 2026-10-11, not from our own testing:

| Property | Finding | Source |
|---|---|---|
| Invocation | `POST https://api.typesafe.ai/v1/systemone` with `state`, `model`, `questions` | docs `/api` |
| Input | Text only: string, JSON object or array. 64k tokens per request; 32k for state plus longest question | docs `/models` |
| Output | No generated text. `Choice` (label + per-option probabilities + confidence), `Score`, `Noul` (probability of yes) | docs `/api` |
| Training on our data | None. "Jev is not fine-tuned or LoRA-adapted with customer data … the same weights serve every account" | docs `/models` |
| Memory / external data | No memory between calls and no tool or web access is documented. Not independently verified | docs |
| Training data and knowledge cutoff | **Not disclosed** | docs, blog |
| Versions | Pinned id `jev-1.13.0`; aliases move without notice; the response reports the versioned id | docs `/models` |
| Determinism | Not documented | — |
| Known weaknesses | "struggles with tasks that require numeric precision"; reads dates as text; loses accuracy with irrelevant state; `Choice` answers lean toward the first-listed option | docs `/model-jaggedness/jev-1.13` |
| Price and limits | $0.042 per million input tokens, output free; 100K tokens/s and 80 requests/s, subject to change | docs `/models` |

**openjev.com is not Jev.** Inspected 2026-10-11: it now calls itself "SemIf (formerly
OpenJev)", states "Not affiliated with or endorsed by TypeSafe", and is a browser demo
that reads option probabilities from the logits of small open models (Qwen3 0.6B,
MiniCPM5 2B, Qwen3.5 4B) fetched from Hugging Face. It offers no package or API. Results
from it say nothing about Jev. The technique is reserved here as the `local` provider
(section 5). This machine has no GPU (CPU-only PyTorch, 15 GB RAM), so a full local run
is not practical here.

### Data — **DECIDED 2026-10-11**

- **Market and universe (D10, owner, 2026-10-11):** ten assets of different kinds, list
  `multi_asset_10_v1` in `config/experiment.yaml`, plus SPY as market proxy. The owner
  named the S&P 500, gold and bitcoin and asked for seven more to be chosen:

  | Ticker | Exposure | Modelling rows start |
  |---|---|---|
  | `IVV` | S&P 500 (SPY is the market proxy and is never held, so the index is traded through IVV) | 2011-04 |
  | `GLD` | Gold | 2011-04 |
  | `BTC-USD` | Bitcoin, spot series; first bar 2014-09-17 | 2015-09 |
  | `TLT` | US Treasury bonds, 20+ years | 2011-04 |
  | `EFA` | Developed-market stocks outside North America | 2011-04 |
  | `EEM` | Emerging-market stocks | 2011-04 |
  | `USO` | Crude oil | 2011-04 |
  | `VNQ` | US real estate investment trusts | 2011-04 |
  | `UUP` | US dollar against a basket of currencies | 2011-04 |
  | `HYG` | US high-yield corporate bonds | 2011-04 |

  **The list was chosen in 2026 with hindsight** (bitcoin above all) **and that must be
  stated in every report.** Nine assets are available for the first test fold; bitcoin
  joins in 2015-09.
  - *Why:* the Jev bill for the S&P 500 universe (about $900) was too high for the owner.
    Ten assets cost about $20 (section 9).
  - *Superseded 2026-10-11, D9:* every S&P 500 constituent as listed on 2026-10-11 (503
    tickers, `sp500_2026-10-11`, dataset `725401c78cad`, frozen but never modelled). Still
    runnable with `--overrides config/sp500.yaml`. It is not point-in-time: 190 of the 503
    joined the index after 2014-10-01. If it is ever revived, decide first whether to use
    each stock only from its index-join date, and see section 8, items 18 and 19.
  - *Superseded 2026-10-11:* 100 large US stocks, hand-fixed list `us_large_cap_100_v1`.
    Still runnable with `--overrides config/large_cap_100.yaml`.
- **One calendar for every asset:** rows dated when the market proxy did not trade are
  dropped at download (`data.keep_market_days`), so bitcoin's weekend and holiday bars are
  removed (1,370 rows) and a "trading day" means the same for all ten. Bitcoin's return
  from Friday's open to Monday's open therefore spans the weekend.
- **Source:** yfinance daily bars, 2010-01-01 to 2026-09-30. Downloaded once, frozen as
  parquet with a SHA-256; that hash is the dataset version.
- **Risk-free rate:** 13-week Treasury bill yield (`^IRX`, yfinance), frozen the same way.
  Daily rate = annual yield / 252; missing days carry the last published yield forward.
- **Missing price data:** rows with missing or non-positive prices are dropped and
  counted. Nothing is filled or interpolated.
- **Enhanced-information study (news or other text): not in scope now** (owner decision).

### Universe change — **DECIDED 2026-10-12 (D13, owner)**

The owner asked to remove bitcoin and add six stocks so that the universe is fifteen.

- **New universe `mixed_15_v2`:** the nine remaining funds (`IVV GLD TLT EFA EEM USO VNQ UUP
  HYG`) plus six single stocks: `GOOGL PG IBM CVX WFC CSCO`, plus SPY as market proxy.
- **How the six were chosen (owner chose the "largest by 2009 market cap" rule):** the
  largest US companies by market capitalisation in 2009, skipping the twelve smoke-test
  stocks (`config/smoke.yaml`) so that the smoke runs still reveal nothing about the
  experiment's assets. Source: a retrospective S&P 500 market-cap table for 2009 on
  finhacker.cz (its date within 2009 is not stated; a second source could not be fetched).
  Ranks 1 to 13 were XOM, MSFT, WMT, GOOGL, AAPL, JNJ, PG, JPM, IBM, CVX, WFC, PFE, CSCO; the
  smoke set removed XOM, MSFT, WMT, AAPL, JNJ, JPM, PFE, leaving the six above. Chosen with
  no knowledge of later returns, but all six are still listed, a mild survivorship filter,
  and three of them are technology companies.
- **Ranking rule holds 4 of 15** (`rank_fraction: 0.27`) and the declared check holds 1 of 15
  (`rank_check_fraction: 0.07`). 0.3 and 0.1 of 15 would be 4.5 and 1.5 and round to 4 and 2,
  which would silently turn the top-1 check into a top-2; the fractions are set so the
  intent (about 30%, and a single-asset check) survives. **Flagged for the owner: this is a
  new D11 parameter choice.**
- **Data:** dataset `0b91d318b8c2` (SHA-256 `0b91d318b8c2b1ec98168ff3d4bc0c5c421765c9812a72b4b6726cef7b193f18`),
  downloaded 2026-10-12, 16 tickers, 67,376 rows, none dropped, every ticker has all 4,211
  trading days from 2010-01-04, so there are no late starters and the calendar rule now removes
  nothing. Two daily moves beyond 25%: USO in 2020 and **IBM -25% on 2026-07-14** (67M shares
  traded against a normal 4M; the unadjusted and adjusted closes agree, so it is a real move
  and not a data error). It falls inside the locked holdout.
- **What this invalidates:**
  - The ten-asset baseline (`baseline_multi_asset_v1`, `rerun_dev_2026-10-12`) and the
    published report: superseded, kept as history.
  - **All Jev responses bought so far.** Each Jev prompt buckets an asset against the pooled
    group and includes its rank within the group, so every state changes with the universe.
    31,873 of 32,839 ten-asset zero-shot requests (about $3.6) had been paid for when the run
    was stopped; none was scored and none can be reused.
  - The freeze recorded at `7223fb6`. The design is re-frozen at the commit that contains
    D13. The D12 rolling-window variants are re-run on the new universe.
- **Unchanged:** features, labels, grids, trade rules (apart from the two fractions above),
  Jev wording `v2`. The v2 text did not change; only the values filled into it do. The
  earlier ten-asset annotation never produced a result that could have guided any choice.
- **Cost on the fifteen assets** (`jev-estimate`, rough): 50,940 rows through 2024-09, about
  $5.3 zero-shot and $20.8 with examples; about 8% more at the pilot's measured token usage,
  so about $5.8 and $22.4.
- *Superseded 2026-10-12 by D13:* the ten-asset list in D10 above, including the statements
  about bitcoin, the nine-asset first fold, and the 18% bitcoin share of the trend rules.

### Task — **FROZEN 2026-10-11** (see section 4; values marked * were provisional defaults)

- **Prediction timestamp:** after the close of day *t*, using data up to and including *t*.
- **Execution:** open of *t+1*.
- **Label return:** open(*t+1*) to open(*t+1+h*), dividend and split adjusted.
- **Horizons\*:** 1, 5, 20 trading days. Primary: 5.
- **Labels\*:** BUY if forward return > +k·σ_t·√h, SELL if < −k·σ_t·√h, else HOLD; σ_t is
  the standard deviation of daily returns over the 60 days ending at *t*; k = 0.5.
- **Features:** 27 price- and volume-derived features (`jevbench/features.py`), all returns
  or ratios, identical for every model. Rows with any missing feature are dropped for all
  models, then the first 63 trading days are dropped for all models.
- **Sensitivity set:** k ∈ {0.25, 0.75}; fixed thresholds {1d: 0.75%, 5d: 1.5%, 20d: 3%};
  volatility window ∈ {20, 120}.

## 4. Experimental Protocol

- **Walk-forward:** expanding training window; 12-month test folds starting 2014-10-01;
  twelve folds through 2026-09-30.
- **Validation:** the 12 months before each test fold. All tuning uses it. The final fit
  uses train + validation.
- **Purge and embargo:** `h + 1` trading days purged before every boundary plus an embargo
  of `h` days; each row's label end date is also checked against the next segment.
- **Preprocessing:** fitted inside each model on fitting rows only.
- **Reference classifier:** the traditional classifier with the best mean *validation*
  macro-F1 per horizon. It is never chosen on test results.
- **Failed external answers** count as wrong predictions and are never held; the failure
  rate is reported.

### Verdict window and design freeze — **DECIDED 2026-10-11 (D8)**

- The verdict rests on **all twelve folds pooled, 2014-10 to 2026-09** (segment `all`).
  Results for the first ten folds and the last two are also reported separately as a
  robustness check.
- **Design frozen at commit `7223fb6`** (2026-10-11). Basis for treating every
  fold as out-of-sample: when the design was fixed, the only results seen were two
  12-stock smoke runs over three folds, on a universe that is no longer used; no model is
  tuned on test folds; no question wording had been sent to any API; nothing had been run
  on the ten assets.
- That commit includes everything decided on 2026-10-11: the ten-asset universe and
  single-calendar rule (D10), question wording `v2` (section 5), and the ranking rule of
  top 3 with a top-1 check (D11, section 6).
- *Superseded:* an earlier freeze was recorded at commit `79b2e86`, before D10 and D11.
  No full-universe run was made under it.
- The code still removes data from 2024-10-01 onward unless a run is started with
  `--unlock-holdout --confirm-design-frozen`. That switch now means "run the verdict
  window". A run without it is a partial-window run and says so in its report.
- **Jev wording `v2` gets one attempt.** A pilot restricted to dates before 2014-10
  (`--pilot N`) may check that the client works and outputs are not degenerate. If the
  wording is changed after any evaluated date has been scored, later results are
  exploratory.
- Values frozen without explicit owner sign-off (marked \* in sections 3 and 6): horizons
  and primary horizon, k = 0.5, 5 bps cost, Sharpe margin 0.2. The owner was offered the
  chance to change them before the first full run and went ahead with the run. **They are
  now fixed**: changing any of them makes later results exploratory.

*Superseded 2026-10-11:* the earlier plan held 2024-10 to 2026-09 as a locked holdout and
the sole confirmatory test. Dropped because a 2-year window cannot detect a realistic
Sharpe difference.

### Rolling-window variants (option A) — **DECIDED 2026-10-12 (D12, owner); EXPLORATORY**

The owner asked for rolling training windows of 3, 6, 9 and 12 months, each refitted every
W months (option A). The expanding-window design above stays the primary and reference
design; these four are **declared exploratory sensitivity variants** (rule 11) and each
adds comparisons to the multiple-testing count. They change no feature, label, trade rule
or wording.

- **Per fold, window W:** train = the W months before the validation window; validation =
  W/3 months (1, 2, 3, 4); refit on train + validation; test = the next W months. Purge and
  embargo are unchanged (`2h + 1` trading days before each boundary).
- **Config:** `config/rolling_<W>m.yaml` plus `config/rolling_small_samples.yaml` (tree leaf
  sizes cut from 50-200 to 10-20, still 8 configurations per fold). Code: `train_window_months`,
  `min_val_days` in `jevbench/splits.py`.
- **The 20-day horizon is skipped for W = 3 and 6.** The purge gap at 20 days is 41 trading
  days, which leaves no validation data in a 1 or 2 month window. Skipped, not forced.
  W = 9 and 12 cover all three horizons. The 5-day primary horizon runs for all four.
- **First test fold:** 2014-10-01, except W = 9 which starts 2015-01-01 so that the holdout
  start (2024-10-01) stays on a fold boundary. Test periods are therefore a few months
  shorter for W = 9.
- **Thin samples.** At W = 3 a fold trains on about 500 rows and validates on about 100,
  from labels that overlap by 5 days; validation macro-F1 is very noisy there. Read the
  3 and 6 month results as stress tests, not as competitors to the primary design.
- **Holdout stays locked** for these runs (development window only).
- **Jev costs nothing extra:** annotation is per row and independent of the fold.

### State sent to external classifiers (fold-independent, so each row is sent once)

- No ticker, name, calendar date or price level.
- Each feature is shown as a bucket plus its value. Bucket cut-points are quantiles
  (10/30/70/90%) of all assets over the 750 trading days *before* the row's month.
- Example variant: 4 examples per class (by primary-horizon label), drawn from the 250
  trading days before the month, only rows whose label windows for every horizon had
  closed before the month began. One example set per month.
- Each BUY/HOLD/SELL question is asked in three rotated option orders and the
  probabilities are averaged, to offset Jev's documented first-option lean.
- Every response is cached by content hash; a returned model id other than the pinned one
  aborts the run.

## 5. Model Registry

Tuned models get an equal budget of 8 configurations per fold, scored by validation
macro-F1.

| ID | Config name | Model | Inputs | Status |
|---|---|---|---|---|
| B0 | `majority` | Majority class | labels | implemented |
| B0r | `stratified_random` | Random draw at class frequencies (no-skill reference) | labels | implemented |
| B1 | `logreg` | Logistic regression, standardised | controlled features | implemented |
| B2 | `random_forest` | Random forest, 200 trees | controlled features | implemented |
| B3 | `gbt` | LightGBM | controlled features | implemented |
| R1 | `momentum_rule` | Volatility-scaled trailing return, 8 variants | controlled features | implemented |
| R2 | `ma_cross_rule` | Moving-average crossover, 6 variants | controlled features | implemented |
| J1 | `jev_signal_zero` | Jev's own probabilities, no examples | features as text | built, **not run** |
| J2 | `jev_signal_examples` | Jev's own probabilities, with examples | + training examples | built, **not run** |
| J3 | `jev_head_zero` | LightGBM on Jev outputs | Jev outputs (zero-shot) | built, **not run** |
| J4 | `jev_head_examples` | LightGBM on Jev outputs | Jev outputs (examples) | built, **not run** |
| J5 | `jev_plus_controlled_zero` | LightGBM on features + Jev outputs | both | built, **not run** |
| J6 | `jev_plus_controlled_examples` | LightGBM on features + Jev outputs | both | built, **not run** |

J1 and J2 are "Jev as a classifier". J5 and J6 are the "Jev-augmented classifier". J3 and
J4 show whether Jev's outputs alone carry information. Never merge arms into one "Jev"
number. K-Means is not included.

### Reserved providers — **DECIDED 2026-10-11** (owner: "buffer space" for an OpenAI classifier)

`jevbench/providers.py` registers external classifiers. Each gets the same six arms
(`<provider>_signal|head|plus_controlled_<zero|examples>`), the same state, the same
questions, and its own comparison family in the report.

| Provider | Column prefixes | Status |
|---|---|---|
| `jev` | `jevz`, `jevx` | client and annotator built; never run live |
| `openai` | `oaiz`, `oaix` | **reserved: no client.** Arm names resolve today and report "not run" |
| `local` | `lclz`, `lclx` | **reserved: no client.** Open model read through option logits (the SemIf technique) |

Before running a new provider, record here: the pinned model snapshot, how probabilities
are obtained (for a chat model, token log-probabilities over the option labels), its
knowledge cutoff, a cost estimate, and that it is a separate hypothesis family. A
general-purpose language model knows far more market history than Jev is documented to,
so contamination risk is higher and the anonymisation check (section 8, item 1) is
mandatory for it.

Question wording versions:
- `v1`: described "one large US stock". Never sent to any API. Superseded 2026-10-11.
- `v2` (current; never sent to any API): the same layout and questions with "stock"
  replaced by "asset", the snapshot introduced as one of "a small group of assets of
  different kinds", percentiles described as "among the assets in its group", and the
  market readings named "US stock market index". Required by D10; no other change.

## 6. Evaluation Metrics and Decision Criteria — **DECIDED 2026-10-11 (D5 to D7)**

- **Primary test:** net Sharpe ratio difference at the 5-day horizon, on the verdict
  window, for the ranking portfolio.
- **Ranking portfolio (primary rule, `rank`; D11, owner, 2026-10-11):** each day hold the
  **top 3 of the 10 assets** by score (`rank_fraction: 0.3`; also 3 while only nine assets
  have history), equally weighted, opened at the next open and held *h* days in *h* daily
  tranches. Fully invested, so it differs from buy and hold only in which assets it holds.
  Score is P(BUY) − P(SELL) for probabilistic models and the raw signal strength for
  rules. Assets without a score are never held. Ties are broken at random with a fixed
  seed, so `majority` and `stratified_random` both hold a random selection: the no-skill
  reference.
- **Top-1 check (`rank_check`; D11):** the same rule holding only the single top asset
  (`rank_check_fraction: 0.1`). Declared before any result was seen and reported beside
  the primary rule in every run. **It never decides the verdict.** The owner asked whether
  holding 1 asset made sense as the main test; it was kept as a check because it is the
  noisiest version, tests only the top pick, is likely to be dominated by bitcoin, and
  gives up the diversification that buy and hold keeps.
- **BUY-names portfolio (secondary rule, `buy_names`):** hold the assets labelled BUY,
  capped at 10% each per tranche; the rest is cash. With ten assets the cap keeps this
  book far from fully invested, so read its Sharpe ratio, not its return.
  **D14 (owner, 2026-10-12): each BUY gets a fixed slot of 1/15 of capital**
  (`max_weight: 0.0666667`), so an asset's weight never depends on how many other assets
  are BUY. Up to all fifteen can be held; the rest is cash. Still a secondary view, not the
  primary test: a book that is mostly in cash mixes selection with market exposure, and the
  always-HOLD and random baselines degenerate under it. One more comparison for the
  multiple-testing count. *Superseded by D14:* the 10% cap above, under which a name's
  weight was `min(1 / number of BUYs, 10%)`.
- **Buy-and-hold benchmark:** `always_buy`, every asset equally weighted through the same
  engine and costs. SPY (`market_buy_and_hold`) is context only.
- *Superseded 2026-10-11 by D11:* top 20% of the universe (2 of 10), a default the owner
  had not signed off.
- **Costs and cash:** 5 bps\* per unit of turnover; sensitivities at 2 and 10 bps. Idle
  cash earns the T-bill rate. Sharpe and Sortino use returns in excess of that rate.
- **Also reported:** net return, CAGR, maximum drawdown, Calmar, turnover, exposure, alpha
  (with bootstrap interval) and beta against the market, the long-short version of each
  rule, and for BUY-names the Sharpe of the same exposure spread over every stock.
- **Statistics:** paired stationary block bootstrap over dates (mean block max(10, 2h)
  days, 2,000 resamples); Holm correction within each comparison family and provider;
  significance level 0.05.
- **Decision rule:** an arm is "better" only if the Sharpe difference is at least 0.2\*,
  its interval lower bound is above zero and Holm-adjusted p < 0.05. The thesis is
  supported only if a Jev-alone arm is better than both the reference classifier and buy
  and hold. Implemented in `report.conclusion`.
- **Detectable effect:** every report states the typical interval half-width and the
  difference detectable with 80% power. Record the full baseline run's figure in section
  7 before Jev is run.
- **Diagnostics:** macro-F1 (margin +0.02), balanced accuracy, per-class precision and
  recall, confusion matrix, log loss, Brier, ECE, directional hit rate, results by fold,
  stock and regime.

*Superseded 2026-10-11:* primary metric macro-F1 with a +0.02 margin, and long-only
BUY-names as the main trading test.

## 7. Experiment History and Results

| Date | Code version | What was done | Result | Status |
|---|---|---|---|---|
| 2026-10-11 | none | Phase 1 inspection of local folder and GitHub repository | Both empty. Jev identified from public documentation | Superseded by owner confirmation |
| 2026-10-11 | none | Owner decisions, round 1: Jev = TypeSafe `jev-1.13.0` (no key yet); US large caps via yfinance; all Jev permutations; no text study | Sections 3 and 5 | Decided |
| 2026-10-11 | `8e9de43` | Pipeline implemented; 64 tests. Smoke run `smoke_2026-10-11` (12 stocks, 3 folds, baselines, dataset `72519f1d13e4`) | Runs end to end; labels matched an independent recomputation on 300 rows | **Not a finding.** Old engine: BUY-names only, zero risk-free rate. Its Sharpe ratios are not comparable with later runs |
| 2026-10-11 | `8e9de43` | Owner decisions, round 2 (D5 to D8): trading primary, ranking portfolio, equal-weight buy-and-hold benchmark, verdict on all twelve folds with the design frozen now | Sections 1, 4, 6 | Decided |
| 2026-10-11 | `79b2e86` | D5 to D8 implemented; provider registry added; 75 tests. Smoke run `smoke_v2_2026-10-11` (same 12 stocks and folds) | Runs end to end. Interval on a Sharpe difference about ±0.76 at 5 days, so this run could not detect a difference below about 1.1 | **Not a finding.** With 12 stocks the ranking portfolio holds 2 names |
| 2026-10-11 | `79b2e86` | Owner requests, round 3: backtest page as a local HTML file; openjev.com inspected; room reserved for an OpenAI classifier | `visualise` command; sections 3 and 5 | Done. openjev.com is not Jev and was not downloaded or run |
| 2026-10-11 | `79b2e86` | Owner decision D9: universe = all 503 S&P 500 tickers listed on 2026-10-11. Prices downloaded and frozen as dataset `725401c78cad` | 502 stocks obtained (`VYLR` has no bars before 2026-10); 1,984,450 rows; nothing dropped in cleaning. Stale pre-listing bars found in three tickers (section 8, item 18) | Superseded by D10 the same day. Data frozen; **no model was run on it** |
| 2026-10-11 | `7223fb6` | Owner decision D10: universe = ten assets (`multi_asset_10_v1`), because the S&P 500 Jev bill was too high. Calendar rule and wording `v2` added. Prices frozen as dataset `4df028245fc7` | All 11 tickers obtained; 45,137 rows; 1,370 off-calendar bitcoin rows dropped; no gaps, no zero-volume rows. 32,839 modelling rows through 2024-09 | Decided |
| 2026-10-11 | `7223fb6` | Owner decision D11: ranking rule holds the top 3 of 10 assets; top 1 reported as a declared check. Both sessions' work combined; outputs reworded from "stocks" to "assets"; 77 tests | Sections 4 and 6 | Decided; new freeze recorded |

| 2026-10-11 | `3988057` | **Baseline run `baseline_multi_asset_v1`**: verdict window (twelve folds, 2014-10-01 to 2026-09-22), ten assets, dataset `4df028245fc7`, traditional models and rules only. Benchmark code identical to the freeze commit `7223fb6`; the later commit changed the dashboard only. 704 s | See "Baseline results" below | **Real out-of-sample baseline results. Not a result on Jev** |
| 2026-10-12 | `115d3d1` | Fresh clone; prices re-downloaded (ten assets, SHA `9d73476d…`, differs from the original `4df02824…` because the vendor adjusts history retroactively). Dev-window run `rerun_dev_2026-10-12` (ten folds, 715 s) | 77 tests pass; run completes | Superseded by D13; not a finding |
| 2026-10-12 | `115d3d1` | Jev pilot: 50 rows dated before 2014-10, zero-shot, budget $0.10 | 50 of 50 answered, 0 failures, pinned model confirmed, outputs not degenerate; 2,693 billed tokens per request against 2,489 estimated (+8%); cost $0.0057 | Client verified against the live API. Says nothing about predictive power |
| 2026-10-12 | `115d3d1` | Zero-shot annotation of the ten-asset universe, cap $5, stopped by the owner-directed universe change at 31,873 of 32,839 rows (about $3.6) | None scored | **Discarded** with D13; nothing was learned from it |
| 2026-10-12 | uncommitted | Owner decision D12: rolling 3, 6, 9 and 12 month training windows as exploratory variants; `config/rolling_*m.yaml`; 80 tests | See section 4 | Decided, exploratory |
| 2026-10-12 | uncommitted | Owner decision D13: bitcoin removed, six stocks added, universe `mixed_15_v2`; dataset `0b91d318b8c2` frozen; 80 tests | See section 3 | Decided; design to be re-frozen at the next commit |
| 2026-10-12 | uncommitted | Owner decision D14: BUY-names rule uses a fixed 1/15 slot per name; test added; 81 tests | See section 6 | Decided; secondary view only |
| 2026-10-12 | uncommitted | **Jev zero-shot annotation, 15 assets** (`jev_outputs_mixed_15_v2_v2_zero`): 50,940 rows through 2024-09, wording `v2`, `jev-1.13.0`, cap $7 | 50,940 of 50,940 answered, 0 failures; 137.2M input tokens billed, **$5.76**; 27 minutes. Outputs not degenerate (HOLD is the top call for 83% of rows at 1 day, 50% at 5, 41% at 20) | Complete. Wording `v2` has now had its one attempt on this universe |
| 2026-10-12 | uncommitted | Baseline `mixed15_dev_traditional` and full dev run `mixed15_dev_full` (ten folds, 2014-10 to 2024-09, 15 assets, top 4 of 15, dataset `0b91d318b8c2`, Jev zero-shot arms included); rolling-window runs `mixed15_rolling_3m/6m/9m/12m` (D12; exploratory). Holdout locked throughout | 5-day primary, net Sharpe: equal-weight buy and hold 0.52, random selection 0.21, random forest 0.40, momentum 0.29, GBT 0.25, moving-average 0.25, **Jev signal 0.11, Jev head 0.06, Jev plus controlled 0.26**, logreg -0.15. Against buy and hold: Jev signal -0.41 (-0.72 to -0.14, Holm p 0.05), Jev head -0.46 (-0.70 to -0.23, p 0.00), Jev plus controlled -0.26 (-0.59 to +0.02, p 0.40). Jev plus controlled 0.26 against its Jev-free twin GBT 0.25 | **Development window only; the verdict window (holdout) has not been run.** Jev alone is below the random-selection line and no Jev arm beats buy and hold. Jev adds nothing measurable to the controlled features. Rolling variants: see run folders; results move around with window length without a monotonic pattern, as expected from noise (3 and 6 month runs are stress tests) |
| 2026-10-12 | uncommitted | **With-examples Jev sample check**: 1,500 random development rows, wording `v2`, cap $1, scored against zero-shot on the same rows (rank correlation of P(BUY) - P(SELL) with the forward return, macro-F1, log-loss). Output moved to `data/_sample_checks/` so no benchmark reads it as a full run | 1,500 of 1,500 answered, **$0.72**, 11.5k tokens billed per request (18% above the 9.7k estimate; full variant would be about $25). Zero-shot over all 50,940 rows: rank correlation +0.002 / -0.010 / -0.011 at 1 / 5 / 20 days, macro-F1 0.29 to 0.33 (random is about 0.33), log-loss 1.38 to 1.52 against 1.07 for the class prior alone. Examples minus zero-shot rank correlation: +0.004 (-0.017, +0.026), -0.023 (-0.049, +0.003), -0.004 (-0.046, +0.036); the two scores correlate 0.67 to 0.89; examples says HOLD for 62% of rows at 5 days against 43% true | No measurable gain from examples; not bought in full. Zero-shot Jev carries no ranking signal on this sample. A check this size could not see a true gain smaller than about 0.03 |

### Baseline results (run `baseline_multi_asset_v1`, 2026-10-11)

Primary test: 5-day horizon, top 3 of 10, all folds, net Sharpe ratio in excess of the
T-bill rate. Full tables: `results/baseline_multi_asset_v1/report.md` and
`EXPERIMENT_REPORT.md`; charts: `results/baseline_multi_asset_v1/backtests.html`.

| Strategy | Sharpe | Difference from equal-weight buy and hold (95% interval) |
|---|---:|---|
| Moving-average rule | 1.40 | +0.46 (−0.01 to +0.90) |
| Momentum rule | 1.26 | +0.32 (−0.21 to +0.81) |
| Equal-weight buy and hold | 0.94 | — |
| Random forest (reference classifier) | 0.86 | −0.08 (−0.52 to +0.36) |
| Logistic regression | 0.85 | −0.09 (−0.55 to +0.40) |
| SPY buy and hold (context) | 0.74 | — |
| Gradient-boosted trees | 0.60 | −0.34 (−0.77 to +0.09) |
| Random selection (no skill) | 0.41 | — |

- **No strategy is reliably different from buy and hold** on the primary test: every
  interval includes zero and the smallest Holm-adjusted p is 0.24.
- **Detectable effect:** the interval on a Sharpe difference is typically ±0.45, so a true
  difference below about 0.65 would usually be missed. The margin for "better" is 0.2.
  For Jev to be called better it must beat both the random forest (0.86) and buy and hold
  (0.94) with an interval that excludes zero, which in practice needs a Sharpe ratio
  around 1.5 or more.
- **Top-1 check:** same picture. Moving-average rule +0.40 (−0.18 to +0.96); nothing
  reliable.
- **Other horizons:** at 1 day the three classifiers are reliably *worse* than buy and
  hold on the primary rule (−0.62 to −0.82, Holm p ≤ 0.04), because daily turnover costs
  eat them. At 20 days nothing is reliable.
- **Classification versus trading:** the classifiers beat random guessing on macro-F1 by
  about 0.03 at 1 and 5 days (Holm p = 0.002) yet do not beat buy and hold when traded.
  This is pitfall 4 in practice.
- **By period:** the moving-average rule leads in both parts (Sharpe 1.24 against 0.82 for
  buy and hold before 2024-10; 1.76 against 1.20 after).
- **Not tested:** how much of the trend rules' lead comes from bitcoin. The moving-average
  rule placed 18% of its positions in bitcoin against 9% for buy and hold. Any breakdown
  by asset would be exploratory.

No Jev run has been made.

## 8. Known Failure Modes and Pitfalls

1. **Pretraining contamination.** Jev's training data and cutoff are undisclosed, so a
   historical backtest may test recall. The state is anonymised to limit this; that cannot
   be proven sufficient. **Planned check, not yet built:** ask the model to identify the
   year or sector from a state and confirm it does no better than chance. Mandatory for
   any general-purpose language model.
2. **Unequal learning.** Traditional models train on labels; signal arms do not. Report
   all six arms of a provider separately.
3. **Low power.** Sharpe differences have wide intervals. Read "no reliable difference"
   together with the detectable-effect figure; it is not evidence of equality.
4. **Models are tuned for classification, not trading.** Grids are scored on validation
   macro-F1. A model can classify better and trade worse.
5. **Macro-F1 has a misleading floor.** The majority baseline scores about 0.19 and random
   guessing about 0.33. Compare against `stratified_random`.
6. **Volatility-scaled labels reward predicting move size.** Macro-F1 can rise without any
   ability to predict direction.
7. **Numeric weakness.** The vendor says Jev handles numbers poorly; the text
   representation is a tuned choice.
8. **Choice order bias.** Handled by averaging three rotated orders; the spread between
   orders is saved per row.
9. **Version drift and withdrawal.** Jev is an early-access product.
10. **Survivorship bias** inflates every absolute return, including buy and hold of the
    same list. It makes SPY an unfairly easy benchmark, which is why SPY is context only.
11. **Overlapping labels** at 5 and 20 days: effective sample size is far below row count.
12. **Multiple testing** across horizons, rules, arms, providers, wordings and reruns.
13. **Small universes distort both rules.** With 12 stocks the ranking portfolio holds 2
    names; with few BUY names the 10% cap leaves the BUY-names book under-invested.
14. **Backtest simplifications:** no weight drift, one all-in cost, no market impact or
    borrow limits, opening prints assumed achievable.
15. **Free data:** yfinance had transient failures during development. The downloader
    retries and records failures. Check the manifest after every download.
16. **Token estimates are rough** (3.5 characters per token) until a pilot reports usage.
17. **Sharpe ratios changed definition** on 2026-10-11 (now in excess of the T-bill rate).
    Do not compare the first smoke run's figures with later ones.
18. **Stale bars before a US listing** (S&P 500 override only). In dataset `725401c78cad`,
    `SW` (to 2024-07), `FERG` (to 2021-03) and `AMCR` (to 2019-06) carry 5,859 zero-volume
    rows from before their US listings, nearly all with a flat price. Nothing removes them.
19. **Two share classes of one company** (S&P 500 override only: GOOGL/GOOG, FOXA/FOX,
    NWSA/NWS) get near-identical scores, so the ranking portfolio can hold one company twice.
20. **Ten assets is a small universe** (see item 13). The ranking portfolio holds 3 of the
    10, and the top-1 check holds one. Expect a wide interval on any Sharpe difference
    against a margin of 0.2; section 7 records the measured figure. "No reliable
    difference" is the likely outcome for small true effects.
21. **Assets are recognisable from their readings.** Bucket cut-points pool all ten
    assets, so bitcoin always reads as "very high" volatility and the dollar fund as "very
    low"; the S&P 500 fund has a market-relative return of zero. The state hides the
    ticker but not, in effect, the asset. This raises the contamination risk in item 1
    and makes the planned anonymisation check more important.
22. **Bitcoin is executed with no delay.** Its daily bar closes at midnight UTC, the same
    instant as the next bar's open, so its signal and its fill share one price. The funds
    wait from the 16:00 close to the next 09:30 open. No future data is used, but
    bitcoin's fills are optimistic, and 5 bps understates its trading cost.
23. **Hindsight in the asset list.** Bitcoin was chosen knowing its history; equal-weight
    buy and hold of the ten is flattered by it from 2015-09. The comparison between models
    and that benchmark uses the same assets, so this inflates levels more than differences.
24. **Trend rules and bitcoin.** The two trend rules have the highest baseline Sharpe
    ratios and hold about twice the bitcoin that buy and hold does. Bitcoin was chosen
    with hindsight and is filled with no delay (item 22). Their lead is not reliable
    statistically and should not be read as a robust edge.

## 9. Architecture and Reproducibility

Interpreter: `C:\Users\dylan\anaconda3\python.exe` (Python 3.11.5). The `python` on PATH
is a different install. Versions in `requirements.txt`. Seed: `20261011` in the config;
per-fit seed = seed + 1000·h + fold.

| Path | Role |
|---|---|
| `config/experiment.yaml` | Single source of configuration. `config/smoke.yaml` overrides for a fast check |
| `jevbench/data.py` | Download, freeze, load prices and the risk-free rate; data lock |
| `jevbench/features.py`, `labels.py`, `dataset.py` | Features, labels, modelling table |
| `jevbench/splits.py` | Purged walk-forward folds |
| `jevbench/models/` | Baselines, classifiers, rules, external-provider arms |
| `jevbench/providers.py` | Registry of external classifiers (Jev; OpenAI and local reserved) |
| `jevbench/jev.py` | State builder, cached Jev client, annotation, cost estimate. **Never run against the live API** |
| `jevbench/evaluate.py`, `stats.py`, `backtest.py` | Metrics, bootstrap, trading simulation |
| `jevbench/benchmark.py`, `report.py`, `run.py` | Orchestration, report, command line |
| `jevbench/visualise.py`, `visualise_template.html` | Self-contained local HTML page of a run's backtests |
| `tests/` | 77 tests: leakage, labels, calendar, splits, isolation, metrics, bootstrap, trade timing, ranking rules, Jev, providers |
| `results/<run>/` | Config, manifest, metrics, fit log, `report.md`, `backtests.html` (predictions kept locally) |

Commands (run from the repository root with the interpreter above):

```
python -m pytest -q
python -m jevbench.run download                      # freeze prices and the T-bill rate
python -m jevbench.run quality
python -m jevbench.run benchmark --name <run>        # partial window (first ten folds)
python -m jevbench.run benchmark --name <run> --unlock-holdout --confirm-design-frozen   # verdict window
python -m jevbench.run sensitivity                   # the five predefined variants
python -m jevbench.run report --name <run> [--publish]   # --publish writes EXPERIMENT_REPORT.md
python -m jevbench.run visualise --name <run>        # writes results/<run>/backtests.html
python -m jevbench.run jev-estimate                  # offline cost estimate
python -m jevbench.run jev-annotate --variant zero --approved-cost-usd <N> [--pilot N | --sample N]
```

Add `--overrides config/smoke.yaml` for a fast pipeline check. It deliberately uses 12
stocks that are *not* in the experiment's universe and only three folds, so checking the
code never reveals anything about the ten assets. `report` and `visualise` need a run made
with the current engine; `smoke_2026-10-11` predates it. `config/sp500.yaml` and
`config/large_cap_100.yaml` restore the two superseded stock universes.

Measured or estimated cost (2026-10-11):
- Smoke benchmark: 155 s.
- Ten-asset universe, dataset `4df028245fc7`: 32,839 modelling rows through 2024-09;
  about 37,800 through 2026-09 (extrapolated from price-row counts).
- Full baseline run on the verdict window: roughly 15 to 30 minutes on this machine
  (extrapolated from the smoke run, which is a third of the folds; not yet run).
- Jev (`jev-estimate`, offline, rough): 2,489 tokens per zero-shot request and 9,714 with
  examples. For the 32,839 rows through 2024-09: $3.43 and $13.40, $16.83 for both
  variants, and under an hour each at the rate limit. Scaled to the full window: **about
  $20 for both variants.**
- *Superseded 2026-10-11 (S&P 500 universe, D9):* 1,578,433 rows through 2024-09; baseline
  about 7 to 8 hours (one mid-sample fit on 960k rows took 62 s for logreg, 381 s for
  random forest, 163 s for GBT); Jev about $900 and about 12 + 47 hours; the predictions
  table would be about 57 million rows with all Jev arms and may not fit in 14 GB.
- *Superseded 2026-10-11 (100-stock universe):* baseline 1.5 to 2 hours; Jev about 390k
  rows per variant, about $40 and $150.

## 10. Outstanding Questions and Next Steps

Needs the owner:
1. `TYPESAFE_API_KEY` in `.env`, and a Jev budget (about $20 for both variants on the
   ten assets).
2. For OpenAI: which model, and a budget. For a local open model: hardware with a GPU.

Settled 2026-10-11: the ranking rule (D11) and the go-ahead for the baseline run on the
verdict window.

Next steps, in order:
1. ~~Download the full dataset; review the manifest for failed tickers.~~ Done 2026-10-11
   (ten assets, none failed).
2. ~~Baseline benchmark on the verdict window.~~ Done 2026-10-11 (section 7).
3. With a key: `jev-annotate --pilot` (suggested budget $1) to verify the client against
   the live API, measure real token usage and check outputs are not degenerate.
4. Build and run the anonymisation check (pitfall 1).
5. Full Jev annotation, verdict run with Jev arms, sensitivity runs, final report.
6. Then, if wanted: OpenAI client, its own pilot and run.

## 11. Instructions for Future AI Sessions

- Read this file before modifying the methodology or interpreting any result.
- Preserve established decisions unless new evidence justifies a documented change.
- Update this file whenever an assumption, method, important configuration or major result
  changes, and record the reason.
- Never silently overwrite a prior decision or historical result; append and mark the old
  entry as superseded.
- If project code conflicts with this file, flag the discrepancy to the owner. Do not pick
  one silently.
- Do not run billed API calls beyond an approved budget. State the expected cost first.
- The design is frozen (section 4). Do not change features, labels, grids, trade rules or
  question wording without the owner's agreement, a new `jev.wording_version` where
  relevant, and a log entry marking later results exploratory.
- Add an external classifier only through `jevbench/providers.py`, and record it in
  section 5 before running it.
- Smoke-run numbers are pipeline checks. Never report them as findings.
- The owner wants visualisations as local HTML files (`visualise` command), not hosted
  artifacts.
