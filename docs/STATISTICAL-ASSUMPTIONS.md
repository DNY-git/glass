# STATISTICAL ASSUMPTIONS — SPORTS LOOKING GLASS

Status: authored **before any Phase 3 build code** per quant ruling A1
(Phase 3 brief, DOCS step); Phase 3 then built `app/models/` to this
register, and independent review passed it (PASS, 2026-10-16, after 1
fix cycle) — the checkpoint commit that records the phase as official
comes immediately after this docs step. Sections 1, 3, 4, and 5 now
describe **implemented, tested behavior** of `app/models/` (verified
against the code and its acceptance tests during Phase 3 docs work);
§2's "what will test it" entries name Phases 9 and 11, which **have not
run** — they are commitments, not results. §7 (simulation and scenarios)
was likewise **authored before any Phase 4 build code** (quant ruling A5,
Phase 4 brief decision 14) and was updated to implemented reality at the
Phase 4 docs step (2026-10-17), verified against the shipped code and
its acceptance tests. This register is the honest statement of the
model's assumptions and their weaknesses, kept coordinated with
`docs/KNOWN-LIMITATIONS.md` and any quant advisories.

Scope: pipeline stage 5 (STATISTICAL MODELS), model version
`"poisson-mle-v1"`. Every number produced by this stage is an in-sample
**estimate**. See §6.

## 1. Model form

Log-linear Poisson goal model, fitted by unpenalized maximum
likelihood:

```
λ_home = exp(μ + α_home + β_away + h)
λ_away = exp(μ + α_away + β_home)
```

- `μ` is the grand mean log-rate; it absorbs the league-wide scoring
  level and the team means.
- `α_t` is team `t`'s attack strength, `β_t` its defence strength, both
  on the log scale, with **sum-to-zero identifiability**:
  `Σα = 0`, `Σβ = 0` (verified within `SUM_TO_ZERO_EPSILON = 1e-6`).
  Without this constraint `μ` and the strengths are not separately
  identified — any constant can be shifted between `μ` and the α/β and
  leave every λ unchanged.
- `h` is a **single shared home-advantage log-term**, estimated by MLE
  like every other parameter. It is never hardcoded, never assumed to be
  a fixed league constant, and its estimated value is echoed in each
  fit's provenance. Its data-dependence is proven by test (fit at an
  early cutoff yields a different `h` than fit on the full history).
- Goals of the two sides in one match are modeled as **independent
  Poisson draws given the parameters**: home goals ~ Poisson(λ_home),
  away goals ~ Poisson(λ_away), independent of each other.

Fixed configuration of this model version: unpenalized (no ridge; the
config field exists and defaults to `None`, so any future shrinkage must
be explicit and echoed), fit scope = both fixture seasons pooled, teams
and parameters ordered by sorted team names.

## 2. Assumptions and their weaknesses

Each entry: the assumption, why it matters, and what will test it. The
"testing" entries below name Phases 9 and 11 — **neither has run**;
until they do, nothing in this section has been empirically tested, and
the fitted numbers remain in-sample estimates on synthetic data (§6).

**(a) Conditional independence of home and away goals.**
*Assumption:* given (μ, α, β, h), a team's goal count is independent of
its opponent's in the same match.
*Weakness:* real football exhibits common shocks — weather, referee
decisions, game state (a team chasing the game opens up and concedes),
red cards — that correlate the two counts. Empirical home/away goal
correlations are typically in the 0.1–0.2 range; on this project's
fixture set the observed figure is 0.084. Positive correlation means
the joint scoreline distribution is too diffuse: mass is spread away
from the diagonal relative to reality.
*What will test it:* Phase 11 chronological evaluation scores the
resulting scoreline/outcome distributions (log loss, Brier, RPS) and
calibration against realized results; residual correlation diagnostics
are a candidate for the model-improvement loop (Phase 12/13, and the
Dixon-Coles joint correction listed in §2d).

**(b) Poisson variance: var = mean.**
*Assumption:* each goal count has variance equal to its mean.
*Weakness:* goal counts in football are commonly **overdispersed**
(variance exceeding the mean) because scoring rates drift within and
across matches. Ignoring overdispersion understates tail probabilities
of high-scoring outliers and overstates the precision of the fitted
parameters; a negative-binomial alternative is the standard remedy.
*What will test it:* overdispersion is explicitly **checked in
Phase 11** (variance-vs-mean diagnostics alongside predictive scores);
it is deferred, not ignored, from this phase (see §2d rationale).

**(c) Single shared home-advantage term.**
*Assumption:* every team benefits from the same multiplicative home
factor `exp(h)`; there is no per-team home advantage, no away effect,
and no interaction with competition or season.
*Weakness:* home advantage plausibly varies by team (travel, pitch,
support intensity) and by season; pooling it into one term biases
team-specific λs for teams whose true home effect differs from the
league average.
*What will test it:* Phase 11 calibration and per-team score residuals
surface systematic home/away misfit; a per-team or time-varying `h` is
an explicit model-improvement candidate (§2d), justified only if it
moves out-of-sample scores.

**(d) No form, no time decay, no Dixon-Coles, no player effects, no
scoreline dependence — by design, this phase.**
*Assumption:* recent matches count as much as old ones within the
pooled window; a match's likelihood factorizes into independent
Poisson terms with no low-score correction (Dixon-Coles τ), no team
form window, no player personnel term.
*Weakness:* each omission is a known predictive improvement foregone:
goals are not exchangeable over time (teams improve/decay), 0-0 and 1-1
are underweighted without a Dixon-Coles correction, and player absence
moves rates. On this project's fixtures the baseline fit has **120 goal
observations for 12 parameters** (μ, h, 5 free α, 5 free β) — richer
structures would be weakly identified at that ratio.
*Why deferred (rationale, not oversight):* evaluation noise of roughly
±0.05 log loss **swamps** any plausible in-sample gain from fancier
structures, so added complexity cannot be shown to help with the data at
hand; and PLAN §8 postpones advanced model families until the baseline
has been chronologically backtested and evaluated. Dixon-Coles, time
decay, form, player effects, and overdispersion corrections are
**explicitly deferred, not forgotten** — each becomes admissible only
with evidence from Phases 9/11 that the baseline misses it.
*What will test it:* Phases 9 (chronological backtesting vs baselines)
and 11 (evaluation) quantify how much the omissions cost; the
model-improvement stage then weighs upgrades against the noise floor.

**(e) Stationarity across pooled seasons.**
*Assumption:* both fixture seasons are drawn from one stationary
process — the same (μ, α, β, h) describe 2024-25 and 2025-26, so
pooling them is legitimate.
*Weakness:* teams change between seasons (promotion, recruitment,
management), so pooled strengths average over regimes and can lag
current form; a pooled fit describes no single season exactly.
*What will test it:* per-season fits compared against the pooled fit
and chronological backtest performance (Phases 9/11) reveal whether
pooling costs predictive accuracy; each fit records the seasons it
consumed so the pooling is always visible in provenance.

**(f) Draw-bias caveat (E2) — a known, directional model defect.**
*Assumption:* none is being made that holds; this is the failure mode
of assumptions (a)+(b) taken together.
*Weakness:* **independent Poissons characteristically
under-represent draws.** Because the two goal counts are independent,
`P(home = away)` gets too little mass — the missing low-score dependence
that a Dixon-Coles-style correction targets. Users of this model should
expect drawn scorelines to be systematically underpredicted until that
correction ships.
*What will test it:* draw-frequency calibration against realized
results is part of Phase 11's evaluation; the size of the draw deficit
is the evidence that would justify the deferred correction.

## 3. Estimator

- **Newton-Raphson** on the (concave) log-likelihood, with **analytic
  derivatives** — score (gradient) and observed information (Hessian) —
  not numerical differentiation. The likelihood is concave in the
  unconstrained parameterization, so a stationary point found this way
  is the global maximum of the unpenalized likelihood.
- **Hand-rolled dense linear solve**: stdlib Gaussian elimination with
  partial pivoting on systems no larger than ~12×12 at fixture scale.
  No numpy/scipy/optimizer library (PLAN §3). Quant tested naive
  fixed-point/IPF updates and found them divergent (±150 in 200
  iterations), which is why full Newton with analytic derivatives is
  mandated.
- Named constants (implemented in `app/models/constants.py`, each
  echoed in every fit's config provenance):
  - `NEWTON_TOL = 1e-10` — convergence threshold on the **infinity
    norm of the applied update step** (max |step_i| after damping).
  - `MAX_ITERATIONS = 100` — hard cap on Newton steps.
  - `DAMPING = 1.0` — full Newton step.
- **Step / backtracking rule — builder-confirmed 2026-10-16 (review
  PASS); the earlier "to-be-confirmed-by-builder" placeholder is hereby
  resolved:** the implemented rule is exactly the documented default —
  a full Newton step scaled by `DAMPING = 1.0`, with **no backtracking,
  no line search, and no trust radius**. Each iteration solves
  `I @ delta = g` (hand-rolled Gaussian elimination with partial
  pivoting), applies `step = DAMPING * delta` to the parameter vector,
  and declares convergence when `max |step_i| < NEWTON_TOL` **after**
  the step has been applied. The reported iteration count is the
  number of steps applied; reaching `MAX_ITERATIONS` first yields the
  named non-converged status — a reported result, not a failure.
- **Non-convergence is a reported result, never silent** (implemented
  and test-proven): every fit returns a required `convergence_status` —
  `CONVERGED`, `MAX_ITERATIONS`, `SINGULAR_SYSTEM` (the Newton system
  singular or a non-finite update, typically thin pre-cutoff history),
  or `NO_DATA` (no strictly pre-cutoff matches, or fewer than two
  distinct teams) — alongside its parameters; no parameter vector is
  ever emitted without a status. A singular Hessian on thin data
  surfaces as a flagged `SINGULAR_SYSTEM`/insufficient result — never a
  crash dressed as success and never a silent fallback. The pure
  evaluators echo the fit's convergence status and insufficient flags
  on every `ScorelineMatrix`, so downstream can never lose the flag
  (brief open question 3, default a).
- Estimation is fully deterministic: no randomness, no wall clock, no
  environment reads inside `app/models`; shuffled input yields
  bit-identical output (parameters ordered by sorted team names, matches
  iterated in canonical order).
- **Unpenalized by refusal, not by silence** (implemented): `FitConfig`
  carries a `ridge` field defaulting to `None`; a non-None value is
  refused with a `ValueError` — poisson-mle-v1 implements no
  shrinkage, so no silent-shrinkage path exists to hide in.

## 4. Scoreline truncation

- `MAX_GOALS = 10` (K): scoreline cells `log P(i, j)` are computed for
  `i, j ∈ 0..K` (an 11×11 matrix) as the analytic product of two
  Poisson pmfs: `log P(i,j) = i·ln λ_h − λ_h − ln(i!) + j·ln λ_a −
  λ_a − ln(j!)`.
- **Documented bound:** at fixture-fitted lambdas, K = 10 drops at most
  **≤ 6×10⁻⁴** of joint probability mass; K = 15 would drop
  **≤ 1.2×10⁻⁷** (at the cost of a 16×16 matrix).
- **Dropped mass is always reported** on the matrix as
  `1 − F_pois(K; λ_home)·F_pois(K; λ_away)` — never hidden, never
  assumed away.
- **W/D/L are exact under truncation:** home/draw/away probabilities
  are computed from **analytic Poisson tails**, not from sums of the
  truncated cells, so the outcome probabilities are unaffected by K;
  in implementation the tails are summed to a fixed bound
  `OUTCOME_TAIL_GOALS = 128`, deliberately independent of `MAX_GOALS`
  (the unsummed remainder is below 1e-100 at any fixture-scale lambda);
  `pH + pD + pA = 1` within `PROB_SUM_EPSILON = 1e-12`. Two matrices of
  different K for the same fitted params yield byte-identical outcome
  triples while their cell counts and dropped masses differ.
- Raw log-probability cells are exposed (not only probabilities) so
  later phases can verify them against hand-computed goldens.

## 5. Insufficient-data thresholds

Named, documented constants; flags **attach to the fitted output and are
never hidden**:

- `MIN_MATCHES_PER_TEAM = 10` — a team with fewer pre-cutoff matches is
  flagged per-team; its strengths rest on thin evidence.
- `MIN_TOTAL_MATCHES = 20` — below this many pre-cutoff matches the
  whole fit is flagged `insufficient_data`.
- `MIN_TOTAL_GOALS = 60` — below this many observed pre-cutoff goals the
  whole fit is flagged `insufficient_data`.

Rationale for the values: the full fixture pool (60 matches, 156 goals,
20 matches per team) passes cleanly, while an early-cutoff fit (e.g. the
first matchday) demonstrably trips both the overall and the per-team
flags — the thresholds discriminate between "enough to estimate" and
"enough to notice we don't". `sample_size` (matches used, goals
observed) accompanies every fit so consumers always see what the
estimate rests on. Fitting still returns a well-formed object under the
thresholds — insufficiency is reported, not crashed on: an empty
pre-cutoff history (or fewer than two distinct teams) returns a
`NO_DATA`-flagged object with neutral zeros, and a thin history whose
information matrix is singular returns a flagged `SINGULAR_SYSTEM`
result (the last well-defined iterate, explicitly marked) — both with
the insufficient flags attached.

## 6. Honesty — what these numbers are not

- **In-sample fits on synthetic data are ESTIMATES ONLY.** They are not
  evidence of accuracy. A scoreline matrix that sums to 1, an outcome
  distribution that looks plausible, and a converged Newton run all
  demonstrate *internal consistency*, nothing more: **normalized ≠
  accurate** (constitution, HANDOFF Part V).
- **Evidence begins at Phases 9 and 11** — chronological backtesting
  against baselines and evaluation (log loss, Brier, RPS, calibration)
  against realized results. Until those run, no number from
  `app/models` may be described — in code, docs, briefs, or reports —
  as validated, accurate, or beating anything.
- **Probabilities are never certainties.** Every emitted probability is
  an estimate with stated uncertainty; this project computes no
  confidence intervals this phase, so point estimates carry no
  uncertainty band at all — a further reason to treat them as
  provisional.
- **The baseline is deliberately modest** (§2d): at fixture scale it is
  120 goal observations for 12 parameters, and evaluation noise of
  ±0.05 log loss swamps fancier structures' plausible gains. Shipping
  only the baseline Poisson is an honest scope decision, not a claim
  that the baseline is sufficient.
- Nothing here is betting functionality. These estimates are for
  research and decision analysis, presented with their weaknesses.

## 7. Simulation and scenarios (Monte Carlo) — implemented and tested (Phase 4)

Status: **authored BEFORE any Phase 4 build code**, per quant ruling A5
(Phase 4 brief, decision 14, DOCS step) — the Phase 3 A1 pre-build
pattern applied to the simulation/scenarios section — then **updated at
phase end to implemented reality**, verified against the shipped code
and its acceptance tests during the Phase 4 docs step (2026-10-17):
`app/simulation/` and `app/scenarios/` exist under `app/`, the suite is
green (57 passed), and independent review passed the phase (PASS,
2026-10-17, first pass, criteria 1–20). The pre-build authorship is
recorded deliberately: every honesty constraint below (simulation noise
≠ uncertainty, hypothetical, analytic-first) was committed to before any
number could be produced. Sections 1–6 bind every simulation and
scenario output without exception — scenario numbers inherit **all §2
caveats** (goal independence, Poisson variance, single shared home
advantage, omitted structures, season stationarity, draw bias) plus §4
truncation and §6 in-sample-estimates-only. Implemented named constants
(echoed on every result): `SIM_VERSION = "sim-categorical-v1"`,
`DEFAULT_N_SIMS = 10_000`.

Scope: HANDOFF Part IV stage 7 (SCENARIO EXPLORATION — *"bounded,
labeled-hypothetical multipliers"*) plus a Monte Carlo layer over the
existing stage-5 scoreline matrix — infrastructure, not a reporter. A
simulation call consumes exactly one frozen `ScorelineMatrix` for one
fixture; it has no history surface, no `as_of`, and no time parameter to
forget, so cutoff discipline stays in `fit` alone (HANDOFF Part V).

**(a) `mc_stderr` measures simulation noise only — never model or
parameter uncertainty.**
*Statement:* `mc_stderr = sqrt(p(1-p)/n)` is computed from the
**analytic** `p` (that exact expression order is part of the contract),
and it quantifies only the Monte Carlo noise of drawing `n_sims`
samples from a fixed, already-known distribution.
*What it is not:* it is not a measure of model uncertainty, parameter
uncertainty, or data uncertainty — **no confidence intervals exist
anywhere in this system** (no bootstrap, no parameter sampling, no
bands anywhere; §6). Increasing `n_sims` shrinks the noise term and
**never** shrinks the uncertainty: a run with 10⁷ draws of an in-sample
estimate is still that same in-sample estimate. Scenario numbers are
**hypothetical**, conditioned on the in-sample fit and on **ALL §2
caveats** (goal independence, Poisson variance, single shared home
advantage, omitted structures, season stationarity, draw bias). The
scenario multipliers are **arbitrary documented knobs** (§d), not
empirical claims about any team. Scenario outputs **restate the
inherited caveats**: draw bias (§2f), overdispersion (§2b), stationarity
(§2e), truncation (§4), and in-sample-estimates-only (§6).

**(b) Sampling target — categorical over the truncated, renormalized
(K+1)² matrix.**
*Statement:* draws come from a cumulative table built **row-major** (i
ascending, j ascending) from `exp(log_probs[i][j])`, divided by the
table sum; each draw is `u = rng.random()` located by
`bisect.bisect_left`, with an **fp-epsilon clamp-to-last-cell guard**
when the lookup lands past the final index (possible only from
floating-point rounding at the table tail; the clamp touches only the
last cell and never shifts mass between cells).
*Documented deviation:* MC frequencies therefore deviate from the
analytic `outcome_probs` target by at most
**`dropped_mass / (1 − dropped_mass)` ≤ ~6.004×10⁻⁴** at
fixture-fitted lambdas (K = 10, where `dropped_mass ≤ 6×10⁻⁴` per §4) —
the same figure the acceptance tests assert docs/code agreement on
(implemented and test-asserted).
*Rejected alternative, recorded honestly:* independent untruncated
Poisson draws are **not** used this phase, because they would require
an `out_of_range_count` (draws outside 0..K) — a second sampling path
and a second truth surface. **No `out_of_range_count` field exists by
design**; the already-disclosed dropped mass of §4 stands in its place,
and revisiting this choice requires a future brief that says why.

**(c) Seed policy — required, keyword-only, instance-only.**
*Statement:* `seed` is a **required keyword-only `int` argument** of
`simulate` — no default and no RNG-object parameter anywhere in the
API. Each call constructs a **fresh `random.Random(seed)`**; the RNG is
instance-only — no module-level RNG binding, no `random.seed()` global
seeding, no unseeded `Random()`.
*Draw primitive:* **`random()` is the only draw primitive** — the one
method CPython documents as sequence-stable across Python versions for
a given seed; `randrange`/`randint`/`choice`/`choices`/`sample`/
`getrandbits`/`shuffle` are banned in the simulation module.
*Banned seed sources:* `hash()`-derived seeds (str hashing is salted
per process, which would also break cross-process bit-identity),
`time`/`os.urandom`/`secrets`/`uuid`/`id()`, and seeding from
`input_digest` or any parameter value or digest.
*Contract:* identical `(fitted, home, away, seed, n_sims, sim_version
[, scenario])` → **field-for-field identical frozen output**;
`seed`, `n_sims`, and the `SIM_VERSION` string are echoed on every
result for provenance.

**(d) Transform semantics (developer-decided) — parameter-scale,
bounded, never clamped, never averaged.**
*Statement:* the transform is literal **parameter-scale**:
`α′ = m·α`, `β′ = m·β`, `h′ = m·h`. Bounds are named documented
constants **`MULTIPLIER_MIN = 0.5`** and **`MULTIPLIER_MAX = 2.0`**,
inclusive at both ends; a non-inclusive-of-range, non-finite, or
non-numeric multiplier raises **`ValueError` — never silent clamping**
(clamping would be fabricated data, constitution prohibition 4).
*Honest interpretation:* on the log scale a multiplier **dulls (m < 1)
or amplifies (m > 1) the parameter's deviation from league mean**, so
**the sign of the effect depends on the parameter's sign** — the same
`m < 1` applied to a positive α and to a negative α moves λ in opposite
directions. This is stated rather than glossed; the multipliers
themselves are arbitrary knobs, not measured effects.
*Labeling and averaging:* every scenario carries a non-empty
caller-supplied **label echoed on every output**, and scenarios are
**labeled hypothetical and never averaged** — the API evaluates one
scenario per call, alternatives are presented side by side, and
disagreement is reported, never collapsed into a silently invented
ensemble (comparison belongs to stage 8 / Phase 7).

**(e) Analytic-first rule — simulation never replaces `outcome_probs`.**
*Statement:* the reported single-match probability is always the
analytic `outcome_probs` (§4: exact under truncation, analytic tails).
A single-match probability has a closed form today; simulating it would
add noise to an exact quantity, so **simulation NEVER replaces
`outcome_probs`**. Legitimate uses are (i) Phase 12's replay machinery
(same-seed end-to-end determinism replay, stochastic path replay) and
(ii) future aggregate/season-path quantities with no closed form
(season point totals, multi-stage paths). Phase 11 evaluates analytic
probabilities only — MC noise never contaminates log loss, Brier, or
RPS.

**(f) Honesty — internal consistency is not validation.**
*Statement:* MC frequencies tracking the analytic probabilities
demonstrate **sampler internal consistency only** — never *"validated"*
and never *"accurate"*; §6's *normalized ≠ accurate* applies verbatim
to Monte Carlo agreement. **Evidence begins at Phases 9 and 11**
(chronological backtesting and evaluation against realized results);
until those run, no number from simulation or scenarios may be
described — in code, docs, briefs, or reports — as validated, accurate,
or beating anything. Nothing here is betting functionality
(constitution prohibition 3); these are hypothetical research numbers
presented with their weaknesses.

**(g) Provenance refusal — a scenario whose baseline does not equal
the given fitted object is refused.**
*Statement (implemented beyond the pre-build specification, recorded at
phase end so this register describes the code and not the plan):*
`simulate(fitted, home, away, ..., scenario=s)` raises `ValueError`
unless `s.baseline == fitted` (frozen-dataclass **value equality**).
Simulating under a mismatched baseline would draw from one fit's
distribution while echoing a different fit's provenance on the result —
mislabeled output — so the mismatch is refused outright rather than
silently reconciled or re-labeled. This guard shipped with the build
and is pinned by test
(`test_simulate_scenario_baseline_mismatch_refused_by_value_equality`).

## 8. Forecasts (stage 6) — forecast discipline, snapshot immutability, and serving honesty — implemented and tested (Phase 5)

Status: **authored BEFORE any Phase 5 build code**, per the Phase 5
brief decision 16 (the Phase 3 §3 / Phase 4 §7 pre-build pattern, here
quant-mandated) — every constraint below was committed to before a line
of `app/forecasts/`, `app/storage/`, or `app/api/` could exist — then
**updated at phase end to implemented reality**, verified against the
shipped code and its acceptance tests during the Phase 5 docs step
(2026-10-17): all three packages exist under `app/`, the suite is green
(83 passed), and independent review passed the phase (PASS, 2026-10-17,
first pass, criteria 1–27). The pre-build authorship is recorded
deliberately: every honesty, immutability, and serving constraint below
was fixed in prose before a stored byte or an HTTP body could exist.
The bindings cited are the Phase 5 brief's quant rulings (F1–F3, S1–S3,
A1–A3, H1, L1) and the developer's recorded answers of 2026-10-17
(stdlib `http.server`; re-derive `log_probs`; no `GET /teams`; new
scoreless `Fixture`; no generation CLI;
`FORECAST_VERSION = "forecast-poisson-mle-v1"`; amendment A2 as
written). Two build-time deviations from the pre-build text are
recorded in the brief as ratified architect amendments (2026-10-17) and
noted here where they touch this section's claims: (i) path segments
are decoded by a small strict manual decoder (`decode_segment` in
`app/api/server.py`) rather than `urllib.parse` — AMENDMENT A5: `urllib`
stays banned under A2's exactly-pinned exception map
`{"app.storage": {"sqlite3"}, "app.api": {"http"}}`, and a permissive
`unquote` never raises on malformed escapes, which criterion 19's 400s
require; (ii) criterion 8's raw-write refusal surfaces as
`sqlite3.IntegrityError` (the brief's `OperationalError` mention
corrected by erratum — test reality over brief text; no test text
changed).

Scope: HANDOFF Part IV stage 6 (FORECAST DISTRIBUTIONS — *"full
scoreline/outcome distributions, frozen at creation"*) plus the durable
write-once snapshot store and the read-only serving surface around it.
Sections 1–7 bind every forecast without exception: a forecast is the
§5 fit projected through the §4 matrix — inheriting all §2 caveats, §4
truncation and its dropped-mass disclosure, §5's flags, §6's honesty,
and §7e's analytic-first rule. Nothing below is a claim about
predictive quality; this section specifies **discipline and provenance
properties** — what a forecast may contain, when it was frozen, how it
verifies — never accuracy. "Validated" and "accurate" remain banned
until Phases 9/11 evidence exists (§6, §7f).

**(a) Cutoff discipline — the cutoff IS the fixture date, derived inside
the builder; no caller-supplied `as_of` exists (F1/L1).**
*Statement:* the builder signature is `build_forecast(matches, fixture)`
— no `as_of`, `cutoff`, `date`, or any time-like parameter exists to
forget. The cutoff **is `fixture.date`**, computed inside the builder,
which then calls `fit(matches, fixture.date)` — so Phase 3's strict
`date < as_of` filter (§3) applies unchanged underneath: cutoff
enforcement lives in the calculation, never only at the call site
(HANDOFF Part V), and here it is double-enforced (builder derivation +
fit's internal filter).
*Guarantees:* nothing dated **on or after** the fixture date can enter
the fit — a match dated exactly at the fixture date is excluded by the
strict `<` (silently outside the cutoff, never an error: that is the
leakage defense), while the fixture's own natural key appearing in
`matches` is refused with `ValueError` — the target must not be its
own history.
*Day granularity, stated precisely (L1):* `fixture.date` is a strict
day-granularity date string — never a datetime, never a fractional
day, never a wall-clock instant; `as_of` is stored as exactly the
fixture date string. The engine therefore **cannot exploit within-day
ordering even when a kickoff time is known** (two same-date matches
cannot be ordered against each other) and **cannot verify wall-clock
pre-kickoff ordering at all** — the domain has dates, no clock (S2:
no wall clock anywhere in forecast content or schema). This is honest
day-level pre-match discipline and is never described as anything
finer.

**(b) The forecast record — frozen, analytic, deterministic, scoreless
(F2).**
*Statement:* `Forecast` is a frozen dataclass with a pinned field
contract: the fixture natural key (competition, season, date, home,
away) plus `kickoff` as `OptionalValue` (MISSING never defaulted),
`as_of` (== `fixture.date` exactly), the **full `FittedParams` by
value** (all provenance: model_version, config, pooling, input_digest,
teams, parameters, convergence_status, sample_size, insufficient
flags), matrix essentials (`lambda_home`, `lambda_away`, `max_goals`,
`dropped_mass`), the three analytic outcome probabilities,
`forecast_version`, and `content_hash`.
*Analytic-first across the Phase 4 boundary (§7e):* the stored
probabilities are the analytic `outcome_probs` at full precision —
**Monte Carlo counts and frequencies never become stored probabilities,
and no `seed` field exists anywhere on the record**. A forecast is a
deterministic object: identical `(matches, fixture)` + model version +
config ⇒ field-for-field identical `Forecast` including
`content_hash`. `app/simulation` and `app/scenarios` are not touched by
any forecast.
*Re-derivation:* full `FittedParams` by value make the scoreline matrix
a pure-function output, so the 121 `log_probs` cells are **re-derived
and hash-verified, not stored** (developer decision, 2026-10-17) —
enough for Phase 9 bit-identity verification without duplicating them.
*Flags and disclosure ride every record:* `dropped_mass` (§4) and the
fit's `convergence_status` / `insufficient_data` /
`insufficient_teams` — `SINGULAR_SYSTEM` / `NO_DATA` / insufficient are
**reported results, never fallback estimates**; a plausible-looking
flagged forecast stays flagged.
*Scoreless target:* `Fixture`, the builder's typed input, has **no
`score` field at all** — a forecast target that cannot even represent a
result is structurally incapable of consuming its own future; `Match`
(realized, scored) remains the history type, untouched.
*No baselines:* long-run home/draw/away frequency baselines belong to
Phases 9/11 and are never baked into a forecast.

**(c) Content hash — a written canonicalization spec, recomputable from
stored fields alone (F3).**
*Statement:* `content_hash = sha256(utf-8 bytes of canonical JSON)` over
exactly the record's fields **minus `content_hash` itself**, under a
fixed spec — written as code + module docstring in
`app/forecasts/canonicalization.py` (the spec of record) and summarized
here: keys sorted lexicographically (`sort_keys=True`), fixed
separators `(",", ":")`, `ensure_ascii=True`, no trailing newline;
strings as-is; ints decimal; **floats via Python's shortest round-trip
repr (full precision, no rounding ever)**; bools as `true`/`false`;
enums as their `.value` strings (`convergence_status`); tuples as JSON
arrays in order; `None` as `null`; nested frozen objects (`FitConfig`,
`PoolingRecord`, `SampleSize`, `OptionalValue`) as nested canonical
objects under fixed key names.
*Out of the payload, always:* no timestamp, no filesystem path, no
environment value, no seed, and no Monte Carlo quantity may appear in
the hashed payload (AST-enforced).
*Version is the contract:* `FORECAST_VERSION =
"forecast-poisson-mle-v1"` is part of the hashed content; any change to
the hashed field set, the canonicalization spec, or the derivation
semantics **requires a `FORECAST_VERSION` bump**.
*Verification:* a mismatch is a **hard error
(`ForecastIntegrityError`), never a warning**; the read path recomputes
the hash from the stored fields alone and compares on **every** row it
returns, and any covered field altered by any means changes the hash —
tamper evidence by construction.

**(d) Write-once snapshots — schema triggers, no clock, exact floats,
and the scope of the guarantee stated (S1/S2/S3).**
*Statement:* the forecasts table is write-once **at the schema level**:
`BEFORE UPDATE` and `BEFORE DELETE` triggers raise ABORT inside the
database file, so enforcement survives any client — including a raw
connection and the sqlite3 CLI — not merely well-behaved app code; the
application layer contains **no `UPDATE`/`DELETE` SQL at all**
(AST-scanned), and read connections open `PRAGMA query_only = 1`.
Writes are insert-only under a fixed identity: an identical re-insert is
an idempotent no-op, and an identity collision with different content
is a hard error — the original row is never overwritten.
*No clock in content (S2):* the table has **no timestamp column** — the
hash must be recomputable from stored fields alone; timestamps exist
only in HTTP `Date` headers (headers, never bodies) and in stderr log
lines.
*Float discipline (S3):* sqlite `REAL` stores IEEE-754 doubles exactly
and JSON floats round-trip via Python's exact repr; the mandated test
is build → store → read → recompute the hash → byte-equal to the
original forecast and hash.
*Scope of the guarantee — stated, not hidden:* the triggers stop every
writer that goes through sqlite's normal write paths (app code, raw
connections, the CLI). They do **not** stop a hostile superuser with
`writable_schema` access, who can alter or drop the triggers inside the
file itself. The honest claim is therefore schema-level write-once
against accidental and ordinary rewriting, **plus** content-hash
verification at read time — which still catches any alteration of a
covered field that gets past the triggers.

**(e) Serving honesty — flags at top level, provenance echoed, no
betting surface (H1/A2/A3).**
*Statement:* every forecast response carries, at **top level**
(unmissable, never nested away): `convergence_status`,
`insufficient_data`, `insufficient_teams`, `dropped_mass` — a
`SINGULAR_SYSTEM`/`NO_DATA` forecast is served with its flags
screaming, never as a silent plausible 200 — plus the full provenance
echo (`as_of`, `model_version`, `input_digest`, `forecast_version`,
`content_hash`), the fixture block with kickoff availability (MISSING
stays MISSING), and a fixed deterministic **disclaimer** stating that
these are in-sample estimates pending chronological evaluation
(Phases 9/11), never evidence of accuracy.
*What the surface never has:* no `confidence`, `ci`, `stderr`, or
interval field exists anywhere (§6; §7a's `mc_stderr` is simulation
noise and is not part of a forecast at all; `dropped_mass` is §4
truncation disclosure, not an uncertainty band) — **no uncertainty
quantification ships with a forecast**; and **no betting surface ever**
(constitution prohibition 3): no odds, stakes, EV, Kelly, edge, value,
or wager field or endpoint, with field names saying estimate or
probability, never "confidence"/"edge"/"value".
*No fabricated defaults, byte-deterministic bodies:* unknown fixture ⇒
404 with an explicit JSON error body; malformed input ⇒ 400; responses
are deterministic JSON (sorted keys, fixed separators, full-precision
floats, no timestamp in any body). "Validated"/"accurate" language
stays banned until Phases 9/11.

**(f) Store-then-serve — the API never computes (A1).**
*Statement:* the serving surface is `GET /health` and
`GET /forecasts/{competition}/{season}/{date}/{home}/{away}` only (no
`GET /teams` — developer decision, 2026-10-17), bound to `127.0.0.1`,
serving **stored snapshots only**; generation is not an HTTP verb
(non-GET ⇒ 405), no generation CLI ships, and `build_forecast` appears
nowhere under `app/api` (AST-enforced).
*Rationale:* a compute-on-demand endpoint would mint **ephemeral**
forecasts that never enter the write-once store and can therefore
**never be scored by Phase 11** — the point of durable, hash-identified,
immutable snapshots is that every forecast that ever existed is
scorable. If generation is ever exposed, it must **store-then-serve**
(insert through the write-once path, then serve the stored row) — a
future brief's decision, not this phase's.

**(g) Honesty — these are provenance properties, not quality claims.**
*Statement:* frozen records, byte-identical rebuilds, write-once
triggers, and hash verification demonstrate **immutability,
determinism, and tamper-evidence — provenance only**. A stored,
hash-verified, perfectly normalized forecast is still an **in-sample
point estimate** on synthetic data (§6): *normalized ≠ accurate*
applies verbatim to it. Evidence begins at Phases 9 and 11
(chronological backtesting against baselines; log loss, Brier, RPS,
calibration against realized results); until those run, no forecast —
served or stored — may be described, in code, docs, briefs, or
reports, as validated, accurate, or beating anything. Nothing here is
betting functionality.

## 9. Feature extraction (stage 4) — chronological features, versioned specs, availability — implemented and tested (Phase 6)

Status: **authored BEFORE any Phase 6 build code**, per glass-quant
ruling F6 (Phase 6 brief, decision 12 — the Phase 3 §3 / Phase 4 §7 /
Phase 5 §8 pre-build pattern): every constraint below was committed to
before a line of `app/features/` could exist — then **updated at phase
end to implemented reality**, verified against the shipped code and its
acceptance tests during the Phase 6 docs step (2026-10-19):
`app/features/` exists under `app/`, the suite is green (**103
passed**, clean-env run `env -u PYTEST_ADDOPTS .venv/bin/python -m
pytest -q`), and independent review passed the phase (PASS, 2026-10-19,
first pass, criteria 1–21). The pre-build authorship is recorded
deliberately: every honesty constraint below (MISSING never fabricated,
historical summaries not evidence, zero fitted transformers) was fixed
in prose before a feature value could be computed. The bindings cited
are the Phase 6 brief's glass-quant rulings F1–F7 (consulted 2026-10-18
at conductor top level; no-objections recorded) and the developer's
recorded answers of 2026-10-19 — all six open questions accepted as
recommended: `MISSING_UNTIL_FULL_WINDOW`; keep `xg_form`;
`WITHIN_SEASON` rest days; the lean decision-4 inventory;
`FORM_WINDOW = 5`; competition/season-agnostic window scope. Sections
1–8 are untouched by this section. Shipped surface (all under
`app/features/`, AST-enforced pure): `compute_features` in
`app/features/compute.py`; the frozen **22-field** `FeatureVector` in
`app/features/record.py` (`content_hash` computed at construction,
`init=False`); the named policy constants in
`app/features/constants.py` (each with a why-comment); the package's
own canonicalization spec of record in
`app/features/canonicalization.py` (no import crosses the stage
boundary); 20 new acceptance tests — `tests/test_features.py` (7,
criteria 1–7), `tests/test_features_policies.py` (7, criteria 8–14),
`tests/test_phase6_separation.py` (6, criteria 15–20), with criterion
21 the suite gate; and one version-local golden feature-vector content
hash literal
`8da6751447bd0320ed61839cd5d97562127ff80948e878ac5f07d53eb7a10b05`
(criterion 13 — re-derive on spec/interpreter change, never widen).
Declared amendments riding this section's claims (brief pre-sanctioned,
exact figures): **A1** adds the single dictionary entry
`ALLOWED_APP_IMPORTS["app.features"] = {"app.domain", "app.features"}`
and strengthens `PURE_PACKAGES` in place to `{"app.domain",
"app.validation", "app.features"}` — line-neutral, strictly stronger,
and the reason the (e)/(f) purity rules below are AST-enforceable for
this package (`import os` under `app/features` now flags) —
`tests/test_fixtures_and_hygiene.py` **623 → 624 lines**; **A2** and
**A3** update the Phase 4/5 exact key-set pins to the new 11-key
universe — **831 → 832** (`tests/test_phase4_separation.py`) and
**571 → 572** (`tests/test_phase5_separation.py`) — every legacy
assertion retained (strictly stronger pins). Independently re-derived at
this docs step by a real census run over the checked-in fixtures —
every figure of the (d) table reproduced exactly (xG 10/60, season 2
only, 4 dates; kickoff 30/60, all season 1; strict last-5-all-xG
0/120; no prior ever 6/120; no same-season prior 12/120; fewer than
`FORM_WINDOW` priors 30/120; immediate-prior-had-xG 20/120) — and
`app/models/`, `app/forecasts/`, and `app/storage/` are byte-identical
to checkpoint `44b43ea` (0-byte diff, criterion 16).

Scope: HANDOFF Part IV stage 4 (FEATURE EXTRACTION — *"chronological
features computed from history with explicit cutoffs"*), delivered as
one new pure package `app/features/` with the single entry point
`compute_features(matches, fixture)` and one frozen `FeatureVector`
record living **beside** the Forecast, never inside it. This phase is
**data-layer only**: features are computed and documented, consumed by
nothing (f) — no file under any other `app/` package imports
`app.features` (AST-enforced both directions, criterion 17), and the
first consumer arrives only via its own future brief with its own
version/identity implications. Nothing below is a claim about
predictive quality — features are historical summaries with zero
predictive claim (g), and "validated"/"accurate" remain banned until
Phases 9/11 (§6, §7f, §8g).

**(a) Cutoff discipline — the cutoff IS the fixture date, derived
inside; no caller-supplied time parameter exists (F1).**
*Statement:* the signature is exactly `compute_features(matches,
fixture)` — no `as_of`, `cutoff`, `date`, or any time-like parameter
exists to forget (the builder pattern of §8a: `fit` takes `as_of` as an
argument, `build_forecast` derives it inside; features follow the
builder). The cutoff **is `fixture.date`**, computed inside, and a
strict `date < fixture.date` filter is applied inside to every consumed
match. Nothing dated on or after the fixture date can enter any window:
on/after-cutoff matches sit silently outside it (the leakage defense,
never an error), while the fixture's own natural key appearing in
`matches` is refused with `ValueError` — the target must not be its own
history. Windows are selected in `canonical_sort_key` order (same-date
ties resolved there, never by input order), so neither input order nor
poisoned future matches can change any field.
*Cutoff-drift guard:* the model package's pre-cutoff helper is private
and byte-pinned (f), so the strict-`<` filter is reimplemented inside
`app/features`; the sanctioned equivalence guard is the **digest-parity
cross-check** — for the same `(matches, fixture)`,
`compute_features(...).input_digest == build_forecast(...).fitted
.input_digest` exactly, both sides having consumed the byte-identical
strictly-pre-cutoff set under the same `canonical_state()` definition.
A shared helper is impossible without touching the 0-byte-pinned
`app/models`; the parity test is the sanctioned alternative, recorded
as such. The poisoned-future byte-identity test (appended on-date and
later matches, extreme scorelines, injected teams change nothing,
including `content_hash`) is this stage's PLAN §6 layer-4 regression.

**(b) The `FeatureVector` record — frozen, beside the Forecast,
versioned (F3/F7).**
*Statement:* `FeatureVector` is a separate frozen dataclass; features
are never folded into `Forecast` (that would require a declared
`FORECAST_VERSION` bump plus golden re-derivation — explicitly out of
scope). Field contract: the fixture natural key (competition, season,
date, home, away); `kickoff` as an `OptionalValue` **echo of
availability only** — MISSING never defaulted to a fabricated time, and
the computation reads dates only, because the domain has day
granularity and no within-day ordering discipline (§8a), so consuming
`HH:MM` would claim precision the domain does not have; `as_of ==
fixture.date`; `feature_version`; `input_digest`; per side the six
feature fields (c); and `content_hash`.
- `FEATURE_VERSION = "features-chronological-v1"` — the versioned
  feature spec (HANDOFF IX-6) is this constant plus the named policy
  constants plus this section's inventory. **Bump discipline worded
  identically to `FORECAST_VERSION`'s (§8c): any change to the hashed
  field set, the canonicalization spec, or the derivation semantics
  requires a `FEATURE_VERSION` bump — the constant is the contract's
  version.**
- `input_digest` has the **identical definition to
  `FittedParams.input_digest`** (§8b): sha256 over the strictly-pre-
  cutoff match set's `canonical_state()` — parity pinned by (a)'s
  cross-check test, not by shared code (the helper may not be extracted
  without touching the byte-pinned `app/models`).
- `content_hash` is computed at construction under **Phase 5's
  canonicalization style** (§8c) in the package's **own**
  canonicalization module, whose docstring is the spec of record — no
  import crosses the stage boundary and `app/forecasts/
  canonicalization.py` is untouched.
- History-dependent fields are `OptionalValue`s under the domain's
  two-state availability taxonomy (MISSING ⇔ `value is None`); the two
  count fields are plain `int` where 0 is a true exact fact (c).
  Untouched by this stage: `app/forecasts/`, `app/models/`, the storage
  schema, `FORECAST_VERSION`, and every Phase 5 golden. **No storage of
  features this phase** — re-derivation from fixtures by
  `compute_features` suffices; persistence is a future brief's decision.

**(c) Feature inventory and named policies — the versioned spec,
developer-decided 2026-10-19.**
*Statement:* per side, from the team's strictly-pre-cutoff matches in
canonical order; **all prior matches count regardless of competition or
season** (one simple scope, a documented limitation — today's fixtures
are single-competition; a mixed-competition history would blend):

| Field | Definition | Policy constant | MISSING policy |
|---|---|---|---|
| `*_goals_scored_form` | mean goals scored over the team's last `FORM_WINDOW` pre-cutoff matches | `FORM_WINDOW = 5`; `FORM_WINDOW_POLICY = "MISSING_UNTIL_FULL_WINDOW"` | MISSING until the full window exists (0–4 priors); never a partial-window mean |
| `*_goals_conceded_form` | same window, goals conceded | same | same |
| `*_rest_days` | calendar days from the team's most recent **same-season** pre-cutoff match to the fixture date | `REST_DAYS_POLICY = "WITHIN_SEASON"` | MISSING at season start; the cross-season alternative — reporting the ~301-day off-season gap as "rest" — is **rejected as a different quantity** |
| `*_xg_form` | mean xG over the window's **xG-available** matches only | `XG_FORM_POLICY = "MEAN_OVER_AVAILABLE_WITH_N"` | MISSING at `n_xg = 0`; missing xG never participates as 0.0 |
| `*_xg_n` | count of xG-available matches in the window (0..`FORM_WINDOW`) | — | plain `int`, exact fact |
| `*_prior_matches` | count of strictly-pre-cutoff matches (any competition/season) | — | plain `int`, 0 allowed and honest |

*Counts vs estimates:* `xg_n` and `prior_matches` are plain `int`s
because 0 is a true exact fact — no prior matches *is* the count —
never an imputed estimate: estimates are MISSING, counts are facts, and
a zero count is a disclosure, never a fabricated zero-value standing in
for a missing estimate.
*xG estimator honesty:* strict rolling-xG (last `FORM_WINDOW` matches
all carrying xG) measures **0/120** team appearances on this data and
is **NOT shipped** (it would be MISSING everywhere, d). `xg_form` under
`MEAN_OVER_AVAILABLE_WITH_N` is a **different estimator-of-form** —
the mean over the available subset with `n_xg` disclosed — and is
documented as such wherever it appears; it is a different quantity
measured on fewer matches, not a substitute for the strict window.
*Determinism:* identical `(matches, fixture)` ⇒ field-for-field
identical records including `content_hash`; no RNG anywhere in the
package, no wall clock (ISO date arithmetic only), accumulation in
exactly canonical window order at full float precision (no rounding, no
sort-dependent reduction).

**(d) Measured availability — the binding table** (re-derived by real
run over the checked-in fixtures, 2026-10-18; 60 matches, 6 teams × 20,
156 goals, 2024-08-10 → 2025-10-11):

| Quantity | Measured coverage | Feature consequence |
|---|---|---|
| xG present | **10/60** matches (season 2 only; 4 distinct dates) | xG features MISSING for every season-1 fixture |
| Strict last-5-all-xG window | **0/120** team appearances | strict rolling-xG feature **not shipped** (MISSING everywhere) |
| "Immediately prior match had xG" | **20/120** | upper bound on early-window xG usefulness |
| Kickoff | **30/60** (all season 1) | echo only; every stored Forecast fixture MISSING (Phase 5 item 12 dormancy rides) |
| No prior match ever | **6/120** appearances | form/rest/xG MISSING (never 0) |
| No same-season prior | **12/120** appearances | `rest_days` MISSING (WITHIN_SEASON policy) |
| Fewer than `FORM_WINDOW` prior matches | **30/120** appearances (derived) | goals-form MISSING under the default full-window policy |

Every feature declares measured availability; **MISSING propagates
visibly**; the synthetic-data caveat rides every feature (fictional
league, hand-authored fixtures — historical summaries of synthetic
history, never evidence).

**(e) Zero fitted transformers (F2) — a commitment, not a phase.**
*Statement:* every feature is a **pure function of `(matches,
fixture)`** — no scaling, encoding, normalization, or dataset-level
statistics of any kind; team identity is the team-name string (sorted
names, never encoded to integers); nothing is fitted at import time or
call time. Any future fitted transformer must fit **inside the cutoff,
per fixture**, with its fitted state hash-covered on the record —
recorded here as the commitment to how it would be done honestly,
**never built this phase**.

**(f) Data-layer only (F4) — nothing consumes features yet.**
*Statement:* `fit`, `FitConfig`, `MODEL_VERSION`, and `build_forecast`
are unmodified and never consume a feature; no estimator change, no
features-into-fit, no new model, no Elo (a deterministic recursive
summary is at most a feature, never a second forecast source — the
Phase 7 ensembles rule), no feature-selection research (Phase 10's),
and no `app/state/` (stage 3 stays unbuilt per roadmap order; features
compute directly from match history plus domain types, and no
dependency is invented to paper over the order). §3's convergence and
insufficient-data flags ride unchanged on every fit. Vectors are
computed in memory and stored nowhere — no sqlite table, no
serialization, no persistence (`data/` remains not created); the
in-memory `content_hash` is hashing, not storage.

**(g) Honesty — historical summaries, not evidence.**
*Statement:* every field of a `FeatureVector` is a **historical
summary of past matches — not a probability, not a model output, not
evidence** of anything predictive: a rolling mean describes what
happened, nothing more. A well-formed, hash-verified feature vector
demonstrates provenance and determinism only — *normalized ≠ accurate*
(§6) applies to it verbatim. **MISSING propagates visibly and is never
rendered as 0** (constitution prohibition 4): a missing window, a
missing xG record, and a season-opening absence of rest-day history are
reported as MISSING, never smoothed into plausible numbers. Features
are consumed by no forecast, so nothing in the system can currently
emit them as a probability — and any future consumer arrives via its
own brief with its own version and identity implications. The
synthetic-data caveat rides every feature. Until Phases 9/11, no
feature may be described — in code, docs, briefs, or reports — as
validated, accurate, or evidence of predictive value. Nothing here is
betting functionality (constitution prohibition 3).

## 10. Decision analysis (stage 8) — report structure, comparison without collapse, the no-scoring boundary — IMPLEMENTED AND TESTED (authored pre-build, Phase 7; verified 2026-10-19)

Status: **authored BEFORE any Phase 7 build code**, per Phase 7 brief
decision 12 (the Phase 3 §3 / Phase 4 §7 / Phase 5 §8 / Phase 6 §9
pre-build pattern): every constraint below was committed to before a line
of `app/decisions/` could exist — and is now **implemented-and-tested
reality**, verified at the Phase 7 DOCS step against the shipped code
and its acceptance tests (suite 120 passed, clean-env run 2026-10-19),
exactly as §§7–9 were. What shipped matches what was specified: one pure
package `app/decisions/` (`__init__.py`, `constants.py`,
`canonicalization.py` — its own spec of record, no import crosses the
stage boundary — `record.py`, `builder.py`) with the single entry point
`build_decision_report(forecast, *, scenarios=())`; the frozen 28-field
`DecisionReport` plus the nested `ScenarioComparison` and
`ScenarioSpread` records, `content_hash` computed at construction; and
`REPORT_VERSION = "decision-report-v1"` with `DISCLAIMER` as the
package's **exactly two** module-level constants — A6/decision 8
shipped verbatim: no threshold, no knob, no decision rule exists
anywhere in the package. The bindings cited are the Phase 7 brief's
glass-quant rulings A1–A8 (consulted 2026-10-19 at conductor top level;
no-objections recorded) and the developer's recorded answer of 2026-10-19
fixing `REPORT_VERSION = "decision-report-v1"`. Sections 1–9 are
untouched by this section: a report computes nothing of its own — it
renders frozen outputs produced under §§1–8, which bind it without
exception. Flipping this section's status changed no claim below:
"validated" and "accurate" remain banned until Phases 9/11, and the
evaluated observation count remains exactly 0.

Scope: HANDOFF Part IX item 7 (IX-7 — *"Decision analysis — comparison
of model outputs without a silently invented ensemble, disagreement
reported not collapsed"*), delivered as pipeline stage 8 DECISION
ANALYSIS: one new pure package `app/decisions/` with the single entry
point `build_decision_report(forecast, *, scenarios=())`. Nothing below
is a claim about predictive quality — a report is a presentation
structure over §8 forecasts and §7 scenario outputs — and
"validated"/"accurate" remain banned until Phases 9/11 (§6, §7f, §8g).

**(a) What a report IS — a deterministic in-process VIEW of an existing
frozen Forecast; no `matches`, no time parameter, no new leakage surface
(A1/A2).**

*Statement:* the signature is exactly `build_decision_report(forecast,
*, scenarios=())` — **no `matches` argument and no time-like parameter
exists to forget** (the §8a/§9a builder pattern). The report is a
**serialization of an already cutoff-enforced artifact**: the cutoff was
enforced once, inside `build_forecast`, when the Forecast was frozen
(§8a), and a renderer of frozen bytes **cannot see any history at all**
— no matches, no scores, no post-cutoff data — so **no new leakage
surface is opened** (stated explicitly here pre-build per A2; the cheap
poisoned-future byte-identity regression ships anyway). Determinism:
identical `(forecast [, scenarios])` ⇒ field-for-field identical report
including `content_hash`; no RNG, no wall clock, no environment reads.
The record carries its own `REPORT_VERSION = "decision-report-v1"` and
`content_hash` computed at construction under the package's **own**
canonicalization spec of record (no import crosses the stage boundary),
with bump discipline worded identically to §8c: any change to the hashed
field set, the canonicalization spec, or the derivation semantics
requires a `REPORT_VERSION` bump. Provenance chains to the source
forecast through echoed `forecast_version` + `forecast_content_hash`
(alongside the model_version / input_digest / as_of / sample echoes) —
full provenance without re-serializing `FittedParams`.
*Not stored, not served (A5/A8):* the report is generated **in process
and never persisted** — no sqlite table, no `SCHEMA_VERSION` bump, no
API route, no CLI. Ephemerality breaks nothing and pre-scores nothing:
evaluation joins on **forecasts** (frozen, write-once, hashed, pinned —
§8's substrate, already complete), so a deterministic re-derivable view
adds nothing evaluation needs. Persistence or serving arrives only via a
future brief with developer instruction.

**(b) Comparison without collapse — side-by-side labeled hypotheticals,
spread reported, the anti-ensemble clause answered head-on (IX-7; A1).**

*Statement:* scenario comparisons are **labeled hypotheticals presented
side by side with deltas**: each entry echoes its `label` and its
`transforms` verbatim, must be built from **the forecast's own
`FittedParams`** (frozen value equality; a mismatched baseline is
refused with `ValueError`, and duplicate labels are refused too —
ambiguity never averaged, §7g extended), and each probability is the
**analytic** `outcome_probs` of the `scenario_matrix` (§7e — never a
Monte Carlo frequency). **The ONLY cross-scenario aggregation shipped is
min/max/spread** over the entries' analytic probabilities, per outcome;
**a mean is an invented ensemble** and exists nowhere in the records or
their canonical payload. The IX-7 failure mode is answered, not
silenced: **no second independent model exists in this system** (§9f:
no second forecast source, no Elo), so **no cross-model agreement, no
ensemble, and no agreement metric is ever presented** — the fixed
disclaimer says so on every report. "Disagreement" therefore means
exactly two structural components: (i) min/max/spread across labeled
hypotheticals, and (ii) **flag-vs-plausible-number tension** — top-level
flags screaming beside plausible-looking normalized probabilities, both
visible, neither hidden, and never judged by any threshold (c).

**(c) No thresholds, no decision rules — a position, not a default
(A6).**

*Statement:* Phase 7 ships **no threshold and no decision rule of any
kind** — no "flag when P(home) > X", no tuned constant, no auto-tuning,
no threshold optimization. The package's constants module defines
**exactly** `REPORT_VERSION` and `DISCLAIMER`: no numeric knob, and no
rule converting a probability into a decision, exists anywhere in the
package. Two reasons, both structural: such a knob is arbitrary at
best, and choosing it by **fitting on outcomes would leak directly into
Phase 10's protected improvement loop** (HANDOFF stage 10: a tuning loop
protected from evaluating itself on its own tuning data) — one step
from the banned value-detection framing. Consequently the report states
**estimate properties only**: field order shows home, draw, away and
nothing derives a favored side — no argmax, no "most likely", no
pick-shaped field — and each scenario `delta_*` is descriptive
arithmetic between a labeled hypothetical and its own baseline, never
"value".

**(d) Vocabulary contract — estimate / probability / flag / caveat, and
uncertainty as flag echo alone (A4).**

*Statement:* fields say **estimate, probability, flag, caveat** —
nothing else. **Uncertainty is expressed solely by echoing flags** at
top level: `convergence_status`, `insufficient_data`,
`insufficient_teams`, `dropped_mass` — plus the in-sample and synthetic
caveats in the fixed disclaimer (§8e's serving-honesty rule extends
verbatim; `dropped_mass` is §4 truncation disclosure, not an
uncertainty band). **No confidence-interval, standard-error, interval,
or numeric reliability-band field exists anywhere on a report** (§6,
§7a, §8e) — no uncertainty quantification ships with a report, and
`mc_stderr` (**simulation noise only**, §7a) **never enters a report**.
Scenario comparisons are **analytic-only, never Monte Carlo
frequencies** (§7e). Field-name bans: the Phase 5 shared betting-token
list plus `recommendation`, `pick`, `tip`, `advice`; `value` is banned
as a field name only — the `OptionalValue` type name and `.value`
attribute access remain legitimate.

**(e) The no-scoring boundary — evaluated n = 0; evidence begins at
Phases 9/11 (A1/A3; continuity with §6 and §8g).**

*Statement:* Phase 7 performs **zero scoring**: no log loss, no Brier,
no RPS, no hit rate, no calibration, and no baselines — all of those
belong to Phases 9 and 11 — and **the evaluated observation count in
any report is exactly 0**. Until Phases 9/11 run, a report presents
in-sample estimates only and measures nothing. Long-run
home/draw/away frequency baselines are never baked into a report
(§8b). The evaluation substrate is already complete (§8's frozen,
write-once, hashed, pinned forecasts) and **Phase 7 adds nothing
evaluation needs — stated here to kill the temptation to pre-score**;
an AST/token guard over `app/decisions/**` asserts the **absence** of
scoring vocabulary in the package's source, extend-not-weaken (future
scoring terms join that guard, never leave it). Evidence begins at
Phases 9 (chronological backtesting against baselines) and 11 (log
loss, Brier, RPS, calibration against realized results) — §6's and
§8g's boundary applied verbatim to reports.

**(f) Honesty — a view of in-sample estimates, never new evidence
(continuity of §9g).**

*Statement:* **probabilities are estimates, not certainties** (§6):
every number a report presents is an in-sample point estimate echoed at
full precision from the §8 forecast or a §7 labeled hypothetical.
**No pick, recommendation, tip, or advice framing ever**, including
win-probability-as-pick; and nothing here is betting functionality
(constitution prohibition 3): no odds, stakes, EV, Kelly, edge, value,
or wager field or framing. **No accuracy claims:** `validated`,
`accurate`, and `beating` are banned in reports — in code, docs, briefs,
and report contents alike — until Phases 9/11 evidence exists (§6, §7f,
§8g). The fixed **disclaimer rides every report**, stating that the
numbers are in-sample analytic estimates on synthetic fixtures from a
single fitted model, pending chronological evaluation (Phases 9/11),
never evidence of accuracy; that **no second independent model exists
so no cross-model agreement is claimed**; that scenario comparisons are
labeled hypotheticals, side by side, never averaged or ensembled; and
that probabilities are estimates, not certainties. §9g's anchor carries
forward unchanged: *"historical summaries … not evidence"* — **a report
is a view of in-sample estimates rendered from an existing forecast;
rendering adds no evidence of any kind.** A well-formed, hash-verified
report demonstrates provenance and determinism only — *normalized ≠
accurate* (§6) applies verbatim to it — and the **synthetic-data caveat
rides every report** (fictional league, hand-authored fixtures).

*Phase-end verification (2026-10-19, docs step):* every constraint
above is pinned by the shipped Phase 7 acceptance tests (criteria 1–17
in `tests/test_decisions.py`, `tests/test_decisions_scenarios.py`,
`tests/test_phase7_separation.py`; suite 120 passed, clean-env run):
the signature and structurally-absent history surface (a); min/max-only
spread with the arithmetic mean pinned absent from every record and the
canonical payload (b); the exactly-two-names constants module (c); the
vocabulary contract with word-boundary token and field-name scans (d);
the scoring-token guard asserting absence, extend-not-weaken (e); and
the fixed disclaimer plus the version-local golden report content hash
`00929af76bb833b741db5ae038a08913321eed976d775e654c36094009224768`
(f). Reports remain exactly what (a) declares them: in-process,
unstored, deterministic re-derivable views of frozen §8 forecasts.

## 11. Temporal integrity (IX-8) — pre-registrations binding Phases 9 and 11 — IMPLEMENTED AND TESTED (authored pre-build, Phase 8; verified 2026-10-19)

Status: **authored BEFORE any Phase 8 build code**, per Phase 8 brief
decision 3 (the Phase 3 §3 / Phase 4 §7 / Phase 5 §8 / Phase 6 §9 /
Phase 7 §10 pre-build pattern; a fresh section chosen over amending
§8/§9 so those phases' implemented-and-tested records stay untouched):
every pre-registration below was committed to in prose before any Phase 8
test existed and before any Phase 9 or 11 machinery exists — and at the
Phase 8 DOCS step (2026-10-19, suite **133 passed**, clean-env run) this
section was flipped to **implemented-and-tested reality for Phase 8's
own scope**, exactly as §§7–10 were. What that flip means here is
deliberately narrow: **Phase 8 itself ships no statistics** — it is a
tests-and-docs-only phase (zero production code under `app/` — `git
diff 1e1c1ac -- app/` empty, exit 0; no new `app/` package; zero
predictions, zero baselines, zero metrics, zero storage; the evaluated
observation count stays exactly 0, §10e). The temporal-integrity
defenses that guard the discipline below are now **shipped tests**
(`tests/test_temporal_integrity.py`, `tests/test_vocab_guards.py`, plus
the one-line AMENDMENT A1 in `tests/test_phase7_separation.py`), while
the forward contracts (a)–(d) remain **standing pre-registrations** —
binding prose gates for Phases 9 and 11, deliberately NOT built in this
phase (nothing yet exists to build them against: no `app/backtesting/`,
no `app/evaluation/`). The bindings cited are the Phase 8 brief's
glass-quant rulings A0–A9 (consulted 2026-10-19 at conductor top level;
no open developer questions). Sections 1–10 are untouched by this
section. Flipping this section's status changed no claim below.

**The three-step line (A0) — stated here so no phase can blur it:**
Phase 8 = defenses only → Phase 9 = machinery (walk-forward harness,
frozen predictions, baselines — **still no metrics**) → Phase 11 =
first scoring (the evidence gate). **"Phase 8 adds nothing evaluation
needs"** — the evaluation substrate was complete at Phase 5 (frozen,
write-once, hashed forecasts; §8); Phase 8 merely audits it. No metric
of any kind, no baseline, no realized-result join, and no walk-forward
deliverable exists anywhere in this phase.

**(a) Sample-size pre-registrations (A6) — the scored population is
fixed before Phase 11 computes anything.**
*Statement:* the frozen checked-in fixtures contain **exactly 60
matches** — 20 dates × 3 matches per date, 6 teams, 156 goals — **not
120**: 120 counts team-appearances (6 teams × 20 each), and no figure
in this register may say "120 matches". Walk-forward-eligible
**unflagged** fits number **exactly 30 of 60**: the first 30 fixtures
trip at least one §5 insufficient-data flag (all per-team priors fall
below `MIN_MATCHES_PER_TEAM` in the early window), and fixture 1
returns `NO_DATA` (no strictly pre-cutoff history). Ceilings,
registered now: at most **60 predictions**, at most **30 clean**
(unflagged). The **scored population must be PRE-REGISTERED in a brief
before Phase 11 computes any metric**, and evaluation bin counts are
fixed pre-score — no post-hoc regrouping. Variant ranking is
**infeasible** at this n: with ≤ 30 clean observations the per-model
score SE (~0.15–0.25) is at or above the §2d noise floor (~±0.05 log
loss), so no variant difference is resolvable — consequently "beating"
claims stay banned on sample-size grounds **even after Phase 11 runs**.
The synthetic-hand-authored caveat (fictional league, hand-authored
fixtures) and §2e's stationarity caveat ride **every** walk-forward
number. All figures here are pinned to the frozen fixtures: if the
fixtures ever change, every registration in this paragraph is
re-derived by named brief before Phase 9 or 11 relies on it.

**(b) Phase 9 forward contracts (A2) — test-first gate and the single
model spec.**
*Statement:* two commitments bind the Phase 9 brief as gates, not
suggestions: (i) **test-first** — the harness's first acceptance test,
*poison the entire remaining future → every earlier frozen prediction
is byte-identical*, must exist **before the harness may emit any
output**; (ii) the walk-forward harness takes **exactly one model
spec** — no `specs` parameter, no config loop, no best-of-N selection
— so Phase 12/stage-10's protected improvement loop is structurally
unbuildable from this surface (§10c's no-threshold position extended).
Phase 8's runtime nothing-to-tune pin (single `FitConfig` identity,
non-None ridge refused) is now a shipped, test-pinned fact (criterion 8)
and the substrate of (ii).

**(c) Run-manifest contract (A7) — documented now, built in Phase 9.**
*Statement:* each walk-forward run's manifest records: sha256 of every
consumed fixture file; the consumed history's `canonical_state()`
digest; per prediction the fixture's `input_digest` and `content_hash`
(§8 fields, unchanged); `model_version`, the `FitConfig` identity, and
the interpreter/dependency versions. The **run-level digest** is
sha256 over the **ordered** list of `(fixture key, content_hash)`
pairs. **No timestamp and no wall-clock value may appear in any
hashed payload** (S2's no-clock rule, §8c/§8d, extended verbatim to
manifests). Re-running an identical run must reproduce an identical
manifest and run-level digest — that identity **is** the idempotence
proof.

**(d) Storage forward record (A5) — none this phase; the Phase 9/11
inheritance, recorded.**
*Statement:* Phase 9's backtest predictions go through the **existing
write-once forecasts table** — they ARE `Forecast`s (§8), so
`insert_forecast`'s idempotence and identity-collision detection apply
unchanged; baselines (long-run home/draw/away frequencies, computed
from realized results — IX-9/Phase 9's) are **in-process
re-derivable and never stored** (the §10a Phase 7 report pattern); the
evaluation-record table is **Phase 11's** schema bump —
`SCHEMA_VERSION` stays 1 until then. Flagged for the Phase 9 and 11
briefs, **not fixed here**: `get_forecast()` fetches a single row per
natural key (`ORDER BY as_of, input_digest`, single fetch) —
ambiguous once Phase 9 stores many predictions per fixture; those
briefs must address it explicitly.

**(e) Honesty — the boundary carries forward unchanged.**
*Statement:* until Phase 9's machinery runs as specified and Phase 11's
scoring runs against its pre-registered population, evaluated n remains
exactly 0 (§6, §10e), and `validated`/`accurate`/`beating` remain
banned — now additionally on the registered sample-size grounds of (a).
Nothing in this section is betting functionality (constitution
prohibition 3); every Phase 9/11 number remains an estimate carrying
the weaknesses §§2–6 record.

*Phase-end verification (2026-10-19, docs step):* Phase 8's temporal-
integrity defenses are implemented and pinned by the shipped acceptance
tests (criteria 1–13 mapped 1:1 in `tests/test_temporal_integrity.py`
(8) and `tests/test_vocab_guards.py` (5), plus AMENDMENT A1's one-line
segment-boundary fix in `tests/test_phase7_separation.py`, **440 → 440
lines**): the five-entry poison-coverage registry with its AST census
and negative probes — a future history-consuming entry point fails the
suite until it is registered and poisoned (the standing-regression
clause of PLAN §6 layer 4); cutoff-at-source **bit-identity** over
fully unfiltered pools (same-day siblings and future matches included)
for `fit`, `build_forecast`, and `compute_features`; same-day
invisibility pinned as **declared design, never a "fix"**; the
independent snapshot-immutability audit (raw UPDATE/DELETE refusal plus
read-path hash recompute catching a hostile trigger-dropping tamper);
the seedless-by-construction pin (no `random` reference of any spelling
in the history-consuming calculation surface, with positive-control
probes); the nothing-to-tune signature/`FitConfig`/ridge-refusal pin
backing (b); and the hardened vocabulary guards (app-wide strict-
segment scoring scan with the exactly-one pinned honest-negation
allowlist, the accuracy-trio identifier scan, and the
performance/rank/correct/best field-shape bans with the score-vocabulary
negative regression — `score`/`scoreline`/`scored` never banned).
Suite: `env -u PYTEST_ADDOPTS .venv/bin/python -m pytest -q` →
**133 passed** (2026-10-19, clean-env docs run) — 120 prior + 13 new.
Every pre-registration above (a)–(d) now binds Phases 9 and 11 as
standing contract; none of it was consumed, computed, or relaxed this
phase, and the evaluated observation count remains exactly 0.

## 12. Backtesting (IX-9) — baseline definition, scored-population accounting, standing bans — IMPLEMENTED AND TESTED (authored pre-build, Phase 9; verified 2026-10-22)

Status: **authored BEFORE any Phase 9 build code**, per Phase 9 brief
decision 15 and glass-quant ruling A6 (the §3/§7/§8/§9/§10/§11
pre-build pattern; a fresh section appended so §§1–11 stay
byte-identical — this append changes no prior line): every registration
below was committed prose before any `app/backtesting/` module, test, or
baseline number existed — and is now **implemented-and-tested reality**,
verified against the shipped code and its acceptance tests during the
Phase 9 DOCS step (2026-10-22): `app/backtesting/` exists as a pure
package (six modules, 535 lines: `__init__.py`, `constants.py`,
`canonicalization.py`, `record.py`, `baselines.py`, `harness.py`), the
suite is green (**147 passed**, clean-env run), and independent review
passed the phase (**PASS, 2026-10-22, FIRST pass, criteria 1–15**, after
tester PASS ×15). The pre-build authorship is recorded deliberately:
the baseline definition, the scored-population accounting, and the
no-join boundary were fixed in prose before any walk-forward number
could be produced. Phase 9 ships **machinery only**, exactly as
registered — the §11 three-step line now reads Phase 8 defenses
(shipped) → Phase 9 machinery (**shipped, still no metrics**) → Phase 11
first scoring: **no metric of any kind is computed in this phase**, no
model-vs-baseline comparison exists, and the evaluated observation count
stays exactly **0** (§6, §10e, §11e). Shipped surface behind these
registrations: **one public `matches`-parameter function exactly** —
`run_walk_forward` in `app/backtesting/harness.py`, pure (stdlib +
`app.domain` + `app.forecasts` only; **no `app.storage` import** —
persistence is the CALLER's, through the existing write-once
`insert_forecast` into a caller-passed DB; **no committed DB;
`SCHEMA_VERSION` stays 1**); every baseline function underscore-private
in `baselines.py` (the only realized-score consumer, one reviewable
file); the frozen `BaselineRecord`/`RefusalRecord`/`RunManifest`/
`WalkForwardRun` records; `BACKTEST_VERSION =
"backtest-walkforward-v1"` (no knob); and the version-local golden run
digest `150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f`
(derived from the real first run; **re-derive on change, never widen,
never delete**). The registered accounting is now a test-pinned, hand-
audited fact: **60 = 3 + 27 + 30** targets and **57 = 27 + 30**
predictions (criterion 2), nothing silently skipped or dropped.
Declared amendments riding this section's claims (brief pre-sanctioned,
exact figures): **A1** (`tests/test_temporal_integrity.py` poison
registry 5 → 6, `matches` census 3 → 4; **440 → 452** combined with A2),
**A2** (the same file: Phase 8's `app/` byte-pin re-pointed
`1e1c1ac` → `ea92667` and rescoped to the pre-existing packages,
excluding this phase's `app/backtesting`), **A3 + A3'**
(`tests/test_fixtures_and_hygiene.py` **625 → 626** — one
`ALLOWED_APP_IMPORTS` entry with the A3'-corrected self-inclusive value
`{"app.domain", "app.forecasts", "app.backtesting"}` plus the
line-neutral `PURE_PACKAGES` five-set — and the pin-collision class
across four separation files: **833 → 834**, **573 → 574**, **510 →
510**, **440 → 443** for the fifth file A3' found), and **A4**
(`tests/test_health_script.py` valve **300 → 1500 s**, **105 → 105**
lines, after this phase's trip; the sole sanctioned edit ever to
`scripts/health-check.sh` — the determinism-section strip-regex fix
plus the counts-only `UNPARSEABLE` gate — and the 653-line
`tests/test_backtesting.py` accepted as a deviation). All four
amendments and both build-time STOP-and-reports are recorded in
`docs/KNOWN-LIMITATIONS.md` Phase 9.

**(a) Baseline definition — the only legal form (IX-9; quant ruling
A5).** *Definition, verbatim:* a baseline is the **per-fixture,
chronological, pooled long-run home/draw/away frequency** over realized
matches with strictly `date < fixture.date` — **uniform weighting**
(one vote per historical match), **no decay**, **no home/away split**;
each counted match's outcome is decided by goal comparison (H/D/A).
**A full-sample baseline is banned — it leaks the future.** The IX-9
phrase "long-run" is realized as the **cumulative strictly-pre-cutoff
window**: a truly full-sample "long-run" frequency would see the future
and is banned (the IX-9 reconciliation, registered here per brief
decision 7). The **first date's THREE fixtures** get a **MISSING**
baseline: `n = 0`, all three frequencies `None`, status
`MISSING_NO_HISTORY` — **never a fake uniform (⅓, ⅓, ⅓), never a
full-sample fallback**; missing data is a first-class result (HANDOFF
Part V), reported as itself, never filled. The baseline record is
exactly the **triple + `n` + status**, **content-hashed in-process**,
**re-derivable from the matches alone** (independent recomputation is
the check of record), and **NEVER stored** — no column, no table, no
schema surface (`SCHEMA_VERSION` stays 1). Weaknesses ride every
baseline: tiny early `n` (0–3 on the first date), the synthetic
hand-authored fixtures (§6), and §2f's independent-Poisson draw bias,
which makes the draw frequency the baseline the model is structurally
weakest against.

**(b) Scored-population accounting — pre-registered and auditable
(§11(a); quant rulings A1/A10, probes E1/E4).** *Registration,
verbatim, pinned to the frozen checked-in fixtures:* **60 targets = 3
structural refusals + 27 flagged predictions + 30 clean = 57
predictions** — equivalently **57 = 27 + 30** and **60 = 3 + 27 + 30**
— with the accounting **fully auditable**: every target is either a
refusal record or an emitted prediction, nothing is silently skipped or
dropped, and the ceiling **≤ 30 clean** stands (§11(a)). The **3
structural refusals** are exactly the first date's three fixtures: zero
strictly-pre-cutoff history → a `NO_DATA` fit whose team index is empty
(`teams == ()`) → `build_forecast` raises the team-index `ValueError`,
recorded as a **first-class status** (`REFUSED_NO_PRE_CUTOFF_HISTORY`
carrying the original message) — **never a silent skip, never a dropped
target, never replaced by a uniform**. **Flagged** = emitted with a §5
insufficient-data/insufficient-teams flag or `convergence_status !=
CONVERGED`; **clean** = emitted with none. **No metric is computed
against any of it — evaluated n stays exactly 0** after this phase.
Every figure is pinned to the frozen fixtures: a fixture change forces
re-registration by named brief (§11(a)'s rule).

**(c) §11(a)'s standing bans, restated as binding on every Phase 9
walk-forward number.** The scored population is **PRE-REGISTERED** here
— never chosen after the fact; evaluation **bin counts are fixed
pre-score**, with no post-hoc regrouping when Phase 11 computes
anything. **Variant ranking is infeasible** at this n (≤ 30 clean
observations: per-model score SE ~0.15–0.25 against the §2d noise floor
~±0.05), so **"beating" claims stay banned on sample-size grounds EVEN
AFTER Phase 11 runs** — and no model-vs-baseline comparison, reduction,
or ranking of any kind exists at Phase 9 at all. The synthetic-hand-
authored caveat (fictional league, hand-authored fixtures) and §2e's
stationarity caveat **ride every walk-forward number** this phase
emits. Nothing in this section is betting functionality (constitution
prohibition 3); every baseline and forecast remains an estimate
carrying §§2–6's recorded weaknesses.

**(d) The no-join boundary (quant ruling A1, blocker-grade).** At
Phase 9 **no prediction-to-own-outcome join ships**: the one-line
natural-key join is **re-established at Phase 11**, and until then a
join with no consumer would be an unguarded artifact. The
**realized-result surface at Phase 9 is pre-cutoff history ONLY** —
realized matches consumed strictly `date < fixture.date` (fit inputs
and baseline windows) — plus prediction-side counts (targets / refusals
/ flagged / clean) and the per-fixture baseline triple + `n` + status.
Illegal this phase: pairing any prediction field with a realized
field; any model-vs-baseline comparison, reduction, or ranking; any
mean/sum/min/max over outcome-aligned arrays. Evaluated observation n
remains exactly **0** when this phase ends.

**(e) Change control.** **Any later change to the baseline definition
in (a) or the population accounting in (b) — including any fixture
change that would move their figures — is a NAMED BRIEF** (§11(a)'s
re-registration rule extended here to (a) and (b)); no implementation
detail may drift from these registrations silently. Flipping this
section's status changed no registration: §§1–11 remain untouched by
this append.

*Phase-end verification (2026-10-22, docs step):* every constraint above
is pinned by the shipped Phase 9 acceptance tests (criteria 1–12 in
`tests/test_backtesting.py`, criteria 13–14 appended to
`tests/test_vocab_guards.py`, suite 147 passed, clean-env run). (a)
shipped verbatim: per-fixture chronological baselines only, computed by
underscore-private functions in `app/backtesting/baselines.py` —
fixture 4 hand-recomputed at exactly (1/3, 1/3, 1/3) with `n = 3` and
fixture 36 at (15/33, 8/33, 10/33) with `n = 33` by independent test
arithmetic; the `n` sequence over all 60 targets is exactly 0, 0, 0, 3,
3, 3, 6, …, 57; the first date's **three** fixtures carry
`MISSING_NO_HISTORY`, `n = 0`, all frequencies `None` — a fake uniform
(⅓, ⅓, ⅓) and a full-sample fallback are both pinned **absent**
behaviorally; baselines are content-hashed in-process, re-derivable
from the matches alone, and **never stored** (schema introspection
shows no baseline column/table). (b) shipped as registered and now
audited: `n_targets == 60`, `n_refusals == 3` (exactly the first date's
three natural keys, each a `RefusalRecord` with status
`REFUSED_NO_PRE_CUTOFF_HISTORY` and the original `ValueError` message —
first-class, never a skip, never a uniform), `n_flagged == 27`,
`n_clean == 30`, `n_predictions == 57`, `len(predictions) +
len(refusals) == 60`; **no metric is computed against any of it —
evaluated n is exactly 0**. (c)'s bans are **mechanically enforced**:
an AST/token scan over `app/backtesting/**` plus a function-level
co-occurrence scan (a function touching both a `Forecast` field and a
`.score` attribute is flagged; positive controls probe both ways)
asserts zero scoring/comparative vocabulary and **zero
prediction-to-outcome pairing** — (d) is shipped as the absence of the
join itself: `run_walk_forward` never pairs a prediction field with a
realized field, the one-line natural-key join remains re-established at
Phase 11, and the realized-result surface here is pre-cutoff history
only. The test-first poison gate (§11(b)(i), criterion 1) exists and
passes: poisoning the entire remaining future leaves every earlier
prediction field-for-field identical including `content_hash`. The
run-manifest contract (§11(c)) shipped with `run_digest` over the
ordered `(fixture key, content_hash)` list, double-run idempotence at
both the in-process and store levels, and no timestamp anywhere. The
declarations of this section stand: fixture changes force
re-registration by named brief; "validated"/"accurate"/"beating"
remain banned — Phase 9 ran but computed no score, so the evidence gate
is Phase 11's alone, on the pre-registered population.
