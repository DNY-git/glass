# STATISTICAL ASSUMPTIONS — SPORTS LOOKING GLASS

Status: authored **before any Phase 3 build code** per quant ruling A1
(Phase 3 brief, DOCS step); Phase 3 then built `app/models/` to this
register, and independent review passed it (PASS, 2026-10-16, after 1
fix cycle) — the checkpoint commit that records the phase as official
comes immediately after this docs step. Sections 1, 3, 4, and 5 now
describe **implemented, tested behavior** of `app/models/` (verified
against the code and its acceptance tests during Phase 3 docs work);
§2's "what will test it" entries name Phases 9 and 11, which **have not
run** — they are commitments, not results. This register is the honest
statement of the model's assumptions and their weaknesses, kept
coordinated with `docs/KNOWN-LIMITATIONS.md` and any quant advisories.

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
