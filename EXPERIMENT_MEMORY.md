# EXPERIMENT_MEMORY.md

Authoritative record of the research decisions for this project. Read it before changing
methodology or interpreting results. Update it incrementally; never silently overwrite a
prior decision or result (see section 11).

Status markers: **DECIDED** (approved by the project owner), **PROVISIONAL** (proposed
default, implemented, not explicitly approved), **OPEN** (needs a decision or evidence).

Last updated: 2026-10-11. Pipeline implemented and validated on two smoke runs. **No Jev
call has been made, no full-universe run has been made, and no experimental result
exists.**

> **Discrepancy flagged 2026-10-11, unresolved.** This file describes a 100-stock universe.
> `config/experiment.yaml` at commit `79b2e86` lists 503 S&P 500 constituents
> (`sp500_2026-10-11`); `config/large_cap_100.yaml` restores the 100-stock list. The change
> was made by a second session working in this repository at the same time, on the owner's
> request there to "extend the trading universe to all stocks in S&P500" (referred to in
> the config as decision D9). D9 has not been written into this file yet. Until it is:
> treat the universe as **changing to the S&P 500**, treat the runtime and Jev cost
> estimates in section 9 as roughly five times too low, and record a new freeze commit in
> section 4 once D9 is written up.

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

- **Market and universe:** 100 large US stocks, fixed list `us_large_cap_100_v1` in
  `config/experiment.yaml`, plus SPY as market proxy. The list was chosen in 2026 with
  hindsight. **It is not point-in-time; survivorship and selection bias are accepted and
  must be stated in every report.**
- **Source:** yfinance daily bars, 2010-01-01 to 2026-09-30. Downloaded once, frozen as
  parquet with a SHA-256; that hash is the dataset version.
- **Risk-free rate:** 13-week Treasury bill yield (`^IRX`, yfinance), frozen the same way.
  Daily rate = annual yield / 252; missing days carry the last published yield forward.
- **Missing price data:** rows with missing or non-positive prices are dropped and
  counted. Nothing is filled or interpolated.
- **Enhanced-information study (news or other text): not in scope now** (owner decision).

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
- **Design frozen at commit `79b2e86`** (2026-10-11). Basis for treating every fold
  as out-of-sample: when the design was fixed, the only results seen were two 12-stock
  smoke runs over three folds; no model is tuned on test folds; Jev wording `v1` had
  never been sent to the API.
- The code still removes data from 2024-10-01 onward unless a run is started with
  `--unlock-holdout --confirm-design-frozen`. That switch now means "run the verdict
  window". A run without it is a partial-window run and says so in its report.
- **Jev wording `v1` gets one attempt.** A pilot restricted to dates before 2014-10
  (`--pilot N`) may check that the client works and outputs are not degenerate. If the
  wording is changed after any evaluated date has been scored, later results are
  exploratory.
- Values frozen without explicit owner sign-off (marked \* in sections 3 and 6): horizons
  and primary horizon, k = 0.5, 5 bps cost, top-20% ranking fraction, Sharpe margin 0.2.
  **Until the first full-universe run is made they can still be changed cleanly**; doing
  so means recording a new freeze commit here.

*Superseded 2026-10-11:* the earlier plan held 2024-10 to 2026-09 as a locked holdout and
the sole confirmatory test. Dropped because a 2-year window cannot detect a realistic
Sharpe difference.

### State sent to external classifiers (fold-independent, so each row is sent once)

- No ticker, name, calendar date or price level.
- Each feature is shown as a bucket plus its value. Bucket cut-points are quantiles
  (10/30/70/90%) of all stocks over the 750 trading days *before* the row's month.
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

Question wording versions: `v1` (current; never sent to any API).

## 6. Evaluation Metrics and Decision Criteria — **DECIDED 2026-10-11 (D5 to D7)**

- **Primary test:** net Sharpe ratio difference at the 5-day horizon, on the verdict
  window, for the ranking portfolio.
- **Ranking portfolio (primary rule):** each day hold the top 20%\* of stocks by score,
  equally weighted, opened at the next open and held *h* days in *h* daily tranches. Fully
  invested, so it differs from buy and hold only in which stocks it holds. Score is
  P(BUY) − P(SELL) for probabilistic models and the raw signal strength for rules. Stocks
  without a score are never held. Ties are broken at random with a fixed seed, so
  `majority` and `stratified_random` both hold a random selection: the no-skill reference.
- **BUY-names portfolio (secondary rule):** hold the stocks labelled BUY, capped at 10%
  each per tranche; the rest is cash.
- **Buy-and-hold benchmark:** `always_buy`, every stock equally weighted through the same
  engine and costs. SPY (`market_buy_and_hold`) is context only, because the stock list
  was chosen with hindsight.
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

No full-universe run, no Jev run and no verdict-window run has been made.

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
| `tests/` | 75 tests: leakage, labels, splits, isolation, metrics, bootstrap, trade timing, ranking rule, Jev, providers |
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

Add `--overrides config/smoke.yaml` for the 12-stock check. `report` and `visualise` need a
run made with the current engine; `smoke_2026-10-11` predates it.

Measured or estimated cost (2026-10-11):
- Smoke benchmark: 155 s. Full baseline run: about 1.5 to 2 hours (extrapolated from
  single-fit timings at 250k rows; not yet run).
- Jev, full universe, about 390k rows per variant (rough offline estimate): zero-shot
  about 2,400 tokens per request, about $40; with examples about 9,300 tokens per request,
  about $150; the token rate limit implies at least 10 hours for the example variant.

## 10. Outstanding Questions and Next Steps

Needs the owner:
1. Last chance to change the starred defaults (section 4) before the first full run.
2. Go-ahead for the full baseline run on the verdict window (about 2 hours, no fees).
3. `TYPESAFE_API_KEY` in `.env`, and a Jev budget (about $190 for both variants; cheaper
   with fewer examples per class or weekly sampling of training rows).
4. For OpenAI: which model, and a budget. For a local open model: hardware with a GPU.

Next steps, in order:
1. Download the full dataset; review the manifest for failed tickers.
2. Run the baseline benchmark on the verdict window; record the detectable effect here.
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
