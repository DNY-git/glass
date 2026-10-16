# KNOWN LIMITATIONS — SPORTS LOOKING GLASS

The honest list. Updated every phase (constitution; HANDOFF Part IX item
13 formalizes this at Phase 13, but the discipline starts now). Nothing
here is hidden behavior — each item is also recorded where it was found.

Entry below reflects the state as of Phase 2 (Domain and data),
2026-10-16.

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

## Not yet applicable

Model-calibration, leakage, and statistical limitations are not yet
listable: as of Phase 2 the repository contains data but **no
calculations, no models, and no statistics** — pipeline stages 3–10 are
unbuilt. Data provenance and format limitations are documented in
`docs/DATA-SOURCES.md`; statistical assumptions and evaluation
limitations will be documented in `docs/STATISTICAL-ASSUMPTIONS.md` and
`docs/EVALUATION.md` when those subjects first exist.
