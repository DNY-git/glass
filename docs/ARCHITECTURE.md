# ARCHITECTURE — SPORTS LOOKING GLASS

Status as of 2026-10-16 (Phase 1): **only `app/__init__.py` exists.**
Everything in the module map and directory tree below except that one file
is the **target/planned structure**, declared in `docs/PLAN.md` (status:
proposed) and `docs/HANDOFF.md` Part IV. Modules are instantiated by the
phase that needs them, never speculatively. Nothing in a planned block
below should be read as existing code.

## The pipeline (ten stages, mandatory module separation)

From HANDOFF Part IV. Each stage is a distinct module; pure statistical
code imports no storage, no HTTP, no I/O.

| # | Stage | Responsibility | Planned module |
|---|-------|----------------|----------------|
| 1 | DATA | Fixtures, loaders, provenance. | `app/ingestion/` |
| 2 | VALIDATION | Schema and integrity checks; defects reported, not guessed around. | `app/validation/` |
| 3 | PRE-MATCH STATE | As-of-kickoff view of the world. | `app/state/` |
| 4 | FEATURE EXTRACTION | Chronological features computed from history with explicit cutoffs. | `app/features/` |
| 5 | STATISTICAL MODELS | Pure computation: Poisson goal models, strength parameters, calibration. | `app/models/` |
| 6 | FORECAST DISTRIBUTIONS | Full scoreline/outcome distributions, frozen at creation (immutable). | `app/forecasts/` |
| 7 | SCENARIO EXPLORATION | Bounded, labeled-hypothetical multipliers. | `app/scenarios/` |
| 8 | DECISION ANALYSIS | Comparison of model outputs and their disagreement, honestly presented. | `app/decisions/` |
| 9 | OUTCOME EVALUATION | Log loss, Brier, RPS against realized results, strictly chronological. | `app/evaluation/` (harness: `app/backtesting/`) |
| 10 | MODEL IMPROVEMENT | A tuning loop protected from evaluating itself on its own tuning data. | `app/improvement/` |

Cross-cutting planned modules: `app/domain/` (entities/value objects) and
`app/storage/` (local persistence, idempotency; sqlite via stdlib, default
backend — to be confirmed in the Phase 2 brief). `app/api/` holds thin
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

## Target directory structure (PLANNED — from docs/PLAN.md §2)

    lookingglass/
    ├── .opencode/               # agent suite (exists from bootstrap)
    ├── .gitignore               # .venv/, __pycache__/, .pytest_cache/, data/
    ├── pytest.ini               # EXISTS (Phase 1)
    ├── conftest.py              # EXISTS (Phase 1)
    ├── app/                     # the engine; ten stages as separated modules
    │   ├── __init__.py          # EXISTS (Phase 1) — the ONLY app/ file today
    │   ├── domain/              # PLANNED — domain models
    │   ├── ingestion/           # PLANNED — stage 1 DATA: loaders, provenance
    │   ├── validation/          # PLANNED — stage 2: defect reports
    │   ├── storage/             # PLANNED — cross-cutting: local persistence
    │   ├── state/               # PLANNED — stage 3: as-of-kickoff views
    │   ├── features/            # PLANNED — stage 4: versioned feature specs
    │   ├── models/              # PLANNED — stage 5: pure statistics (stdlib)
    │   ├── forecasts/           # PLANNED — stage 6: immutable, cutoff inside
    │   ├── scenarios/           # PLANNED — stage 7: bounded multipliers
    │   ├── decisions/           # PLANNED — stage 8: disagreement reported
    │   ├── backtesting/         # PLANNED — stage 9: chronological harness
    │   ├── evaluation/          # PLANNED — stage 9: log loss, Brier, RPS
    │   ├── improvement/         # PLANNED — stage 10: protected tuning loop
    │   └── api/                 # PLANNED (Phase 5+): thin FastAPI routers
    ├── tests/                   # EXISTS (Phase 1): 1:1 with criteria
    ├── fixtures/                # PLANNED (from Phase 2): small sample data
    ├── data/                    # PLANNED (from Phase 2): git-ignored working data
    ├── scripts/health-check.sh  # EXISTS (bootstrap + Phase 1 recursion guard)
    ├── README.md                # EXISTS
    └── docs/                    # EXISTS: HANDOFF, ROADMAP, PLAN, PROGRESS-LOG,
                                 # HEALTH-LOG, ARCHITECTURE, KNOWN-LIMITATIONS,
                                 # briefs/; DATA-SOURCES.md arrives Phase 2

## Instantiation status (2026-10-16)

| Item | Status |
|------|--------|
| `app/__init__.py` | Exists — docstring only, no logic |
| `pytest.ini`, root `conftest.py`, `tests/`, `scripts/health-check.sh` | Exists (Phase 1) |
| `.venv/` (Python 3.12.3, pip 26.2.1, pytest 9.1.1) | Exists, git-ignored |
| All `app/` subpackages, `fixtures/`, `data/`, API, statistics | **Do not exist — planned, phase by phase** |

There is no data model, no statistics, no forecast, and no API in the
repository today. `docs/DATA-SOURCES.md`, `docs/STATISTICAL-ASSUMPTIONS.md`,
and `docs/EVALUATION.md` do not exist yet because there is no data or
statistics to document; they arrive with the phases that introduce them.
