# PHASE 10 BRIEF — OPERATIONAL RELIABILITY (BLOCK 4, OPENING PHASE)

Status: proposed (2026-10-22, glass-architect). Per `docs/ROADMAP.md` this is **Block 4, Phase 10 — the block's opening phase**; block mode applies: this brief plans Phase 10 only (Phases 11/12 are not planned here). Blocks 1, 2, **and 3** developer acceptance are recorded (roadmap block-acceptance table, rows dated 2026-10-17 / 2026-10-19 / **2026-10-22** — neither duplicated nor edited here), so the constitutional gate to start Phase 10 is satisfied. **glass-quant was consulted** (mandatory; run at conductor top level, 2026-10-22) — rulings **ADV-1–ADV-10** are binding design constraints cited inline.

**Scope anchor (ADV-0/Phase 8 precedent, restated so no phase can blur it): Phase 10 is HANDOFF Part IX item 10 "Operational reliability" — it is NOT pipeline stage 10 MODEL IMPROVEMENT** (`app/improvement/` remains PLANNED; no tuning loop, no variant machinery, no config loop ships or is representable). **Phase 10 is also NOT IX-11 forecast evaluation** (Phase 11's evidence gate — zero metrics, evaluated n stays exactly 0) **and NOT IX-12 integration and verification** (Phase 12's end-to-end determinism replay). IX-11/IX-12 deliverables ship nowhere in this phase.

## Objective

Deliver HANDOFF Part IX item 10 **verbatim** — *"Operational reliability — error handling, compile checks, health monitoring, runtime sanity on this hardware"* (IX-10) — as: the architect-sanctioned **run-structure rework of `scripts/health-check.sh`** (the rework the Phase 4 A2 record and Phase 9 AMENDMENT A4 both explicitly reserved to Phase 10), an **evidence-based downward valve re-tune** under the standing re-scope clause, **TEST-ONLY error-handling coverage** (corrupted-store loud failure; interrupted-batch atomicity — zero production change expected), the **compile-checks strand completed** to cover `tests/`, and **load-labeled runtime-sanity records** on this hardware. **Zero statistics this phase; evaluated n remains exactly 0; no wall-clock SLA is promised anywhere** (ADV-5/ADV-8).

## State verified before writing this brief (probed 2026-10-22)

- **HEAD = `80b8f79`** (full hash `80b8f79383ab1c990ffc497a8d2c751ebc2b5b11`; "phase 9: chronological backtesting harness, per-fixture baselines, idempotent runs"). `git log`: 866eba5 → 45ed27e → 1c5067b → a5d7f56 → f208e43 → 44b43ea → cfde3a6 → 1e1c1ac → ea92667 → 80b8f79. All nine phase reviewer verdicts first-pass PASS (Phases 4–9); all nine monitor sweeps **WARN** with the carried finding 1.
- **ADV-1 BLOCKER discharged — the Block 3 acceptance row EXISTS** (`docs/ROADMAP.md` block acceptance record, quoted): **"| 3 | yes (recorded) | 2026-10-22 | Phases 7–9 committed at 1e1c1ac, ea92667, 80b8f79 … all three reviewer verdicts first-pass PASS, suite 147 passed with zero skip/xfail. Phase 9's declared amendments included the A4 evidence-based health-check valve re-scope (300 → 1500 s …) and the sanctioned `scripts/health-check.sh` determinism fix; the harness is machinery only, evaluated n = 0 until Phase 11. Acceptance reported by the developer at the Phase 10 boundary ("Accept, start Block 4") and recorded here per the constitution."** The row's recording **also discharges Phase 11's block gate** — Phases 11 and 12 run inside Block 4 with no further block boundary (noted for the conductor's later planning; nothing here plans them).
- **Dirty tree = exactly the three protocol docs** (`git status --porcelain` → ` M docs/HEALTH-LOG.md`, ` M docs/PROGRESS-LOG.md`, ` M docs/ROADMAP.md`): the Phase 9 monitor-sweep entry, the Phase 9 PROGRESS-LOG record, and the ROADMAP Phase 9 `committed` flip **plus the Block 3 acceptance row**. Monitor WARN carried. All **must ride Phase 10's checkpoint commit**, as Phases 2–9's did (monitor finding 1).
- **Suite figure of record: 147 passed** (committed Phase 9 PROGRESS-LOG; docs run 723.04 s at load ~11; clean-env runs ×2+ at load ~9.5–12.7 on 4 cores, ~647–750 s; offline lo-up form 867.88 s). The suite was not re-run at brief time — the tester/reviewer/monitor executions of record govern.
- **Runtime watch item evolution traced (HEALTH-LOG)**: Phase 7 sweep raised rule 7 (health-test setup 162.69 s at load 8.39, A2-300 s valve margin ~1.9×, setup-dominated); Phase 8 sweep: carried, no deterioration; Phase 9 sweep: **the dominant cost** — inner runs 116.72–123.11 s each, script wall ~627 s at load ~8.9–10.4, direct-suite setup 524.15 s; **A4 valve (1500 s) held at ~2.9×** (the old 300 s valve would have tripped); watch item **live for Phase 10 with the brief assigning the five-inner-run rework to Phase 10 (IX-10)** — this brief discharges it.
- **AMENDMENT chains cited accurately**: **A2 (Phase 4, standing)** — valve 120 → 300 s (2.34× the then-worst 128 s), two in-place edits, 105 → 105 lines, no assertion changed, with the standing re-trigger clause *"any future trip re-triggers the same clause (re-scope with fresh evidence, never weaken)"*; **A4 (Phase 9)** — the clause's second exercise: valve 300 → 1500 s (2.3–2.5× the then-worst ~600–660 s script wall at load ~10–11; rejected bounds recorded), again two in-place edits 105 → 105, plus the sole-then-sanctioned script edit (determinism strip-regex fix + counts-only `UNPARSEABLE` gate). **The current valve is A4's 1500 s**; A4 itself recorded that *"re-architecture of the script's run structure is **Phase 10's**"* — this brief is that named successor, not a third valve accident.
- **`scripts/health-check.sh` probed (80 lines)**: exactly five inner pytest executions — run 1 (`-q --tb=no | tail -20`), run 2 (`-q --tb=no -rsxX | tail -30`), the skips run (`-q --tb=no -rsxX | grep 'SKIPPED|XFAIL|XPASS' || echo none` — **flags identical to run 2**), and the determinism pair SUM1/SUM2 (two further plain runs, counts-only strip + `COUNTS_RE` + `UNPARSEABLE`/`MISMATCH`/`OK:` branches); recursion guard at line 13; compile covers `app` only; nine sections; `set -u` only (exit-0-by-design, Phase 1 decision).
- **`tests/test_health_script.py` probed (105 lines)**: `HEALTH_TIMEOUT_S = 1500` (A4, line 21); `SECTION_HEADERS` = exactly nine pinned strings; one module-scoped subprocess fixture; three tests asserting (i) exit 0 + all headers, (ii) `OK:` determinism + no `MISMATCH`, (iii) `none` skips + clean pip. **ADV-3: this structure is SOUND — the script is fixed; the test inherits with zero assertion changes.**
- **Storage read path probed**: `app/storage/forecasts_db.py` — `insert_forecast` wraps check+INSERT in one `BEGIN IMMEDIATE` transaction with `rollback()` on any exception; `verify_all` (`:294–308`) recomputes every row's content hash, first mismatch raises `ForecastIntegrityError`; `SCHEMA_VERSION == 1`. `tests/test_storage.py` (425 lines) covers triggers, idempotence/conflict, round-trip, 1-ulp tamper, query_only, single-INSERT tracing, no-timestamp schema — **and contains NO corrupted-file test and NO interrupted-multi-insert-batch test**: ADV-6's two error-path tests target concrete, verified gaps. Malformed-ingestion coverage exists since Phase 2 (`defect-sample.json`, 7 planted defects) — **no concrete gap found; no ingestion-test extension** (ADV-6's closing clause).
- **Suite composition probed**: 25 test modules / 147 tests; cross-file test imports are in-pattern (`test_backtesting.py` imports from `test_vocab_guards.py`), so `test_operational.py` may import `SECTION_HEADERS` from `test_health_script` (single source of truth). No hygiene collision exists: this phase adds **no `app/` package**, so `ALLOWED_APP_IMPORTS`, `PURE_PACKAGES`, and every separation-file pin stay untouched (Phase 8's zero-hygiene-growth pattern).
- **`docs/STATISTICAL-ASSUMPTIONS.md` ends at §12** (1373 lines; §§11–12 are the quant's own pre-registrations, implemented-and-tested, binding Phases 9/11 — untouched by this brief). **§13 ruled NOT needed** — design decision 9.
- **`docs/PLAN.md` clauses checked**: §3 no-third-party discipline holds (stdlib/bash only); §5 layer 3 ("the health script runs the suite twice and asserts the summaries match (timings stripped)") — the rework keeps exactly this, machine-checked (counts-only, loud `UNPARSEABLE`); §8 postpones performance tuning/parallelism — this phase reduces **execution counts of the verification harness**, never engine performance, and touches no calculation path; §4's "stdlib socket-blocking guard in tests **if needed**" — discharged as **not needed** (design decision 12).

## glass-quant consultation — RUN; rulings binding (record, not a gate)

The mandatory glass-quant consult for Phase 10 **was run at conductor top level, 2026-10-22**. Binding rulings, cited inline: **(ADV-1, BLOCKER)** verify and quote the Block 3 acceptance row before finalizing (Phase 4 precedent) — done above; its recording also discharges Phase 11's gate; **(ADV-2, core deliverable)** restructure the script's run structure — recommended 3-run design with capture-once derivation, ~620 → ~370–390 s expected wall at load ~10, 6 → 4 executions per direct-suite cycle, latency 25 → ~15 min; the 2-run alternative requires anchored-counts greps (the current unanchored grep could hijack `tail -n1` under `-rsxX`; `UNPARSEABLE` would catch loudly) — architect judges 3-run vs 2-run and records reasoning (design decision 1); never cut: the two-execution determinism comparison, skips/xfails "none", pip, compile, tree/commit sections, five-largest, recursion guard, offline runability, test-side harness subsetting ban (E2 stands); **(ADV-3)** the in-suite health test structure is SOUND — fix the script, the test inherits with ZERO assertion changes; any surrogate-output/`HEALTH_FAST` design = REJECT (test weakening by another route); only the A2/A4 two-line pattern (timeout + docstring) may ever touch that file, by named amendment; **(ADV-4)** re-tune the valve DOWN with fresh evidence after the restructure at the historical load envelope (≥ load ~10, never idle-only), `HEALTH_TIMEOUT_S ≈ 2.3–2.5×` new worst observed via named amendment (two in-place edits, 105 → 105), rejected bounds recorded as A4 did — or keep 1500 s with rewritten honest rationale; the figure is NOT predesigned (design decision 6 pre-declares the verifiable procedure); **(ADV-5)** load-insensitivity is impossible — position: reduce load **exposure** (execution counts) + rely on proven outcome-invariance + load-labeled runtime records; no wall-clock SLA promise anywhere; **(ADV-6)** error-handling strand: 2–4 TEST-ONLY tests, zero production change expected; probe the REAL corruption behavior (sqlite `DatabaseError` vs our `ForecastIntegrityError`) and document whichever is real; pin journal atomicity as observed; decide compile-tests yes/no; explicitly ruled OUT: signal handlers, fsync tuning, crash daemons, log rotation, disk-full sims, monitoring services, CI, Docker; **(ADV-7)** the 10-item invariant checklist below is the brief's "invariants any change must keep green"; **(ADV-8)** claims discipline — zero statistics, evaluated n = 0, improvements stated as execution-count facts, wall times as load-labeled ranges never percentages, no bare "optimized"/"reliable" adjectives, placement HEALTH-LOG/KNOWN-LIMITATIONS/PROGRESS-LOG; **(ADV-9, blocker-grade)** the out-of-scope list below; **(ADV-10)** zero developer questions; the CHECK-PRESERVATION MAPPING below is the central trust artifact; dropping a CHECK (vs an execution) or changing what the constitution's mandatory loop verifies is developer-eyes territory (stated up front, below).

## Design decisions (this brief resolves them)

1. **3-run design ADOPTED over the 2-run alternative (ADV-2; reasoning recorded).** New structure: **run 1** = plain `-q --tb=no`, captured once → display `tail -n 20` **and** determinism SUM1; **run 2** = `-q --tb=no -rsxX`, captured once → display `tail -n 30` **and** the skips/xfails grep (this execution absorbs the old skips run — same flags, byte-identical output class, so the separate execution was pure duplication); **run 3** = plain `-q --tb=no`, executed silently → determinism SUM2. **Reasoning:** (i) the determinism pair (runs 1 and 3) keeps **two identical-flag plain executions** — the A4-pinned mechanism (counts-only strip, `COUNTS_RE`, loud `UNPARSEABLE`, `MISMATCH` only when both sides parse) survives with **zero semantic drift**; (ii) the sums are extracted **only from plain captures**, so the unanchored counts grep never sees `-rsxX` output — the hijack hazard the quant flagged is **eliminated structurally**, which is why the anchored-counts rewrite is unnecessary here (decision 4); (iii) the 2-run alternative would either put the determinism pair on mixed flags (semantic drift from A4) or re-derive SUM2 through anchored greps over `-rsxX` output (a semantics change to the A4-pinned mechanism) — exactly the quiet drift the A4 counts-pin was adopted to prevent; (iv) the extra plain run costs one suite execution (~2 min at load ~10) and buys flag-identical determinism semantics. Expected (predictions, never claims): script wall **~620 → ~370–390 s** at load ~10; non-health-suite executions per direct-suite cycle **6 → 4**; hang-detection latency **25 → ~15 min**.
2. **Capture-once derivation, stdout/stderr split preserved byte-for-byte (A4-faithful).** Each run redirects stdout and stderr to **separate** files in a `mktemp -d` capture dir (`trap` cleanup — no strays): display = combined stream through the same `tail -n 20`/`tail -n 30`; the skips grep and both sum extractions read **stdout only** — the exact A4 input classes (today's display pipelines were `2>&1`; today's SUM lines were stdout-only). The full replacement text is AMENDMENT A1 below. No `HEALTH_FAST`, no surrogate output, no environment knob — the script runs the real suite (ADV-3).
3. **All nine section headers stay byte-identical; header honesty preserved by ordering.** The nine `== … ==` headers are unchanged (substring-pinned by the untouched `SECTION_HEADERS`); the `-rsxX` execution remains the one displayed under `== pytest run 2 (with skip/xfail reasons) ==` (execution 2 — the label stays true), and run 1's plain display keeps its header. The silent run 3 introduces **no new header** (a tenth header would fail the untouched header test — by design).
4. **Anchored-vs-unanchored decision: KEEP the A4 unanchored grep + `COUNTS_RE` gate, verbatim (pinned).** Under decision 1 the sums never consume `-rsxX` output, so anchoring buys nothing and changing the extraction would alter A4-pinned semantics for no gain; the `UNPARSEABLE` gate remains the loud backstop for any future summary-shape drift. Pinned by criterion 4 (sum lines contain no `-m pytest`, no `-rsxX`; exactly three invocations, exactly one `-rsxX` in the whole script).
5. **Run-count pin: source-level structural pin, in-pattern.** The strongest non-brittle pin available without harness machinery: `tests/test_operational.py` asserts the script source contains **exactly 3** `-m pytest` invocations and **exactly 1** `-rsxX`, and that the SUM1/SUM2 extraction lines reference the captured `run1.out`/`run3.out` files (stable literals fixed by AMENDMENT A1). The repo already pins source strings (`== 12` pins in separation files; A4 pinned the strip line); behavior is separately pinned end-to-end by the untouched health tests (`OK:` determinism proves two sums parsed and matched; `none` skips proves the `-rsxX` grep ran).
6. **Valve re-tune: PROCEDURE pre-declared, figure decided at build-verification (ADV-4 option chosen).** AMENDMENT A2 below pre-authorizes exactly the A2/A4 two-in-place-line pattern (docstring figure + `HEALTH_TIMEOUT_S` line, 105 → 105, no assertion change) and binds the verifiable procedure: (1) every `bash scripts/health-check.sh` execution during the Phase 10 window is recorded with wall time **and the load average at invocation start**; (2) W = worst recorded **post-restructure** wall among executions at **load ≥ 8** (the historical envelope floor — Phase 9's relevant runs were load 8.9–12.7); (3) the new valve V satisfies **2.3×W ≤ V ≤ 2.5×W**, rounded to the nearest 50 s, and V < 1500 (a re-tune **down**); (4) rejected bounds and reasons recorded in PROGRESS-LOG, A4 style; (5) **fallback:** if no post-restructure execution at load ≥ 8 exists at build-verification, no downward figure is set — 1500 s stands with the constant line's comment honestly rewritten in place under A2 (citing the missing-load evidence; re-tune deferred to the next phase that carries load evidence); idle-only evidence **never** justifies a downward figure; waiting for load is permitted, never required. Verifiability: criterion 7 (105-line + citation pins, test-side) plus the reviewer's arithmetic check (V/W ∈ [2.3, 2.5] against the load-labeled measurements cited in PROGRESS-LOG).
7. **Error-handling strand: exactly the two ADV-6 core tests, TEST-ONLY, zero production change expected (ADV-6).** `tests/test_operational.py` (NEW, ≤ ~440 lines): (a) **corrupted/truncated store fails loudly** — garbage bytes and a half-truncated real DB into `tmp_path`, then `open_read_connection` + `verify_all`: the builder **probes the real behavior first** and pins the observed exception type (expected: `sqlite3.DatabaseError` — "file is not a database" / "database disk image is malformed" — raised at the first read; `ForecastIntegrityError` is the structurally-valid-row hash-mismatch path, a different mechanism). Whatever the probe shows is pinned and documented; what is **never** acceptable is a silent empty/garbage return. (b) **interrupted multi-insert batch** — A, B committed; a caller-side batch then inserts C and hits a `ForecastConflictError` (nextafter-perturbed duplicate identity) mid-batch: prior rows intact, `verify_all` returns exactly the committed set hash-clean, zero partial row for the failed insert — **journal atomicity pinned as observed** (per-`insert_forecast` `BEGIN IMMEDIATE` + rollback; the caller-side loop shape is what a Phase 11-style batch gets for free). Ruled out verbatim per ADV-6: signal handlers, fsync tuning, crash daemons, log rotation, disk-full sims, monitoring services, CI, Docker. **Ingestion: no extension — no concrete gap** (Phase 2's defect fixture and validation tests stand).
8. **Compile checks extended to `tests/` — YES (completes the IX-10 "compile checks" strand).** One line in the compile section: `compileall -q app` → `compileall -q app tests` — seconds, stdlib, covers the whole repo Python surface; the section's quiet-on-success semantics unchanged. Pinned by criterion 3.
9. **`docs/STATISTICAL-ASSUMPTIONS.md` §13: NOT needed (chosen over a fresh section, with reasoning).** That document holds statistical design pre-registrations and implemented statistical reality; §§11–12 are the quant's own registrations binding Phases 9/11 and stay untouched. **Phase 10 ships zero statistics** (evaluated n = 0; no model, forecast, baseline, or metric surface changes) and its design content — harness run structure, valve discipline, error-path behavior — is operational, correctly recorded in this brief, KNOWN-LIMITATIONS Phase 10, and the protocol logs. A §13 would blur the document's purpose and imply statistical machinery where none ships. (The alternative is defensible on "every phase gets a section" grounds; rejected as category-error — placement per ADV-8 governs.)
10. **Zero production code (byte-pinned).** `git diff 80b8f79 -- app/` must exit 0 with empty output (Phase 8 criterion-7 pattern, version-local; a future phase touching `app/` re-points it by named amendment). Additionally the golden-pin and guard test files are byte-pinned (criterion 8). No `ALLOWED_APP_IMPORTS`/`PURE_PACKAGES`/separation-pin amendments exist this phase (no new `app/` package).
11. **Load position (ADV-5), binding on every doc this phase writes.** Load-insensitivity is **impossible** on a shared 4-core machine. The phase's honest levers, in order: (a) **reduce load exposure** — execution counts are the load-independent facts (5 → 3 inner runs; 6 → 4 executions of the non-health suite per direct-suite cycle); (b) **outcome-invariance** — already proven across every recorded execution (147 passed identical in 7+ Phase 9 runs at load 8.9–12.7 and offline); (c) **load-labeled runtime records** — every runtime figure in HEALTH-LOG/PROGRESS-LOG/KNOWN-LIMITATIONS carries its load average, as ranges, **never percentages, never bare adjectives**. **No wall-clock SLA promise appears anywhere** — the valve is a hang-detection bound with evidence margin, never a performance guarantee.
12. **Exit-0-by-design kept — brief position (ADV-9).** The script's `set -u`-only semantics (a failing check prints but cannot abort the sweep) is the recorded Phase 1 decision (KNOWN-LIMITATIONS Phase 1 item 1); the gate is the **direct suite run**, per the constitution. This phase does not redesign exit semantics; the position is restated so the restructure is never misread as the moment to "fix" it.
13. **PLAN §4's socket-blocking guard clause: discharged "not needed".** Offline runability is verified by the recorded `unshare -rn` lo-up protocol runs (tester discipline since Phase 6); a new socket guard would add machinery for zero verified gap. The rework keeps the script fully local; offline suite runability rides criterion 9's recorded executions.
14. **Docs placement (ADV-8):** KNOWN-LIMITATIONS gets a new Phase 10 section **plus appended follow-through** on Phase 1 items 2 and 5 (prior measured figures never rewritten — append-only); HEALTH-LOG conventions carry the load-labeled runtime records and the watch-item evolution; PROGRESS-LOG records the executions, the valve evidence, and the amendment declarations; ROADMAP flips Phase 10 (block table and Block 1/2/3 rows byte-identical). No doc this phase uses the words "optimized" or "reliable" as bare adjectives.

## CHECK-PRESERVATION MAPPING (ADV-10 — the central trust artifact; the reviewer verifies every row)

Each current execution of the 5-run script → the check it carries → where it survives in the 3-run script. **A CHECK is never dropped; only redundant EXECUTIONS are eliminated.**

| # | Current execution (5-run script) | Check carried | Survival in the 3-run script |
|---|----------------------------------|---------------|------------------------------|
| 1 | `pytest run 1`: `-q --tb=no \| tail -n 20` | first suite execution + display tail | Run 1, same flags; display = captured combined stream through the same `tail -n 20`; same header |
| 2 | `pytest run 2`: `-q --tb=no -rsxX \| tail -n 30` | second suite execution + skip/xfail-reason display | Run 2 (the single `-rsxX` execution), same flags; display = captured combined stream through the same `tail -n 30`; same header |
| 3 | skips run: `-q --tb=no -rsxX \| grep -E 'SKIPPED\|XFAIL\|XPASS' \|\| echo none` | skips/xfails = "none" gate | grep over **run 2's captured stdout** — same pattern, same `none` fallback, same section; the eliminated execution was flags-identical to row 2 |
| 4 | determinism SUM1: plain run → counts grep `tail -n 1` → `strip_summary` | determinism sum 1 | **run 1's captured stdout** through the identical grep/tail/strip pipeline (same stdout-only input class as A4) |
| 5 | determinism SUM2: plain run → same | determinism sum 2 | **run 3** (new silent plain execution) captured stdout through the identical pipeline — the determinism pair remains **two identical-flag plain executions** |
| — | recursion guard; last commit; working tree; compile; pip check; five largest; exit-0-by-design | all | byte-identical sections; compile **extended** `app` → `app tests` (sanctioned addition, criterion 8/decision 8) |

Load-independent facts: non-health-suite executions per direct-suite cycle **6 → 4**; inner pytest executions per script **5 → 3**; determinism comparison executions **2 → 2** (unchanged); skips "none" gate **present**; every one of the **nine section headers** byte-identical.

## Files and directories to create or modify

BUILD step:

- `scripts/health-check.sh` — **AMENDMENT A1 ONLY** (the run-structure rework; full replacement text at the end of this brief). This is the sanctioned exercise of the reservation Phase 9 A4 itself recorded ("run-structure rework is Phase 10's, IX-10") — **the ONLY sanctioned amendment to this file ever after A4's**; after A1 the script returns to do-not-modify status for all later phases.
- `tests/test_operational.py` — **NEW**, criteria 1–8, ≤ ~440 lines, stdlib only (`sqlite3`, `dataclasses`, `pathlib`, `re`, `subprocess`/`git` byte-pins, `math.nextafter`).
- `tests/test_health_script.py` — **AMENDMENT A2 ONLY, and only if/when the decision-6 procedure executes its edit** (two in-place lines: docstring valve figure + `HEALTH_TIMEOUT_S` constant with the Phase 10 A2 citation; 105 → 105; the fallback path's honest-rationale rewrite is the same two lines). **Nothing else in that file may ever change** (ADV-3).
- Do not create or modify: `pytest.ini`, `conftest.py`, fixtures, `docs/DATA-SOURCES.md`, any file under `app/` (byte-pinned), `app/backtesting/`, `app/evaluation/`, `app/improvement/`, `app/state/`, any Phase 1–9 test file (incl. the golden-pin and guard files — byte-pinned by criterion 8), requirements/pyproject, CI, linters, Docker, `data/`, any committed DB.

DOCS step:

- `docs/KNOWN-LIMITATIONS.md` — intro flip to Phase 10; new **Phase 10** section (the 3-run rework with the mapping; the compile-tests extension; the valve figure with its load-labeled evidence or the fallback rationale; the corruption/batch tests with the pinned real behavior; zero production code; evaluated n = 0; no wall-clock SLA position); **appended follow-through** on Phase 1 items 2 and 5 (A2/A4/Phase-10 chain; the 6× suite-cost clause updated with execution counts — prior figures never rewritten); "Not yet applicable" refresh (stages 3/10/evaluation remain).
- `docs/HEALTH-LOG.md` — the load-labeled runtime records for this phase's executions; the watch-item entry updated by append (execution counts down; valve figure; outcome-invariance reconfirmed).
- `docs/PROGRESS-LOG.md` — standard entry: the rework, the mapping, the valve evidence (W with load labels, V with ratio), rejected bounds, the amendment declarations, the quant-consult record (2026-10-22, ADV-1–ADV-10). The three protocol docs **must ride the Phase 10 checkpoint commit**.
- `docs/ROADMAP.md` — Phase 10 `in progress` → `committed` (PENDING-hash convention); **block table byte-identical; Block 1/2/3 rows untouched — the Block 3 row is quoted in this brief, never edited**.
- `README.md` — current state: Phase 10, real test count (docs agent).
- `docs/ARCHITECTURE.md` — status line: no new module; stage map unchanged; the health script's run structure recorded as 3 inner runs; stage 3/10/evaluation remain PLANNED.
- `docs/PLAN.md` — **no change** (no module added; §4's socket-guard "if needed" clause is discharged as not needed — design decision 13, recorded here and in KNOWN-LIMITATIONS).
- `docs/STATISTICAL-ASSUMPTIONS.md` — **no change** (decision 9; §§1–12 untouched).

## Dependencies

- **None new.** stdlib/bash only: `mktemp`/`trap`/`sed`/`grep`/`tail`/`find`/`xargs`/`wc` (already used by the script), `sqlite3`/`dataclasses`/`pathlib`/`re`/`math` (test-side), `git` (byte-pin, tests only — Phase 6/8 precedent). pytest already installed (justification unchanged).
- **Explicitly refused:** any third-party package; numpy/pandas/scipy or any numeric stack; any monitoring/CI/Docker/service tooling; any new `app/` module; any sqlite schema change (`SCHEMA_VERSION` stays 1); any environment knob (`HEALTH_FAST` et al. — REJECT per ADV-3).

## Acceptance criteria

Criteria 1–8 map 1:1 to pytest test functions in the **new `tests/test_operational.py`**; criterion 9 is the suite-level gate verified by recorded executions (tester, reviewer ×2, monitor), as in Phases 1–9. No test may use skip or xfail. All tests run offline from the checked-in fixtures. Expected total **147 + 8 = 155** (a prediction, never a claimed fact).

1. **`test_corrupted_store_fails_loudly_never_silently`** (ADV-6; error handling) — into a `tmp_path`: (a) a garbage-bytes `.db` (e.g. 4 KiB of non-sqlite bytes) and (b) a valid forecast DB (one inserted row) truncated to its first 512 bytes; for each, `open_read_connection` + `verify_all` (and `get_forecast` for the valid-key case) **raises** — never returns an empty tuple, never returns garbage, never warns; the exception type pinned is the **real probed behavior** on this platform (expected `sqlite3.DatabaseError`; the test docstring records the probe result and explains why this is NOT `ForecastIntegrityError` — that one is the structurally-valid-row hash-mismatch path); the pinned type is platform/sqlite-version-local by the golden-discipline rule (re-probe on interpreter/sqlite change, never widen to bare `Exception`).
2. **`test_interrupted_multi_insert_batch_prior_rows_intact_verify_clean`** (ADV-6; journal atomicity pinned as observed) — insert and commit forecasts A and B; then a caller-side batch inserts C (succeeds) and a `dataclasses.replace`-perturbed duplicate-identity D (`nextafter` on `dropped_mass`, same identity) which raises `ForecastConflictError` mid-batch; after the raised exception: `verify_all` returns exactly A, B, C in canonical order, every content hash recomputes clean, the row count is exactly 3, and **zero partial row for D** exists (raw count + identity probe). No production code changes to make this pass — the property is pinned as observed in `insert_forecast`'s per-call `BEGIN IMMEDIATE` + rollback.
3. **`test_compile_section_covers_app_and_tests`** (IX-10 compile checks; decision 8) — the script source's compile invocation contains both `app` and `tests` (string pin on the `compileall -q app tests` literal), and the compile section header still precedes it; the section stays quiet-on-success.
4. **`test_health_script_exactly_three_inner_runs_one_rsx_x_sums_from_plain_captures`** (ADV-2/ADV-4; decision 1/4/5) — over the script source: **exactly 3** occurrences of `-m pytest`; **exactly 1** occurrence of `-rsxX`; the SUM1 extraction line contains no `-m pytest` and no `-rsxX` and references the run-1 stdout capture; the SUM2 extraction line likewise references the run-3 stdout capture; both extraction lines contain the `strip_summary` pipe. The anchored-vs-unanchored decision is pinned: the extraction lines are byte-stable and consume plain captures only.
5. **`test_health_script_determinism_mechanism_a4_verbatim`** (A4 semantics survive verbatim) — the script source contains, verbatim: the `strip_summary` sed line (both timing forms stripped), the `COUNTS_RE` counts-only pattern line, the `UNPARSEABLE` loud branch (with its echo of both sides), the `MISMATCH` branch, and the `OK: $SUM1` emission; and the recursion-guard line (`PYTEST_ADDOPTS` … `-k 'not health_script'`) is byte-identical to the committed form.
6. **`test_health_script_section_headers_exactly_nine_verbatim`** (ADV-7 invariant 3; the "SECTION_HEADERS still match" criterion) — parse the script source's header-emitting `echo "== … =="` lines; assert **exactly nine** are emitted (no tenth header exists) and, in order, each contains the corresponding `SECTION_HEADERS` substring imported from `tests/test_health_script.py` (single source of truth — cross-file import in-pattern); assert the tuple itself is unchanged (the nine pinned strings, in the pinned order).
7. **`test_health_valve_amendment_two_line_pattern_105_lines`** (ADV-4/ADV-3; A2/A4 pattern discipline) — `tests/test_health_script.py` is **exactly 105 lines**; the `HEALTH_TIMEOUT_S` constant line carries an integer and the "AMENDMENT A2 (Phase 10)" citation; the module docstring line carries the matching valve figure and citation; the file contains no `skip`/`xfail` and its three test functions remain (the assertions themselves run green in the suite). The figure's arithmetic (V within [2.3×W, 2.5×W] of the worst cited load-labeled post-restructure measurement, or the documented fallback) is the **reviewer's checklist item** against the PROGRESS-LOG citation (decision 6), not re-derived test-side.
8. **`test_app_and_golden_files_byte_pinned_vs_phase9`** (zero production code; golden pins untouched) — `git diff 80b8f79 -- app/` exits 0 with empty output; and `git diff 80b8f79 --` over the golden-pin and guard files (`tests/test_backtesting.py`, `tests/test_forecasts.py`, `tests/test_features.py`, `tests/test_decisions.py`, `tests/test_simulation.py`, `tests/test_poisson_fit.py`, `tests/test_scoreline_matrix.py`, `tests/test_temporal_integrity.py`, `tests/test_vocab_guards.py`) exits 0 with empty output (version-local pin; a future phase re-points by named amendment).
9. **Suite gate (recorded execution)** — `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` from the repo root reports 0 failed, 0 errors, 0 skipped, 0 xfailed, 0 xpassed (expected total **155**; the real number recorded by the tester). Executed and pasted by the tester; executed independently (twice) by the reviewer; re-executed by the monitor via the health script; one **offline** `unshare -rn bash -c 'ip link set lo up && env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q'` run recorded (lo-up protocol). `bash scripts/health-check.sh` completes with `OK:` determinism, `none` skips/xfails, clean pip, and all nine headers — **with every runtime figure recorded load-labeled**. **Reviewer checklist before PASS:** (i) the CHECK-PRESERVATION MAPPING above verified row by row against the shipped script — each of the nine sections and every check still asserted; (ii) the determinism counts-gate semantics unchanged (criteria 4–5) and the skips/pip assertions unchanged (untouched test file + suite green); (iii) the valve figure's arithmetic per decision 6 (or the documented fallback); (iv) no harness subsetting occurred (E2 — `tests/test_backtesting.py` byte-pinned, criterion 8); (v) the amendment declarations match the shipped diffs exactly. **Watch the valve** — the load-driven watch item rides this gate; any trip re-scopes the mechanism with fresh evidence (the standing clause), never weakens/skips/xfails.

## Invariants any change must keep green (ADV-7 — the 10-item checklist)

1. **Recursion guard** — `PYTEST_ADDOPTS` `-k 'not health_script'` byte-identical (criterion 5).
2. **Determinism = counts-only, two identical-flag runs, loud `UNPARSEABLE`, `MISMATCH` only when both sides parse** — A4 semantics verbatim (criterion 5).
3. **The nine section headers verbatim**, `SECTION_HEADERS` unchanged, no tenth header (criterion 6 + the untouched health test).
4. **The three health-test assertions unchanged** — exit 0 + all headers; `OK:` determinism + no `MISMATCH`; `none` skips + clean pip (ADV-3; the file's only sanctioned edits are A2's two valve lines).
5. **A2/A4 valve discipline** — evidence-based re-scope by named amendment only, two in-place lines, never an assertion change; idle-only evidence never justifies a downward figure (decision 6).
6. **No skip, no xfail anywhere in the suite** — zero tolerated, this phase included.
7. **E2: the full backtesting harness executes everywhere** — no subsetting, no test-side timeout around any harness run (criterion 8's byte-pin).
8. **Offline runability** — the lo-up protocol form recorded every phase (criterion 9).
9. **Version-local golden pins untouched** — re-derive on change, never widen (criterion 8).
10. **Append-only, dated doc updates** — follow-through appends only; prior measured figures never rewritten (decision 14).

## Out of scope (ADV-9 — blocker-grade, verbatim-shape)

- **No evaluation or metrics of any kind** — no log loss, no Brier, no RPS, no calibration, no score-vs-outcome computation; **evaluated n stays exactly 0** (Phase 11's evidence gate).
- **No `app/evaluation/`, no `app/improvement/`, no `app/state/` package** — none exists; none is created (Phase 10 ≠ pipeline stage 10 MODEL IMPROVEMENT).
- **No API changes**; no CLI; no plotting.
- **No schema bump** (`SCHEMA_VERSION` stays 1); no new table/column; no committed DB.
- **No new dependencies** (stdlib/bash only).
- **No CI, no Docker, no services, no monitoring daemons, no log rotation, no crash daemons, no signal handlers, no fsync tuning, no disk-full simulations** (ADV-6's explicit ruling-out).
- **No fixture edits** (§11(a)/§12 registrations untouched).
- **No `app/backtesting/` changes; no harness subsetting; no test-side timeout around any harness execution** (E2 stands).
- **No test deletions, no skips, no xfails, no assertion weakening anywhere** — including any surrogate-output or `HEALTH_FAST` route around the health test (ADV-3: REJECT).
- **No exit-semantics redesign** — exit-0-by-design stands (recorded Phase 1 decision; the gate is the direct suite run).
- **No ingestion-test extension** (no concrete gap; Phase 2 coverage stands).
- **No wall-clock SLA promise anywhere** (ADV-5); no bare "optimized"/"reliable" claims (ADV-8).
- **No `docs/STATISTICAL-ASSUMPTIONS.md` §13** (decision 9); §§11–12 untouched.

## Risks

- **A check dropped silently during the restructure:** the mapping table is the guard — criteria 4/5/6 pin the structure source-side, the untouched health tests pin it behaviorally end-to-end, and the reviewer verifies the mapping row by row (criterion 9 checklist).
- **Capture-derivation subtlety** (display vs sum input classes): decision 2 mandates separate stdout/stderr captures so both A4 input classes survive byte-faithfully; the fallback for any parse failure is loud `UNPARSEABLE`, never a silent OK.
- **Valve too tight at unprecedented load:** the trip path is the standing clause — STOP, fresh evidence, re-scope; never weaken/skip/xfail. The fallback path (decision 6 step 5) prevents an idle-only downward figure from creating exactly this hazard.
- **Corruption-test behavior is sqlite/platform-local:** pinned as observed with the locality note (golden-discipline rule) — the invariant asserted is "fails loudly, never silently", which holds under any loud type.
- **Source-pin brittleness:** string counts/verbatim lines are in-pattern here (the repo pins source strings throughout); the pinned literals are fixed by AMENDMENT A1 itself, so test and script cannot drift apart within the phase.
- **Load-driven runtime (carried watch item):** outcomes are invariant across all recorded executions; wall-clock remains load-driven and is recorded as load-labeled ranges only (ADV-5). Execution counts — the load-independent facts — improve 5 → 3 and 6 → 4.
- **Overengineering:** bash + `mktemp` only; no new tools, no machinery, no knobs (the 2-run anchored-grep alternative was rejected precisely for the added semantics surface).

## Open questions for the developer

**None** (ADV-10 — every design question is resolved as a brief position: the 3-run structure with reasoning, capture-once semantics, the kept unanchored-grep decision, the run-count pin mechanism, the valve procedure with fallback, the two-test error set, the compile-tests extension, the §13 ruling, the zero-production byte-pin).

**Developer-eyes threshold, stated up front (ADV-10):** this restructure changes **HOW OFTEN** the mandatory loop's checks execute, never **WHAT** they check. The CHECK-PRESERVATION MAPPING above is the central trust artifact the reviewer verifies. Should any design — here or in any future phase — drop a CHECK rather than an execution, or change what the constitution's mandatory loop verifies, that is **developer-eyes territory**: the phase stops at the conductor and the conflict is reported to the developer (constitution header clause). Block 4's acceptance remains the developer's at the Phases 10–12 boundary; this brief plans nothing beyond Phase 10.

---

## Declared amendments (pre-sanctioned by this brief; declared at checkpoint, review, and monitor sweep)

### AMENDMENT A1 (Phase 10) — `scripts/health-check.sh` run-structure rework: five inner runs → three, capture-once derivation (the sanctioned exercise of Phase 9 A4's explicit reservation; the ONLY sanctioned amendment to this file ever after A4's)

**Authority:** the Phase 4 A2 record ("re-architecting the script's five inner runs is Phase 10's, HANDOFF IX-10"), restated by Phase 9 A4's NOT-sanctioned list ("re-architecture of the script's run structure is Phase 10's"); quant ruling ADV-2 (core deliverable); architect decision 1 (3-run over 2-run). Check semantics are preserved per the mapping above; the recursion guard, every section header, and the exit-0-by-design semantics are untouched.

**Replace the entire file exactly with:**

```bash
#!/usr/bin/env bash
# Mechanical health sweep for Sports Looking Glass.
# set -u only: one failing check must not abort the sweep (no set -e).
set -u

cd "$(dirname "$0")/.." || exit 1

PY=".venv/bin/python"

# Recursion guard: the health script's own pytest runs must not
# execute the tests that spawn this script. They run in the direct
# suite instead (pytest, from the repo root).
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-k 'not health_script'"

if [ ! -x "$PY" ]; then
    echo "There is nothing to check yet: $PY does not exist."
    echo "This is expected before Phase 1 completes."
    exit 0
fi

echo "== last commit =="
git log -1 --oneline 2>&1 || true

echo
echo "== working tree =="
git status --porcelain 2>&1 || true

echo
echo "== compile =="
if [ -d app ]; then
    "$PY" -m compileall -q app tests 2>&1 || true
else
    echo "skipped"
fi

# Phase 10 AMENDMENT A1 (architect-sanctioned run-structure rework,
# docs/briefs/phase-10.md): exactly THREE inner pytest executions
# replace the former five. The old skips run was flags-identical to
# run 2, and the determinism sums re-ran the suite twice more; those
# redundant EXECUTIONS are eliminated, no CHECK. Each run's stdout
# and stderr are captured ONCE into a temp dir; the display tails,
# the skips/xfails grep, and the determinism sums are DERIVED from
# the captures (stdout-only for grep/sums and combined for display =
# the exact Phase 9 A4 input classes). Determinism keeps two
# IDENTICAL plain-flag runs (run 1 and run 3) with the A4 mechanism
# verbatim: counts-only strip, COUNTS_RE gate, loud UNPARSEABLE.
# All nine section headers are byte-identical to the Phase 1 pins.
CAPTURES="$(mktemp -d)"
trap 'rm -rf "$CAPTURES"' EXIT

echo
echo "== pytest run 1 =="
"$PY" -m pytest -q --tb=no >"$CAPTURES/run1.out" 2>"$CAPTURES/run1.err" || true
cat "$CAPTURES/run1.out" "$CAPTURES/run1.err" | tail -n 20

echo
echo "== pytest run 2 (with skip/xfail reasons) =="
"$PY" -m pytest -q --tb=no -rsxX >"$CAPTURES/run2.out" 2>"$CAPTURES/run2.err" || true
cat "$CAPTURES/run2.out" "$CAPTURES/run2.err" | tail -n 30

echo
echo "== skips/xfails =="
grep -E 'SKIPPED|XFAIL|XPASS' "$CAPTURES/run2.out" || echo "none"

echo
echo "== determinism comparison (timings stripped) =="
# Phase 9 AMENDMENT A4 mechanism, unchanged: strip BOTH timing forms;
# counts-only comparison, never timings; UNPARSEABLE is loud, never
# a silent OK. Phase 10 A1: SUM1 derives from run 1's PLAIN stdout
# capture; run 3 (below) executes silently and its PLAIN stdout
# capture yields SUM2 -- two identical-flag executions, byte-
# identical A4 extraction semantics on both sides.
strip_summary() {
    sed -E 's/in [0-9.]+s//; s/ +\([0-9]+:[0-9]+:[0-9]+\)//; s/ +$//'
}
COUNTS_RE='^[0-9]+ [a-z]+(, [0-9]+ [a-z]+)*$'
"$PY" -m pytest -q --tb=no >"$CAPTURES/run3.out" 2>"$CAPTURES/run3.err" || true
SUM1=$(grep -E '^[0-9]+ (passed|failed)|passed|failed|error' "$CAPTURES/run1.out" | tail -n 1 | strip_summary)
SUM2=$(grep -E '^[0-9]+ (passed|failed)|passed|failed|error' "$CAPTURES/run3.out" | tail -n 1 | strip_summary)
if ! [[ "$SUM1" =~ $COUNTS_RE ]] || ! [[ "$SUM2" =~ $COUNTS_RE ]]; then
    echo "UNPARSEABLE (counts-only comparison expected after stripping):"
    echo "sum 1: $SUM1"
    echo "sum 2: $SUM2"
elif [ "$SUM1" = "$SUM2" ]; then
    echo "OK: $SUM1"
else
    echo "MISMATCH"
    echo "sum 1: $SUM1"
    echo "sum 2: $SUM2"
fi

echo
echo "== pip check =="
"$PY" -m pip check 2>&1 | tail -n 5 || true

echo
echo "== five largest .py files (app/ and tests/) =="
find app tests -name '*.py' -type f 2>/dev/null | xargs wc -l 2>/dev/null | sort -rn | sed -n '2,6p'
```

*(One honest label change within the A4 block: the MISMATCH/UNPARSEABLE side labels read `sum 1:`/`sum 2:` instead of `run 1:`/`run 2:`, because SUM2 now derives from run 3 — no test depends on those labels; the block's parse/compare semantics are byte-identical. Declared here.)*

**NOT sanctioned:** reducing below three executions or merging the determinism pair (the two-execution comparison is inviolable); any change to the recursion guard, `PY`, section headers, pip, five-largest, or the early-exit branch; any non-stdlib tool; caching outputs across phases; any `HEALTH_FAST`-style knob. After A1, the script returns to do-not-modify status.

### AMENDMENT A2 (Phase 10) — health-test valve re-tune: procedure pre-declared, figure decided at build-verification (the standing A2/A4 re-scope clause, third exercise, DOWN with fresh evidence per ADV-4)

**Pre-authorized — exactly, in `tests/test_health_script.py` only, executed (or the fallback applied) at build-verification under decision 6's procedure:** two in-place line edits — the module docstring's valve figure + citation, and the `HEALTH_TIMEOUT_S` constant line — **105 → 105 lines, no assertion changed**, citing "AMENDMENT A2 (Phase 10)" and `docs/briefs/phase-10.md`. The figure V satisfies **2.3×W ≤ V ≤ 2.5×W** (nearest 50 s) where W = worst post-restructure script wall at load ≥ 8 recorded across the phase's executions, each wall labeled with its invocation-start load; rejected bounds and reasons recorded in PROGRESS-LOG (A4 style). **Fallback (decision 6 step 5):** absent load-≥ 8 evidence, no downward figure — 1500 s stands with the constant line's comment rewritten in place (same two lines) citing the missing-load evidence; idle-only evidence never justifies a downward figure.

**NOT sanctioned:** any third edit; any mechanism change (scaling, retries, measurement loops, load-gating); any change to assertions, `SECTION_HEADERS`, the fixture, or the recursion-guard behavior; deleting/skipping/xfailing any health test — ever; using idle-only measurements to justify a downward figure.

*End of Phase 10 brief. Block 4 acceptance is the developer's at the Phases 10–12 boundary; this brief plans nothing beyond Phase 10. Blocks 1, 2, and 3 acceptance rows are recorded — neither duplicated nor edited here. glass-quant was consulted (2026-10-22, conductor top level): rulings ADV-1–ADV-10 binding; the Block 3 row verified and quoted (ADV-1); the 3-run-over-2-run decision recorded with reasoning (design decision 1); the valve procedure pre-declared with fallback (decision 6); zero open developer questions (ADV-10).*
