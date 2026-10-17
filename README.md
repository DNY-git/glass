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

**Phase 4 (Simulation and scenarios): built and reviewed (PASS, 2026-10-17,
first pass, criteria 1–20); checkpoint pending.** Pipeline stage 7
exists — `app/scenarios/`: bounded, labeled-hypothetical multiplicative
transforms on named parameters (`attack`, `defence`, `home_advantage`;
inclusive bounds 0.5–2.0; out-of-range multipliers are a `ValueError`,
**never silently clamped**; one scenario per call, never averaged or
ensembled; strict applicability). Alongside it sits `app/simulation/`,
a **cross-cutting Monte Carlo module** (not one of the ten pipeline
stages): seeded simulation over one fixture's scoreline matrix, with a
required keyword-only integer `seed`, `random()`-only draws, and
`SIM_VERSION = "sim-categorical-v1"` — it is the **only module in the
codebase permitted to import `random`** (AST-enforced). Analytic-first
is unchanged: the reported single-match probability is always the
analytic `outcome_probs`; `mc_stderr` measures **simulation noise only,
never model or parameter uncertainty — no confidence intervals exist
anywhere in this system**, and scenario numbers are labeled
hypotheticals all the way down (see `docs/STATISTICAL-ASSUMPTIONS.md`
§7). Phase 3 (Core statistics) remains: `app/models/` — an unpenalized
Poisson goal model (`"poisson-mle-v1"`) with attack/defence strengths
and an **estimated** home-advantage term, fitted by Newton-Raphson
maximum likelihood inside `fit` (cutoff enforced inside the
calculation), plus analytic scoreline matrices (truncation mass always
reported) and outcome probabilities exact under any truncation.
Deterministic and stdlib-only by construction; every fit carries its
convergence status and sha256 provenance. See
`docs/STATISTICAL-ASSUMPTIONS.md` for the model's assumptions and their
weaknesses — every number it produces is an **in-sample estimate on
synthetic fixtures, never evidence of accuracy**. Phases 1 (Foundation),
2 (Domain and data), and 3 (Core statistics) are committed at
**45ed27e**, **1c5067b**, and **a5d7f56**. The local, offline,
deterministic test loop is operational: 57 tests, all green. No
forecasts, no storage, no API yet (by design; see
`docs/briefs/phase-4.md` and `docs/PLAN.md`). See `docs/ROADMAP.md` for
phase status and `docs/PROGRESS-LOG.md` for the record.

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

Verified output (2026-10-17, Phase 4 docs run, clean environment —
`env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q`):
`57 passed in 66.48s`. Zero skips, zero xfails — no test in this suite
may use skip or xfail (constitution). Run time varies with machine load
(recorded this phase roughly 30–66 s). If your shell inherits a stray
`PYTEST_ADDOPTS` (e.g. from a health-script environment), unset it as
above so the health tests are not silently deselected; the health
script's own inner runs deselect them on purpose (recursion guard).

## Running the health check

From the repository root:

```sh
bash scripts/health-check.sh
```

Verified on 2026-10-17 (Phase 4 docs run): ran to completion; compile
clean; determinism comparison `OK: 54 passed, 3 deselected`;
skips/xfails `none`; `pip check` clean ("No broken requirements
found."). Its own pytest invocations report `54 passed, 3 deselected`
(10.36 s and 9.45 s in this run): the script exports a
`PYTEST_ADDOPTS` recursion guard so its internal suite runs never
re-execute the tests that spawn the script; those health tests run in
the direct suite above. Expect roughly half a minute to a couple of
minutes — the script runs the non-health suite five times internally
(recorded totals range from 14.1 s idle at Phase 3's 37-test inner
suite to 128 s under heavy external load on 2026-10-17, the run that
tripped the health test's 120 s timeout and prompted the
evidence-based re-scope to 300 s under AMENDMENT A2 — see
`docs/KNOWN-LIMITATIONS.md` item 2).

Important: by design (no `set -e`, so one failing check cannot abort the
sweep) the health script prints failures but still exits 0. It is a
monitoring report, **not** the pass/fail gate. The gate is a direct suite
run of `.venv/bin/python -m pytest -q` (Phase 1 criterion 10). See
`docs/KNOWN-LIMITATIONS.md`.

## Repository layout (what exists now)

    lookingglass/
    ├── app/                     # the engine; Phase 4: domain/, ingestion/,
    │                            # validation/, models/, scenarios/, simulation/
    ├── fixtures/                # synthetic OpenFootball-shaped JSON (Phase 2)
    ├── tests/                   # 57 tests, 1:1 with acceptance criteria
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
  and their weaknesses (Phase 3), plus simulation and scenarios (Phase
  4, §7).
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
