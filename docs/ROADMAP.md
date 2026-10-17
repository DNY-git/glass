# ROADMAP

Status values: `planned` / `in progress` / `committed`.
Developer acceptance is recorded per BLOCK, not per phase.

## FIXED block table (do not change without developer instruction)

| Block | Phases |
|-------|--------|
| 1     | 1-3    |
| 2     | 4-6    |
| 3     | 7-9    |
| 4     | 10-12  |
| 5     | 13     |

## Phases

| Phase | Name                            | Status    |
|-------|---------------------------------|-----------|
| 1     | Foundation                      | committed   |
| 2     | Domain and data                 | committed   |
| 3     | Core statistics                 | in progress |
| 4     | Simulation and scenarios        | planned   |
| 5     | Forecasting API                 | planned   |
| 6     | Feature engine                  | planned   |
| 7     | Decision analysis               | planned   |
| 8     | Temporal integrity              | planned   |
| 9     | Backtesting                     | planned   |
| 10    | Operational reliability         | planned   |
| 11    | Forecast evaluation             | planned   |
| 12    | Integration and verification    | planned   |
| 13    | Consolidation and research readiness | planned |

Status notes:
- Phase 1 is `committed`: checkpoint hash **45ed27e** — `phase 1:
  foundation venv, pytest wiring, app package, health-check loop`
  (2026-10-16, master). Built and passed independent review (PASS,
  2026-10-16); hash recorded in docs/PROGRESS-LOG.md. Pre-commit suite
  run: 9 passed.
- Phase 2 is `committed`: checkpoint hash **1c5067b** — `phase 2:
  domain models, OpenFootball ingestion, validation, synthetic
  fixtures` (2026-10-16, master). Built and passed independent review
  (PASS, 2026-10-16, after 3 fix cycles); suite 24 passed. The commit
  also carried the three uncommitted Phase-1 protocol records
  (HEALTH-LOG, PROGRESS-LOG, ROADMAP — monitor finding 1) plus the
  Phase 2 DOCS-step files. Hash recorded in docs/PROGRESS-LOG.md per
  the Phase 1 convention. Pre-commit suite re-run: 24 passed.
- Phase 3 is `in progress`: built and passed independent review (PASS,
  2026-10-16, after 1 fix cycle; the fix cycle also carried a
  tester-caught, builder-acknowledged honesty finding); suite 37
  passed. Checkpoint hash **PENDING** — glass-git records the real hash
  at the Phase 3 checkpoint (immediately after this docs step), which
  also carries the three uncommitted protocol records (HEALTH-LOG,
  PROGRESS-LOG, ROADMAP — monitor finding 1, carried from Phases 1–2)
  and the brief amendment-A1-declared **+1 line** in
  tests/test_fixtures_and_hygiene.py; the docs agent then replaces
  PENDING with the hash here and in docs/PROGRESS-LOG.md and flips this
  row to `committed` (Phase 1/2 convention).

## Block acceptance record

| Block | Accepted by developer | Date | Notes |
|-------|-----------------------|------|-------|
|       |                       |      |       |

## Postponed

Per the handoff: frontend, multi-domain framework, and other domains are
postponed until football works end to end.
