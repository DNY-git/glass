# MASTER PLAN — SPORTS LOOKING GLASS

Status: proposed (2026-10-13, glass-architect). Binding documents: the
constitution (`.opencode/rule/lookingglass-constitution.md`) and
`docs/HANDOFF.md`. This plan answers the eight planning questions of
HANDOFF Part X, in order, and restates the postponements. It reconstructs
principles, not old filenames.

Ground rules that every phase inherits: one phase at a time; blocks of
three with the developer as acceptance gate; lightweight (venv, pytest,
stdlib first); every dependency justified, default none; pure statistical
code imports no storage, HTTP, or I/O; tests prove phases with real
commands and real output; commits only via the checkpoint protocol on
green tests; never push without explicit developer authorization.

## 1. What is the minimum viable first phase?

Phase 1 "Foundation" (ROADMAP Phase 1, HANDOFF Part IX item 1). Nothing
else can be verified until a green, offline, deterministic local test loop
exists, so the loop itself is the minimum viable increment:

- an isolated `.venv/` at the repo root with pip and pytest inside;
- `pytest.ini` wiring plus a root `conftest.py` so `app/` is importable
  under both `pytest` and `python -m pytest`;
- the `app/` package (engine root) and a `tests/` directory;
- `scripts/health-check.sh` executing fully end to end (its pre-build
  early exit is passed), including its double-run determinism comparison;
- acceptance criteria written 1:1 with tests, suite green with zero
  skips/xfails, review pass, checkpoint commit, monitor verdict OK.

Phase 1 creates no subpackages, no data, no calculations, and no API.
Deeper structure is instantiated by the phases that need it — empty
scaffolding is overengineering.

## 2. What is the directory structure?

Target structure, mapped to the ten pipeline stages of HANDOFF Part IV.
Subpackages are created when their phase begins, never speculatively:

    lookingglass/
    ├── .opencode/               # agent suite (exists from bootstrap)
    ├── .gitignore               # .venv/, __pycache__/, .pytest_cache/, data/
    ├── pytest.ini               # Phase 1
    ├── conftest.py              # Phase 1: root on sys.path for bare `pytest`
    ├── app/                     # the engine; ten stages as separated modules
    │   ├── __init__.py          # Phase 1
    │   ├── domain/              # domain models (entities/value objects)
    │   ├── ingestion/           # stage 1 DATA: loaders, provenance
    │   ├── validation/          # stage 2 VALIDATION: defect reports
    │   ├── storage/             # cross-cutting: local persistence — DEFERRED (Phase 2 brief decision 1)
    │   ├── state/               # stage 3 PRE-MATCH STATE: as-of-kickoff views
    │   ├── features/            # stage 4: chronological features, versioned specs
    │   ├── models/              # stage 5: pure statistics (stdlib only)
    │   ├── forecasts/           # stage 6: immutable distributions, cutoff inside
    │   ├── scenarios/           # stage 7: bounded hypothetical multipliers
    │   ├── decisions/           # stage 8: comparison, disagreement reported
    │   ├── backtesting/         # stage 9: chronological harness, baselines
    │   ├── evaluation/          # stage 9: log loss, Brier, RPS, calibration
    │   ├── improvement/         # stage 10: tuning loop (protected from itself)
    │   └── api/                 # thin FastAPI routers only (Phase 5+)
    ├── tests/                   # 1:1 with acceptance criteria per phase
    ├── fixtures/                # small, checked-in sample data (EXISTS, Phase 2)
    ├── data/                    # git-ignored working data (deferred with app/storage)
    ├── scripts/health-check.sh  # continuous baseline (exists)
    └── docs/                    # HANDOFF, ROADMAP, PLAN, PROGRESS-LOG,
                                 # HEALTH-LOG, briefs/, DATA-SOURCES.md,
                                 # KNOWN-LIMITATIONS.md

Stage-to-module rule: each of the ten pipeline stages lives in its own
module; pure statistical code (`app/models`, evaluation math) imports only
stdlib and domain types — never storage, HTTP, or filesystem. API routers
contain no logic. `app/storage` (sqlite via stdlib, default backend) was
confirmed **deferred** by the Phase 2 brief (design decision 1): no
durable state was needed that phase, and the proposal returns in the
first brief that needs durable state (immutable snapshots, Phase 5+);
consequently `data/` is also not created yet. `app/domain` is
cross-cutting and exists since Phase 2 (with `app/ingestion`,
`app/validation`, and `fixtures/`).

## 3. Which dependencies are genuinely necessary?

| Dependency | Phase | Justification |
|------------|-------|---------------|
| pytest    | 1     | The constitution mandates a pytest test loop; `scripts/health-check.sh` invokes `python -m pytest`. Installed into `.venv`; exact version recorded in PROGRESS-LOG. |
| pip (in venv) | 1 | The health script runs `python -m pip check`; the venv must be self-describing. |
| uv (machine tool, bootstrap only) | 1 | One-time installer used only to bootstrap pip+pytest because this machine's system Python lacks ensurepip/pip (developer approval required — see open questions of the Phase 1 brief). Nothing in the engine imports it; it is not a product dependency. |
| FastAPI + uvicorn | 5 | Edge only, when an API phase arrives; routers stay thin over domain logic. Justified again at that brief. |
| sqlite3, json, csv, math, statistics, argparse, subprocess | stdlib | Storage, ingestion, Poisson math, and tooling with zero installs. |

Explicit non-dependencies by default: no numpy, pandas, scipy, scikit-learn
or any numeric stack (stdlib `math` suffices for the Poisson engine; revisit
only with written justification and developer approval); no Docker, no
services, no cloud, no CI-platform requirements; no linters/formatters in
the phase loop unless the developer asks; no AI/LLM/generative packages,
ever, at runtime.

## 4. What works offline?

Everything after one-time bootstrap. The engine, every phase's fixtures,
every test, and the health script run entirely from the local machine:

- ingestion reads local files only (`data/` git-ignored, small samples
  checked in under `fixtures/`); nothing downloads at runtime; provenance
  and license recorded in `docs/DATA-SOURCES.md` (Phase 2);
- tests are hermetic: fixed inputs, explicit seeds, temp dirs for outputs,
  no network, no wall clock;
- the health script (`scripts/health-check.sh`) is fully local;
- the single network touchpoint is the Phase 1 one-time installation of
  pip+pytest into the venv (subject to developer approval); afterwards
  `pip check` and the whole loop work with the network down.

Enforcement: runtime code review plus planned operational checks
(Phase 10), including a stdlib socket-blocking guard in tests if needed.

## 5. How is determinism tested?

Definition (constitution): identical inputs + model version + seed +
config produce identical output. All four are recorded with each forecast.

Mechanisms: all randomness flows through explicitly seeded RNGs — the
caller passes an int seed and the RNG instance is constructed fresh
inside the call (deliberate tightening of "RNG objects passed by the
caller", Phase 4 brief decision 1: a caller-passed RNG object would make
outputs depend on hidden caller-side stream position, the implicit state
the constitution bans) — no global `random`, no unseeded or implicit state;
no wall-clock time and no environment lookups inside calculations; no
unsorted iteration inside calculations.

Testing, in layers:
1. Golden-value tests: fixed inputs + fixed seed assert exact expected
   numbers (e.g., exact Poisson probabilities to full precision).
2. In-process double-run tests: the same calculation with the same seed is
   run twice in one process and asserted bit-identical.
3. Suite level, every phase: the health script runs the suite twice and
   asserts the summaries match (timings stripped); the monitor repeats
   this at every sweep.
4. End to end (Phase 12): the full offline pipeline is run twice with the
   same seed and the outputs are diffed for byte identity.
5. Static guards (temporal-integrity phase, reusable later): stdlib AST
   scans assert that pure calculation modules contain no `datetime.now`,
   `time.time`, `os.environ`, or unseeded `random` usage.

## 6. How is future-data leakage prevented as the system grows?

Five cumulative layers:

1. Cutoff inside the calculation. History cutoffs are enforced inside the
   forecast builder and feature calculations themselves — a caller that
   forgets to filter must still be unable to leak. Call-site filtering
   alone is never sufficient.
2. Immutable artifacts. Pre-match snapshots and forecasts are frozen at
   creation; evaluation, tuning, and correction append new records and
   never rewrite originals.
3. Chronological harness. Backtesting (Phase 9) walks strictly forward in
   time; evaluation (Phase 11) is strictly chronological and idempotent.
4. Adversarial tests. The dedicated Temporal Integrity phase (Phase 8)
   injects poisoned future matches and asserts that outputs for earlier
   matches are byte-identical, audits snapshot immutability, and verifies
   cutoff at source. The same "poisoned future changes nothing" test
   becomes a standing regression whenever a new history-consuming
   calculation is added.
5. Import hygiene. AST-based tests assert that pure modules (statistical
   models, evaluation math) import no storage, HTTP, or filesystem code,
   so the leakage surface stays structurally small.

## 7. How is each phase independently verifiable?

- Every phase brief contains numbered, testable acceptance criteria
  mapping 1:1 to tests, an out-of-scope list, and risks; criteria never
  reference an unbuilt phase.
- Tests prove phases: real commands, real pasted output; zero skips,
  zero xfails; never weaken, delete, skip, or xfail a test to pass.
- The loop: brief → build → test (1:1) → independent review (suite run
  twice by the reviewer) → docs → checkpoint commit on green tests →
  monitor sweep (OK/WARN/ERROR; ERROR is a hard stop).
- The health script is a continuous baseline: at every phase end
  `bash scripts/health-check.sh` runs to completion with a clean pip
  check, zero skips/xfails, and a matching double-run determinism line.
- Durable state records everything: PROGRESS-LOG (built, real test
  counts, commands, checkpoint hashes), HEALTH-LOG (sweep verdicts),
  ROADMAP (statuses), per-phase briefs under `docs/briefs/`.
- Independence: every phase is verifiable offline from local fixtures on
  this machine; developer acceptance occurs once per block (1-3, 4-6,
  7-9, 10-12, 13), never mid-block, and Phase N+1 never starts before
  Phase N is reviewed, committed, and monitor-swept.

## 8. What is postponed until the statistical engine works?

- Frontend of any kind (constitution: no frontend before the core
  pipeline is reliable).
- A generic multi-domain framework (constitution: not before football
  works end to end).
- Any domain other than football.
- Any API surface beyond the minimum thin FastAPI routers (they wait for
  the core statistics and simulation phases).
- Advanced model families beyond the baseline Poisson engine — nothing
  beyond the documented baseline until the baseline has been backtested
  and evaluated chronologically.
- Performance tuning, parallelism, and generalization work.

## Postponements (restated per HANDOFF Part X)

Postponed by consensus until football works end to end: the frontend, the
multi-domain framework, and any domain other than football.

Never (absolute prohibitions, not postponements): betting functionality
of any kind; paid APIs or keys in the core workflow; required cloud or
required Docker; any AI/LLM/generative dependency in the runtime or in any
computed number; fabricating or silently imputing missing data; claiming
the lost implementation was recovered.
