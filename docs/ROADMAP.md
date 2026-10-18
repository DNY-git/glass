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
| 3     | Core statistics                 | committed   |
| 4     | Simulation and scenarios        | committed   |
| 5     | Forecasting API                 | in progress |
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
- Phase 3 is `committed`: checkpoint hash **a5d7f56** — `phase 3:
  poisson core statistics, mle fitter with internal cutoff, scoreline
  matrices` (2026-10-17, master). Built and passed independent review
  (PASS, 2026-10-16, after 1 fix cycle; the fix cycle also carried a
  tester-caught, builder-acknowledged honesty finding); suite 37
  passed. The commit also carried the three protocol records
  (HEALTH-LOG, PROGRESS-LOG, ROADMAP — monitor finding 1, carried from
  Phases 1–2) and the brief amendment-A1-declared **+1 line** in
  tests/test_fixtures_and_hygiene.py. Hash recorded in
  docs/PROGRESS-LOG.md per the Phase 1/2 convention. Docs-step suite
  re-run (2026-10-17): 37 passed.
- Phase 4 is `committed`: checkpoint hash **f208e43** — `phase 4:
  seeded simulation, bounded hypothetical scenarios, scoreline matrix
  sampling` (2026-10-17 20:21 +0100, master). Built and passed
  independent review (PASS, 2026-10-17, first pass, criteria 1–20,
  after tester PASS plus the AMENDMENT-A2 timeout re-scope); suite 57
  passed. The checkpoint commit carries the three protocol records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor
  finding 1, carried from Phases 1–3 sweeps), the phase brief, the
  AMENDMENT-A1-declared **+2 lines** in
  tests/test_fixtures_and_hygiene.py (612 → 614), and the
  AMENDMENT-A2-declared **two in-place edits** in
  tests/test_health_script.py (health-test timeout 120 → 300 s,
  evidence-based; 105 → 105 lines). Hash recorded in
  docs/PROGRESS-LOG.md per the Phase 1–3 convention. Block 1 developer
  acceptance is recorded in the block acceptance record below
  (acceptance is recorded per BLOCK, not per phase; Block 2 acceptance
  belongs to the developer at the Phases 4–6 boundary).
- Phase 5 is `in progress`: checkpoint hash **PENDING** (convention:
  the docs agent replaces PENDING with the real hash and flips the
  status to `committed` immediately after the checkpoint commit). Built
  and passed independent review (PASS, 2026-10-17, first pass, criteria
  1–27, after tester PASS ×27 with 469 probes and zero bugs, and after
  the architect ratified AMENDMENTS A3–A5 plus the criterion-8 erratum
  the builder self-declared — A1/A2 were pre-sanctioned in the brief);
  suite 83 passed. The checkpoint commit must carry the three protocol
  records (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md —
  monitor finding 1, carried from Phases 1–4 sweeps), the phase brief
  with AMENDMENTS A1–A5 and the criterion-8 erratum, the
  AMENDMENT-A1+A2-declared **+9 lines** in
  tests/test_fixtures_and_hygiene.py (614 → 623), the
  AMENDMENT-A3-declared **+5 lines** in tests/test_phase4_separation.py
  (826 → 831), and the AMENDMENT-A4-declared **+11 lines** in
  tests/test_domain.py. Block 2 developer acceptance belongs to the
  developer at the Phases 4–6 boundary (recorded per BLOCK, not per
  phase).

## Block acceptance record

| Block | Accepted by developer | Date | Notes |
|-------|-----------------------|------|-------|
| 1     | yes (recorded)        | 2026-10-17 | Phases 1–3 committed at 45ed27e, 1c5067b, a5d7f56; all three reviewer verdicts PASS. Acceptance reported by the conductor at the Phase 4 boundary and recorded here per the constitution — the Phase 4 brief flagged the then-empty table as constitutionally required (docs/briefs/phase-4.md, "State verified before writing this brief"). |

## Postponed

Per the handoff: frontend, multi-domain framework, and other domains are
postponed until football works end to end.
