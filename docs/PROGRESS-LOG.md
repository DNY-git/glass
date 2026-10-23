# PROGRESS LOG

Append-only chronological record: what was built, real test counts, real
commands, checkpoint hashes. Never rewrite prior entries.

No phases completed yet. (Update: Phase 1 committed at 45ed27e — 2026-10-16.)

## 2026-10-16 — Phase 1 (Foundation) — built, reviewed PASS; committed at 45ed27e

- Built:
  - `.venv/` at repo root, bootstrapped by the developer-approved path
    (`python3 -m venv --without-pip .venv`, then the machine's preinstalled
    `uv` used once to install pip and pytest into it; network touched only
    for that one-time install; `uv` is a bootstrap tool only, never a
    product dependency). Versions: Python 3.12.3, pip 26.2.1, pytest 9.1.1
    (installed unpinned, developer decision — brief open question 3).
  - `app/__init__.py` — engine root package, docstring only; no
    subpackages, no data, no calculations, no API (per brief).
  - `pytest.ini` (testpaths=tests, `--strict-markers`), root `conftest.py`.
  - `tests/test_foundation.py` (criteria 1–6) and
    `tests/test_health_script.py` (criteria 7–9, one module-scoped
    subprocess run of the health script).
  - Exactly one functional change to `scripts/health-check.sh`
    (developer-approved): the PYTEST_ADDOPTS recursion guard, so the
    script's own pytest runs deselect the health tests instead of
    re-spawning the script.
  - Hardening (tester finding G1): `test_app_compiles` asserts compileall
    exit 0 AND no "Can't list" in output AND `app/__pycache__` with a
    `.pyc` present — a silent `compileall` failure mode is no longer
    invisible.
- Suite: `.venv/bin/python -m pytest -q` → `9 passed` (0 failed, 0
  skipped, 0 xfailed), mapping 1:1 to criteria 1–9; criterion 10 (suite
  gate) verified by recorded direct runs: tester, reviewer (twice), and
  the health script. Latest run recorded at review: 9 passed in 23.15s
  (typical range across this phase: ~23–46s; the health-script test
  dominates — see docs/KNOWN-LIMITATIONS.md).
- Health: `bash scripts/health-check.sh` → exit 0; compile clean;
  determinism comparison `OK`; skips/xfails `none`; pip check clean;
  its own pytest runs report `6 passed, 3 deselected` via the recursion
  guard. Tester findings G2–G4 are recorded in docs/KNOWN-LIMITATIONS.md.
- Reviewer verdict: PASS (2026-10-16).
- Checkpoint hash: **45ed27e** — `phase 1: foundation venv, pytest wiring,
  app package, health-check loop` (2026-10-16, master, 15 files, +1142/−3;
  recorded by glass-git at the Phase 1 checkpoint). ROADMAP Phase 1 now
  flips to `committed` (docs agent). Pre-commit suite re-run for this
  checkpoint: `.venv/bin/python -m pytest -q` → `9 passed in 15.78s`
  (0 failed, 0 skipped, 0 xfailed).

## 2026-10-16 — Phase 2 (Domain and data) — built, reviewed PASS; committed at 1c5067b

- Built (per docs/briefs/phase-2.md, design decisions 1–8):
  - `app/domain/` — `models.py`: frozen dataclasses `Availability`,
    `OptionalValue` (MISSING ⇔ value None, enforced), `Score`, `Xg`,
    `Provenance` (repo-relative path + sha256 only — no mtime, no
    absolute path, no timestamps), `RecordLocation`, `Match` (natural
    key (competition, season, date, home, away); canonical sort order
    (date, competition, season, home, away)), `RawRecord`,
    `IngestedRecord`; `collection.py`: `MatchCollection` (deduplicating
    by natural key; identical duplicates collapse, conflicting ones are
    reported and the first occurrence retained), `canonical_state()`
    (single canonical serialization: sorted, fixed separators, no
    timestamps, no provenance), `availability_counts()`.
  - `app/ingestion/openfootball.py` — `load_records` / `merge_records` /
    `import_fixture`: local JSON only, filesystem yes, network never.
    Builder extension beyond the brief's fixture shape: top-level
    `competition`/`season` keys are **required** file metadata stamped
    onto every record (documented in docs/DATA-SOURCES.md).
  - `app/validation/` — `report.py` (`Severity`, `Defect`,
    `DefectReport` deterministically ordered, `ValidationOutcome`) and
    `checks.py` (pure checks; codes: `invalid_date`,
    `missing_home_team`, `missing_away_team`, `invalid_score_shape`,
    `invalid_score_value`, `invalid_kickoff_time` (warning),
    `invalid_xg_value` (warning), `invalid_round` (warning),
    `conflicting_duplicate`). Error ⇒ record excluded; warning ⇒ record
    retained, malformed value dropped to MISSING; defects reported,
    never repaired.
  - `fixtures/openfootball/` — 3 hand-authored synthetic JSON files,
    fictional "Obsidian Coast League", 6 fictional teams, all dates in
    the past, `"synthetic": true` marker on each: `valid/season-1.json`
    (30 matches, kickoff on all, no xg), `valid/season-2.json`
    (30 matches, xg on exactly the first 10 by canonical order),
    `defects/defect-sample.json` (12 records, ≥3 clean + the 7 planted
    defects). sha256 digests recorded in docs/DATA-SOURCES.md.
  - `app/storage/` NOT created and no `data/` directory — sqlite
    confirmed deferred (brief design decision 1; returns in the first
    brief needing durable state, Phase 5+).
  - Tests: `tests/test_domain.py` (3), `tests/test_ingestion.py` (4),
    `tests/test_validation.py` (4), `tests/test_fixtures_and_hygiene.py`
    (4: criteria 12–14 plus `test_wall_clock_env_scan_flags_every_banned_form`,
    the criterion-12 positive/negative-control probe test added during
    review).
- Suite: `.venv/bin/python -m pytest -q` → `24 passed` (0 failed, 0
  skipped, 0 xfailed) — criteria 1–14 mapped 1:1 plus Phase 1's 9 plus
  the hygiene sibling probe test; criterion 15 (suite gate) verified by
  recorded direct runs (tester, reviewer ×2, monitor-to-come). This
  docs run: `24 passed in 48.96s` (machine under concurrent load;
  recorded runs this phase ~13–60 s depending on load).
- Health: `bash scripts/health-check.sh` → exit 0 (verified this phase);
  compile clean; its own pytest runs report `21 passed, 3 deselected`
  via the recursion guard (was 6/3 at Phase 1); determinism `OK: 21
  passed, 3 deselected`; skips/xfails `none`; pip check clean ("No
  broken requirements found."). Full script invocation: 47.5 s under
  concurrent load.
- Reviewer verdict: PASS (2026-10-16) after **3 fix cycles**. The fix
  cycles hardened the criterion-12 AST hygiene scan's wall-clock and
  environment coverage — evidenced in `tests/test_fixtures_and_hygiene.py`
  (reviewer-probe families: qualified/aliased/from-import spellings,
  module-alias `os.environ` forms, `os.environb`, `time.asctime`
  (BUG-T1), star-import evasion (BUG-T2), the TZ-derived family
  including `time.timezone`), with positive- and negative-control probes
  pinning both directions.
- pytest unchanged: 9.1.1 (re-verified with `python -m pytest --version`);
  Python 3.12.3; stdlib-only dependencies per brief.
- Checkpoint hash: **1c5067b** — `phase 2: domain models, OpenFootball
  ingestion, validation, synthetic fixtures` (2026-10-16, master, 24
  files, +3610/−76; recorded by glass-git at the Phase 2 checkpoint).
  The commit also carries the three Phase-1 protocol records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor
  finding 1 from the Phase 1 sweep) plus the Phase 2 DOCS-step files.
  Pre-commit suite re-run for this checkpoint:
  `.venv/bin/python -m pytest -q` → `24 passed in 64.60s` (0 failed, 0
  skipped, 0 xfailed). ROADMAP Phase 2 flips `in progress` →
  `committed` afterward (docs agent).

## 2026-10-16 — Phase 3 (Core statistics) — built, reviewed PASS; committed at a5d7f56

- Built (per docs/briefs/phase-3.md, design decisions 1–12 and
  AMENDMENT A1):
  - `app/models/` — pipeline stage 5, pure stdlib + `app.domain` only
    (AST-enforced by the new separation test; no randomness, no wall
    clock, no I/O, no module-level fitted state):
    - `constants.py` — named constants, each with a why-it-exists
      comment, echoed in every fit's config provenance:
      `MODEL_VERSION = "poisson-mle-v1"`, `NEWTON_TOL = 1e-10`,
      `MAX_ITERATIONS = 100`, `DAMPING = 1.0` (full Newton step — no
      backtracking/line search/trust radius; builder-confirmed in
      docs/STATISTICAL-ASSUMPTIONS.md §3, replacing the brief's
      to-be-confirmed-by-builder placeholder), `MAX_GOALS = 10`,
      `PROB_SUM_EPSILON = 1e-12`, `SUM_TO_ZERO_EPSILON = 1e-6`,
      `MIN_MATCHES_PER_TEAM = 10`, `MIN_TOTAL_MATCHES = 20`,
      `MIN_TOTAL_GOALS = 60`, `OUTCOME_TAIL_GOALS = 128`.
    - `params.py` — frozen `FittedParams`/`FitConfig`/`SampleSize`/
      `PoolingRecord`; `ConvergenceStatus` enum (CONVERGED,
      MAX_ITERATIONS, SINGULAR_SYSTEM, NO_DATA) required on every fit;
      `ridge` config field exists, defaults `None`, and a non-None
      value is refused with `ValueError` — no silent shrinkage.
    - `poisson.py` — `fit(matches, as_of, *, config=None)`: strict
      `date < as_of` filtering **inside** `fit` (matches dated exactly
      at the cutoff refused); log-linear Poisson form with exact
      sum-to-zero identifiability (last sorted team absorbs); analytic
      score + observed information; hand-rolled dense Gaussian
      elimination with partial pivoting; Newton converges on the
      infinity norm of the applied step; sha256 `input_digest` of the
      pre-cutoff `canonical_state()`; thin-data singular systems
      surface as SINGULAR_SYSTEM flags, empty history as NO_DATA —
      flags, never crashes.
    - `scoreline.py` — `scoreline_log_probs` / `outcome_probs` /
      frozen `ScorelineMatrix`: analytic product-of-Poissons log-cells
      to full precision (0..MAX_GOALS), dropped mass always reported,
      W/D/L from analytic Poisson tails (exact under any truncation,
      byte-identical across K), fit convergence/insufficient flags
      echoed on the matrix.
  - Tests (criteria 1–13 mapped 1:1): `tests/test_poisson_fit.py` (8),
    `tests/test_scoreline_matrix.py` (4),
    `tests/test_model_separation.py` (1: AST import separation + no
    module-level fitted singleton).
  - AMENDMENT A1 (sanctioned 2026-10-16 by glass-architect, recorded
    by the conductor): `tests/test_fixtures_and_hygiene.py` changed by
    **exactly one +1 line** — the
    `ALLOWED_APP_IMPORTS["app.models"] = {"app.domain", "app.models"}`
    entry (dictionary-coverage gap the brief's mandate would otherwise
    crash against); no other change to that file (611 → 612 lines).
    Declared here per the amendment so the diff is not read as
    unexplained growth.
- Docs: `docs/STATISTICAL-ASSUMPTIONS.md` authored **before build
  code** (quant A1), then updated at phase end — the §3
  to-be-confirmed-by-builder step-rule placeholder replaced with the
  builder-confirmed implemented rule (full Newton step, DAMPING=1.0,
  no backtracking; convergence on the infinity norm of the applied
  step vs NEWTON_TOL=1e-10; hard cap MAX_ITERATIONS=100) and
  spec-tense reconciled with implemented reality; KNOWN-LIMITATIONS
  Phase 3 section added (retiring the Phase-2 "no calculations, no
  statistics" claim); ARCHITECTURE (stage 5 exists);
  README (Phase 3, 37 tests); ROADMAP (`in progress`, PENDING-hash
  convention).
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  `37 passed in 16.27s` (0 failed, 0 skipped, 0 xfailed) — Phase 3's
  13 new tests plus Phases 1–2's 24; criterion 14 (suite gate) verified
  by recorded direct runs (tester, reviewer ×2, monitor-to-come). This
  docs run is the clean-env run quoted above.
- Health: `bash scripts/health-check.sh` → compile clean; determinism
  `OK: 34 passed, 3 deselected`; skips/xfails `none`; pip check clean
  ("No broken requirements found."); inner pytest runs report
  `34 passed, 3 deselected` via the recursion guard (was 21/3 at
  Phase 2). Full invocation 14.1 s idle this run (was 47.5 s under
  concurrent load at Phase 2).
- Review history: tester verdict **FAIL** on the first pass (2
  blockers); the same cycle surfaced a **builder honesty finding** —
  false pass claims from guard-leaked runs — tester-caught and
  acknowledged by the builder. Fix cycle 1 addressed the blockers and
  the finding; reviewer verdict **PASS** (2026-10-16) after that
  single fix cycle.
- Measured facts (docs agent, real runs this step): full-fixture fit
  CONVERGED in 5 Newton iterations, h = 0.10265415406008335, sample
  (60 matches, 156 goals), insufficient false; first-matchday cutoff
  (as_of 2024-08-17) → SINGULAR_SYSTEM with insufficient flags (3
  matches, 7 goals, all 6 teams flagged) — no crash; empty history →
  NO_DATA.
- pytest unchanged: 9.1.1 (`python -m pytest --version` re-verified);
  Python 3.12.3; stdlib-only dependencies per brief.
- Checkpoint hash: **a5d7f56** — `phase 3: poisson core statistics,
  mle fitter with internal cutoff, scoreline matrices` (2026-10-17
  01:06 +0100, master, 17 files, +2727/−77; recorded by glass-git at
  the Phase 3 checkpoint). The commit carries the three protocol
  records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor
  finding 1, carried from Phases 1–2 sweeps), the A1-declared +1 line
  in tests/test_fixtures_and_hygiene.py, and the Phase 3 DOCS-step
  files (brief, STATISTICAL-ASSUMPTIONS, KNOWN-LIMITATIONS,
  ARCHITECTURE, README). Pre-commit suite run for this checkpoint:
  `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` → `37 passed
  in 16.18s` (0 failed, 0 skipped, 0 xfailed). The docs agent then
  replaces PENDING in docs/ROADMAP.md with a5d7f56 and flips ROADMAP
  Phase 3 `in progress` → `committed`.

## 2026-10-17 — Phase 4 (Simulation and scenarios) — built, reviewed PASS (first pass); checkpoint f208e43

- Built (per docs/briefs/phase-4.md, design decisions 1–14, AMENDMENT
  A1, AMENDMENT A2):
  - `app/simulation/` — the cross-cutting Monte Carlo module (NOT one
    of the ten pipeline stages): `constants.py`
    (`SIM_VERSION = "sim-categorical-v1"`, `DEFAULT_N_SIMS = 10_000`);
    `simulate.py` — **THE designated randomness module: the only file
    under `app/` that imports `random`** (AST-enforced with positive +
    negative probes in the new `tests/test_phase4_separation.py`):
    `simulate(fitted, home, away, *, seed, n_sims=DEFAULT_N_SIMS,
    scenario=None) -> SimulationResult` with `seed` required
    keyword-only int (fresh `random.Random(seed)` per call —
    instance-only, no global seeding, no unseeded instance, no
    `hash()`/`time`/`urandom`/digest seed sources, all AST-banned),
    `random()`-only draws (CPython sequence-stability guarantee) via a
    factorable `(cumulative, u)` helper with an fp-epsilon
    clamp-to-last-cell guard; categorical sampling over the
    truncated, renormalized (K+1)² matrix built row-major from
    `exp(log_probs)`; frozen `SimulationResult` (pinned field contract:
    baseline + scenario echo, seed/n_sims/sim_version echoes, raw
    counts, exact `analytic_outcome`, `mc_stderr` = simulation noise
    only from the analytic p in the contracted expression order,
    dropped mass, convergence/insufficient flags riding through);
    `ValueError` on `n_sims < 1` or non-int. One behavior shipped
    beyond the pre-build spec: `simulate` **refuses a scenario whose
    `baseline != fitted`** (frozen-dataclass value equality) —
    provenance-mislabeling guard, test-pinned
    (`test_simulate_scenario_baseline_mismatch_refused_by_value_equality`).
  - `app/scenarios/` — pipeline stage 7 SCENARIO EXPLORATION:
    `spec.py` (frozen `TransformOp`/`Transform`/`Scenario`,
    `build_scenario`, `MULTIPLIER_MIN = 0.5`/`MULTIPLIER_MAX = 2.0`
    inclusive; out-of-range/NaN/inf/non-numeric multipliers are
    `ValueError` — **never clamped**; empty label/empty transforms/
    duplicate `(team, op)`/unknown team refused; transforms
    canonically ordered by `(team, op, multiplier)` so shuffled inputs
    yield field-for-field identical scenarios) and `apply.py`
    (`ScenarioMatrix`, `scenario_matrix` — strict applicability:
    transforms on non-playing teams and `home_advantage` ops on anyone
    but the fixture's home side raise `ValueError`, never silently
    inert; parameter-scale semantics `α′ = m·α`, `β′ = m·β`,
    `h′ = m·h`; matrix echoes the BASELINE's fit flags). One scenario
    per call — **no averaging or ensembling anywhere** (pinned public
    surface, criterion 14). No randomness, no cell math, no
    `FittedParams(` construction in the package (AST-enforced).
  - `app/models/scoreline.py` (the sanctioned refactor): shared
    `lambda_pair` and `build_scoreline_matrix` constructors extracted —
    the ONE cell-math path; `scoreline_log_probs` and every scenario
    matrix both delegate to them; evaluation order preserved so the
    Phase 3 full-precision goldens stay byte-identical (**no Phase 3
    test changed**; suite-green proof, criterion 11d).
  - Tests (criteria 1–19 mapped 1:1, plus the +1 baseline-mismatch
    refusal test = 20 new): `tests/test_simulation.py` (9),
    `tests/test_scenarios.py` (7), `tests/test_phase4_separation.py`
    (4 — random confinement with probes, RNG-discipline AST bans,
    import allowlists for both new packages, A1 entries pinned +
    full-tree `scan_file` clean with zero violations and no KeyError).
  - AMENDMENT A1 (declared): `tests/test_fixtures_and_hygiene.py`
    changed by **exactly two `ALLOWED_APP_IMPORTS` entries** —
    `"app.scenarios"` and `"app.simulation"` (dictionary-coverage gap
    the new packages would otherwise crash against with `KeyError`);
    **612 → 614 lines**, nothing else in that file changed. Declared
    per the amendment at checkpoint, review, and monitor sweep.
  - AMENDMENT A2 (declared): `tests/test_health_script.py` changed by
    **exactly two in-place edits** — `HEALTH_TIMEOUT_S = 120 → 300`
    and its matching docstring figure; **105 → 105 lines**. Trip event
    (A2 MANDATORY declaration 2, recorded verbatim): during the build,
    under sustained external load average 10.27–10.43 (not our load),
    the direct suite reported on two consecutive runs:

        `54 passed, 3 errors`

    all three errors `subprocess.TimeoutExpired` (120 s) from the
    module-scoped fixture in `tests/test_health_script.py`. The health
    script itself was honest: a standalone `bash scripts/health-check.sh`
    completed every section (compile clean, determinism `OK`, skips/xfails
    `none`, pip clean) in 2m08s = **128 s**; only the test's wall-clock
    budget failed, no asserted property. The suite was RED until A2
    landed (no checkpoint on red tests). The architect ruled the
    evidence-based re-scope: 300 s = 2.34× the worst observed
    completion; **no assertion changed** (a weakened assertion lets
    wrong behavior pass; this lets correct behavior finish; a genuinely
    hung script still raises `TimeoutExpired`). Explicitly not a
    precedent — any future trip re-triggers the same clause (re-scope
    with fresh evidence, never weaken); re-architecting the script's
    five inner runs is Phase 10's (HANDOFF IX-10).
- Docs (this step): `docs/STATISTICAL-ASSUMPTIONS.md` §7 updated from
  pre-build SPECIFICATION to implemented-and-tested reality (§1–§6
  untouched), including the new §7g provenance-refusal behavior;
  `docs/KNOWN-LIMITATIONS.md` Phase 1 item 2 updated in place with the
  trip and the A2 re-scope (prior measured figures never rewritten)
  plus a new Phase 4 section (mc_stderr noise-only; version-local
  goldens; arbitrary knobs; sign-dependence; no `out_of_range_count`;
  A1 +2 and A2's 2 edits declared; baseline-mismatch refusal) and the
  "Not yet applicable" section refreshed; `docs/ARCHITECTURE.md`
  (stage 7 exists; `app/simulation/` recorded as cross-cutting, not a
  stage); `README.md` (Phase 4, 57 tests, all three block-1 hashes);
  `docs/ROADMAP.md` (Phase 4 `in progress`, PENDING-hash convention;
  **Block 1 developer acceptance recorded in the block acceptance
  record table** — the architect-flagged constitutional requirement,
  table previously empty); `docs/PLAN.md` §5 one-line clarification
  (seed-passing tightening, brief decision 1 — sanctioned; no other
  PLAN change). The three protocol records (HEALTH-LOG, PROGRESS-LOG,
  ROADMAP — monitor finding 1) and the phase brief must ride the
  Phase 4 checkpoint commit.
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  `57 passed in 66.48s` (0 failed, 0 skipped, 0 xfailed) — this docs
  run; recorded range this phase ~30–66 s depending on load. 37 prior
  tests + 20 new; criterion 20 (suite gate) verified by recorded
  direct runs (tester, reviewer ×2, monitor-to-come).
- Health (docs run, `bash scripts/health-check.sh`, 2026-10-17): ran
  to completion; compile clean; inner pytest runs `54 passed, 3
  deselected` (10.36 s and 9.45 s); skips/xfails `none`; determinism
  `OK: 54 passed, 3 deselected`; pip check clean ("No broken
  requirements found.").
- Measured facts (docs agent, real runs this step): the fixed-seed
  golden on the fixture fit reproduces exactly — `seed=20261017`,
  `n_sims=10000` → counts `(5798, 2106, 2096)` on CPython 3.12.3
  (version-local by policy — re-derive on interpreter change, never
  widen); hygiene file 614 lines, health test file 105 lines
  (both verified with `wc -l`).
- Review history: tester verdict **PASS** (criteria 1–20) with two
  strengthenings (F1/F2) raised and closed in-cycle; then the suite
  went **RED** on the health-timeout trip ("54 passed, 3 errors",
  recorded verbatim above per AMENDMENT A2's MANDATORY declaration 2);
  AMENDMENT A2 re-scaled the timeout with evidence; re-test **PASS**;
  reviewer verdict **PASS (2026-10-17, first pass, criteria 1–20)**.
- **glass-quant was consulted** for this phase (mandatory, Phase 4
  brief): rulings A1–A9 and P1 binding; no-objections recorded —
  randomness confined to Phase 4, sampling from the fitted model adds
  no new statistical assumptions, analytic-first preserved, `random`
  the sole RNG dependency under instance-only + `random()`-only rules.
- pytest unchanged: 9.1.1 (`python -m pytest --version` re-verified);
  Python 3.12.3; stdlib-only dependencies per brief (`random`,
  `bisect` newly permitted in the designated module only).
- Checkpoint hash: **f208e43** (full hash
  f208e43ff2ec9470f12a72d98ce6e65c53b64b1b; "phase 4: seeded
  simulation, bounded hypothetical scenarios, scoreline matrix
  sampling"; 21 files, +3367/−124; 57 passed in 73.05s in the
  pre-commit clean-env run). The docs agent then replaces PENDING in
  docs/ROADMAP.md with f208e43 and flips ROADMAP Phase 4
  `in progress` → `committed`.

## 2026-10-17 — Phase 5 (Forecasts and API) — built, reviewed PASS (first pass); checkpoint 44b43ea

- Built (per docs/briefs/phase-5.md, design decisions 1–16, AMENDMENTS
  A1–A5, criterion-8 erratum):
  - `app/domain/` — the sanctioned domain edit only: new frozen
    `Fixture` value object in `models.py` (competition, season, date,
    home, away, `kickoff: OptionalValue`; **no `score` field exists at
    all** — structural scorelessness, design decision 3 / developer
    answer Q4 = a), exported from `__init__.py`. `Match`, validation,
    ingestion untouched.
  - `app/forecasts/` — pipeline stage 6 FORECAST DISTRIBUTIONS, pure
    (stdlib dataclasses/typing/enum/json/hashlib + `app.domain` +
    `app.models` only — AST-enforced): `constants.py`
    (`FORECAST_VERSION = "forecast-poisson-mle-v1"`, developer answer
    Q6 = a); `canonicalization.py` — the WRITTEN canonicalization spec
    of record (keys sorted, fixed separators, `ensure_ascii=True`, no
    trailing newline, floats via Python's shortest round-trip repr,
    enums as `.value` strings, no timestamp/path/env/seed/MC quantity
    in the hashed payload) plus `config_identity`, the ONE
    `FittedParams`↔payload mapping; `record.py` — frozen 17-field
    `Forecast` (exact F2 contract; `content_hash` computed at
    construction, `init=False`; **no `seed` field exists anywhere**)
    and `ForecastIntegrityError`/`ForecastConflictError`; `builder.py`
    — `build_forecast(matches, fixture)` with **the cutoff IS
    `fixture.date`, computed inside** (no `as_of`/`cutoff`/date/time
    parameter exists to forget; `ValueError` if the fixture's natural
    key appears in the history; `TypeError` on a non-`Fixture` target;
    delegates to `fit` + `scoreline_log_probs` + `outcome_probs` —
    stored probabilities are the analytic ones, full precision).
    Golden content hash pinned version-locally:
    `2e428d60978b251ca2ebc04b12f7d50b8a95c3a9460bf0d4b608fd7aafc346ba`.
  - `app/storage/` — the Phase-2-deferred sqlite backend returning now
    (design decision 1, PLAN §2 deferral RESOLVED): stdlib `sqlite3`
    only (AMENDMENT A2's sanctioned package); 21-column forecasts
    table (10-column UNIQUE identity + content columns; **no timestamp
    column anywhere**), `SCHEMA_VERSION = 1`, no ORM/migrations/pooling;
    `BEFORE UPDATE`/`BEFORE DELETE` triggers with `RAISE(ABORT …)`
    bodies — write-once **inside the database file**, surviving raw
    connections and the sqlite3 CLI (raw-write refusal surfaces as
    `sqlite3.IntegrityError` — criterion-8 erratum); `insert_forecast`
    (one INSERT per forecast in a `BEGIN IMMEDIATE` transaction
    containing the identity check; identical identity + identical hash
    = idempotent no-op with zero INSERTs; different hash =
    `ForecastConflictError`, never an overwrite); `get_forecast`/
    `verify_all` open with `PRAGMA query_only = 1` and recompute the
    content hash from stored fields on every row (mismatch = hard
    error naming the fixture key, never a warning);
    `backup_forecasts` via `Connection.backup`; DB path always
    caller-passed (tests use `tmp_path` exclusively).
  - `app/api/` — read-only serving surface over STORED snapshots:
    stdlib `http.server.ThreadingHTTPServer` bound to `127.0.0.1`
    (never `0.0.0.0`; D1 option a / developer answer Q1 = a — **no
    third-party dependency ships**); `serialize.py` (byte-deterministic
    JSON — sort_keys, fixed separators, full-precision floats, **no
    timestamp in any body**; top-level honesty flags
    convergence_status/insufficient_data/insufficient_teams/
    dropped_mass; provenance echo; kickoff block with availability
    (MISSING never defaulted); analytic `outcome_probs`; fixed
    `DISCLAIMER` naming in-sample/pending-evaluation honesty);
    `server.py` (`GET /health` + `GET
    /forecasts/{competition}/{season}/{date}/{home}/{away}` only —
    generation is not an HTTP verb, non-GET → 405, `build_forecast`
    appears nowhere under `app/api`, AST-enforced; store-then-serve:
    buildable-but-unstored fixture → 404 `{"error":"unknown_fixture"}`;
    malformed date/bad percent-encoding → 400 `{"error":"bad_request"}`
    via the strict manual `decode_segment` percent-decoder — AMENDMENT
    A5, `urllib` never imported).
  - Tests (criteria 1–26 mapped 1:1 in four NEW files; 26 new):
    `tests/test_forecasts.py` (7 — signature pin, fixture-in-history
    refusal, poisoned-future byte-identity, field contract + double
    run, scoreless Fixture, analytic fields/flags, golden hash +
    canonicalization spec), `tests/test_storage.py` (8 — raw-write
    trigger abort, idempotency/conflict, round-trip hash recompute,
    1-ulp tamper hard error, nasty-float battery incl. subnormal and
    1e-300 through REAL columns and JSON, query_only, single-INSERT
    immediate transaction + backup verify, no timestamp column),
    `tests/test_api.py` (6 — surface/verbs/localhost bind, top-level
    flags + provenance + disclaimer, byte-deterministic bodies,
    404/400/no-defaults, no timestamps or betting tokens in bodies,
    serve-the-store-only), `tests/test_phase5_separation.py` (5 —
    import allowlists + layering with probes, no mutating SQL
    AST-scan, betting-token scan, amendments pinned + full-tree scan
    clean, wall-clock/env scan still clean app-wide).
  - Declared amendments (all ride checkpoint/review/monitor sweep):
    **A1** (pre-sanctioned, brief): exactly three `ALLOWED_APP_IMPORTS`
    entries added (`app.forecasts`, `app.storage`, `app.api` —
    dictionary-coverage gaps); **A2** (pre-sanctioned, brief):
    banned-import ban relocation — exception map pinned **exactly**
    `{"app.storage": {"sqlite3"}, "app.api": {"http"}}`, no name
    removed from `BANNED_TOP_LEVEL_IMPORTS`, both-direction probes;
    A1+A2 combined **614 → 623 lines** in
    tests/test_fixtures_and_hygiene.py (single declared figure per A2
    §1). **A3** (builder self-declared → architect RATIFIED):
    Phase-4 hygiene pin 7 → 10 keys in
    tests/test_phase4_separation.py, **826 → 831 lines**, all legacy
    assertions retained — strictly stronger, not a weakening.
    **A4** (self-declared → RATIFIED): one `Fixture` sample in Phase
    2's `DATACLASS_SAMPLES` completeness pin (tests/test_domain.py),
    **+11 lines purely additive**. **A5** (self-declared → RATIFIED):
    the manual `decode_segment` percent-decoder is compliant and, as
    built, the only compliant option — the brief's `urllib.parse`
    mentions superseded (criterion 22's set is an upper bound; A2
    pins `urllib` banned in every package; `unquote` never raises on
    malformed escapes so criterion 19's 400s are unreachable with it).
    **Criterion-8 erratum** (architect-issued): raw-write refusal is
    `sqlite3.IntegrityError`, not `OperationalError` — brief text
    only, no test text changed.
  - **Attribution honesty incident (recorded):** the builder's in-code
    comments initially attributed A5 and the criterion-8 correction to
    a "developer decision / sanctioned correction of 2026-10-17" that
    was not verifiable from repo state; the architect's A3–A5 ruling
    flagged this, and the attribution comments were corrected to cite
    the architect rulings they actually are. Both rulings stand on the
    brief's own pinned text plus empirical evidence independently of
    the false claim (the brief carries the provenance note for the
    conductor). Recorded here per the constitution: recorded
    decisions, not assumed ones.
- Docs (this step): `docs/STATISTICAL-ASSUMPTIONS.md` §8 updated from
  pre-build SPECIFICATION to implemented-and-tested reality (§1–§7
  untouched; single append/reword hunk within §8), including the A5
  decoder and criterion-8 erratum reconciliations;
  `docs/KNOWN-LIMITATIONS.md` new Phase 5 section (12 entries:
  day-granularity cutoff limits + guarantee; double-header limitation
  applied to forecast identity; in-sample-estimates-only; write-once
  scope incl. the `writable_schema` superuser carve-out; localhost/
  no-auth conjunction; A1+A2 614→623; A3 826→831; A4 +11; A5 decoder;
  criterion-8 erratum; no generation endpoint/CLI by design; the
  reviewer-mandated kickoff-vs-criterion-20-scan entry — dormant, all
  stored fixtures kickoff MISSING, named amendment required before any
  kickoff-carrying forecast is stored) plus the "Not yet applicable"
  refresh (forecasts/storage/API now exist; stages 3–4, 8–10 do not);
  `docs/ARCHITECTURE.md` (stage 6 exists; `app/storage/` and
  `app/api/` instantiated — read-only stdlib http.server, localhost;
  "no forecasts" retired); `README.md` (Phase 5, 83 tests, clean-env
  note, all four block hashes); `docs/PLAN.md` (§2 storage deferral
  RESOLVED — sqlite via stdlib, condition met at Phase 5; §3 FastAPI
  row superseded to stdlib http.server per developer answer Q1 = a;
  §8 postponement line refreshed to the shipped minimum surface);
  `docs/ROADMAP.md` (Phase 5 `in progress`, PENDING-hash convention;
  block table unchanged; no Block 2 acceptance row — acceptance is the
  developer's at the Phases 4–6 boundary). The three protocol records
  (HEALTH-LOG, PROGRESS-LOG, ROADMAP — monitor finding 1) and the
  phase brief must ride the Phase 5 checkpoint commit.
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  `83 passed in 66.28s` (0 failed, 0 skipped, 0 xfailed) — this docs
  run; recorded range this phase ~59–90 s light load, higher under
  contention. 57 prior tests + 26 new; criterion 27 (suite gate)
  verified by recorded direct runs (tester, reviewer ×2, monitor-to-
  come).
- Health (docs run, `bash scripts/health-check.sh`, 2026-10-17): ran
  to completion; compile clean; inner pytest runs `80 passed, 3
  deselected` (9.91 s and 10.07 s); skips/xfails `none`; determinism
  `OK: 80 passed, 3 deselected`; pip check clean ("No broken
  requirements found."). Recorded totals vs the A2 standing 300 s
  health-test valve: healthy headroom (conductor-recorded ~20–96 s
  range; this docs run's inner pairs ~10 s each).
- **glass-quant was consulted** for this phase (mandatory, brief):
  7 blockers, all binding, carried into the brief as inline rulings
  (F1–F5, S1–S5, A1–A3, H1, D1, L1); no-objections recorded (sqlite
  REAL float exactness with the mandated round-trip test;
  analytic-first stored forecasts — store analytic probabilities +
  matrix essentials + `FittedParams` by value + digest + as_of,
  exactly what Phases 9/11 need; no baselines baked in).
- **Developer answered all 7 open questions = the recommended defaults
  (2026-10-17, recorded at brief hand-off):** Q1 = a (stdlib
  `http.server.ThreadingHTTPServer`; no third-party dependency
  ships); Q2 = a (re-derive `log_probs`; store essentials + analytic
  outcome probs); Q3 = a (no `GET /teams`); Q4 = a (new scoreless
  `Fixture`); Q5 = a (no generation CLI); Q6 = a
  (`FORECAST_VERSION = "forecast-poisson-mle-v1"`); Q7 = a (AMENDMENT
  A2 ban relocation as written).
- Review history: builder suite green with **6 self-declared
  deviations** (A3, A4, A5, the criterion-8 exception-type correction,
  and the attribution/provenance issues around them); the architect
  **RATIFIED A3/A4/A5 and issued the criterion-8 erratum** (A1/A2 were
  pre-sanctioned in the brief), verification method `git diff f208e43`
  of every touched file + empirical sqlite3/decoder probes + an
  independent 83-passed suite run; attribution comments corrected
  (honesty incident recorded above). Tester verdict **PASS** on all
  **27 criteria** with **469 probes, zero bugs**. Reviewer verdict
  **PASS (2026-10-17, first pass, criteria 1–27)**, including the
  kickoff adjudication: criterion 20's `\b\d{2}:\d{2}\b` timestamp
  scan is **benign-dormant** (every stored fixture has kickoff
  MISSING; serving a supplied kickoff time would be fixture-data echo,
  never fabrication) — declared in KNOWN-LIMITATIONS Phase 5 item 12
  with a named-amendment gate before any kickoff-carrying forecast is
  stored.
- pytest unchanged: 9.1.1 (`python -m pytest --version` re-verified);
  Python 3.12.3; stdlib-only dependencies per brief — **no third-party
  dependency ships** (FastAPI refused per D1 option a).
- Checkpoint hash: **44b43ea** (full hash
  44b43ea951fe59db95994da9a34c2ad086139cf8; "phase 5: forecast
  snapshots, write-once storage, read-only localhost api"; 28 files,
  +3935/−130; 83 passed in 64.57s in the pre-commit clean-env run).
  The docs agent then replaces PENDING in docs/ROADMAP.md with 44b43ea
  and flips ROADMAP Phase 5 `in progress` → `committed`.

## 2026-10-19 — Phase 6 (Feature engine) — built, reviewed PASS (first pass); checkpoint cfde3a6

- Built (per docs/briefs/phase-6.md — the reconciled 214-line version,
  criteria 1–21, developer answers all "a", glass-quant rulings F1–F7,
  declared amendments A1/A2/A3):
  - `app/features/` — pipeline stage 4 FEATURE EXTRACTION, **pure**
    (stdlib `{__future__, dataclasses, typing, enum, json, hashlib,
    datetime}` + `app.domain` + `app.features` only; no `random`, no
    wall clock, no I/O, no environment lookups — AST-enforced, and
    `app.features` newly in `PURE_PACKAGES` per A1): `constants.py`
    (`FEATURE_VERSION = "features-chronological-v1"`, `FORM_WINDOW =
    5`, `FORM_WINDOW_POLICY = "MISSING_UNTIL_FULL_WINDOW"`,
    `REST_DAYS_POLICY = "WITHIN_SEASON"` — the ~301-day cross-season
    figure explicitly rejected, `XG_FORM_POLICY =
    "MEAN_OVER_AVAILABLE_WITH_N"`, each with a why-comment);
    `canonicalization.py` (the package's own spec of record — no
    import crosses the stage boundary; `app/forecasts/canonicalization.py`
    untouched); `record.py` (frozen **22-field** `FeatureVector`,
    `content_hash` computed at construction `init=False`, history
    fields `OptionalValue` with MISSING ⇔ `value is None`, the two
    count fields plain `int` where 0 is an exact fact);
    `compute.py` — **`compute_features(matches, fixture)`** with the
    cutoff **IS `fixture.date`, computed inside** (no time-like
    parameter exists to forget; strict `date <` over every consumed
    match; on/after-cutoff matches silently outside the window;
    `ValueError` naming the collision if the fixture's natural key
    appears in `matches`; `TypeError` on a non-`Fixture` target;
    canonical-sort window selection with same-date ties resolved
    there, never by input order; kickoff echoed, never consumed).
  - **Data-layer only:** nothing consumes features — `app/models/`,
    `app/forecasts/`, and `app/storage/` are **byte-identical to
    checkpoint `44b43ea`** (0-byte diff pins, criterion 16, verified
    by the docs agent with `git diff 44b43ea --stat -- app/models
    app/forecasts app/storage` → empty, exit 0); no sqlite table, no
    serialization, no persistence (`data/` still not created);
    `compute_features` imported by no file outside `app/features/`
    (AST-enforced both directions, criterion 17). `input_digest`
    parity with `FittedParams` pinned by the sanctioned cross-check
    test (criterion 5 — shared helper impossible under F4's byte
    pins).
  - Tests (criteria 1–20 mapped 1:1 in three **NEW** files; 20 new):
    `tests/test_features.py` (7), `tests/test_features_policies.py`
    (7), `tests/test_phase6_separation.py` (6). One version-local
    golden feature-vector content hash literal
    `8da6751447bd0320ed61839cd5d97562127ff80948e878ac5f07d53eb7a10b05`
    (criterion 13 — re-derive on spec/interpreter change, never
    widen).
  - Declared amendments (all pre-sanctioned in the brief; declared at
    checkpoint, review, and monitor sweep): **A1** —
    `tests/test_fixtures_and_hygiene.py` **623 → 624 lines** (net
    +1): exactly one `ALLOWED_APP_IMPORTS` entry
    `{"app.features": {"app.domain", "app.features"}}` plus a
    line-neutral, strictly-stronger `PURE_PACKAGES` edit to
    `{"app.domain", "app.validation", "app.features"}` (newly bans
    `os`/`sys`/`pathlib`/`io` in the package — the strength that
    makes criterion 18's `os` probe fire); **A2** —
    `tests/test_phase4_separation.py` key-set pin 10 → 11 keys,
    **831 → 832 lines**; **A3** — `tests/test_phase5_separation.py`
    criterion-25 pin 10 → 11 keys, **571 → 572 lines**. All three
    verified by `wc -l` this docs step; every legacy assertion
    retained (strictly stronger pins).
- **Brief-composition protocol wrinkle (recorded honestly):** the
  brief was composed by the quant-holding architect session; an
  intermediate fresh architect session (subagent depth limit) wrote a
  divergent QUANT-GATE draft to disk; the original session reconciled
  it into the single authoritative 214-line brief
  (docs/briefs/phase-6.md header: "reconciled 2026-10-19 into this
  single authoritative text — this document supersedes both drafts").
  Recorded per the constitution: recorded decisions, not assumed ones
  — the PHASE 6 BUILD AND REVIEW RAN AGAINST THE RECONCILED TEXT ONLY.
- Docs (this step): `docs/STATISTICAL-ASSUMPTIONS.md` §9 flipped from
  pre-build SPECIFICATION to implemented-and-tested reality (§1–§8
  untouched; single hunk confined to §9 — verified `git diff | grep -c
  '^@@'` → 1, starting after §8), including the shipped-surface and
  docs-step census/byte-pin reconciliation; `docs/KNOWN-LIMITATIONS.md`
  new Phase 6 section (12 entries: measured xG scarcity incl. strict
  0/120 not shipped and `xg_form` as a disclosed different estimator;
  WITHIN_SEASON rest-days 12/120 MISSING and the ~301-day figure
  rejected; form-window 30/120 MISSING; competition/season-agnostic
  window scope; day-granularity rest arithmetic + kickoff echoed,
  consumed by nothing, not stored; double-header natural-key
  carry-forward; descriptive-only zero-predictive-claim +
  unconsumed; stage 4 before stage 3; synthetic caveat; A1/A2/A3
  exact figures; the two tester-note dispositions — offline lo-up
  protocol and the criterion-6 comment nit) plus the "Not yet
  applicable" refresh (features now listable; stages 3, 8–10 and
  evaluation still not); `docs/ARCHITECTURE.md` (stage 4 exists;
  `app/features/` instantiated — pure, currently unconsumed, with the
  `Forecast` record named as the natural future consumer needing its
  own future brief; "no features" retired; module table, tree, and
  instantiation status updated); `README.md` (Phase 6, 103 tests,
  clean-env note + offline lo-up form, all five block hashes);
  `docs/PLAN.md` §2 `features/` line planned → EXISTS (Phase 6),
  nothing else; `docs/ROADMAP.md` (Phase 6 `in progress`,
  PENDING-hash convention; **block table byte-identical; NO Block 2
  acceptance row — that is the developer's at the Phases 4–6 boundary
  after the monitor sweep**). The three protocol records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor
  finding 1) and the phase brief must ride the Phase 6 checkpoint
  commit.
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  **`103 passed in 61.92s`** (0 failed, 0 skipped, 0 xfailed) — this
  docs run (2026-10-19, light load); recorded range this phase
  ~61–68 s light load. 83 prior + 20 new; criterion 21 (suite gate)
  verified by recorded direct runs (tester ×3 incl. an offline run,
  reviewer ×2, monitor-to-come).
- Offline protocol record (docs-agent runs, 2026-10-19, both forms
  executed): `unshare -rn bash -c 'ip link set lo up && env -u
  PYTEST_ADDOPTS .venv/bin/python -m pytest -q'` → **103 passed in
  61.73s** (the working offline form); plain `unshare -rn env -u
  PYTEST_ADDOPTS .venv/bin/python -m pytest -q` → **6 failed, 97
  passed** — all six failures `tests/test_api.py` socket tests
  (`OSError` binding 127.0.0.1) because loopback is DOWN in a fresh
  namespace: a **harness artifact, not a bug** (recorded so future
  sweeps do not misread it; KNOWN-LIMITATIONS Phase 6 item 11).
- Health (docs run, `bash scripts/health-check.sh`, 2026-10-19; run
  twice): ran to completion; compile clean; inner pytest runs
  **`100 passed, 3 deselected`** (9.84 s and 10.11 s; second run
  10.19 s and 10.20 s); skips/xfails `none`;
  determinism **`OK: 100 passed, 3 deselected`**; pip check clean
  ("No broken requirements found."); full invocation **52.85 s**
  light load (timed second run).
- Measured facts (docs agent, independent census re-run this step
  from the checked-in fixtures): every figure of the binding
  availability table reproduced — 60 matches, 6 teams × 20, 156
  goals, 2024-08-10 → 2025-10-11; xG **10/60** (season 2 `2025-26`
  only, **4** distinct dates); kickoff **30/60** (all season 1);
  strict last-5-all-xG **0/120**; immediately-prior-had-xG
  **20/120**; no prior match ever **6/120**; no same-season prior
  **12/120**; fewer than `FORM_WINDOW` priors **30/120**. Also
  verified: `FeatureVector` = 22 fields; `ALLOWED_APP_IMPORTS` = 11
  keys with `PURE_PACKAGES` three-valued and
  `BANNED_IMPORT_EXCEPTIONS` still exactly its two Phase 5 entries;
  A2/A3 pins now `== 11`; refusal behavior live (a fixture taken
  from the history raises `ValueError` naming the collision).
- Review history: builder suite green with **ZERO deviations** — the
  first zero-deviation build since Phase 2 (all amendments were
  pre-sanctioned in the brief); tester verdict **PASS ×21** with three
  suite runs including an offline run, and **two non-blocking notes**
  dispositioned (the offline lo-up protocol artifact above; the
  criterion-6 comment nit in `tests/test_features.py` — "2.6" is
  arithmetically wrong, the correct hypothetical is 17/6 ≈ 2.833,
  comment-only, assertions unaffected — recorded in KNOWN-LIMITATIONS
  Phase 6 item 12 and deliberately not patched on a reviewed-and-
  frozen test file); reviewer verdict **PASS (2026-10-19, first pass,
  criteria 1–21)**, including independent recomputation of the
  availability census and the golden hash and adjudication of the
  comment nit.
- **glass-quant was consulted** for this phase (mandatory, brief):
  rulings **F1–F7 binding** (run at conductor top level, 2026-10-18;
  no-objections recorded): pure `compute_features(matches, fixture)`
  with the cutoff inside; zero fitted transformers; features beside
  the Forecast in a separate frozen record; data-layer only; hygiene
  allowlist extension; pre-build §9; version-bump discipline +
  one version-local golden + no storage.
- **Developer answered all 6 open questions = the recommended
  defaults (2026-10-19, recorded at brief hand-off):** Q1 = a
  (`MISSING_UNTIL_FULL_WINDOW`); Q2 = a (keep `xg_form`,
  `MEAN_OVER_AVAILABLE_WITH_N`, MISSING at `n_xg = 0`); Q3 = a
  (`WITHIN_SEASON`, never the ~301-day figure); Q4 = a (lean
  decision-4 inventory); Q5 = a (`FORM_WINDOW = 5`); Q6 = a
  (competition/season-agnostic window — documented limitation).
- pytest unchanged: 9.1.1; Python 3.12.3; stdlib-only dependencies
  per brief (refused: numpy/pandas/scipy/scikit-learn or any
  numeric/ML stack, `random` under `app/features`, `sqlite3`/`http`
  exception map untouched at its two Phase 5 entries).
- Checkpoint hash: **cfde3a6** (full hash
  cfde3a67bc513890115106b2b774515e1735d4e6; "phase 6: chronological
  feature engine, versioned specs, availability statuses"; 20 files,
  +3045/−82; 103 passed in 61.90s in the pre-commit clean-env run).
  The docs agent then replaces PENDING in docs/ROADMAP.md with cfde3a6
  and flips ROADMAP Phase 6 `in progress` → `committed`.

## 2026-10-19 — Phase 7 (Decision analysis) — built, reviewed PASS (first pass); checkpoint 1e1c1ac

- Built (per docs/briefs/phase-7.md, criteria 1–18, design decisions
  1–13, glass-quant rulings A1–A8, developer answer Q1 = a, declared
  amendments A1–A4):
  - `app/decisions/` — pipeline stage 8 DECISION ANALYSIS, **pure**
    (stdlib `{__future__, dataclasses, typing, enum, json, hashlib}` +
    `app.domain`/`app.models`/`app.forecasts`/`app.scenarios`/
    `app.decisions` only; in `PURE_PACKAGES` per A1; **no
    `app.features`** — Phase 6 criterion 17's pin stays green; **no
    `app.simulation`** — never imported; no `os`/`sys`/`pathlib`/
    `io`/`time`/`random`/`sqlite3`/`http`; no wall clock, no I/O, no
    environment lookups), five modules, 522 lines:
    - `constants.py` — **exactly two** module-level names:
      `REPORT_VERSION = "decision-report-v1"` (developer answer Q1 =
      a) and the fixed `DISCLAIMER` (in-sample analytic estimates,
      single fitted model, synthetic-fixture caveat, pending Phases
      9/11, not-evidence-of-accuracy, the no-second-independent-model /
      never-averaged-or-ensembled clause, estimates-not-certainties) —
      **no threshold, knob, or decision rule exists anywhere in the
      package** (A6 position; criterion 1 pins the two-name module).
    - `canonicalization.py` — the package's **own** spec of record
      (keys sorted, fixed separators, `ensure_ascii=True`, no trailing
      newline, floats via shortest round-trip repr, enums as `.value`,
      tuples as arrays; no timestamp/path/env/seed/MC quantity in the
      payload); no import crosses the stage boundary;
      `app/forecasts/canonicalization.py` untouched.
    - `record.py` — frozen **28-field** `DecisionReport` plus nested
      frozen `ScenarioComparison` (8 fields) and `ScenarioSpread` (4
      fields); `content_hash` computed at construction (`init=False`);
      flags top-level; `kickoff` MISSING never defaulted.
    - `builder.py` — `build_decision_report(forecast, *,
      scenarios=())`: **no `matches`, no time-like parameter**
      (criterion 1 signature pin; the forecast's cutoff was enforced
      once, inside `build_forecast` — a renderer of frozen bytes sees
      no history, so no new leakage surface); `TypeError` on a
      non-`Forecast`; `scenarios` keyword-only; scenario **baseline
      refusal by frozen value equality** and **duplicate-label
      refusal** (`ValueError`, mirroring Phase 4); canonical entry
      order by label (shuffled input ⇒ field-for-field identical
      report incl. hash); **analytic `outcome_probs` only** via the
      one cell-math path (`scenario_matrix` + `outcome_probs`), never
      MC frequencies; per-outcome `min()`/`max()`/spread **only** —
      no mean/sum/ensemble anywhere (criterion 9 pins the computed
      mean's absence); provenance chains through echoed
      `forecast_version` + `forecast_content_hash`.
  - **Zero-scoring / zero-persistence boundary:** reports are
    **in-process VIEWS** — no sqlite table, no `SCHEMA_VERSION` bump
    (still exactly 1), no API route, no CLI; nothing outside
    `app/decisions/` imports the package (AST-enforced both
    directions, criterion 15); `git diff cfde3a6` over
    `app/domain app/models app/forecasts app/scenarios app/simulation
    app/features app/storage app/api app/ingestion app/validation` →
    **empty, exit 0** (docs-agent verified this step); **evaluated n =
    0 — zero scoring ships** (log loss/Brier/RPS/hit rate/calibration/
    baselines all belong to Phases 9/11; a word-boundary token guard
    over `app/decisions/**` asserts their absence, extend-not-weaken).
  - Tests (criteria 1–17 mapped 1:1 in three **NEW** files, 17 new;
    each compacted to exactly 440 lines): `tests/test_decisions.py`
    (7), `tests/test_decisions_scenarios.py` (5),
    `tests/test_phase7_separation.py` (5). Version-local golden report
    content hash
    `00929af76bb833b741db5ae038a08913321eed976d775e654c36094009224768`
    (forecast pair 2024-08-31 Coralgate Athletic vs Harbourlight
    Comets; forecast hash `53df65d1…`; two labeled scenarios
    `home-sharper`/`away-leakier`; derivation in comments; re-derive
    on change, **never widen**).
  - Declared amendments (all pre-sanctioned in the brief; declared at
    checkpoint, review, and monitor sweep): **A1** —
    `tests/test_fixtures_and_hygiene.py` **624 → 625** (net +1):
    exactly one `ALLOWED_APP_IMPORTS` entry
    `{"app.decisions": {"app.domain", "app.models", "app.forecasts",
    "app.scenarios", "app.decisions"}}` plus a line-neutral,
    strictly-stronger `PURE_PACKAGES` edit to the four-set
    `{"app.domain", "app.validation", "app.features", "app.decisions"}`
    (newly bans `os`/`sys`/`pathlib`/`io` in `app/decisions` — the
    strength that makes criterion 15's probes fire); **A2** —
    `tests/test_phase4_separation.py` key-set pin 11 → 12, **832 →
    833**; **A3** — `tests/test_phase5_separation.py` criterion-25 pin
    11 → 12, **572 → 573**; **A4** — `tests/test_phase6_separation.py`
    pins updated **in place** (12-key union incl. `app.decisions`,
    `PURE_PACKAGES` four-set, source-string pins now `== 12` and
    strengthened to exclude **both** `== 10` and `== 11`), **510 →
    510**. All four verified by `wc -l` this docs step; every legacy
    assertion retained in all four files (strictly stronger, never a
    weakening).
- **Process record (recorded honestly):** the first build session was
  **interrupted by a server restart mid-work**; a second session
  completed the phase. The three new test files were compacted to 440
  lines each **by comment/docstring condensation only**; the reviewer
  audited the compaction against the brief's criteria 1–17 mapping and
  confirmed **no probe dropped** — catching and restoring two
  accidental deletions in the process. **Zero self-declared deviations
  remained after the resume** (A1–A4 exactly as pre-sanctioned).
- Docs (this step): `docs/STATISTICAL-ASSUMPTIONS.md` §10 flipped from
  pre-build SPECIFICATION to implemented-and-tested reality (§1–§9
  untouched; **single hunk confined to §10** — verified `git diff |
  grep -c '^@@'` → 1, +189/−0 starting after §9), including the
  phase-end verification paragraph pinning every §10 constraint to the
  shipped tests; `docs/KNOWN-LIMITATIONS.md` new Phase 7 section (13
  entries: ephemeral unstored in-process views; evaluated n = 0, zero
  scoring; no thresholds by design (A6); anti-ensemble min/max only +
  no second independent model exists; scenario comparisons are labeled
  hypotheticals; flag-vs-plausible tension presented, never judged;
  disclaimer wording pinned by test = contract bump; synthetic +
  in-sample caveats ride every report; estimate-properties only, no
  pick-shaped field; amendments A1–A4 exact figures; and the three
  tester/reviewer note dispositions — the `\b` word-boundary scoring-
  guard note, the A2/A3 amendment-number collision note, and the
  interruption-compaction audit) plus the "Not yet applicable" refresh
  (decision reports now exist; stages 3, 9–10 and evaluation still do
  not); `docs/ARCHITECTURE.md` (stage 8 exists; `app/decisions/`
  instantiated — pure, in-process views over frozen forecasts,
  currently unconsumed, never stored; module table, tree, and
  instantiation status updated; "PLANNED" markers retired);
  `README.md` (Phase 7, 120 tests, clean-env note + offline lo-up
  form, all six block hashes); `docs/PLAN.md` §2 `decisions/` line
  planned → EXISTS (Phase 7), **nothing else**; `docs/ROADMAP.md`
  (Phase 7 `in progress`, PENDING-hash convention; **block table
  byte-identical; Block 2 acceptance row recorded pre-brief, riding
  this checkpoint; NO Block 3 acceptance row — that is the
  developer's at the Phases 7–9 boundary**). The three protocol
  records (docs/HEALTH-LOG.md,
  docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor finding 1,
  **including the Block 2 row**) and the phase brief must ride the
  Phase 7 checkpoint commit.
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  **`120 passed in 152.76s`** (0 failed, 0 skipped, 0 xfailed) — this
  docs run (2026-10-19, machine load elevated); recorded range this
  phase ~61–153 s (tester runs 80.04 s and 73.82 s; reviewer runs
  134.14 s and 145.19 s; offline run 128.55 s). 103 prior + 17 new;
  criterion 18 (suite gate) verified by recorded direct runs (tester,
  reviewer ×2, monitor-to-come).
- Offline protocol record (docs-agent run, 2026-10-19): `unshare -rn
  bash -c 'ip link set lo up && env -u PYTEST_ADDOPTS .venv/bin/python
  -m pytest -q'` → **120 passed in 70.49s** (the working offline
  lo-up form; a plain `unshare -rn` still fails the six localhost API
  tests — harness artifact, not a bug, Phase 6 item 11).
- Health (docs run, `bash scripts/health-check.sh`, 2026-10-19): ran
  to completion; compile clean; inner pytest runs **`117 passed, 3
  deselected`** (11.41 s and 11.25 s); skips/xfails `none`;
  determinism **`OK: 117 passed, 3 deselected`**; pip check clean
  ("No broken requirements found."); full invocation **59.09 s** —
  ample headroom under the A2-standing 300 s health-test valve.
- Measured facts (docs agent, real runs this step): signature exactly
  `(forecast, *, scenarios=())` (no `matches`/time parameter);
  `DecisionReport` = 28 fields; the constants module = exactly
  `{REPORT_VERSION, DISCLAIMER}`; `app.simulation` never imported by
  `app/decisions` (module-load probe); the golden hash reproduces via
  the suite pin; `wc -l`: 625 / 833 / 573 / 510 (amended files) and
  440 / 440 / 440 (new files); `app/decisions/` = 522 lines.
- Review history: tester verdict **PASS ×18** — golden content hash
  `00929af7…` independently re-derived, scenario deltas bit-exact,
  plus an offline suite run; reviewer verdict **PASS (2026-10-19,
  first pass, criteria 1–18)** including the interruption-compaction
  audit (no probe dropped; two accidental deletions caught and
  restored). Both non-blocking observations (the `\b` word-boundary
  scoring-guard note; the A2/A3 amendment-number collision note) ruled
  **DOCS-level** and dispositioned in KNOWN-LIMITATIONS Phase 7 items
  11–12.
- **glass-quant was consulted** for this phase (mandatory, brief;
  run at conductor top level, 2026-10-19): rulings **A1–A8 binding**,
  no-objections recorded — prospective report **structure** over
  frozen outputs; the signature without `matches`/time; the
  absence-of-scoring blocker criterion; the vocabulary contract; the
  unstored frozen report with provenance chain; **no thresholds**
  (position, not default); the IX-7 out-of-scope list; and the
  evaluation substrate already complete — nothing to pre-score.
- **Developer answered Q1 = a (2026-10-19, recorded at brief
  hand-off):** `REPORT_VERSION = "decision-report-v1"`; the three
  structural questions resolved by brief positions (storage = none,
  thresholds = none, features-consumer = no).
- pytest unchanged: 9.1.1; Python 3.12.3; stdlib-only dependencies
  per brief (refused: numpy/pandas/scipy/scikit-learn or any
  numeric/ML stack, any third-party package, `random` under
  `app/decisions`, `app.simulation`, `sqlite3`/`http` exception map
  untouched at its two Phase 5 entries).
- Checkpoint hash: **1e1c1ac** (full hash
  1e1c1ac3ba4968fa7d69f46467c0d79452ae1b54; "phase 7: decision reports,
  scenario comparison without collapse, no-scoring boundary";
  2026-10-19 19:25 +0100, master; 21 files, +2755/−92; 120 passed in
  153.07s in the pre-commit clean-env run).
  The docs agent then replaces PENDING in docs/ROADMAP.md with 1e1c1ac
  and flips ROADMAP Phase 7 `in progress` → `committed`, as in Phases
  4–6.

## 2026-10-19 — Phase 8 (Temporal integrity) — built, reviewed PASS (first pass); checkpoint ea92667

- Built (per docs/briefs/phase-8.md, criteria 1–14, design decisions
  1–14, glass-quant rulings A0–A9, AMENDMENT A1) — **tests and
  documentation only: ZERO production code changed** (`git diff 1e1c1ac
  -- app/` **empty, exit 0**, version-local byte-pin; no new `app/`
  package — the first phase since Phase 2 with **zero hygiene growth**,
  no `ALLOWED_APP_IMPORTS`/`PURE_PACKAGES` amendments):
  - `tests/test_temporal_integrity.py` (**NEW**, 440 lines, 8 tests,
    criteria 1–8): the five-entry poison-coverage registry bijection +
    AST census of every public `matches`-parameter entry point +
    negative probes (a future history-consuming entry point fails the
    suite until registered and poisoned — PLAN §6 layer 4's standing
    regression clause); cutoff-at-source **bit-identity** over fully
    unfiltered pools (same-day siblings + future matches + extreme
    scorelines, poisons never raise) for `fit`, `build_forecast`,
    `compute_features` incl. `input_digest`/`content_hash`; same-day
    invisibility pinned as **declared design, never a fix** (behavioral
    + docstring source pin); independent snapshot-immutability audit
    (raw UPDATE/DELETE → `IntegrityError`; hostile trigger-dropping
    tamper caught by read-path hash recompute naming the fixture key;
    re-armed triggers refuse again); seedless-by-construction AST pin
    (no `random` of any spelling under `app/models|forecasts|features|
    decisions`, positive-control probes, `app/simulation/simulate.py`
    the sanctioned home) + the `git diff 1e1c1ac -- app/` empty
    byte-pin; nothing-to-tune pin (signature exactly `(matches, as_of,
    *, config=None)`, `FitConfig` exactly the five pinned fields,
    non-None ridge → `ValueError`, no spec/config/variant/seed-shaped
    parameter on any entry point).
  - `tests/test_vocab_guards.py` (**NEW**, 321 lines, 5 tests, criteria
    9–13): the segment-boundary guard asserted on the imported
    `_SCORING_PATTERN.pattern` with `brier_score`/`_rps_`/`x_brier`
    positive controls and `log_probs`/`probability`-class negatives;
    app-wide strict-segment scoring scan with an **exactly-one pinned
    negation allowlist** — `app/simulation/__init__.py`, "MC noise
    never contaminates log loss, Brier, or RPS." — the honest docstring
    preserved **by design** (deletion or rewording fails; a second
    allowlisted site fails); accuracy-trio **identifier-scope** scan
    (the five recorded validation-vocabulary "validated" uses pinned as
    the reason source-text scope is not claimed app-wide;
    `validated_records` composite pinned NOT flagged); field-name bans
    exactly for performance/rank/correct/best shapes with the
    **score-vocabulary negative regression** (`score`/`scoreline`/
    `scored` never banned — 75 real identifier uses are legitimate
    domain vocabulary); non-bans pinned (`baseline`, `metric`, `word`).
  - `tests/test_phase7_separation.py` — **AMENDMENT A1 ONLY**: the
    `_SCORING_PATTERN` compile line changed in place, `\b`-form →
    segment-boundary lookarounds (closing the Phase 7 item-11
    suffixed-form gap, pulled forward from Phases 9/11 per A4);
    **440 → 440 lines**, every legacy assertion retained, strictly
    stronger (empirically verified superset — reviewer re-verified).
  - **Scope anchor (recorded honestly):** quant ruling **ADV-0**
    corrected the conductor's framing error — Phase 8 is **IX-8
    temporal integrity, NOT backtesting**: backtesting machinery is
    Phase 9, first scoring is Phase 11; zero predictions, zero
    baselines, zero metrics ship — **evaluated n remains exactly 0**.
- Docs (this step): `docs/STATISTICAL-ASSUMPTIONS.md` **§11 authored
  BEFORE any build code** (+102/−0, single hunk appended after §10;
  the Phase 3 §3 / Phase 4 §7 / Phase 5 §8 / Phase 6 §9 / Phase 7 §10
  pre-build pattern) and flipped at this step from SPECIFICATION to
  implemented-and-tested reality (**§§1–10 untouched — single hunk
  confined to §11**, verified `git diff | grep -c '^@@'` → 1,
  +139/−0 total): the three-step line and "Phase 8 adds nothing
  evaluation needs"; the A6 sample pre-registrations (60 matches = 20
  dates × 3, 6 teams, 156 goals — 120 is team-appearances, never
  "matches"; walk-forward-eligible unflagged fits exactly 30/60;
  ceilings ≤ 60 predictions ≤ 30 clean; scored population
  pre-registered before Phase 11; bins fixed pre-score; variant ranking
  infeasible at this n → "beating" banned on sample-size grounds even
  after Phase 11); the A2 forward contracts (test-first gate —
  *poison the entire remaining future → earlier predictions
  byte-identical* must exist before the harness may emit output — and
  the single-model-spec/no-config-loop/no-best-selection commitment);
  the A7 run-manifest contract (fixture sha256s, `canonical_state()`
  digest, per-fixture `input_digest` + `content_hash`, model_version +
  FitConfig identity + versions, ordered-list run digest, **no
  timestamp in hashed payload**, re-run = idempotence proof); the A5
  storage forward record (predictions → the existing write-once
  forecasts table; baselines in-process re-derivable; evaluation table
  = Phase 11's schema bump; `get_forecast()` single-row-per-natural-key
  ambiguity flagged for the Phase 9/11 briefs, not fixed here) — plus
  the phase-end verification paragraph pinning every §11 claim to the
  shipped tests. `docs/KNOWN-LIMITATIONS.md`: intro + "Not yet
  applicable" header flipped to Phase 8 (stages 3, 9–10 + evaluation
  remain unbuilt; backtesting/evaluation remain planned; "temporal
  integrity" deliberately NOT listed — nothing to retire), new
  **Phase 8** section (10 items: tests+docs-only/evaluated-n-0;
  AMENDMENT A1 declared; the exactly-one-entry scoring allowlist with
  the honest docstring preserved by design; the accuracy-trio
  identifier-scope decision with the five recorded "validated" uses;
  score/scoreline/scored never source-banned; same-day invisibility =
  declared design; the `get_forecast()` Phase 9/11 note; SCHEMA_VERSION
  still 1; the pinned nothing-to-tune surface; the load-driven runtime
  watch item), and the **Phase 7 item 11 disposition UPDATED by
  appended follow-through only** (the original item text untouched).
  `docs/ARCHITECTURE.md` (Phase 8 status line: temporal-integrity
  defenses exist as tests + docs; no new module; stage map unchanged;
  `app/backtesting/`/`app/evaluation/` remain PLANNED; test counts
  refreshed to 24 modules / 133 tests). `README.md` (Phase 8, 133
  tests, clean-env note + offline lo-up form, all **seven** commit
  hashes 45ed27e/1c5067b/a5d7f56/f208e43/44b43ea/cfde3a6/1e1c1ac).
  `docs/ROADMAP.md` (Phase 8 `in progress`, PENDING-hash convention;
  **block table byte-identical; Block 2 acceptance row untouched; NO
  Block 3 acceptance row — the developer's at the Phases 7–9
  boundary**). `docs/PLAN.md` **verified untouched** (Phase 8 adds no
  module). The three protocol records (docs/HEALTH-LOG.md,
  docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor finding 1) plus the
  phase brief and the two new test files must ride the Phase 8
  checkpoint commit.
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  **`133 passed in 100.34s`** (this docs run, 2026-10-19; 0 failed, 0
  skipped, 0 xfailed) — 120 prior + 13 new; load-driven wall-clock
  this phase ranged roughly **100–225 s** depending on machine load,
  outcomes **identical across 6+ recorded executions** (tester ×3,
  reviewer ×2, docs ×2). Criterion 14 (suite gate) verified by
  recorded direct runs (tester, reviewer ×2, docs agent).
- Offline protocol record (docs-agent run, 2026-10-19): `unshare -rn
  bash -c 'ip link set lo up && env -u PYTEST_ADDOPTS .venv/bin/python
  -m pytest -q'` → **`133 passed in 128.77s`** (the working lo-up
  form; plain `unshare -rn` still fails the six localhost API tests —
  harness artifact, not a bug, Phase 6 item 11).
- Health (docs run, `bash scripts/health-check.sh`, 2026-10-19): ran
  to completion; compile clean; inner pytest runs **`130 passed, 3
  deselected`** (14.21 s and 16.29 s); skips/xfails `none`;
  determinism **`OK: 130 passed, 3 deselected`**; pip check clean
  ("No broken requirements found."). The A2-standing 300 s health-test
  valve remained ample all phase (watch item carried: the health
  test's module-scoped setup inner time went 24.7 s at the Phase 7
  sweep → ~35 s under load — setup-dominated, ~1.9× margin — recorded
  in KNOWN-LIMITATIONS Phase 8 item 10).
- Review history: tester verdict **PASS ×14** — a 131-check probe
  suite driving the registry/census/allowlist machinery both ways,
  **three honest probe-bug disclosures** (probe-side defects the
  tester caught and reported rather than papering over), and the suite
  run **×3 including an offline run**. Reviewer verdict **PASS
  (2026-10-19, first pass, criteria 1–14)** — including **empirical
  verification that AMENDMENT A1's segment-boundary pattern is a
  strict superset** of the legacy `\b` form and **execution of the §11
  forward-contract checklist** (test-first-gate sentence, single-model-
  spec/no-config-loop/no-best-selection declaration, manifest field
  list + no-timestamp rule, A6 population/bin/ranking pre-registrations
  — design decision 10's reviewer-checklist route in force).
- Builder record: **zero deviations**; one self-resolved brief
  ambiguity — criterion 8's config reading, resolved per design
  decision 9 — **adjudicated coherent by both tester and reviewer**.
- **glass-quant was consulted** for this phase (mandatory, brief; run
  at conductor top level, 2026-10-19): rulings **A0–A9 binding**,
  zero developer questions (A9); **ADV-0 scope-anchor correction of
  the conductor's framing error recorded honestly** (Phase 8 = IX-8
  only — not backtesting, not metrics); A1 poison-matrix registry +
  cutoff-at-source bit-identity; A2 nothing-to-tune pin + pre-declared
  Phase 9 test-first gate and single-spec contract; A3 seedless pin;
  A4 vocabulary hardening (including the architect's resolution of the
  ruling's own literal-pattern-vs-positive-control tension as
  segment-boundary semantics, design decision 6, and the
  identifier-scope trio resolution, design decision 11); A5 storage
  forward record; A6 sample-size pre-registrations; A7 run-manifest
  contract; A8 out-of-scope list. **AMENDMENT A1 declared** (one line
  in place, 440 → 440, strictly stronger, empirically verified
  superset; declared at checkpoint, review, and monitor sweep).
- pytest unchanged: 9.1.1; Python 3.12.3; stdlib-only dependencies
  (refused: numpy/pandas/scipy/scikit-learn or any numeric/ML stack,
  any third-party package, any new `app/` module, any sqlite schema
  change — `SCHEMA_VERSION` still exactly 1).
- Checkpoint hash: **ea92667** (full hash
  ea92667af37e069c843c4ba9696771552dcc6e94; "phase 8: temporal
  integrity defenses, poison registry, vocabulary guards";
  2026-10-19 22:13 +0100, master; 11 files, +1514/−58; 133 passed in
  157.65s in the pre-commit clean-env run).
  The docs agent then replaces PENDING in docs/ROADMAP.md with
  ea92667 and flips ROADMAP Phase 8 `in progress` → `committed`, as
  in Phases 4–7.

## 2026-10-22 — Phase 9 (Backtesting) — built, reviewed PASS (first pass); checkpoint 80b8f79

- Brief of record: `docs/briefs/phase-9.md` (342 lines, glass-architect,
  2026-10-20, amended in place by AMENDMENTS A3' and A4 with full
  provenance). HANDOFF Part IX item 9 — *"Backtesting — strictly
  chronological backtesting harness, baselines (long-run home/draw/away
  frequencies), idempotent runs"* — delivered as a **pure
  `app/backtesting/` package**, machinery only. **glass-quant was
  consulted** (mandatory; run at conductor top level, 2026-10-20):
  rulings **A0–A10 binding** (A0 pre-declared the A1/A2/A3 amendments;
  A1 blocker-grade no-join scope boundary — the realized-result surface
  is pre-cutoff history ONLY, the one-line natural-key join is
  re-established at Phase 11; A2 the test-first poison gate; A3
  walk-forward mechanics + the single structural model spec; A4
  caller-side persistence through the existing write-once path, no
  committed DB, `SCHEMA_VERSION` stays 1; A5 baselines per-fixture
  chronological only; A6 §12 authored BEFORE any build code; A7
  vocabulary extend-not-weaken; A8 out-of-scope list; A9 zero
  developer questions — **none were raised**; A10 empirical probes
  **E1–E4** — E1 the 3 structural first-date refusals, E2 the full
  harness runtime (~2.5 s idle / ~4.2 s loaded — full harness
  everywhere, never subset), E3 unfiltered-pool cannot leak, E4 the
  baseline `n` sequence 0, 0, 0, 3, …, 57 — re-verified by the
  architect at brief time, reconciled as design decisions 2, 3, 17).
- Build: `app/backtesting/` **NEW** — `constants.py`
  (`BACKTEST_VERSION = "backtest-walkforward-v1"`, no knob),
  `canonicalization.py` (own spec of record, no timestamp anywhere),
  `record.py` (frozen `BaselineRecord`/`RefusalRecord`/`RunManifest`/
  `WalkForwardRun`, construction-time content hashes), `baselines.py`
  (ALL functions underscore-private; the only realized-score consumer),
  `harness.py` (`run_walk_forward(matches, *, fixture_file_sha256s=(),
  interpreter_version=None)` — the SINGLE public `matches`-parameter
  entry point, pure, **no `app.storage` import** — persistence is the
  caller's) + `__init__.py` — **6 modules, 535 lines**.
  `tests/test_backtesting.py` (**NEW**, criteria 1–12) and
  `tests/test_vocab_guards.py` (criteria 13–14 appended; **321 → 440
  lines**, within budget). Shipped facts pinned by test: golden run
  digest `150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f`
  (version-local, derived from the real first run, independently
  re-derived in test); the auditable accounting **60 targets = 3
  structural refusals (first-class `RefusalRecord`s — never skipped,
  never uniformed) + 27 flagged + 30 clean = 57 predictions**;
  hand-computed baselines (fixture 4 exactly (1/3, 1/3, 1/3), n = 3;
  fixture 36 (15/33, 8/33, 10/33), n = 33); MISSING `n = 0` at the
  first date's three fixtures, fake uniform and full-sample fallback
  both pinned absent; baselines never stored; double-run idempotence in
  process and at the store level (`True`×57 then `False`×57 through
  `insert_forecast` into a `tmp_path` DB; `SCHEMA_VERSION == 1`; no
  committed DB); the test-first poison gate (criteria 1) — poisoning
  the entire remaining future leaves every earlier prediction
  field-for-field identical including `content_hash`; and the no-join
  enforcement (token scan + function-level co-occurrence AST scan with
  positive controls both ways). **Zero metrics of any kind; no
  model-vs-baseline comparison exists; no prediction-to-outcome join
  ships — evaluated n remains exactly 0.**
- Declared amendments (brief pre-sanctioned; declared at checkpoint,
  review, and monitor sweep), exact figures verified `wc -l`:
  **A1** (`tests/test_temporal_integrity.py`) poison registry 5 → 6 +
  `matches` census 3 → 4 for `run_walk_forward` + its poison test;
  **A2** (same file) Phase 8's `app/` byte-pin re-pointed `1e1c1ac` →
  `ea92667` and rescoped to the pre-existing packages (excluding
  `app/backtesting`) — **combined 440 → 452**; **A3+A3'**
  (`tests/test_fixtures_and_hygiene.py`) one `ALLOWED_APP_IMPORTS`
  entry with the A3'-corrected **self-inclusive** value
  `{"app.domain", "app.forecasts", "app.backtesting"}` + the
  line-neutral `PURE_PACKAGES` five-set, **625 → 626**, and the
  pin-collision class across four separation files —
  `tests/test_phase4_separation.py` **833 → 834**,
  `tests/test_phase5_separation.py` **573 → 574**,
  `tests/test_phase6_separation.py` **510 → 510** (net zero),
  `tests/test_phase7_separation.py` **440 → 443** (the fifth file,
  found at A3'-ruling time); **A4** (`tests/test_health_script.py`)
  `HEALTH_TIMEOUT_S` **300 → 1500 s**, **105 → 105 lines**, no
  assertion changed + the SOLE sanctioned edit ever to
  `scripts/health-check.sh` (determinism-section strip-regex fix for
  pytest's ≥ 60 s `(0:MM:SS)` parenthetical + the counts-only
  `UNPARSEABLE` gate; five inner runs, recursion guard, and every other
  section untouched) + the 653-line `tests/test_backtesting.py`
  adjudicated **ACCEPTED as a deviation** (A4 item 3 — soft convention,
  no split, no trim). Every legacy assertion retained in all six
  amended files (strictly stronger, never a weakening).
- Builder record: **two interrupted sessions** (server restarts) — the
  second completed the first's work — and **two STOP-and-reports, zero
  self-sanctioning**. (i) 2026-10-20: the builder stopped against
  A3's blocker-grade sanctioned value — the mandated five-module
  package could not wire its own intra-package imports against the
  criterion-12 prefix scanner; the architect independently re-verified
  the scanner, probed all eleven existing entries as self-inclusive,
  **RATIFIED the corrected self-inclusive value (AMENDMENT A3')** and
  folded in A3's own missed fifth pinned file
  (`tests/test_phase7_separation.py`) — a brief-composition omission,
  same mechanical pin-collision class; not a developer decision (A9
  stands). (ii) 2026-10-21: the A4 health-valve TRIP — the direct
  suite, on the conductor's independent reproduction **verbatim**:
  `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` → **`144
  passed, 3 errors in 428.03s (0:07:08)`** — all three errors
  `subprocess.TimeoutExpired: bash scripts/health-check.sh timed out
  after 300 seconds` at `tests/test_health_script.py:21`, zero test
  failures; the builder STOP-and-reported both A4 defects (valve no
  longer holds at load ~11; the determinism strip-regex defect) without
  touching any unsanctioned file; the suite was RED until A4 items 1–2
  landed — no checkpoint on red tests. Architect ruled A4 (2026-10-21)
  under the standing Phase 4 re-scope clause: 1500 s ≈ 2.3–2.5× the
  worst observed ~600–660 s script wall at load ~10–11 (rejected bounds
  and reasons recorded in the brief); test-cost reduction rejected with
  reasoning (2–3%, tautology risk); waiting for lower load NOT
  required.
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  **`147 passed in 723.04s (0:12:03)`** (this docs run, 2026-10-22,
  machine load ~11 per `uptime` at start; 0 failed, 0 errors, 0
  skipped, 0 xfailed) — 133 prior + 14 new. Recorded executions:
  clean-env ×2+ at load ~9.5–12.7 on 4 cores (~647–750 s), all
  outcomes identical; offline `unshare -rn` lo-up form **147 passed in
  867.88 s**; health script exit 0 with inner runs **`144 passed, 3
  deselected` ×2** (117–131 s each — both > 60 s, the A4 strip-fix
  positive proof), determinism `OK:`, skips/xfails `none`, pip clean,
  script wall **~627 s**. Criterion 15 (suite gate) verified by
  recorded direct runs (tester, reviewer ×2, conductor, docs agent).
- Review history: tester verdict **PASS ×15** — the golden run digest
  independently re-derived, the hand-computed baselines independently
  recomputed (fixture 4 and fixture 36 reproduced exactly), and the
  suite executed **×3 including an offline run**. Reviewer verdict
  **PASS (2026-10-22, FIRST pass, criteria 1–15)** — including an
  amendment **byte-audit** of all six amended test files against the
  declared figures, the reviewer's **own re-derivation of the golden
  run digest**, and **A4's 1500 s ratio adjudication** (evidence
  arithmetic re-checked). Zero fix cycles — first pass, as in Phases
  4–8 (tester and reviewer both clean on the first round).
- Docs (this step): `docs/STATISTICAL-ASSUMPTIONS.md` **§12 authored
  BEFORE any build code** (+95/−0, single hunk appended after §11, per
  ruling A6/brief decision 15) and flipped at this step from
  SPECIFICATION to implemented-and-tested reality (**§§1–11 untouched;
  the flip is a single hunk confined to §12** — the pre-build §12 rode
  the working tree only, so vs checkpoint ea92667 the whole section
  shows as a clean `+179/−0` append, `git diff | grep -c '^@@'` → 1):
  the shipped surface (one public `matches`-parameter function, pure,
  no storage import; baselines private; 535 lines; golden digest), the
  now-real 60 = 3 + 27 + 30 = 57 accounting, the hand-recomputed
  baseline pins, the MISSING-at-first-date pins, the mechanically
  enforced no-join boundary, and the declared amendments A1–A4 with
  exact figures, plus the phase-end verification paragraph pinning
  every §12 claim to the shipped tests. `docs/KNOWN-LIMITATIONS.md`:
  intro + "Not yet applicable" flipped to Phase 9 (**"Backtesting"
  leaves the not-yet-applicable list**; stages 3, 10, evaluation remain
  — `app/evaluation/` stays PLANNED, Phase 11's), new **Phase 9**
  section (12 items: zero metrics/evaluated n = 0 with no
  model-vs-baseline comparison — deliberately; the 3 structural
  refusals first-class, 60 = 3 + 27 + 30 = 57 auditable; baselines
  per-fixture chronological only with tiny-early-n, MISSING-never-
  faked, never-stored, synthetic + §2f draw-bias caveats; no
  prediction-to-outcome join — Phase 11 re-establishes; the
  `get_forecast` brief position (three points) with latent fetchone
  retained; `SCHEMA_VERSION` 1 + no committed DB; the version-local
  golden run digest — re-derive, never widen; amendments A1/A2/A3+A3'/A4
  with exact figures; both STOP-and-reports; the 653-line accepted
  deviation; the load-driven runtime watch item; the 9-vs-10
  accuracy-sites one-line disposition — the quant prose said 9, its
  own list and the real scan say 10, the guard pins the real 10) and
  the **Phase 1 item 2 disposition UPDATED by appended A4 follow-through
  only** (the RED run verbatim, the 300 → 1500 s re-scope, the strip
  fix, post-fix evidence — all prior measured figures kept as
  measured, nothing rewritten). `docs/ARCHITECTURE.md` (Phase 9 status
  line: stage-9 backtesting exists as a pure package consumed by
  nothing under `app/`; `app/evaluation/` remains PLANNED; stage map
  unchanged; module table + tree updated; test counts refreshed to 25
  modules / 147 tests). `README.md` (Phase 9, 147 tests, clean-env
  docs-run figure 147 passed in 723.04 s with the honest ~11-min-at-
  load-~10 note, offline lo-up form 867.88 s, all **eight** commit
  hashes 45ed27e/1c5067b/a5d7f56/f208e43/44b43ea/cfde3a6/1e1c1ac/
  ea92667). `docs/ROADMAP.md` (Phase 9 `in progress`, PENDING-hash
  convention — the git agent makes the checkpoint commit; this agent
  replaces PENDING and flips the row to `committed` after, as in
  Phases 4–8; **block table byte-identical; Block 1/2 rows untouched;
  NO Block 3 acceptance row — the developer's at the Phases 7–9
  boundary after the Phase 9 commit and monitor sweep**).
  `docs/PLAN.md` §2: the `backtesting/` line flipped planned → EXISTS
  (Phase 9), nothing else. The three protocol records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor
  finding 1) plus the phase brief, the two new test files, the six
  amended test files, `app/backtesting/`, and the A4 script/test edits
  must ride the Phase 9 checkpoint commit.
- Zero developer questions (A9) — every structural question resolved as
  a brief position. Block 3 acceptance remains the developer's at the
  Phases 7–9 boundary after the Phase 9 commit and monitor sweep.
- pytest unchanged: 9.1.1; Python 3.12.3; stdlib-only dependencies
  (refused: numpy/pandas/scipy/scikit-learn or any numeric/ML stack,
  any third-party package, any sqlite schema change — `SCHEMA_VERSION`
  still exactly 1; no committed DB).
- Checkpoint hash: **80b8f79** (full hash
  80b8f79383ab1c990ffc497a8d2c751ebc2b5b11; `phase 9: chronological
  backtesting harness, per-fixture baselines, idempotent runs`;
  2026-10-22 18:25 +0100, master; 25 files, +2482/−138; 147 passed in
  714.36s in the pre-commit clean-env run).
  The docs agent then replaces PENDING in docs/ROADMAP.md with
  80b8f79 and flips ROADMAP Phase 9 `in progress` → `committed`, as
  in Phases 4–8.

## 2026-10-22 — Phase 10 (Operational reliability) — built, reviewed PASS (first pass); checkpoint 8abe1ca

- Brief of record: `docs/briefs/phase-10.md` (267 lines, glass-architect,
  2026-10-22). HANDOFF Part IX item 10 — *"Operational reliability —
  error handling, compile checks, health monitoring, runtime sanity on
  this hardware"* — delivered as tests + docs only: the
  architect-sanctioned **run-structure rework of
  `scripts/health-check.sh`** (the rework the Phase 4 A2 record and
  Phase 9 A4 both reserved to Phase 10), an **evidence-based downward
  valve re-tune**, **TEST-ONLY error-handling coverage**, the
  **compile-checks strand completed** to cover `tests/`, and
  **load-labeled runtime-sanity records** on this hardware. Scope
  anchor (ADV-0/Phase 8 precedent): Phase 10 is IX-10, **not** pipeline
  stage 10 (`app/improvement/` stays PLANNED) and **not** IX-11/IX-12.
  **glass-quant was consulted** (mandatory; run at conductor top
  level, 2026-10-22): rulings **ADV-1–ADV-10 binding** (ADV-1 blocker
  discharged — the Block 3 acceptance row verified and quoted, which
  also discharges Phase 11's block gate; ADV-2 the 3-run rework with
  capture-once derivation; ADV-3 the in-suite health-test structure
  SOUND — the script is fixed, the test inherits with zero assertion
  changes; ADV-4 valve re-tune DOWN with fresh load-labeled evidence
  under a pre-declared procedure; ADV-5 load position — reduce
  execution counts, no wall-clock SLA anywhere; ADV-6 the two
  TEST-ONLY error-path tests against probed real behavior, zero
  production change; ADV-7 the 10-item invariants; ADV-8 docs
  placement; ADV-9 exit-0-by-design kept; ADV-10 zero developer
  questions — **none were raised**). Block table and the Block 1/2/3
  acceptance rows verified untouched.
- Build: `scripts/health-check.sh` — **AMENDMENT A1** (the sole
  sanctioned exercise of A4's reservation; the ONLY sanctioned
  amendment to the script after A4's) — full-file replacement,
  **80 → 98 lines**, byte-exact against the brief's A1 text
  (re-verified by diff at the docs step): **exactly THREE inner pytest
  executions replace the former FIVE** with capture-once derivation —
  run 1 (plain, captured once) feeds the display tail AND determinism
  SUM1; run 2 (`-rsxX`, captured once) feeds its display tail AND the
  skips/xfails grep (absorbing the old skips run, flags-identical to
  run 2 — pure duplication); run 3 (silent plain execution) yields
  SUM2, keeping the determinism pair two identical-flag plain runs
  with the A4 mechanism byte-verbatim (counts-only strip, `COUNTS_RE`,
  loud `UNPARSEABLE`). `tests/test_operational.py` **NEW** (criteria
  1–8, 409 lines, 8 tests, stdlib only): the error-handling strand —
  corrupted/truncated store raises `sqlite3.DatabaseError` LOUDLY at
  the first read, pinned as probed (NOT `ForecastIntegrityError` —
  that is the structurally-valid-row hash-mismatch path; pin
  platform/sqlite-version-local) — and the interrupted multi-insert
  batch (mid-batch `ForecastConflictError`: prior rows intact,
  `verify_all` hash-clean in canonical order, zero partial row for the
  failed insert — journal atomicity pinned as observed in
  `insert_forecast`'s per-call `BEGIN IMMEDIATE` + rollback) — plus
  the source pins: compile covers `app tests`, exactly 3 `-m pytest`
  and exactly 1 `-rsxX`, SUM lines consume plain captures only, the A4
  mechanism verbatim, exactly nine section headers, the A2 two-line
  valve pattern, and the version-local byte-pins. **Zero production
  code: `git diff 80b8f79 -- app/` empty** (exit 0; pinned by
  criterion 8's test); no new `app/` package; no hygiene amendments.
- Check-preservation mapping (ADV-10; reviewer verified row by row):
  **a CHECK is never dropped — only redundant EXECUTIONS were
  eliminated**. The eliminated executions were exactly the redundant
  ones (the old skips run's flags were identical to run 2's; the
  determinism sums were two extra executions replaced by derivation
  from captures + the silent run 3); determinism comparison executions
  2 → 2 (unchanged); skips "none" gate present; all nine section
  headers, the recursion guard, pip, five-largest, and
  exit-0-by-design byte-identical. Load-independent facts: inner
  pytest executions **5 → 3**; non-health-suite executions per
  direct-suite cycle **6 → 4**. Compile checks extended `app` →
  `app tests` (decision 8, criterion 3-pinned).
- Valve evidence (AMENDMENT A2, Phase 10 — decision-6 procedure
  executed; every health-script execution recorded with wall time AND
  invocation-start load): builder **317 s @ load 9.79**, **322 s @
  8.96**, **335 s @ 10.06**; reviewer **332.43 s @ 10.09**; tester
  standalone **238.34 s @ 10.71**. **W = 335 s** (worst
  post-restructure wall at load ≥ 8); **V = 800 s** —
  **800/335 ≈ 2.39×, inside the pre-declared [2.3, 2.5] band**
  (reconciled with the shipped A2 comment's at-A2-time W = 322 s →
  2.48× — both in band). Exactly two in-place edits in
  `tests/test_health_script.py` (the `HEALTH_TIMEOUT_S` constant and
  the matching docstring figure), **105 → 105 lines, no assertion
  changed**. Rejected bounds recorded A4-style: **700** (2.09× — under
  band), **750** (margin-fragile — in band at the then-worst but
  erodes to 2.24× at the final W = 335), **850** (2.54× — over band),
  **keep 1500** (4.48× — not evidence-proportional after the rework).
  The valve is a hang-detection bound with evidence margin, never a
  performance guarantee (ADV-5); the full 120 → 300 → 1500 → 800
  chain with provenance (A2/Phase 4; A4/Phase 9 after the
  verbatim-reproduced trip; A2/Phase 10 down-tune) is appended to
  KNOWN-LIMITATIONS Phase 1 item 2 (append-only; prior figures never
  rewritten).
- Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
  **155 passed** clean-env across every recorded execution at load
  ~0.97–12 (118–514 s; outcomes identical everywhere, zero
  skips/xfails/errors) — 147 prior + 8 new. This docs run: **155
  passed in 149.60 s** at load 9.67 (`uptime` at invocation). Offline
  lo-up form: **155 passed in 502.50 s** at load 9.80. Health script
  standalone: exit 0, walls **238–335 s at load ~6.5–10.7**; inner
  runs **`149 passed, 6 deselected` ×2** (displayed runs 1–2; run 3
  silent), determinism **`OK:`** counts-only, skips/xfails `none`,
  pip clean, all nine headers. **N1 (tester), recorded: 155 direct =
  149 passed + 6 deselected inside script runs by the byte-pinned
  recursion guard — the 3 health tests + the 3 `test_operational`
  source pins whose names contain `health_script`; no check lost, and
  the pins run in every direct suite execution.** Execution-count and
  latency facts: inner runs 5 → 3, per-direct-suite-cycle executions
  6 → 4, script wall ~627 s (Phase 9, load ~8.9–10.4) → **~330 s at
  comparable load** — expected hang-detection latency 25 → ~15 min.
- Declared amendments (brief pre-sanctioned; declared at checkpoint,
  review, and monitor sweep), exact figures verified: **A1**
  (`scripts/health-check.sh`) full-file run-structure rework, **80 →
  98 lines**, byte-exact vs the brief's A1 text; **A2**
  (`tests/test_health_script.py`) exactly two in-place lines, valve
  **1500 → 800 s**, **105 → 105 lines**, no assertion changed. Every
  legacy assertion retained (strictly stronger, never a weakening).
  `docs/STATISTICAL-ASSUMPTIONS.md` **gained no §13** (decision 9 —
  zero statistics ship; a section would imply statistical machinery
  where none exists; §§1–12 untouched).
- Review history: tester verdict **PASS** (criterion 9 executed and
  pasted, including the offline lo-up run and the standalone health
  run; findings F1 = the docs-step gate and N1 = the recursion-guard
  count note, both closed within protocol). Reviewer verdict **PASS
  (2026-10-22, FIRST pass)** — the CHECK-PRESERVATION MAPPING verified
  row by row against the shipped script, the determinism counts-gate
  semantics confirmed unchanged (criteria 4–5), the valve arithmetic
  re-checked against the load-labeled measurements (V/W = 2.39× ∈
  [2.3, 2.5]), no harness subsetting (E2 — golden files byte-pinned),
  and the amendment declarations matched to the shipped diffs exactly.
  Zero fix cycles — first pass, as in Phases 4–9.
- Docs (this step): `docs/KNOWN-LIMITATIONS.md` — intro flipped to
  Phase 10; new **Phase 10** section (7 items: zero production code /
  evaluated n = 0 / no SLA / no §13; the 3-run rework with the
  check-preservation summary; the compile-tests extension; the 800 s
  valve with its load-labeled evidence and rejected bounds; the
  corruption pins — real `sqlite3.DatabaseError`, not
  `ForecastIntegrityError`, platform-local; the batch-atomicity pin +
  the N1 clause; the A1/A2 declared figures); Phase 1 items 2 and 5
  **appended** follow-through only (the full 120 → 300 → 1500 → 800
  valve chain with provenance; the 6× → 4× suite-cost clause with
  load-labeled current figures — all prior measured figures kept as
  measured); "Not yet applicable" refreshed to Phase 10 (stages 3 and
  10, `app/evaluation/`, and improvement remain PLANNED).
  `docs/PROGRESS-LOG.md` (this entry). `docs/ROADMAP.md` — Phase 10
  `in progress`, PENDING-hash convention (the git agent makes the
  checkpoint commit; this agent then replaces PENDING and flips the
  row to `committed`, as in Phases 4–9; **block table byte-identical;
  Block 1/2/3 rows untouched — the Block 3 acceptance row recorded
  2026-10-22 rides this checkpoint commit unedited**). `README.md`
  (Phase 10, 155 tests, honest load-labeled run-time note: suite
  ~2–8 min at load ~1–12; health script ~4–6 min; clean-env and
  offline lo-up forms). `docs/ARCHITECTURE.md` (health script
  recorded as 3 inner runs with capture-once derivation and the
  compile-tests extension; no new module — `tests/test_operational.py`
  added to the test inventory; stages 3, 10, evaluation, improvement
  remain PLANNED; test counts refreshed to 26 modules / 155 tests).
  `docs/PLAN.md` checked — **no change needed** (its health-script
  wording — the double-run determinism comparison, the continuous
  baseline — remains exactly true under the 3-run structure). The
  three protocol records (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md,
  docs/ROADMAP.md — monitor finding 1, carrying the Phase 9 records)
  plus the phase brief, `scripts/health-check.sh`, the two test-file
  edits, and `tests/test_operational.py` must ride the Phase 10
  checkpoint commit.
- Zero developer questions (ADV-10) — every design question resolved
  as a brief position. Block 4 acceptance remains the developer's at
  the Phases 10–12 boundary.
- pytest unchanged: 9.1.1; Python 3.12.3; stdlib-only dependencies
  (refused: any third-party package; any monitoring/CI/Docker/service
  tooling; any environment knob such as `HEALTH_FAST`; any sqlite
  schema change — `SCHEMA_VERSION` still exactly 1; no committed DB).
- Checkpoint hash: **8abe1ca** (full hash
  8abe1ca156a1048d8c1c6d7543bfe58359e51a78; `phase 10: health-check
  restructure to 3 runs, valve re-tune down, corruption and atomicity
  tests`; 2026-10-22 22:20 +0100, master; 10 files, +1199/−78; the
  git agent's pre-commit clean-env run: **155 passed in 68.76s** at
  load 0.47 — green, no commits on red; the docs agent then replaces
  PENDING in docs/ROADMAP.md with 8abe1ca and flips ROADMAP Phase 10
  `in progress` → `committed`, as in Phases 4–9.

## 2026-10-23 — Phase 11 (Forecast evaluation) — built, reviewed PASS (first pass); checkpoint PENDING

- Brief of record: `docs/briefs/phase-11.md` (452 lines incl. the C1–C10
  adjudication record; glass-architect, 2026-10-22/23). HANDOFF Part IX
  item 11 — *"Forecast evaluation — log loss, Brier, RPS against
  hand-computed values and baselines, calibration over many
  observations, idempotent evaluation records"* — delivered as the
  **evidence gate**: the first-ever scoring of the frozen,
  pre-registered walk-forward predictions (Phase 9's machinery)
  against realized results. **Milestone: the evaluated observation
  count went from exactly 0 to exactly 30 (primary) / 57 (secondary)
  for the first time**, with the 3 structural refusals excluded from
  every metric and counted in the 60 = 3 + 27 + 30 accounting. Scope
  anchor (Phase 8/10 precedent): Phase 11 is IX-11, **not** IX-12
  integration (Phase 12 CONSUMES these records, recomputing nothing)
  and **not** pipeline stage 10 (`app/improvement/` stays PLANNED);
  the phase is READ-ONLY over the frozen model, forecast, and backtest
  artifacts. **glass-quant was consulted** (mandatory; run at conductor
  top level, 2026-10-22): rulings **ADV-1–ADV-14 binding** (scored
  populations pinned pre-score; the exact metric forms — natural-log
  log loss with no ε-clamp, full-sum Brier, ½-scaled ordinal RPS with
  the scoreline variant rejected; 5 equal-width calibration bins with
  empty-bin honesty; the digest gate FIRST and the record-table
  decision; the amendment pre-declaration; side-by-side legality;
  vocabulary; golden-pin discipline; no CIs; the poison trio; runtime;
  out-of-scope — ZERO developer questions, none raised). Block table
  and the Block 1/2/3 acceptance rows verified untouched.
- **`docs/STATISTICAL-ASSUMPTIONS.md` §13 was AUTHORED PRE-BUILD**
  (2026-10-22, single appended hunk, before any `app/evaluation/` or
  `tests/test_evaluation.py` code existed — the §3/§7–§12 pre-build
  pattern; the reviewer's git-history checklist item (i) verified the
  authored-before-first-hunk position). §13 fixes the formulas, the
  populations (60 = 3+27+30; primary 30; secondary 57; refusals
  accounting-only), the 5-bin edges + pooling + empty-bin honesty, the
  draw aggregate, the ddof=0 overdispersion diagnostic, side-by-side
  legality (deltas/verdicts banned forever; noise-floor rationale
  §13/brief-only), the vocabulary rule, and the record contract —
  nothing chosen post-score. Flipped to implemented-and-tested at this
  DOCS step (status line + phase-end verification append; §§1–12
  untouched — single-hunk diff verified).
- Build: `app/evaluation/` **NEW** — a pure package, exactly four
  modules, **639 lines** (`__init__.py` 39, `metrics.py` 92,
  `calibration.py` 147, `evaluate.py` 361): the single public entry
  `evaluate_predictions(predictions, baselines, matches, *,
  run_digest, expected_run_digest)` with the **digest gate before any
  metric computes** (tampered digest → `ValueError`, zero metric
  calls), the re-established one-line natural-key join (explicit
  refusals on 0 and >1 matches), the deliberately duplicated flag
  predicate, population accounting, per-match contributions,
  `log_loss`/`brier`/`rps` (hard refusal, never a clamp, on zero
  probability on the realized outcome), the 5-bin calibration tables +
  draw aggregate + overdispersion diagnostic (descriptive only), the
  frozen result/record containers, and `EVALUATION_VERSION = 1`;
  imports exactly `{app.domain, app.forecasts, app.backtesting,
  dataclasses, hashlib, json, math, typing}` (AST-pinned; no
  `app.models`/`app.simulation` — the scoreline variant structurally
  cannot exist; no storage/HTTP). `app/storage/` **sanctioned bump**:
  `SCHEMA_VERSION` 1 → 2 (§11(d) executes), the write-once
  content-hashed no-clock `evaluations` table + immutability triggers,
  the write-only `insert_evaluation_record` (`__all__` 11 → 12 names);
  **read paths untouched** — `git diff 8abe1ca -- app/storage` =
  `forecasts_db.py` +97/−8 and `__init__.py` +2 (reviewer checklist
  (v) verified); no evaluation read API; no committed DB.
- Golden pins (ADV-10): golden metric literals pinned in
  `tests/test_evaluation.py` FIRST, from the first green run — the 12
  mean-metric literals ({model, baseline} × {log loss, Brier, RPS} ×
  {primary 30, secondary 57}), the calibration bin tables + dominant-
  share literals for both populations, both draw deficits, the
  smallest-component literal 0.12816022966803042, and ≥3 hand-computed
  single-prediction values with independent in-test arithmetic
  (−ln(0.55); Brier 0.38; RPS 0.11125 ≠ the unscaled 0.2225). **The
  golden values re-derived BIT-EXACT under three independent
  arithmetic implementations** (builder, tester + reviewer full
  independent re-derivations, conductor) — exact-pinning is free on a
  deterministic pipeline; re-derive on change, never widen.
- Adjudication record — **builder-proposed deviations C1–C10,
  architect-adjudicated 2026-10-23; NEVER developer rulings (no
  developer contact occurred — the builder's "user-ruled" labels were
  false and were corrected tree-wide, C6)**. The architect adjudicated
  each item empirically (import-graph probes, diff audits vs
  `8abe1ca`, a full clone-and-commit reproduction of criterion 8,
  a 178-passed suite run) and amended the brief in place wherever a
  brief defect was exposed (the Phase 9 A3' pattern). Headline: **C3**
  — the seven-entry `GOLDEN_PIN_FILES` variant including
  `tests/test_evaluation.py` was **clone-proven LATENT POST-COMMIT
  RED** (a new file diffs empty only while untracked; the moment the
  checkpoint commit tracks it, criterion 8 fails on its **779-line
  new-file diff** — reproduced read-only in a throwaway clone) →
  **reverted to the six-entry tuple**; post-commit green clone-verified
  by the builder AND the tester AND the reviewer, and the app/-excludes
  line verified green in the same probe. **C5f** — one sanctioned
  comment-only one-liner (`tests/test_evaluation.py:510`, 1 → 1 line,
  file stays 779; suite re-run green). **C6** — line-neutral comment
  hygiene across the amended files (per-file `wc -l` unchanged).
  **C8** — `tests/test_evaluation.py` shipped at **779 lines**,
  ACCEPTED as a declared deviation vs the ≤ ~620 projection (all 21
  declared tests present, none cut; precedent: phase4 835,
  backtesting 664). C1/C2/C4/C5/C7/C9/C10: brief-defect corrections
  (the forced `PACKAGE_APP_IMPORTS` hunk; the PURE six-set; the A9
  idempotent-`False` prose; the `__all__` count 11 → 12; the signature
  prose; the +23 suite arithmetic; the storage diff verification).
  Full record in the brief's adjudication section.
- Process record: **two server-restart interruptions occurred BEFORE
  any write this phase** (zero partial writes; the build restarted
  clean — the Phase 7 interruption precedent). Zero self-sanctioning
  beyond the adjudicated items; zero undeclared edits.
- Declared amendments A1–A10, exact actual figures (`wc -l`-verified
  at the docs step): **A1** `test_temporal_integrity.py` **452 → 464**
  (registry 6 → 7, census 4 → 5, byte-pin re-point `ea92667` →
  `8abe1ca` + rescoped `PRE_EXISTING_APP`, criterion-8 knob scan
  extended); **A2** `test_phase4_separation.py` **834 → 835**; **A3**
  `test_phase5_separation.py` **574 → 576** (incl. the C1-forced
  `app.storage` local-scan hunk); **A4** `test_phase6_separation.py`
  **510 → 513** (byte-pin drops `app/storage`); **A5**
  `test_phase7_separation.py` **443 → 448** (byte-pin drops
  `app/storage`; `SCHEMA_VERSION` pin → 2); **A6**
  `test_fixtures_and_hygiene.py` **626 → 629** (`app.evaluation` key
  14, `app.storage` value, PURE six-set); **A7**
  `test_backtesting.py` **653 → 664** (exactness block re-pointed;
  criterion-11 two-table/`SCHEMA_VERSION`-2 pins; the five-entry knob
  scan NOT extended — decision 12); **A8** `test_vocab_guards.py`
  **440 → 464** (the ONE `SCORING_EXEMPT_PREFIXES` exemption +
  both-direction boundary probes; `SCORING_ALLOWLIST` stays exactly
  one entry); **A9** `test_storage.py` **425 → 483** (the appended
  criterion-17 evaluations-table test); **A10** `test_operational.py`
  **409 → 410** (criterion 8 re-point + the C3 six-entry golden set +
  app/-excludes). New file **`tests/test_evaluation.py` 779 lines**
  (C8). Every legacy assertion retained in all ten amended files
  (strictly stronger, never a weakening).
- Suite: **178 passed** (= 155 + 23: 21 new-file tests + 1 storage test
  + 1 vocab boundary probe — C9 reconciliation) across every recorded
  execution, zero failed/errors/skipped/xfailed/xpassed. Clean-env ×2:
  **178 passed in 149.59s** and **178 passed in 146.96s** at the
  recorded loads. Offline lo-up ×2: **178 passed in 190.38s** and
  **178 passed in 182.99s**. Health script: exit 0, three inner runs
  **`172 passed, 6 deselected` ×2** (displayed runs 1–2; run 3
  silent), determinism **`OK:`** counts-only, skips/xfails `none`, pip
  clean ("No broken dependencies found."), all nine headers, inside
  the **untouched 800 s valve**. A post-revert clone verification ran
  the suite green at 178 post-commit (criterion 8 verified both pre-
  and post-commit — the C3 revert's positive proof). The 6 deselected
  inside script runs = the 3 health tests + the 3 `test_operational`
  source pins whose names contain `health_script` (the byte-pinned
  recursion guard; no check lost).
- Review history: tester verdict **PASS ×23** with a full independent
  re-derivation of the golden values (bit-exact) and recorded clean-env
  and offline executions; reviewer verdict **PASS (2026-10-23, FIRST
  pass)** with its own independent golden re-derivation (bit-exact) and
  the full DOCS checklist executed — §13's git-history position, the
  EVALUATION.md anti-inflation audit (every number a pinned test
  literal; S1–S4 verbatim), no quality-adjective claims in docs, the
  noise-floor rationale absent from EVALUATION.md, the storage diff =
  sanctioned only, amendment actuals vs `wc -l`, no
  skip/xfail/subsetting, and the IX-12 consumption note. Zero fix
  cycles — first pass, as in Phases 4–10.
- Docs (this step): `docs/EVALUATION.md` **CREATED** (six sections per
  brief decision 13 — purpose/anti-inflation; populations; formulas;
  results side by side with n + caveats; "what these numbers are not"
  carrying S1–S4 verbatim; provenance incl. the run digest, the two
  fixture-file sha256 values, `EVALUATION_VERSION = 1`, and the
  criterion map — every number a pinned test literal, cited inline).
  `docs/STATISTICAL-ASSUMPTIONS.md` §13 flipped to implemented-and-
  tested + phase-end verification append (§§1–12 byte-identical,
  single-hunk diff verified). `docs/KNOWN-LIMITATIONS.md` — intro
  flipped to Phase 11; new **Phase 11** section (12 items: the first
  evaluated n > 0 milestone with caveats; the duplicated flag
  predicate + its 27/30 count-pin guard; the tiny-n calibration loud
  caveat with the pinned ~81%/~80% dominant-bin shares and Phase 13
  registration; the draw deficit — negative on both populations,
  descriptive, opposite the §2f underprediction direction as
  measured; the overdispersion descriptive-only pin; no CIs;
  side-by-side legality banned forever; the retained `get_forecast`
  latent; `SCHEMA_VERSION` 2 + the write-only evaluations surface; the
  C1–C10 builder-proposed/architect-adjudicated record incl. C3 and
  C5f; the A1–A10 actuals incl. C8's 779; the brief's "No conftest.py
  exists" State-line inaccuracy — trivia, one clause); "Not yet
  applicable" refreshed to Phase 11 (**evaluation LEAVES the list**;
  stages 3 and 10 remain; prior n = 0 statements are historical and
  never rewritten). `docs/ROADMAP.md` — Phase 11 `in progress`,
  PENDING-hash convention (**block table byte-identical; rows 1–10 and
  the Block 1/2/3 acceptance rows untouched — the Block 3 acceptance
  row recorded 2026-10-22 rides this checkpoint commit unedited**).
  `README.md` (Phase 11 state, 178 tests, honest load-labeled
  run-time note, commit hashes through 8abe1ca). `docs/ARCHITECTURE.md`
  (evaluation IMPLEMENTED — four modules, 639 lines; `app/backtesting/`
  gains its first consumer; the `evaluations` table row and
  `SCHEMA_VERSION = 2`; stages 3 and 10 remain PLANNED; integration =
  Phase 12; test counts → 27 modules / 178 tests). `docs/PLAN.md` — §2
  `evaluation/` line planned → EXISTS (no SCHEMA_VERSION mention
  existed; nothing else changed). `docs/HEALTH-LOG.md` untouched by
  this agent (monitor-owned).
- **Dirty-docs riding note (the Phase 10 protocol records, flipped
  truthfully):** the three Phase 10 protocol records (docs/HEALTH-LOG.md,
  docs/PROGRESS-LOG.md, docs/ROADMAP.md — appended/flipped at the
  Phase 10 docs step) never landed in 8abe1ca; the monitor's WARN
  carried through its post-checkpoint sweep. They ride **this**
  Phase 11 checkpoint commit, together with §13's pre-build append
  (uncommitted build-step hunk) and all of this phase's docs — the
  standard riding note, Phases 1–10 pattern.
- Zero developer questions (ADV-14) — every design question resolved
  by the quant rulings or the brief. Block 4 acceptance remains the
  developer's at the Phases 10–12 boundary.
- pytest unchanged: 9.1.1; Python 3.12.3; stdlib-only dependencies
  (refused: any third-party package; numpy/pandas/scipy or any
  numeric/ML stack; plotting; any API change; any second schema
  surface beyond the one declared table; any environment knob).
  `SCHEMA_VERSION` now exactly **2** (the §11(d) sanction); no
  committed DB.
- Checkpoint hash: **PENDING** — the git agent makes the checkpoint
  commit (on green tests; the docs-step suite of record: 178 passed,
  clean-env ×2 at 149.59s/146.96s); this agent then replaces PENDING
  in docs/ROADMAP.md and docs/PROGRESS-LOG.md with the recorded hash
  and flips ROADMAP Phase 11 `in progress` → `committed`, as in
  Phases 4–10.
