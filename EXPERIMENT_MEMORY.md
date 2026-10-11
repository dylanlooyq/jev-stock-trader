# EXPERIMENT_MEMORY.md

Authoritative record of the research decisions for this project. Read it before changing
methodology or interpreting results. Update it incrementally; never silently overwrite a
prior decision or result (see section 11).

Status markers: **DECIDED** (approved by the project owner), **PROVISIONAL** (proposed
default, implemented, not yet approved), **OPEN** (needs a decision or evidence).

Last updated: 2026-10-11. Pipeline implemented and validated on a smoke run. **No Jev
call has been made and no experimental result exists yet.**

> **Read section 0 first.** The owner's second round of decisions on 2026-10-11 changes the
> primary test from classification to trading. Sections 4 and 6 still describe the code as
> it stands; where they conflict with section 0, section 0 is the decision and the code is
> behind.

## 0. Owner Decisions of 2026-10-11 (second round) — **DECIDED, implementation pending**

Thesis as stated by the owner: *can Jev as a classifier outperform traditional models for
stock trading*, compared against buy and hold and against a Jev-augmented classifier.

| # | Decision | Supersedes |
|---|---|---|
| D5 | **Trading performance is the primary test.** The verdict rests on the net Sharpe difference. Macro-F1 and other classification metrics are diagnostics | Section 6 "Primary: pooled macro-F1" and the macro-F1 decision rule |
| D6 | **Ranking portfolio is the primary trade rule:** each day hold the top fifth of stocks by P(BUY) − P(SELL), fully invested. The hold-the-BUY-names portfolio is secondary | Section 6 "long-only primary (SELL = no position)" as the main test |
| D7 | **Buy-and-hold benchmark = equal-weight universe** through the same engine and costs. SPY is context only, because the stock list was chosen with hindsight | — |
| D8 | **Verdict on the full walk-forward, 2014-10 to 2026-09, with the design frozen now.** The separate 2-year holdout is dropped as the sole confirmatory test. Jev wording `v1` gets one attempt; any later rewording is exploratory only | Section 4 "Final holdout … LOCKED" as the confirmatory test |

Three comparisons answer the thesis, all on net Sharpe of the ranking portfolio:
1. Jev alone (J1, J2) versus the reference traditional classifier.
2. Jev-augmented classifier (J5, J6) versus the same classifier without Jev (B3).
3. Jev alone versus Jev-augmented.
Each is also compared with equal-weight buy and hold.

Also agreed, to implement with the above: idle cash earns the T-bill rate and Sharpe uses
excess returns; an exposure-matched benchmark; alpha and beta against the market; the
minimum detectable effect written down before Jev runs; the Jev pilot restricted to rows
before 2014-10.

**Design freeze.** It takes effect at the commit that implements D5 to D8; record that
commit hash here. Basis for treating all folds as out-of-sample: no full-universe result
had been seen when the design was fixed (only the 12-stock smoke run), and no model is
tuned on test folds. After the freeze, any change to features, labels, grids, trade rules
or Jev wording makes subsequent results exploratory and must be logged as such.

---

## 1. Research Objective

**Question.** Does Jev produce better BUY / HOLD / SELL stock-price classifications than
conventional classifiers given the same information, and does any such advantage survive
as trading performance net of costs?

**Evidence for Jev's superiority** (all required):
- A Jev arm beats the reference traditional classifier on the primary metric by at least
  the predefined margin (section 6), on identical out-of-sample observations.
- The paired, time-aware confidence interval for the difference excludes zero after
  multiple-comparison correction.
- The advantage is not confined to one horizon, one label threshold, one fold or one
  market regime.

**Evidence against:** Jev is statistically indistinguishable from or worse than the
reference classifier, or wins only in a narrowly selected configuration.

"Insufficient evidence" is a valid and likely conclusion. Short-horizon stock direction has
a very low signal-to-noise ratio; a result in which no model beats random guessing is
plausible and must be reported as such.

## 2. Non-Negotiable Research Rules

1. No look-ahead bias or data leakage. Every feature uses only information available at
   the prediction timestamp.
2. No random splitting of time-dependent observations as the primary evaluation.
3. No test-set tuning: hyperparameters, thresholds, calibration, Jev wording, feature
   representation and model selection never see the final holdout.
4. No unequal-information comparison presented as an equivalent comparison.
5. No unsupported claims of statistical significance.
6. No claims of profitability based on classification accuracy alone.
7. No fabricated data or results. Missing or failed outputs are recorded as missing.
8. Jev's question wording and state layout are hyperparameters. Every variant tried counts
   toward the multiple-testing budget, gets a new `jev.wording_version`, and is logged in
   section 5.
9. Every benchmark run is appended to `results/registry.jsonl`. Runs are never overwritten.
10. No billed Jev call without a stated cost estimate and an owner-approved budget.

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

Consequences: Jev is zero-shot with fixed weights, so training-fold information can reach
it only through the request or through a model trained on its outputs. Its probabilities
are available, so log loss and Brier score apply, but whether they are calibrated for this
task is an empirical question.

### Data — **DECIDED 2026-10-11**

- **Market and universe:** 100 large US stocks, fixed list `us_large_cap_100_v1` in
  `config/experiment.yaml`, plus SPY as market proxy. The list was chosen in 2026 with
  hindsight. **It is not point-in-time; survivorship and selection bias are accepted and
  must be stated in every report.**
- **Source:** yfinance daily bars, 2010-01-01 to 2026-09-30. Downloaded once, frozen as
  parquet with a SHA-256; that hash is the dataset version. Re-downloading creates a new
  version because adjusted prices are revised.
- **Missing data:** rows with missing or non-positive prices are dropped and counted.
  Nothing is filled or interpolated. Late-listed stocks enter when they have history.
- **Enhanced-information study (news or other text): not in scope now** (owner decision).

### Task — **PROVISIONAL** (implemented; awaiting owner approval before the design freeze)

- **Prediction timestamp:** after the close of day *t*, using data up to and including *t*.
- **Execution:** open of *t+1*.
- **Label return:** open(*t+1*) to open(*t+1+h*), dividend and split adjusted.
- **Horizons:** 1, 5, 20 trading days. Primary: 5.
- **Labels:** BUY if forward return > +k·σ_t·√h, SELL if < −k·σ_t·√h, else HOLD; σ_t is
  the standard deviation of daily returns over the 60 days ending at *t*; k = 0.5.
- **Features:** 27 price- and volume-derived features (`jevbench/features.py`), all returns
  or ratios, identical for every model. Rows with any missing feature are dropped for all
  models, then the first 63 trading days are dropped for all models.
- **Sensitivity set (fixed in advance):** k ∈ {0.25, 0.75}; fixed thresholds
  {1d: 0.75%, 5d: 1.5%, 20d: 3%}; volatility window ∈ {20, 120}. Horizons 1 and 20 are
  reported alongside the primary.

## 4. Experimental Protocol — **PROVISIONAL**

- **Walk-forward:** expanding training window; 12-month test folds starting 2014-10-01;
  ten development folds through 2024-09-30.
- **Validation:** the 12 months before each test fold. All tuning uses it. The final fit
  uses train + validation.
- **Purge and embargo:** `h + 1` trading days purged before every boundary plus an embargo
  of `h` days; each row's label end date is also checked against the next segment.
- **Preprocessing:** fitted inside each model on fitting rows only.
- **Final holdout: 2024-10-01 to 2026-09-30, LOCKED.** Holdout rows are removed before
  features are computed. Unlocking needs `--unlock-holdout --confirm-design-frozen`.
  **The design has not been frozen. Do not unlock.**
- **Reference classifier:** the traditional classifier with the best mean *validation*
  macro-F1 per horizon. It is never chosen on test results.
- **Failed Jev answers** count as wrong predictions and as no position; the failure rate is
  reported.
- **Jev state construction (fold-independent, so each row is sent once):**
  - No ticker, name, calendar date or price level.
  - Each feature is shown as a bucket plus its value. Bucket cut-points are quantiles
    (10/30/70/90%) of all stocks over the 750 trading days *before* the row's month.
  - Example arm: 4 examples per class (by primary-horizon label), drawn from the 250
    trading days before the month, only rows whose label windows for every horizon had
    closed before the month began. One example set per month.
  - Each BUY/HOLD/SELL question is asked in three rotated option orders and the
    probabilities are averaged, to offset the documented first-option lean.
- Every Jev response is cached by content hash; a returned model id other than the pinned
  one aborts the run.

## 5. Model Registry

Tuned models get an equal budget of 8 configurations per fold.

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

Owner decision 2026-10-11: run all Jev permutations (signal versus features, with and
without examples). J1 and J2 test Jev as a classifier. J3 to J6 test whether Jev's outputs
carry information; J5/J6 against B3 is the direct ablation. A win for J3 to J6 is not
evidence that Jev is the better classifier. K-Means is not included.

Jev wording versions: `v1` (current; never sent to the API).

## 6. Evaluation Metrics and Decision Criteria — **PROVISIONAL**

- **Primary:** pooled macro-F1 at the 5-day horizon, Jev arm versus reference classifier.
- **Practically meaningful improvement:** at least +0.02 macro-F1.
- **Secondary:** balanced accuracy, accuracy, per-class precision and recall, confusion
  matrix, class distributions, log loss, multiclass Brier, ECE and reliability bins
  (probabilistic models only), directional hit rate, results by fold, stock and regime.
- **Trading:** long-only primary (SELL = no position), 10% cap per name per daily tranche,
  5 bps per unit of turnover; sensitivities at 2 and 10 bps and long-short with 50 bps
  borrow. Reported: net return, CAGR, Sharpe, Sortino, maximum drawdown, Calmar, turnover,
  exposure, positions opened, mean forward return by signal. Benchmarks: `always_buy`
  through the same engine, and SPY buy-and-hold.
- **Statistics:** paired stationary block bootstrap over dates (mean block
  max(10, 2h) days, 2,000 resamples) for macro-F1 and Sharpe differences; Holm correction
  within each family of comparisons; significance level 0.05.
- **Decision rule:** "supported" only if difference ≥ margin, interval lower bound > 0 and
  Holm-adjusted p < 0.05 at the primary horizon. Implemented in `report.conclusion`.

## 7. Experiment History and Results

| Date | Code version | What was done | Result | Status |
|---|---|---|---|---|
| 2026-10-11 | none | Phase 1 inspection of local folder and GitHub repository | Both empty. Jev identified from public documentation | Superseded by owner confirmation below |
| 2026-10-11 | uncommitted | Owner decisions: Jev = TypeSafe `jev-1.13.0` (no key yet); US large caps via yfinance; all Jev permutations; no text study | Recorded in sections 3 and 5 | Decided |
| 2026-10-11 | uncommitted | Pipeline implemented; 64 automated tests pass | See section 9 | Engineering validation |
| 2026-10-11 | uncommitted | Smoke run `smoke_2026-10-11`: 12 stocks, 3 development folds, baselines only, dataset `72519f1d13e4` | Pipeline runs end to end. Labels matched an independent recomputation on 300 sampled rows. Jev arms correctly reported as not run | **Not a finding.** Small universe, 3 folds. Do not cite its numbers |

| 2026-10-11 | uncommitted | Owner decisions D5 to D8 (section 0): trading primary, ranking portfolio, equal-weight buy-and-hold benchmark, verdict on the full 12 years with the design frozen now | Recorded; code not yet changed | Decided, implementation pending |

No full-universe run, no Jev run and no holdout evaluation has been made.

## 8. Known Failure Modes and Pitfalls

1. **Pretraining contamination.** Jev's training data and cutoff are undisclosed, so a
   historical backtest may test recall. The state is anonymised to limit this; that cannot
   be proven sufficient. **Planned check, not yet built:** ask Jev to identify the year or
   sector from a state and confirm it does no better than chance.
2. **Unequal learning.** Traditional models train on labels; J1 does not. Report all six
   Jev arms separately; never merge them into one "Jev" number.
3. **Macro-F1 has a misleading floor.** The majority baseline scores about 0.19 and random
   guessing about 0.33. Always compare against `stratified_random`, not `majority`.
4. **Volatility-scaled labels reward predicting move size.** Volatility clusters, so a
   model can gain macro-F1 by separating HOLD from non-HOLD without predicting direction.
   Read macro-F1 with the directional hit rate and trading results.
5. **Numeric weakness.** The vendor says Jev handles numbers poorly; the text
   representation is a tuned choice.
6. **Choice order bias.** Handled by averaging three rotated orders; the spread between
   orders is saved per row as a diagnostic.
7. **Version drift and withdrawal.** Jev is an early-access product.
8. **Survivorship bias** in the fixed stock list.
9. **Overlapping labels** at 5 and 20 days: effective sample size is far below row count.
10. **Multiple testing** across horizons, thresholds, arms, wordings and reruns.
11. **Costs and turnover** can erase a classification edge.
12. **Weight cap in small universes.** With few BUY names the 10% cap leaves the book
    under-invested, so compare Sharpe and exposure, not raw return.
13. **Backtest simplifications:** no weight drift, cash earns nothing, one all-in cost.
14. **Free data:** yfinance had a transient failure for one ticker during development; the
    downloader retries and records failures. Check the manifest after every download.
15. **Token estimates are rough** (3.5 characters per token). Real usage is known only
    after a pilot.

## 9. Architecture and Reproducibility

Interpreter: `C:\Users\dylan\anaconda3\python.exe` (Python 3.11.5). The `python` on PATH
is a different install. Versions in `requirements.txt`. Seed: `20261011` in the config;
per-fit seed = seed + 1000·h + fold.

| Path | Role |
|---|---|
| `config/experiment.yaml` | Single source of configuration. `config/smoke.yaml` overrides for a fast check |
| `jevbench/data.py` | Download, freeze, load; holdout lock |
| `jevbench/features.py`, `labels.py`, `dataset.py` | Features, labels, modelling table |
| `jevbench/splits.py` | Purged walk-forward folds |
| `jevbench/models/` | Baselines, classifiers, rules, Jev arms |
| `jevbench/jev.py` | Jev state builder, cached client, annotation, cost estimate. **Never run against the live API** |
| `jevbench/evaluate.py`, `stats.py`, `backtest.py` | Metrics, bootstrap, trading simulation |
| `jevbench/benchmark.py`, `report.py`, `run.py` | Orchestration, report, command line |
| `tests/` | 64 tests: leakage, labels, splits, isolation, metrics, bootstrap, trade timing, Jev |
| `results/<run>/` | Config, manifest, metrics, fit log, report (predictions kept locally) |

Commands (run from the repository root with the interpreter above):

```
python -m pytest -q
python -m jevbench.run download                      # freeze the full dataset
python -m jevbench.run quality
python -m jevbench.run benchmark --name <run>        # development folds, holdout locked
python -m jevbench.run sensitivity                   # the five predefined variants
python -m jevbench.run jev-estimate                  # offline cost estimate
python -m jevbench.run jev-annotate --variant zero --approved-cost-usd <N> [--sample N]
python -m jevbench.run report --name <run> [--publish]   # --publish writes EXPERIMENT_REPORT.md
```

Add `--overrides config/smoke.yaml` for the 12-stock check.

Measured or estimated cost (2026-10-11):
- Smoke benchmark: 279 s. Full development baseline run: about 1.5 to 2 hours
  (extrapolated from single-fit timings at 250k rows; not yet run).
- Jev, full universe including holdout, about 390k rows per variant (rough estimate):
  zero-shot about 2,400 tokens per request, about $40; with examples about 9,300 tokens
  per request, about $150; the token rate limit implies at least 10 hours for the example
  variant.

## 10. Outstanding Questions and Next Steps

Decisions needing owner approval:
1. Remaining provisional items: horizons and primary horizon, k = 0.5, 5 bps cost. (The
   primary test, trade rule, benchmark and test window were decided in section 0.)
2. Approve the full baseline run (about 2 hours local compute, no fees).
3. Jev budget: about $190 for both variants on all rows. Cheaper options: fewer examples
   per class, or annotate training rows weekly instead of daily.
4. Provide `TYPESAFE_API_KEY` in `.env`.

Next steps, in order:
1. Download the full dataset; review the manifest for failed tickers.
2. Run the development baseline benchmark.
3. With a key: a small Jev pilot on validation-period rows only (suggested budget $1) to
   verify the client against the live API, measure real token usage and check that outputs
   are not degenerate.
4. Build and run the anonymisation check (pitfall 1).
5. Full Jev annotation, development benchmark with Jev arms, sensitivity runs.
6. Record the design freeze here, then unlock the holdout once.

## 11. Instructions for Future AI Sessions

- Read this file before modifying the methodology or interpreting any result.
- Preserve established decisions unless new evidence justifies a documented change.
- Update this file whenever an assumption, method, important configuration or major result
  changes, and record the reason.
- Never silently overwrite a prior decision or historical result; append and mark the old
  entry as superseded.
- If project code conflicts with this file, flag the discrepancy to the owner. Do not pick
  one silently.
- Do not run billed Jev calls beyond an approved budget. State the expected cost first.
- Do not unlock the holdout until the design freeze is recorded in section 4.
- Do not edit `jev.build_questions` or the state layout without bumping
  `jev.wording_version` and logging the change in section 5.
- Smoke-run numbers are pipeline checks. Never report them as findings.
