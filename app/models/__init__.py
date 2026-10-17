"""Statistical models (pipeline stage 5): Poisson goal model, pure stdlib.

Fits attack/defence strengths and an estimated home-advantage term by
unpenalized maximum likelihood on strictly pre-cutoff history, and
evaluates analytic scoreline/outcome distributions. No storage, no HTTP,
no randomness, no wall clock (enforced by tests/test_model_separation.py).
Every number produced here is an in-sample estimate — see
docs/STATISTICAL-ASSUMPTIONS.md — never evidence of accuracy.
"""

from .constants import (
    DAMPING,
    MAX_GOALS,
    MAX_ITERATIONS,
    MIN_MATCHES_PER_TEAM,
    MIN_TOTAL_GOALS,
    MIN_TOTAL_MATCHES,
    MODEL_VERSION,
    NEWTON_TOL,
    OUTCOME_TAIL_GOALS,
    PROB_SUM_EPSILON,
    SUM_TO_ZERO_EPSILON,
)
from .params import (
    ConvergenceStatus,
    FitConfig,
    FittedParams,
    PoolingRecord,
    SampleSize,
)
from .poisson import fit
from .scoreline import ScorelineMatrix, outcome_probs, scoreline_log_probs

__all__ = [
    "DAMPING",
    "MAX_GOALS",
    "MAX_ITERATIONS",
    "MIN_MATCHES_PER_TEAM",
    "MIN_TOTAL_GOALS",
    "MIN_TOTAL_MATCHES",
    "MODEL_VERSION",
    "NEWTON_TOL",
    "OUTCOME_TAIL_GOALS",
    "PROB_SUM_EPSILON",
    "SUM_TO_ZERO_EPSILON",
    "ConvergenceStatus",
    "FitConfig",
    "FittedParams",
    "PoolingRecord",
    "SampleSize",
    "ScorelineMatrix",
    "fit",
    "outcome_probs",
    "scoreline_log_probs",
]
