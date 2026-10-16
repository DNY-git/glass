# KNOWN LIMITATIONS — SPORTS LOOKING GLASS

The honest list. Updated every phase (constitution; HANDOFF Part IX item
13 formalizes this at Phase 13, but the discipline starts now). Nothing
here is hidden behavior — each item is also recorded where it was found.

Entry below reflects the state as of Phase 1 (Foundation), 2026-10-16.

## Phase 1

1. **`scripts/health-check.sh` intentionally exits 0 on failed inner
   checks** (tester finding G2). The script uses `set -u` only, so a
   failing check prints its failure but cannot abort the sweep — by
   design, for monitoring continuity. Consequence: the script's exit code
   is not a pass/fail gate. The gate is a **direct** suite run
   (`.venv/bin/python -m pytest -q`) — Phase 1 acceptance criterion 10,
   verified by recorded direct runs from tester, reviewer, and monitor.
   Always read the script's output; never rely on its exit code alone.

2. **The health-script test consumes most of its timeout budget** (tester
   finding G4). `tests/test_health_script.py` shares one module-scoped
   `bash scripts/health-check.sh` run under a 120 s timeout; observed
   runtime is roughly 85 s of that margin (the script runs the suite five
   times internally). A slower machine or a growing suite can push it
   over. If it trips, the responsible phase's brief must **re-scope the
   mechanism** — never weaken, skip, or xfail the test (constitution).

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
   suite (9 tests, ~23–50 s) is slow relative to what it tests because
   criteria 7–9 spawn the health script, which internally runs the suite
   several times — an accepted ~6x suite cost while the health test
   exists (brief risk register). Harmless at Phase 1 scale; if it becomes
   a bottleneck, a later brief must re-scope it — never weaken the test.

## Not yet applicable

There are no data-quality, model-calibration, leakage, or statistical
limitations to list: as of Phase 1 the repository contains no data, no
calculations, and no statistics — only the engine root package, the test
loop, and the health script. Data provenance, statistical assumptions,
and evaluation limitations will be documented in `docs/DATA-SOURCES.md`,
`docs/STATISTICAL-ASSUMPTIONS.md`, and `docs/EVALUATION.md` when those
subjects first exist.
