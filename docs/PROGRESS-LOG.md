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

## 2026-10-16 — Phase 2 (Domain and data) — built, reviewed PASS; checkpoint PENDING

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
- Checkpoint hash: **PENDING** — to be recorded by glass-git at the
  Phase 2 checkpoint commit. That commit must also carry the three
  uncommitted Phase-1 protocol records (docs/HEALTH-LOG.md,
  docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor finding 1 from the
  Phase 1 sweep) plus this entry and the Phase 2 DOCS-step files; ROADMAP
  Phase 2 flips `in progress` → `committed` with the hash afterward.
