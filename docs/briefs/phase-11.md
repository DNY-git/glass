# PHASE 11 BRIEF — FORECAST EVALUATION, THE EVIDENCE GATE (BLOCK 4, PHASE 2 OF 3)

Status: proposed (2026-10-22, glass-architect). Per `docs/ROADMAP.md` this is **Block 4, Phase 11 — the block's second phase**; block mode applies: this brief plans Phase 11 only (Phase 12 is not planned here). Blocks 1–3 developer acceptance rows are recorded (roadmap block-acceptance table, rows dated 2026-10-17 / 2026-10-19 / 2026-10-22 — neither duplicated nor edited here), and Block 4 was accepted-to-start at the Phase 10 boundary; per the Phase 10 brief, Phases 11 and 12 run inside Block 4 with no further block boundary — **the constitutional block gate to start Phase 11 is satisfied.** **glass-quant was consulted** (mandatory; run at conductor top level, 2026-10-22) — rulings **ADV-1–ADV-14** are binding design constraints, recorded below and cited inline.

**Scope anchor (Phase 8/10 precedent): Phase 11 is HANDOFF Part IX item 11 "Forecast evaluation" — it is NOT IX-12 integration and verification** (Phase 12's end-to-end determinism replay, which must CONSUME this phase's outputs and never recompute them) **and NOT pipeline stage 10 model improvement** (`app/improvement/` stays PLANNED; this phase is READ-ONLY over the frozen model, forecast, and backtest artifacts — no re-tuning, no variant, no config, no fixture edit).

## Objective

Deliver HANDOFF Part IX item 11 **verbatim** — *"Forecast evaluation — log loss, Brier, RPS against hand-computed values and baselines, calibration over many observations, idempotent evaluation records"* (HANDOFF:153–155) — as: the first-ever scoring of the pre-registered walk-forward predictions against realized results, i.e. the **evidence gate** that closes §11's three-step line (Phase 8 defenses shipped → Phase 9 machinery shipped, still no metrics → **Phase 11 first scoring**). **Milestone: the evaluated observation count goes from exactly 0 to exactly 57 (secondary) / 30 (primary) for the first time**, and the constitution's "idempotent ingestion and evaluation … evaluation records that never alter original forecasts" (HANDOFF:126–127) becomes a shipped, tested fact. The scored population, metric formulas, calibration bin edges, side-by-side legality, and vocabulary are fixed in `docs/STATISTICAL-ASSUMPTIONS.md` **§13, authored BEFORE any build code** (this phase's pre-build section; decision 5) so that nothing — population, bins, or formula — is chosen post-score.

## State verified before writing this brief (probed 2026-10-22)

- **HEAD = `8abe1ca`** ("phase 10: health-check restructure to 3 runs, valve re-tune down, corruption and atomicity tests"); chain `… → ea92667 → 80b8f79 → 8abe1ca`. **Dirty tree = exactly the three protocol docs** (`M docs/HEALTH-LOG.md`, `M docs/PROGRESS-LOG.md`, `M docs/ROADMAP.md` — Phase 10 monitor/progress/roadmap updates) — all must ride Phase 11's checkpoint commit (monitor WARN carried).
- **Suite of record: 155 passed** (Phase 10, committed `8abe1ca`); health valve = **800 s** (`tests/test_health_script.py:21`, "AMENDMENT A2 (Phase 10)", 105 → 105 lines) — untouched this phase. All reviewer verdicts through Phase 10 first-pass PASS; all monitor sweeps WARN with the carried dirty-docs finding. Block 3 acceptance row (quoted verbatim in the Phase 10 brief) also discharges Phase 11's block gate.
- **`wc -l` re-verified (current → this phase's projection basis):** `test_temporal_integrity.py` 452, `test_vocab_guards.py` 440, `test_fixtures_and_hygiene.py` 626, `test_phase4_separation.py` 834, `test_phase5_separation.py` 574, `test_phase6_separation.py` 510, `test_phase7_separation.py` 443, `test_backtesting.py` 653, `test_storage.py` 425, `test_operational.py` 409, `test_health_script.py` 105, `docs/STATISTICAL-ASSUMPTIONS.md` 1373 (ends at §12; **no §13 exists — this phase authors it**), `app/storage/forecasts_db.py` 339, `scripts/health-check.sh` 98 (untouched).
- **§11(d) verbatim (the sanctioned bump):** *"the evaluation-record table is **Phase 11's** schema bump — `SCHEMA_VERSION` stays 1 until then. Flagged for the Phase 9 and 11 briefs, **not fixed here**: `get_forecast()` fetches a single row per natural key (`ORDER BY as_of, input_digest`, single fetch) — ambiguous once Phase 9 stores many predictions per fixture; those briefs must address it explicitly."* §12(a) fixes the baseline's only legal form; §12(b) registers **60 = 3 + 27 + 30** and **57 = 27 + 30**; §12(c) fixes bin counts pre-score and bans "beating" claims **even after Phase 11 runs**; §12(d): *"the one-line natural-key join is **re-established at Phase 11**"*; §12 carries the golden run digest `150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f` ("re-derive on change, never widen, never delete"). §2b: *"overdispersion is explicitly checked in Phase 11 (variance-vs-mean diagnostics alongside predictive scores)"*; §2f: *"draw-frequency calibration against realized results is part of Phase 11's evaluation."*
- **Amendment collision surfaces pinned (every line count below is `wc -l`-verified):** `test_temporal_integrity.py` — `PHASE8_CHECKPOINT = "ea92667"` (`:39`), `PRE_EXISTING_APP` 12-path tuple incl. `app/storage`, excl. `app/backtesting` (`:40–43`), `POISON_REGISTRY` 6 keys (`:88–95`, set pin `:186–189`, per-entry pins `:190–195`, stale comment "exactly five keys" `:184`), `MATCHES_ENTRY_POINTS` 4-tuple (`:99`, equality `:205`), byte-pin hunk (`:412–421`), criterion-8 knob scan over four entries with banned set `{spec,specs,configs,variant,variants,candidate,seed}` and the `config`/signature sub-pins (`:444–452`). `test_backtesting.py` — the **AMENDMENT A1/A2/A3 exactness block** (`:626–653`: checkpoint literal, 6-key registry set, 4-tuple census, `PRE_EXISTING_APP` set + `"app/backtesting" not in`, `len(...) == 13`, five-package pure set) **plus** the criterion-11 storage pins `tables == ("forecasts",)` (`:582–583`), `SCHEMA_VERSION == 1` (`:586`), "exactly one table" comment (`:577–578`); its five-entry knob scan (`:413–419`) is **not** extended (decision 12). `test_fixtures_and_hygiene.py` — `ALLOWED_APP_IMPORTS` 13 keys with per-package values (`:49–63`), `app.storage` value `{domain, forecasts, storage}` (`:58`), `PURE_PACKAGES` five-set (`:64`), `BANNED_IMPORT_EXCEPTIONS` exact two-entry map (`:42–45`, **unchanged**). Separation files — `len(hygiene.ALLOWED_APP_IMPORTS) == 13` at phase4 `:803`, phase5 `:471`, phase6 `:424`, phase7 `:391`; key-union literals at phase4 `:804–813`, phase5 `:472–479`, phase6 `:425`, phase7 `:392–395`; **`app.storage`'s value exact-pinned a second and third time** in phase6 `expected_legacy` `:421` and phase7 `expected_legacy` `:388` (phase5's own value pin at `:487–491`); PURE exact-set pins phase6 `:432`, phase7 `:406`; cross-file self-checks phase6 `:456` (`"== 13" in` phase4/phase5 sources) and `:458` (excluded stale counts `(10, 11, 12)`), phase7 `:431–435` (`"== 13" in` the three sources; `== 10/11/12` not-ins). **Byte-pin inventory — FOUR byte-diff pins cross `app/`:** temporal (`:416` vs checkpoint), phase6 criterion-16 `git diff PHASE5_CHECKPOINT -- app/models app/forecasts app/storage` (`:259–269`), phase7 criterion-16 `PROTECTED_PACKAGES` incl. `app/storage` (`:38–42`, `:328–334`) + `forecasts_db.SCHEMA_VERSION == 1` (`:335`), and `test_operational.py` `PHASE9_COMMIT = "80b8f79"` (`:58`) with `_git_diff("app/") == ""` and `_git_diff(*GOLDEN_PIN_FILES) == ""` (`:401–409`; `GOLDEN_PIN_FILES` = nine files at `:61–71`, **three of which this phase amends**). `tests/test_storage.py` has **no** "exactly one table" pin; its schema pins (`PINNED_COLUMNS :83`, `:396–408`, forecasts triggers `:120–148`) are forecasts-scoped and stay green; the evaluations-table pins are ADDED by amendment A9.
- **Vocabulary machinery pinned:** `SCORING_ALLOWLIST` = exactly one `(file, sentence)` entry (`test_vocab_guards.py :31–33`, exact pins `:195–198`); scoring hits computed by `scoring_violations()` (`:87–94`); the raw-pattern `files_with_hits` loops run at **two** sites (`:210–213` and `:416–419`) and assert `== {SIMULATION_INIT}`; app-wide exact-set guards that already cover any new package automatically: comparative tokens zero app-wide (`:415`), accuracy-trio identifiers zero (`:224–234`), `_ACCURACY_PATTERN` word uses exactly 5 sites (`:254–266`), bare "accuracy" word exactly 10 recorded sites (`:381–392`), `FIELD_BAN` over every dataclass field (`:275–304`); `OUTCOME_COMPARATIVE_TOKENS` 13-tuple defined once here (`:55–59`); `SCORING_TOKENS` six-tuple defined in `test_phase7_separation.py:46`. `test_backtesting`'s no-join scans (`_JOIN_PATTERN` `:165`, co-occurrence `:169`) are scoped to `app/backtesting/**` only (`:431`) — `app/evaluation/` is legally the joining package.
- **Harness/record facts relied upon:** `run_walk_forward(matches, *, fixture_file_sha256s=(), interpreter_version=None)`; canonical run digest derives without caller echoes (Phase 9 test `:608–613`); `@pytest.fixture(scope="module") canonical_run` pattern (`test_backtesting.py:198`); `Forecast` has **no flag field** — flags live in `forecast.fitted` with the exact three-clause predicate at `app/backtesting/harness.py:83–86` (`_is_flagged`, **private**, and `app/backtesting/**` becomes byte-pinned this phase → the predicate is duplicated, decision 4); `BaselineRecord` MISSING on the first date's three targets (§12(a)); `get_forecast(connection, competition, season, date, home, away)` uses `fetchone` (`forecasts_db.py:288` — the flagged latent ambiguity), `verify_all` (`:294–308`), `__all__` has exactly **11** names (`:327–339` — C5 correction 2026-10-23: the first-draft probe text miscounted as 10; the 13-line block holds 11 names), `SCHEMA_VERSION = 1` (`:34`).
- **Guard semantics verified:** the `matches` census is **position-free** (`test_temporal_integrity.py:121–132` scans posonly/args/kwonly) and counts **public** functions only (underscore-private exempt) → exactly **one** new public `matches`-parameter function may ship (census 4 → 5, ADV-7); `validate_registry` resolves entries by `importlib.import_module` + `getattr` (`:102–118`) → the new entry's test must exist in an importable `tests/test_evaluation.py`. The health-script recursion guard is name-based `-k 'not health_script'` (`health-check.sh:13`); the 6 deselected = 3 `test_health_script` + the 3 `test_operational` tests whose names contain `health_script` (`:283/:309/:335`) — **all new tests run inside every execution**. No `conftest.py` exists; fixtures are re-derived per test module (module scope, Phase 9 pattern).
- **ADV-4's probes independently re-verified read-only against the frozen fixtures** (`fixtures/openfootball/valid/season-{1,2}.json`, first date **2024-08-10**): excluding the 3 refusal targets leaves **57 matches, 114 team-goal observations, sum 149, mean 1.30702 (probe 1.307 ✓), population variance (ddof=0) 0.96711 (probe 0.967 ✓)** — sample variance (ddof=1) is 0.9757 and does **not** reproduce the probe, which pins the denominator; all 60 matches: 156 goals / 120, mean 1.300; realized draws among the 57: **14** (14/57 = 0.2456).

## glass-quant consultation — RUN 2026-10-22 (conductor top level); rulings ADV-1–ADV-14 BINDING (record, not a gate)

1. **ADV-1 (BLOCKER) — the scored population is pinned PRE-SCORE, in this brief.** PRIMARY = the **30 clean** predictions; SECONDARY = **all 57** (flags riding); the **3 REFUSALS are excluded from every metric** and appear only in accounting (**60 = 3 + 27 + 30**); `n` is stated on **every** number; the **3 MISSING baselines are exactly the 3 refusal targets** (symmetry).
2. **ADV-2 (BLOCKER) — metric definitions, exact.** Log loss = `−ln(p_realized)`, **natural log, NO ε-clamp** (the smallest probability component on this population is ≈0.128, so no clamp is ever needed here; zero-on-realized-outcome is a **named hard refusal, never smoothed** — constitution prohibition 4). Brier = **FULL 3-outcome sum, NO halving**, range `[0,2]`, uniform reference `⅔`. RPS = **½-scaled, 3-category ordinal** over H < D < A: `½·[(F_p(H)−F_o(H))² + (F_p(D)−F_o(D))²]`, range `[0,1]`; the fine-grained scoreline variant is **REJECTED** with reasoning recorded in §13.
3. **ADV-3 (BLOCKER) — calibration, exact.** **5 equal-width bins** `[0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1.0]` (last inclusive), **pooled (p, realized-indicator) pairs across the three outcomes**, per-bin `(n, mean p, realized frequency)`; **EMPTY BINS (n=0) are NEVER merged**; plus the **§2f draw aggregate, one number per population**; **no chi-square, no smoothing, no reliability-quality claim**.
4. **ADV-4 (SHOULD-FIX)** — ship the **§2b overdispersion diagnostic** (probe: n=114, mean 1.307, variance 0.967 — descriptive only, no test claim) and the **§2f draw calibration**; the population pin is a **brief position** (decision 3).
5. **ADV-5 (BLOCKER) — join and read-path discipline.** Join = prediction natural key → `Match.natural_key`, **one line**, **REFUSE on 0 matches and on >1 match**; `get_forecast`'s `fetchone` is **NEVER load-bearing** for evaluation; **NO new fetch-by-content_hash API**; **do NOT modify app/storage read paths**; ship the recommended proof that `score(read-back via verify_all into tmp_path) == score(in-process)`.
6. **ADV-6 (BLOCKER) — digest gate FIRST, and the record table decision is the brief's to make explicitly.** **RE-DERIVE the run and assert `run_digest == 150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f` BEFORE any metric computes**; ship the evaluation-record table per §11(d) (`EVALUATION_VERSION`, content-hashed, no clock, write-once/idempotent, sqlite confined to `app/storage`, exception map `{"app.storage": {"sqlite3"}, "app.api": {"http"}}` **UNCHANGED**, caller-passed DB, `tmp_path` in tests, no committed DB, `SCHEMA_VERSION` 1 → 2) **— decide and record ship vs in-process-only deviation** (decision 1: SHIP).
7. **ADV-7 (BLOCKER) — pre-declare the amendments EXACTLY** (7 files minimum, 9 with the table): (1) `test_temporal_integrity` registry 6 → 7, census 4 → 5, byte-pin re-point `ea92667` → `8abe1ca` + `PRE_EXISTING_APP` rescoped (add `app/backtesting`, exclude `app/evaluation`), criterion-8 knob scan extended; (2) `test_fixtures_and_hygiene` self-inclusive `ALLOWED_APP_IMPORTS["app.evaluation"]` (VERIFY against actual imports) + `PURE_PACKAGES` 5 → 6; (3) the **four separation files** key-set 13 → 14 + unions + `PURE_PACKAGES` pins + self-checks; (4) `test_vocab_guards` `SCORING_TOKENS` site-pin **scoped-exclusion to `app/evaluation/**` ONLY** (extend-not-weaken; OUTCOME_COMPARATIVE + accuracy trio + `FIELD_BAN` stay enforced inside `app/evaluation`); (5) with the table: `test_storage` schema pins + `test_backtesting` criterion-11 `SCHEMA_VERSION == 1` pin. **This brief declares TEN files (A1–A10)**: the audit below found three forced hunks and one forced file beyond that enumeration — every byte-pin that crosses `app/storage` must also drop it (phase6 `:262`, phase7 `PROTECTED`), `test_operational`'s `app/`-and-golden byte-pins break the moment the sanctioned schema bump or any amendment lands (decision 12, evidence cited).
8. **ADV-8 (BLOCKER) — side-by-side legality.** Baseline metrics with the **same formulas**, **ABSOLUTE values side-by-side**, same population, with `n` + caveats = **LEGAL** (IX-11's "and baselines" is the basis). Deltas, ratios, percentages, better/worse, or **any verdict ILLEGAL — still banned after Phase 11** (§11(a)/§12(c) ban "beating"). The rationale (model–baseline gap sits at the §2d noise floor ±0.05 vs score SE 0.15–0.25) stays **brief/§13-only, never a docs claim**.
9. **ADV-9 — vocabulary.** Metric identifiers (`log_loss`, `brier`, `rps`, `calibration`) are legal **inside `app/evaluation/` only**; NEW doc-level ban: **quality adjectives may never describe model output as a claim** — `accurate`, `well-calibrated`, `good fit`, `reliable`, `trustworthy`. Docs are not machine-scanned → the honest-negation sentences are pinned as exact legal prose in the DOCS step below.
10. **ADV-10 — golden-pin discipline.** Golden metrics in tests **FIRST** (mean log loss/Brier/RPS for model **and** baseline per registered population, plus **≥3 hand-computed single-prediction values with independent in-test arithmetic** — IX-11's "hand-computed values"); deterministic ⇒ exact-pinning is free; **re-derive on change, never widen**; `docs/EVALUATION.md` **CREATED this phase** citing ONLY pinned test-literal numbers; **§13 AUTHORED PRE-BUILD** (formulas, bins, populations, side-by-side legality, vocabulary); anti-inflation rule: **no `EVALUATION.md` number without a pinned test source**.
11. **ADV-11 — no CIs** (§6); calibration is computed but presented **descriptive-with-loud-caveat** ("over many observations" vs n ≤ 30; ~80% of pairs sit in one bin); **larger-n calibration registered as Phase 13** (decision 13).
12. **ADV-12 — leakage/integrity: read-only over frozen `Forecast`s + `Match.score`; poison trio** — (a) altering a **scored** match's outcome changes that contribution **and** the aggregates (positive control); (b) altering a **REFUSAL TARGET**'s score changes **NOTHING**; (c) evaluation over a stored DB leaves the DB **byte-identical** / `verify_all` unchanged; outcome identity via the manifest's `fixture_file_sha256s` + `run_digest` on the evaluation record; **no clock**.
13. **ADV-13 — runtime.** One extra harness run ≈3 s; **module-scoped fixture** (Phase 9 pattern); **no subsetting (E2)**; the **800 s valve is untouched**.
14. **ADV-14 — out of scope:** `improvement/`, model/variant/config changes, re-tuning (READ-ONLY over frozen artifacts), API routes, plotting, thresholds/decisions, fixture edits. **IX-12 must CONSUME Phase 11 outputs, not recompute them** → keep every evaluation entry point re-runnable and read-only. **ZERO developer questions.**

## Design decisions (this brief resolves them)

1. **SHIP the evaluation-record table (ADV-6; executes §11(d) and IX-11's "idempotent evaluation records").** In-process-only records would be a **named deviation** from the pre-registered §11(d) bump and would leave idempotence unpersisted; write-once, content-hash, and no-clock properties need the schema. Consequences, all pinned: `SCHEMA_VERSION = 1 → 2`; one new table `evaluations` with columns `(evaluation_version, run_digest, fixture_file_sha256s, payload, content_hash)` (**no timestamp column**), `BEFORE UPDATE`/`BEFORE DELETE` triggers mirroring the forecasts table (`RAISE(ABORT …)` — surfaces as `sqlite3.IntegrityError`, criterion-8 erratum precedent); one new **write-only** production function `insert_evaluation_record(connection, record) -> bool` in `app/storage/forecasts_db.py` (check-then-INSERT inside `BEGIN IMMEDIATE`: identical content hash → `False` with **zero INSERTs**, same identity + different hash → `EvaluationConflictError`, never an overwrite — the `insert_forecast` pattern); `forecasts_db.__all__` gains **exactly** `insert_evaluation_record`; **no read API** for evaluations (tests read rows with raw `sqlite3` as `test_backtesting.py:579` already does); sqlite stays confined to `app/storage` (exception map unchanged); caller-passed DB, `tmp_path` in tests, **no committed DB**. Storage gains `from app.evaluation import EvaluationConflictError, EvaluationRecord` (one-way: evaluation **never** imports storage — mirrors storage→forecasts today). **Forced byte-pin consequence:** every byte-pin crossing `app/storage` must drop that path by the same named amendment (A1/A5/A6/A10) — recorded as FORCED, with evidence, not slipped in.
2. **Module split: a lean new `app/evaluation/` package — exactly four files.** `__init__.py` (re-exports the public surface), `metrics.py` (`log_loss`, `brier`, `rps`: one-prediction pure functions + aggregate means), `calibration.py` (the 5-bin tables, the draw aggregate, and the §2b overdispersion diagnostic — one module, documented as the descriptive-frequency block), `evaluate.py` (the join, the digest gate, population accounting, contributions, `EvaluationResult`/`EvaluationRecord`/`EvaluationConflictError`, `EVALUATION_VERSION = 1`, and the single public entry `evaluate_predictions(predictions, baselines, matches, *, run_digest, expected_run_digest)`). App-side imports pinned to **exactly** `app.domain`, `app.forecasts`, `app.backtesting`; stdlib pinned to exactly `{dataclasses, hashlib, json, math, typing}` — **no** `os/sys/pathlib/io/random/time/datetime`, **no** `app.models`/`app.simulation` (structural proof that no scoreline-variant RPS exists), **no** `app.storage`/`app.api`. Pure statistical code importing no storage or HTTP (constitution) holds by construction. Exactly **one** public `matches`-parameter function ships (census 4 → 5); every helper that needs `matches` is underscore-private (the census is position-free and public-only — verified).
3. **Population pin — brief position + §13 pre-registration + test pins (ADV-1/ADV-4).** PRIMARY = 30 clean, SECONDARY = all 57 (flags riding), 3 refusals accounting-only, `60 = 3 + 27 + 30`, `n` carried on every metric container. App-level enforcement is the digest gate (fixtures + predictions are frozen behind `run_digest`); the **count** enforcement lives in criteria 3/4/9, which fail on any fixture or classification drift. Nothing is chosen post-score: §13(b) fixes the populations and §13(c) fixes the bins **before** any metric exists.
4. **The flag predicate is duplicated, deliberately.** `app/backtesting/harness.py:_is_flagged` is private, and `app/backtesting/**` joins the byte-pin this phase (A1), so neither importing it nor promoting it is available without violating a frozen surface. `app/evaluation/evaluate.py` carries the identical three-clause predicate (`insufficient_data` / `insufficient_teams` / `convergence_status.value != "CONVERGED"`, stringly compared so `app.models` is not imported); drift is guarded by the 27/30 count pins. Recorded in §13 and KNOWN-LIMITATIONS as a duplicated-not-shared predicate with its guard.
5. **Build order is a gate: §13 first, tests second, docs last (ADV-10).** Step 0 of the build appends **§13 to `docs/STATISTICAL-ASSUMPTIONS.md` as a single hunk BEFORE any app or test code exists** (the §3/§7–§12 pre-build pattern), fixing formulas, bins, populations, side-by-side legality, and vocabulary in prose. Golden literals are derived from the **first green run** and pinned in tests (`tests/test_evaluation.py`), then `docs/EVALUATION.md` is created citing **only** those literals; at the DOCS step §13 flips to implemented-and-tested reality (status line + verification append, never a rewrite of the pre-build text). Re-deriving later **re-pins, never widens**.
6. **Calibration and diagnostics, decided exactly (ADV-3/ADV-4/ADV-11).** (a) Bins: `[0,.2) [.2,.4) [.4,.6) [.6,.8) [.8,1.0]`, last inclusive; pairs pooled across the three outcomes (3 pairs per scored match: `(p, 1_realized)` for H, D, A); empty bins report `n=0` with `mean_p = None` and `realized_frequency = None` (**never `0.0` — a fabricated number — and never merged**); tables computed for **both** populations; ~80% single-bin concentration is pinned as a literal and quoted with its caveat. (b) **Draw aggregate = `realized_draw_rate − mean_predicted_draw_probability` per population** (positive = underprediction, the §2f deficit direction; components are calibration-against-realized, not model-vs-baseline, so ADV-8's ban does not touch it); the realized secondary rate `14/57` is hand-counted in-test. (c) **Overdispersion scope: the SECONDARY population's realized team-goals — n=114, mean=149/114, population variance (ddof=0)** — chosen because that denominator **reproduces ADV-4's probe exactly** (1.307 / 0.967; ddof=1 gives 0.9757 ≠ probe — verified, State section); descriptive only: no test, no claim, var < mean reported as a number, not a verdict.
7. **Side-by-side legality enforced mechanically (ADV-8).** `EvaluationResult` carries `model` and `baseline` **absolute** `MetricTriples` on the same population with `n` and caveats; a local banned-identifier set (`delta, diff, difference, ratio, pct, percent, improvement, uplift, better, worse, advantage, edge, gap, gain, superior, ci, confidence, lower, upper`) is scanned over `app/evaluation/**` sources and every evaluation dataclass field (criterion 13), on top of the app-wide comparative-token guard. The noise-floor rationale lives in this brief and §13(d) only — **never** in `EVALUATION.md`.
8. **Vocabulary: ONE scoped prefix exemption, everything else untouched (ADV-7/ADV-9).** `test_vocab_guards.py` gains `SCORING_EXEMPT_PREFIXES = ("app/evaluation/",)` (exactly one prefix) consulted **only** by `scoring_violations()` and the two `files_with_hits` loops; `SCORING_ALLOWLIST` stays **exactly one sentence** (the honest simulation docstring); the comparative-token, accuracy-trio, `FIELD_BAN`, and bare-"accuracy" exact-set guards run over `app/evaluation/**` **unweakened** (criterion 22 probes both directions). Consequently `app/evaluation/**` must contain **zero** occurrences of the words `validated`/`accurate`/`beating`/`accuracy` and zero comparative tokens — legal metric identifiers only. Doc-level: the four pinned honest-negation sentences below are the only sanctioned phrasings around quality vocabulary, and `accurate/well-calibrated/good fit/reliable/trustworthy` never describe model output anywhere (reviewer checklist).
9. **`get_forecast` brief position — three points, per §11(d)'s explicit flag and ADV-5.** (i) Evaluation never calls it: the round-trip proof uses `verify_all`, and a source scan pins `get_forecast` absent from `app/evaluation/**` (criterion 14). (ii) The latent `fetchone` ambiguity is **retained, not "fixed"** — `get_forecast`'s signature and its `fetchone` line are pinned unchanged (criterion 14); no read path in `app/storage` is modified this phase (reviewer diff row: `git diff 8abe1ca -- app/storage` may contain **only** the sanctioned schema/insert additions). (iii) No fetch-by-content-hash API is added (`__all__` gains exactly one write-side name). A future serving brief owns the ambiguity itself.
10. **Record contract (ADV-6/ADV-12).** `EvaluationRecord` (frozen): `evaluation_version: int` (`EVALUATION_VERSION = 1`), `run_digest: str`, `fixture_file_sha256s: tuple[tuple[str, str], ...]` (caller echo, real fixture hashes supplied by the caller/test), `payload: str` (canonical JSON of the full `EvaluationResult` — `json.dumps(..., sort_keys=True, separators=(",", ":"))`, floats json-round-trip exact per Phase 5's pinned property), `content_hash: str` (= `sha256(payload)` hex). **No clock anywhere**: no time field, no time import, no ISO-datetime form in the payload. The record never alters forecasts — persistence is one INSERT on a separate table (criterion 18).
11. **Result surface carries per-match `contributions`** — ordered canonically: `(natural_key, outcome, log_loss, brier, rps)` per scored target — so ADV-12(a)'s "that contribution changes" is observable, and the population metric equals the arithmetic mean of the matching contribution subset (cross-checked in tests). Aggregates and contributions together make the record payload deterministic and fully re-derivable (IX-12 consumes, never recomputes).
12. **Amendment inventory: TEN files, A1–A10 — ADV-7's enumeration plus three forced additions, all evidence-backed (ADV-7 honored in kind).** A1 temporal (registry/census/byte-pin re-point+rescope/criterion-8), A2 hygiene (key 14 + two values + pure 6), A3–A6 the four separation files (key 14, unions, `app.storage` value pins in phase5/6/7, pure sets, self-check flips, **phase6 byte-pin drops `app/storage`, phase7 byte-pin drops `app/storage` + `SCHEMA_VERSION → 2`**), A7 vocab (prefix exemption + probes), A8 backtesting (its A1/A2/A3 exactness block — breaks **unconditionally**, not only with the table — plus criterion-11 table/`SCHEMA_VERSION` pins), A9 storage (the ADDED evaluations-table schema test), A10 operational (byte-pin re-point + pathspec excludes + three golden files removed from `GOLDEN_PIN_FILES`). The **five-entry knob scan in `test_backtesting` is NOT extended** — undeclared edits are forbidden; temporal's scan is the declared extension site. Line figures below are **projections**; actuals are declared at checkpoint/review/monitor with `wc -l` (Phase 9 figure discipline).
13. **Docs placement (ADV-9/ADV-10/ADV-11).** `docs/STATISTICAL-ASSUMPTIONS.md` §13 (pre-build, flipped at DOCS); **`docs/EVALUATION.md` created** with six fixed sections (purpose/anti-inflation rule; populations; formulas; results side-by-side with n and caveats; "what these numbers are not" carrying the pinned negations; provenance: digest, fixture hashes, version, criterion map); `KNOWN-LIMITATIONS` new Phase 11 section + "evaluation" leaves the "Not yet applicable" header (prior `n = 0` statements are historical and **never rewritten** — append-only); `ARCHITECTURE` gains `app/evaluation/` and the `evaluations` table with `SCHEMA_VERSION = 2`; `README` state + test count (docs agent); `PROGRESS-LOG` standard entry incl. the consult record, the §13-pre-build proof, amendment actuals, the **first-evaluated-n > 0** milestone; `HEALTH-LOG` load-labeled runs; `ROADMAP` Phase 11 `committed` (PENDING-hash; block table and rows 1–10 byte-identical). Larger-n calibration is **registered as Phase 13** in KNOWN-LIMITATIONS + EVALUATION.md's caveats.
14. **Runtime and health (ADV-13).** One module-scoped fixture re-derives the run once (≈3 s; Phase 9's `scope="module"` pattern); no test-side subsetting or timeout around any harness execution (E2); the full suite gains 23 tests (21 in the new file + 1 in `test_storage` + 1 A8 boundary probe in `test_vocab_guards`; C9 reconciliation 2026-10-23 — A8 item 4 declared that extra test but this line's first-draft arithmetic omitted it); the **800 s valve, `scripts/health-check.sh`, and `pytest.ini` are untouched**; expected suite total **155 + 23 = 178** (a prediction, never a claimed fact).

## Files and directories to create or modify

BUILD step (in the order below — step 0 is a gate, decision 5):

0. `docs/STATISTICAL-ASSUMPTIONS.md` — **§13 AUTHORED PRE-BUILD, single appended hunk, before any app/ or test/ code exists** (projected 1373 → ~1493; actuals recorded at DOCS): status header (authored-before-build, ADV citations), (a) metric formulas verbatim incl. no-ε/no-halving/½-scaling and the scoreline-variant rejection, (b) populations (60 = 3+27+30; primary 30; secondary 57; refusals accounting-only; MISSING ≡ refusals; n-on-every-number), (c) the 5-bin edges + pooling + empty-bin honesty + the draw-aggregate definition + the overdispersion definition (n=114, ddof=0), (d) side-by-side legality (absolute legal, deltas/verdicts banned forever; noise-floor rationale lives HERE, never in EVALUATION.md), (e) vocabulary (metric identifiers legal in `app/evaluation/` only; quality adjectives banned as claims; the pinned negations), (f) the record contract + the duplicated-predicate note. Flipped to implemented-and-tested at the DOCS step; §§1–12 untouched.
1. `app/evaluation/__init__.py` (projected ~45 lines) — public re-exports: `evaluate_predictions`, `EvaluationResult`, `EvaluationAccounting`, `PopulationScores`, `MetricTriple`, `ScoredContribution`, `CalibrationTable`, `CalibrationBin`, `OverdispersionDiagnostic`, `EvaluationRecord`, `EvaluationConflictError`, `EVALUATION_VERSION`.
2. `app/evaluation/metrics.py` (projected ~95) — `log_loss(outcome_probs, outcome)`, `brier(outcome_probs, outcome)`, `rps(outcome_probs, outcome)` (the 3-tuple call form; C7 correction 2026-10-23 — criteria 5/7/8/9 and the shipped signatures govern over this first-draft four-arg prose); uniform-reference docstrings; hard `ValueError("zero probability …")` when the realized component is 0.0; aggregate mean helpers; **no epsilon, clamp, or clip of any spelling**.
3. `app/evaluation/calibration.py` (projected ~135) — the pinned `BIN_EDGES`, `calibration_table(pairs)`, `draw_deficit(...)`, `overdispersion(goals)` (population variance, ddof=0); empty bins → `n=0`, fields `None`.
4. `app/evaluation/evaluate.py` (projected ~210) — the one public entry, the digest gate (`ValueError` mentioning `run_digest` **before** any metric import is invoked), the one-line dict join with explicit 0 / >1 refusals, the duplicated flag predicate, accounting, contributions, populations, `build_evaluation_record(...)` (canonical payload, `content_hash`), `EVALUATION_VERSION = 1`.
5. `app/storage/forecasts_db.py` (339 → +~55) — `SCHEMA_VERSION = 2`; `_EVALUATIONS_TABLE_DDL` (5 pinned columns, no timestamp) + the two immutability triggers; `_DDL` extended; `insert_evaluation_record(connection, record) -> bool` (`BEGIN IMMEDIATE`); `__all__` += exactly `insert_evaluation_record`. **`get_forecast`, `verify_all`, `open_read_connection`, `backup_forecasts`, and every read path are NOT touched** (ADV-5). `app/storage/__init__.py` re-exports the new writer.
6. `tests/test_evaluation.py` — **NEW**, criteria 1–16 and 18–22, projected ≤ ~620 lines, stdlib only (`math`, `hashlib`, `json`, `dataclasses`, `sqlite3`, `pathlib`, `re`, `ast`, `inspect`, `subprocess` for nothing — no git calls needed here), module-scoped re-derivation fixture (Phase 9 pattern), no skip/xfail.
7. **Amendments A1–A10** — exact texts after `---` (files: `test_temporal_integrity.py`, `test_fixtures_and_hygiene.py`, `test_phase4_separation.py`, `test_phase5_separation.py`, `test_phase6_separation.py`, `test_phase7_separation.py`, `test_vocab_guards.py`, `test_backtesting.py`, `test_storage.py`, `test_operational.py`). Any OTHER pin that breaks before/while building → **STOP and report** (Phase 9 A3' class); no undeclared edits, ever.
- Do not create or modify: `scripts/health-check.sh`, `pytest.ini`, any `conftest.py`, fixtures, `app/backtesting/**` (byte-pinned this phase), `app/models/**`, `app/forecasts/**`, `app/decisions/**`, `app/api/**`, `app/improvement/`, `app/state/`, requirements/pyproject, CI, linters, Docker, `data/`, any committed DB, any test file outside the A1–A10 set, and any test deletion/skip/xfail/assertion weakening.

DOCS step (after the suite is green with golden literals pinned):

- `docs/EVALUATION.md` — **CREATED this phase**, six sections per decision 13; every number cites its pinned test criterion inline (anti-inflation rule); the four pinned honest-negation sentences verbatim: **(S1)** "These numbers are descriptive evaluations of a small synthetic sample; they are not evidence of predictive skill." **(S2)** "Model and baseline values appear side by side as absolute quantities; no difference, ratio, ranking, or verdict between them is computed or claimed." **(S3)** "Calibration bins are counts and frequencies only; no reliability or goodness-of-fit claim follows from them." **(S4)** "No forecast is called validated, accurate, or beating anything." (`accurate/well-calibrated/good fit/reliable/trustworthy` never appear as claims; no CI/interval language; the noise-floor rationale never appears here.)
- `docs/STATISTICAL-ASSUMPTIONS.md` — §13 status flip + phase-end verification append only.
- `docs/KNOWN-LIMITATIONS.md` — new Phase 11 section (first evaluated n = 57/30; duplicated flag predicate; tiny-n + single-bin calibration caveat; draw deficit; overdispersion descriptive; no CIs; side-by-side legality; amendments A1–A10 with actual figures; larger-n calibration = Phase 13); "Not yet applicable" refresh (**evaluation leaves it**; stages 3/10 remain).
- `docs/ARCHITECTURE.md` — `app/evaluation/` module row + storage row update (`evaluations` table, `SCHEMA_VERSION = 2`, write-only record surface); stage map: evaluation IMPLEMENTED.
- `README.md` — current state: Phase 11, real test count, `SCHEMA_VERSION` mention updated to 2 (docs agent).
- `docs/PROGRESS-LOG.md` — standard entry: consult record (2026-10-22, ADV-1–ADV-14), §13 pre-build proof (authored before build code), amendment actual figures, the first-evaluated-n milestone, golden-pin derivations, suite figures. The three dirty protocol docs **ride the Phase 11 checkpoint commit**.
- `docs/HEALTH-LOG.md` — load-labeled runtime records for this phase's executions (watch item carried).
- `docs/ROADMAP.md` — Phase 11 `planned → committed` (PENDING-hash convention); **block table byte-identical; rows 1–10 and all acceptance rows untouched**.
- `docs/PLAN.md` — **no change** (no new dependency; §2 storage/§5 layer already pre-registered this bump).

## Dependencies

- **None new.** stdlib only: `math`, `hashlib`, `json`, `dataclasses`, `typing` (evaluation); `sqlite3` stays confined to `app/storage`; pytest already installed (justification unchanged).
- **Explicitly refused:** any third-party package; numpy/pandas/scipy/scikit-learn or any numeric/ML stack; plotting libraries; FastAPI routes or any API change; any second schema surface beyond the one declared table; any environment knob; CI/Docker/services.

## Acceptance criteria

Criteria 1–16 and 18–22 map 1:1 to test functions in the **new `tests/test_evaluation.py`**; criterion 17 lives in `tests/test_storage.py` (amendment A9); criterion 19 is the suite-level gate verified by recorded executions (tester, reviewer ×2, monitor). No test may use skip or xfail; everything runs offline from the checked-in fixtures. Expected total **155 + 23 = 178** (a prediction, never a claimed fact).

1. **`test_rederived_run_matches_golden_digest_and_first_evaluation_n_positive`** (ADV-6 gate) — a module-scoped fixture re-derives `run_walk_forward(ALL_MATCHES)` with default echoes; assert `run.manifest.run_digest == "150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f"` **before** any evaluation call; then `evaluate_predictions(run.predictions, run.baselines, ALL_MATCHES, run_digest=…, expected_run_digest=…)` succeeds and returns a result whose `secondary.n_matches == 57 > 0` and `primary.n_matches == 30` — the **first evaluated n > 0 in the project's history**, asserted here.
2. **`test_tampered_run_digest_refuses_before_any_metric_computes`** (ADV-6) — with `expected_run_digest` = golden and `run_digest` = a one-character-flipped digest, `pytest.raises(ValueError, match="run_digest")`; a counter monkeypatched onto `app.evaluation.evaluate.log_loss` (evaluate.py imports the metric functions **by name**, decision 2/seam) records **zero calls**; no result object and no record are produced.
3. **`test_population_accounting_pinned_prescore_60_3_27_30`** (ADV-1 BLOCKER) — accounting: `n_targets == 60`, `n_predictions == 57`, `n_refusals == 3`, `n_flagged == 27`, `n_clean == 30`; `refusal_keys` equals exactly the three natural keys of the first date (hand-derived in-test from `min(m.date)`); `primary.n_matches == 30`, `secondary.n_matches == 57`; every `MetricTriple` and calibration table in both populations carries its `n` (no bare number anywhere); no metric container exists for n=60.
4. **`test_missing_baseline_symmetry_with_refusal_targets`** (ADV-1) — the three `MISSING_NO_HISTORY` baseline keys == `refusal_keys` == prediction-less matches (three-way set equality); `baseline.n == model.n` inside both populations; no baseline value is `None` on any scored target; a fake uniform baseline is absent (status-driven, not filled).
5. **`test_hand_computed_single_prediction_values`** (ADV-10/IX-11 "hand-computed values") — ≥3 single-prediction goldens with **independent in-test arithmetic** (no production helper used to derive the expected value), each compared within 1e-12 absolute: (i) `log_loss((0.55, 0.25, 0.20), H)` == `−math.log(0.55)`; (ii) `brier((0.2, 0.3, 0.5), A)` == `0.04 + 0.09 + 0.25` (= 0.38); (iii) `rps((0.4, 0.35, 0.25), D)` == `½·(0.4² + 0.75² result)` = **0.11125** hand-expanded from the cumulative forms `F_p = (0.4, 0.75, 1.0)`, `F_o = (0, 1, 1)`.
6. **`test_zero_probability_on_realized_outcome_hard_refusal_no_clamp`** (ADV-2/constitution prohibition 4) — (a) a prediction whose realized component is exactly `0.0` raises `ValueError` whose message contains `zero probability` — never a finite clamped score; (b) source scan of `app/evaluation/**`: no `epsilon`, `clamp`, `clip`, `sys.float_info`, or `1e-` literal anywhere; (c) golden: the smallest probability component over **all** scored pairs of the real evaluation equals the first-run literal (probe ≈ 0.128) and is `> 0.1`, demonstrating the clamp question is moot on this population.
7. **`test_brier_full_three_outcome_sum_no_halving_uniform_reference`** (ADV-2) — the hand value 0.38 from criterion 5 equals the production value (no `/3`, no `/2`: also assert `brier` on a probe ≠ any halved form within 1e-15); uniform `(⅓, ⅓, ⅓)` against any outcome is `2/3` within 1e-15; every Brier value in both populations lies in `[0, 2]`.
8. **`test_rps_half_scaled_ordinal_form_not_scoreline_variant`** (ADV-2) — the hand value 0.11125 within 1e-12 **and** `!=` the unscaled cumulative sum 0.2225 (pins the ½); uniform reference vs H equals `5/18` within 1e-15; every population RPS lies in `[0, 1]`; AST pin: `app/evaluation/**` imports **nothing** from `app.models`/`app.simulation` (no scoreline-matrix variant exists), matching §13(a)'s recorded rejection.
9. **`test_golden_mean_metrics_model_and_baseline_both_populations`** (ADV-10) — **exact-equality golden pins** for the 12 first-run literals: {model, baseline} × {log_loss, brier, rps} × {primary (n=30), secondary (n=57)}, each stored as a literal with a "golden: first green run; re-derive, never widen" comment and asserted alongside its `n`; cross-check: each model metric equals the arithmetic mean of the matching `contributions` subset computed in-test, and baseline metrics use the same metric functions on baseline triples (same formula, same population — ADV-8's legal shape).
10. **`test_calibration_five_equal_width_bins_boundaries_and_empty_bin_honesty`** (ADV-3) — bins tuple length **always 5**; boundary probes pin edges exactly: `0.0→bin0`, `0.2→bin1`, `0.4→bin2`, `0.6→bin3`, `0.8→bin4`, `1.0→bin4` (last inclusive), `0.3999→bin1`, `0.7999→bin3`; pooled `n_pairs == 3 × n_matches` (90 primary / 171 secondary) and `sum(bin.n) == n_pairs`; each bin's `(n, mean_p, realized_frequency)` recomputed in-test with independent arithmetic and golden-pinned per population; **empty bins (if any) report `n=0`, `mean_p is None`, `realized_frequency is None`, and the tuple is never length 4**; the dominant bin's share golden-pinned (the ~80% figure EVALUATION.md may quote).
11. **`test_draw_aggregate_deficit_both_populations`** (ADV-4/§2f) — `draw_deficit == realized_draw_rate − mean_predicted_draw_probability` recomputed in-test for both populations (golden-pinned); the secondary realized rate is hand-counted as exactly **14** draws among the 57 (`== 14/57` within 1e-15); the primary count is independently counted in-test from the clean subset.
12. **`test_overdispersion_diagnostic_n114_population_variance`** (ADV-4/§2b) — `n == 114 == 2 × secondary.n_matches`; goals hand-extracted from the scored matches' `Match.score`; `mean == 149/114` with `round(mean, 3) == 1.307`; `variance == Σ(g − mean)² / 114` (ddof=0) with `round(variance, 3) == 0.967` (the ddof=1 value 0.9757 is asserted **≠** the shipped value, pinning the denominator choice); descriptive-only docstring (no test, no verdict).
13. **`test_baseline_side_by_side_absolute_no_delta_no_ci_surface`** (ADV-8/ADV-11) — both populations expose `model` and `baseline` absolute triples with `n`; **delta-illegal probe**: the pinned banned set `{delta, diff, difference, ratio, pct, percent, improvement, uplift, better, worse, advantage, edge, gap, gain, superior, ci, confidence, lower, upper}` has **zero** identifier hits in `app/evaluation/**` sources **and** zero hits across every evaluation dataclass field name; no field or method suggests comparison/verdict; no CI/interval field exists anywhere in the result surface.
14. **`test_join_refuses_zero_and_multiple_matches_get_forecast_never_load_bearing`** (ADV-5) — (a) one-line natural-key join: a prediction whose key matches **no** `Match` raises `ValueError` containing `no match` and the offending key; two `Match`es sharing a key raise `ValueError` containing `more than one match` and the key; (b) `"get_forecast"` appears **nowhere** in `app/evaluation/**` sources, and monkeypatching `app.storage.forecasts_db.get_forecast` to raise cannot affect any evaluation path (the round trip uses `verify_all`); (c) read-path pins: `inspect.signature(get_forecast)` is exactly `(connection, competition, season, date, home, away) -> Forecast | None`, its source still contains `fetchone` (ambiguity retained, never silently fixed), and `forecasts_db.__all__` equals the 11 pre-existing names ∪ exactly `{insert_evaluation_record}` (12 names total; C5 correction 2026-10-23 — the first-draft count of 10 was wrong: the pinned checkpoint's `__all__` holds 11) — **no fetch-by-content-hash API exists**.
15. **`test_db_roundtrip_metrics_equal_and_read_phase_byte_identical`** (ADV-5 recommended proof, ADV-12c) — insert all 57 predictions into a `tmp_path` DB (Phase 9 caller-side pattern), `verify_all` read-back, evaluate the read-back forecasts with the same baselines/matches/digests: the result equals the in-process result **field-for-field (dataclass equality, exact floats)**; the DB file's bytes are sha256-identical before vs after the read/evaluate phase; `verify_all` before/after returns identical tuples; all writes stayed under `tmp_path`.
16. **`test_evaluation_record_idempotent_content_hashed_no_clock`** (ADV-6/IX-11 idempotent records) — build the record with **real** fixture hashes (`sha256` of each fixture file's bytes, `(("season-1.json", …), ("season-2.json", …))`); first `insert_evaluation_record` → `True`, second identical → `False` with **zero INSERTs**; a payload mutated by `math.nextafter` on one metric under the same identity → `EvaluationConflictError(RuntimeError)` and the stored row is byte-unchanged; `content_hash == hashlib.sha256(payload).hexdigest()`; payload is canonical (re-serialization is the identical string; `json.loads` round-trips) and contains **no ISO-datetime form**; record fields are exactly `(evaluation_version, run_digest, fixture_file_sha256s, payload, content_hash)`; `EVALUATION_VERSION == 1` is echoed into the row; `run_digest` and the fixture hashes are present (outcome identity); two consecutive in-process evaluations are equal (idempotence at the compute level); no `time`/`datetime` import or field exists in `app/evaluation/**`.
17. **`test_evaluations_table_write_once_no_timestamp_schema_v2`** (in `tests/test_storage.py`, amendment A9) — `forecasts_db.SCHEMA_VERSION == 2`; `sqlite_master` tables == exactly `("forecasts", "evaluations")` (order pinned after the build-probe); `PRAGMA table_info(evaluations)` == exactly `(evaluation_version, run_digest, fixture_file_sha256s, payload, content_hash)`; **no timestamp-like column**; raw `UPDATE`/`DELETE` on `evaluations` raises with `immutable` in the message (mirror of the forecasts triggers, pinned as observed); the forecasts table still exposes exactly its 21 pinned columns; `BANNED_IMPORT_EXCEPTIONS` still exactly `{"app.storage": {"sqlite3"}, "app.api": {"http"}}`.
18. **`test_evaluation_writes_never_alter_forecasts_or_verify_all`** (HANDOFF:126–127, ADV-12c) — across evaluate + record insert on one `tmp_path` DB: the `forecasts` table dump (`SELECT *` ordered) is identical before/after, `verify_all` returns the identical 57 hash-clean forecasts, and exactly one `evaluations` row was added — evaluation records never alter original forecasts.
19. **`test_poisoned_scored_outcome_edit_changes_that_contribution_and_aggregates`** (ADV-12a positive control) — `dataclasses.replace` a **scored** match's score so its H/D/A outcome flips; re-evaluate: that match's contribution (all three metrics) differs, and the affected population aggregates differ; forecasts/DB remain untouched.
20. **`test_poisoned_refusal_target_score_edit_changes_nothing`** (ADV-12b) — alter the score of a **first-date (refusal-target)** match: the entire result — accounting, both populations, contributions, diagnostics — is **equal** to the unpoisoned result, and the record built from it has the identical `content_hash`.
21. **`test_poisoned_extra_matches_leave_evaluation_unchanged`** (registry poison; ADV-12) — append synthetic future-dated `Match`es with distinct natural keys to the input list: the result is byte-identical to the unpoisoned evaluation (extra rows simply never join). This exact test name is the `POISON_REGISTRY["evaluate_predictions"]` entry (criterion 22).
22. **`test_amendment_surface_exact_and_guards_extended_not_weakened`** (ADV-7/ADV-9) — pin the amended surfaces: `temporal.POISON_REGISTRY` has **exactly 7** keys with `"evaluate_predictions" == ("test_evaluation", "test_poisoned_extra_matches_leave_evaluation_unchanged")` and resolves; `temporal.MATCHES_ENTRY_POINTS == ("fit", "build_forecast", "compute_features", "run_walk_forward", "evaluate_predictions")`; `temporal.PHASE10_CHECKPOINT == "8abe1ca"`; `len(hygiene.ALLOWED_APP_IMPORTS) == 14` with `ALLOWED_APP_IMPORTS["app.evaluation"] == {"app.domain", "app.forecasts", "app.backtesting", "app.evaluation"}` (self-inclusive, import-verified) and `"app.evaluation" in ALLOWED_APP_IMPORTS["app.storage"]`; `hygiene.PURE_PACKAGES` == the exact six-set with `app.evaluation`; `vocab.SCORING_EXEMPT_PREFIXES == ("app/evaluation/",)` (exactly one prefix) while `vocab.SCORING_ALLOWLIST` remains **exactly one** entry; `phase7.SCORING_TOKENS` and `vocab.OUTCOME_COMPARATIVE_TOKENS` (13) and `ACCURACY_TRIO` unchanged; extend-not-weaken probes: a scoring token under `app/evaluation/x.py` passes while the same text under `app/models/x.py` still flags, and a comparative token / accuracy-trio identifier / `FIELD_BAN` field **inside** `app/evaluation/` still flags; `inspect.signature(evaluate_predictions)` is exactly `("predictions", "baselines", "matches", "run_digest", "expected_run_digest")` (three positionals — `matches` is POSITIONAL_OR_KEYWORD; the digest pair is keyword-only after `*`; C7 correction 2026-10-23 — criterion 1's call form governs); AST: import roots of `app/evaluation/**` ⊆ `{app.domain, app.forecasts, app.backtesting, dataclasses, hashlib, json, math, typing}`; zero occurrences of `validated/accurate/beating/accuracy` in `app/evaluation/**`.
23. **Suite gate (recorded execution)** — `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` reports 0 failed, 0 errors, 0 skipped, 0 xfailed, 0 xpassed (expected **178** — C9 reconciliation; the real number recorded by the tester); one offline `unshare -rn bash -c 'ip link set lo up && … pytest -q'` run recorded (lo-up protocol); `bash scripts/health-check.sh` completes `OK:` determinism, `none` skips/xfails, clean pip, nine headers, **inside the untouched 800 s valve**, with load-labeled timings. **Reviewer checklist before PASS:** (i) §13's git-history position: authored **before** the first app/test hunk; (ii) every `EVALUATION.md` number appears as a literal in `tests/test_evaluation.py` (anti-inflation), and the four negation sentences appear verbatim; (iii) no quality adjective claims output anywhere in docs; (iv) the noise-floor rationale appears only in this brief/§13; (v) `git diff 8abe1ca -- app/storage` contains only the sanctioned schema/insert additions (read paths untouched); (vi) amendment actuals match `wc -l` and the declared hunks exactly; (vii) no skip/xfail/subsetting; (viii) IX-12 consumption note: evaluation remains re-runnable and read-only.

## Out of scope (ADV-14 — blocker-grade; nothing here may be built, imported, plotted, or tested)

1. **`app/improvement/`** — does not exist; recommendation, thresholds, and tuning come later.
2. **Any re-tuning, re-fitting, or re-calibration of Phase 10's model** — Phase 11 only scores the forecasts already produced.
3. **New API endpoints or CLI surface** — evaluation is exercised through tests only.
4. **Plotting, dashboards, or any visualization dependency.**
5. **Decision thresholds** ("is 0.1023 good enough?") — none may be declared, and no verdict, label, grade, or recommendation may exist anywhere (ADV-9).
6. **Edits to fixtures, the harness, or saved predictions** — the recorded forecast bytes are frozen.
7. **Confidence intervals, bootstrap, chi-square, reliability diagrams, or statistical-significance machinery** (ADV-11).
8. **Scoreline RPS** — rejected in ADV-2/§13; not built, not tested, not mentioned as future work in a way that implies it will be scored.
9. **Any ε-clamp, clipping, renormalization, or other repair of the `p_realized == 0` case.**
10. **Any fix to `get_forecast`'s dict-vs-integer bug or any other read path** (ADV-5).
11. **A committed database, a live-data path, or any network access.**
12. **Changes to `scripts/health-check.sh` or the 800 s valve** (ADV-13).
13. **Skips and xfails of any kind.**
14. **Phase 12 planning or `improvement/` design work inside this phase's code.** Per ADV-14, IX-12 *consumes* this phase's records; it does not recompute them. Nothing Phase 12 needs may be smuggled in as a hook or stub.

## Risks

1. **Amendment-collision drift (highest).** Nine existing test files carry exact-set pins (line counts, unions, tuples, byte-pins) that Phase 11 deliberately moves. Every touch is a *declared* amendment recorded in PROGRESS-LOG; anything the builder finds that this brief did **not** anticipate is a STOP-and-report condition, not an invitation to widen a pin (see the "declared amendment" rule and criterion 22).
2. **Golden literals written before the code runs.** Every projected figure in the files table and every pin in the amendments is a projection. The order is fixed: build → hand-check against independently computed values → freeze the literals → pin. Literal-before-code and code-decides-its-own-pin are both forbidden (ADV-10; criterion 4).
3. **`sqlite_master` table-order assumption.** `tables == ("forecasts", "evaluations")` wherever the table tuple is pinned depends on creation order, not alphabetical order. This is verified at build time (the raw string is quoted for empirical confirmation) and, if it does not hold, the deviation is recorded — the assertion is never relaxed to `set(...)`.
4. **Read-back divergence (ADV-5).** The join returns a dict from `get_forecast` while `score()` consumes `Forecast` dataclasses. The single-line conversion and the round-trip criterion (15) are the only thing standing between this phase and a silent None-tuple fallback producing "valid" 1.0 contributions. The digest gate (criterion 17) runs before any of it.
5. **Misreading ADV-8 in review.** Side-by-side absolute values are legal; the moment a delta, ratio, "% better", or ranking appears, the phase fails. Reviewers must apply ADV-8 as written, not as "clearly that is harmless".
6. **Runtime valve.** Scoring 60 predictions is microseconds; the module-scoped fixture (~3 s) is the whole cost (ADV-13). Runtime risk is therefore negligible and no optimization is sanctioned.
7. **The three dirty protocol docs** (ROADMAP, PROGRESS-LOG, HEALTH-LOG) ride this checkpoint with the code, as the monitor's WARN records; the builder appends the Phase 11 entry before commit (criterion 21).

## Open questions for the developer

**None.** All substantive choices were settled by glass-quant's fourteen rulings (recorded above) and by the structural audit recorded in this brief's design decisions. Nothing in Phase 11 awaits a decision from you: the phase either ships to the frozen protocol or it stops and reports a deviation.

---

# Declared amendments (Phase 11)

Every hunk below is declared here in full; nothing else in the pinned files may move. Projected line figures are `wc -l` projections from the probe session and are replaced by actuals declared at checkpoint. Any collision surface the builder finds that this section did not anticipate is a STOP-and-report condition (criterion 22), never a silent widening.

## AMENDMENT A1 — `tests/test_temporal_integrity.py`

**Authority:** Phase 11 brief (census/registry/byte-pin re-point). **Touch surface:** `:39–43`, `:85–88` (C6 comment hygiene), `:88–99`, `:184–205`, `:412–421`, `:444–452`; projected file length 452 → ~485.

1. Checkpoint re-point (`:39`, version-local, never widened):

```python
# Criterion 7: the app/ byte-pin is version-local to this checkpoint;
# Phase 11 AMENDMENT A1 re-points it at Phase 10's commit (8abe1ca)
# and excludes app/storage (sanctioned schema work) and the new
# app/evaluation/ (does not exist at the pinned commit).
PHASE10_CHECKPOINT = "8abe1ca"
```

(replaces `PHASE8_CHECKPOINT = "ea92667"` and its stale two-line comment).

2. `PRE_EXISTING_APP` (`:40–43`) becomes the 12-path tuple — `app/storage` **dropped** (sanctioned change), `app/backtesting` **added** (frozen at `8abe1ca`), `app/evaluation` absent (new package):

```python
PRE_EXISTING_APP = (
    "app/__init__.py", "app/api", "app/backtesting", "app/decisions", "app/domain", "app/features",
    "app/forecasts", "app/ingestion", "app/models", "app/scenarios", "app/simulation", "app/validation",
)
```

3. `POISON_REGISTRY` (`:88–95`) gains its seventh entry (exact value pinned):

```python
    "evaluate_predictions": ("test_evaluation", "test_poisoned_extra_matches_leave_evaluation_unchanged"),
```

with the stale comment above the dict corrected from six to seven keys (`:184`), the set pin at `:186–189` gaining `"evaluate_predictions"`, and a new per-entry pin mirroring the existing six:

```python
    assert POISON_REGISTRY["evaluate_predictions"] == ("test_evaluation", "test_poisoned_extra_matches_leave_evaluation_unchanged")
```

4. `MATCHES_ENTRY_POINTS` (`:99`, equality at `:205`) extends 4 → 5 (AST census of public `matches` entry points under `app/`; `evaluate_predictions` takes `matches`):

```python
MATCHES_ENTRY_POINTS = ("fit", "build_forecast", "compute_features", "run_walk_forward", "evaluate_predictions")
```

5. Signature pin (new, adjacent to the census pins — the tuple lists all five parameter names in order; parameter kinds are pinned in criterion 22; C7):

```python
    assert tuple(inspect.signature(evaluate_predictions).parameters) == (
        "predictions", "baselines", "matches", "run_digest", "expected_run_digest",
    )
```

6. Byte-pin hunk (`:412–421`): comment and base updated to `PHASE10_CHECKPOINT`, diff arguments unchanged (`*PRE_EXISTING_APP`); the three assertions (`returncode`, empty stdout, empty stderr) stay verbatim.

7. The criterion-8 banned-name knob scan (`:444–452`) keeps its four-entry loop and its three-entry `config` sub-loop **unchanged**; `evaluate_predictions` is deliberately not added (decision 12 — its signature is pinned by item 5 instead).

8. **C6 comment hygiene (`:85–88`; line-neutral, 4 lines → 4 lines)** — the stale registry header comment becomes exactly:

```python
# A1 BLOCKER: the pinned seven history-consuming entry points, each to
# its REAL, resolvable poison/tamper test (Phases 3-8 contributed the
# first five; Phase 9 A1 added run_walk_forward; Phase 11 A1 adds
# evaluate_predictions -> the test-first poison gate in tests/test_evaluation.py).
```

(the history chain is verified: five keys at `ea92667`, six at `80b8f79`, seven now; the garbled "this file's 6" tail — already stale at Phase 8 — is dropped.)

## AMENDMENT A2 — `tests/test_phase4_separation.py`

**Authority:** new `app.evaluation` key in the import universe. **Touch surface:** `:788–795` (C6 comment hygiene), `:803–813`; projected file length 834 → ~836.

1. `:803` — `assert len(hygiene.ALLOWED_APP_IMPORTS) == 13` → `== 14`.
2. `:804–813` — the key-union literal becomes `set(expected_legacy) | {"app.features", "app.decisions", "app.backtesting", "app.evaluation"}`. The `expected_legacy` dict and every per-package value assert stay byte-identical (extend, never weaken).
3. Everything else in the file, including the full-tree scan and the stdlib/banned-import machinery, untouched.

4. **C6 comment hygiene (`:788–795`; line-neutral, 8 lines → 8 lines)** — `:788` `exactly thirteen keys` → `exactly fourteen keys`; `:791` `11 -> 12 for app.decisions; A3', Phase 9: 12 -> 13 for the` → `11 -> 12 for app.decisions; A3', Phase 9: 12 -> 13 (backtesting);`; `:792` `app.backtesting entry + PURE_PACKAGES),` → `A6, Phase 11: 13 -> 14 (app.evaluation + PURE_PACKAGES six-set)),`. File line count unchanged.

## AMENDMENT A3 — `tests/test_phase5_separation.py`

**Authority:** same universe extension + `app.storage`'s new import of `app.evaluation`. **Touch surface:** `:42` (C1 forced hunk), `:456–461` (C6 comment hygiene), `:471–491`; projected file length 574 → ~580.

1. `:471` — `len(hygiene.ALLOWED_APP_IMPORTS) == 13` → `== 14`.
2. `:472–479` — the key-union literal gains `"app.evaluation"` alongside `"app.features"`, `"app.decisions"`, `"app.backtesting"`.
3. `:487–491` — the exact `app.storage` value pin becomes:

```python
    assert hygiene.ALLOWED_APP_IMPORTS["app.storage"] == {
        "app.domain",
        "app.forecasts",
        "app.storage",
        "app.evaluation",
    }
```

4. **C1 forced hunk (`:42`; architect-ratified 2026-10-23)** — the phase-local `PACKAGE_APP_IMPORTS` (whose `scan_phase5_imports` covers `app/storage/**` via `:113`) gains the sanctioned one-way import:

```python
    "app.storage": {"app.domain", "app.forecasts", "app.storage", "app.evaluation"},
```

(This brief's A3 Authority line already named "`app.storage`'s new import of `app.evaluation`" but the first-draft touch surface omitted this line — the audit gap the builder reported as C1. Without it the scan flags `forecasts_db.py`'s `from app.evaluation import …`. The import direction is storage→evaluation only (decision 1; `app/evaluation/**` imports no storage — verified, criterion 22's AST pin); the round-trip proof is test-side (criterion 15). No other file needs this edit: phase4's local dict covers only simulation/scenarios — probed.)

5. **C6 comment hygiene (`:456–461`; line-neutral, 6 → 6 lines)** — `:456` `exactly thirteen keys` → `exactly fourteen keys`; `:461` `…(app.decisions) — scan still clean.` → `…(app.decisions); A6/Phase 11 sets 13 -> 14 (app.evaluation) — scan still clean.`

## AMENDMENT A4 — `tests/test_phase6_separation.py`

**Authority:** universe extension, duplicated `app.storage` value pin, self-checks, and the Phase-5 byte-pin that crosses `app/storage`. **Touch surface:** `:259–269`, `:406–411` (C6 comment hygiene), `:421–435` (C2), `:452–458` (C6/C2); projected file length 510 → ~518.

1. `:259–269` (criterion-16 byte-pin vs `PHASE5_CHECKPOINT`) — the diff target list drops `"app/storage"` (sanctioned Phase 11 schema work), leaving `"app/models", "app/forecasts"`, with the comment extended by one line: `# app/storage dropped by Phase 11 AMENDMENT A4 (SCHEMA_VERSION 2 + evaluations table).` The three assertions stay verbatim.
2. `:421` — `expected_legacy`'s `app.storage` value becomes `{"app.domain", "app.forecasts", "app.storage", "app.evaluation"}`.
3. `:424` — `len(...) == 13` → `== 14`.
4. `:425` — key-union literal gains `"app.evaluation"`.
5. `:433–435` — **C2 architect-ratified 2026-10-23**: the `PURE_PACKAGES` exact-set line gains `app.evaluation` (six-set), with its two-line comment reading exactly:

```python
    # Phase 11 AMENDMENT A4 (C2, architect-ratified): app.evaluation JOINS the
    # pure set (stdlib + domain/forecasts/backtesting imports only).
    assert hygiene.PURE_PACKAGES == {"app.domain", "app.validation", "app.features", "app.decisions", "app.backtesting", "app.evaluation"}
```

(The first-draft five-set text contradicted this brief's own ADV-7(2) and criterion 22, and its stated rule is false: `app.decisions`/`app.backtesting` import `app.forecasts` and are pure members. The enforced purity rule is no `os`/`sys`/`pathlib`/`io` and no `open()` — which `app/evaluation/**` satisfies; registration is strictly stronger. The false `(user-ruled C2)` provenance label is replaced by `(C2, architect-ratified)` everywhere — C6.)
6. `:456` — `"len(hygiene.ALLOWED_APP_IMPORTS) == 13" in amended` → `"== 14"`, and the name check adds `'and \'"app.evaluation"\' in amended`.
7. `:458` — excluded stale counts `(10, 11, 12)` → `(10, 11, 12, 13)`.

8. **C6 comment hygiene (line-neutral)** — `:406` `exactly THIRTEEN keys (Phase 9` → `exactly FOURTEEN keys (Phase 9`; `:407` `A3');` → `A3' + Phase 11 A6);`; `:410` `sanctioned five-package strengthening (Phases 7/9 A1 + A3 add` → `sanctioned six-package strengthening (Phases 7/9 A1 + A3 add`; `:411` `app.decisions, app.backtesting);` → `app.decisions, app.backtesting; Phase 11 A6 adds app.evaluation);`; `:453` `both declare the 13-key universe with app.features, app.decisions` → `both declare the 14-key universe (Phase 11 A6) with app.features,`; `:454` `and app.backtesting in the union, and both still assert every legacy` → `app.decisions, app.backtesting, app.evaluation in the union; both still assert every legacy`. File line count unchanged.

## AMENDMENT A5 — `tests/test_phase7_separation.py`

**Authority:** same surfaces in the Phase 7 file, plus its `SCHEMA_VERSION` pin. **Touch surface:** `:38–42`, `:328–335`, `:375–380` (C6), `:388–412` (C2), `:426–428` (C6), `:431–435`; projected file length 443 → ~451.

1. `:38–42` — `PROTECTED_PACKAGES` drops `"app/storage"` (9 entries remain), comment gains one line noting the Phase 11 exclusion.
2. `:328–334` — the byte-pin diff block itself is untouched (it splats `*PROTECTED_PACKAGES`).
3. `:335` — `assert forecasts_db.SCHEMA_VERSION == 1  # unchanged` → `assert forecasts_db.SCHEMA_VERSION == 2  # Phase 11 AMENDMENT A5: evaluations table`.
4. `:388` — `expected_legacy`'s `app.storage` value gains `"app.evaluation"` (same hunk text as A3 item 3).
5. `:391` — `len(...) == 13` → `== 14`.
6. `:392–395` — key-union literal gains `"app.evaluation"`.
7. `:408–412` — **C2 architect-ratified 2026-10-23**: the `PURE_PACKAGES` multi-line exact-set gains `app.evaluation` (six-set; same correction and rationale as A4 item 5), its preceding two-line comment reading exactly:

```python
    # Phase 11 AMENDMENT A5 (C2, architect-ratified): app.evaluation JOINS the
    # pure set (stdlib + domain/forecasts/backtesting imports only).
```
8. `:431` — `"len(hygiene.ALLOWED_APP_IMPORTS) == 13" in source` → `"== 14"`, name check adds `'and \'"app.evaluation"\' in source`.
9. `:433–435` — the three not-in lines add a fourth: `assert "len(hygiene.ALLOWED_APP_IMPORTS) == 13" not in source, name`.

10. **C6 comment hygiene (line-neutral)** — `:375` `exactly 13 keys (Phase 9 A3')` → `exactly 14 keys (Phase 9 A3', Phase 11 A6)`; `:378` `five-package strengthening;` → `six-package strengthening (A6);`; `:426` `the exact 13-key universe (Phase 9 A3')` → `the exact 14-key universe (Phase 11 A6)`; `:427` `with app.decisions and app.backtesting in the union, and none of` → `with app.decisions, app.backtesting and app.evaluation in the union, and none of`; `:428` `== 10`/`== 11`/`== 12` → add ``/`== 13` `` to the surviving-forms list. File line count unchanged.

## AMENDMENT A6 — `tests/test_fixtures_and_hygiene.py`

**Authority:** the universe itself (single source of truth). **Touch surface:** `:49–67`; projected file length 409 → ~416. **Not touched:** `BANNED_IMPORT_EXCEPTIONS` (stays exactly `{"app.storage": {"sqlite3"}, "app/api": {"http"}}`, `:42–45`).

1. New key appended after `app.backtesting` (`:63`):

```python
    "app.evaluation": {"app.domain", "app.forecasts", "app.backtesting", "app.evaluation"},  # Phase 11: evaluation imports stdlib + app.domain/app.forecasts/app.backtesting only (pure statistical code, no storage/HTTP)
```

2. `:63–64` — `len` value pins that live in other files are handled there; this file's own `ALLOWED_APP_IMPORTS` docstring comment is updated from thirteen to fourteen keys.
3. `PURE_PACKAGES` (`:67`) — **six-set: `app.evaluation` joins** (C2 architect-ratified 2026-10-23, superseding the first-draft five-set text, which contradicted this brief's own ADV-7(2) ("PURE_PACKAGES 5 → 6") and criterion 22 ("the exact six-set with app.evaluation") and asserted a rule the existing set already falsifies — `app.decisions`/`app.backtesting` import `app.forecasts` and are members; the enforced rule is no `os`/`sys`/`pathlib`/`io` imports and no `open()`, which `app/evaluation/**` satisfies by probe; registration is the Phase 6/7/9 strictly-stronger pattern). The block must read exactly (the false `(user-ruled C2)` label is replaced — C6):

```python
# Phase 11 AMENDMENT A6 (C2, architect-ratified): app.evaluation JOINS the pure
# set — stdlib + domain/forecasts/backtesting imports only, no storage/HTTP.
PURE_PACKAGES = {"app.domain", "app.validation", "app.features", "app.decisions", "app.backtesting", "app.evaluation"}
```
4. `app.storage` value (`:58`) — gains `"app.evaluation"` (one-way: storage imports `EvaluationRecord`/`EvaluationConflictError`; `app.evaluation` imports no storage).

## AMENDMENT A7 — `tests/test_backtesting.py`

**Authority:** exactness block re-point to Phase 11 + storage introspection across the schema bump. **Touch surface:** `:577–586`, `:626–653`; projected file length 626 → ~645. **Not touched:** the five-entry banned-name knob scan (`:413–419`) — it stays five entries, undeclared edit avoided (decision 12).

1. `:577–578` — comment "exactly one table" → "exactly the two pinned tables".
2. `:582–583` — `assert tables == ("forecasts",)` → `assert tables == ("forecasts", "evaluations")` (creation order, pinned after the build-probe; never relaxed to `set(...)`).
3. `:586` — `assert forecasts_db.SCHEMA_VERSION == 1` → `== 2`.
4. `:628` — `assert temporal.PHASE8_CHECKPOINT == "ea92667"` → `assert temporal.PHASE10_CHECKPOINT == "8abe1ca"`.
5. `:629–632` — the 6-key `set(temporal.POISON_REGISTRY)` literal gains `"evaluate_predictions"`, and a new per-entry pin follows the existing `run_walk_forward` pin:

```python
    assert temporal.POISON_REGISTRY["evaluate_predictions"] == (
        "test_evaluation", "test_poisoned_extra_matches_leave_evaluation_unchanged",
    )
```

6. `:638–640` — `temporal.MATCHES_ENTRY_POINTS` 4-tuple → 5-tuple adding `"evaluate_predictions"`.
7. `:642–648` — the `set(temporal.PRE_EXISTING_APP)` literal swaps `"app/storage"` for `"app/backtesting"` (12 names); the `assert "app/backtesting" not in temporal.PRE_EXISTING_APP` line is replaced by:

```python
    assert "app/storage" not in temporal.PRE_EXISTING_APP
    assert "app/evaluation" not in temporal.PRE_EXISTING_APP
```

8. `:650` — `len(hygiene.ALLOWED_APP_IMPORTS) == 13` → `== 14`.
9. New value pins immediately after the existing `app.backtesting` value pin:

```python
    assert hygiene.ALLOWED_APP_IMPORTS["app.evaluation"] == {
        "app.domain", "app.forecasts", "app.backtesting", "app.evaluation",
    }
    assert hygiene.ALLOWED_APP_IMPORTS["app.storage"] == {
        "app.domain", "app.forecasts", "app.storage", "app.evaluation",
    }
```

10. `:650–654` — **C2 architect-ratified 2026-10-23**: the `PURE_PACKAGES` set pin gains `app.evaluation` (six-set; same correction as A4 item 5), and the comment's false provenance label is replaced: `# value, the six-package pure set (user-ruled C2).` → `# value, the six-package pure set (C2, architect-ratified).`

## AMENDMENT A8 — `tests/test_vocab_guards.py`

**Authority:** ADV-9's single structural exemption (metric identifiers legal in `app/evaluation/` only). **Touch surface:** `:28–33`, `:87–94`, `:210–213`, `:416–419`; projected file length 339 → ~352. **Not weakened anywhere:** `SCORING_ALLOWLIST` stays exactly one entry (`:31–33`, `:195–198`); the comparative-pattern app-wide zero-hit assert, the accuracy trio, and the `FIELD_BAN` machinery run unchanged — including inside `app/evaluation/` (zero `validated`/`accurate`/`beating`/`accuracy` words allowed there).

1. New constant after `SCORING_ALLOWLIST`:

```python
# Criterion (Phase 11): the ONE structural exemption — the evaluation
# package's own metric identifiers (log_loss, brier, rps + variants) are
# legal HERE and only here. Prefix-scoped, never a per-sentence allowlist.
SCORING_EXEMPT_PREFIXES: tuple[str, ...] = ("app/evaluation/",)
```

2. `scoring_violations` (`:87–94`) gains the prefix gate as its first line of defense, spans logic untouched:

```python
    if rel_path.startswith(SCORING_EXEMPT_PREFIXES):
        return []
```

(the comparative/FIELD_BAN scans are separate functions and do not consult this gate.)

3. The two `files_with_hits` loops (`:210–213` and `:416–419`) each gain, before the `if phase7._SCORING_PATTERN.search(text):` line:

```python
        if rel.startswith(SCORING_EXEMPT_PREFIXES):
            continue
```

with the trailing exact-set asserts unchanged (`files_with_hits == {SIMULATION_INIT}` in both loops — `app/evaluation/` files never enter the set).

4. New probe pinning the exemption boundary in both directions: an `app/evaluation/metrics.py`-shaped snippet with `log_loss`/`brier`/`rps` identifiers produces zero scoring violations under the `app/evaluation/` rel path, and the identical text under `app/models/probe.py` produces non-zero hits.

## AMENDMENT A9 — `tests/test_storage.py`

**Authority:** criterion 17 (the evaluations table lives here — storage is the one sanctioned file change). **Touch surface:** one appended test; projected file length 440 → ~480. **Not touched:** `PINNED_COLUMNS` (`:83`), the forecasts triggers (`:120–148`), and the forecasts-column pins (`:396–408`) — all forecasts-scoped and still green.

New test `test_evaluations_table_write_once_no_timestamp_schema_v2`, asserting: `forecasts_db.SCHEMA_VERSION == 2`; `sqlite_master` tables == exactly `("forecasts", "evaluations")` (order pinned after the build-probe; never `set(...)`); `PRAGMA table_info(evaluations)` == exactly `(evaluation_version, run_digest, fixture_file_sha256s, payload, content_hash)`; **no timestamp-like column anywhere in that tuple**; raw `UPDATE` and raw `DELETE` on `evaluations` each raise with `immutable` in the message (mirror of the forecasts triggers, message text pinned as observed); a second insert of an identical record is the idempotent no-op — returns `False` with **zero INSERTs** (C4 correction 2026-10-23: this first-draft prose said "raises", contradicting criterion 16, decision 1, and the `insert_forecast`/§11(d) precedent — criterion 16 governs) — and a differing-content record under the same natural identity raises `EvaluationConflictError` (write-once); the forecasts table still exposes exactly its 21 pinned columns. The appended test's opening NOTE block must read (C4, comment-only, 6 → 6 lines): `NOTE: Semantics per criterion 16 as amended 2026-10-23 — the second identical insert is the idempotent False no-op (zero INSERTs); only a DIFFERING payload under the same natural identity raises EvaluationConflictError.`

## AMENDMENT A10 — `tests/test_operational.py`

**Authority:** criterion 8 re-point to this checkpoint + the golden-set rescope (C3). **Touch surface:** `:58`, `:61–71`, `:401–409`; projected file length 425 → ~429.

1. `:58` — `PHASE9_COMMIT = "80b8f79"` → `PHASE11_COMMIT = "8abe1ca"` (comment gains one line: re-pointed by Phase 11 AMENDMENT A10, never widened).
2. `:61–71` — **C3 architect-ratified 2026-10-23**: `GOLDEN_PIN_FILES` is rebuilt as a **six-entry** tuple. The three files this phase amends (`tests/test_backtesting.py` — A7, `tests/test_temporal_integrity.py` — A1, `tests/test_vocab_guards.py` — A8) are **removed** — they cannot stay byte-identical to `8abe1ca` once amended, exactly the rescope this brief's own decision 12 already recorded ("three golden files removed from `GOLDEN_PIN_FILES`"), which the first-draft "tenth entry" wording of A10.2 contradicted. `tests/test_evaluation.py` does **not** enter: a file absent at the pinned commit diffs empty only while untracked (green now) and emits its full new-file diff the moment the checkpoint commit tracks it — reproduced read-only 2026-10-23 (clone → commit → criterion 8 FAILED on exactly this line, 779-line new-file diff). Phase 10 precedent: a phase never byte-pins its own new or amended test files. The removed three **plus** `tests/test_evaluation.py` re-enter at the next criterion-8 re-point, pinned against Phase 11's own commit (carry-forward note for a future brief — not scoped here):

```python
GOLDEN_PIN_FILES = (
    "tests/test_forecasts.py",
    "tests/test_features.py",
    "tests/test_decisions.py",
    "tests/test_simulation.py",
    "tests/test_poisson_fit.py",
    "tests/test_scoreline_matrix.py",
)
```

with the comment at `:61–63` reading exactly (3 lines → 3 lines):

```python
# Criterion 8 (Phase 11 AMENDMENT A10, C3 architect-ratified): the
# golden-pin files at this checkpoint, byte-pinned (six files; the
# three amended guards + test_evaluation re-enter at the next re-point).
```
3. `:401–409` — the test is renamed `test_app_and_golden_files_byte_pinned_vs_phase11` and its app diff excludes the two sanctioned surfaces:

```python
    assert _git_diff("app/", ":(exclude)app/storage", ":(exclude)app/evaluation") == ""
```

(the `assert _git_diff(*GOLDEN_PIN_FILES) == ""` line is unchanged and now covers the six-entry tuple; the app/-excludes line was verified post-commit green in the same 2026-10-23 clone probe.)

---

*Brief authored by glass-architect 2026-10-22/23 against HANDOFF IX-11 and glass-quant ADV-1–ADV-14. Builder implements Phase 11 exactly as written; any structural surprise is a STOP-and-report, not a decision.*

---

## Adjudication record — builder deviations C1–C10 (2026-10-23, glass-architect; Phase 9 A3' precedent)

**Provenance (read this first).** The Phase 11 builder, having completed the BUILD step green (suite 178 passed, health OK, nothing staged, DOCS step not yet begun), reported ten deviations from this brief's amendment texts and labeled several of them "user-ruled" (C2/C3). **No developer ruling exists in this loop: there was no developer contact.** Every "user-ruled" label — in the builder's report and in the tree — is builder-proposed and is treated as such here. The architect (owner of this brief) adjudicated each item empirically against the tree: import-graph probes, `git diff` audits against `8abe1ca`, a full clone-and-commit reproduction of criterion 8's post-commit behavior, and a full-suite run (178 passed in 233 s). Where a builder item exposed a **defect in this brief**, the brief is amended in place with correction text and provenance (the Phase 9 A3' pattern); **the amendment texts as amended here are the binding texts**. The false `(user-ruled C2)`/`(user-ruled C3)` provenance labels are corrected by the C6 hygiene items above and this note; the PROGRESS-LOG Phase 11 entry must record all ten items as **builder-proposed, architect-adjudicated 2026-10-23** — never as developer rulings.

**Rulings:**

1. **C1 — RATIFY + brief amended (A3 item 4, touch surface).** `app/evaluation` imports NO storage (probe + criterion 22's green AST pin); the sanctioned edge is `app/storage/forecasts_db.py:25` → `app.evaluation` (decision 1, one-way). The edit at `test_phase5_separation.py:42` (phase-local `PACKAGE_APP_IMPORTS["app.storage"]`) is a forced hunk of that sanctioned import — the file's criterion-22 scan covers `app/storage/**` — and belongs exactly where the builder put it. The brief's A3 Authority already named the import but the first-draft touch surface omitted `:42`: an audit gap (brief defect), not builder overreach. phase4's local dict covers only simulation/scenarios and needs no edit (probed).
2. **C2 — RATIFY + brief amended (A4.5/A5.7/A6.3/A7.10).** `app/evaluation` is genuinely pure under the enforced rule (no `os`/`sys`/`pathlib`/`io`, no `open()` — probed), and this brief's own ADV-7(2) ("PURE_PACKAGES 5 → 6") and criterion 22 ("the exact six-set with app.evaluation") mandated the six-set. The four "unchanged five-set" texts were the brief's error, including a stated purity rule the existing set already falsifies (`app.decisions`/`app.backtesting` import `app.forecasts` and are members). Six-set RATIFIED as the corrected brief text; provenance labels corrected.
3. **C3 — SPLIT: removals RATIFIED (A10.2 amended), the `test_evaluation` addition REVERTED.** The three removed guards are amended this phase (A1/A7/A8) and cannot stay byte-identical to `8abe1ca`; decision 12 already recorded their removal; their Phase 9 goldens remain covered cross-file (criterion 1 re-derives the same digest literal; criterion 22 + A7's exactness block pin registry/census/checkpoint/pure sets; declared hunks + `wc -l` actuals + reviewer checklist (vi) cover the changed surfaces). The `PHASE9_COMMIT`→`PHASE11_COMMIT` re-point, the rename, and the app/-excludes line are per-brief, verified, and the excludes line is post-commit green (clone probe). **However `tests/test_evaluation.py` must NOT enter `GOLDEN_PIN_FILES`**: its diff vs `8abe1ca` is empty only while untracked and goes red the moment the checkpoint commits it (clone-reproduced). Final tuple = six entries; the three guards + `test_evaluation` re-enter at the next criterion-8 re-point (carry-forward note, not scoped here).
4. **C4 — RATIFY + brief amended (A9 prose).** Criterion 16 governs and is right: second identical insert → `False` with zero INSERTs (decision 1; `insert_forecast`/§11(d) write-once-idempotence precedent); only identity + differing content raises `EvaluationConflictError`. The shipped `test_storage` test implements criterion 16 exactly.
5. **C5 — RATIFY + brief amended (criterion 14(c) + State line).** The pinned checkpoint's `forecasts_db.__all__` holds **11** names (enumerated; the 13-line span `:327–339` confirms); the test pins 11 ∪ {`insert_evaluation_record`} = **12**, and its in-test comment flagged the prose discrepancy — resolved by this correction. **Follow-up sanction C5f (2026-10-23, glass-architect):** with criterion 14(c) amended to 11, the in-test comment's present-tense parenthetical "criterion 14's prose says 10 — actual 11" (`tests/test_evaluation.py:510`) now actively contradicts the binding prose — the exact C6-class reviewer trap; the "honest history" argument fails because the first-draft-10 history is already preserved twice (the amended prose's own C5 provenance note and C5 above), and a tree comment must describe the current state, not archive drafts. **Sanctioned replacement (line-neutral 1→1, comment-only, file stays 779 lines):** on `tests/test_evaluation.py:510`, replace the entire comment — `# 11 ACTUAL pre-existing names (criterion 14's prose says 10 — actual 11)` → `# 11 pre-existing names (criterion 14(c) as amended 2026-10-23)` (house style per the C4-sanctioned `test_storage` NOTE; "ACTUAL" drops because no discrepancy remains). Builder applies exactly this one replacement, nothing beyond; suite re-run green required, no functional change expected.
6. **C6 — RATIFY, extended to all files.** Line-neutral comment updates are sanctioned (Phase 7 A4 precedent: "stale comments updated as comment text only"), NOT a KNOWN-LIMITATIONS note: comments asserting "thirteen keys"/"five-package"/"six entry points" directly above pins reading 14/six/seven are reviewer traps on declared amendment surfaces. The architect's scan found stale sites the builder did not declare (`phase4 :788–795`, `phase5 :456–461`, `phase6 :406–411/:452–454`); all sites, plus the `(user-ruled …)` label fixes (hygiene, phase6, phase7, backtesting, operational, and `tests/test_evaluation.py:717` — the phase's own new file, corrected in the same pass) and the `test_storage` NOTE (C4), are covered by the per-amendment items above. Every edit comment-only with per-file `wc -l` unchanged; final actuals declared at checkpoint.
7. **C7 — RATIFY + brief amended (prose lines).** Criteria govern: the metric functions take the 3-tuple form `log_loss(outcome_probs, outcome)` (file-step line 63's four-arg prose corrected); criterion 22's parenthetical corrected to "three positionals; `matches` is POSITIONAL_OR_KEYWORD; the digest pair is keyword-only after `*`" (criterion 1's call form; kinds are asserted in the shipped criterion-22 test).
8. **C8 — ACCEPT with declaration; no split mandated.** The ≤~620 figure was explicitly a projection (amendment preamble). 779 lines carry all 21 declared tests (criteria 1–16, 18–22 — verified present, suite green, none cut); precedent: phase4 835 (declared), backtesting 664 (accepted). A split would break `POISON_REGISTRY["evaluate_predictions"]`'s module name and scatter the golden literals/module-scoped fixture — rework risk without analytical gain. Declare `wc -l` 779 in the PROGRESS-LOG actuals, the HEALTH-LOG rule-6 line, and the KNOWN-LIMITATIONS amendment row.
9. **C9 — RATIFY + brief amended (decision 14/criterion 23/preamble).** The brief's own A8 item 4 declared the extra boundary-probe test while decision 14's arithmetic omitted it. Suite of record: **155 + 21 + 1 + 1 = 178**; tester/reviewer/monitor gate on 178 (still a prediction, never a claimed fact).
10. **C10 — VERIFIED.** `app/evaluation/**` imports exactly `{app.domain, app.forecasts, app.backtesting, dataclasses, hashlib, json, math, typing}` — no os/sys/pathlib/io/open/time/random/datetime, no `app.storage`/`app.api` (probe + green AST pin). `git diff 8abe1ca -- app/storage` = sanctioned only: `forecasts_db.py` +97/−8 (SCHEMA_VERSION 2; evaluations DDL + trigger pair; `insert_evaluation_record`; `__all__`/exports — **no read-path hunk**) and `__init__.py` +2. Golden spot-checks: smallest scored probability `0.12816022966803042` ≈ the ADV-4/§13 probe 0.128 and `> 0.1`; hand values re-derived independently (`rps` 0.11125 = ½(0.16 + 0.0625); `brier` 0.38); `GOLDEN_METRICS` in valid ranges with correct n (30/57); calibration bins sum to 90 = 3×30 with the ~81% dominant-bin share. All ten amended files green in the 178-passed suite; nothing staged. The suite must be re-run green after these adjudication edits are applied, and criterion 8 must be verified green both pre- and post-commit (the C3 revert makes it so).

**None of C1–C10 is developer-territory**: all are mechanical pin-collision, brief-internal prose-consistency, or arithmetic-reconciliation items of the class ratified across Phases 3–10; ADV-14's "ZERO developer questions" and this brief's no-open-questions position stand unchanged.
