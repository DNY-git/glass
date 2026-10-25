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
| 8     | Temporal integrity              | committed   |
| 9     | Backtesting                     | committed   |
| 10    | Operational reliability         | committed   |
| 11    | Forecast evaluation             | committed   |
| 12    | Integration and verification    | committed   |
| 13    | Consolidation and research readiness | in progress |

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
- Phase 8 is `committed`: checkpoint hash **ea92667** (full hash
  ea92667af37e069c843c4ba9696771552dcc6e94; `phase 8: temporal
  integrity defenses, poison registry, vocabulary guards`;
  2026-10-19 22:13 +0100, master). Built and passed independent review
  (PASS, 2026-10-19, first pass, criteria 1–14,
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
  Phase 9, first scoring Phase 11); zero developer questions. Hash
  recorded in docs/PROGRESS-LOG.md per the Phase 1–7 convention. Block
  3 developer acceptance belongs to the developer at the Phases 7–9
  boundary (recorded per BLOCK, not per phase; no Block 3 acceptance
  row).
- Phase 9 is `committed`: checkpoint hash **80b8f79** (full hash
  80b8f79383ab1c990ffc497a8d2c751ebc2b5b11; `phase 9: chronological
  backtesting harness, per-fixture baselines, idempotent runs`;
  2026-10-22 18:25 +0100, master). Built and passed independent review
  (**PASS, 2026-10-22, first pass, criteria 1–15**,
  after tester PASS ×15 with the golden run digest independently
  re-derived, baselines hand-recomputed, and suite runs ×3 including
  an offline run); suite **147 passed** (clean-env runs ×2+ at load
  ~9.5–12.7, ~647–750 s; offline 867.88 s; docs run 723.04 s); the
  stage-9 harness exists as a pure `app/backtesting/` package (six
  modules, 535 lines) — **machinery only, still no metrics, evaluated
  n = 0**, no prediction-to-outcome join (Phase 11's); the 60-target
  accounting is 3 refusals + 27 flagged + 30 clean = 57 predictions;
  brief-pre-sanctioned AMENDMENTS **A1+A2**
  (tests/test_temporal_integrity.py **440 → 452**: registry 5 → 6,
  census 3 → 4, byte-pin re-pointed `1e1c1ac` → `ea92667` and rescoped
  to pre-existing packages), **A3+A3'** (hygiene **625 → 626** with the
  self-inclusive value; separation-file pins **833 → 834**, **573 →
  574**, **510 → 510**, **440 → 443**), **A4**
  (tests/test_health_script.py valve **300 → 1500 s**, **105 → 105**,
  after the build-time trip reproduced verbatim — `144 passed, 3
  errors in 428.03s (0:07:08)` — plus the sole sanctioned
  `scripts/health-check.sh` determinism strip-regex/counts-pin fix);
  two builder STOP-and-reports (the A3' brief defect; the A4 valve
  trip), zero self-sanctioning; the 653-line `tests/test_backtesting.py`
  accepted as a deviation (A4 item 3); glass-quant consulted (2026-10-
  20, rulings A0–A10 binding, empirical probes E1–E4 re-verified);
  zero developer questions. Hash recorded in docs/PROGRESS-LOG.md per
  the Phase 1–8 convention. **Block table untouched; Block 1/2 rows
  untouched; NO Block 3 acceptance row — developer acceptance belongs
  to the developer at the Phases 7–9 boundary after the Phase 9 commit
  and monitor sweep** (recorded per BLOCK, not per phase).
- Phase 10 is `committed`: checkpoint hash **8abe1ca** (full hash
  8abe1ca156a1048d8c1c6d7543bfe58359e51a78; `phase 10: health-check
  restructure to 3 runs, valve re-tune down, corruption and atomicity
  tests`; 2026-10-22 22:20 +0100, master). Built and passed
  independent review (**PASS, 2026-10-22, first pass, criteria 1–9**,
  after tester PASS — findings F1/N1 closed within protocol); suite
  **155 passed**
  (clean-env runs at load ~0.97–12, 118–514 s; offline lo-up 502.50 s
  at load 9.80; docs run 149.60 s at load 9.67). HANDOFF Part IX item
  10 ships as **tests + documentation only** — zero production code
  (`git diff 80b8f79 -- app/` empty; no new `app/` package): the
  architect-sanctioned **health-script run-structure rework**
  (AMENDMENT A1, `scripts/health-check.sh` **80 → 98 lines**,
  byte-exact vs the brief — five inner pytest executions → three with
  capture-once derivation, every check preserved, compile checks
  extended `app` → `app tests`), the **evidence-based downward valve
  re-tune** (AMENDMENT A2, `tests/test_health_script.py` valve
  **1500 → 800 s**, two in-place lines, **105 → 105** — 800/335 ≈
  2.39× the worst post-restructure script wall at load 10.06, inside
  the pre-declared [2.3, 2.5] band), and TEST-ONLY error-handling
  coverage (`tests/test_operational.py`, NEW, 409 lines/8 tests:
  corrupted store fails loudly as `sqlite3.DatabaseError`; interrupted
  batch atomicity pinned as observed). Evaluated n remains exactly 0;
  no wall-clock SLA anywhere; zero statistics (no
  `docs/STATISTICAL-ASSUMPTIONS.md` §13 — brief decision 9);
  glass-quant consulted (2026-10-22, rulings ADV-1–ADV-10 binding);
  zero developer questions. Hash recorded in docs/PROGRESS-LOG.md per
  the Phase 1–9 convention. **Block table
  untouched; Block 1/2/3 rows untouched — the Block 3 acceptance row
  (recorded 2026-10-22) rides the Phase 10 checkpoint commit unedited;
  Block 4 acceptance belongs to the developer at the Phases 10–12
  boundary** (recorded per BLOCK, not per phase).
- Phase 11 is `committed`: checkpoint hash **02b86cd** (full hash
  02b86cdd266e9bef2192004228e9432f811e6f16; `phase 11: forecast
  evaluation — log loss, Brier, RPS, calibration, idempotent records`;
  2026-10-23 15:11:20 +0100, master). Built and passed independent
  review (**PASS, 2026-10-23, first pass, criteria 1–23**, after
  tester PASS ×23 with the golden metric values independently
  re-derived bit-exact, and recorded clean-env and offline suite
  runs); suite **178 passed** (clean-env ×2: 149.59 s / 146.96 s at
  the recorded loads; offline lo-up ×2: 190.38 s / 182.99 s; health
  script 3 inner runs `172 passed, 6 deselected` ×2, determinism
  `OK:` counts-only, skips none, pip clean, inside the untouched
  800 s valve). HANDOFF Part IX item 11 ships as the pure
  `app/evaluation/` package (four modules, 639 lines) — the evidence
  gate: digest-gated scoring of the frozen walk-forward predictions
  against realized results (**first evaluated n > 0: 30 primary /
  57 secondary**; 3 refusals excluded and counted; 60 = 3 + 27 + 30),
  hand-computed single-prediction goldens, pooled 5-bin calibration,
  the draw aggregate, the ddof=0 overdispersion diagnostic
  (descriptive), and idempotent no-clock evaluation records — plus the
  §11(d) sanctioned schema bump (**`SCHEMA_VERSION` 1 → 2**: the
  write-once `evaluations` table + `insert_evaluation_record`; read
  paths untouched; no committed DB). Golden literals pinned in
  `tests/test_evaluation.py` (**779 lines — C8-accepted declared
  deviation**); ten declared amendments A1–A10 with `wc -l`-verified
  actuals; builder-proposed deviations **C1–C10 architect-adjudicated
  2026-10-23 — never developer rulings** (C3: a clone-proven latent
  post-commit criterion-8 RED caught and reverted to the six-entry
  golden set, post-commit green clone-verified by builder, tester, and
  reviewer); `docs/STATISTICAL-ASSUMPTIONS.md` §13 authored pre-build
  and flipped to implemented-and-tested; `docs/EVALUATION.md` created
  (every number a pinned test literal); glass-quant consulted
  2026-10-22 (rulings ADV-1–ADV-14 binding); zero developer
  questions. Hash recorded in docs/PROGRESS-LOG.md per the Phase
  1–10 convention. **Block table untouched;
  Block 1/2/3 rows untouched — the Block 3 acceptance row (recorded
  2026-10-22) rides this checkpoint commit unedited; Block 4
  acceptance belongs to the developer at the Phases 10–12 boundary**
  (recorded per BLOCK, not per phase).
- Phase 12 is `committed`: checkpoint hash **de74da9** (full hash
  de74da989b33fcce5a6c9e503d772f4d2425af84; `phase 12: end-to-end
  pipeline integration and determinism replay`; 2026-10-24 08:11:21
  +0100, master). Built and passed independent review (**PASS,
  2026-10-24, first pass, criteria 1–11**, after tester PASS ×11 with
  an independent golden re-derivation and an instrumented cross-process
  probe); suite **188 passed** (direct clean-env 271.93 s at load
  3.28 → 4.53; offline lo-up 274.61 s at load 3.89 → 5.11; health
  script exit 0, wall 190 s, inner `182 passed, 6 deselected` ×2,
  determinism `OK:`, skips none, pip clean, inside the untouched
  800 s valve). HANDOFF Part IX item 12 ships as **tests only** —
  zero production code (`git diff 02b86cd -- app/` empty; no new
  `app/` package) and **zero amendments** (the
  first phase since Phase 2; no existing test file modified; the
  standing guards held with no re-point): `tests/test_integration.py`
  (NEW, 434 lines, 10 tests) proves the end-to-end offline
  composition (fixture files → ingestion → walk-forward → evaluation
  → record → both-table store → verified read-back) and the
  determinism replay (in-process double-run, cross-process under
  `PYTHONHASHSEED` 0/424242, the seeded simulation leg twice),
  **consuming** the Phase 9/11 pins and recomputing nothing (a
  mismatch is RED, never a re-pin). New golden
  `GOLDEN_RECORD_HASH` is a CPython-3.12.3-local deterministic
  re-render (consumption framing); evaluated n remains exactly
  30/57; `app/storage/forecasts_db.py` is 428 lines — declared
  growth, split deferred to a future serving brief (ADV-12.6); zero
  statistics shipped (no §14; `docs/STATISTICAL-ASSUMPTIONS.md` and
  `docs/EVALUATION.md` byte-identical). glass-quant consulted
  2026-10-23 (rulings ADV-12.1–ADV-12.11 binding); D1–D2 brief-prose
  corrections adjudicated 2026-10-24 (no test changes); zero
  developer questions. Hash recorded in docs/PROGRESS-LOG.md per the
  Phase 1–11 convention. **Block table untouched; Block 1/2/3 rows
  untouched — the Block 3 acceptance row (recorded 2026-10-22) rides
  this checkpoint commit unedited; NO Block 4 acceptance row —
  developer acceptance belongs to the developer at the Phases 10–12
  boundary after the Phase 12 commit and monitor sweep** (recorded
  per BLOCK, not per phase).

- Phase 13 is `in progress`: checkpoint hash **PENDING** (the git
  agent replaces PENDING with the checkpoint hash after the commit
  and flips this row `in progress` → `committed`, as in Phases 4–12).
  Built as **documentation only** — zero production code, zero test
  files, zero amendments, zero new statistics (`git diff de74da9 --
  app/ tests/` empty); the evidence mechanism is the traceability
  audit. Brief of record: `docs/briefs/phase-13.md`
  (glass-architect, 2026-10-24); glass-quant consulted 2026-10-24
  (rulings ADV-13.1–ADV-13.11 binding); zero developer questions.
  `docs/KNOWN-LIMITATIONS.md` completed (Phase 13 section appended,
  "Not yet applicable" finalized), the larger-n calibration
  pre-registration recorded (procedure only; computes nothing; not
  run; the numeric minimum-n trigger is a future brief's), and the
  research-readiness statement R1–R12 written; eight of the ten
  stages exist — stage 3 (`app/state/`) and stage 10
  (`app/improvement/`) remain planned; `docs/STATISTICAL-ASSUMPTIONS.md`
  and `docs/EVALUATION.md` byte-identical (no §14); suite 188 passed.
  **Block table untouched; rows 1–12 untouched (the Phase 12 row flip
  and Block 4 row pre-date this phase and ride unedited); the Block 4
  acceptance row (recorded 2026-10-24) rides this checkpoint commit
  unedited; NO Block 5 acceptance row — Block 5 acceptance belongs to
  the developer at the final boundary after the Phase 13 commit and
  monitor sweep** (recorded per BLOCK, not per phase).

## Block acceptance record

| Block | Accepted by developer | Date | Notes |
|-------|-----------------------|------|-------|
| 1     | yes (recorded)        | 2026-10-17 | Phases 1–3 committed at 45ed27e, 1c5067b, a5d7f56; all three reviewer verdicts PASS. Acceptance reported by the conductor at the Phase 4 boundary and recorded here per the constitution — the Phase 4 brief flagged the then-empty table as constitutionally required (docs/briefs/phase-4.md, "State verified before writing this brief"). |
| 2     | yes (recorded)        | 2026-10-19 | Phases 4–6 committed at f208e43, 44b43ea, cfde3a6 — simulation and bounded scenarios, forecasts with write-once storage and read-only API, feature engine; all three reviewer verdicts PASS, suite 103 passed with zero skip/xfail. Acceptance reported by the developer at the Phase 7 boundary ("Accept, start Block 3") and recorded here per the constitution. |
| 3     | yes (recorded)        | 2026-10-22 | Phases 7–9 committed at 1e1c1ac, ea92667, 80b8f79 — decision reports with anti-ensemble scenario comparison and the no-scoring boundary, temporal-integrity defenses (poison registry, vocabulary guards), chronological backtesting harness with per-fixture baselines; all three reviewer verdicts first-pass PASS, suite 147 passed with zero skip/xfail. Phase 9's declared amendments included the A4 evidence-based health-check valve re-scope (300 → 1500 s, after a verbatim-reproduced trip) and the sanctioned `scripts/health-check.sh` determinism fix; the harness is machinery only, evaluated n = 0 until Phase 11. Acceptance reported by the developer at the Phase 10 boundary ("Accept, start Block 4") and recorded here per the constitution. |
| 4     | yes (recorded)        | 2026-10-24 | Phases 10–12 committed at 8abe1ca, 02b86cd, de74da9 — operational reliability (health-check run structure 5 → 3 inner runs, evidence-based valve re-tune 1500 → 800 s, corruption and atomicity tests), forecast evaluation (the evidence gate: log loss, Brier, RPS, pooled calibration, idempotent evaluation records), and end-to-end pipeline integration with determinism replay; all three reviewer verdicts first-pass PASS, suite 155 → 188 passed with zero skip/xfail. Phase 11 discharged the evidence gate with the first evaluated n > 0 (30 primary / 57 secondary, 3 refusals excluded and counted), §13 pre-registered, no confidence intervals and no accuracy, beating, or verdict claims. Phase 12 was zero-amendment and zero-production-code (`tests/test_integration.py`, 434 lines, 10 tests; cross-process determinism under `PYTHONHASHSEED` 0/424242; `GOLDEN_RECORD_HASH` ef46a366…). All three post-checkpoint monitor sweeps were WARN-only, carrying the dirty protocol-docs hygiene item (the three dirty protocol docs ride the Phase 13 checkpoint), the declared >400-line inventory including `app/storage/forecasts_db.py` at 428 lines with the split deferred, and the load-driven runtime watch item. Acceptance reported by the developer at the Phase 13 boundary ("Accept, start Block 5") and recorded here per the constitution. |

## Postponed

Per the handoff: frontend, multi-domain framework, and other domains are
postponed until football works end to end.
