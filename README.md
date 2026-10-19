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

**Phase 6 (Feature engine): built and reviewed (PASS, 2026-10-19,
first pass, criteria 1–21); checkpoint pending.** Pipeline stage 4
exists — `app/features/`: `compute_features(matches, fixture)` with
the cutoff **inside** the function (the cutoff IS `fixture.date`,
derived inside — no `as_of`/`cutoff`/time parameter exists to forget;
nothing dated on or after the fixture date can enter any window),
producing a frozen, deterministic 22-field `FeatureVector` with a
sha256 `content_hash` computed at construction
(`FEATURE_VERSION = "features-chronological-v1"`; named policy
constants `FORM_WINDOW = 5`, `FORM_WINDOW_POLICY =
"MISSING_UNTIL_FULL_WINDOW"`, `REST_DAYS_POLICY = "WITHIN_SEASON"`
— never the ~301-day off-season gap, `XG_FORM_POLICY =
"MEAN_OVER_AVAILABLE_WITH_N"` with `n_xg` disclosed). Every feature is
a **historical summary of synthetic history — not a probability, not a
model output, not evidence**; MISSING propagates visibly and is never
rendered as 0 (measured availability: xG on 10/60 matches, season 2
only; strict rolling-xG covers 0/120 appearances and is therefore not
shipped — see `docs/STATISTICAL-ASSUMPTIONS.md` §9 and
`docs/KNOWN-LIMITATIONS.md` Phase 6). The package is pure and
**consumed by nothing**: no file outside `app/features/` imports it
(AST-enforced both directions), features are computed in memory and
stored nowhere, and `app/models/`, `app/forecasts/`, and
`app/storage/` are byte-identical to checkpoint 44b43ea.

**Phase 5 (Forecasts and API), committed at 44b43ea** — pipeline
stage 6 exists — `app/forecasts/`: `build_forecast(matches, fixture)`
with the
cutoff **inside** the builder (the cutoff IS `fixture.date`, a strict
day-granularity date string — no `as_of`/`cutoff`/time parameter exists
to forget; nothing dated on or after the fixture date can enter the
fit), producing a frozen, deterministic 17-field `Forecast` with a
sha256 `content_hash` computed at construction
(`FORECAST_VERSION = "forecast-poisson-mle-v1"`). Snapshots are
durable and **write-once**: `app/storage/` stores them in a sqlite
database whose schema itself refuses UPDATE/DELETE (triggers
`RAISE(ABORT …)` inside the database file — enforcement survives raw
connections and the CLI), whose read path recomputes every returned
row's content hash (mismatch is a hard error, never a warning), and
which has **no timestamp column anywhere**. `app/api/` is a
**read-only** stdlib `http.server` bound to `127.0.0.1`, two GET
routes (`/health` and
`/forecasts/{competition}/{season}/{date}/{home}/{away}`), serving
**stored snapshots only** — byte-deterministic JSON bodies with
honesty flags at top level, full provenance echo, and a fixed
in-sample-estimate disclaimer. There is no generation endpoint and no
generation CLI **by design** (a compute-on-demand forecast would be
ephemeral and could never be scored by Phase 11). Every stored
forecast is an **in-sample point estimate — never validated**;
evidence begins at Phases 9/11 (see `docs/STATISTICAL-ASSUMPTIONS.md`
§8 and `docs/KNOWN-LIMITATIONS.md` Phase 5 for the honest list,
including the day-granularity cutoff's limits and the amendment-declared
test-file edits). Phase 4 (Simulation and scenarios) remains:
`app/scenarios/` — bounded, labeled-hypothetical multiplicative
transforms (never clamped, never averaged) — and `app/simulation/` —
the cross-cutting seeded Monte Carlo module, the **only module in the
codebase permitted to import `random`** (AST-enforced); `mc_stderr`
measures **simulation noise only, never model or parameter
uncertainty — no confidence intervals exist anywhere in this system**.
Phase 3 (Core statistics) remains: `app/models/` — an unpenalized
Poisson goal model (`"poisson-mle-v1"`) fitted by Newton-Raphson
maximum likelihood inside `fit` (cutoff enforced inside the
calculation), with analytic scoreline matrices (truncation mass always
reported) and outcome probabilities exact under any truncation.
Deterministic and stdlib-only by construction (no third-party
dependency ships). Phases 1–5 are committed at **45ed27e**
(Foundation), **1c5067b** (Domain and data), **a5d7f56** (Core
statistics), **f208e43** (Simulation and scenarios), and **44b43ea**
(Forecasts and API). The local,
offline, deterministic test loop is operational: 103 tests, all green.
See `docs/ROADMAP.md` for phase status and `docs/PROGRESS-LOG.md` for
the record.

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

Verified output (2026-10-19, Phase 6 docs run, clean environment —
`env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q`):
`103 passed in 61.92s`. Zero skips, zero xfails — no test in this suite
may use skip or xfail (constitution). Run time varies with machine load
(recorded this phase roughly 61–68 s light load, higher under
contention). If your shell inherits a stray `PYTEST_ADDOPTS` (e.g. from
a health-script environment), unset it as
above so the health tests are not silently deselected; the health
script's own inner runs deselect them on purpose (recursion guard).

Fully offline verification (e.g. under a fresh network namespace):

```sh
unshare -rn bash -c 'ip link set lo up && env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q'
```

Verified 2026-10-19: `103 passed in 61.73s`. The loopback step is
required — a plain `unshare -rn` (interface down) fails the six
localhost-binding API tests with `OSError`; that is a namespace-harness
artifact, **not** a bug (see `docs/KNOWN-LIMITATIONS.md` Phase 6,
item 11).

## Running the health check

From the repository root:

```sh
bash scripts/health-check.sh
```

Verified on 2026-10-19 (Phase 6 docs run): ran to completion; compile
clean; its own pytest invocations report `100 passed, 3 deselected`
(9.84 s and 10.11 s in this run): the script exports a
`PYTEST_ADDOPTS` recursion guard so its internal suite runs never
re-execute the tests that spawn the script; those health tests run in
the direct suite above; skips/xfails `none`; determinism comparison
`OK: 100 passed, 3 deselected`; `pip check` clean ("No broken
requirements found.). Expect roughly half a minute to a couple of
minutes — the script runs the non-health suite five times internally
(full invocation measured this phase: **52.85 s** light load, second
run's inner pairs 10.19 s and 10.20 s; Phase 4 recorded up to
128 s under heavy external load, the run that tripped the health
test's then-120 s timeout and prompted the
evidence-based re-scope to 300 s under AMENDMENT A2 — see
`docs/KNOWN-LIMITATIONS.md` item 2).

Important: by design (no `set -e`, so one failing check cannot abort the
sweep) the health script prints failures but still exits 0. It is a
monitoring report, **not** the pass/fail gate. The gate is a direct suite
run of `.venv/bin/python -m pytest -q` (Phase 1 criterion 10). See
`docs/KNOWN-LIMITATIONS.md`.

## Repository layout (what exists now)

    lookingglass/
    ├── app/                     # the engine: domain/, ingestion/,
    │                            # validation/, models/, forecasts/, storage/,
    │                            # api/, scenarios/, simulation/, features/
    ├── fixtures/                # synthetic OpenFootball-shaped JSON (Phase 2)
    ├── tests/                   # 103 tests, 1:1 with acceptance criteria
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
  and their weaknesses (Phase 3), simulation and scenarios (Phase 4,
  §7), forecasts, snapshot immutability, and serving honesty
  (Phase 5, §8), and chronological features, versioned feature specs,
  and measured availability (Phase 6, §9).
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
