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

**Phase 11 (Forecast evaluation), built and reviewed (PASS, 2026-10-23,
first pass, criteria 1–23, after tester PASS ×23); checkpoint pending.**
HANDOFF Part IX item 11 ships as a **pure `app/evaluation/` package**
(four modules, 639 lines) — the evidence gate: the first-ever scoring
of the frozen walk-forward predictions against realized results,
digest-gated (the golden run digest is re-derived and asserted **before
any metric computes**), read-only over frozen forecasts and match
scores, joined by the re-established one-line natural-key join
(explicit refusals on 0 and >1 matches). **The evaluated observation
count goes from exactly 0 to exactly 30 (primary, the 30 clean
predictions) / 57 (secondary, flags riding) for the first time**; the
3 structural refusals stay excluded from every metric and counted in
the 60 = 3 + 27 + 30 accounting. Log loss (natural log, **no ε-clamp of
any spelling** — a zero probability on the realized outcome is a hard
refusal), the full 3-outcome Brier sum, and the ½-scaled 3-category
ordinal RPS ship against hand-computed single-prediction values and
per-fixture chronological baselines; 5-bin pooled calibration tables,
the draw aggregate, and the overdispersion diagnostic ship
descriptive-only. Model and baseline **absolute** values appear side by
side with `n` — deltas, ratios, and verdicts are banned forever
(`docs/STATISTICAL-ASSUMPTIONS.md` §13; `docs/EVALUATION.md` records
every pinned number, every number a pinned test literal). Idempotent,
content-hashed, no-clock evaluation records persist through the
sanctioned §11(d) schema bump (**`SCHEMA_VERSION` 1 → 2**: the
write-once `evaluations` table + `insert_evaluation_record`; forecasts'
read paths untouched; no committed DB) and never alter original
forecasts. **178 tests.** See `docs/KNOWN-LIMITATIONS.md` Phase 11 for
the honest list, including the ten declared amendments A1–A10 and the
builder-proposed, architect-adjudicated C1–C10 record.

**Phase 10 (Operational reliability), committed at 8abe1ca** — HANDOFF Part IX item 10 ships as **tests + documentation
only** — zero production code (`git diff 80b8f79 -- app/` empty; no
new `app/` package) — as: the architect-sanctioned **health-script
run-structure rework** (AMENDMENT A1: five inner pytest executions →
three with capture-once derivation; **every check preserved**, only
redundant executions eliminated — the check-preservation mapping
verified row by row; compile checks extended `app` → `app tests`),
the **evidence-based downward valve re-tune** (AMENDMENT A2:
health-test timeout **1500 → 800 s**, two in-place lines, no assertion
changed — 800/335 ≈ 2.39× the worst post-restructure script wall at
load 10.06, inside the pre-declared [2.3, 2.5] band), and TEST-ONLY
error-handling tests pinning the real sqlite behavior (a corrupted or
truncated store fails **loudly** with `sqlite3.DatabaseError` at the
first read, never silently; an interrupted multi-insert batch leaves
prior rows intact with zero partial row). **155 tests. Evaluated n
remains exactly 0; no wall-clock SLA is promised anywhere.** See
`docs/KNOWN-LIMITATIONS.md` Phase 10 for the honest list, including
the declared amendments A1/A2.

**Phase 9 (Backtesting), committed at 80b8f79** — HANDOFF Part IX
item 9 ships as a **pure `app/backtesting/` package**
(six modules, 535 lines) — the strictly chronological **machinery**
with **still no metrics**: one public walk-forward harness,
`run_walk_forward(matches, *, fixture_file_sha256s=(),
interpreter_version=None)` — deterministic, canonical-chronological,
the single model spec pinned structurally closed (no config/variant/
seed knob exists), **no `app.storage` import** (persistence is the
caller's; no committed DB; `SCHEMA_VERSION` stays 1) — plus frozen
per-fixture chronological **baselines** (strictly pre-cutoff pooled
H/D/A frequencies; MISSING `n = 0` at the first date's three fixtures,
never a fake uniform; **never stored**) and a first-class **refusal
accounting**: over the frozen fixtures **60 targets = 3 structural
refusals + 27 flagged + 30 clean = 57 predictions**, auditable, never
skipped or uniformed. **No prediction-to-outcome join ships — the
one-line natural-key join is re-established at Phase 11**; zero
metrics of any kind, no model-vs-baseline comparison exists —
**evaluated n remains exactly 0** (the three-step line: Phase 8
defenses → Phase 9 machinery → Phase 11 first scoring). See
`docs/STATISTICAL-ASSUMPTIONS.md` §12 and `docs/KNOWN-LIMITATIONS.md`
Phase 9 for the honest list, including the declared amendments
(A1/A2/A3+A3'/A4) and both build-time STOP-and-reports.

**Phase 8 (Temporal integrity), committed at ea92667** — HANDOFF Part IX
item 8
ships as **tests and documentation only** — zero production code
(`git diff 1e1c1ac -- app/` empty at that phase; no new `app/` package — the first
phase since Phase 2 with zero hygiene growth) — the standing
temporal-integrity defenses: a **poison-matrix coverage registry** with
an AST census (a future history-consuming entry point fails the suite
until it is registered and given a poison test), **cutoff-at-source
bit-identity probes** over fully unfiltered pools (same-day siblings
and future matches included — day-granularity same-day invisibility is
declared design, never "fixed"), an independent **snapshot-immutability
audit**, a **seedless-by-construction pin** for the history-consuming
calculation surface (no `random` anywhere, positive controls), the
**nothing-to-tune pin** (single `FitConfig` identity; non-None ridge
refused), and hardened **vocabulary guards** (the suffixed-form
scoring-guard fix — AMENDMENT A1, `tests/test_phase7_separation.py`
440 → 440 lines, strictly stronger; an app-wide strict-segment scoring
scan with exactly one pinned honest-negation allowlist; an
accuracy-trio identifier scan; performance/rank/correct/best
field-shape bans that never touch the legitimate `score`/`scoreline`/
`scored` domain vocabulary). **Zero predictions, zero baselines, zero
metrics: evaluated n remains 0** — the corrected three-step line: Phase
8 defenses only → Phase 9 machinery → Phase 11 first scoring (see
`docs/STATISTICAL-ASSUMPTIONS.md` §11 and `docs/KNOWN-LIMITATIONS.md`
Phase 8).

**Phase 7 (Decision analysis), committed at 1e1c1ac** — pipeline stage 8
exists — `app/decisions/`: `build_decision_report(forecast, *,
scenarios=())` renders a frozen `Forecast` as a frozen, deterministic
28-field `DecisionReport` with a sha256 `content_hash` computed at
construction (`REPORT_VERSION = "decision-report-v1"`) — a **pure,
in-process VIEW of an already cutoff-enforced artifact**: no `matches`
and no time-like parameter exists to forget (the cutoff was enforced
once, inside `build_forecast`), nothing outside the package imports it
(AST-enforced both directions), and reports are **never stored** — no
sqlite table, no schema bump, no API route — only re-derivable from
frozen forecasts. Optional labeled-hypothetical scenario comparisons
sit side by side with per-entry deltas; the only cross-scenario
aggregation is **min/max spread — never a mean** (a mean would be an
invented ensemble, and **no second independent model exists**, so no
cross-model agreement and no agreement metric is ever invented — the
anti-ensemble clause answered head-on in a fixed, test-pinned
disclaimer). **Zero scoring ships: evaluated n = 0** — log loss,
Brier, RPS, hit rate, calibration, and baselines belong to Phases 9/11
(a token guard asserts their absence); **no thresholds and no decision
rules exist anywhere in the package** (a position, not a default).
See `docs/STATISTICAL-ASSUMPTIONS.md` §10 and
`docs/KNOWN-LIMITATIONS.md` Phase 7 for the honest list.

**Phase 6 (Feature engine), committed at cfde3a6** — pipeline stage 4
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
dependency ships). Phases 1–10 are committed at **45ed27e**
(Foundation), **1c5067b** (Domain and data), **a5d7f56** (Core
statistics), **f208e43** (Simulation and scenarios), **44b43ea**
(Forecasts and API), **cfde3a6** (Feature engine), **1e1c1ac**
(Decision analysis), **ea92667** (Temporal integrity), **80b8f79**
(Backtesting), and **8abe1ca** (Operational reliability). The local,
offline, deterministic test loop is
operational: 178 tests, all green. See `docs/ROADMAP.md` for phase
status and `docs/PROGRESS-LOG.md` for the record.

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

Verified output (2026-10-23, Phase 11 recorded clean-environment runs,
×2 — `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q`):
`178 passed in 149.59s` and `178 passed in 146.96s` at the phase's
recorded machine loads. Zero skips, zero
xfails — no test in this suite
may use skip or xfail (constitution). **Runs take roughly 2–8 minutes
depending on machine load** (Phases 10–11 recorded clean-env runs of
118–514 s at load ~0.97–12 and 149.59/146.96 s — a load-driven watch
item; outcomes identical across every recorded execution) — the health test spawns the health
script, which runs
the non-health suite three times internally (Phase 10's
run-structure rework: five inner runs → three, every check
preserved), the backtesting
tests execute the full 60-target walk-forward harness ~8 times per
suite run, and the evaluation tests re-derive that same run once via a
module-scoped fixture (full harness everywhere — no subsetting, no test-side
timeout). If your
shell
inherits a stray `PYTEST_ADDOPTS` (e.g. from
a health-script environment), unset it as
above so the health tests are not silently deselected; the health
script's own inner runs deselect them on purpose (recursion guard).

Fully offline verification (e.g. under a fresh network namespace):

```sh
unshare -rn bash -c 'ip link set lo up && env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q'
```

Verified (Phase 11, recorded offline lo-up runs, ×2): `178 passed in
190.38s` and `178 passed in 182.99s` (Phase 10's recorded offline run:
`155 passed in 502.50s` at load 9.80). The
loopback step is
required — a plain `unshare -rn` (interface down) fails the six
localhost-binding API tests with `OSError`; that is a namespace-harness
artifact, **not** a bug (see `docs/KNOWN-LIMITATIONS.md` Phase 6,
item 11).

## Running the health check

From the repository root:

```sh
bash scripts/health-check.sh
```

Verified (Phase 11, recorded runs of this phase): ran to completion
inside the untouched 800 s valve
(Phase 10 recorded walls 238–335 s
at machine load ~6.5–10.7; the pre-rework five-run script wall was
~627 s at load ~8.9–10.4); compile clean (covering `app` and
`tests`); its own pytest invocations report
`172 passed, 6 deselected` — the 6 deselected are the 3 health tests
plus the 3 `tests/test_operational.py` source pins whose names contain
`health_script`, deselected on purpose by the recursion guard and
executed in every direct suite run: the script
exports a
`PYTEST_ADDOPTS` recursion guard so its internal suite runs never
re-execute the tests that spawn the script; skips/xfails `none`;
determinism comparison
`OK: 172 passed, 6 deselected`; `pip check` clean ("No broken
requirements found."). Expect roughly **four to six minutes** at
moderate load — the
script runs the non-health suite three times internally (the Phase 10
AMENDMENT A1 rework: five inner runs → three with capture-once
derivation; every check preserved, only redundant executions
eliminated). The health
test's timeout valve remains **800 s** (the Phase 10 AMENDMENT A2
evidence-based DOWN-tune: 800 ≈ 2.39× the worst post-restructure
script wall, 335 s at load 10.06 — see
`docs/KNOWN-LIMITATIONS.md` Phase 1 item 2 and Phase
10).

Important: by design (no `set -e`, so one failing check cannot abort the
sweep) the health script prints failures but still exits 0. It is a
monitoring report, **not** the pass/fail gate. The gate is a direct suite
run of `.venv/bin/python -m pytest -q` (Phase 1 criterion 10). See
`docs/KNOWN-LIMITATIONS.md`.

## Repository layout (what exists now)

    lookingglass/
    ├── app/                     # the engine: domain/, ingestion/,
    │                            # validation/, models/, forecasts/, storage/,
    │                            # api/, scenarios/, simulation/, features/,
    │                            # decisions/, backtesting/, evaluation/
    ├── fixtures/                # synthetic OpenFootball-shaped JSON (Phase 2)
    ├── tests/                   # 178 tests, 1:1 with acceptance criteria
    ├── scripts/health-check.sh  # mechanical health sweep
    ├── pytest.ini               # testpaths=tests, --strict-markers
    ├── conftest.py              # repo root importability for bare pytest
    ├── .venv/                   # local venv (git-ignored)
    ├── .opencode/               # agent suite and constitution
    └── docs/                    # handoff, roadmap, plan, logs, briefs,
                                 # DATA-SOURCES, STATISTICAL-ASSUMPTIONS,
                                 # KNOWN-LIMITATIONS, EVALUATION

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
  (Phase 5, §8), chronological features, versioned feature specs,
  and measured availability (Phase 6, §9), decision reports,
  comparison without collapse, and the no-scoring boundary
  (Phase 7, §10), and the temporal-integrity pre-registrations
  binding Phases 9 and 11 (Phase 8, §11), the backtesting baseline
  definition, scored-population accounting, and standing bans —
  machinery only, still no metrics (Phase 9, §12), and the
  evaluation pre-registrations — metric formulas, populations,
  calibration bins, side-by-side legality — authored pre-build and
  flipped to implemented reality (Phase 11, §13).
- `docs/EVALUATION.md` — the Phase 11 evaluation record: the pinned
  metric values side by side (model and baseline, absolute, with n),
  the calibration tables, and full provenance — every number a pinned
  test literal.
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
