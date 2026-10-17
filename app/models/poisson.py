"""Poisson goal model: unpenalized MLE by Newton-Raphson (stage 5).

Model form (docs/STATISTICAL-ASSUMPTIONS.md section 1, quant B1):

    lambda_home = exp(mu + alpha_home + beta_away + h)
    lambda_away = exp(mu + alpha_away + beta_home)

with sum-to-zero identifiability on alpha and beta and a single shared,
estimated home-advantage log-term h. Home and away goals of a match are
independent Poisson draws given the parameters.

Estimator (quant B2): Newton-Raphson on the concave log-likelihood with
analytic score and observed information (no numerical differentiation),
and a hand-rolled dense Gaussian elimination with partial pivoting — no
fixed-point/IPF (quant measured it divergent), no numpy/scipy. The
sum-to-zero constraints are exact: alpha/beta for the last team in
sorted order is defined as minus the sum of the free ones, so the
reduced parameterization is unconstrained and every iterate (and the
returned fit) satisfies sum(alpha) = sum(beta) = 0.

Imports: standard library + app.domain only; no storage, no HTTP, no
filesystem, no randomness, no wall clock, no environment reads
(enforced structurally by tests/test_model_separation.py). Cutoff
discipline lives here: ``fit`` filters strictly ``date < as_of`` inside
the function itself, so a caller that forgets to filter still cannot
leak future data (constitution, HANDOFF Part V).
"""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, Sequence

from app.domain import (
    IngestedRecord,
    Match,
    MatchCollection,
    Provenance,
    RecordLocation,
    canonical_state,
)

from .constants import (
    MIN_MATCHES_PER_TEAM,
    MIN_TOTAL_GOALS,
    MIN_TOTAL_MATCHES,
    MODEL_VERSION,
)
from .params import (
    ConvergenceStatus,
    FitConfig,
    FittedParams,
    PoolingRecord,
    SampleSize,
)

# Pivot threshold for the hand-rolled solver, relative to the largest
# entry of the system matrix: a pivot below 1e-12 * ||I||_max means the
# observed-information matrix is numerically singular (thin pre-cutoff
# history: the likelihood then depends on fewer independent linear
# combinations of the 12 parameters than there are parameters). Such a
# solve is refused and reported as SINGULAR_SYSTEM — never dressed up as
# a converged fit, never silently regularized. Well-conditioned fixture
# systems have pivot ratios of order 1, so this threshold cannot fire
# on healthy data.
_PIVOT_RATIO_EPSILON = 1e-12


class _SingularSystem(Exception):
    """Internal signal: the Newton system is singular or non-finite.

    Private to this module; ``fit`` converts it into the reported
    convergence_status SINGULAR_SYSTEM. It never escapes as a crash.
    """


def _pre_cutoff_matches(matches: Iterable[Match], as_of: str) -> tuple[Match, ...]:
    """Strictly pre-cutoff history, in Phase 2 canonical order.

    The cutoff is enforced HERE, inside the calculation: only matches
    with date < as_of (strictly; a match dated exactly at the cutoff is
    refused) enter the likelihood. Dates are ISO calendar strings
    (validated at ingestion), so lexicographic order is chronological
    order. The canonical sort (date, competition, season, home, away)
    makes iteration order independent of input order — shuffled input
    yields bit-identical fits (brief decision 7, criterion 3).
    """
    pre = [match for match in matches if match.date < as_of]
    pre.sort(key=lambda match: match.canonical_sort_key)
    return tuple(pre)


def _input_digest(pre: Sequence[Match]) -> str:
    """sha256 of the pre-cutoff set's canonical_state() (brief decision 5).

    Reuses the Phase 2 canonical serialization byte-for-byte, so the
    digest is deterministic, path-free and timestamp-free, and identical
    for any input ordering. MatchCollection's public API takes
    IngestedRecords, whose provenance/location are deliberately excluded
    from canonical_state (app/domain/collection.py: provenance is
    environment-derived metadata, not match state); the neutral carrier
    values below therefore cannot influence the digest and never leave
    this function.
    """
    collection = MatchCollection()
    for index, match in enumerate(pre):
        collection.add(
            IngestedRecord(
                match=match,
                provenance=Provenance(source_path="", sha256=""),
                location=RecordLocation(source_path="", index=index),
            )
        )
    return hashlib.sha256(canonical_state(collection).encode("utf-8")).hexdigest()


def _newton_solve(matrix: Sequence[Sequence[float]], rhs: Sequence[float]) -> list[float]:
    """Dense solve of matrix @ x = rhs by Gaussian elimination with
    partial pivoting (systems <= ~12x12 at fixture scale; stdlib only).

    Raises _SingularSystem if the largest entry found at any pivot
    position is below _PIVOT_RATIO_EPSILON times the matrix's global
    largest entry, i.e. the system is numerically singular — reported
    upstream as a flag, never a crash dressed as success.
    """
    n = len(rhs)
    scale = max((abs(value) for row in matrix for value in row), default=0.0)
    if scale == 0.0:
        raise _SingularSystem("zero system matrix")
    threshold = _PIVOT_RATIO_EPSILON * scale
    # Augmented working copy; original matrix untouched.
    work = [list(row) + [rhs[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(work[r][col]))
        pivot = work[pivot_row][col]
        if abs(pivot) <= threshold:
            raise _SingularSystem(f"singular pivot at column {col}")
        if pivot_row != col:
            work[col], work[pivot_row] = work[pivot_row], work[col]
        pivot = work[col][col]
        for row in range(col + 1, n):
            factor = work[row][col] / pivot
            if factor != 0.0:
                for c in range(col, n + 1):
                    work[row][c] -= factor * work[col][c]
    # Back substitution.
    solution = [0.0] * n
    for row in range(n - 1, -1, -1):
        accumulator = work[row][n]
        for c in range(row + 1, n):
            accumulator -= work[row][c] * solution[c]
        solution[row] = accumulator / work[row][row]
    return solution


# One sparse loading pattern: (parameter index, loading) pairs. For a
# match the log-rate of each side is a 0/+-1 combination of the free
# parameters, with the dropped (sum-to-zero) team contributing -1 to
# every free alpha/beta slot.
def _loadings(teams_size: int, home_index: int, away_index: int) -> tuple[
    tuple[tuple[int, float], ...], tuple[tuple[int, float], ...]
]:
    """Loading pairs (home term, away term) for one match.

    Parameter layout: [mu, free_alpha..., free_beta..., h]. The last
    team in sorted order (index teams_size - 1) has no free slot; its
    alpha/beta equal minus the sum of the free ones, so whenever that
    team appears, every free slot of the corresponding block gets -1.
    Pair order is mu, alpha slots ascending, beta slots ascending, h —
    deterministic by construction.
    """
    dropped = teams_size - 1
    alpha_base = 1
    beta_base = 1 + (teams_size - 1)

    def block(base: int, team_index: int) -> tuple[tuple[int, float], ...]:
        if team_index == dropped:
            return tuple((base + k, -1.0) for k in range(teams_size - 1))
        return ((base + team_index, 1.0),)

    home_pairs = (
        ((0, 1.0),)
        + block(alpha_base, home_index)
        + block(beta_base, away_index)
        + ((2 * teams_size - 1, 1.0),)  # h is the last parameter slot
    )
    away_pairs = ((0, 1.0),) + block(alpha_base, away_index) + block(beta_base, home_index)
    return home_pairs, away_pairs


def _score_and_information(
    theta: Sequence[float],
    observations: Sequence[tuple[tuple[tuple[int, float], ...], tuple[tuple[int, float], ...], int, int]],
) -> tuple[list[float], list[list[float]]]:
    """Analytic score g and observed information I of the log-likelihood.

    For a term with log-rate eta = theta . loadings, goals y and rate
    w = exp(eta): dL/deta = y - w, d2L/deta2 = -w; the chain rule over
    the loadings gives g += (y - w) * loadings and I += w * loadings
    x loadings (the observed information is positive semi-definite, so
    the Newton system is I @ step = g). Iteration order over terms and
    loadings is fixed — bit-identical on every run.
    """
    n_params = len(theta)
    gradient = [0.0] * n_params
    information = [[0.0] * n_params for _ in range(n_params)]
    for home_pairs, away_pairs, home_goals, away_goals in observations:
        for pairs, goals in ((home_pairs, home_goals), (away_pairs, away_goals)):
            eta = 0.0
            for index, loading in pairs:
                eta += loading * theta[index]
            try:
                rate = math.exp(eta)
            except OverflowError as error:  # pragma: no cover - defensive
                raise _SingularSystem("non-finite Poisson rate") from error
            residual = goals - rate
            for index, loading in pairs:
                gradient[index] += residual * loading
            for index_i, loading_i in pairs:
                for index_j, loading_j in pairs:
                    information[index_i][index_j] += rate * loading_i * loading_j
    return gradient, information


def fit(
    matches: Iterable[Match],
    as_of: str,
    *,
    config: FitConfig | None = None,
) -> FittedParams:
    """Fit the Poisson goal model on strictly pre-cutoff history.

    Only matches with ``date < as_of`` (strictly before the cutoff; a
    match dated exactly at the cutoff is refused) enter the likelihood —
    the filter lives inside this function, not at any call site
    (constitution, HANDOFF Part V). Parameters are a pure function of
    the arguments: no module-level fitted state, no cache, no
    randomness, no wall clock (quant G1, brief decision 7).

    A non-converged fit is a **reported result**: the returned object
    always carries ``convergence_status`` (CONVERGED, MAX_ITERATIONS,
    SINGULAR_SYSTEM or NO_DATA) and, where relevant, the insufficient-
    data flags; no parameter vector is ever emitted without its status
    (quant B2/D2). The returned numbers are in-sample estimates, never
    evidence of accuracy (docs/STATISTICAL-ASSUMPTIONS.md section 6).
    """
    if config is None:
        config = FitConfig()
    if config.ridge is not None:
        raise ValueError(
            "poisson-mle-v1 is unpenalized: FitConfig.ridge must be None "
            "(shrinkage is not implemented; no silent shrinkage, ever)"
        )

    pre = _pre_cutoff_matches(matches, as_of)
    digest = _input_digest(pre)

    total_goals = sum(match.score.home + match.score.away for match in pre)
    sample_size = SampleSize(matches=len(pre), goals=total_goals)

    teams = sorted(
        {team for match in pre for team in (match.home, match.away)}
    )
    team_position = {team: index for index, team in enumerate(teams)}

    counts = {team: 0 for team in teams}
    for match in pre:
        counts[match.home] += 1
        counts[match.away] += 1
    insufficient_teams = tuple(
        team for team in teams if counts[team] < MIN_MATCHES_PER_TEAM
    )
    insufficient_data = (
        sample_size.matches < MIN_TOTAL_MATCHES
        or sample_size.goals < MIN_TOTAL_GOALS
        or bool(insufficient_teams)
    )

    seasons = sorted({match.season for match in pre})
    competitions = sorted({match.competition for match in pre})
    pooling = PoolingRecord(
        competition=", ".join(competitions),
        seasons=tuple(seasons),
        as_of=as_of,
        sample_size=sample_size,
    )

    def build(
        theta: Sequence[float], iterations: int, status: ConvergenceStatus
    ) -> FittedParams:
        # Expand the reduced coordinates back to full sum-to-zero vectors:
        # the dropped team's strength is minus the sum of the free ones.
        if teams:
            alpha_free = list(theta[1 : 1 + len(teams) - 1])
            beta_free = list(theta[1 + len(teams) - 1 : 1 + 2 * (len(teams) - 1)])
            alpha = tuple(alpha_free + [-sum(alpha_free)])
            beta = tuple(beta_free + [-sum(beta_free)])
        else:
            alpha = ()
            beta = ()
        return FittedParams(
            model_version=MODEL_VERSION,
            config=config,
            pooling=pooling,
            input_digest=digest,
            teams=tuple(teams),
            mu=theta[0],
            home_advantage=theta[-1],
            alpha=alpha,
            beta=beta,
            iterations=iterations,
            convergence_status=status,
            sample_size=sample_size,
            insufficient_data=insufficient_data,
            insufficient_teams=insufficient_teams,
        )

    if not pre or len(teams) < 2:
        # Nothing (or almost nothing) to estimate: a well-formed,
        # flagged object — insufficiency is reported, not crashed on.
        n_free = max(len(teams) - 1, 0)
        return build([0.0] * (2 + 2 * n_free), 0, ConvergenceStatus.NO_DATA)

    n_free = len(teams) - 1
    observations = [
        (
            *_loadings(len(teams), team_position[match.home], team_position[match.away]),
            match.score.home,
            match.score.away,
        )
        for match in pre
    ]

    # Deterministic data-dependent start: mu at the pooled log mean goal
    # rate per side; strengths and h at zero.
    theta: list[float] = [0.0] * (2 + 2 * n_free)
    if total_goals > 0:
        theta[0] = math.log(total_goals / (2.0 * len(pre)))

    status = ConvergenceStatus.MAX_ITERATIONS
    iterations = 0
    for iteration in range(1, config.max_iterations + 1):
        gradient, information = _score_and_information(theta, observations)
        try:
            delta = _newton_solve(information, gradient)
        except _SingularSystem:
            status = ConvergenceStatus.SINGULAR_SYSTEM
            iterations = iteration
            break
        step = [config.damping * component for component in delta]
        if not all(math.isfinite(component) for component in step):
            status = ConvergenceStatus.SINGULAR_SYSTEM
            iterations = iteration
            break
        theta = [value + component for value, component in zip(theta, step)]
        iterations = iteration
        if max(abs(component) for component in step) < config.newton_tol:
            status = ConvergenceStatus.CONVERGED
            break

    return build(theta, iterations, status)


__all__ = ["fit"]
