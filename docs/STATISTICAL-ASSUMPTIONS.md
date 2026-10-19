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
