# HEALTH LOG

Append-only monitoring history. One entry per sweep: phase, date, checkpoint
hash, test counts, runtime, verdict, findings. Never edit or delete previous
entries.

No sweeps recorded yet.

## 2026-10-13 — pre-Phase-1 baseline

- Phase: none (pre-Phase-1 baseline sweep)
- Date: 2026-10-13
- Checkpoint: 866eba5 (chore: bootstrap Looking Glass agent suite, block-cadence conductor, monitor)
- Tests: 0 passed / 0 failed / 0 skipped / 0 xfailed — suite could not run: no .venv, no tests/; health-check.sh exited early: "There is nothing to check yet: .venv/bin/python does not exist. This is expected before Phase 1 completes."
- Runtime: 0.069s (full health-check.sh invocation)
- Verdict: OK
- Findings: none. Working tree clean (git status --porcelain empty, exit 0); compile N/A (app/ does not exist); determinism N/A (no suite); skips/xfails 0; warnings none (no previous entry to compare); no .py source files (none over 400 lines); pip check N/A (no .venv; system python3 3.12.3 reports "No module named pip").

## 2026-10-16 — Phase 1 (Foundation) post-checkpoint sweep

- Phase: 1 (Foundation)
- Date: 2026-10-16
- Checkpoint: 45ed27e (phase 1: foundation venv, pytest wiring, app package, health-check loop; master)
- Tests: direct `.venv/bin/python -m pytest -q` → 9 collected, 9 passed / 0 failed / 0 skipped / 0 xfailed; four direct runs identical outcomes (13.57s, 13.20s, 15.02s, 14.77s). health-check.sh internal runs (6 passed, 3 deselected via PYTEST_ADDOPTS recursion guard) ×2 identical; determinism section "OK: 6 passed, 3 deselected"; skips/xfails section "none" (full-output run `-rA` shows 9× PASSED only).
- Runtime: full health-check.sh invocation 12.926s (real); direct suite 13.20–15.02s. Baseline 0.069s was the pre-venv early exit — growth is structural (suite now exists), no prior full-sweep runtime to compare.
- Verdict: WARN
- Findings:
  1. Rule 1 (tree clean): `git status --porcelain` → ` M docs/PROGRESS-LOG.md` and ` M docs/ROADMAP.md`. Diffs verified docs-only: PROGRESS-LOG records checkpoint hash 45ed27e (recorded after the commit per protocol step 6, necessarily uncommitted); ROADMAP flips Phase 1 `in progress` → `committed`, citing 45ed27e. Both are protocol-predictable post-commit records, no code. Hygiene: they must land in a subsequent commit, else every future sweep sees a dirty tree. `git status --ignored` shows only `.venv/`, `__pycache__/`, `app/__pycache__/`, `tests/__pycache__/`, `.pytest_cache/` — all listed in .gitignore; no stray or ignored artifacts otherwise.
  2. Observation (docs accuracy, not a failure): docs/KNOWN-LIMITATIONS.md item 2 cites "~85 s of that margin" for the health-script test's 120 s timeout; not reproduced — the shared script spawn dominates a 13.2–15.0 s suite (~105 s margin observed), and docs/PROGRESS-LOG.md itself records 15.78s pre-commit. The 85 s figure appears stale or cold-cache.
- All other rules pass: compile clean (`compileall -q app` empty output); determinism identical (script "OK: 6 passed, 3 deselected", direct runs all "9 passed"); skips/xfails 0 (grep → "none"); warnings 0 vs baseline 0 (no warnings summary in pytest output); largest .py 130 lines (tests/test_foundation.py) under 400; pip check → "No broken requirements found."

## 2026-10-16 — Phase 2 (Domain and data) post-checkpoint sweep

- Phase: 2 (Domain and data)
- Date: 2026-10-16
- Checkpoint: 1c5067b (phase 2: domain models, OpenFootball ingestion, validation, synthetic fixtures; master)
- Tests: direct `.venv/bin/python -m pytest -q` ×3 → 24 collected, 24 passed / 0 failed / 0 skipped / 0 xfailed, identical outcomes every run (48.02s, 50.77s, 45.58s). health-check.sh internal runs (21 passed, 3 deselected via PYTEST_ADDOPTS recursion guard) ×4 identical; determinism section "OK: 21 passed, 3 deselected"; skips/xfails section "none" (full-output run `-rA` shows 24× PASSED only, no SKIPPED/XFAIL/XPASS).
- Runtime: direct suite 45.58–50.77s (Phase 1: 13.2–15.0s — growth structural: 15 new tests; slowest is tests/test_health_script.py::test_health_script_runs_to_completion at 39.83s setup, which spawns health-check.sh). No prior full-sweep script runtime recorded for a like-for-like comparison.
- Verdict: WARN
- Findings:
  1. Rule 1 (tree clean): `git status --porcelain` → ` M docs/PROGRESS-LOG.md` and ` M docs/ROADMAP.md` only. Diffs verified docs-only and protocol-predictable (same pattern as Phase 1 finding 1): PROGRESS-LOG records checkpoint hash 1c5067b (step 6, recorded after the commit, necessarily uncommitted); ROADMAP flips Phase 2 `in progress` → `committed` citing 1c5067b (sanctioned post-commit status flip). No code, no untracked files; `git status --ignored` shows only .venv/, __pycache__/ (×5), .pytest_cache/ — all gitignored. Hygiene: both must land in a subsequent commit, else every future sweep sees a dirty tree. Phase 1 finding 1's remediation verified: the three Phase-1 protocol records rode 1c5067b (`git show --stat 1c5067b` → docs/HEALTH-LOG.md +13, docs/PROGRESS-LOG.md, docs/ROADMAP.md all in the commit).
  2. Rule 6 (files > ~400 lines): tests/test_fixtures_and_hygiene.py is 611 lines (largest app source app/validation/checks.py 246). Flagged per rule; mitigating context: it is a test file whose size tracks the fixture-hygiene matrix (wall-clock/env sets are reviewer-audited enumerations per docs/KNOWN-LIMITATIONS.md), not sprawl in production code.
  3. Phase 1 observation 2 (stale "~85 s" figure in KNOWN-LIMITATIONS) verified resolved: current item 2 explicitly supersedes the earlier figure and cites a revised remaining margin of roughly 72–107 s (~2.5x headroom), consistent with the ~40 s health-script-test setup observed here.
- All other rules pass: compile clean (`compileall -q app` empty output); determinism identical (4 internal + 3 direct runs, same outcomes; timings vary within 45.6–50.8s, allowed); skips/xfails 0; warnings 0 vs 0 previous (no warnings summary in any run, `-rA` grep count 0); pip check → "No broken requirements found."

## 2026-10-17 — Phase 3 (Core statistics) post-checkpoint sweep

- Phase: 3 (Core statistics)
- Date: 2026-10-17
- Checkpoint: a5d7f56 (phase 3: poisson core statistics, mle fitter with internal cutoff, scoreline matrices; master, 2026-10-17 01:06:22 +0100; full hash a5d7f56e8e1ecfb274eddf0f53cab0383f90d0d4; 17 files, +2727/−77)
- Tests: direct `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q -rA` → 37 collected, 37 passed / 0 failed / 0 skipped / 0 xfailed in 15.53s; health-check.sh internal runs (34 passed, 3 deselected via PYTEST_ADDOPTS recursion guard) ×2 identical (2.97s, 2.11s); determinism section "OK: 34 passed, 3 deselected"; skips/xfails section "none" (`-rA` full output greps SKIPPED/XFAIL/XPASS: none, 37× PASSED only).
- Runtime: direct suite 15.53s (Phase 2: 45.58–50.77s — decrease despite +13 tests; the Phase 2 ~40 s health-script-test setup no longer dominates); full health-check.sh invocation well under one minute.
- Verdict: WARN
- Findings:
  1. Rule 1 (tree clean): `git status --porcelain` → ` M docs/PROGRESS-LOG.md` and ` M docs/ROADMAP.md` only; nothing else dirty, no untracked files. Diffs inspected line-by-line: docs-only and protocol-predictable (same pattern as Phases 1–2 finding 1): PROGRESS-LOG replaces "checkpoint PENDING" with the recorded hash a5d7f56 (protocol step 6, recorded after the commit, necessarily uncommitted); ROADMAP flips Phase 3 `in progress` → `committed` citing a5d7f56 (sanctioned post-commit status flip). `git status --ignored` shows only .venv/, __pycache__/ (×7), .pytest_cache/ — all gitignored; no strays. Remediation pattern continued: `git show --stat a5d7f56` shows the commit carries docs/HEALTH-LOG.md +14, docs/PROGRESS-LOG.md, docs/ROADMAP.md. Hygiene: both dirty docs must land in a subsequent commit, else every future sweep sees a dirty tree.
  2. Rule 6 (carried finding 2 from Phase 2): tests/test_fixtures_and_hygiene.py is 612 lines (was 611). Growth is exactly the +1 sanctioned and declared by docs/briefs/phase-3.md AMENDMENT A1 ("Net growth: +1 line"): `git show --stat a5d7f56` → `tests/test_fixtures_and_hygiene.py | 1 +`, the ALLOWED_APP_IMPORTS["app.models"] dictionary-coverage entry. Largest app source app/models/poisson.py 365 lines — under 400. Carried finding, no new sprawl.
  3. Hash-accuracy note (docs accuracy, not a failure): the conductor initially carried hash 3f88ab7, which never existed (`git cat-file -t 3f88ab7` → "fatal: Not a valid object name 3f88ab7", exit 128); glass-docs verified the real commit a5d7f56 against message/stats and recorded it — the working-tree PROGRESS-LOG/ROADMAP diffs above carry the corrected a5d7f56. Verified: `git log -1` → a5d7f56e8e1ecfb274eddf0f53cab0383f90d0d4, message matches the checkpoint description.
- All other rules pass: compile clean (`compileall -q app` empty output, app/models included); determinism identical (2 script-internal + script determinism pair + 1 direct run, all same outcomes; timing spread 2.11–2.97s internal, allowed); skips/xfails 0; warnings 0 vs 0 previous (full `-rA` output greped case-insensitively for warning|error|skip|xfail|xpass — only a PASSED test whose name contains "no_skips"; no warnings summary); pip check → "No broken requirements found."

## 2026-10-17 — Phase 4 (Simulation and scenarios) post-checkpoint sweep

- Phase: 4 (Simulation and scenarios)
- Date: 2026-10-17
- Checkpoint: f208e43 (phase 4: seeded simulation, bounded hypothetical scenarios, scoreline matrix sampling; master, 2026-10-17 20:21 +0100; full hash f208e43ff2ec9470f12a72d98ce6e65c53b64b1b; 21 files, +3367/−124)
- Tests: health-check.sh internal runs (54 passed, 3 deselected via PYTEST_ADDOPTS recursion guard) ×2 identical (11.04s, 10.97s); determinism section "OK: 54 passed, 3 deselected"; skips/xfails section "none"; direct `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q -rA` → 57 collected, 57 passed / 0 failed / 0 skipped / 0 xfailed in 79.96s (57 = 54 + 3 health_script tests, deselected only inside the script by the recursion guard — by design, not skips).
- Runtime: script-internal ~11.0s per run (Phase 3: 2.11–2.97s); direct suite 79.96s (Phase 3: 15.53s) — growth structural (+17 tests, three new large test files); PROGRESS-LOG records 73.05s for the pre-commit clean-env 57-passed run. Interpreted against the A2 standing 300s health-test valve, current margins are healthy (~6x at observed direct-suite size). The Phase-4 trip (`54 passed, 3 errors`, subprocess.TimeoutExpired ×3 at the then-120s timeout, under external load ~10) is resolved: A2 re-scoped the timeout 120→300s with zero assertions changed; verified recorded in docs/KNOWN-LIMITATIONS.md item 2 update and docs/briefs/phase-4.md; suite now green (0 errors).
- Verdict: WARN
- Findings:
  1. Rule 1 (carried Phases 1–3): `git status --porcelain` → ` M docs/PROGRESS-LOG.md` and ` M docs/ROADMAP.md` only; diffs verified docs-only and protocol-predictable (PROGRESS-LOG replaces "checkpoint PENDING" with f208e43; ROADMAP flips Phase 4 `in progress` → `committed` citing f208e43). `git status --ignored` filtered shows no strays. Remediation pattern continued: `git show --stat f208e43` → commit carries docs/HEALTH-LOG.md +14. Hygiene: both dirty docs must land in a subsequent commit.
  2. Rule 6 (carried): tests/test_fixtures_and_hygiene.py is 614 lines (was 612) — exactly the +2 declared by AMENDMENT A1 (`git show --stat f208e43` → `tests/test_fixtures_and_hygiene.py | 2 +`). Carried finding, no undeclared growth.
  3. Rule 6 (NEW): three new test files exceed ~400 lines — tests/test_phase4_separation.py 826 (now the repo's largest file), tests/test_scenarios.py 562, tests/test_simulation.py 439. Mitigating: test files, not production code; largest app source app/models/poisson.py 365 and new app/simulation/simulate.py 207 are both under 400 — no app sprawl.
- All other rules pass: compile clean (`compileall -q app` empty output); determinism identical (2 script-internal + script determinism pair + 1 direct run, same outcomes); skips/xfails 0 (grep → "none", `-rA` full output PASSED-only); warnings 0 vs 0 previous (no warnings summary); pip check → "No broken requirements found."

## 2026-10-18 — Phase 5 (Forecasts and API) post-checkpoint sweep

- Phase: 5 (Forecasts and API)
- Date: 2026-10-18
- Checkpoint: 44b43ea (phase 5: forecast snapshots, write-once storage, read-only localhost api; master, 2026-10-18 06:55 +0100; full hash 44b43ea951fe59db95994da9a34c2ad086139cf8; 28 files, +3935/−130)
- Tests: health-check.sh internal runs (80 passed, 3 deselected via PYTEST_ADDOPTS recursion guard) ×2 identical (10.20s, 9.99s); determinism section "OK: 80 passed, 3 deselected"; skips/xfails section "none"; direct `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q -rA` → 83 collected, 83 passed / 0 failed / 0 skipped / 0 xfailed in 66.08s (83 = 80 + 3 health_script tests deselected only inside the script by the recursion guard — by design, not skips). Committed PROGRESS-LOG records 83 passed in 64.57s for the pre-commit clean-env run.
- Runtime: script-internal 9.99–10.20s per run (Phase 4: 10.97–11.04s — flat despite +26 internal tests); direct suite 66.08s (Phase 4: 79.96s — down); full health-check.sh invocation 54.883s real (script makes 5 internal pytest runs × ~10s + overhead). Interpreted against the standing A2 300s health-test valve: the health-script test spawns the full script (~55s observed) — margin ~5.5× (245s headroom), healthy.
- Verdict: WARN
- Findings:
  1. Rule 1 (carried Phases 1–4): `git status --porcelain` → ` M docs/PROGRESS-LOG.md` and ` M docs/ROADMAP.md` only — exactly the two predicted post-commit protocol records, nothing else dirty. Diffs inspected in full: docs-only and protocol-predictable (PROGRESS-LOG replaces "checkpoint PENDING" with 44b43ea + full hash + file stats + pre-commit run figure; ROADMAP flips Phase 5 `in progress` → `committed` citing 44b43ea). No untracked strays; `git status --ignored` shows only .venv/, .pytest_cache/, __pycache__/ (×12) — all gitignored. Remediation pattern continued: `git show --stat 44b43ea` → the commit carries docs/HEALTH-LOG.md +14 (the Phase 4 sweep entry). Hygiene: both dirty docs must land in a subsequent commit, else every future sweep sees a dirty tree.
  2. Rule 6 (carried; declared, not drift): tests/test_fixtures_and_hygiene.py 623 (was 614) — the +9 verified against `git show 44b43ea -- tests/test_fixtures_and_hygiene.py` as exactly AMENDMENT A1 (+3 ALLOWED_APP_IMPORTS entries) + A2 (BANNED_IMPORT_EXCEPTIONS map + 1-line scan-condition clause, net 0); no check deleted or relaxed beyond the declared A2 exception. tests/test_phase4_separation.py 831 (was 826) — exactly AMENDMENT A3's declared +5 (comment +2 net, `len==7`→`10`, +3 key-set entries); diff contains no deleted assertion (brief A3: "Net: 826 → 831 lines (+5); diff contains no deletions of assertions" — verified). tests/test_scenarios.py 562 and tests/test_simulation.py 439 unchanged, as the brief promises.
  3. Rule 6 (NEW): three new test files exceed ~400 lines — tests/test_phase5_separation.py 571, tests/test_storage.py 425, tests/test_forecasts.py 409 (tests/test_api.py 359 under). Mitigating: test files, not production code; app/ stays under control — largest app source app/models/poisson.py 365 (unchanged), new app/storage/forecasts_db.py 339 and app/api/server.py 186 both under 400.
  4. Observation (process incident, recorded and closed before review — not a sweep failure, logged because it bears on trust in declarations this sweep relies on): the builder's in-code comments initially attributed A5 and the criterion-8 erratum to a "developer decision / sanctioned correction of 2026-10-17" not verifiable from repo state; the architect's ruling caught and corrected the attribution to architect-ruling before review. Verified: committed PROGRESS-LOG at 44b43ea carries "Attribution honesty incident (recorded)"; the corrected attribution rides the commit (app/api/server.py:14 "AMENDMENT A5 architect ruling 2026-10-17"); remaining `developer decision` citations in app/ (spec.py, scoreline.py, api/__init__.py) were spot-checked and reference genuine Phase 3–5 developer/D-type decisions, not A5/erratum.
- All other rules pass: compile clean (`compileall -q app` → "COMPILE_OK", empty output); determinism identical (2 script-internal + script determinism pair + 1 direct run, same outcomes; internal timing spread 9.99–10.20s, allowed); skips/xfails 0 (script "none", direct `-rA` PASSED-only, 83×); warnings 0 vs 0 previous (no warnings summary in any run); pip check → "No broken requirements found."; rule 7 runtime trend healthy — no sharp growth (internal per-run flat, direct suite down despite +26 tests).
