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

## 2026-10-16 — Phase 3 (Core statistics) — built, reviewed PASS; checkpoint PENDING

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
- Checkpoint hash: **PENDING** — no hash invented; glass-git records
  the real hash at the Phase 3 checkpoint, then the docs agent replaces
  PENDING here and in docs/ROADMAP.md and flips ROADMAP Phase 3
  `in progress` → `committed`. The checkpoint carries the three
  protocol records (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md,
  docs/ROADMAP.md — monitor finding 1, carried from Phases 1–2
  sweeps), the A1-declared +1 line in tests/test_fixtures_and_hygiene.py,
  and the Phase 3 DOCS-step files (brief, STATISTICAL-ASSUMPTIONS,
  KNOWN-LIMITATIONS, ARCHITECTURE, README).
