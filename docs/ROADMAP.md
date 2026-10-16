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
| 2     | Domain and data                 | in progress |
| 3     | Core statistics                 | planned   |
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
- Phase 2 is `in progress`: built and passed independent review (PASS,
  2026-10-16, after 3 fix cycles); suite 24 passed. Checkpoint hash
  **PENDING** — recorded by glass-git at the Phase 2 checkpoint commit,
  which must also carry the uncommitted Phase-1 protocol records
  (HEALTH-LOG, PROGRESS-LOG, ROADMAP — monitor finding 1). ROADMAP flips
  to `committed` after the commit; the hash lands in
  docs/PROGRESS-LOG.md and here per the Phase 1 convention.

## Block acceptance record

| Block | Accepted by developer | Date | Notes |
|-------|-----------------------|------|-------|
|       |                       |      |       |

## Postponed

Per the handoff: frontend, multi-domain framework, and other domains are
postponed until football works end to end.
