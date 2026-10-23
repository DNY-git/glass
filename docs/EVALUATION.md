# EVALUATION — FORECAST SCORES AGAINST REALIZED RESULTS (PHASE 11, HANDOFF IX-11)

Status: exists since Phase 11 (2026-10-23). This document records what
Phase 11 computed and where each number is pinned. The anti-inflation
rule (glass-quant ruling ADV-10) governs every line below: **no number
appears here without a pinned test source** — every number is a literal
in `tests/test_evaluation.py` (or, for criterion 23, a recorded suite
gate), cited inline by criterion. Golden values were pinned in tests
FIRST, from the first green run, and are re-derived, never widened.

## 1. Purpose

Phase 11 is the evidence gate: the first-ever scoring of the frozen,
pre-registered walk-forward predictions (Phase 9's `app/backtesting/`
machinery) against realized results — strictly chronological, digest-
gated, and read-only over frozen `Forecast`s and `Match.score`. The
evaluated observation count went from exactly 0 to exactly **30
(primary) / 57 (secondary)** for the first time (criterion 1) — the
milestone this document records. The golden run digest is re-derived and
asserted BEFORE any metric computes (criterion 1); a tampered digest
refuses with zero metric calls (criterion 2). Evaluation records never
alter original forecasts (criteria 15 and 18), and Phase 12 consumes
these records and recomputes nothing.

## 2. Populations

Pre-registered before any metric existed (`docs/STATISTICAL-ASSUMPTIONS.md`
§13(b); pinned by criteria 3–4):

- Over the frozen fixtures: **60 targets = 3 structural refusals + 27
  flagged + 30 clean = 57 predictions** (criterion 3). The 3 refusals
  are excluded from every metric of every kind and appear only in
  accounting; **no metric container exists for n = 60**.
- **PRIMARY = the 30 clean predictions** (no insufficient-data /
  insufficient-teams flag, `CONVERGED`).
- **SECONDARY = all 57 predictions** (27 flagged + 30 clean, flags
  riding).
- Inside each population the model and the baseline carry the **same
  population and the same `n`** (criterion 4); the 3 `MISSING_NO_HISTORY`
  baselines are exactly the 3 refusal targets — a three-way set equality
  with the prediction-less matches (criterion 4); no baseline value is
  `None` on any scored target.
- **`n` is stated on every number**; a bare number is illegal.

## 3. Formulas

Pinned (`docs/STATISTICAL-ASSUMPTIONS.md` §13(a); ADV-2):

- **Log loss** = `−ln(p_realized)`, natural log, **no ε-clamp of any
  spelling** — a source scan of `app/evaluation/**` asserts zero
  occurrences of `epsilon`, `clamp`, `clip`, `sys.float_info`, or a
  `1e-` literal (criterion 6). A zero probability on the realized
  outcome is a hard `ValueError` refusal, never a finite clamped score
  and never smoothed (criterion 6). The smallest probability component
  over every scored pair is **0.12816022966803042** (criterion 6), so
  the refusal case does not occur on this population.
- **Brier** = the **full 3-outcome sum** `(p_H − o_H)² + (p_D − o_D)² +
  (p_A − o_A)²` — no halving — range `[0, 2]`; the uniform reference
  `(⅓, ⅓, ⅓)` against any outcome is `2/3` (criterion 7).
- **RPS** = **½-scaled, 3-category ordinal** over the fixed ordering
  H < D < A, range `[0, 1]`; the uniform reference vs H is `5/18`, and
  the hand value 0.11125 is asserted **≠** the unscaled cumulative sum
  0.2225 — the ½ is pinned (criterion 8). The fine-grained scoreline
  variant is rejected (`docs/STATISTICAL-ASSUMPTIONS.md` §13(a)) and
  structurally absent: `app/evaluation/**` imports nothing from
  `app.models` or `app.simulation` (criterion 8 AST pin).
- **Hand-computed single-prediction values** (IX-11's "hand-computed
  values"; criterion 5), each compared within 1e-12 against independent
  in-test arithmetic: `log_loss((0.55, 0.25, 0.20), H) = −ln(0.55)`;
  `brier((0.2, 0.3, 0.5), A) = 0.38`; `rps((0.4, 0.35, 0.25), D) =
  0.11125` (from the cumulative forms `F_p = (0.4, 0.75)`, `F_o = (0, 1)`).

Baselines are scored with the **same formulas on the same population**
(§13(d)); each model mean is cross-checked in-test as the arithmetic
mean of its contributions subset (criterion 9).

## 4. Results, side by side — absolute values with `n` and caveats

Model and baseline absolute mean values over the identical population,
identical formulas, identical `n` (golden pins: criterion 9,
`GOLDEN_METRICS`, "golden: first green run; re-derive, never widen"):

**Primary population (n = 30 clean predictions):**

| Metric   | Model                | Baseline             |
|----------|----------------------|----------------------|
| Mean log loss | 1.0893088945036264 | 1.0756660244986818 |
| Mean Brier   | 0.657717020755589  | 0.6513262608006456 |
| Mean RPS     | 0.23748019128548054 | 0.2350484286002546 |

**Secondary population (n = 57 predictions, flags riding):**

| Metric   | Model                | Baseline             |
|----------|----------------------|----------------------|
| Mean log loss | 1.172910978563622 | 1.10026212693129 |
| Mean Brier   | 0.7110877726071556 | 0.6659747894436246 |
| Mean RPS     | 0.2599049808350038 | 0.2385794979516648 |

**Calibration** (criterion 10; §13(c)): exactly 5 equal-width bins with
edges `(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)`, last bin inclusive at 1.0;
(p, realized-indicator) pairs pooled across the three outcomes (3 pairs
per scored match); each bin reports `(n, mean p, realized frequency)`;
empty bins report `n = 0` with `None` fields — never a fabricated number
and never merged.

Primary (n = 30; 90 pooled pairs; dominant-bin share
**0.8111111111111111** = 73/90):

| Bin         | n  | mean p             | realized frequency |
|-------------|----|--------------------|--------------------|
| [0.0, 0.2)  | 2  | 0.1922355541990161 | 0.5                |
| [0.2, 0.4)  | 73 | 0.3068857322030056 | 0.3013698630136986 |
| [0.4, 0.6)  | 15 | 0.48085802938550376 | 0.4666666666666667 |
| [0.6, 0.8)  | 0  | None               | None               |
| [0.8, 1.0]  | 0  | None               | None               |

Secondary (n = 57; 171 pooled pairs; dominant-bin share
**0.8011695906432749** = 137/171):

| Bin         | n   | mean p             | realized frequency |
|-------------|-----|--------------------|--------------------|
| [0.0, 0.2)  | 6   | 0.16572509513274955 | 0.6666666666666666 |
| [0.2, 0.4)  | 137 | 0.30851337436509413 | 0.32116788321167883 |
| [0.4, 0.6)  | 27  | 0.4853685454016753  | 0.3333333333333333 |
| [0.6, 0.8)  | 1   | 0.6343664153403693  | 0.0                |
| [0.8, 1.0]  | 0   | None               | None               |

At these `n` the concentration of pairs in one bin is loud: calibration
here is **descriptive-with-loud-caveat** (§13(c)); **larger-n
calibration is registered as Phase 13** (ADV-11).

**Draw aggregate** (§2f; criterion 11): `realized draw rate − mean
predicted draw probability`, per population — primary
**−0.03437540133650058** (7 draws counted among the 30), secondary
**−0.025271786352718206** (14 draws among the 57, hand-counted in-test).
The negative sign is the realized rate sitting below the mean predicted
draw probability on both populations — calibration arithmetic against
realized results, never a model-vs-baseline comparison (§13(c)).

**Overdispersion diagnostic** (§2b; criterion 12): over the secondary
population's realized team-goals — **n = 114 = 2 × 57, sum 149**, the
mean is **149/114** (`round(mean, 3) == 1.307`) and the **population
variance (ddof = 0) rounds to 0.967**; the sample variance (ddof = 1)
value 0.9757 is asserted **≠** the shipped value — the denominator is
pinned. Reported as numbers only: descriptive, no test, no verdict.

Caveats riding every number above: a small synthetic sample (the
fictional "Obsidian Coast League" fixtures); the 27 flagged predictions
ride the secondary population; baselines are per-fixture chronological
windows whose early `n` is tiny (Phase 9 item 3).

## 5. What these numbers are not

The four pinned honest-negation sentences (verbatim; §13(e), Phase 11
brief decision 8) — the only sanctioned phrasings around quality
vocabulary in this document:

- **(S1)** "These numbers are descriptive evaluations of a small
  synthetic sample; they are not evidence of predictive skill."
- **(S2)** "Model and baseline values appear side by side as absolute
  quantities; no difference, ratio, ranking, or verdict between them is
  computed or claimed."
- **(S3)** "Calibration bins are counts and frequencies only; no
  reliability or goodness-of-fit claim follows from them."
- **(S4)** "No forecast is called validated, accurate, or beating
  anything."

No decision threshold, label, grade, or recommendation exists anywhere
in the evaluation surface (§13(e)); `docs/STATISTICAL-ASSUMPTIONS.md`
§13(d) bans deltas, ratios, percentages, and verdicts between model and
baseline **forever** — still banned after this phase scored.

## 6. Provenance

- **Run digest** (the ADV-6 digest gate, asserted before any metric
  computes — criterion 1):
  `150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f`
  (the §12 golden of record — re-derive on change, never widen, never
  delete).
- **Fixture identity** — the evaluation record's `fixture_file_sha256s`
  is the real sha256 of each fixture file's bytes in the pinned name
  order (criterion 16):
  - `fixtures/openfootball/valid/season-1.json` =
    `f779fc0a952e00ecd904c8019b288c43326635cb5c5a698f2f74870b11d57e39`
  - `fixtures/openfootball/valid/season-2.json` =
    `5a9da621c678933b0a5f0320a79c8c245783b34bbaf59a73e0fd7d7609d916a9`

  (recorded in `docs/DATA-SOURCES.md`; re-verified byte-for-byte with
  `sha256sum` at the Phase 11 docs step).
- **Evaluation version**: `EVALUATION_VERSION = 1` (criterion 16),
  echoed into every record row.
- **Idempotent evaluation records** — the §11(d) table `evaluations`
  (`SCHEMA_VERSION = 2`, this phase's sanctioned bump; criterion 17):
  columns exactly `(evaluation_version, run_digest,
  fixture_file_sha256s, payload, content_hash)`, **no timestamp
  column**, write-once immutability triggers mirroring the forecasts
  table; `insert_evaluation_record` is idempotent on identical content
  (`False`, zero INSERTs) and raises `EvaluationConflictError` on same
  identity with differing content — never an overwrite (criterion 16).
  Across evaluate + insert the forecasts table dump and `verify_all`
  are byte-identical and exactly one evaluation row is added (criteria
  15 and 18); evaluation writes never alter original forecasts
  (HANDOFF:126–127).
- **Leakage/integrity proofs**: altering a scored match's outcome
  changes that contribution and the aggregates (positive control,
  criterion 19); altering a refusal target's score changes nothing —
  identical result and identical `content_hash` (criterion 20);
  appended extra matches leave the evaluation byte-identical (criterion
  21, the poison-registry entry).
- **Criterion map**: criteria 1–16 and 18–22 are the 21 tests in
  `tests/test_evaluation.py` (779 lines, C8-accepted declared
  deviation); criterion 17 is
  `test_evaluations_table_write_once_no_timestamp_schema_v2` in
  `tests/test_storage.py` (amendment A9); criterion 23 is the
  suite-level recorded-execution gate (suite 178 passed;
  `bash scripts/health-check.sh` completes `OK:` inside the untouched
  800 s valve).
- **Consumption (IX-12)**: Phase 12 consumes this phase's records and
  recomputes nothing; every evaluation entry point stays re-runnable
  and read-only.
