# Sports Looking Glass

A deterministic statistical future-analysis engine for football
(soccer). It takes historical match data, validates it, extracts
chronological features, fits statistical models, produces forecast
probability distributions, explores bounded scenarios, supports decision
analysis, and evaluates its own forecasts against what actually happened —
strictly in chronological order. It is a research and decision-analysis
system: it estimates, it never promises, and it never places or assists
bets.

Reconstructed from documentation after the original repository was lost.
The historical counts of the lost project (276 tests, 380 matches) are
history, never the current state of this repository.

## Current state

**Phase 2 (Domain and data): built and reviewed (PASS, after 3 fix
cycles); checkpoint pending.** The domain layer exists:
`app/domain/` (immutable models, deduplicating match collection,
canonical serialization), `app/ingestion/` (OpenFootball-format JSON
ingestion from local fixtures with provenance and idempotent imports),
`app/validation/` (defect reports — defects are reported, never guessed
around), and `fixtures/openfootball/` (small hand-authored synthetic
fixtures with fictional teams — see `docs/DATA-SOURCES.md`). No
statistics, no forecasts, no storage, no API yet (by design; see
`docs/briefs/phase-2.md` and `docs/PLAN.md`). Phase 1 (Foundation) is
committed at **45ed27e**. The local, offline, deterministic test loop is
operational: 24 tests, all green. See `docs/ROADMAP.md` for phase status
and `docs/PROGRESS-LOG.md` for the record.

## Requirements

- Linux with a Python >= 3.10 interpreter (developed and verified on
  Python 3.12.3).
- Bash for the health script.
- Nothing else. No Docker, no services, no cloud, no API keys. After the
  one-time venv bootstrap below, everything runs offline.

## Setup

The repository already contains a bootstrapped `.venv/` at the root
(git-ignored). If it is present, there is nothing to do — skip to
"Running the tests".

Provenance of the existing `.venv/` (one-time, 2026-10-16): this machine's
system Python has no pip and no ensurepip, so the venv was created with
`python3 -m venv --without-pip .venv`, and `pip` plus `pytest` were
installed into it with the machine's preinstalled `uv` — the
developer-approved bootstrap path (option a, open question 1 of
`docs/briefs/phase-1.md`). Network was touched only for that single
install; `uv` is a bootstrap tool only, never imported by any project
code, and not a product dependency. Installed versions are recorded in
`docs/PROGRESS-LOG.md` (currently: pip 26.2.1, pytest 9.1.1, installed
unpinned by developer decision — see `docs/KNOWN-LIMITATIONS.md`).

If `.venv/` is ever destroyed, recreate it by the same approved path:
`python3 -m venv --without-pip .venv`, then use `uv` once to install `pip`
and `pytest` into it. The acceptance tests require only that
`.venv/bin/python` is >= 3.10 with working pip and pytest
(`tests/test_foundation.py`, criteria 1–3).

## Running the tests

From the repository root:

```sh
.venv/bin/python -m pytest -q
```

Verified output (2026-10-16): `24 passed` (Phase 2 docs run: 48.96 s
under concurrent load; recorded runs this phase range roughly 13–60 s
depending on load — the health-script test dominates, see
`docs/KNOWN-LIMITATIONS.md`). Zero skips, zero xfails — no test in this
suite may use skip or xfail (constitution).

## Running the health check

From the repository root:

```sh
bash scripts/health-check.sh
```

Verified on 2026-10-16: exit code 0; compile clean; determinism
comparison `OK`; skips/xfails `none`; `pip check` clean ("No broken
requirements found."). Its own pytest invocations report `21 passed, 3 deselected`:
the script exports a `PYTEST_ADDOPTS` recursion guard so its internal
suite runs never re-execute the tests that spawn the script; those health
tests run in the direct suite above. Expect roughly half a minute to a
minute — the script runs the non-health suite five times internally
(observed 47.5 s total under concurrent load, 2026-10-16).

Important: by design (no `set -e`, so one failing check cannot abort the
sweep) the health script prints failures but still exits 0. It is a
monitoring report, **not** the pass/fail gate. The gate is a direct suite
run of `.venv/bin/python -m pytest -q` (Phase 1 criterion 10). See
`docs/KNOWN-LIMITATIONS.md`.

## Repository layout (what exists now)

    lookingglass/
    ├── app/                     # the engine; Phase 2: domain/, ingestion/,
    │                            # validation/ (+ Phase 1 __init__.py)
    ├── fixtures/                # synthetic OpenFootball-shaped JSON (Phase 2)
    ├── tests/                   # 24 tests, 1:1 with acceptance criteria
    ├── scripts/health-check.sh  # mechanical health sweep
    ├── pytest.ini               # testpaths=tests, --strict-markers
    ├── conftest.py              # repo root importability for bare pytest
    ├── .venv/                   # local venv (git-ignored)
    ├── .opencode/               # agent suite and constitution
    └── docs/                    # handoff, roadmap, plan, logs, briefs,
                                 # DATA-SOURCES, KNOWN-LIMITATIONS

The much larger target structure (ten separated pipeline modules) is
declared in `docs/ARCHITECTURE.md` and `docs/PLAN.md`, and is instantiated
phase by phase — never speculatively.

## Documentation

- `docs/HANDOFF.md` — the full brief of record.
- `.opencode/rule/lookingglass-constitution.md` — binding rules.
- `docs/ROADMAP.md` — phase status.
- `docs/ARCHITECTURE.md` — pipeline stages and module map (target marked).
- `docs/DATA-SOURCES.md` — data formats, fixture provenance, licenses.
- `docs/PROGRESS-LOG.md` — what was built, real test counts, checkpoint
  hashes.
- `docs/KNOWN-LIMITATIONS.md` — the honest list, updated every phase.
- `docs/briefs/` — per-phase briefs.

## Ground rules (non-negotiable)

No AI/LLM/generative dependency at runtime; zero cost and fully offline;
no betting functionality of any kind; missing data is reported, never
fabricated; determinism is required (seeded RNGs only, no wall clock in
calculations); tests are never weakened, deleted, skipped, or xfailed to
make a phase pass.
