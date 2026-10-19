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

## 2026-10-19 — Phase 6 (Feature engine) — built, reviewed PASS (first pass); checkpoint PENDING

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
- Checkpoint hash: **PENDING** — glass-git records the real hash at
  the Phase 6 checkpoint (immediately after this docs step); PENDING
  is then replaced with that hash here and in docs/ROADMAP.md, and
  ROADMAP Phase 6 `in progress` → `committed` flips with it.
