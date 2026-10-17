"""Seeded Monte Carlo simulation over one fixture's scoreline matrix.

**THE designated randomness module** (Phase 4 brief decision 2): the
``random`` module is imported in exactly this file and nowhere else
under ``app/`` — AST-enforced with positive and negative probes in
tests/test_phase4_separation.py. Every reported single-match
probability remains the analytic ``outcome_probs``; simulation exists
for (i) Phase 12's replay machinery and (ii) future aggregate/season-
path quantities with no closed form (brief decision 7) — it NEVER
replaces the analytic number (docs/STATISTICAL-ASSUMPTIONS.md §7e).

Seed policy (decision 1, §7c): ``seed`` is a required keyword-only
``int`` — no default, no RNG-object parameter, no ``rng``/
``random_state``/``generator`` anywhere. Each call constructs a **fresh
``random.Random(seed)``**: instance-only, no module-level RNG binding,
no ``random.seed()`` global state, no unseeded instance, no wall
clock, no ``hash()``/``id()``/``secrets``/``uuid`` seed derivation
(AST-banned, criterion 17). Identical ``(fitted, home, away, seed,
n_sims, sim_version [, scenario])`` input yields field-for-field
identical frozen output.

Draws use **``rng.random()`` only** — the one method CPython
documents as sequence-stable across Python versions for a given seed.
Sampling target (decision 4, §7b): categorical draws over the
truncated, renormalized (K+1)^2 matrix — a cumulative table built
row-major from ``exp(log_probs)``, divided by the table sum, located
by ``bisect.bisect_left`` with an fp-epsilon clamp-to-last-cell guard
(``_draw_cell``). MC frequencies therefore deviate from the analytic
target by at most ``dropped_mass / (1 - dropped_mass)``; there is no
``out_of_range_count`` field by design.

Cutoff discipline lives in ``fit`` alone: this module has no
``as_of``, no history, and no time parameter to forget.
"""

from __future__ import annotations

import bisect
import math
import random
from dataclasses import dataclass

from app.models import (
    ConvergenceStatus,
    FittedParams,
    ScorelineMatrix,
    outcome_probs,
    scoreline_log_probs,
)
from app.scenarios import Scenario, scenario_matrix

from .constants import DEFAULT_N_SIMS, SIM_VERSION


@dataclass(frozen=True)
class SimulationResult:
    """One seeded simulation of one fixture — frozen, fully provenance-echoed.

    Field set is the pinned Phase 4 contract (brief decision 5, A4+A9):
    the baseline fit by reference, the scenario spec (or None), the
    seed/n_sims/sim_version echoes, raw integer counts, the analytic
    target, ``mc_stderr`` (simulation noise ONLY — never model or
    parameter uncertainty; this system computes no confidence
    intervals), the matrix's dropped mass, and the fit flags riding
    through (losing a flag would dress plausible-looking garbage as
    healthy output).
    """

    baseline: FittedParams
    scenario: Scenario | None
    seed: int
    n_sims: int
    sim_version: str
    counts_home: int
    counts_draw: int
    counts_away: int
    analytic_outcome: tuple[float, float, float]
    mc_stderr: tuple[float, float, float]
    dropped_mass: float
    convergence_status: ConvergenceStatus
    insufficient_data: bool
    insufficient_teams: tuple[str, ...]


def _cumulative_table(matrix: ScorelineMatrix) -> list[float]:
    """Normalized cumulative sampling table, row-major over the matrix.

    Entries are ``exp(log_probs[i][j])`` for i ascending then j
    ascending (brief decision 4), each divided by the table sum, so
    the table is the CDF of the RENORMALIZED truncated distribution —
    the documented sampling target (§7b).
    """
    weights = [math.exp(log_p) for row in matrix.log_probs for log_p in row]
    total = sum(weights)
    cumulative: list[float] = []
    running = 0.0
    for weight in weights:
        running += weight
        cumulative.append(running / total)
    return cumulative


def _draw_cell(cumulative: list[float], u: float) -> int:
    """Index of the cell ``u`` selects in the cumulative table.

    ``bisect_left`` locates the first cumulative entry >= u. The
    fp-epsilon clamp-to-last-cell guard fires only when floating-point
    rounding at the table tail leaves ``cumulative[-1]`` below ``u``
    (so the lookup runs past the final index): the clamp touches only
    the last cell and never shifts mass between cells (brief decision
    4, §7b). Factored at module scope so the guard is unit-testable
    (criterion 4).
    """
    index = bisect.bisect_left(cumulative, u)
    if index >= len(cumulative):
        return len(cumulative) - 1
    return index


def simulate(
    fitted: FittedParams,
    home: str,
    away: str,
    *,
    seed: int,
    n_sims: int = DEFAULT_N_SIMS,
    scenario: Scenario | None = None,
) -> SimulationResult:
    """Simulate ``n_sims`` draws for one fixture under a required seed.

    Signature is pinned (criterion 1): ``seed`` is keyword-only with no
    default (an omitted seed raises TypeError — never a coin-flip of
    system entropy); there is no RNG-object parameter and no
    ``as_of``/``history``/``matches``/time parameter to forget — cutoff
    discipline lives in ``fit`` alone (A9).

    With ``scenario=None`` (echoed on the result) the draws come from
    ``scoreline_log_probs(fitted, home, away)``; with a scenario the
    draws, analytic target, and dropped mass come from the scenario's
    matrix, and the scenario's baseline must equal ``fitted`` — a
    mismatch would label the output with the wrong provenance and is
    refused rather than silently reconciled. Simulation consumes
    exactly one frozen ScorelineMatrix worth of distribution and never
    replaces the analytic ``outcome_probs`` (decision 7).
    """
    if isinstance(n_sims, bool) or not isinstance(n_sims, int):
        raise ValueError(f"n_sims must be an int, got {type(n_sims).__name__}")
    if n_sims < 1:
        raise ValueError(f"n_sims must be >= 1, got {n_sims}")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError(f"seed must be an int, got {type(seed).__name__}")

    if scenario is None:
        matrix = scoreline_log_probs(fitted, home, away)
    else:
        if scenario.baseline != fitted:
            raise ValueError(
                "scenario baseline does not equal the given fitted object "
                "(simulating under a mismatched baseline would mislabel the "
                "output)"
            )
        matrix = scenario_matrix(scenario, home, away).matrix

    analytic = outcome_probs(matrix)
    cumulative = _cumulative_table(matrix)

    # Fresh, instance-only RNG per call: identical inputs + seed ->
    # field-for-field identical output, no caller-side or global state
    # (decision 1, §7c).
    rng = random.Random(seed)
    stride = matrix.max_goals + 1
    counts_home = 0
    counts_draw = 0
    counts_away = 0
    for _ in range(n_sims):
        i, j = divmod(_draw_cell(cumulative, rng.random()), stride)
        if i > j:
            counts_home += 1
        elif i == j:
            counts_draw += 1
        else:
            counts_away += 1

    # Exact expression order is part of the contract (decision 5):
    # sqrt(p * (1.0 - p) / n_sims) from the ANALYTIC p — this measures
    # simulation noise only, never parameter or model uncertainty.
    mc_stderr = tuple(math.sqrt(p * (1.0 - p) / n_sims) for p in analytic)

    return SimulationResult(
        baseline=fitted,
        scenario=scenario,
        seed=seed,
        n_sims=n_sims,
        sim_version=SIM_VERSION,
        counts_home=counts_home,
        counts_draw=counts_draw,
        counts_away=counts_away,
        analytic_outcome=analytic,
        mc_stderr=mc_stderr,
        dropped_mass=matrix.dropped_mass,
        convergence_status=matrix.convergence_status,
        insufficient_data=matrix.insufficient_data,
        insufficient_teams=matrix.insufficient_teams,
    )


__all__ = ["DEFAULT_N_SIMS", "SIM_VERSION", "SimulationResult", "simulate"]
