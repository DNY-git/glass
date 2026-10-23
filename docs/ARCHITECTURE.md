# ARCHITECTURE — SPORTS LOOKING GLASS

Status as of 2026-10-23 (Phases 9–11): **pipeline stages 1–2, 4–8 and the
cross-cutting layers exist** — `app/domain/` (immutable models,
match collection, canonical state), `app/ingestion/` (stage 1 DATA),
`app/validation/` (stage 2 VALIDATION), `app/features/` (stage 4
FEATURE EXTRACTION: the pure, cutoff-inside feature engine —
`compute_features(matches, fixture)` and the frozen 22-field
`FeatureVector` with `FEATURE_VERSION = "features-chronological-v1"`;
**instantiated but currently unconsumed** — no file outside the package
imports it (AST-enforced both directions), and the natural future
consumer is the `Forecast` record (stage 6), which arrives only via its
own future brief with its own version/identity implications — the
Phase 6 brief's F4 foreclosed in-phase wiring), `app/models/`
(stage 5
STATISTICAL MODELS: Poisson MLE fitter, fitted-parameter records,
analytic scoreline/outcome evaluation), `app/forecasts/` (stage 6
FORECAST DISTRIBUTIONS: the pure, deterministic, frozen forecast
builder and record), `app/scenarios/` (stage 7
SCENARIO EXPLORATION: bounded, labeled-hypothetical multipliers),
`app/decisions/` (stage 8 DECISION ANALYSIS: the pure, deterministic
`build_decision_report(forecast, *, scenarios=())` and the frozen
28-field `DecisionReport` with `REPORT_VERSION =
"decision-report-v1"` — **in-process views over frozen forecasts,
currently unconsumed by anything, never stored** — no file outside the
package imports it, AST-enforced both directions),
`app/backtesting/` (the stage-9 BACKTESTING harness — the pure,
deterministic walk-forward machinery: `run_walk_forward` and the frozen
`WalkForwardRun`/`BaselineRecord`/`RefusalRecord`/`RunManifest` records
with `BACKTEST_VERSION = "backtest-walkforward-v1"` — **machinery only,
still no metrics**; pure stdlib + `app.domain` + `app.forecasts`, no
storage import, currently consumed by nothing under `app/`),
`app/simulation/` (the cross-cutting Monte Carlo module — **not** one
of the ten pipeline stages), plus the cross-cutting durable store
`app/storage/` (sqlite write-once snapshots via stdlib) and the
read-only serving surface `app/api/` (stdlib `http.server`, bound to
`127.0.0.1`), plus checked-in synthetic fixtures under `fixtures/`.
Phase 8 (Temporal integrity, HANDOFF Part IX item 8) added **no
module**: its temporal-integrity defenses exist as **tests +
documentation only** (`tests/test_temporal_integrity.py`,
`tests/test_vocab_guards.py`, plus one declared line in
`tests/test_phase7_separation.py`) — zero production code under `app/`
at that phase. Phase 9 (Backtesting, HANDOFF Part IX item 9) added
`app/backtesting/` (pure, five modules + `__init__.py` — six files,
535 lines) and nothing
else under `app/`; `app/evaluation/` was **PLANNED** at that phase —
the one-line prediction-to-outcome join deliberately did not exist
yet. Phase 10 (Operational reliability, HANDOFF Part IX item 10)
added **no module**: tests + documentation only —
`tests/test_operational.py` (NEW, 8 tests), the architect-sanctioned
AMENDMENT-A1 rework of `scripts/health-check.sh`, and the
AMENDMENT-A2 two-line valve edit in `tests/test_health_script.py` —
**zero production code under `app/`** at that phase; the health script
now makes **three inner pytest executions with capture-once
derivation** (five until Phase 10 — every check preserved, only
redundant executions eliminated) and its compile checks cover
`app` + `tests`. Phase 11 (Forecast evaluation, HANDOFF Part IX item
11) added `app/evaluation/` (pure, four modules, 639 lines) — the
**evidence gate**: the digest-gated scoring layer (log loss, Brier,
½-scaled ordinal RPS, the 5-bin calibration tables, the draw
aggregate, the ddof=0 overdispersion diagnostic, and the idempotent,
content-hashed, no-clock evaluation record with `EVALUATION_VERSION =
1`) — **the first consumer of `app/backtesting/`**, first evaluated
population 30 primary / 57 secondary — plus the §11(d) sanctioned
schema bump (**`SCHEMA_VERSION` 1 → 2**: the write-once `evaluations`
table + the write-only `insert_evaluation_record`; storage's read
paths untouched; no committed DB). `app/improvement/` (stage 10)
remains **PLANNED** — Phase 10 was HANDOFF Part IX item 10, not
pipeline stage 10 — and Phase 12 (Integration and verification,
HANDOFF Part IX item 12) remains **PLANNED**: it CONSUMES Phase 11's
records and recomputes nothing.
`app/state/` (stage 3 PRE-MATCH STATE)
remains **planned**: stage 4
legitimately precedes stage 3 per roadmap order, features compute
directly from match history plus domain types, and no dependency on
stage 3 is invented (Phase 6 brief F4). Everything else in the module
map and directory tree below
is the **target/planned structure**, declared in `docs/PLAN.md`
(status: proposed) and `docs/HANDOFF.md` Part IV. Modules are
instantiated by the phase that needs them, never speculatively. Nothing
in a planned block below should be read as existing code.

## The pipeline (ten stages, mandatory module separation)

From HANDOFF Part IV. Each stage is a distinct module; pure statistical
code imports no storage, no HTTP, no I/O.

| # | Stage | Responsibility | Module |
|---|-------|----------------|----------------|
| 1 | DATA | Fixtures, loaders, provenance. | `app/ingestion/` (exists since Phase 2) |
| 2 | VALIDATION | Schema and integrity checks; defects reported, not guessed around. | `app/validation/` (exists since Phase 2) |
| 3 | PRE-MATCH STATE | As-of-kickoff view of the world. | `app/state/` |
| 4 | FEATURE EXTRACTION | Chronological features computed from history with explicit cutoffs. | `app/features/` (exists since Phase 6) |
| 5 | STATISTICAL MODELS | Pure computation: Poisson goal models, strength parameters, calibration. | `app/models/` (exists since Phase 3) |
| 6 | FORECAST DISTRIBUTIONS | Full scoreline/outcome distributions, frozen at creation (immutable). | `app/forecasts/` (exists since Phase 5) |
| 7 | SCENARIO EXPLORATION | Bounded, labeled-hypothetical multipliers. | `app/scenarios/` (exists since Phase 4) |
| 8 | DECISION ANALYSIS | Comparison of model outputs and their disagreement, honestly presented. | `app/decisions/` (exists since Phase 7) |
| 9 | OUTCOME EVALUATION | Log loss, Brier, RPS against realized results, strictly chronological. | `app/backtesting/` (harness: **EXISTS since Phase 9** — machinery, still no metrics) + `app/evaluation/` (scoring: **EXISTS since Phase 11** — the evidence gate) |
| 10 | MODEL IMPROVEMENT | A tuning loop protected from evaluating itself on its own tuning data. | `app/improvement/` |

Cross-cutting modules: `app/domain/` **exists since Phase 2**
(entities/value objects); `app/simulation/` **exists since Phase 4** —
the seeded Monte Carlo layer over one fixture's scoreline matrix, and
the **only module in the codebase permitted to import `random`**
(AST-enforced with probes). It is deliberately **not one of the ten
pipeline stages**: it consumes exactly one frozen `ScorelineMatrix`
per call, never replaces the analytic `outcome_probs` as the reported
single-match probability, and exists for Phase 12 replay machinery and
future aggregate quantities with no closed form (see
`docs/STATISTICAL-ASSUMPTIONS.md` §7). And `app/storage/` (local
persistence, idempotency; sqlite via stdlib, default backend) —
deferred by the Phase 2 brief (design decision 1) — was **confirmed
instantiated at Phase 5** (brief design decision 1): the immutable
forecast snapshots are exactly the durable state the deferral waited
for. `app/api/` is the read-only serving surface over stored
snapshots — **stdlib `http.server.ThreadingHTTPServer` bound to
`127.0.0.1`** (zero third-party dependencies; the Phase 5 brief's D1
option a, developer answer Q1 = a), two `GET` routes, no generation
verb, routers containing no logic.

## Rules of separation (binding)

- Pure statistical code (`app/models`, evaluation math) imports only the
  standard library and domain types — never storage, HTTP, or the
  filesystem.
- Domain models, ingestion, storage, features, statistical models,
  forecasts, scenarios, decision reports, backtesting, evaluation, and API
  routing are distinct modules.
- History cutoffs are enforced inside calculations (e.g. inside the
  forecast builder), never only at call sites.
- Forecasts and pre-match snapshots are immutable once created.
- Determinism: identical inputs + model version + seed + config produce
  identical output; all randomness flows through explicitly seeded RNGs
  (the caller passes an int seed; the RNG instance is constructed fresh
  inside the call — PLAN §5 as clarified by the Phase 4 brief decision
  1); no wall-clock time, environment lookups, or
  unsorted iteration inside calculations.

## Target directory structure (what exists now vs PLANNED — from docs/PLAN.md §2)

    lookingglass/
    ├── .opencode/               # agent suite (exists from bootstrap)
    ├── .gitignore               # .venv/, __pycache__/, .pytest_cache/, data/
    ├── pytest.ini               # EXISTS (Phase 1)
    ├── conftest.py              # EXISTS (Phase 1)
    ├── app/                     # the engine; ten stages as separated modules
    │   ├── __init__.py          # EXISTS (Phase 1) — engine root package
    │   ├── domain/              # EXISTS (Phase 2) — models, collection, canonical state
    │   ├── ingestion/           # EXISTS (Phase 2) — stage 1 DATA: loader, provenance
    │   ├── validation/          # EXISTS (Phase 2) — stage 2: defect reports
    │   ├── storage/             # EXISTS (Phase 5) — sqlite write-once snapshots (stdlib); triggers enforce immutability
    │   ├── state/               # PLANNED — stage 3: as-of-kickoff views
    │   ├── features/            # EXISTS (Phase 6) — stage 4: compute_features, frozen FeatureVector (pure; cutoff inside; currently unconsumed)
    │   ├── models/              # EXISTS (Phase 3) — stage 5: pure statistics (stdlib)
    │   ├── forecasts/           # EXISTS (Phase 5) — stage 6: frozen forecasts, cutoff inside (pure)
    │   ├── scenarios/           # EXISTS (Phase 4) — stage 7: bounded, labeled-hypothetical multipliers
    │   ├── simulation/          # EXISTS (Phase 4) — CROSS-CUTTING seeded Monte Carlo (not a stage; the only random importer)
    │   ├── decisions/           # EXISTS (Phase 7) — stage 8: frozen decision reports (pure; in-process views over forecasts; unconsumed; never stored)
    │   ├── backtesting/         # EXISTS (Phase 9) — stage 9 harness: walk-forward machinery, baselines (pure; no metrics; no storage import; consumed by app/evaluation since Phase 11)
    │   ├── evaluation/          # EXISTS (Phase 11) — stage 9: log loss, Brier, RPS, calibration (pure; digest-gated; idempotent evaluation records)
    │   ├── improvement/         # PLANNED — stage 10: protected tuning loop
    │   └── api/                 # EXISTS (Phase 5) — read-only stdlib http.server on 127.0.0.1; no logic, no generation
    ├── tests/                   # EXISTS (Phase 11): 178 tests, 1:1 with criteria
    ├── fixtures/                # EXISTS (Phase 2): synthetic OpenFootball-shaped JSON
    ├── data/                    # NOT CREATED — git-ignored working data; the DB path is caller-passed, no data/ dir in-repo
    ├── scripts/health-check.sh  # EXISTS (bootstrap + Phase 1 recursion guard + Phase 10 A1 rework: 3 inner runs, capture-once derivation; compile covers app + tests)
    ├── README.md                # EXISTS
    └── docs/                    # EXISTS: HANDOFF, ROADMAP, PLAN, PROGRESS-LOG,
                                 # HEALTH-LOG, ARCHITECTURE, KNOWN-LIMITATIONS,
                                 # DATA-SOURCES, STATISTICAL-ASSUMPTIONS, briefs/

## Instantiation status (2026-10-23, Phase 11)

| Item | Status |
|------|--------|
| `app/__init__.py` | Exists — docstring only, no logic |
| `app/domain/` (models.py, collection.py) | Exists (Phase 2) — frozen dataclasses, deduplicating `MatchCollection`, `canonical_state()`, availability counts |
| `app/ingestion/` (openfootball.py) | Exists (Phase 2) — local JSON loader, provenance (repo-relative path + sha256), idempotent import |
| `app/validation/` (report.py, checks.py) | Exists (Phase 2) — `Defect`/`DefectReport`, pure checks; defects reported, never repaired |
| `app/features/` (constants.py, canonicalization.py, record.py, compute.py) | Exists (Phase 6) — stage 4: `compute_features(matches, fixture)` with the cutoff **IS `fixture.date`, computed inside** (no time-like parameter exists to forget; strict `date <` over every consumed match; `ValueError` if the fixture's natural key appears in the history; `TypeError` on a non-`Fixture` target; canonical-sort window selection, same-date ties resolved there); frozen **22-field** `FeatureVector` (`content_hash` computed at construction, `init=False`) with `FEATURE_VERSION = "features-chronological-v1"`; named policy constants (`FORM_WINDOW = 5`, `FORM_WINDOW_POLICY = "MISSING_UNTIL_FULL_WINDOW"`, `REST_DAYS_POLICY = "WITHIN_SEASON"`, `XG_FORM_POLICY = "MEAN_OVER_AVAILABLE_WITH_N"`); `input_digest` parity with `FittedParams` pinned by cross-check test; own canonicalization spec of record (no import across the stage boundary); pure — stdlib + `app.domain`/`app.features` only, in `PURE_PACKAGES` (AST-enforced); **descriptive history only, zero predictive claim, consumed by nothing — no file outside the package imports it** (AST-enforced both directions); no storage/persistence — vectors exist in memory only |
| `app/models/` (constants.py, params.py, poisson.py, scoreline.py) | Exists (Phase 3) — `"poisson-mle-v1"`: unpenalized Poisson MLE by Newton-Raphson with analytic derivatives and a hand-rolled dense solve; frozen `FittedParams`/`FitConfig` with required `convergence_status` (CONVERGED / MAX_ITERATIONS / SINGULAR_SYSTEM / NO_DATA), sha256 input digest, pooling record; analytic scoreline matrices (reported dropped mass) and outcome probabilities exact under truncation; cutoff enforced **inside** `fit` (`date < as_of`); no randomness, no wall clock, no module-level fitted state. Phase 4 refactor: shared `lambda_pair`/`build_scoreline_matrix` constructors extracted (the ONE cell-math path — `scoreline_log_probs` and every scenario matrix both delegate to them; Phase 3 goldens byte-identical) |
| `app/forecasts/` (constants.py, canonicalization.py, record.py, builder.py) | Exists (Phase 5) — stage 6: `build_forecast(matches, fixture)` with the cutoff **IS `fixture.date`, computed inside** (no `as_of`/`cutoff`/time parameter exists to forget; refuses a fixture present in its own history with `ValueError`; `TypeError` on a non-`Fixture` target); frozen 17-field `Forecast` (`content_hash` computed at construction; no `seed` field exists anywhere); `FORECAST_VERSION = "forecast-poisson-mle-v1"` part of the hashed content; the written canonicalization spec of record (`canonicalization.py`); `ForecastIntegrityError`/`ForecastConflictError`; pure — stdlib + `app.domain`/`app.models` only (AST-enforced); in-sample estimates, never evidence of accuracy |
| `app/storage/` (forecasts_db.py) | Exists (Phase 5) — durable **write-once** sqlite store, stdlib `sqlite3` only (AMENDMENT A2's sanctioned package): two pinned tables — the 21-column forecasts table (identity UNIQUE constraint; **no timestamp column**) and, since Phase 11, the 5-column `evaluations` table `(evaluation_version, run_digest, fixture_file_sha256s, payload, content_hash)` (**no timestamp column**; the §11(d) sanctioned bump — **`SCHEMA_VERSION = 2`**, was 1) — both with `BEFORE UPDATE`/`BEFORE DELETE` triggers `RAISE(ABORT …)` inside the file (raw-write refusal surfaces as `sqlite3.IntegrityError` — criterion-8 erratum); `insert_forecast` (one INSERT in a `BEGIN IMMEDIATE` transaction; identical identity + identical hash = idempotent no-op, different hash = `ForecastConflictError`, never an overwrite) and, since Phase 11, the **write-only** `insert_evaluation_record` (same idempotence/conflict semantics; `EvaluationConflictError`; `__all__` = 12 names; **no read API for evaluations** — tests read rows with raw sqlite3); read path opens `PRAGMA query_only = 1` and recomputes the content hash on **every** returned row; `verify_all`, `backup_forecasts` via `Connection.backup`; caller-passed DB path, never an env lookup; **read paths untouched by Phase 11** (`get_forecast`'s signature and `fetchone` line pinned unchanged; no fetch-by-content-hash API) |
| `app/api/` (serialize.py, server.py) | Exists (Phase 5) — **read-only** serving surface over STORED snapshots: stdlib `ThreadingHTTPServer` bound to `127.0.0.1` (never `0.0.0.0`; zero third-party dependencies — D1 option a), two `GET` routes (`/health`, `/forecasts/{competition}/{season}/{date}/{home}/{away}`); non-GET → 405, unknown fixture → 404 `{"error":"unknown_fixture"}` (store-then-serve — `build_forecast` appears nowhere under `app/api`, AST-enforced), malformed input → 400 (strict manual percent-decoder, AMENDMENT A5 — no urllib); byte-deterministic JSON bodies (sorted keys, fixed separators, full-precision floats, no timestamp in any body); top-level honesty flags + provenance echo + fixed `disclaimer`; no-auth posture holds only as localhost + read-only + no secrets |
| `app/scenarios/` (spec.py, apply.py) | Exists (Phase 4) — stage 7: frozen `TransformOp`/`Transform`/`Scenario`, `build_scenario` (bounds `MULTIPLIER_MIN = 0.5`/`MULTIPLIER_MAX = 2.0` inclusive, `ValueError` — **never clamping**, canonical transform ordering, duplicate/unknown-team refusal, required non-empty label), `scenario_matrix` (strict applicability; parameter-scale transforms `α′ = m·α` etc.; matrix echoes the baseline's flags); one scenario per call — **no averaging or ensembling anywhere**; no randomness, no cell math, no `FittedParams` construction (AST-enforced) |
| `app/decisions/` (constants.py, canonicalization.py, record.py, builder.py) | Exists (Phase 7) — stage 8: `build_decision_report(forecast, *, scenarios=())` — **no `matches`, no time-like parameter exists to forget** (the forecast's cutoff was enforced once, inside `build_forecast`); frozen **28-field** `DecisionReport` plus nested frozen `ScenarioComparison` (8 fields) and `ScenarioSpread` (4 fields), `content_hash` computed at construction (`init=False`) under the package's own canonicalization spec of record; `REPORT_VERSION = "decision-report-v1"` + the fixed `DISCLAIMER` as the constants module's **exactly two** names (no threshold, no knob, no decision rule exists — A6 position, pinned by test); provenance chains through echoed `forecast_version` + `forecast_content_hash`; scenario refusals by frozen value equality (mismatched baseline, duplicate labels → `ValueError`), entries canonically ordered by label; **min/max/spread only — a mean is an invented ensemble and exists nowhere**; analytic `outcome_probs` only, never MC (`app.simulation` never imported); pure — stdlib + `app.domain`/`app.models`/`app.forecasts`/`app.scenarios` only, in `PURE_PACKAGES` (AST-enforced both directions); **in-process views over frozen forecasts, consumed by nothing, stored nowhere** — no sqlite table, no schema bump, no API route; evaluated n = 0 (zero scoring ships) |
| `app/backtesting/` (constants.py, canonicalization.py, record.py, baselines.py, harness.py + `__init__.py`; 535 lines) | Exists (Phase 9) — IX-9 **machinery only, still no metrics**: single public `matches`-parameter function exactly — `run_walk_forward(matches, *, fixture_file_sha256s=(), interpreter_version=None)` (no spec/config/variant/seed knob — the single-model-spec surface is pinned closed) — canonical-chronological targets (`canonical_sort_key`), per-target `Fixture` re-derived as natural key + **kickoff echo** (never the score), pool = matches minus the target, `ValueError` → first-class `RefusalRecord` (`REFUSED_NO_PRE_CUTOFF_HISTORY` — **60 targets = 3 refusals + 27 flagged + 30 clean = 57 predictions**, auditable, never skipped/uniformed); underscore-private chronological baselines in `baselines.py` (the ONLY realized-score consumer: strictly `date < fixture.date`, uniform weighting, MISSING `n = 0` at the first date's three fixtures, **never stored**, in-process re-derivable); frozen `WalkForwardRun`/`BaselineRecord`/`RefusalRecord`/`RunManifest` with construction-time content hashes; version-local golden run digest (re-derive, never widen); double-run + store-level idempotence via the CALLER's `insert_forecast` into a caller-passed DB; own canonicalization spec of record; pure — stdlib + `app.domain`/`app.forecasts` only, **no `app.storage` import**, in `PURE_PACKAGES` (AST-enforced); **no prediction-to-outcome join, no metric of any kind computed here — the scoring layer is `app/evaluation/`**; **consumed by `app/evaluation/` since Phase 11** (the harness's first consumer) |
| `app/evaluation/` (metrics.py, calibration.py, evaluate.py + `__init__.py`; 639 lines) | Exists (Phase 11) — IX-11 **the evidence gate**: single public entry `evaluate_predictions(predictions, baselines, matches, *, run_digest, expected_run_digest)` — the digest gate runs BEFORE any metric computes (golden run digest asserted; tampered digest refuses with zero metric calls), the one-line natural-key join refuses 0 and >1 matches, the flag predicate is deliberately duplicated from the byte-pinned harness (drift guarded by the 27/30 count pins), populations (primary 30 clean / secondary 57; the 3 refusals accounting-only; 60 = 3 + 27 + 30), per-match contributions; `log_loss`/`brier`/`rps` (natural-log log loss with **no ε-clamp of any spelling** — hard refusal on zero probability on the realized outcome; full-sum Brier; ½-scaled ordinal RPS — the scoreline variant structurally impossible: no `app.models`/`app.simulation` import, AST-pinned); 5-bin pooled calibration tables, draw aggregate, and the ddof=0 overdispersion diagnostic — **descriptive only**; model/baseline **absolute** side-by-side with `n` (a pinned banned-identifier scan enforces no delta/verdict surface); frozen `EvaluationRecord` (`EVALUATION_VERSION = 1`, canonical-JSON payload, sha256 content hash, **no clock anywhere**) inserted write-once by `app.storage.insert_evaluation_record` — records never alter forecasts; pure — stdlib `{dataclasses, hashlib, json, math, typing}` + `app.domain`/`app.forecasts`/`app.backtesting` only, in `PURE_PACKAGES` (AST-enforced); imports no storage/API (one-way: storage imports the record types); IX-12 consumes its records and recomputes nothing |
| `app/simulation/` (constants.py, simulate.py) | Exists (Phase 4) — **cross-cutting Monte Carlo module, not one of the ten pipeline stages**: `simulate(fitted, home, away, *, seed, n_sims=10_000, scenario=None)` with required keyword-only int `seed` (fresh `random.Random(seed)` per call, `random()`-only draws, categorical sampling over the truncated renormalized matrix), frozen `SimulationResult` (raw counts, exact `analytic_outcome`, `mc_stderr` = simulation noise only, dropped mass, flags riding through); `SIM_VERSION = "sim-categorical-v1"`; **the only module permitted to import `random`** (AST-enforced with probes); refuses a scenario whose baseline ≠ the given fitted object (value equality) |
| `fixtures/openfootball/` (3 synthetic JSON files) | Exists (Phase 2) — 60 valid matches + 12-record defect sample, fictional teams, `"synthetic": true` marker |
| `pytest.ini`, root `conftest.py`, `tests/` (27 modules, 178 tests), `scripts/health-check.sh` | Exists (Phases 1–11; health-check.sh reworked at Phase 10 by AMENDMENT A1 — three inner pytest executions with capture-once derivation, five until Phase 10, every check preserved; compile checks extended `app` → `app tests`; `tests/test_evaluation.py` added at Phase 11) |
| `.venv/` (Python 3.12.3, pip 26.2.1, pytest 9.1.1) | Exists, git-ignored |
| `data/` | **Not created** — git-ignored working data; the sqlite DB path is caller-passed (storage tests use `tmp_path` exclusively), no `data/` directory is created in-repo (Phase 5 brief design decision 1) |
| Remaining `app/` subpackages (state, improvement) | **Do not exist — planned, phase by phase** (stage 4 `features` removed from this list at Phase 6 — it exists; stage 8 `decisions` removed at Phase 7 — it exists; the stage-9 backtesting harness removed at Phase 9 — `app/backtesting/` exists; stage-9 `evaluation` removed at Phase 11 — `app/evaluation/` exists) |

There is data (synthetic fixtures), a fitted statistical model, a
chronological feature layer (stage 4 — descriptive, currently
unconsumed), a scenarios/simulation layer, a decision-report layer
(stage 8 — deterministic in-process views over frozen forecasts,
currently unconsumed and never stored), a **backtesting layer
(stage-9 harness — pure walk-forward machinery, baselines, refusal
accounting — consumed by the evaluation layer since Phase 11; the
harness itself still computes no metrics),** an **evaluation layer
(stage 9 — `app/evaluation/`'s digest-gated log loss, Brier, RPS,
calibration, and idempotent no-clock evaluation records — first scored
population 30/57; every number pinned in tests),** **durable immutable forecast
snapshots (the system's first durable artifacts), and a read-only
localhost API
over them** in the repository today.
`docs/DATA-SOURCES.md` exists (formats, fixture provenance, licenses);
`docs/STATISTICAL-ASSUMPTIONS.md` exists (the model's assumptions and
their weaknesses — authored before the Phase 3 build per quant ruling,
updated to the implemented reality; §7 covers simulation and
scenarios, authored before the Phase 4 build per quant ruling and
likewise updated; §8 covers forecasts, snapshot immutability, and
serving honesty, authored before the Phase 5 build per quant mandate
and likewise updated to implemented reality; §9 covers feature
extraction, authored before the Phase 6 build per quant ruling F6 and
likewise updated to implemented reality; §10 covers decision analysis
— report structure, comparison without collapse, the no-scoring
boundary — authored before the Phase 7 build per quant ruling A1 and
likewise updated to implemented reality; §11 covers the temporal-
integrity pre-registrations binding Phases 9 and 11, authored before
the Phase 8 build and likewise updated; §12 covers the backtesting
baseline definition, scored-population accounting, and standing bans —
authored before the Phase 9 build per quant ruling A6 and likewise
updated to implemented reality; §13 covers the evaluation
pre-registrations — metric formulas, populations, calibration bins,
side-by-side legality — authored before the Phase 11 build per
quant rulings ADV-1–ADV-14 and likewise updated to implemented
reality); `docs/EVALUATION.md` exists (created at Phase 11: the
pinned evaluation record — purpose and anti-inflation rule,
populations, formulas, side-by-side absolute results with `n` and
caveats, the honest negations, and provenance; every number a pinned
test literal).
