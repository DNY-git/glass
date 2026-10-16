# SPORTS LOOKING GLASS — PROJECT HANDOFF

This document is the full brief for the project. It was written at bootstrap
(2026-10-13) on the developer's instruction to serve as the brief of record for
the reconstruction; it is not a recovered artifact of the lost repository.
Where it describes the lost project, that material is history. The binding
rules for all agents live in `.opencode/rule/lookingglass-constitution.md`.

## PART I — WHAT THIS IS

Sports Looking Glass is a deterministic statistical future-analysis engine.
Football first. It takes historical match data, validates it, extracts
chronological features, fits statistical models, produces forecast
probability distributions, explores bounded scenarios, supports decision
analysis, and evaluates its own forecasts against what actually happened —
strictly in chronological order.

It is a research and decision-analysis system. It estimates. It never
promises. Every probability it emits is an estimate with stated uncertainty,
and every gap in its data is reported as a gap.

## PART II — ABSOLUTE PROHIBITIONS

These are repeated from the constitution and are not negotiable:

1. No AI, LLM, or generative dependency in the product. AI assists
   development only; it never contributes to a computed number at runtime.
2. Zero cost: no paid APIs, no API keys in the core workflow, no required
   cloud, no required Docker. Works offline from local fixtures.
3. No betting functionality of any kind. No stakes, no odds shopping, no
   wager integration. Probabilities are estimates.
4. Never fabricate data. Missing xG, missing kickoff times, missing rest
   days — all reported as missing, never silently imputed.
5. Never claim the old implementation was recovered. Its test counts (276
   tests, 380 matches) are history, not current facts.

## PART III — DOMAIN AND DATA

- Football (soccer) only, for now: competitions, seasons, teams, matches,
  scorelines, and where available shot-level statistics (xG).
- Primary structured data: the OpenFootball formats (match lists in their
  JSON/CSV encodings), with provenance and license recorded in
  `docs/DATA-SOURCES.md`.
- All data lives in local fixtures under `data/` (git-ignored) or small
  checked-in sample fixtures under the repository. Nothing downloads at
  runtime. Nothing calls a network service.
- Ingestion is idempotent: importing the same file twice yields the same
  stored state, with no duplicates.

## PART IV — SYSTEM ARCHITECTURE

Module separation is mandatory. The pipeline has ten stages:

1. **DATA** — fixtures, loaders, provenance.
2. **VALIDATION** — schema and integrity checks; defects reported, not
   guessed around.
3. **PRE-MATCH STATE** — as-of-kickoff view of the world.
4. **FEATURE EXTRACTION** — chronological features computed from history
   with explicit cutoffs.
5. **STATISTICAL MODELS** — pure computation: Poisson goal models,
   strength parameters, calibration.
6. **FORECAST DISTRIBUTIONS** — full scoreline/outcome distributions,
   frozen at creation.
7. **SCENARIO EXPLORATION** — bounded, labeled-hypothetical multipliers.
8. **DECISION ANALYSIS** — comparison of model outputs and their
   disagreement, honestly presented.
9. **OUTCOME EVALUATION** — log loss, Brier, RPS against realized results,
   strictly chronological.
10. **MODEL IMPROVEMENT** — a tuning loop protected from evaluating itself
    on its own tuning data.

Rules of separation: pure statistical code imports no storage, no HTTP, no
I/O. Domain models, ingestion, storage, features, statistical models,
forecasts, scenarios, decision reports, backtesting, evaluation, and API
routing are distinct modules. API routers stay thin; logic lives in domain
modules.

## PART V — ANALYTICAL INTEGRITY

- **No future information** in pre-match or historical calculations.
- **History cutoffs are enforced inside the calculation** — for example,
  inside the forecast builder — never only at call sites. A caller that
  forgets to filter must still be unable to leak.
- **Forecasts and pre-match snapshots are immutable** once created.
  Evaluation, tuning, and correction never rewrite them.
- **Determinism:** identical inputs + model version + seed + config produce
  identical output. All randomness flows through explicitly seeded RNGs
  passed by the caller. No wall-clock time, no environment lookups, no
  unsorted iteration inside calculations.
- **Missing data is a first-class result.** Insufficient histories,
  unavailable xG, unknown kickoff times, model disagreement, and weak
  calibration are reported, never hidden or smoothed.
- **A normalized distribution is not evidence of accuracy.** Evaluation
  against baselines is the evidence, and it is done chronologically.

## PART VI — ENGINEERING DISCIPLINE

- One phase at a time per `docs/ROADMAP.md`; never start Phase N+1 until
  Phase N passed review, was committed, and passed the monitor sweep.
- Phases run in blocks of three (1-3, 4-6, 7-9, 10-12, 13); the developer
  is the acceptance gate at each block boundary.
- Lightweight by default: Python venv, pytest, standard library first.
  FastAPI at the edge when an API phase arrives. Every dependency must be
  justified; the default answer is none. No Docker, no services.
- Tests prove phases: real commands, real output, 1:1 mapping from
  acceptance criteria to tests. Never weaken, delete, skip, or xfail a
  test to make a phase pass.
- Commits only via the checkpoint protocol on green tests. Never push
  without explicit developer authorization.
- No frontend before the core pipeline is reliable. No generic
  multi-domain framework before football works end to end.

## PART VII — ENVIRONMENT

Linux Mint, modest hardware, Python 3 in a local venv, offline-capable by
design. Design for this machine, not for a cloud. Health monitoring runs
via `scripts/health-check.sh`.

## PART VIII — HISTORY OF THE LOST PROJECT

The original repository was lost. What survives is documentation: this
handoff, the roadmap shape, and the memories recorded above. The lost
project ran 276 tests against 380 matches — history, never to be quoted as
the current state. We reconstruct **principles, not old filenames**: cutoff
enforcement inside the forecast builder, immutable pre-match snapshots,
idempotent ingestion and evaluation, versioned feature specs and model
versions, and evaluation records that never alter original forecasts.

## PART IX — PHASE MAP

The 13 phases below match `docs/ROADMAP.md` exactly:

1. **Foundation** — repo skeleton, venv, pytest wiring, `app/` package,
   local test loop, health script operational.
2. **Domain and data** — domain models, OpenFootball ingestion, validation,
   local fixtures, idempotent imports.
3. **Core statistics** — Poisson goal model, attack/defence strengths, home
   advantage as documented constants, seeded RNG, pure modules.
4. **Simulation and scenarios** — scoreline matrix simulation, bounded
   labeled-hypothetical scenario multipliers.
5. **Forecasting API** — forecast builder with cutoff enforced inside,
   immutable forecast snapshots, thin FastAPI routers over domain logic.
6. **Feature engine** — chronological features, versioned feature specs,
   availability statuses for xG and kickoff/rest data.
7. **Decision analysis** — comparison of model outputs without a silently
   invented ensemble, disagreement reported not collapsed.
8. **Temporal integrity** — leakage defenses: future-match injection tests,
   snapshot immutability audits, cutoff-at-source verification.
9. **Backtesting** — strictly chronological backtesting harness, baselines
   (long-run home/draw/away frequencies), idempotent runs.
10. **Operational reliability** — error handling, compile checks, health
    monitoring, runtime sanity on this hardware.
11. **Forecast evaluation** — log loss, Brier, RPS against hand-computed
    values and baselines, calibration over many observations, idempotent
    evaluation records.
12. **Integration and verification** — end-to-end offline pipeline,
    determinism replay (same seed twice, identical output).
13. **Consolidation and research readiness** — docs consolidation,
    `docs/KNOWN-LIMITATIONS.md`, research-ready honest reporting.

## PART X — PLANNING QUESTIONS

The master plan (`docs/PLAN.md`) must answer, in order:

1. What is the minimum viable first phase?
2. What is the directory structure?
3. Which dependencies are genuinely necessary?
4. What works offline?
5. How is determinism tested?
6. How is future-data leakage prevented as the system grows?
7. How is each phase independently verifiable?
8. What is postponed until the statistical engine works?

Postponed by consensus, to be restated in the plan: frontend, multi-domain
framework, and any domain other than football.
