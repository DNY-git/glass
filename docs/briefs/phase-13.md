# PHASE 13 BRIEF — CONSOLIDATION AND RESEARCH READINESS (BLOCK 5, THE FINAL PHASE)

Status: proposed (2026-10-24, glass-architect). Per `docs/ROADMAP.md` this is **Block 5, Phase 13 — the final phase and the only phase in Block 5**; block mode applies: this brief plans Phase 13 only, and no Phase 14 exists. Phase 12 is committed (`de74da9`); **Block 4 acceptance is verified recorded** (Block acceptance record row 4, "yes (recorded)", 2026-10-24, notes ending *"Acceptance reported by the developer at the Phase 13 boundary ("Accept, start Block 5") and recorded here per the constitution."*) — **the constitutional block gate to start Phase 13 is satisfied**, and the row rides the Phase 13 checkpoint unedited. **glass-quant was consulted** (mandatory; run at conductor top level, 2026-10-24) — rulings **ADV-13.1–ADV-13.11** are binding design constraints, recorded below and cited inline.

## Objective

Deliver HANDOFF Part IX item 13 **verbatim** — *"Consolidation and research readiness — docs consolidation, `docs/KNOWN-LIMITATIONS.md`, research-ready honest reporting"* (HANDOFF:158–159) — as **documentation only**: the final consolidated documentation state, with `docs/KNOWN-LIMITATIONS.md` completed (intro flipped, Phase 13 section appended, "Not yet applicable" finalized), the larger-n calibration **pre-registration** recorded, the research-readiness honesty block R1–R12 written, and the stage-3/stage-10 gap stated as G1–G5. **Why this is the phase's whole content (ADV-13.1, BLOCKER):** Phase 13 ships **zero new computed numbers or statistics, zero `app/` changes, zero new test files, zero amendments to existing tests**. The evidence mechanism is not a test — it is the **traceability audit** (ADV-13.6): every number in every new or edited text is matched to an exact pinned literal, its source, and its `n`; every cross-document value is checked against its peers; every new section is scanned for the ADV-13.4 banned vocabulary; and the reviewer records the command output. That audit is the test-equivalent.

**Explicit non-goals (ADV-13.1/13.2/13.5/13.10).** Phase 13 does **not** build pipeline stages 3 (`app/state/`) or 10 (`app/improvement/`); does **not** author a §14 in `docs/STATISTICAL-ASSUMPTIONS.md`; does **not** create a standalone research-readiness document; does **not** add or amend any test; does **not** touch production code, the API, the schema, dependencies, fixtures, or `docs/DATA-SOURCES.md`; and does **not** acquire, accept, or simulate real data. It records the larger-n protocol **procedure** only — the numeric minimum-n trigger is developer-territory and belongs to a future named brief (ADV-13.3).

## State verified before writing this brief (probed 2026-10-24)

- **HEAD = `de74da9`** (`de74da989b33fcce5a6c9e503d772f4d2425af84`, `phase 12: end-to-end pipeline integration and determinism replay`, 2026-10-24 08:11:21 +0100, master); chain `… → 8abe1ca → 02b86cd → de74da9`.
- **Dirty tree = exactly the three protocol docs** (`git status --porcelain`): `M docs/HEALTH-LOG.md` (+16), `M docs/PROGRESS-LOG.md` (+9/−3), `M docs/ROADMAP.md` (+11/−11) — docs-only, no code hunks. They are the Phase 12 monitor sweep entry plus the two post-commit protocol records it names; **all three ride the Phase 13 checkpoint** (standing Phases 1–12 convention). The ROADMAP dirty state includes the pre-existing Phase 12 row flip and the Block 4 acceptance row (this probe predated the Block 4 row); **the Block 4 row rides unedited — do not edit row 4**.
- **Block 4 acceptance gate verified:** `docs/ROADMAP.md` Block acceptance record has **row 4 = yes (recorded), 2026-10-24**, citing Phases 10–12 at `8abe1ca`, `02b86cd`, `de74da9` and ending *"Acceptance reported by the developer at the Phase 13 boundary ("Accept, start Block 5") and recorded here per the constitution."* The row is **unedited by this phase**; no Block 5 row exists and none may be added.
- **Suite of record: 188 tests collected, 28 test modules** (`pytest --collect-only -q` probed: `188 tests collected in 0.90s`; `ls tests/test_*.py | wc -l` = 28). Health valve **800 s** (`tests/test_health_script.py:21`, AMENDMENT A2 (Phase 10)) — untouched.
- **`app/state/` and `app/improvement/` do not exist** (`ls` → No such file or directory); **eight of the ten pipeline stages exist** (1, 2, 4, 5, 6, 7, 8, 9).
- **`docs/STATISTICAL-ASSUMPTIONS.md` = 1569 lines**, last header `## 13.` (line 1375), **no `## 14`**; `docs/EVALUATION.md` = **220 lines**; `git diff de74da9 -- docs/STATISTICAL-ASSUMPTIONS.md docs/EVALUATION.md` = **0 bytes**.
- **`tests/test_integration.py` = 434 lines.** Its **criterion-9** pin (`:402–423`) asserts `git diff 02b86cd -- app/` empty, the `tests/` diff ⊆ `{tests/test_integration.py}`, no `app/` path in `git status --porcelain`, and under `tests/` only `?? tests/test_integration.py` — **so any new test file in Phase 13 is mechanically RED pre-commit**, and no existing test may be amended. Its **criterion-10** pin (`:426–434`) asserts S1–S4 and the §6 consumption sentence verbatim in `EVALUATION.md`, no `## 14` in `STATISTICAL-ASSUMPTIONS.md`, and last section `13` — **so both evidence documents stay byte-identical**.
- **Guard machinery (the zero-amendment argument):** `POISON_REGISTRY` exactly 7 keys (`tests/test_temporal_integrity.py:89–99`), `MATCHES_ENTRY_POINTS` the 5-tuple (`:101`), `PHASE10_CHECKPOINT = "8abe1ca"` (`:40`); `GOLDEN_PIN_FILES` six test files, **no docs path** (`tests/test_operational.py:64–71`); `BANNED_IMPORT_EXCEPTIONS` unchanged. No test reads README, ARCHITECTURE, KNOWN-LIMITATIONS, PLAN, or ROADMAP — the only docs-reading pins are the Phase 12 honesty pin over EVALUATION/SA, which stay byte-identical.
- **Drift to correct:** `README.md:18–20` still says Phase 12 *"checkpoint pending"* (Phase 12 committed at `de74da9`); the commit list at `README.md:230–235` ends at `02b86cd`. **`docs/briefs/phase-13.md` does not exist; no "research-ready" claim exists anywhere in the tree yet.**
- **`docs/KNOWN-LIMITATIONS.md` = 1547 lines:** intro lines 8–9 say Phase 12; Phase 12 section `:1387–1502`; `## Not yet applicable (as of Phase 12)` `:1504–1547`. **`docs/HEALTH-LOG.md` is monitor-owned.**

## glass-quant consultation — RUN 2026-10-24 (conductor top level); rulings ADV-13.1–ADV-13.11 BINDING (record, not a gate)

1. **ADV-13.1 (BLOCKER) — zero-statistics boundary.** Docs-only; zero new computed numbers/statistics; zero `app/` changes; zero new test files; zero amendments. Restatements only of the exact pinned literals listed in decision 6's table (population/accounting, calibration shares, draw aggregates, overdispersion, provenance strings, structural facts). Forbidden: any new sum, mean, difference, ratio, percentage, rounding, extrapolation, re-aggregation, new subset, or new precision. **`n_sims` is not sample size.**
2. **ADV-13.2 (BLOCKER) — NO §14.** The larger-n calibration registration lands in `docs/KNOWN-LIMITATIONS.md`'s Phase 13 section. `STATISTICAL-ASSUMPTIONS.md` and `EVALUATION.md` stay **byte-identical**; the Phase 12 pin stays green with no amendment. A future phase shipping new statistics authors its own section under a named amendment; Phase 13 does not pre-empt it. **No standalone research-readiness doc.**
3. **ADV-13.3 (BLOCKER) — a genuine pre-registration** with the exact content of decision 3 (status line + seven clauses). The numeric minimum-n trigger is **developer-territory**; the registration fixes procedure only; the future n-extending brief sets the numeric trigger.
4. **ADV-13.4 (BLOCKER) — R1–R12 verbatim** in the Phase 13 research-readiness subsection, and the banned-vocabulary rule of decision 4. The sanctioned negations are the only legal claim-adjacent occurrences.
5. **ADV-13.5 (BLOCKER) — stages 3/10 gap framing G1–G5** of decision 5. Honest count: **eight of ten stages exist**; the two missing stages are named. Building them is developer-territory; Phase 13 records the gap only.
6. **ADV-13.6 (BLOCKER) — docs-only integrity + the traceability audit** of decision 6: `git diff de74da9 -- app/ tests/` empty; evidence docs byte-identical; KNOWN-LIMITATIONS append-only (prior sections byte-identical; intro flip; Phase 13 appended; "Not yet applicable" finalized); the number table, cross-document consistency, stage-status consistency, historical-record check, honesty pins, banned vocabulary, README correction, ROADMAP discipline.
7. **ADV-13.7 (SHOULD-FIX, binding wording) — consolidation traps** of decision 7: no model-vs-baseline direction; no draw-sign inference; no overdispersion confirmation; no calibration-quality words; `n = 60`/`60 matches evaluated` banned; no "historical/real-world data" without "synthetic"; no determinism-as-validation; no cross-metric aggregation; scenarios are arbitrary documented knobs (`MULTIPLIER_MIN = 0.5`, `MULTIPLIER_MAX = 2.0`), labeled hypothetical, never "calibrated/empirically justified/data-driven"; no betting/AI vocabulary.
8. **ADV-13.8 (SHOULD-FIX) — evidence docs byte-identical;** stale §2(a)/§11(b)(ii) references reconciled by **annotation** (G5), never by editing.
9. **ADV-13.9 (NOTE) — zero-amendment carry** for `app/`, `tests/`, `scripts/`, `pytest.ini`, `conftest.py`, fixtures, and evidence docs; docs edits are expected and are **not** amendments; the three dirty protocol docs ride the Phase 13 checkpoint; the README drift correction is a restatement, not a new number.
10. **ADV-13.10 (BLOCKER gate) — Block 4 acceptance verified recorded (row 4); it rides the checkpoint unedited.** Phase 13 status `planned` → `in progress` (PENDING hash) at the docs step, then `committed` after the checkpoint. **NO Block 5 acceptance row.** Final-phase language: "Phase 13 committed" ≠ all ten stages implemented ≠ system complete.
11. **ADV-13.11 (NOTE) — re-run and record unchanged/green:** `tests/test_vocab_guards.py`; the `_ACCURACY_PATTERN` pin (`tests/test_vocab_guards.py:279` over `tests/test_phase7_separation.py:58`); `tests/test_evaluation.py::test_baseline_side_by_side_absolute_no_delta_no_ci_surface` (criterion 13); `tests/test_integration.py::test_docs_honesty_pins_s1_s4_consumption_no_section14`; `tests/test_operational.py::test_app_and_golden_files_byte_pinned_vs_phase11` (criterion 8); `tests/test_temporal_integrity.py::test_poison_coverage_registry_bijection_and_census` and `::test_poison_coverage_registry_negative_probes`; the full suite (188); the health script. **Do NOT add a naive doc-wide token scan** (false positives by construction; a new test file is mechanically blocked). The reviewer applies the ADV-13.4 list to the NEW Phase 13 sections only, with R1–R12 as allowlist.

## Design decisions (this brief resolves them)

1. **Docs-only, one DOCS step, no BUILD step (ADV-13.1/13.9).** The docs agent writes the six files in the work list; the reviewer audits them against this brief before the checkpoint. **Zero production code, zero test files, zero amendments.** `git diff de74da9 -- app/ tests/ scripts/ pytest.ini conftest.py fixtures/` must be empty; `git status --porcelain` must show docs paths only. The phase's defining property is its own acceptance criterion (AC1).
2. **No §14; the registration lands in KNOWN-LIMITATIONS (ADV-13.2/13.8).** `docs/STATISTICAL-ASSUMPTIONS.md` and `docs/EVALUATION.md` are **byte-identical to `de74da9`** (1569 / 220 lines; no `## 14`; S1–S4 and §6 verbatim). The evidence documents are closed; the Phase 12 honesty pin stays green with no amendment. **No standalone research-readiness document** and no new deliverable docs file (this brief excepted).
3. **The pre-registration text — status line + seven clauses (ADV-13.3, BLOCKER).** The Phase 13 section carries this block, verbatim in substance:

> **Status: PRE-REGISTRATION — authored 2026-10-24; computes nothing; not run.**
>
> 1. **Current pinned state.** The evaluated population is 30 clean predictions (primary) and 57 predictions (secondary) from 60 targets = 3 structural refusals + 27 flagged + 30 clean (57 = 27 + 30). All results are on the frozen synthetic fixtures; no real data has been accepted.
> 2. **Condition for re-evaluation.** Re-evaluation happens only through a named brief that either adds checked-in fixtures or accepts real data through the loader with provenance and license recorded in `docs/DATA-SOURCES.md`; that brief re-derives and re-pins (never widens), re-asserts the run digest before any metric computes, and leaves this protocol unchanged. `n_sims` is not a trigger. This registration commits to no data acquisition.
> 3. **Populations.** PRIMARY = unflagged + `CONVERGED`; SECONDARY = all emitted predictions including flagged; refusals are excluded from every metric and counted only in accounting; `MISSING_NO_HISTORY` baselines are the refusal targets; model and baseline carry the same population and the same `n`; no refusal-inclusive metric container exists; `n` is stated on every number; no post-hoc subsetting.
> 4. **Metrics — unchanged §13(a)–(c).** Log loss = `−ln(p_realized)`, natural log, no ε-clamp of any spelling; Brier = the full 3-outcome sum, no halving; RPS = ½-scaled, 3-category ordinal over H < D < A; calibration = exactly 5 equal-width bins with edges 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, last bin inclusive, pooled (p, realized-indicator) pairs, empty bins reported as `n = 0`/`None` and never merged or re-binned; draw aggregate = realized draw rate − mean predicted draw probability per population; overdispersion = ddof = 0, descriptive. The fine-grained scoreline RPS remains rejected. No second scoring path.
> 5. **Constraints that do not relax with `n`.** No confidence interval, standard error, bootstrap, significance test, p-value, or chi-square. No delta, ratio, percentage, ranking, improvement, better/worse, or verdict; absolute side-by-side values only; no "beating". Calibration is descriptive only. The synthetic caveat stands until real data is accepted. §13(d)'s bans are permanent.
> 6. **What is NOT pre-committed.** No numeric minimum-n threshold; no expected metric value or range; no accuracy target; no pass/fail; no significance level; no CI method; no model-selection, tuning, or variant plan; no improvement promise; no data-acquisition commitment — each would need its own named brief.
> 7. **Change control.** Append-only. Any change to these clauses is a named brief. No silent drift.

The **numeric minimum-n trigger is developer-territory** and is deliberately absent; the registration fixes procedure only (ADV-13.3).

4. **R1–R12 verbatim + the banned-vocabulary audit (ADV-13.4, BLOCKER).** The research-readiness subsection carries these twelve sentences **verbatim**, labelled R1–R12:

R1. "As of Phase 13 the evaluated population is exactly 30 clean predictions (primary) and 57 predictions (secondary) from 60 targets = 3 structural refusals + 27 flagged + 30 clean; the 3 refusals are excluded from every metric and appear only in accounting."
R2. "These numbers are descriptive evaluations of a small synthetic sample; they are not evidence of predictive skill."
R3. "Calibration is descriptive only at this n: 73 of 90 primary pairs (share 0.8111111111111111) and 137 of 171 secondary pairs (share 0.8011695906432749) fall in the [0.2, 0.4) bin."
R4. "Model and baseline values appear side by side as absolute quantities with the same formulas, the same population, and the same n; no difference, ratio, percentage, ranking, or verdict between them is computed or claimed."
R5. "Calibration bins are counts and frequencies only; no reliability or goodness-of-fit claim follows from them."
R6. "No forecast is called validated, accurate, or beating anything."
R7. "No confidence interval, standard error, bootstrap, significance test, p-value, or chi-square statistic exists anywhere in the evaluation surface; every reported number is a point value with its n."
R8. "Determinism and replay are provenance properties — identical inputs, model version, seed, and config produce identical output — not validation, not accuracy, and not evidence of predictive skill."
R9. "All results are on hand-authored synthetic fixtures; real-data behaviour is untested end to end, and the loader's real-file quirks are a documented limitation."
R10. "Runtime figures are load-labelled observations, not an SLA or a performance guarantee."
R11. "Pipeline stages 3 (PRE-MATCH STATE, app/state/) and 10 (MODEL IMPROVEMENT, app/improvement/) are unbuilt; their absence is a documented architectural gap, not a defect in the existing forecasts."
R12. "'Research-ready' here means the documentation, provenance, and reproducibility conditions for research use are met: every number is traceable to a pinned test literal, every known limitation is stated, the evidence documents are closed and pre-registered, and the pipeline is deterministic and replayable. It does not mean the model is validated, accurate, statistically powered, a calibration-quality claim, generalisable, production-ready, or ready for real-data claims."

**Banned affirmative vocabulary (claims) in the NEW Phase 13 sections** — verbatim list:

```
validated, accurate, accuracy, beating, beats, outperforms, better, worse,
superior, inferior, improvement, edge, skill, predictive power,
well-calibrated, reliable, trustworthy, good fit, robust, generalisable,
production-ready, deployment-ready, research-grade, publication-ready,
peer-review-ready, comparable, close to, in line with, roughly equal, on
par, marginally, slightly, trails, leads, ahead of, behind, matches the
baseline, nearly as good, competitive, significant, statistically
significant, correlated (as claim), confirms, proves, demonstrates skill,
evidence of skill (affirmative), the model is calibrated, calibration is
good, within tolerance, certain, guaranteed, will predict, always, never
wrong, all ten stages implemented, complete pipeline, fully implemented,
the system is complete, n is large enough, sufficient sample,
statistically powered, AI-powered, machine learning, neural, LLM,
cloud-ready, scalable.
```

**Audit rule (claims scan).** The list is scanned in the **new Phase 13 text only** (KNOWN-LIMITATIONS Phase 13 section + final NYA + README Phase 13 paragraph + ARCHITECTURE Phase 13 additions + PLAN status line + ROADMAP Phase 13 note + PROGRESS-LOG Phase 13 entry). Three structural classes are **not claims** and are not RED: (a) the R1–R12 block verbatim; (b) the registration's own negation clauses (3, 5, 6) and G5's two quoted stale locators, which ADV-13.3/ADV-13.5 require; (c) filesystem/module identifiers (`app/improvement/`). Everything else is a claim and must not occur. The brief itself is excluded (it quotes the list by construction). This is the only reading under which the required negations and annotation coexist with the ban; the reviewer records the classification of any hit, and a genuine affirmative hit is RED.

5. **Stages 3/10 — G1–G5, eight of ten (ADV-13.5, BLOCKER).** The Phase 13 section carries this content:

G1. **Stage 3 (PRE-MATCH STATE, `app/state/`) is unbuilt.** No separate as-of-kickoff snapshot artifact exists. This is **not** a leakage gap: the cutoff is enforced inside every history-consuming calculation (strict `date < as_of`), and the poison registry pins `fit` / `build_forecast` / `compute_features` / `run_walk_forward` / `evaluate_predictions`. Forecast immutability is a property of the stored `Forecast`, not of a stage-3 snapshot. Unbuilt, not rejected; building it is a future scope decision.
G2. **Stage 10 (MODEL IMPROVEMENT, `app/improvement/`) is unbuilt.** No tuning loop, variant search, model selection, or re-fit machinery exists. It is structurally absent — **not** "protected by a mechanism". Exactly one model spec exists (`poisson-mle-v1`); `run_walk_forward` takes no spec/variant/config/seed loop; the single-model-spec surface is pinned closed. If ever built, its brief must carry a protected-split design (tuning data disjoint from evaluation) before any tuning runs.
G3. **Their absence does not weaken the existing evidence; it limits what the system can do.** The evidence is descriptive and small-n either way. No forecast is called validated, accurate, or beating anything.
G4. **Phase 12 KNOWN-LIMITATIONS item 7's "Their completion is Phase 13's work" is CLARIFIED:** Phase 13 completes their **documentation**, not the stages. Both remain unbuilt after Phase 13.
G5. **`STATISTICAL-ASSUMPTIONS` §2(a) ("model-improvement loop (Phase 12/13, …)") and §11(b)(ii) ("Phase 12/stage-10's protected improvement loop") are stale forward references** — read as historical candidates, not work performed. The register stays **byte-unchanged**; the annotation lives here, never in the evidence document.

**Honest count: eight of the ten stages exist; stage 3 and stage 10 are the two missing stages, named.** Do **not** claim "the system is complete", "all ten stages implemented", "stage 3 unnecessary", "stage 10 not needed", or that "the protected improvement loop exists". Building stages 3/10 is developer-territory; Phase 13 records the gap only.

6. **Docs-only integrity and the traceability audit (ADV-13.6, BLOCKER).** KNOWN-LIMITATIONS is **append-only**: `git diff de74da9 -- docs/KNOWN-LIMITATIONS.md` may show hunks only (a) in the intro's Phase line and (b) from `## Not yet applicable` to EOF; **the region between is byte-identical**, including Phase 11 item 3 (`:1261–1267`) and Phase 12 item 7 (`:1483–1489`). The intro flips to "Phase 13 (Consolidation and research readiness), 2026-10-24"; the Phase 13 section is appended; the "Not yet applicable" section is replaced by its final form (decision 8). **The traceability audit is the test-equivalent** — every number in the shipped Phase 13 documentation edits (the six files in the work list) must appear in this table with its exact string, source, and `n`. The brief itself is excluded: it is the audit's instruction and carries file:line locators, not restatements.

| Exact string | Pinned source | `n` |
|---|---|---|
| `60`, `3`, `27`, `30`, `57`; `60 = 3 + 27 + 30`; `57 = 27 + 30` | `tests/test_evaluation.py:205–213`; `tests/test_integration.py:227–231`; EVALUATION.md §2; SA §13(b) | 60 targets; 30 primary; 57 secondary |
| `73/90 = 0.8111111111111111`; `137/171 = 0.8011695906432749` | `tests/test_evaluation.py:78` (`GOLDEN_DOMINANT_SHARE`); EVALUATION.md §4; KL Phase 11 item 3 | 90 pairs; 171 pairs |
| `−0.03437540133650058`; `−0.025271786352718206`; `7/30`; `14/57` | `tests/test_evaluation.py:80`; EVALUATION.md §4; KL Phase 11 item 4 | 30; 57 |
| `114`, `149`, `149/114`, `1.307`, `0.967`, `0.9757` | `tests/test_evaluation.py:419–437`; EVALUATION.md §4; KL Phase 11 item 5 | 114 |
| `150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f` | `tests/test_evaluation.py:50`; `tests/test_backtesting.py:78`; EVALUATION.md §6; `tests/test_integration.py:44` | n/a |
| `ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47` | `tests/test_integration.py:68`; KL Phase 12 item 2 | n/a |
| `f779fc0a952e00ecd904c8019b288c43326635cb5c5a698f2f74870b11d57e39`; `5a9da621c678933b0a5f0320a79c8c245783b34bbaf59a73e0fd7d7609d916a9` | EVALUATION.md §6:184–186; DATA-SOURCES.md:85–86 | n/a |
| `de74da9` / `de74da989b33fcce5a6c9e503d772f4d2425af84` | git; ROADMAP Phase 12 note; PROGRESS-LOG Phase 12 | n/a |
| `188` tests; `28` modules | `pytest --collect-only -q`; ARCHITECTURE.md:167,195; README.md:43,237,373 | n/a |
| `800` s valve | `tests/test_health_script.py:21` | n/a |
| `SCHEMA_VERSION = 2` | `app/storage/forecasts_db.py:37`; `tests/test_integration.py:377` | n/a |
| `EVALUATION_VERSION = 1` | `app/evaluation/evaluate.py:40`; EVALUATION.md §6 | n/a |
| `8 of 10` stages | HANDOFF Part IV; ARCHITECTURE stage table; `app/` listing | n/a |
| `5` bins; edges `0.0, 0.2, 0.4, 0.6, 0.8, 1.0` | SA §13(c); `tests/test_evaluation.py:62–76` | n/a (protocol) |

**Rules:** (i) no number outside the table; (ii) **the 12 `GOLDEN_METRICS` literals are NOT restated** (not in ADV-13.1's allowed set — reference §13(a)–(c) and EVALUATION.md §4 by pointer only); (iii) no new derived quantity of any kind; (iv) scan the new text for new `%` signs, new high-precision decimals, and comparative words — a hit is RED; (v) dates (`2026-10-24`), section numbers (§13, §2(a), §11(b)(ii)), and phase/block numbers are structural references, not quantities. **Cross-document consistency:** `30`/`57` and `60 = 3 + 27 + 30` must agree across KL Phases 11/12/13, EVALUATION §2, SA §13(b), README, ARCHITECTURE, and PROGRESS-LOG; shares, draw aggregates, overdispersion, provenance strings, and structural facts must be exact. **Stage-status consistency:** "eight of ten; stages 3/10 unbuilt/planned" in ARCHITECTURE, PLAN, KL Phases 12/13, and README; no "complete pipeline". **Historical records:** Phases 7–10 `n = 0` statements (`KL:688`, `:858`, `:979`, `:1125`) and the Phase 11/12 forward references are **never rewritten**. The reviewer records the table walk, the grep matrix, and the scan in the verdict and PROGRESS-LOG; any failure is RED, never a pin edit.

7. **Consolidation traps (ADV-13.7, binding wording).** New Phase 13 text must not: characterise model-vs-baseline direction ("baseline better", "model worse", "close", "competitive", "gap small"); infer draw direction ("under-predicts draws", "bias confirmed/reversed"); confirm overdispersion ("Poisson holds", "no overdispersion found"); use calibration-quality words; write `n = 60` or "60 matches evaluated" (60 targets = 3 + 27 + 30; evaluated `n` = 30/57); write "historical/real-world data" without "synthetic"; treat determinism as validation; aggregate across metrics ("overall score", "composite", "average across metrics", "evidence strong/moderate/weak", "confidence rating"); or call scenarios "calibrated/empirically justified/data-driven" — scenarios are arbitrary documented knobs (`MULTIPLIER_MIN = 0.5`, `MULTIPLIER_MAX = 2.0`), labeled hypothetical. No betting/AI vocabulary.

8. **"Not yet applicable — final" (ADV-13.6).** Replace the live tail section with exactly this final form (title and content):

> ## Not yet applicable — final (as of Phase 13)
>
> The limitations recorded for each implemented phase are listed above. Two pipeline stages remain unbuilt and are therefore not listed as limitations of running code: **stage 3** (PRE-MATCH STATE, `app/state/`) and **stage 10** (MODEL IMPROVEMENT, `app/improvement/`). There are no pre-match snapshots and no tuning loop to mis-trust; their absence is documented in the Phase 13 section above. Earlier `n = 0` statements (Phases 7–10) and forward references in earlier sections are historical records of those phases and are never rewritten.
>
> Data provenance and format limitations remain in `docs/DATA-SOURCES.md`; the model's statistical assumptions and their weaknesses are in `docs/STATISTICAL-ASSUMPTIONS.md`; the evaluation limitations are in `docs/EVALUATION.md` and the Phase 11 section above.

Do **not** claim "every possible limitation is listed".

9. **Evidence docs untouched; stale references by annotation (ADV-13.8).** No edit to `docs/STATISTICAL-ASSUMPTIONS.md` or `docs/EVALUATION.md`; G5 is the only reconciliation of §2(a)/§11(b)(ii), and it lives in KNOWN-LIMITATIONS. The register's historical text stays as written.

10. **Zero-amendment carry and riding disposition (ADV-13.9).** No file under `app/`, no test, no script, no config, no fixture, no evidence doc changes. Docs edits are not amendments. The three dirty protocol docs (`docs/HEALTH-LOG.md`, `docs/PROGRESS-LOG.md`, `docs/ROADMAP.md`) plus `docs/briefs/phase-13.md` ride the Phase 13 checkpoint. The README correction is a restatement of the existing `de74da9`, not a new number.

11. **Block gate, status flips, final-phase language (ADV-13.10).** Block 4 acceptance is verified (row 4) and rides unedited. `docs/ROADMAP.md`: Phase 13 row `planned` → `in progress`; add the Phase 13 status note with checkpoint hash **`PENDING`** (the git agent replaces `PENDING` with the checkpoint hash and flips the row to `committed` after the commit, as in Phases 4–12). **Block table byte-identical; rows 1–12 byte-identical; Phase 13's status cell is the only phase-row change; acceptance rows 1–4 byte-identical; NO Block 5 acceptance row.** Final-phase language is permitted ("Phase 13 is the final phase of the thirteen-phase map"); completeness claims are not ("all ten stages implemented", "the system is complete", "complete pipeline"). "Phase 13 committed" is a phase-status fact, not a completeness claim.

12. **README/PLAN status conventions — no new drift.** README's Phase 13 paragraph makes **no pre-commit hash claim** (it says the phase is documentation-only and points to ROADMAP/PROGRESS-LOG for the checkpoint), so the final README does not repeat the Phase 12 "checkpoint pending" drift; the Phase 12 paragraph is corrected to `de74da9`. PLAN's status line records that Phase 13 (the plan's final phase) reached its docs step on 2026-10-24 and that the plan names no Phase 14; §5 layer 4 already reads IMPLEMENTED (Phase 12) and is unchanged. ARCHITECTURE's status line reads Phases 9–13 and states eight of ten stages exist.

## Files and directories to create or modify

DOCS step only (no BUILD step):

1. `docs/KNOWN-LIMITATIONS.md` — (a) intro lines 8–9: Phase 12 → **Phase 13 (Consolidation and research readiness)**, date unchanged; (b) append **`## Phase 13`** with seven items: (1) docs-only consolidation / zero code / zero test files / zero amendments / the traceability audit as evidence / 188 tests unchanged; (2) the larger-n calibration pre-registration (decision 3, status + clauses 1–7); (3) research readiness — **R1–R12 verbatim** (decision 4) and the R12 definition; (4) stages 3/10 — **G1–G5** (decision 5), eight of ten, Phase 12 item 7 clarified, §2(a)/§11(b)(ii) annotated; (5) what Phase 13 does not do — no §14, no new doc, no new statistic, no data acquisition, no stage build, no API, no dependency; the numeric minimum-n is a future brief's; (6) recorded state — 188 tests / 28 modules / 800 s valve / `SCHEMA_VERSION = 2` / `EVALUATION_VERSION = 1`; load-labelled runtime record, no SLA; (7) historical records — Phases 1–12 byte-identical, `n = 0` statements and forward references never rewritten; (c) replace `## Not yet applicable (as of Phase 12)` with the final form of decision 8. **Prior Phase 1–12 sections byte-identical.**
2. `README.md` — (a) new **Phase 13** paragraph at the top of "Current state": documentation only; zero production code, zero test files, zero amendments, zero new statistics; KNOWN-LIMITATIONS completed; the pre-registration (procedure only; computes nothing; not run; the numeric minimum-n trigger is a future brief's); the research-readiness statement is **R1–R12** in `docs/KNOWN-LIMITATIONS.md` Phase 13 (pointer; R12 defines the term and its limits); **eight of the ten stages exist — stage 3 (`app/state/`) and stage 10 (`app/improvement/`) remain unbuilt**; `docs/STATISTICAL-ASSUMPTIONS.md` and `docs/EVALUATION.md` byte-identical (no §14); **188 tests**; no pre-commit hash claim. (b) Phase 12 paragraph: *"checkpoint pending"* → *"committed at `de74da9`"*. (c) commit list (`:230–235`): add **`de74da9`** (Integration and verification) and note that Phase 13 is documentation only with its checkpoint recorded in ROADMAP/PROGRESS-LOG. No other README paragraph changes.
3. `docs/ARCHITECTURE.md` — status line **"as of 2026-10-24 (Phases 9–13)"**; add the Phase 13 sentence (no module; docs-only consolidation; KNOWN-LIMITATIONS completed; pre-registration and R1–R12 written; **eight of the ten stages exist**, stages 3 and 10 remain planned); make the stage table's caption state the honest count; change the instantiation-status heading to **"(2026-10-24, Phase 13)"**; keep `28 modules, 188 tests`. No stage row changes; no code claims.
4. `docs/PLAN.md` — **status line only**: append that Phase 13 (the plan's final phase) reached its docs step on 2026-10-24 and that the plan names no Phase 14. §5 layer 4 is already IMPLEMENTED (Phase 12) — unchanged. No directory-tree edit.
5. `docs/ROADMAP.md` — Phase 13 row `planned` → `in progress`; append the Phase 13 status note (brief of record, docs-only scope, ADV-13.1–13.11 consulted 2026-10-24, zero developer questions, **checkpoint hash PENDING**, Block 4 row rides unedited, **NO Block 5 row**). **Block table, rows 1–12, and acceptance rows 1–4 byte-identical** except Phase 13's status cell.
6. `docs/PROGRESS-LOG.md` — append the Phase 13 entry (heading `## 2026-10-24 — Phase 13 (Consolidation and research readiness) — built (docs-only), reviewed PASS (first pass); checkpoint PENDING`): brief of record; consult record; docs-only proof (`git diff de74da9 -- app/ tests/` empty; docs-only status); the traceability audit result (number table walk, cross-doc matrix, banned-vocab scan, stage-status check, historical-record check); the registration / R1–R12 / G1–G5 recorded; the recorded executions (suite 188 ×2 identical, offline, health OK; load-labelled, no SLA); Block 4 gate verified and row unedited; **no Block 5 row**; riding note (the three dirty protocol docs + this brief); checkpoint hash **PENDING**. Do not rewrite the Phase 12 entry.

Do **not** create or modify: any file under `app/`, any test file, `scripts/health-check.sh`, `pytest.ini`, `conftest.py`, `fixtures/`, `docs/STATISTICAL-ASSUMPTIONS.md`, `docs/EVALUATION.md`, `docs/HEALTH-LOG.md` (monitor-owned), `docs/HANDOFF.md`, `docs/DATA-SOURCES.md`, any new docs file, requirements/pyproject, CI, Docker, `data/`, any committed DB.

## Dependencies

- **None new.** The docs step uses only `git`, `grep`, `wc`, `sha256sum`, and the existing `.venv` pytest for the guard re-runs. No third-party package; no numeric/ML stack; no API change; no environment knob; no CI/Docker/services.

## Acceptance criteria (1:1 auditable; each maps to one command/grep/file check)

**Mapping note.** No criterion maps to a test function: a new test file is mechanically RED pre-commit (Phase 12 criterion 9, `tests/test_integration.py:402–423`) and no existing test may be amended (ADV-13.1). The 1:1 map is **AC# → reviewer check**; the reviewer records the command output and the table walk in the verdict and PROGRESS-LOG. A failed check is RED and a STOP-and-report.

1. **Docs-only boundary** — `git diff de74da9 -- app/ tests/ scripts/ pytest.ini conftest.py fixtures/` is empty (0 bytes); `git status --porcelain` shows only documentation paths (`README.md` plus `docs/`) and the untracked `docs/briefs/phase-13.md`; no `app/` or `tests/` path appears.
2. **Evidence docs byte-identical** — `git diff de74da9 -- docs/STATISTICAL-ASSUMPTIONS.md docs/EVALUATION.md` is empty; `wc -l` = 1569 / 220; no `## 14`; last SA section 13; S1–S4 and the §6 sentence present.
3. **KNOWN-LIMITATIONS append-only + content complete** — `git diff de74da9 -- docs/KNOWN-LIMITATIONS.md` shows hunks only in the intro Phase line and from `## Not yet applicable` to EOF; the Phase 13 section has all seven items; the intro reads Phase 13; the final NYA title is exact.
4. **Registration complete** — the status line and all seven clauses are present; the numeric minimum-n threshold, expected metric value/range, accuracy target, pass/fail, significance level, CI method, model-selection/tuning plan, and data-acquisition commitment are all absent; `n_sims` is not treated as sample size.
5. **R1–R12 verbatim** — twelve labelled sentences byte-match this brief (line-wrap-normalized); no paraphrase.
6. **G1–G5 present** — stages 3/10 unbuilt; the honest count "eight of ten"; G4's clarification; G5's annotation of §2(a)/§11(b)(ii); the forbidden completeness claims absent.
7. **Banned vocabulary clean** — the ADV-13.4 list applied to the new Phase 13 text only, with the decision-4 allowlist; zero affirmative hits; any hit classified and recorded.
8. **Traceability table complete** — every number in the new/edited docs text (not the brief) matches a table row (exact string, source, `n`); the 12 `GOLDEN_METRICS` literals are not restated; no new `%` sign, high-precision decimal, derived quantity, or comparative word.
9. **Cross-document consistency** — the decision-6 matrix greps clean in all named locations; shares, draw/overdispersion, provenance, and structural facts exact; stage status consistent.
10. **README corrected** — Phase 13 paragraph present; Phase 12 paragraph reads `de74da9` (no "checkpoint pending"); commit list includes `de74da9`; 188 tests; stages 3/10 unbuilt; R1–R12 pointer.
11. **ROADMAP discipline** — Phase 13 row `in progress` with **PENDING** at the docs step; block table byte-identical; rows 1–12 byte-identical; Phase 13's status cell is the only phase-row change; acceptance rows 1–4 byte-identical; **no Block 5 row**; Block 4 row verified and unedited.
12. **Historical records + final NYA** — Phases 7–10 `n = 0` statements (`KL:688`, `:858`, `:979`, `:1125`), Phase 11 item 3, and Phase 12 item 7 byte-identical; final NYA exact; no "every possible limitation is listed".
13. **Honesty/guard pins green** — re-run `tests/test_vocab_guards.py`; `tests/test_evaluation.py::test_baseline_side_by_side_absolute_no_delta_no_ci_surface`; `tests/test_integration.py::test_docs_honesty_pins_s1_s4_consumption_no_section14`; `tests/test_operational.py::test_app_and_golden_files_byte_pinned_vs_phase11`; `tests/test_temporal_integrity.py::test_poison_coverage_registry_bijection_and_census` and `::test_poison_coverage_registry_negative_probes` — all green, no amendment.
14. **Suite gate (recorded execution)** — `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` reports **188 passed**, 0 failed/errors/skipped/xfailed/xpassed, **twice with identical outcomes**; one offline `unshare -rn bash -c 'ip link set lo up && … pytest -q'` run recorded; `bash scripts/health-check.sh` completes `OK:` (`182 passed, 6 deselected` ×2, determinism `OK:`, skips/xfails `none`, pip clean, nine headers, inside the untouched 800 s valve); all timings load-labelled, no SLA.
15. **Clone post-commit probe + no new deps + no skip/xfail** — a throwaway clone at the checkpoint runs the full suite green (docs-only, but run it; Phase 11 C3 lesson); no third-party dependency added; no skip/xfail anywhere; runtime figures load-labelled.

## Amendments

**Expected ZERO (ADV-13.1/13.9).** No existing test, guard, script, config, fixture, or evidence document is amended; docs edits are not amendments. If any guard fails because of a docs edit, **STOP-and-report** — do not re-point a pin, do not edit a test, do not widen an allowlist. A forced amendment is a scope violation.

## Out of scope (nothing here may be built, imported, tested, or documented as done)

1. **Stages 3 and 10** — `app/state/` and `app/improvement/` remain unbuilt; no tuning loop, no snapshot artifact, no protected-split machinery.
2. **§14 or any addition to `STATISTICAL-ASSUMPTIONS.md` / `EVALUATION.md`** — both byte-identical.
3. **Any new docs file** — no `RESEARCH-READINESS.md`, no `CONSOLIDATION.md`, no standalone registration document.
4. **Any new or amended test file** — mechanically RED (Phase 12 criterion 9).
5. **Any production code, API, schema, dependency, script, or config change.**
6. **Any new statistic or derived number** — no sum, mean, difference, ratio, percentage, rounding, extrapolation, re-aggregation, new subset, or new precision; no restatement of the 12 `GOLDEN_METRICS` literals.
7. **Any data acquisition, real data, fixture edit, or `DATA-SOURCES.md` change.**
8. **Any numeric minimum-n trigger, expected metric range, accuracy target, pass/fail, significance level, CI method, or model-selection/tuning plan.**
9. **Any claim vocabulary** — no validation, accuracy, beating, model-vs-baseline direction, draw-sign inference, overdispersion confirmation, calibration-quality word, `n = 60`, determinism-as-validation, cross-metric aggregation, or scenario "calibrated" language.
10. **Any Block 5 acceptance row; any edit to the block table or acceptance rows 1–4; any edit to `docs/HEALTH-LOG.md`.**
11. **Committing outside the checkpoint protocol; pushing without developer authorization.**

## Risks

1. **Number drift in prose (highest).** A single derived number or restated metric literal would break the zero-statistics boundary. Control: the decision-6 table is the complete allowed set; the reviewer walks every number; any miss is RED.
2. **Banned-vocabulary leakage** — especially stage names, the G5 locators, and the registration's negation clauses. Control: the decision-4 claims-scan allowlist; the reviewer records classification; no mechanical doc-wide scan (ADV-13.11).
3. **Accidental edit to an evidence document or a prior KL section** — control: `git diff de74da9` gates (AC2/AC3/AC12); the Phase 12 honesty pin re-run (AC13).
4. **Scope creep toward §14, stage building, data acquisition, or a numeric trigger** — control: out-of-scope list; STOP-and-report; the registration deliberately omits the number.
5. **Protocol drift in ROADMAP** — adding a Block 5 row or editing row 4 — control: AC11's byte checks; the row rides unedited.
6. **Leaving `PENDING` in ROADMAP/PROGRESS-LOG or creating a new README "checkpoint pending" drift** — control: the PENDING→hash convention (decision 11) and README's no-pre-commit-hash rule (decision 12).
7. **Post-commit latent RED** — control: the clone probe (AC15), the Phase 11 C3 lesson.

## Open questions for the developer

**None.** Every choice is resolved by ADV-13.1–ADV-13.11 and existing registrations. The one developer-territory item — the **numeric minimum-n trigger** — is deliberately **not** decided by this phase; it belongs to a future n-extending brief (ADV-13.3), and the registration commits to no data acquisition. **Block 5 acceptance is the developer's at the final boundary, after the Phase 13 commit and monitor sweep; this phase adds no Block 5 acceptance row.**

---

*Brief authored by glass-architect 2026-10-24 against HANDOFF IX-13 and glass-quant ADV-13.1–ADV-13.11 (consulted at conductor top level, 2026-10-24; rulings binding). The docs agent implements Phase 13 exactly as written; any structural surprise is a STOP-and-report, not a decision.*
