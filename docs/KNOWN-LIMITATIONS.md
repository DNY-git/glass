# KNOWN LIMITATIONS — SPORTS LOOKING GLASS

The honest list. Updated every phase (constitution; HANDOFF Part IX item
13 formalizes this at Phase 13, but the discipline starts now). Nothing
here is hidden behavior — each item is also recorded where it was found.

Entry below reflects the state as of Phase 7 (Decision analysis),
2026-10-19.

## Phase 1

1. **`scripts/health-check.sh` intentionally exits 0 on failed inner
   checks** (tester finding G2). The script uses `set -u` only, so a
   failing check prints its failure but cannot abort the sweep — by
   design, for monitoring continuity. Consequence: the script's exit code
   is not a pass/fail gate. The gate is a **direct** suite run
   (`.venv/bin/python -m pytest -q`) — Phase 1 acceptance criterion 10,
   verified by recorded direct runs from tester, reviewer, and monitor.
   Always read the script's output; never rely on its exit code alone.

2. **The health-script test has a bounded timeout budget** (tester
   finding G4; stale figure corrected this phase per monitor finding 2).
   The 120 s timeout of `tests/test_health_script.py` wraps one
   `bash scripts/health-check.sh` run, which internally invokes pytest
   five times (two visible runs, a skip/xfail run, and the two runs of
   the determinism comparison). An earlier "~85 s of that margin" figure
   could not be reproduced and is replaced by measured values: full
   health-script invocations of ~12.9 s (Phase 1 monitor sweep,
   2026-10-16) and ~47.5 s (Phase 2 docs run, 2026-10-16, machine under
   concurrent load) — a remaining margin of roughly 72–107 s, i.e. the
   timeout currently has at least ~2.5x headroom in the worst observed
   load and more when idle. A much slower machine or a much larger suite
   can still push it over. If it trips, the responsible phase's brief
   must **re-scope the mechanism** — never weaken, skip, or xfail the
   test (constitution).
   **Update 2026-10-17 (Phase 4 — AMENDMENT A2, the predicted trip
   happened; prior figures above kept as measured, nothing rewritten).**
   During the Phase 4 build, under sustained external load average
   10.27–10.43 (not this project's load), the direct suite reported
   `54 passed, 3 errors` on two consecutive runs — all three errors
   `subprocess.TimeoutExpired` (120 s) from the module-scoped fixture in
   `tests/test_health_script.py`. The health script itself was
   functional and honest: a standalone `bash scripts/health-check.sh`
   completed every section (compile clean, determinism `OK`, skips/xfails
   `none`, pip clean) in 128 s (2m08s); only the test's wall-clock
   budget failed, no asserted property of the script. Per this item's
   own trigger, AMENDMENT A2 of the Phase 4 brief re-scoped the timeout
   **120 s → 300 s** (2.34× the worst observed completion) in exactly
   two in-place edits to `tests/test_health_script.py` — the
   `HEALTH_TIMEOUT_S` constant and its matching docstring figure — file
   size unchanged (105 lines). **No assertion changed**: the health
   tests still assert content and completion (exit 0 + all section
   headers, `OK:` determinism, no `MISMATCH`, `none` skips, clean pip);
   a script that hangs >300 s, exits non-zero, drops a section,
   mismatches, shows a skip, or breaks pip fails exactly as before. The
   trigger stands for any future trip: evidence-based re-scope in the
   responsible phase's brief, never a weakened, skipped, or xfailed
   test — and re-architecting the script's five inner runs is
   explicitly Phase 10's (HANDOFF IX-10).

3. **Criterion 7 header checks are substring-based** (tester finding G3).
   `test_health_script_runs_to_completion` asserts that the script's
   output contains each expected section header as a literal substring.
   This is a weak structural guarantee (a stray occurrence elsewhere
   would satisfy it) but is adequate for Phase 1's purpose: detecting the
   pre-Phase-1 early exit and confirming all sections ran. To be
   revisited if the health script's output format evolves.

4. **pytest is installed unpinned** (developer decision, Phase 1 brief
   open question 3). No requirements/pyproject pinning file exists. The
   exact installed version is recorded in `docs/PROGRESS-LOG.md` (as of
   Phase 1: pytest 9.1.1, pip 26.2.1, Python 3.12.3). A future environment
   change could silently upgrade pytest; pinning will be revisited only if
   a future phase shows it is needed. The venv itself was bootstrapped
   with `uv` (one-time, developer-approved); `uv` is not a product
   dependency and nothing imports it.

5. **Suite runtime is dominated by health-script spawning.** The direct
   suite (24 tests as of Phase 2) is slow relative to what it tests
   because the health test spawns the health script, which internally
   runs the non-health suite five times (see item 2) — an accepted
   multiple-of-suite cost while the health test exists (brief risk
   register). Recorded direct-suite runs this phase range roughly 13–60 s
   depending on machine load (48.96 s in the Phase 2 docs run under
   concurrent load; Phase 1 idle-machine runs were 13–23 s). Harmless at
   current scale; if it becomes a bottleneck, a later brief must re-scope
   it — never weaken the test.

## Phase 2

1. **Synthetic fixtures diverge from real OpenFootball quirks.** The
   loader was built and tested against hand-authored, well-formed
   OpenFootball-*shaped* JSON (see `docs/DATA-SOURCES.md`). Real files
   may carry quirks the defect fixture under-covers: unexpected score
   shapes, inconsistent name spellings, stray encodings, or fields this
   phase never saw. If real data is later accepted (Phase 2 brief open
   question 1, option b), the loader needs tolerance work and this
   phase's fixture set may need re-scoping (brief risk "Data quality /
   format drift").

2. **JSON encodings only.** Phase 2 implements exactly one encoding:
   JSON match lists. The CSV encodings mentioned in the handoff are
   unimplemented; a CSV loader arrives only when a source needs it
   (brief design decision 3).

3. **No durable storage yet.** `app/storage/` and the `data/` directory
   are deferred (brief design decision 1): accepted state lives in an
   in-memory `MatchCollection`, rebuilt per import, and idempotency is
   proven at the loader/collection level — not against a database. The
   stdlib-sqlite proposal returns in the first brief that needs durable
   state (immutable snapshots, Phase 5+).

4. **Natural-key collisions.** The natural key (competition, season,
   date, home, away) cannot distinguish two distinct matches between the
   same pair on one day (a double-header). Impossible in the synthetic
   fixtures by construction; documented here, not silently accepted — a
   real source exhibiting this would need a key extension (e.g. round or
   a source-unique id).

5. **The criterion-12 AST hygiene scan has inherent, documented limits.**
   `tests/test_fixtures_and_hygiene.py` is a static AST scan of `app/`,
   not a sandbox:
   - **Indirection evades it.** Wall-clock or environment access hidden
     behind `getattr(...)`, `eval`, `exec`, `__import__`, or
     `importlib`, or behind attribute chains not rooted in a plain
     imported name (e.g. `get_os().environ`), cannot be resolved
     statically and is not flagged.
   - **Timezone-derivative datetime members are off the banned sets.**
     `astimezone()` with no arguments on a naive receiver reads the
     local timezone; naive-receiver `timestamp()` and the classmethod
     `fromtimestamp()` are likewise TZ-derived. They are deliberately
     not members of `WALL_CLOCK_CALLS`/`ENVIRONMENT_PATHS` (which cover
     current-time readers and environment lookups) — not covered, and
     not claimed to be.
   - **Star-import use-site detection is deliberately out of scope.**
     `from os|time|datetime import *` binds banned names as bare Names
     that the use-site scan cannot resolve (BUG-T2); the scan therefore
     flags the **import statement itself**, which covers any subsequent
     use regardless of spelling.
   - The banned-name sets (`WALL_CLOCK_CALLS`, `ENVIRONMENT_PATHS`) are
     **explicit finite enumerations maintained by hand; their
     completeness is never claimed**. Enforcement is reviewer audits of
     the stdlib for missed twins (`time.clock_gettime_ns` and
     `time.timezone` were caught exactly that way), plus a
     positive-control probe test
     (`test_wall_clock_env_scan_flags_every_banned_form`) pinning every
     known banned form so detection cannot silently regress.

## Phase 3

1. **In-sample estimates only — never evidence of accuracy.** Every
   number from `app/models/` (fitted parameters, scoreline matrices,
   outcome probabilities) is an in-sample fit on the synthetic fixture
   pool. Convergence, normalization to 1, and plausible-looking
   probabilities demonstrate *internal consistency* only —
   **normalized ≠ accurate** (constitution; docs/STATISTICAL-ASSUMPTIONS.md
   §6). Evidence begins at Phases 9 (chronological backtesting) and 11
   (evaluation against realized results); neither has run. Until they
   do, no number from this stage may be described as validated,
   accurate, or beating anything.

2. **Overdispersion ignored (var = mean).** The Poisson assumption
   (variance equal to mean) understates tail probabilities of
   high-scoring outliers and overstates the precision of fitted
   parameters; football goal counts are commonly overdispersed, and a
   negative-binomial alternative is the standard remedy. Explicitly
   **deferred to Phase 11** (variance-vs-mean diagnostics alongside
   predictive scores) — deferred, not forgotten
   (STATISTICAL-ASSUMPTIONS §2b).

3. **Draw bias of independent Poissons.** Independent home/away goal
   draws characteristically under-represent draws — the missing
   low-score dependence a Dixon-Coles-style correction targets.
   Drawn scorelines will be systematically underpredicted until that
   correction ships, which Phase 11 draw-frequency calibration must
   justify (STATISTICAL-ASSUMPTIONS §2f).

4. **Scoreline truncation bound K = 10.** Scoreline cells cover 0..10
   goals per side (11×11); at fixture-fitted lambdas this drops at
   most ≤ 6×10⁻⁴ of joint mass (asserted by test; the K=15 alternative
   would drop ≤ 1.2×10⁻⁷). Dropped mass is **always reported** on the
   matrix, never hidden; W/D/L probabilities come from analytic
   Poisson tails and are exact under any truncation
   (STATISTICAL-ASSUMPTIONS §4).

5. **Stationarity across pooled seasons.** Both fixture seasons
   (2024-25 + 2025-26) are pooled under a single (μ, α, β, h);
   pooled strengths average over regimes and describe no single
   season exactly. Each fit records the pooling it consumed in
   provenance so the assumption is always visible
   (STATISTICAL-ASSUMPTIONS §2e).

6. **All fits consume synthetic fixtures.** The entire statistical
   layer has only ever seen the fictional "Obsidian Coast League"
   (6 teams, 60 matches, 156 goals). Real data may behave differently
   — and the Phase 2 loader limitation (real-file quirks) compounds
   this: a fit on real data is untested territory end to end.

7. **Thin data is flag-not-crash, and flagged numbers are not
   estimates to trust.** A first-matchday cutoff returns a well-formed
   `SINGULAR_SYSTEM` result with insufficient flags attached (measured:
   3 matches, 7 goals, all 6 teams flagged) — no crash; empty history
   returns `NO_DATA`. But the `SINGULAR_SYSTEM` object carries the
   last well-defined iterate: it is a **reported flag, not a fallback
   estimate** — downstream must treat it as unusable, not as noisy
   (STATISTICAL-ASSUMPTIONS §3, §5).

8. **The 612-line hygiene test file now carries one A1-declared line.**
   Amendment A1 to the Phase 3 brief sanctioned exactly one +1 line in
   `tests/test_fixtures_and_hygiene.py` (the
   `ALLOWED_APP_IMPORTS["app.models"]` entry — a dictionary-coverage
   gap the new package would otherwise crash against); declared here
   per the amendment. Monitor finding 2 (file size, carried from
   Phase 2) remains carried; the file grew 611 → 612 lines and nothing
   else in it changed.

## Phase 4

1. **`mc_stderr` measures simulation noise only — no confidence
   intervals exist anywhere.** The `mc_stderr` field of every
   `SimulationResult` is `sqrt(p(1-p)/n_sims)` computed from the
   **analytic** probability: it quantifies Monte Carlo sampling noise
   over a fixed, already-known distribution and nothing else. It is not
   model, parameter, or data uncertainty — there is no bootstrap, no
   parameter sampling, and no confidence band anywhere in this system
   (STATISTICAL-ASSUMPTIONS §7a, §6). Increasing `n_sims` shrinks this
   term and never shrinks uncertainty: a 10⁷-draw run of an in-sample
   estimate is still that same in-sample estimate.

2. **Golden simulation counts are CPython-version-local.** The single
   fixed-seed golden pins exact counts `(5798, 2106, 2096)` for
   `seed=20261017`, `n_sims=10000` on the fixture fit, derived on
   CPython 3.12.3 (`SIM_VERSION = "sim-categorical-v1"`). Draws use
   `random.Random(seed).random()` — CPython documents that sequence as
   stable across versions — but the golden is treated as
   interpreter-local by the Phase 3 golden discipline: on an interpreter
   change, **re-derive and re-document the literal — never widen a
   bound, never delete the golden**.

3. **Scenario multipliers are arbitrary documented knobs — hypothetical
   all the way down.** `MULTIPLIER_MIN = 0.5` / `MULTIPLIER_MAX = 2.0`
   are named, documented, inclusive bounds chosen for usability, not
   estimated from data; every scenario number is a labeled hypothetical
   conditioned on the in-sample fit and **all §2 caveats** of
   STATISTICAL-ASSUMPTIONS. No scenario output is evidence, and none is
   averaged or ensembled — one scenario per call, disagreement reported
   (STATISTICAL-ASSUMPTIONS §7d).

4. **Parameter-scale transforms are sign-dependent.** The shipped
   transform semantics are literal parameter scale (`α′ = m·α`,
   `β′ = m·β`, `h′ = m·h`): a multiplier dulls (m < 1) or amplifies
   (m > 1) the parameter's deviation from league mean, so **the
   direction of the effect on λ depends on the parameter's sign** — the
   same m < 1 moves λ in opposite directions for positive and negative
   α. Stated, not glossed (STATISTICAL-ASSUMPTIONS §7d).

5. **No `out_of_range_count` field exists — by design.** Simulation
   draws categorically over the truncated, renormalized (K+1)²
   matrix rather than from independent untruncated Poissons; MC
   frequencies can therefore deviate from the analytic `outcome_probs`
   target by at most `dropped_mass / (1 − dropped_mass)` ≤ ~6.004×10⁻⁴
   at fixture-fitted lambdas (asserted by test). The untruncated
   alternative was rejected because it would need a second sampling
   path and a second truth surface; the already-disclosed dropped mass
   of Phase 3 item 4 stands in its place. Revisiting requires a future
   brief that says why (STATISTICAL-ASSUMPTIONS §7b).

6. **The hygiene file now carries three A1-declared lines; it grew 612
   → 614 this phase.** AMENDMENT A1 (Phase 4, pre-planned per the
   Phase 2 P1 clause) sanctioned exactly two new
   `ALLOWED_APP_IMPORTS` entries in
   `tests/test_fixtures_and_hygiene.py` (`"app.scenarios"`,
   `"app.simulation"`) — a dictionary-coverage gap the new packages
   would otherwise crash against with `KeyError`; no check was
   weakened, nothing else in that file changed. Declared here and in
   the brief per the amendment; monitor finding 2 (file size) remains
   carried, now covering both the Phase 3 +1 and this +2.

7. **AMENDMENT A2's two in-place edits to a Phase 1 test file
   (105 → 105 lines).** `tests/test_health_script.py` changed by
   exactly the `HEALTH_TIMEOUT_S` constant (120 → 300 s) and its
   matching docstring figure — the evidence-based re-scope of the
   predicted health-timeout trip; full story, evidence, and the
   no-assertion-changed reasoning are in Phase 1 item 2's
   2026-10-17 update. Declared here so the diff is not read as
   unexplained change to a Phase 1 test.

8. **`simulate` refuses a scenario whose baseline does not equal the
   given fitted object.** `simulate(..., scenario=s)` raises
   `ValueError` unless `s.baseline == fitted` (frozen-dataclass value
   equality) — simulating under a mismatched baseline would draw from
   one fit's distribution while echoing another fit's provenance
   (mislabeled output), so it is refused, never reconciled silently.
   Implemented beyond the pre-build spec, test-pinned, documented in
   STATISTICAL-ASSUMPTIONS §7g.

## Phase 5

1. **Day-granularity cutoff — within-day ordering is impossible and
   wall-clock pre-kickoff ordering is unverifiable (L1, mandated
   wording).** The forecast cutoff is `fixture.date`, a strict
   day-granularity date string computed inside
   `build_forecast` (`as_of` is stored as exactly that date string).
   The engine therefore **cannot exploit within-day ordering even when
   a kickoff time is known** — two matches dated the same day cannot be
   ordered against each other — and **cannot verify wall-clock
   pre-kickoff ordering at all**: the domain has dates, no clock, and
   no wall clock exists anywhere in forecast content or schema
   (STATISTICAL-ASSUMPTIONS §8a, §8d). The guarantee, stated precisely:
   **nothing dated on or after the fixture date can enter the fit** — a
   match dated exactly at the fixture date is excluded by `fit`'s
   strict `date < as_of` (double-enforced: the builder also refuses a
   fixture whose natural key appears in the history). This is honest
   day-level pre-match discipline, never described as anything finer.

2. **Forecast identity inherits the double-header natural-key
   limitation (carried from Phase 2 item 4, per brief decision 6).**
   Forecast identity is `(competition, season, date, home, away, as_of,
   model_version, input_digest, config, forecast_version)` — the
   natural key is its first five components, so two distinct same-day
   matches between the same pair (a double-header) are
   **indistinguishable** in forecast identity exactly as in ingestion.
   Impossible in the synthetic fixtures by construction; documented
   here, not silently accepted — a real source exhibiting this would
   need a key extension (e.g. round or a source-unique id) in both
   places.

3. **Stored forecasts are in-sample estimates — nothing is validated
   (evidence begins at Phases 9/11).** A stored, hash-verified,
   perfectly immutable forecast is still an **in-sample point
   estimate** on synthetic fixtures: immutability, determinism, and
   tamper-evidence are provenance properties, not quality claims
   (`normalized ≠ accurate`). The API's `disclaimer` field states this
   on every body. Neither chronological backtesting (Phase 9) nor
   evaluation against realized results (Phase 11) has run; until they
   do, no forecast may be described — in code, docs, briefs, or
   reports — as validated, accurate, or beating anything
   (STATISTICAL-ASSUMPTIONS §6, §8g).

4. **Write-once is schema-level, not superuser-proof — the scope of
   the guarantee stated.** The forecasts table's `BEFORE UPDATE`/
   `BEFORE DELETE` triggers (RAISE ABORT inside the database file)
   stop every writer that goes through sqlite's normal write paths —
   app code, raw connections, the sqlite3 CLI — and the read path
   additionally recomputes the content hash on every row it returns.
   A **hostile superuser with `writable_schema` access can alter or
   drop the triggers inside the file itself** and is outside the
   trigger guarantee; read-time hash verification still catches any
   alteration of a covered field that gets past the triggers
   (STATISTICAL-ASSUMPTIONS §8d).

5. **The localhost/no-auth posture is a conjunction — each pillar is
   load-bearing.** The API binds `127.0.0.1` only (never `0.0.0.0`),
   serves only `GET` methods over an already-validated read-only store
   (`PRAGMA query_only` connections), and the system holds zero
   secrets — no keys, no user data, no betting surface. The absence of
   authentication is acceptable **only** given all three together; if
   any one ever falls (network bind, write methods, secrets),
   authentication becomes a Phase-10+ brief requirement, not an
   afterthought (brief decision 14).

6. **AMENDMENT A1 + A2 — the Phase 2 hygiene file grew 614 → 623
   (declared).** AMENDMENT A1 (pre-planned per P1) added exactly three
   `ALLOWED_APP_IMPORTS` entries (`"app.forecasts"`, `"app.storage"`,
   `"app.api"` — dictionary-coverage gaps the new packages would
   otherwise crash against with `KeyError`); AMENDMENT A2 relocated the
   Phase 2 `sqlite3`/`http` import bans into a package-scoped exception
   map, pinned **exactly** `{"app.storage": {"sqlite3"},
   "app.api": {"http"}}` — a Phase 2 check edited for the first time;
   the edit is a package-scoped exception with both-direction probes
   (criterion 25), not a weakening: no banned name was removed from
   `BANNED_TOP_LEVEL_IMPORTS`, and every other package keeps the full
   ban. Net growth A1 (+3) + A2 (+6) = **614 → 623 lines**, declared as
   one figure per A2 §1. Declared at checkpoint, review, and monitor
   sweep.

7. **AMENDMENT A3 — a Phase 4 pin updated 7 → 10 keys
   (`tests/test_phase4_separation.py`, 826 → 831 lines, declared).**
   A1-mandated growth collided with Phase 4's exact 7-key
   `ALLOWED_APP_IMPORTS` pin; the pin was updated to the exact 10-key
   universe (the seven legacy keys ∪ the three new), all pre-existing
   assertions retained verbatim — strictly stronger, none removed,
   relaxed, skipped, or xfailed. Architect-ratified after the builder
   self-declared it (2026-10-17); not standing precedent (each future
   collision needs its own named amendment).

8. **AMENDMENT A4 — one `Fixture` sample in the Phase 2 dataclass pin
   (`tests/test_domain.py`, +11 lines, purely additive, declared).**
   The new frozen `Fixture` (design decision 3, developer answer
   Q4 = a) required a sample in Phase 2's 1:1 completeness pin
   (`DATACLASS_SAMPLES`); the addition is the pin working as designed —
   the generic frozen/setattr/replace loop now also covers `Fixture`.
   Architect-ratified; nothing else in that file changed.

9. **AMENDMENT A5 — manual percent-decoder; the brief's
   `urllib.parse` mentions superseded (declared).** Path segments are
   decoded by a strict manual `decode_segment`
   (`app/api/server.py`): `urllib` stays on A2's ban in every package
   (its exception map is pinned exactly), and
   `urllib.parse.unquote` never raises on malformed escapes — it
   cannot deliver criterion 19's 400s. `decode_segment` raises
   `ValueError` on bad escapes and truncated UTF-8, mapped to 400 with
   the pinned `{"error": "bad_request"}` body. Architect-ratified
   (2026-10-17); percent-decoding of path segments is still mandated
   and delivered.

10. **Criterion-8 erratum — raw-write refusal is `IntegrityError`,
    brief text only (declared).** A trigger's `RAISE(ABORT, ...)`
    surfaces to Python as `sqlite3.IntegrityError` (verified on this
    platform, sqlite 3.45.1 / CPython 3.12.3, both UPDATE and DELETE),
    not the `OperationalError` the brief originally read;
    `tests/test_storage.py` already pinned the exact `IntegrityError`
    type plus both ABORT messages — erratum corrected brief text only,
    **no test text changed**. (Criterion 13's separate
    `OperationalError` — `PRAGMA query_only` — is a different mechanism
    and remains correct.) Architect-issued, 2026-10-17.

11. **No generation endpoint, no generation CLI — by design, not by
    omission.** The API serves **stored** snapshots only (`GET /health`
    and `GET /forecasts/{competition}/{season}/{date}/{home}/{away}`);
    non-GET methods answer 405 and `build_forecast` appears nowhere
    under `app/api` (AST-enforced). A compute-on-demand endpoint would
    mint **ephemeral** forecasts that never enter the write-once store
    and can therefore never be scored by Phase 11. If generation is
    ever exposed it must store-then-serve — a future brief's decision
    (brief out-of-scope list, open question 5 answered `a`).

12. **A kickoff time-of-day in a response body would trip criterion
    20's timestamp scan — dormant today, gated by amendment (reviewer
    adjudication, benign-dormant).** Criterion 20's body scan uses
    `\b\d{2}:\d{2}\b` among its timestamp-like patterns
    (`tests/test_api.py`); every fixture stored so far carries
    `kickoff` **MISSING** (`{"availability": "MISSING", "time": null}`),
    so no kickoff time-of-day ever appears in a body and the pattern is
    **dormant** with respect to kickoff values. Serving a supplied
    kickoff time is fixture-data echo, never fabrication (MISSING is
    never defaulted) — but storing any forecast whose `Fixture` carries
    a kickoff time would make the scan trip on legitimate data. Before
    that happens, that phase's brief must carry **its own named
    amendment** to criterion 20 (narrowing or exempting the kickoff
    value), never a silent scan weakening. Adjudicated benign-dormant
    by the Phase 5 reviewer (2026-10-17); declared here so the dormancy
    is visible, not accidental.

## Phase 6

1. **Measured xG availability is sparse; strict rolling-xG is not
   shipped; `xg_form` is a disclosed different estimator.** xG is
   present on exactly **10/60** fixture matches — season 2
   (`2025-26`) only, on 4 distinct dates — so every season-1 fixture
   reports xG features MISSING. A strict last-`FORM_WINDOW`-all-xG
   rolling window covers **0/120** team appearances on this data,
   which is why that feature is **not shipped** (it would be MISSING
   everywhere). The shipped `xg_form` under
   `XG_FORM_POLICY = "MEAN_OVER_AVAILABLE_WITH_N"` is a **different
   estimator-of-form** — the mean over the window's xG-available
   subset only, with `n_xg` disclosed — and is documented as such
   wherever it appears: a different quantity measured on fewer
   matches, never a substitute for a strict rolling-xG window; at
   `n_xg = 0` the field is MISSING, never `0.0` (no missing xG ever
   participates as an implicit zero). Independent census at the Phase
   6 docs step reproduced every figure (2026-10-19; also: 20/120
   appearances had xG on the immediately prior match — an upper bound
   on early-window xG usefulness)
   (STATISTICAL-ASSUMPTIONS §9c, §9d).

2. **Rest days are WITHIN_SEASON — season-opening appearances report
   MISSING, never the ~301-day off-season figure.**
   `REST_DAYS_POLICY = "WITHIN_SEASON"`: `rest_days` is the calendar
   days from the team's most recent **same-season** pre-cutoff match;
   with no same-season prior it is MISSING — measured **12/120**
   team appearances (the season-opening class). The cross-season
   alternative — reporting the ~301-day off-season gap as "rest" —
   is **rejected as a different quantity** and never reported
   (developer answer Q3 = a). **6/120** appearances have no prior
   match ever: form, rest, and xG are all MISSING there, never 0
   (STATISTICAL-ASSUMPTIONS §9c, §9d).

3. **Form-window policy leaves early-career form MISSING.**
   `FORM_WINDOW_POLICY = "MISSING_UNTIL_FULL_WINDOW"` with
   `FORM_WINDOW = 5`: a goals-form field is MISSING until the team
   has 5 strictly-pre-cutoff matches — measured **30/120** team
   appearances are affected (each team's first five career matches).
   This is the named policy, not an accident: never a partial-window
   mean; `prior_matches` discloses the true count beside the MISSING
   estimate (developer answers Q1 = a, Q5 = a)
   (STATISTICAL-ASSUMPTIONS §9c, §9d).

4. **The window scope is competition- and season-agnostic — a
   documented v1 limitation.** The form/rest/xG window counts **all**
   of the team's prior matches regardless of competition or season
   (one simple scope, developer answer Q6 = a). Today's fixtures are
   single-competition, so nothing blends in practice — but a
   mixed-competition or multi-season history would blend form across
   competitions and seasons with no separation knob. Stated, not
   silently accepted (STATISTICAL-ASSUMPTIONS §9c).

5. **Day-granularity arithmetic; kickoff echoed, never consumed, and
   not stored.** `rest_days` is an integer calendar-day difference
   (fixture date minus prior-match date); the system has day
   granularity and no within-day ordering discipline (Phase 5 item 1),
   so no intra-day ordering exists anywhere in features. The fixture's
   `kickoff` availability is echoed on the vector for honesty —
   measured **30/60** matches carry kickoff (all season 1), MISSING
   never defaulted to a fabricated time — but the computation reads
   dates only: consuming `HH:MM` would claim precision the domain
   does not have. The echo is computed in memory and **stored
   nowhere**, so Phase 5 item 12's kickoff-vs-criterion-20 gate is
   **not** triggered (STATISTICAL-ASSUMPTIONS §9b, §9d).

6. **Feature identity inherits the double-header natural-key
   limitation (carried from Phase 2 item 4 and Phase 5 item 2).**
   `FeatureVector` identity starts with the same natural key
   (competition, season, date, home, away), so two distinct same-day
   matches between the same pair (a double-header) are
   **indistinguishable** in feature identity exactly as in ingestion
   and forecast identity. Impossible in the synthetic fixtures by
   construction; documented here, not silently accepted — a real
   source exhibiting this would need a key extension (e.g. round or a
   source-unique id) in all places.

7. **Features are descriptive summaries with zero predictive claim —
   and are consumed by nothing.** Every field of a `FeatureVector` is
   a historical summary of past matches: **not a probability, not a
   model output, not evidence** of anything predictive. No file under
   any other `app/` package imports `app/features` (AST-enforced both
   directions — criterion 17), so nothing in the system can currently
   emit a feature as a probability; `build_forecast`, storage, API,
   scenarios, and simulation are untouched, no `FORECAST_VERSION`
   changed, and no Phase 5 golden moved. The first consumer arrives
   via its own future brief with its own version/identity
   implications. Until Phases 9/11, no feature may be described as
   validated, accurate, or evidence of predictive value
   (STATISTICAL-ASSUMPTIONS §9f, §9g).

8. **Stage 4 exists while stage 3 (`app/state/`) does not — roadmap
   order, deliberately.** `app/features/` is instantiated (Phase 6)
   while `app/state/` (PRE-MATCH STATE) remains unbuilt per roadmap
   order; features compute directly from match history plus domain
   types, and **no dependency on stage 3 was invented** to paper over
   the order (brief F4; brief risk "Stage-order confusion" —
   ARCHITECTURE and this entry state it plainly).

9. **The synthetic-data caveat rides every feature.** Every feature is
   a historical summary of the fictional "Obsidian Coast League"
   (6 teams, 60 hand-authored matches) — synthetic history, never
   evidence; a feature computed on real data is untested territory
   end to end, exactly as the model layer is (Phase 3 item 6,
   compounded by the Phase 2 loader limitation).

10. **Declared amendments A1/A2/A3 — exact figures (brief
    pre-sanctioned; declared at checkpoint, review, and monitor
    sweep).** **A1**: `tests/test_fixtures_and_hygiene.py` **623 →
    624** — exactly one new `ALLOWED_APP_IMPORTS` entry
    `{"app.features": {"app.domain", "app.features"}}`
    (dictionary-coverage gap the new package would otherwise crash
    against with `KeyError`) **plus** a line-neutral,
    strictly-stronger `PURE_PACKAGES` edit to `{"app.domain",
    "app.validation", "app.features"}` (newly bans `os`/`sys`/
    `pathlib`/`io` in the package — the strength that makes criterion
    18's `os` probe fire); net +1 line only. **A2**:
    `tests/test_phase4_separation.py` key-set pin 10 → 11 keys, **831
    → 832**. **A3**: `tests/test_phase5_separation.py` criterion-25
    key-set pin 10 → 11 keys, **571 → 572**. A2/A3 are the same
    mechanical pin-collision class as Phases 3–5; every legacy
    assertion retained in all three files (strictly stronger, never a
    weakening).

11. **Offline-check protocol — plain `unshare -rn` produces 6 API
    failures that are a harness artifact, not a bug (tester note,
    disposition recorded).** Under a fresh network namespace the
    loopback interface starts DOWN, so plain
    `unshare -rn env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q`
    reports `6 failed, 97 passed` — all six failures in
    `tests/test_api.py` (`OSError` binding 127.0.0.1). The working
    offline form brings loopback up first:
    `unshare -rn bash -c 'ip link set lo up && env -u PYTEST_ADDOPTS
    .venv/bin/python -m pytest -q'` → **103 passed** (both forms run
    and recorded at the Phase 6 docs step, 2026-10-19). Recorded here
    so future sweeps never misread the plain-form failures as a
    product defect — the API binds localhost by design (Phase 5 item
    5); the product is unchanged.

12. **Criterion-6 comment nit — recorded, deliberately not patched on
    a reviewed-and-frozen test file (tester note, disposition
    recorded).** In `tests/test_features.py`, the hand-built same-date
    tie-break history comment says *"a mean including it would be
    2.6"* — arithmetically wrong: the correct hypothetical is (9+1+2+
    0+1+4)/6 = **17/6 ≈ 2.833**. Comment-only: the asserted value
    (8/5 = 1.6) and every assertion are unaffected (reviewer
    adjudicated the same way). Deliberately **not** patched — the
    reviewed test file is frozen for this phase (an edit after
    review would change the reviewed artifact); a future brief that
    touches the file may correct the comment.

## Phase 7

1. **Decision reports are in-process, ephemeral VIEWS — not stored,
   not served, re-derivable from frozen forecasts.**
   `build_decision_report(forecast, *, scenarios=())` renders a frozen
   `Forecast` in process: no sqlite table, no `SCHEMA_VERSION` bump
   (still exactly 1), no API route, no CLI — and nothing outside
   `app/decisions/` imports the package (AST-enforced both directions,
   criterion 15). Reports are deterministic re-derivable **views**, so
   ephemerality breaks nothing: Phases 9/11 evaluation joins on
   **forecasts** (frozen, write-once, hashed, pinned — that substrate
   is already complete), not on reports. Persistence or serving arrives
   only via a future brief with developer instruction — if ever
   (A5/A8; STATISTICAL-ASSUMPTIONS §10a).

2. **Evaluated n = 0: zero scoring metrics ship with this phase —
   the boundary vs Phases 9/11.** No log loss, no Brier, no RPS, no
   hit rate, no calibration, no baselines; the evaluated observation
   count in any report is exactly 0. An AST/token guard over the source
   of every file under `app/decisions/**` asserts the **absence** of
   scoring vocabulary (criterion 13, extend-not-weaken — future scoring
   terms join that guard's tuple, never leave it). A report measures
   nothing; evidence begins at Phases 9 (backtesting vs baselines) and
   11 (evaluation vs realized results). The evaluation substrate was
   already complete and Phase 7 added nothing it needs — stated to kill
   the temptation to pre-score (A1/A3/A8; §10e).

3. **No thresholds, no decision rules — a position, not a default
   (A6).** `app/decisions/constants.py` defines **exactly**
   `REPORT_VERSION` and `DISCLAIMER`, pinned by test (criterion 1): no
   "flag when P(home)>X", no tuned numeric knob, and no rule converting
   a probability into a decision exists anywhere in the package.
   Thresholds would be arbitrary at best, and choosing one by fitting
   on outcomes would leak directly into Phase 10's protected
   improvement loop — one step from the banned value-detection framing
   (§10c).

4. **Anti-ensemble: min/max spread only — never a mean — and no
   second independent model exists.** The ONLY cross-scenario
   aggregation shipped is per-outcome `minimum`/`maximum`/`spread`
   over the labeled comparisons; no field or canonical-payload key is
   named mean/average/ensemble/aggregate/blend/composite, and the
   arithmetic-mean triple is pinned **absent** by test (criterion 9).
   **No second independent model exists in this system** — one Poisson
   fit per forecast, no Elo, no second forecast source — so no
   cross-model agreement, no ensemble, and no agreement metric is ever
   presented; the IX-7 failure mode is answered head-on in the fixed
   disclaimer, not silenced (§10b).

5. **Scenario comparisons are LABELED HYPOTHETICS, not forecasts.**
   Each comparison entry echoes its `label` and `transforms` verbatim,
   must be built from **the forecast's own `FittedParams`** (a
   mismatched baseline and duplicate labels are refused with
   `ValueError`, mirroring Phase 4's guard), and carries analytic
   `outcome_probs` deltas — descriptive arithmetic between a
   hypothetical and its own baseline, never "value". The
   `MULTIPLIER_MIN = 0.5`/`MULTIPLIER_MAX = 2.0` knobs are inherited
   unchanged from Phase 4's arbitrary documented bounds (Phase 4 item
   3) — every scenario number stays a labeled hypothetical all the way
   down.

6. **Flag-vs-plausible-number tension is presented structurally,
   never judged.** Top-level `convergence_status`/`insufficient_data`/
   `insufficient_teams`/`dropped_mass` flags sit beside plausible-
   looking normalized probabilities — both visible, neither hidden —
   and **no threshold judges the tension** (item 3's position).
   Uncertainty is flag echo only: no confidence-interval, standard-
   error, interval, or numeric reliability-band field exists anywhere
   on a report, and `mc_stderr` (simulation noise only, Phase 4 item
   1) can never enter a report — scenario comparisons are analytic
   only, never Monte Carlo frequencies (criterion 12; §10d).

7. **The disclaimer's wording is fixed and pinned by test — any
   wording change is a contract bump.** `disclaimer ==
   constants.DISCLAIMER` exactly, with its pinned substrings (in-sample
   estimates, synthetic-data caveat, pending Phases 9/11, not-evidence-
   of-accuracy, the no-second-independent-model /
   never-averaged-or-ensembled clause — criterion 5). Changing the
   wording changes every report's hashed content and therefore
   requires a `REPORT_VERSION` bump plus re-derivation of the
   version-local golden hash — **never widened** (§10a bump
   discipline).

8. **The synthetic-data caveat and in-sample status ride every
   report.** Every number is an in-sample point estimate on the
   fictional "Obsidian Coast League" fixtures, copied at full precision
   from a frozen forecast or a labeled hypothetical — **rendering adds
   no evidence of any kind** (§9g's "historical summaries … not
   evidence" continuity). Until Phases 9/11, no report may be
   described — in code, docs, briefs, or report contents — as
   validated, accurate, or beating anything; those words are banned in
   `app/decisions/**` by test (criterion 14; §10f).

9. **Probabilities are estimate properties — no pick-shaped field
   exists.** Field order shows home, draw, away and nothing derives a
   favored side: no argmax, no "most likely", no pick-shaped field is
   present or derivable from the pinned 28-field contract (criterion 2)
   under the vocabulary bans (criterion 14). No odds, stakes, EV,
   Kelly, edge, or value framing exists anywhere — constitution
   prohibition 3 stands.

10. **Declared amendments A1/A2/A3/A4 — exact figures (brief
    pre-sanctioned; declared at checkpoint, review, and monitor
    sweep).** **A1**: `tests/test_fixtures_and_hygiene.py` **624 →
    625** — exactly one new `ALLOWED_APP_IMPORTS` entry
    `{"app.decisions": {"app.domain", "app.models", "app.forecasts",
    "app.scenarios", "app.decisions"}}` (dictionary-coverage gap the
    new package would otherwise crash against with `KeyError`) **plus**
    a line-neutral, strictly-stronger `PURE_PACKAGES` edit to the
    four-set `{"app.domain", "app.validation", "app.features",
    "app.decisions"}` (newly bans `os`/`sys`/`pathlib`/`io` in
    `app/decisions` — the strength that makes criterion 15's probes
    fire); net +1 line only. **A2**: `tests/test_phase4_separation.py`
    key-set pin 11 → 12, **832 → 833**. **A3**:
    `tests/test_phase5_separation.py` criterion-25 key-set pin 11 →
    12, **572 → 573**. **A4**: `tests/test_phase6_separation.py`
    pins updated **in place, line-neutral** — the 12-key union gains
    `app.decisions`, `PURE_PACKAGES` pinned to the four-set, the
    source-string pins now read `== 12` and are strengthened to exclude
    **both** `== 10` and `== 11` — **510 → 510**. All four verified by
    `wc -l` this docs step; every legacy assertion retained in all four
    files (strictly stronger, never a weakening; A4's three-generation
    source-string collision is the same mechanical class ratified at
    Phases 3–6).

11. **The scoring guard is `\b` word-boundary — suffixed identifiers
    would evade it (tester note, disposition recorded).** Criterion
    13's token guard compiles `\b(log_loss|logloss|brier|rps|
    hit_rate|calibration)\b` (case-insensitive) over `app/decisions/**`
    source, so a scoring-shaped identifier that **extends** a pinned
    token with a word character (e.g. a `brier_score`-shaped name)
    does not match the guard. **Spec-conformant today**: a raw-
    substring scan of `app/decisions/**` is clean for every pinned
    token (docs-step verified, 2026-10-19) — nothing ships evading
    detection in fact. Disposition: recorded, not patched — when
    scoring vocabulary legitimately ships at Phases 9/11 the guard's
    tuple must be **extended** (extend-not-weaken, criterion 13's
    superset pin), and that extension should consider suffixed forms;
    the guard is never weakened.

12. **The A2/A3 comment-text amendment numbers collide with earlier
    phases' identically-numbered amendments — phase-scoped by
    convention, comment-only (tester/reviewer note, disposition
    recorded).** The amendment-declaring comments inside
    `tests/test_phase4_separation.py` (A2) and
    `tests/test_phase5_separation.py` (A3) reuse numbers that earlier
    phases also used (Phase 5's A3/A4/A5, Phase 6's A2/A3) —
    amendment numbers are scoped to their own phase's brief by
    convention, exactly as Phase 6's A2/A3 shadowed Phase 5's. The
    edits are comment text plus the pinned key counts; **no assertion
    is affected** (both files execute green in the same 120-test
    suite).

13. **The build was interrupted mid-phase and completed in a second
    session; the reviewer audited the test-file compaction — no probe
    lost (process record).** The first build session was interrupted
    by a server restart mid-work; a second session completed the phase.
    To stay within the ~440-line per-file budget, the three new test
    files were compacted to **440 lines each by comment/docstring
    condensation only**; the reviewer audited the compaction against
    the brief's criteria 1–17 mapping and confirmed **no probe was
    dropped** — catching and restoring two accidental deletions in the
    process. Zero self-declared deviations remained after the resume
    (A1–A4 exactly as pre-sanctioned). Recorded per the constitution:
    recorded events, not assumed ones.

## Not yet applicable (as of Phase 7)

Forecast, storage, API, feature, and decision-report limitations are
now listable and listed above (pipeline stage 6 FORECAST DISTRIBUTIONS,
its durable write-once sqlite store, the read-only serving surface,
pipeline stage 4 FEATURE EXTRACTION — `app/features/` — and pipeline
stage 8 DECISION ANALYSIS — `app/decisions/` — all exist; decision
reports became listable at Phase 7). Still not yet listable: pre-match-
state, backtesting, evaluation, and model-improvement limitations —
pipeline stages 3, 9, 10 are unbuilt; there are no pre-match snapshots,
and no evaluation metrics to mis-trust yet (Phase 7 ships zero scoring
— evaluated n = 0). Model-calibration and predictive limitations (as
distinct from the in-sample assumptions above) arrive with Phases 9 and
11 and will be documented in `docs/EVALUATION.md` (which does not exist
yet — there is no evaluation to document) and in this file. Data
provenance and format limitations remain in `docs/DATA-SOURCES.md`; the
model's statistical assumptions and their weaknesses are in
`docs/STATISTICAL-ASSUMPTIONS.md` (exists since Phase 3; §7 covers
simulation and scenarios; §8 covers forecasts, storage, and serving;
§9 covers feature extraction, added at Phase 6; §10 covers decision
analysis, added at Phase 7).
