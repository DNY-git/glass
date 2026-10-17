# ARCHITECTURE — SPORTS LOOKING GLASS

Status as of 2026-10-16 (Phase 3): **pipeline stages 1–2 and 5 and the
domain layer exist** — `app/domain/` (immutable models, match
collection, canonical state), `app/ingestion/` (stage 1 DATA),
`app/validation/` (stage 2 VALIDATION), `app/models/` (stage 5
STATISTICAL MODELS: Poisson MLE fitter, fitted-parameter records,
analytic scoreline/outcome evaluation), plus checked-in synthetic
fixtures under `fixtures/`. Everything else in the module map and
directory tree below is the **target/planned structure**, declared in
`docs/PLAN.md` (status: proposed) and `docs/HANDOFF.md` Part IV.
Modules are instantiated by the phase that needs them, never
speculatively. Nothing in a planned block below should be read as
existing code.

## The pipeline (ten stages, mandatory module separation)

From HANDOFF Part IV. Each stage is a distinct module; pure statistical
code imports no storage, no HTTP, no I/O.

| # | Stage | Responsibility | Module |
|---|-------|----------------|----------------|
| 1 | DATA | Fixtures, loaders, provenance. | `app/ingestion/` (exists since Phase 2) |
| 2 | VALIDATION | Schema and integrity checks; defects reported, not guessed around. | `app/validation/` (exists since Phase 2) |
| 3 | PRE-MATCH STATE | As-of-kickoff view of the world. | `app/state/` |
| 4 | FEATURE EXTRACTION | Chronological features computed from history with explicit cutoffs. | `app/features/` |
| 5 | STATISTICAL MODELS | Pure computation: Poisson goal models, strength parameters, calibration. | `app/models/` (exists since Phase 3) |
| 6 | FORECAST DISTRIBUTIONS | Full scoreline/outcome distributions, frozen at creation (immutable). | `app/forecasts/` |
| 7 | SCENARIO EXPLORATION | Bounded, labeled-hypothetical multipliers. | `app/scenarios/` |
| 8 | DECISION ANALYSIS | Comparison of model outputs and their disagreement, honestly presented. | `app/decisions/` |
| 9 | OUTCOME EVALUATION | Log loss, Brier, RPS against realized results, strictly chronological. | `app/evaluation/` (harness: `app/backtesting/`) |
| 10 | MODEL IMPROVEMENT | A tuning loop protected from evaluating itself on its own tuning data. | `app/improvement/` |

Cross-cutting modules: `app/domain/` **exists since Phase 2**
(entities/value objects) and `app/storage/` (local persistence,
idempotency; sqlite via stdlib, default backend) was **confirmed
deferred** by the Phase 2 brief (design decision 1) — no durable state
is needed yet, and the proposal returns in the first brief that needs
durable state (immutable snapshots, Phase 5+). `app/api/` holds thin
FastAPI routers only, from Phase 5; routers contain no logic.

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
  passed by the caller; no wall-clock time, environment lookups, or
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
    │   ├── storage/             # DEFERRED (Phase 2 brief decision 1) — sqlite returns Phase 5+
    │   ├── state/               # PLANNED — stage 3: as-of-kickoff views
    │   ├── features/            # PLANNED — stage 4: versioned feature specs
    │   ├── models/              # EXISTS (Phase 3) — stage 5: pure statistics (stdlib)
    │   ├── forecasts/           # PLANNED — stage 6: immutable, cutoff inside
    │   ├── scenarios/           # PLANNED — stage 7: bounded multipliers
    │   ├── decisions/           # PLANNED — stage 8: disagreement reported
    │   ├── backtesting/         # PLANNED — stage 9: chronological harness
    │   ├── evaluation/          # PLANNED — stage 9: log loss, Brier, RPS
    │   ├── improvement/         # PLANNED — stage 10: protected tuning loop
    │   └── api/                 # PLANNED (Phase 5+): thin FastAPI routers
    ├── tests/                   # EXISTS (Phase 3): 37 tests, 1:1 with criteria
    ├── fixtures/                # EXISTS (Phase 2): synthetic OpenFootball-shaped JSON
    ├── data/                    # NOT CREATED — git-ignored working data, deferred with app/storage
    ├── scripts/health-check.sh  # EXISTS (bootstrap + Phase 1 recursion guard)
    ├── README.md                # EXISTS
    └── docs/                    # EXISTS: HANDOFF, ROADMAP, PLAN, PROGRESS-LOG,
                                 # HEALTH-LOG, ARCHITECTURE, KNOWN-LIMITATIONS,
                                 # DATA-SOURCES, STATISTICAL-ASSUMPTIONS, briefs/

## Instantiation status (2026-10-16, Phase 3)

| Item | Status |
|------|--------|
| `app/__init__.py` | Exists — docstring only, no logic |
| `app/domain/` (models.py, collection.py) | Exists (Phase 2) — frozen dataclasses, deduplicating `MatchCollection`, `canonical_state()`, availability counts |
| `app/ingestion/` (openfootball.py) | Exists (Phase 2) — local JSON loader, provenance (repo-relative path + sha256), idempotent import |
| `app/validation/` (report.py, checks.py) | Exists (Phase 2) — `Defect`/`DefectReport`, pure checks; defects reported, never repaired |
| `app/models/` (constants.py, params.py, poisson.py, scoreline.py) | Exists (Phase 3) — `"poisson-mle-v1"`: unpenalized Poisson MLE by Newton-Raphson with analytic derivatives and a hand-rolled dense solve; frozen `FittedParams`/`FitConfig` with required `convergence_status` (CONVERGED / MAX_ITERATIONS / SINGULAR_SYSTEM / NO_DATA), sha256 input digest, pooling record; analytic scoreline matrices (reported dropped mass) and outcome probabilities exact under truncation; cutoff enforced **inside** `fit` (`date < as_of`); no randomness, no wall clock, no module-level fitted state |
| `fixtures/openfootball/` (3 synthetic JSON files) | Exists (Phase 2) — 60 valid matches + 12-record defect sample, fictional teams, `"synthetic": true` marker |
| `pytest.ini`, root `conftest.py`, `tests/` (9 modules, 37 tests), `scripts/health-check.sh` | Exists (Phases 1–3) |
| `.venv/` (Python 3.12.3, pip 26.2.1, pytest 9.1.1) | Exists, git-ignored |
| `app/storage/`, `data/` | **Deferred** (Phase 2 brief design decision 1) — sqlite returns in the first brief needing durable state (Phase 5+) |
| Remaining `app/` subpackages (state, features, forecasts, scenarios, decisions, backtesting, evaluation, improvement), API | **Do not exist — planned, phase by phase** |

There is data (synthetic fixtures) and a fitted statistical model, but
no forecast, no scenarios, and no API in the repository today.
`docs/DATA-SOURCES.md` exists (formats, fixture provenance, licenses);
`docs/STATISTICAL-ASSUMPTIONS.md` exists (the model's assumptions and
their weaknesses — authored before the Phase 3 build per quant ruling,
updated to the implemented reality); `docs/EVALUATION.md` does not
exist yet because there is no evaluation to document; it arrives with
the phase that introduces it.
