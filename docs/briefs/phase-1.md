# PHASE 1 BRIEF — FOUNDATION

Status: proposed (2026-10-13, glass-architect). Per docs/ROADMAP.md this
is Block 1, Phase 1. Phases 2+ are not planned until this phase passes
review, is committed, and passes the monitor sweep.

## Objective

Establish the Foundation per HANDOFF Part IX item 1 and Part VI: an
isolated local venv, pytest wiring, the `app/` package as the root of the
mandated module separation, a green offline local test loop, and
`scripts/health-check.sh` executing fully end to end — so every later
phase is provable by real commands on this machine. This phase creates no
calculations, no data, no subpackages, and no API.

## Environment facts (probed 2026-10-13, before build)

- System python3 = 3.12.3 at /usr/bin/python3, with NO pip, NO ensurepip,
  NO pytest. `python3 -m venv .venv` would create a venv without pip.
- `uv` is installed at ~/.local/bin/uv. Network to pypi is reachable
  right now (one-time install possible, offline thereafter).
- `scripts/health-check.sh` early-exits while `.venv/bin/python` is
  absent; after this phase it must run fully.

## Files and directories to create or modify

Create:
- `.venv/` — isolated venv at repo root (bootstrap method: open question 1).
  Must contain pip and pytest. Already covered by `.gitignore`.
- `app/__init__.py` — package root marking the engine; a short docstring
  only, no logic.
- `pytest.ini` — content:
      [pytest]
      testpaths = tests
      addopts = --strict-markers
  (--strict-markers makes undeclared markers fail loudly; known markers
  like skip/xfail remain governed by the constitution's prohibition.)
- `conftest.py` (repo root) — empty except an explanatory comment: its
  presence makes the repo root importable so `import app` works under both
  bare `pytest` and `python -m pytest`.
- `tests/` — test directory.
- `tests/test_foundation.py` — tests for criteria 1–6.
- `tests/test_health_script.py` — tests for criteria 7–9, sharing ONE
  module-scoped subprocess run of the health script (recursion-safe per
  open question 2; timeout 120 s; clean environment; cwd = repo root).

Modify (only if open question 2 is approved):
- `scripts/health-check.sh` — exactly one functional change: near the top,
  after PY is set, add:
      # Recursion guard: the health script's own pytest runs must not
      # execute the tests that spawn this script. They run in the direct
      # suite instead (pytest, from the repo root).
      export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-k 'not health_script'"
  No other change to the script.

Do not create or modify: README or docs content (the DOCS step of the
phase loop handles those), any `app/` subpackage, data/, fixtures/,
requirements/pyproject files, CI configs, linters, or Docker anything.

## Dependencies

- pytest — justification: the constitution mandates a pytest test loop and
  `scripts/health-check.sh` invokes `python -m pytest`. Unpinned latest at
  install time; exact version recorded in PROGRESS-LOG (open question 3).
- pip (inside .venv) — justification: the health script runs
  `python -m pip check`; the venv must carry its own package metadata.
- uv — justification: bootstrap installer only, because this machine's
  system Python cannot install anything (no ensurepip/pip). One-time use;
  nothing in the engine imports it; requires developer approval
  (open question 1).
- Nothing else. No FastAPI, no coverage plugin, no linters, no numeric
  stack. Default is none.

## Acceptance criteria

Criteria 1–9 map 1:1 to pytest test functions. Criterion 10 is the
suite-level gate, verified by recorded suite executions (test suite
execution, tester + reviewer + monitor) — a test cannot assert its own
suite's greenness without circularity, so this one is verified by real
pasted command output three times over.

1. `tests/test_foundation.py::test_venv_exists_and_is_ignored` —
   `.venv/bin/python` exists at the repo root and reports Python >= 3.10,
   and `.gitignore` contains an entry for `.venv/`.
2. `tests/test_foundation.py::test_pip_available_in_venv` —
   `.venv/bin/python -m pip --version` exits 0 (needed by the health
   script's pip check).
3. `tests/test_foundation.py::test_pytest_installed_in_venv` —
   `.venv/bin/python -m pytest --version` exits 0 and reports a pytest
   version.
4. `tests/test_foundation.py::test_app_package_importable` —
   `.venv/bin/python -c "import app; print(app.__name__)"` from the repo
   root exits 0 and prints `app`.
5. `tests/test_foundation.py::test_pytest_wiring_both_invocations` —
   from the repo root, `.venv/bin/python -m pytest --collect-only -q` and
   `.venv/bin/pytest --collect-only -q` (run with a cleaned environment,
   with any inherited PYTEST_ADDOPTS removed) both exit 0 and yield
   identical, non-empty sets of test node IDs. `--collect-only` is used so
   this test never recursively executes the suite.
6. `tests/test_foundation.py::test_app_compiles` —
   `.venv/bin/python -m compileall -q app` exits 0.
7. `tests/test_health_script.py::test_health_script_runs_to_completion` —
   one module-scoped `bash scripts/health-check.sh` subprocess exits 0,
   its output does NOT contain "There is nothing to check yet", and it
   DOES contain every section header: "last commit", "working tree",
   "compile", "pytest run 1", "pytest run 2", "skips/xfails",
   "determinism comparison", "pip check", "five largest .py files".
8. `tests/test_health_script.py::test_health_script_determinism_ok` — the
   same captured output contains a determinism line matching `^OK:` and
   contains no `MISMATCH`.
9. `tests/test_health_script.py::test_health_script_no_skips_no_broken_deps`
   — the same captured output's skips/xfails section reports `none`, and
   the pip check section reports "No broken requirements found."
10. Suite gate (recorded execution) — `.venv/bin/python -m pytest -q` from
    the repo root reports 0 failed, 0 errors, 0 skipped, 0 xfailed,
    0 xpasseD. Executed and pasted by the tester; executed independently
    (twice) by the reviewer; re-executed by the monitor via the health
    script. No test in the suite may use skip or xfail.

Note for criteria 7–9 (if open question 2 is approved): the health
script's five pytest invocations deselect `tests/test_health_script.py`
via the PYTEST_ADDOPTS guard, so the nested suite cannot re-spawn the
script; the health tests execute in every direct `pytest` run. If
open question 2 is declined, criteria 7–9 are verified by one direct
`bash scripts/health-check.sh` execution whose full output is pasted in
the phase report, and no test spawns the script.

## Out of scope

- Any README or documentation content changes (handled by the DOCS step).
- Any `app/` subpackages (domain/, models/, …) — their phases create them.
- data/ and fixtures/ directories.
- FastAPI or any API surface.
- Version-pinning files (requirements*.txt, pyproject) unless requested.
- CI configuration, coverage measurement, linters, formatters, Docker.
- Any change to `scripts/health-check.sh` beyond the single recursion
  guard (if approved).
- Planning or building Phase 2 (block mode: Phase 2 is not planned until
  Phase 1 passes review, commits, and the monitor sweeps it).

## Risks

- Environment bootstrap: the standard venv+pip flow is impossible on this
  machine; the chosen bootstrap path is an open question. If all options
  were declined (e.g., no sudo and no uv), the loop would be blocked —
  surfaced now, not discovered mid-build.
- Recursion and cost: the health test spawns the health script, which runs
  the suite five times internally — about 6x suite cost per full run while
  the health test exists. Harmless at Phase 1 scale (suite ~ms); if it
  becomes a bottleneck in a later phase, that phase's brief must re-scope
  the mechanism — never skip or weaken the test.
- Guard scope: the PYTEST_ADDOPTS export must live only inside
  `scripts/health-check.sh` (its own process); the reviewer must verify a
  direct `pytest` run still executes the health tests (criterion 5
  asserts direct collection includes them).
- Determinism: the suite itself must stay free of wall-clock and random
  dependence so the monitor's double-run comparison remains OK as the
  suite grows.
- Overengineering: the temptation to pre-create all ten subpackages and
  config machinery is explicitly resisted; structure is declared in the
  plan but instantiated phase by phase.
- Data quality / leakage: not exercised this phase (no data, no
  calculations); tests must still be hermetic (temp dirs, no shared
  mutable state) so later phases inherit good hygiene.

## Open questions for the developer

1. Bootstrap path (blocking): this machine's Python has no pip and no
   ensurepip, so `python3 -m venv .venv && pip install pytest` cannot work.
   Which do you approve?
   a. (Recommended) stdlib `python3 -m venv --without-pip .venv`, then use
      the already-installed `uv` to install `pip` and `pytest` into it
      (one-time network use; pypi is reachable now; the engine stays
      offline afterwards; uv is never imported by any code).
   b. `sudo apt install python3.12-venv python3-pip`, then the classic
      flow (requires sudo and apt).
   c. Download and run get-pip.py, then classic flow (network-fetched
      script; least auditable).
2. Health-script recursion guard: approve the single
   `export PYTEST_ADDOPTS="-k 'not health_script'"` line (with comment) in
   `scripts/health-check.sh` so the script's own pytest runs cannot re-run
   the tests that spawn it, making criteria 7–9 pytest-testable? If
   declined, criteria 7–9 are verified by direct invocation output only.
3. pytest versioning: OK to install the latest pytest unpinned and record
   the exact installed version in docs/PROGRESS-LOG.md (no pinning file),
   revisiting pinning only if a future phase shows it is needed?
