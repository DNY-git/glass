# PHASE 3 BRIEF — CORE STATISTICS

Status: proposed (2026-10-16, glass-architect). Per docs/ROADMAP.md this
is Block 1, Phase 3 — the block's final phase; developer acceptance
occurs once, at the block boundary, after Phase 3 passes review, is
committed, and passes the monitor sweep. glass-quant **was consulted**
for this brief; its rulings are treated as binding design constraints
and are cited inline as (B1), (G1), etc.

## Objective

Deliver pipeline stage 5 (STATISTICAL MODELS) per HANDOFF Part IX item
3: a Poisson goal model with attack/defence strengths and an **estimated**
home-advantage term, fitted by unpenalized maximum likelihood inside a
pure, stdlib-only `app/models/` package — so every later phase can fit
on strictly pre-cutoff history and evaluate scoreline/outcome
distributions without ever seeing the future. Home advantage is a fitted
parameter whose estimation is documented (reconciling the handoff's
"documented constants" with quant ruling B3: nothing about `h` is
hardcoded). Seeded RNG discipline is **not** built this phase: quant's
explicit no-objection confines all randomness to Phase 4; Phase 3 is
entirely deterministic estimation. Per F2: every number produced here is
an in-sample estimate, quotable only as an estimate — never as evidence
of accuracy.

## State verified before writing this brief (probed 2026-10-16)

- HEAD = `1c5067b` ("phase 2: domain models, OpenFootball ingestion,
  validation, synthetic fixtures"); `45ed27e` before it. Phase 1 and 2
  reviewer verdicts PASS; both monitor sweeps verdict **WARN**, finding 1
  carried in both: three protocol docs (`docs/HEALTH-LOG.md`,
  `docs/PROGRESS-LOG.md`, `docs/ROADMAP.md`) sit uncommitted — confirmed
  still the **only** dirty paths; they must ride Phase 3's checkpoint
  commit. Monitor finding 2 (611-line `tests/test_fixtures_and_hygiene.py`)
  is a carried observation — this brief avoids growing that file (design
  decision 8).
- Suite: `.venv/bin/python -m pytest -q` → 24 passed, 0 failed, 0
  skipped, 0 xfailed. Python 3.12.3, pytest 9.1.1, stdlib-only.
- Fixtures: 60 valid matches (2 seasons × 30), 6 fictional teams, integer
  scorelines; **measured this probe: 156 total goals, exactly 20 matches
  per team** (informed the thresholds in open question 2); xG on 10/60,
  kickoff on 30/60 — both out of scope this phase (quant G2).
- `app/models/` does not exist; `docs/STATISTICAL-ASSUMPTIONS.md` does
  not exist (ARCHITECTURE.md explicitly says it "arrives with the phases
  that introduce them" — this is that phase); KNOWN-LIMITATIONS still
  carries "Not yet applicable: no calculations, no models, no
  statistics" — stale as of this phase's DOCS step.
- glass-quant consulted for statistical design (mandatory from Phase 3).
  Rulings below are constraints, not suggestions.

## Design decisions (this brief resolves them)

1. **Model form (B1).** Log-linear Poisson:
   `λ_home = exp(μ + α_home + β_away + h)`,
   `λ_away = exp(μ + α_away + β_home)`.
   Sum-to-zero identifiability on α and β (team means absorbed into μ);
   single shared home-advantage log-term `h`. Home and away goals of each
   match are independent Poisson draws given the parameters.
2. **Estimator (B2): Newton-Raphson is mandated.** Concave log-likelihood
   with analytic derivatives (score + observed information) and a
   hand-rolled dense linear solve (stdlib Gaussian elimination with
   partial pivoting; systems are ≤12×12 at fixture scale). Quant tested
   naive fixed-point/IPF: it demonstrably diverges (±150 in 200
   iterations), so it is **not** acceptable this phase; if a future brief
   ever reconsiders, it must carry damping + tol + cap, all documented.
   Three named, documented, provenance-echoed constants:
   `NEWTON_TOL` (recommended 1e-10), `MAX_ITERATIONS` (recommended 100),
   `DAMPING` (recommended 1.0 — full Newton step; builder documents the
   exact step/backtracking rule it implements in
   `docs/STATISTICAL-ASSUMPTIONS.md`).
3. **Fitter API (G1).** The entry point is
   `fit(matches, as_of, *, config=None) -> FittedParams`. History
   filtering happens **inside** `fit`: only matches with `date < as_of`
   (strictly before the cutoff; matches dated **at** the cutoff are
   refused) enter the likelihood. No module-level fitted singleton, no
   cache, no memoization — parameters are a pure function of arguments.
4. **Fit scope (C1/C3).** Default scope is **both seasons pooled**
   (competition `Obsidian Coast League`, seasons `2024-25` + `2025-26`),
   with stationarity across pooled seasons documented as an assumption.
   Every fit records the pooling it consumed: competition, seasons, the
   `as_of` cutoff, and the pre-cutoff sample sizes.
5. **FittedParams (D2).** Frozen dataclass carrying: `model_version`
   (string constant, `"poisson-mle-v1"`), `config` echo (pooled seasons,
   `NEWTON_TOL`, `MAX_ITERATIONS`, `DAMPING`, `MAX_GOALS`, `ridge`),
   `input_digest` (sha256 of `canonical_state()` — the Phase 2 canonical
   serialization — of the pre-cutoff match set, UTF-8 encoded;
   provenance discipline reused, no timestamps/paths), fitted floats
   (`mu`, `home_advantage`, `alpha`/`beta` aligned to a sorted-team
   `teams` tuple), `iterations`, `convergence_status`, `sample_size`
   (matches used + goals observed), `insufficient_data` flag with
   per-team insufficient flags, and the pooling record (decision 4).
6. **Convergence (B2/D2).** `convergence_status` is a required field on
   every returned object: `CONVERGED` or a named non-converged status
   (e.g. `MAX_ITERATIONS`). A non-converged fit is a **reported result** —
   the flag rides on the object and in its provenance representation; a
   parameter vector is never emitted without its status. `FitConfig` is
   accepted as an optional keyword so tests can force the cap (decision 2
   constants remain the documented defaults, echoed per fit).
7. **Estimation is deterministic (D1).** No randomness anywhere in
   `app/models` — the AST criterion bans `random` there. Parameters are
   ordered by sorted team names; match iteration is Phase 2 canonical
   order; shuffled input yields bit-identical output. Seeded RNG enters
   in Phase 4.
8. **Unpenalized MLE (C2).** Ridge/shrinkage ships as an explicit
   config field defaulting to `None` (unpenalized). No silent shrinkage,
   ever; if a future phase opts in, the value is echoed in provenance.
9. **Scoreline matrix (E1).** Analytic product-of-Poissons:
   `log P(i,j) = i·ln λ_h − λ_h − ln(i!) + j·ln λ_a − λ_a − ln(j!)`
   for `i,j ∈ 0..MAX_GOALS`. `MAX_GOALS` (recommended 10; open question 1)
   is a documented constant paired with a documented λ bound: at
   fixture-fitted lambdas K=10 drops ≤ 6×10⁻⁴ joint mass (K=15:
   ≤ 1.2×10⁻⁷). The matrix **reports** its dropped mass
   (`1 − F_pois(K;λ_h)·F_pois(K;λ_a)`); W/D/L are computed from
   **analytic Poisson tails**, not from truncated cell sums, so outcome
   probabilities are exact under any truncation; `pH+pD+pA = 1` within
   documented `PROB_SUM_EPSILON` (1e-12). Golden tests assert full
   precision.
10. **Pure evaluator API (F1).**
    `scoreline_log_probs(fitted, home, away) -> ScorelineMatrix` (frozen:
    log-probability cells to full precision, `lambda_home`,
    `lambda_away`, `max_goals`, `dropped_mass`);
    `outcome_probs(matrix) -> (p_home, p_draw, p_away)` in **H > D > A**
    order, derived from the matrix's analytic tails. Log-probabilities
    are exposed because Phase 11's hand-computed goldens need them.
    **No cutoff logic, no `as_of`, no history access inside the pure
    evaluators** — cutoff discipline lives in `fit` alone this phase.
11. **Insufficient data (C1).** Named, documented thresholds (open
    question 2; recommended `MIN_MATCHES_PER_TEAM=10`,
    `MIN_TOTAL_MATCHES=20`, `MIN_TOTAL_GOALS=60` — fixture reality 20
    matches/team, 156 goals passes; a first-matchday cutoff fails).
    `sample_size` + `insufficient_data` attach to every fitted output;
    teams below the per-team threshold carry per-team flags.
12. **Why nothing more complicated ships (A2).** At fixture scale this
    is **120 goal observations for 12 parameters** (μ, h, 5 free α, 5
    free β). Nothing beyond the baseline Poisson is justified: evaluation
    noise of roughly ±0.05 log loss swamps any plausible gain from
    fancier structures, and PLAN §8 postpones advanced model families
    until the baseline has been chronologically backtested and evaluated
    (Phases 9 and 11). Dixon-Coles, time decay, form, player effects,
    overdispersion corrections are explicitly deferred, not forgotten.

## Files and directories to create or modify

BUILD step (indicative names; builder may split/merge sensibly):

- `app/models/__init__.py` — package docstring, public exports only.
- `app/models/constants.py` (or constants grouped in params) —
  `MODEL_VERSION`, `NEWTON_TOL`, `MAX_ITERATIONS`, `DAMPING`,
  `MAX_GOALS`, `PROB_SUM_EPSILON`, `SUM_TO_ZERO_EPSILON` (recommended
  1e-6), `MIN_MATCHES_PER_TEAM`, `MIN_TOTAL_MATCHES`, `MIN_TOTAL_GOALS` —
  each with a docstring saying why it exists and what it bounds.
- `app/models/params.py` — frozen `FittedParams`, `FitConfig`,
  convergence-status enum, pooling record, sample-size/insufficient
  structures (decision 5).
- `app/models/poisson.py` — `fit(matches, as_of, *, config=None)`,
  log-likelihood, analytic score/Hessian, Newton loop, hand-rolled dense
  solve, sum-to-zero maintenance (decision 1/2/3). Imports: stdlib +
  `app.domain` only.
- `app/models/scoreline.py` — `scoreline_log_probs`,
  `outcome_probs`, frozen `ScorelineMatrix` (decision 9/10).
- `tests/test_poisson_fit.py` — criteria 1–8.
- `tests/test_scoreline_matrix.py` — criteria 9–12.
- `tests/test_model_separation.py` — criterion 13 (a **new** file; the
  611-line hygiene file is not grown — monitor finding 2).

DOCS step (`docs/STATISTICAL-ASSUMPTIONS.md` is authored **before any
BUILD code**, per quant A1; the rest at phase end, reviewer-verified as
usual):

- `docs/STATISTICAL-ASSUMPTIONS.md` (**new**) stating, before code:
  home/away goals independent conditional on the parameters;
  var = mean Poisson (overdispersion ignored, checked in Phase 11);
  single shared home-advantage log-term, `h` estimated by MLE not
  hardcoded; no form / time-decay / Dixon-Coles / player effects;
  stationarity across pooled seasons; **draw-bias caveat (E2)** —
  independent Poissons characteristically under-represent draws;
  in-sample fits are estimates, never evidence of accuracy (F2);
  the estimator's named constants (tol/cap/damping, K, thresholds) with
  their bounds; the truncation bound at fixture lambdas; the
  baseline-only rationale (decision 12).
- `docs/KNOWN-LIMITATIONS.md` — retire the "Not yet applicable"
  section's claim that no statistics exist; add Phase 3 limitations
  (in-sample only, overdispersion ignored, draw bias, truncation bound,
  stationarity assumption, synthetic-data fits).
- `docs/ARCHITECTURE.md` — `app/models/` exists (stage 5); update the
  instantiation/status tables and the
  "`docs/STATISTICAL-ASSUMPTIONS.md` … do not exist yet" line.
- `README.md` — current state: Phase 3, real test count, checkpoint hash.
- `docs/ROADMAP.md`, `docs/PROGRESS-LOG.md` — standard end-of-phase
  updates; the three currently uncommitted protocol docs (HEALTH-LOG,
  PROGRESS-LOG, ROADMAP — monitor-carried finding 1) **must be included
  in the Phase 3 checkpoint commit**.
- `docs/DATA-SOURCES.md` — no change (no new data sources this phase).

Do not create or modify: `scripts/health-check.sh`, `pytest.ini`,
`conftest.py`, `tests/test_fixtures_and_hygiene.py`, `app/storage/`,
`data/`, any `app/` subpackage other than `models`, requirements/
pyproject, CI, linters, Docker.

## Dependencies

- **None new.** stdlib only: `math` (exp, log, lgamma/log-factorials),
  `dataclasses`/`typing`/`enum` (models), `hashlib` (input digest),
  `ast` (separation test). pytest — already installed; justification
  unchanged. Explicitly refused: numpy/scipy/pandas and any numeric
  stack (PLAN §3; a hand-rolled 12×12 solve suffices), any optimizer
  library, any RNG use this phase.

## Acceptance criteria

Criteria 1–13 map 1:1 to pytest test functions; criterion 14 is the
suite-level gate verified by recorded executions (tester, reviewer ×2,
monitor), exactly as in Phases 1–2. No test may use skip or xfail.

1. `tests/test_poisson_fit.py::test_fit_filters_history_internal_to_cutoff` —
   `fit` receives the **unfiltered** 60-match list with an `as_of` inside
   the history; the returned `sample_size` equals the count of matches
   with `date < as_of` computed independently in the test; a match dated
   **exactly at** `as_of` and one dated after are both refused (not
   counted, not fitted) — cutoff enforced inside the calculation, not at
   the call site.
2. `tests/test_poisson_fit.py::test_poisoned_future_match_cannot_alter_parameters` —
   fit A = `fit(matches_60, as_of=D)`; fit B =
   `fit(matches_60 + poisoned, as_of=D)` where `poisoned` contains
   extreme future scorelines dated at and after D (e.g. a 20-0). A and B
   are **field-for-field identical** — frozen-dataclass equality, equal
   `input_digest`, equal `iterations`, equal `repr` — proving an injected
   future match cannot alter parameters for an earlier `as_of` (G1).
3. `tests/test_poisson_fit.py::test_fit_deterministic_replay_and_order_insensitive` —
   the same fit run twice in one process is identical at full float
   precision across every field including `input_digest`; a shuffled copy
   of the same input matches a canonical-order fit bit-for-bit
   (parameters ordered by sorted team names; iteration in Phase 2
   canonical order; no randomness — D1).
4. `tests/test_poisson_fit.py::test_convergence_status_is_reported_never_silent` —
   default full-fixture fit returns `convergence_status == CONVERGED`
   with `iterations >= 1`; the same fit with the iteration cap forced to
   1 via `FitConfig` (cap echoed in the config) returns a **non-converged
   status on the object and in its provenance representation** — no
   parameter vector is ever returned without a status (B2/D2); every
   `FittedParams` (either status) carries all required provenance fields
   (criterion 8) so the flag can never be lost downstream.
5. `tests/test_poisson_fit.py::test_insufficient_data_flags_and_sample_size` —
   full-pool fit: `sample_size` equals (60 matches, 156 goals),
   `insufficient_data` false, no per-team insufficient flags; an
   early-cutoff fit (as_of yielding well under `MIN_TOTAL_MATCHES`
   pre-cutoff matches, e.g. first matchday): `insufficient_data` true,
   `sample_size` below the documented thresholds, and every team under
   `MIN_MATCHES_PER_TEAM` pre-cutoff matches flagged per-team —
   thresholds are named documented constants and the flags are attached
   to the fitted output, not hidden (C1).
6. `tests/test_poisson_fit.py::test_home_advantage_is_estimated_not_hardcoded` —
   `home_advantage` is a fitted float on `FittedParams`, echoed in
   provenance as estimated (config records estimation, not a constant);
   `h` from the full fit differs from `h` from the early-cutoff fit —
   data-dependent, therefore fitted, not hardcoded (B3).
7. `tests/test_poisson_fit.py::test_model_form_sum_to_zero_and_pooling_record` —
   reconstructing λ via the log-linear formula from
   (μ, α, β, h) reproduces the evaluator's λs (decision 1); sum(α) and
   sum(β) are each within documented `SUM_TO_ZERO_EPSILON` of 0; the
   `teams` tuple is sorted with α/β aligned to it; the pooling record
   names competition, both seasons, and the consumed `as_of` cutoff
   (B1, C3, D1).
8. `tests/test_poisson_fit.py::test_fitted_params_frozen_provenance_and_digest` —
   `FittedParams` is frozen (assignment raises `AttributeError`);
   `model_version == "poisson-mle-v1"`; config echo contains pooled
   seasons, tol, cap, damping, `MAX_GOALS`, and `ridge=None`
   (unpenalized, C2); `input_digest` equals an independently recomputed
   sha256 of the pre-cutoff set's `canonical_state()` (Phase 2 digest
   discipline, decision 5); fitted floats assert full precision; no
   timestamp, absolute path, or environment value appears anywhere in
   the object (determinism).
9. `tests/test_scoreline_matrix.py::test_scoreline_log_probs_golden_values` —
   a hand-constructed `FittedParams` with known (μ, α, β, h) for two
   named teams yields `λ_home`/`λ_away` hand-verified to full precision;
   cells (0,0), (1,0), (0,1), (2,1), (1,2) equal hand-derived literals
   (`i·ln λ_h − λ_h − ln i! + …`) written in the test with the
   derivation in comments, asserted at **full precision** (`==`, no
   tolerance); matrix is (K+1)×(K+1) (E1, PLAN §5 layer 1).
10. `tests/test_scoreline_matrix.py::test_outcome_probs_golden_and_normalizes` —
    `outcome_probs` for the constructed case equals a hand-derived
    (pH, pD, pA) triple at full precision; `pH + pD + pA == 1` within
    documented `PROB_SUM_EPSILON`; a lopsided construction (large
    `λ_home`, tiny `λ_away`) asserts the **H > D > A tuple order**
    semantically (position 0 is the home-win probability, etc.) (E1, F1).
11. `tests/test_scoreline_matrix.py::test_dropped_mass_reported_and_outcomes_exact_under_truncation` —
    `dropped_mass` equals the hand-computed
    `1 − F_pois(K;λ_home)·F_pois(K;λ_away)` at full precision and, for a
    fixture-fitted matrix, is ≤ the documented bound for the shipped K
    (≤ 6×10⁻⁴ at K=10; ≤ 1.2×10⁻⁷ at K=15); the same fitted params
    evaluated at two different `MAX_GOALS` values produce
    **byte-identical (pH,pD,pA)** while matrices and dropped masses
    differ — W/D/L come from analytic tails, exact under truncation
    (E1).
12. `tests/test_scoreline_matrix.py::test_pure_evaluator_api_no_cutoff_logic` —
    `inspect.signature` of `scoreline_log_probs` is exactly
    `(fitted, home, away)` and of `outcome_probs` exactly
    `(matrix)` — no `as_of`/cutoff/history parameter exists to forget
    (cutoff discipline lives in `fit` alone, F1); the matrix exposes raw
    `log_probs` (not only probabilities) for Phase 11's hand-computed
    goldens; repeated calls with equal inputs are bit-identical.
13. `tests/test_model_separation.py::test_models_module_separation_ast` —
    AST scan of every `.py` under `app/models/`: imports only a stdlib
    whitelist (math, dataclasses, typing, enum, hashlib, itertools as
    actually used) plus `app.domain`; **no** `app.storage`,
    `app.ingestion`, `app.validation`, `app.api`, `sqlite3`,
    `urllib*`, `http*`, `socket`, `requests`, `fastapi`; no `open()`,
    `os`, `sys`, `pathlib`, `io`; **no `random`** (estimation contains
    no randomness, D1); no wall-clock or environment forms (extends
    Phase 2's criterion 12 scan — positive/negative-control probes
    preserved, never weakened); and **no module-level fitted singleton**
    — no module-level assignment in `app/models` constructs or binds a
    `FittedParams` or result of `fit` (G1, PLAN §6 layer 5).
14. Suite gate (recorded execution) — `.venv/bin/python -m pytest -q`
    from the repo root reports 0 failed, 0 errors, 0 skipped, 0 xfailed,
    0 xpassed. Executed and pasted by the tester; executed independently
    (twice) by the reviewer; re-executed by the monitor via the health
    script. `bash scripts/health-check.sh` still completes with an `OK:`
    determinism line, `none` skips/xfails, and clean pip check. Watch the
    120 s health-test timeout as the suite grows (KNOWN-LIMITATIONS item
    2): if it trips, this phase re-scopes the mechanism — never weakens,
    skips, or xfails the test.

## Out of scope

- **xG and kickoff times** — explicitly out (quant G2): this phase
  consumes integer scorelines, dates, and team names only; availability
  is recorded but never read.
- **Seeded RNG / simulation** — Phase 4 (quant: RNG confined to Phase 4);
  HANDOFF IX-3's seeded-RNG clause is delivered there, not here.
- Phase 4 scenarios, Phase 5 forecasts/API/storage/FastAPI,
  `app/state`, `app/features`, `app/backtesting`, `app/evaluation` —
  later phases; no cutoff logic beyond `fit`'s internal filter exists
  yet (Phase 8 audits it adversarially, Phase 5 embeds it in the
  forecast builder).
- Model upgrades: Dixon-Coles, time decay, form, overdispersion/
  negative-binomial, player effects, ridge by default (opt-in field
  only), covariance matrices, confidence intervals, optimizer
  frameworks, CLI entry points.
- Any change to `scripts/health-check.sh`, `pytest.ini`, `conftest.py`,
  the Phase 2 hygiene test file, fixtures, or `docs/DATA-SOURCES.md`;
  planning Phase 4 (block mode — developer acceptance first).

## Risks

- **Leakage:** the entire history surface is now the `fit` cutoff.
  Guarded by criteria 1–2 (inclusive-boundary + poisoned-future
  proof); the reviewer should check no pre-filtering sneaks into tests'
  call sites, which would test the caller instead of `fit`.
- **Numerical correctness:** hand-rolled solves and Newton updates are
  easy to get subtly wrong (pivoting, singularity when pre-cutoff data
  is thin). Guarded by criteria 7 (form reconstruction), 5 (thin-data
  fit must still return a flagged, well-formed object), and golden
  values in 9–11. If the Hessian is singular for degenerate inputs, the
  result must surface as a non-converged/insufficient **flag**, never a
  crash dressed as success or a silent fallback.
- **Silent non-convergence:** the classic failure is emitting plausible-
  looking numbers anyway. Guarded by criterion 4 (status required,
  forced-cap test) and criterion 8 (provenance completeness).
- **Determinism:** dict/set iteration over teams, unordered match
  iteration, or any environment read will flip the monitor's double-run
  comparison. Guarded by criteria 3, 8, 13.
- **Golden-literal fragility:** full-precision `==` assertions depend on
  the derivation matching evaluation order. If a literal mismatches by
  an ulp, the correct response is to re-derive and re-document — **never**
  to widen the tolerance (except the documented `PROB_SUM_EPSILON`
  where quant sanctioned it).
- **Overengineering:** resist a general optimizer, a model registry,
  parameter covariance, speculative feature hooks, and growing the
  611-line hygiene file. Four small modules, one Newton loop, one
  matrix builder suffice at 12 params.
- **Suite cost / docs drift:** ~13 new tests grow the health-script-
  fed suite roughly proportionally (KNOWN-LIMITATIONS item 2 budget);
  three protocol docs are still uncommitted and must ride this phase's
  checkpoint or every future sweep stays WARN.
- **Overclaiming outputs:** in-sample fits on synthetic data are
  estimates only (F2). The assumptions doc and KNOWN-LIMITATIONS entry
  must say so; no brief text or doc may describe these numbers as
  validated accuracy.

## Open questions for the developer

1. **Truncation constant `MAX_GOALS` (default a if unanswered):**
   a. **(Recommended)** K = 10 — dropped joint mass ≤ 6×10⁻⁴ at
      fixture-fitted lambdas (documented bound); 11×11 matrix.
   b. K = 15 — ≤ 1.2×10⁻⁷, 16×16 matrix; marginally more cost,
      tighter bound. (Either way the matrix reports dropped mass and
      W/D/L stay exact.)
2. **Insufficient-data thresholds (default a if unanswered):**
   a. **(Recommended)** `MIN_MATCHES_PER_TEAM = 10`,
      `MIN_TOTAL_MATCHES = 20`, `MIN_TOTAL_GOALS = 60` — fixture reality
      (20 matches/team, 156 goals) passes cleanly; a first-matchday
      cutoff demonstrably trips both the overall and per-team flags.
   b. Your own thresholds (state them; criteria 5 is written against
      whichever values ship).
3. **How pure evaluators treat a non-converged fit (default a if
   unanswered):**
   a. **(Recommended)** `scoreline_log_probs` computes and the
      `ScorelineMatrix` echoes the fit's convergence status and
      insufficient flags — downstream can never lose the flag, and no
      silent refusal path is invented this phase.
   b. Evaluators raise `ValueError` on a non-converged
      `FittedParams` — stricter, but creates a hard failure path before
      any consumer exists; revisit at Phase 5 if chosen.

Questions 1–3 fall back to their recommended defaults if unanswered at
build start. Per the constitution, no Phase 4 planning begins until
Phase 3 passes review, is committed, and passes the monitor sweep — and
Block 1 acceptance is the developer's, at the block boundary, after all
three phases.

---

## AMENDMENT A1 — sanctioned 2026-10-16 by glass-architect (recorded by the conductor)

The brief's BUILD list prohibited all changes to
`tests/test_fixtures_and_hygiene.py` while mandating `app/models/`
(criterion 13) and the suite gate (criterion 14). The Phase 2 hygiene
test rglobs every `.py` under `app/` and indexes
`ALLOWED_APP_IMPORTS[package]`; no `"app.models"` key exists, so
criterion 12 crashes with `KeyError: 'app.models'` and criterion 14 is
unachievable as written. This is a dictionary-coverage gap, not a
relaxation of any check.

1. **Sanctioned change — exactly one entry, nothing else.** In
   `tests/test_fixtures_and_hygiene.py`, inside `ALLOWED_APP_IMPORTS`,
   add this single entry:

       "app.models": {"app.domain", "app.models"},  # Phase 3: models imports stdlib + app.domain only

   The brief's "Do not create or modify" paragraph and the Out-of-scope
   bullet are amended to read: "…`tests/test_fixtures_and_hygiene.py` —
   **except the single sanctioned `ALLOWED_APP_IMPORTS["app.models"]`
   entry of amendment A1; nothing else in that file changes**." Net
   growth: +1 line. Monitor finding 2 (611-line file) stays carried;
   this +1 line is an A1-sanctioned deviation and must be declared in
   the Phase 3 checkpoint, review, and monitor sweep so the diff is not
   read as unexplained growth.
2. **No further changes to that file this phase.** Specifically NOT
   sanctioned: adding `app.models` to `PURE_PACKAGES`,
   `BANNED_PURITY_IMPORTS`, or any `BANNED_*`/`WALL_CLOCK_*`/
   `ENVIRONMENT_PATHS` set; touching probes, positive/negative controls,
   or helpers; refactoring or splitting the file. The stricter purity
   rules criterion 13 requires of `app/models` (`open()`, `os`, `sys`,
   `pathlib`, `io`, `random`, no module-level fitted singleton) are
   enforced by the new `tests/test_model_separation.py`, which is the
   sanctioned home for them — criterion 12 keeps its unconditional
   scans (network/star/wall-clock/environment) over `app/models` via
   this one entry, unchanged in strength.
3. **Source of truth for the allowed-set** (builder, reviewer, and
   monitor quote this verbatim):
   `ALLOWED_APP_IMPORTS["app.models"] == {"app.domain", "app.models"}`
   — i.e. `app.domain` (and `app.domain.*` by prefix) plus intra-package
   imports (`app.models`, `app.models.constants`, `app.models.params`,
   `app.models.poisson`, `app.models.scoreline`, and relative `.x` /
   `..domain` forms, which resolve to those absolute names). **Nothing
   else**: no bare `app`, no `app.validation`, no `app.ingestion`, no
   `app.storage`, no `app.api`. This is the strictest allow-set in the
   file apart from `app.domain` itself. Criteria 13 and 14 stand as
   written; no acceptance criterion text changes.
