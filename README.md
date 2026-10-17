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

**Phase 3 (Core statistics): built and reviewed (PASS, after 1 fix
cycle); checkpoint pending.** Pipeline stage 5 exists: `app/models/` —
an unpenalized Poisson goal model (`"poisson-mle-v1"`) with attack/
defence strengths and an **estimated** home-advantage term, fitted by
Newton-Raphson maximum likelihood inside `fit` (cutoff enforced inside
the calculation: only matches strictly before `as_of` enter the
likelihood), plus analytic scoreline matrices (truncation mass always
reported) and outcome probabilities that are exact under any
truncation. Deterministic and stdlib-only by construction; every fit
carries its convergence status and sha256 provenance. See
`docs/STATISTICAL-ASSUMPTIONS.md` for the model's assumptions and their
weaknesses — every number it produces is an **in-sample estimate on
synthetic fixtures, never evidence of accuracy**. Phases 1 (Foundation)
and 2 (Domain and data) are committed at **45ed27e** and **1c5067b**.
The local, offline, deterministic test loop is operational: 37 tests,
all green. No forecasts, no scenarios, no storage, no API yet (by
design; see `docs/briefs/phase-3.md` and `docs/PLAN.md`). See
`docs/ROADMAP.md` for phase status and `docs/PROGRESS-LOG.md` for the
record.

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

Verified output (2026-10-16, Phase 3 docs run, clean environment —
`env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q`):
`37 passed in 16.27s`. Zero skips, zero xfails — no test in this suite
may use skip or xfail (constitution). If your shell inherits a stray
`PYTEST_ADDOPTS` (e.g. from a health-script environment), unset it as
above so the health tests are not silently deselected; the health
script's own inner runs deselect them on purpose (recursion guard).

## Running the health check

From the repository root:

```sh
bash scripts/health-check.sh
```

Verified on 2026-10-16 (Phase 3): exit code 0; compile clean; determinism
comparison `OK: 34 passed, 3 deselected`; skips/xfails `none`; `pip
check` clean ("No broken requirements found."). Its own pytest
invocations report `34 passed, 3 deselected`: the script exports a
`PYTEST_ADDOPTS` recursion guard so its internal suite runs never
re-execute the tests that spawn the script; those health tests run in
the direct suite above. Expect roughly half a minute to a minute — the
script runs the non-health suite five times internally (observed 14.1 s
total idle this run; 47.5 s under concurrent load at Phase 2 — see
`docs/KNOWN-LIMITATIONS.md`).

Important: by design (no `set -e`, so one failing check cannot abort the
sweep) the health script prints failures but still exits 0. It is a
monitoring report, **not** the pass/fail gate. The gate is a direct suite
run of `.venv/bin/python -m pytest -q` (Phase 1 criterion 10). See
`docs/KNOWN-LIMITATIONS.md`.

## Repository layout (what exists now)

    lookingglass/
    ├── app/                     # the engine; Phase 3: domain/, ingestion/,
    │                            # validation/, models/ (+ Phase 1 __init__.py)
    ├── fixtures/                # synthetic OpenFootball-shaped JSON (Phase 2)
    ├── tests/                   # 37 tests, 1:1 with acceptance criteria
    ├── scripts/health-check.sh  # mechanical health sweep
    ├── pytest.ini               # testpaths=tests, --strict-markers
    ├── conftest.py              # repo root importability for bare pytest
    ├── .venv/                   # local venv (git-ignored)
    ├── .opencode/               # agent suite and constitution
    └── docs/                    # handoff, roadmap, plan, logs, briefs,
                                 # DATA-SOURCES, STATISTICAL-ASSUMPTIONS,
                                 # KNOWN-LIMITATIONS

The much larger target structure (ten separated pipeline modules) is
declared in `docs/ARCHITECTURE.md` and `docs/PLAN.md`, and is instantiated
phase by phase — never speculatively.

## Documentation

- `docs/HANDOFF.md` — the full brief of record.
- `.opencode/rule/lookingglass-constitution.md` — binding rules.
- `docs/ROADMAP.md` — phase status.
- `docs/ARCHITECTURE.md` — pipeline stages and module map (target marked).
- `docs/DATA-SOURCES.md` — data formats, fixture provenance, licenses.
- `docs/STATISTICAL-ASSUMPTIONS.md` — the Poisson model's assumptions
  and their weaknesses (Phase 3).
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
