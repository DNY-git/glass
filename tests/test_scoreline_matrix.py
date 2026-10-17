"""Phase 3 acceptance criteria 9-12: the analytic scoreline evaluator.

Hand-derived golden values at full precision (no tolerance — a ulp-level
mismatch means re-deriving, never widening), the dropped-mass report,
outcome probabilities from analytic Poisson tails (exact under any
truncation K), and the pure (fitted, home, away) / (matrix) API shape
with no cutoff parameter to forget.
"""

from __future__ import annotations

import dataclasses
import inspect
import math
from pathlib import Path

from app.domain import MatchCollection
from app.ingestion import import_fixture
from app.models import (
    MAX_GOALS,
    MODEL_VERSION,
    OUTCOME_TAIL_GOALS,
    PROB_SUM_EPSILON,
    ConvergenceStatus,
    FitConfig,
    FittedParams,
    PoolingRecord,
    SampleSize,
    fit,
    outcome_probs,
    scoreline_log_probs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

FULL_AS_OF = "2025-12-31"


def hand_fitted(
    mu: float = 0.25,
    home_advantage: float = 0.15,
    alpha: tuple[float, ...] = (0.2, -0.2),
    beta: tuple[float, ...] = (0.1, -0.1),
) -> FittedParams:
    """A hand-constructed FittedParams with known parameters (criterion 9).

    Teams are fictional and sorted; the provenance fields are plausible
    test values — only (mu, alpha, beta, h) drive the lambdas.
    """
    sample = SampleSize(matches=2, goals=3)
    return FittedParams(
        model_version=MODEL_VERSION,
        config=FitConfig(),  # max_goals = MAX_GOALS = 10
        pooling=PoolingRecord(
            competition="Test Cup",
            seasons=("2024-25",),
            as_of="2025-01-01",
            sample_size=sample,
        ),
        input_digest="0" * 64,
        teams=("Ashford City", "Brookton United"),
        mu=mu,
        home_advantage=home_advantage,
        alpha=alpha,
        beta=beta,
        iterations=5,
        convergence_status=ConvergenceStatus.CONVERGED,
        sample_size=sample,
        insufficient_data=False,
        insufficient_teams=(),
    )


def fixture_fit() -> FittedParams:
    """The real fixture pool fitted at full history."""
    collection = MatchCollection()
    import_fixture(FIXTURES / "season-1.json", collection)
    import_fixture(FIXTURES / "season-2.json", collection)
    return fit([record.match for record in collection.records()], FULL_AS_OF)


def test_scoreline_log_probs_golden_values() -> None:
    # Criterion 9: hand-constructed parameters give hand-verified
    # lambdas and hand-derived cells, asserted at FULL precision.
    # Derivation (docs/STATISTICAL-ASSUMPTIONS.md section 4):
    #   log P(i, j) = i*ln(lh) - lh - ln(i!) + j*ln(la) - la - ln(j!)
    # with ln(n!) = lgamma(n + 1), the same standard-library function
    # the implementation evaluates, in the same left-to-right order,
    # so `==` is exact rather than tolerant.
    fitted = hand_fitted()
    matrix = scoreline_log_probs(fitted, "Ashford City", "Brookton United")

    # lambda_home = exp(mu + alpha_home + beta_away + h)
    #             = exp(0.25 + 0.2 + (-0.1) + 0.15) = exp(0.5)
    expected_home = math.exp(fitted.mu + fitted.alpha[0] + fitted.beta[1] + fitted.home_advantage)
    # lambda_away = exp(mu + alpha_away + beta_home) = exp(0.25 + (-0.2) + 0.1)
    expected_away = math.exp(fitted.mu + fitted.alpha[1] + fitted.beta[0])
    assert matrix.lambda_home == expected_home
    assert matrix.lambda_away == expected_away

    # The matrix is (K+1) x (K+1) with K = MAX_GOALS.
    assert matrix.max_goals == MAX_GOALS == 10
    assert len(matrix.log_probs) == MAX_GOALS + 1
    assert all(len(row) == MAX_GOALS + 1 for row in matrix.log_probs)

    log_rate_home = math.log(matrix.lambda_home)
    log_rate_away = math.log(matrix.lambda_away)

    # Cell (0, 0): 0*ln(lh) - lh - ln(0!) + 0*ln(la) - la - ln(0!)
    assert matrix.log_probs[0][0] == (
        (0 * log_rate_home - matrix.lambda_home - math.lgamma(1.0))
        + (0 * log_rate_away - matrix.lambda_away - math.lgamma(1.0))
    )
    # Cell (1, 0): ln(lh) - lh - 0 + 0 - la - 0
    assert matrix.log_probs[1][0] == (
        (1 * log_rate_home - matrix.lambda_home - math.lgamma(2.0))
        + (0 * log_rate_away - matrix.lambda_away - math.lgamma(1.0))
    )
    # Cell (0, 1): symmetric — 0 - lh - 0 + ln(la) - la - 0
    assert matrix.log_probs[0][1] == (
        (0 * log_rate_home - matrix.lambda_home - math.lgamma(1.0))
        + (1 * log_rate_away - matrix.lambda_away - math.lgamma(2.0))
    )
    # Cell (2, 1): 2*ln(lh) - lh - ln(2!) + ln(la) - la - 0
    assert matrix.log_probs[2][1] == (
        (2 * log_rate_home - matrix.lambda_home - math.lgamma(3.0))
        + (1 * log_rate_away - matrix.lambda_away - math.lgamma(2.0))
    )
    # Cell (1, 2): ln(lh) - lh - 0 + 2*ln(la) - la - ln(2!)
    assert matrix.log_probs[1][2] == (
        (1 * log_rate_home - matrix.lambda_home - math.lgamma(2.0))
        + (2 * log_rate_away - matrix.lambda_away - math.lgamma(3.0))
    )


def test_outcome_probs_golden_and_normalizes() -> None:
    # Criterion 10: the outcome triple equals a hand-derived golden at
    # full precision, normalizes within PROB_SUM_EPSILON, and the
    # H > D > A tuple order is semantic: position 0 is the home-win
    # probability, 1 the draw, 2 the away-win.
    fitted = hand_fitted()
    matrix = scoreline_log_probs(fitted, "Ashford City", "Brookton United")
    outcome = outcome_probs(matrix)

    # Independent golden derivation (mirrors the documented analytic
    # tails, summing to the documented OUTCOME_TAIL_GOALS bound — the
    # unsummed remainder is P(min(X,Y) > 128), astronomically below
    # PROB_SUM_EPSILON at these lambdas):
    #   p_draw = sum_k pmf(k; lh) * pmf(k; la)
    #   p_home = sum_y pmf(y; la) * (1 - F_h(y)), F_h(y) = P(X <= y)
    #   p_away = sum_x pmf(x; lh) * (1 - F_a(x))
    lh, la = matrix.lambda_home, matrix.lambda_away
    log_lh, log_la = math.log(lh), math.log(la)
    cdf_home = cdf_away = 0.0
    p_home = p_draw = p_away = 0.0
    for k in range(OUTCOME_TAIL_GOALS + 1):
        pmf_home = math.exp(k * log_lh - lh - math.lgamma(k + 1.0))
        pmf_away = math.exp(k * log_la - la - math.lgamma(k + 1.0))
        cdf_home += pmf_home
        cdf_away += pmf_away
        p_draw += pmf_home * pmf_away
        p_home += pmf_away * (1.0 - cdf_home)
        p_away += pmf_home * (1.0 - cdf_away)
    assert outcome == (p_home, p_draw, p_away)

    assert abs(sum(outcome) - 1.0) <= PROB_SUM_EPSILON

    # Lopsided construction: a huge home attack/advantage against a
    # tiny away threat. Semantics of the tuple order: outcome[0] is
    # P(home > away) and must dominate; outcome[1] the draw (both sides
    # equal); outcome[2] P(away > home), the smallest here.
    lopsided = hand_fitted(
        home_advantage=0.5,
        alpha=(1.5, -1.5),
        beta=(-0.5, 0.5),
    )
    lob_outcome = outcome_probs(
        scoreline_log_probs(lopsided, "Ashford City", "Brookton United")
    )
    assert lob_outcome[0] > lob_outcome[1] > lob_outcome[2]
    assert lob_outcome[0] > 0.9  # the lopsided home side practically always wins
    assert abs(sum(lob_outcome) - 1.0) <= PROB_SUM_EPSILON


def test_dropped_mass_reported_and_outcomes_exact_under_truncation() -> None:
    # Criterion 11: dropped_mass is the hand-computed exact
    # 1 - F_pois(K; lh) * F_pois(K; la) at full precision, within the
    # documented bound for the shipped K; and W/D/L come from analytic
    # tails, so two truncations of the SAME fitted params yield
    # byte-identical outcome triples while matrices and dropped masses
    # differ (docs/STATISTICAL-ASSUMPTIONS.md section 4).
    fitted = fixture_fit()
    teams = fitted.teams
    matrix_10 = scoreline_log_probs(fitted, teams[0], teams[1])

    def hand_dropped_mass(matrix) -> float:
        # F_pois(K; lambda) accumulated ascending in k, then 1 - Fh * Fa.
        log_lh, log_la = math.log(matrix.lambda_home), math.log(matrix.lambda_away)
        cdf_home = cdf_away = 0.0
        for k in range(matrix.max_goals + 1):
            cdf_home += math.exp(k * log_lh - matrix.lambda_home - math.lgamma(k + 1.0))
            cdf_away += math.exp(k * log_la - matrix.lambda_away - math.lgamma(k + 1.0))
        return 1.0 - cdf_home * cdf_away

    assert matrix_10.dropped_mass == hand_dropped_mass(matrix_10)
    assert 0.0 < matrix_10.dropped_mass <= 6e-4  # documented K=10 bound

    # The SAME fitted params, evaluated with K = 15 (only the echoed
    # config's truncation changes; estimation is unaffected by it).
    fitted_15 = dataclasses.replace(
        fitted, config=dataclasses.replace(fitted.config, max_goals=15)
    )
    matrix_15 = scoreline_log_probs(fitted_15, teams[0], teams[1])
    assert matrix_15.dropped_mass == hand_dropped_mass(matrix_15)
    assert 0.0 < matrix_15.dropped_mass <= 1.2e-7  # documented K=15 bound
    assert matrix_15.dropped_mass < matrix_10.dropped_mass

    # Matrices differ (shape and dropped mass) ...
    assert len(matrix_10.log_probs) == 11
    assert len(matrix_15.log_probs) == 16
    assert matrix_10.dropped_mass != matrix_15.dropped_mass
    # ... but the outcome triples are byte-identical: exact under any
    # truncation.
    outcome_10 = outcome_probs(matrix_10)
    outcome_15 = outcome_probs(matrix_15)
    assert outcome_10 == outcome_15
    assert repr(outcome_10) == repr(outcome_15)


def test_pure_evaluator_api_no_cutoff_logic() -> None:
    # Criterion 12: the evaluator signatures are exactly (fitted, home,
    # away) and (matrix) — there is no as_of / cutoff / history
    # parameter to forget; cutoff discipline lives in `fit` alone this
    # phase. Raw log-probability cells are exposed (not only
    # probabilities) for Phase 11's hand-computed goldens, and equal
    # inputs give bit-identical outputs.
    signature = inspect.signature(scoreline_log_probs)
    parameters = list(signature.parameters.values())
    assert [p.name for p in parameters] == ["fitted", "home", "away"]
    assert all(
        p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in parameters
    )
    assert not any(
        "as_of" in p.name or "cutoff" in p.name or "history" in p.name
        for p in signature.parameters.values()
    )

    outcome_signature = inspect.signature(outcome_probs)
    outcome_parameters = list(outcome_signature.parameters.values())
    assert [p.name for p in outcome_parameters] == ["matrix"]
    assert outcome_parameters[0].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD

    fitted = hand_fitted()
    first = scoreline_log_probs(fitted, "Ashford City", "Brookton United")
    assert isinstance(first.log_probs, tuple)
    assert isinstance(first.log_probs[0], tuple)
    assert isinstance(first.log_probs[0][0], float)

    second = scoreline_log_probs(fitted, "Ashford City", "Brookton United")
    assert first == second  # frozen dataclass, bit-identical floats
    assert first.log_probs == second.log_probs
    assert repr(first) == repr(second)
    assert outcome_probs(first) == outcome_probs(second)
