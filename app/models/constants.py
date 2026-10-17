"""Named constants for the Phase 3 Poisson goal model (poisson-mle-v1).

Every constant here is echoed in each fit's config/provenance record
(brief decisions 2, 5, 8) or bounds a documented numerical trade-off.
Nothing in this module is environment-derived: the values are source
constants, identical on every run (determinism, HANDOFF Part V).

Plain module-level assignments (not class namespaces) are deliberate:
the Phase 3 criterion-13 AST scan expects constants to be literal
bindings; each carries a comment saying why it exists and what it
bounds, which is the closest a Python constant gets to a docstring.
"""

# Model version string stamped onto every FittedParams; identifies the
# model form + estimator in provenance (brief decision 5). Bump only
# with a new model version per the versioning discipline.
MODEL_VERSION = "poisson-mle-v1"

# Newton-Raphson convergence threshold on the infinity norm of the
# applied update step. Below 1e-10 the likelihood (concave, quadratic
# near the optimum) cannot move materially at fixture scale; echoed in
# every fit's config (brief decision 2, quant B2).
NEWTON_TOL = 1e-10

# Hard cap on Newton steps. A non-converged fit within this cap is a
# reported result (convergence_status MAX_ITERATIONS), never a silent
# retry loop (brief decision 6, quant D2).
MAX_ITERATIONS = 100

# Step scale for the Newton update: 1.0 means the full Newton step.
# No backtracking/line search ships this phase; the exact implemented
# step rule is documented in docs/STATISTICAL-ASSUMPTIONS.md section 3
# (brief decision 2).
DAMPING = 1.0

# Scoreline truncation bound K: cells log P(i, j) are computed for
# i, j in 0..K, giving a (K+1)x(K+1) matrix. At fixture-fitted lambdas
# K=10 drops at most ~6e-4 of joint probability mass; the matrix always
# reports its exact dropped mass, and outcome probabilities come from
# analytic Poisson tails so they are exact under any K (brief decision
# 9, docs/STATISTICAL-ASSUMPTIONS.md section 4).
MAX_GOALS = 10

# Outcome triple (p_home, p_draw, p_away) must sum to 1 within this
# tolerance. The three probabilities are independent tail sums, so the
# sum deviates from 1 only by the doubly-truncated tail beyond
# OUTCOME_TAIL_GOALS, which is astronomically smaller than this bound
# at any fixture-scale lambda (brief decision 9).
PROB_SUM_EPSILON = 1e-12

# Sum-to-zero identifiability check: sum(alpha) and sum(beta) must each
# be within this tolerance of 0 on every returned fit (brief decision
# 1, docs/STATISTICAL-ASSUMPTIONS.md section 1).
SUM_TO_ZERO_EPSILON = 1e-6

# Insufficient-data thresholds (brief decision 11, quant-approved
# values): a team with fewer pre-cutoff matches than this is flagged
# per-team; below MIN_TOTAL_MATCHES pre-cutoff matches or MIN_TOTAL_GOALS
# pre-cutoff goals the whole fit is flagged insufficient_data. The full
# fixture pool (60 matches, 156 goals, 20 matches per team) passes all
# three; a first-matchday cutoff trips all three. Flags attach to the
# fitted output and are never hidden.
MIN_MATCHES_PER_TEAM = 10
MIN_TOTAL_MATCHES = 20
MIN_TOTAL_GOALS = 60

# Upper summation bound for the analytic outcome tail sums (home/draw/
# away): p_draw = sum_k pmf(k;lh)*pmf(k;la), p_home = sum_y pmf(y;la)*
# (1 - F_h(y)), p_away likewise, all with k, y in 0..OUTCOME_TAIL_GOALS.
# This bound is independent of MAX_GOALS on purpose: outcomes must be
# byte-identical across different truncations K (brief decision 9,
# criterion 11). At 128 the residual P(min(X,Y) > 128) is below 1e-100
# for any fixture-scale lambda, far under PROB_SUM_EPSILON.
OUTCOME_TAIL_GOALS = 128
