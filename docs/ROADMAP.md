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
| 5     | Forecasting API                 | committed   |
| 6     | Feature engine                  | committed   |
| 7     | Decision analysis               | committed   |
| 8     | Temporal integrity              | in progress |
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
- Phase 5 is `committed`: checkpoint hash **44b43ea** — `phase 5:
  forecast snapshots, write-once storage, read-only localhost api`
  (2026-10-18 06:55 +0100, master). Built and passed independent review
  (PASS, 2026-10-17, first pass, criteria 1–27, after tester PASS ×27
  with 469 probes and zero bugs, and after the architect ratified
  AMENDMENTS A3–A5 plus the criterion-8 erratum the builder
  self-declared — A1/A2 were pre-sanctioned in the brief); suite 83
  passed. The checkpoint commit carries the three protocol records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md — monitor
  finding 1, carried from Phases 1–4 sweeps), the phase brief with
  AMENDMENTS A1–A5 and the criterion-8 erratum, the
  AMENDMENT-A1+A2-declared **+9 lines** (10 added, 1 removed) in
  tests/test_fixtures_and_hygiene.py (614 → 623), the
  AMENDMENT-A3-declared **+5 lines** (12 added, 7 removed) in
  tests/test_phase4_separation.py (826 → 831), and the
  AMENDMENT-A4-declared **+11 lines** in tests/test_domain.py. Hash
  recorded in docs/PROGRESS-LOG.md per the Phase 1–4 convention. Block
  2 developer acceptance belongs to the developer at the Phases 4–6
  boundary (recorded per BLOCK, not per phase; no Block 2 acceptance
  row yet).
- Phase 6 is `committed`: checkpoint hash **cfde3a6** (full hash
  cfde3a67bc513890115106b2b774515e1735d4e6; `phase 6: chronological
  feature engine, versioned specs, availability statuses`;
  2026-10-19 06:44 +0100, master). Built and passed independent review
  (PASS, 2026-10-19, first pass, criteria 1–21, after tester PASS ×21
  with three suite runs including an offline run, and with two
  non-blocking tester notes dispositioned); suite **103 passed**;
  builder green with **zero deviations** (first since Phase 2). The
  checkpoint commit carries the three protocol records
  (docs/HEALTH-LOG.md, docs/PROGRESS-LOG.md, docs/ROADMAP.md —
  monitor finding 1, carried from Phases 1–5 sweeps), the phase brief
  (reconciled 214-line version), and the brief-pre-sanctioned
  AMENDMENTS: **A1** (tests/test_fixtures_and_hygiene.py **623 → 624**
  — exactly one `ALLOWED_APP_IMPORTS` entry for `app.features` plus a
  line-neutral, strictly-stronger `PURE_PACKAGES` strengthening),
  **A2** (tests/test_phase4_separation.py key-set pin 10 → 11, **831 →
  832**), **A3** (tests/test_phase5_separation.py criterion-25 pin 10 →
  11, **571 → 572**). Hash recorded in docs/PROGRESS-LOG.md per the
  Phase 1–5 convention. Block 2 developer acceptance belongs to the
  developer at the Phases 4–6 boundary (recorded per BLOCK, not per
  phase; no Block 2 acceptance row yet — acceptance follows the
  monitor sweep of this commit).
- Phase 7 is `committed`: checkpoint hash **1e1c1ac** (full hash
  1e1c1ac3ba4968fa7d69f46467c0d79452ae1b54; `phase 7: decision
  reports, scenario comparison without collapse, no-scoring
  boundary`; 2026-10-19 19:25 +0100, master). Built and passed
  independent review (PASS, 2026-10-19, first pass, criteria 1–18,
  after tester PASS ×18 with the golden report content hash
  independently re-derived, scenario deltas bit-exact, and an offline
  suite run); suite **120 passed**; builder green with **zero
  self-declared deviations after resume** — the first build session
  was interrupted by a server restart mid-work and a second session
  completed the phase (the reviewer audited the 440-line-per-file
  test compaction: no probe dropped); brief-pre-sanctioned AMENDMENTS
  **A1** (tests/test_fixtures_and_hygiene.py **624 → 625** — one
  `app.decisions` allowlist entry plus a line-neutral,
  strictly-stronger `PURE_PACKAGES` four-set strengthening), **A2**
  (tests/test_phase4_separation.py pin 11 → 12, **832 → 833**), **A3**
  (tests/test_phase5_separation.py pin 11 → 12, **572 → 573**), **A4**
  (tests/test_phase6_separation.py pins updated in place, **510 →
  510**); glass-quant consulted (2026-10-19, rulings A1–A8 binding);
  developer answered Q1 = a (`REPORT_VERSION =
  "decision-report-v1"`). Hash recorded in docs/PROGRESS-LOG.md per
  the Phase 1–6 convention. Block 3
  developer acceptance belongs to the developer at the Phases 7–9
  boundary (recorded per BLOCK, not per phase; no Block 3 acceptance
  row).
- Phase 8 is `in progress` (checkpoint **PENDING**): built and passed
  independent review (PASS, 2026-10-19, first pass, criteria 1–14,
  after tester PASS ×14 with a 131-check probe suite, three honest
  probe-bug disclosures, and suite runs including an offline run);
  suite **133 passed**; builder green with **zero deviations** (one
  self-resolved brief ambiguity, adjudicated coherent by tester and
  reviewer); tests + docs only — **zero production code**
  (`git diff 1e1c1ac -- app/` empty; no new `app/` package); brief-
  pre-sanctioned AMENDMENT **A1**
  (tests/test_phase7_separation.py `_SCORING_PATTERN` compile line,
  `\b`-form → segment-boundary, **440 → 440**, strictly stronger,
  empirically verified superset); glass-quant consulted (2026-10-19,
  rulings A0–A9 binding, including the ADV-0 scope-anchor correction:
  Phase 8 = IX-8 temporal integrity, not backtesting — machinery is
  Phase 9, first scoring Phase 11); zero developer questions. The docs
  agent replaces PENDING in docs/PROGRESS-LOG.md with the checkpoint
  hash and flips this row to `committed` after the checkpoint, as in
  Phases 4–7. Block 3 developer acceptance belongs to the developer at
  the Phases 7–9 boundary (recorded per BLOCK, not per phase; no Block
  3 acceptance row).

## Block acceptance record

| Block | Accepted by developer | Date | Notes |
|-------|-----------------------|------|-------|
| 1     | yes (recorded)        | 2026-10-17 | Phases 1–3 committed at 45ed27e, 1c5067b, a5d7f56; all three reviewer verdicts PASS. Acceptance reported by the conductor at the Phase 4 boundary and recorded here per the constitution — the Phase 4 brief flagged the then-empty table as constitutionally required (docs/briefs/phase-4.md, "State verified before writing this brief"). |
| 2     | yes (recorded)        | 2026-10-19 | Phases 4–6 committed at f208e43, 44b43ea, cfde3a6 — simulation and bounded scenarios, forecasts with write-once storage and read-only API, feature engine; all three reviewer verdicts PASS, suite 103 passed with zero skip/xfail. Acceptance reported by the developer at the Phase 7 boundary ("Accept, start Block 3") and recorded here per the constitution. |

## Postponed

Per the handoff: frontend, multi-domain framework, and other domains are
postponed until football works end to end.
