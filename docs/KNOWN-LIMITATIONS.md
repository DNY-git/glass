# KNOWN LIMITATIONS — SPORTS LOOKING GLASS

The honest list. Updated every phase (constitution; HANDOFF Part IX item
13 formalizes this at Phase 13, but the discipline starts now). Nothing
here is hidden behavior — each item is also recorded where it was found.

Entry below reflects the state as of Phase 4 (Simulation and
scenarios), 2026-10-17.

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

## Not yet applicable (as of Phase 4)

Scenarios and simulation limitations are now listable and listed above
(pipeline stage 7 and the cross-cutting Monte Carlo module exist).
Still not yet listable: forecast, decision, and API limitations —
pipeline stages 3–4, 6, 8–10 are unbuilt; there are no pre-match
snapshots, no features, no forecasts, no decision reports, and no
evaluation metrics to mis-trust yet. Model-calibration and predictive
limitations (as distinct from the in-sample assumptions above) arrive
with Phases 9 and 11 and will be documented in `docs/EVALUATION.md`
(which does not exist yet — there is no evaluation to document) and in
this file. Data provenance and format limitations remain in
`docs/DATA-SOURCES.md`; the model's statistical assumptions and their
weaknesses are in `docs/STATISTICAL-ASSUMPTIONS.md` (exists since
Phase 3; §7 covers simulation and scenarios).
