"""Analytic scoreline/outcome evaluation for fitted Poisson models.

Pure functions of a FittedParams object (brief decisions 9/10, quant
E1/F1): no cutoff logic, no as_of, no history access — cutoff
discipline lives in ``fit`` alone this phase. Truncated cell matrix to
full precision plus dropped-mass report; home/draw/away from analytic
Poisson tails, exact under any truncation K. These are in-sample
estimates of the fitted model, never evidence of accuracy.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import OUTCOME_TAIL_GOALS
from .params import ConvergenceStatus, FittedParams


@dataclass(frozen=True)
class ScorelineMatrix:
    """Truncated joint scoreline distribution of one fixture.

    ``log_probs[i][j]`` is log P(home = i, away = j) for
    i, j in 0..max_goals, to full floating-point precision (exposed for
    Phase 11's hand-computed goldens). ``dropped_mass`` is the exact
    joint mass outside the truncation, 1 - F_pois(K; lh) * F_pois(K; la)
    — reported, never hidden. The fit's convergence status and
    insufficient-data flags are echoed so downstream can never lose them
    (developer decision 3).
    """

    log_probs: tuple[tuple[float, ...], ...]
    lambda_home: float
    lambda_away: float
    max_goals: int
    dropped_mass: float
    convergence_status: ConvergenceStatus
    insufficient_data: bool
    insufficient_teams: tuple[str, ...]


def _team_index(fitted: FittedParams, team: str) -> int:
    try:
        return fitted.teams.index(team)
    except ValueError:
        raise ValueError(
            f"team {team!r} is not in this fit's teams {fitted.teams!r}"
        ) from None


def _log_pmf(goals: int, log_rate: float, rate: float) -> float:
    """log P(Poisson(rate) = goals) = goals*ln(rate) - rate - ln(goals!).

    ln(goals!) is lgamma(goals + 1); the evaluation order below is the
    documented cell formula and is mirrored character-for-character by
    the golden tests (criterion 9 asserts full precision, no tolerance).
    """
    return goals * log_rate - rate - math.lgamma(goals + 1.0)


def _pmf(goals: int, log_rate: float, rate: float) -> float:
    """P(Poisson(rate) = goals) via the analytic log form."""
    return math.exp(goals * log_rate - rate - math.lgamma(goals + 1.0))


def scoreline_log_probs(
    fitted: FittedParams, home: str, away: str
) -> ScorelineMatrix:
    """Joint scoreline log-probabilities for one fixture (H vs A).

    lambdas from the documented log-linear form, evaluated in formula
    order: lambda_home = exp(mu + alpha_home + beta_away + h),
    lambda_away = exp(mu + alpha_away + beta_home). Cells cover
    0..fitted.config.max_goals per side; dropped mass is reported, and
    outcome probabilities (see ``outcome_probs``) come from analytic
    tails and are unaffected by the truncation.
    """
    home_index = _team_index(fitted, home)
    away_index = _team_index(fitted, away)

    lambda_home = math.exp(
        fitted.mu + fitted.alpha[home_index] + fitted.beta[away_index] + fitted.home_advantage
    )
    lambda_away = math.exp(
        fitted.mu + fitted.alpha[away_index] + fitted.beta[home_index]
    )

    max_goals = fitted.config.max_goals
    log_rate_home = math.log(lambda_home)
    log_rate_away = math.log(lambda_away)
    rows = []
    for i in range(max_goals + 1):
        home_part = i * log_rate_home - lambda_home - math.lgamma(i + 1.0)
        rows.append(
            tuple(
                home_part
                + (j * log_rate_away - lambda_away - math.lgamma(j + 1.0))
                for j in range(max_goals + 1)
            )
        )

    # Exact dropped joint mass: 1 - F_pois(K; lh) * F_pois(K; la), the
    # two CDFs summed ascending in k.
    cdf_home = 0.0
    cdf_away = 0.0
    for k in range(max_goals + 1):
        cdf_home += _pmf(k, log_rate_home, lambda_home)
        cdf_away += _pmf(k, log_rate_away, lambda_away)
    dropped_mass = 1.0 - cdf_home * cdf_away

    return ScorelineMatrix(
        log_probs=tuple(rows),
        lambda_home=lambda_home,
        lambda_away=lambda_away,
        max_goals=max_goals,
        dropped_mass=dropped_mass,
        convergence_status=fitted.convergence_status,
        insufficient_data=fitted.insufficient_data,
        insufficient_teams=fitted.insufficient_teams,
    )


def outcome_probs(matrix: ScorelineMatrix) -> tuple[float, float, float]:
    """(p_home, p_draw, p_away) in H > D > A order, exact under truncation.

    Analytic Poisson tails summed to the fixed OUTCOME_TAIL_GOALS bound
    (independent of the matrix's max_goals, so two matrices of the same
    fitted params but different K yield byte-identical triples):

        p_draw = sum_k        pmf(k; lh) * pmf(k; la)
        p_home = sum_y        pmf(y; la) * (1 - F_h(y))
        p_away = sum_x        pmf(x; lh) * (1 - F_a(x))

    with F accumulated ascending so F(k) = P(X <= k) at each step. The
    unsummed remainder is P(min(X,Y) > bound), far below
    PROB_SUM_EPSILON for any fixture-scale lambda.
    """
    log_rate_home = math.log(matrix.lambda_home)
    log_rate_away = math.log(matrix.lambda_away)
    cdf_home = 0.0
    cdf_away = 0.0
    p_home = 0.0
    p_draw = 0.0
    p_away = 0.0
    for k in range(OUTCOME_TAIL_GOALS + 1):
        pmf_home = _pmf(k, log_rate_home, matrix.lambda_home)
        pmf_away = _pmf(k, log_rate_away, matrix.lambda_away)
        cdf_home += pmf_home
        cdf_away += pmf_away
        p_draw += pmf_home * pmf_away
        p_home += pmf_away * (1.0 - cdf_home)
        p_away += pmf_home * (1.0 - cdf_away)
    return (p_home, p_draw, p_away)


__all__ = ["ScorelineMatrix", "outcome_probs", "scoreline_log_probs"]
