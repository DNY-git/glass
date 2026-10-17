"""Scenario matrix evaluation: transforms as parameter arithmetic only.

``scenario_matrix`` applies a scenario's transforms to the BASELINE's
parameter values (parameter-scale: ``p' = m * p``), then hands the
transformed pair to the shared constructors in
``app/models/scoreline.py`` — ``lambda_pair`` and
``build_scoreline_matrix`` — the ONE cell-math path in the codebase
(brief decision 9). This module contains **no** cell formula, no
``lgamma``, and never constructs a ``FittedParams`` (AST-enforced by
tests/test_scenarios.py): a transform changes parameter values, never
fit status, so the matrix echoes the baseline's convergence and
insufficient-data flags exactly.

Applicability is strict (brief decision 11, developer answer to open
question 4): a transform that cannot fire on the evaluated fixture —
team not playing, or a ``home_advantage`` op whose named team is not
the fixture's home side — raises ``ValueError`` at evaluation. A
silently inapplicable transform would present an unchanged number
under a hypothetical label, which is mislabeled output.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models import FittedParams, ScorelineMatrix
from app.models.scoreline import build_scoreline_matrix, lambda_pair

from .spec import Scenario, TransformOp


@dataclass(frozen=True)
class ScenarioMatrix:
    """One scenario's scoreline matrix for one fixture.

    ``scenario`` carries the spec, the label, and the baseline's full
    provenance; ``matrix`` echoes the BASELINE's fit flags (a transform
    does not change fit status). The label is reachable on every
    output — as a direct attribute here and through ``scenario``.
    """

    scenario: Scenario
    matrix: ScorelineMatrix

    @property
    def label(self) -> str:
        """The scenario's label, echoed on every output (decision 10)."""
        return self.scenario.label


def _team_index(fitted: FittedParams, team: str) -> int:
    try:
        return fitted.teams.index(team)
    except ValueError:
        raise ValueError(
            f"team {team!r} is not in this fit's teams {fitted.teams!r}"
        ) from None


def scenario_matrix(scenario: Scenario, home: str, away: str) -> ScenarioMatrix:
    """Evaluate a scenario for one fixture (H vs A) — strict applicability.

    Raises ValueError if ``home``/``away`` are not teams of the
    baseline fit, if a transform names a team not playing in this
    fixture, or if a ``home_advantage`` transform names anyone other
    than the fixture's home side (decision 11 — a transform that
    cannot fire must never produce a "hypothetical" number identical
    to baseline).
    """
    fitted = scenario.baseline
    home_index = _team_index(fitted, home)
    away_index = _team_index(fitted, away)

    # Baseline parameter values (read-only); transforms scale the
    # values, never the FittedParams object itself.
    alpha_home = fitted.alpha[home_index]
    alpha_away = fitted.alpha[away_index]
    beta_home = fitted.beta[home_index]
    beta_away = fitted.beta[away_index]
    home_advantage = fitted.home_advantage

    for transform in scenario.transforms:
        multiplier = transform.multiplier
        if transform.op is TransformOp.HOME_ADVANTAGE:
            if transform.team != home:
                raise ValueError(
                    f"home_advantage transform names {transform.team!r}, who is "
                    f"not the home side of fixture {home!r} vs {away!r}"
                )
            home_advantage = multiplier * home_advantage
            continue

        if transform.team == home:
            team_index = home_index
        elif transform.team == away:
            team_index = away_index
        else:
            raise ValueError(
                f"transform team {transform.team!r} does not play in fixture "
                f"{home!r} vs {away!r}"
            )

        if transform.op is TransformOp.ATTACK:
            if team_index == home_index:
                alpha_home = multiplier * alpha_home
            else:
                alpha_away = multiplier * alpha_away
        elif transform.op is TransformOp.DEFENCE:
            if team_index == home_index:
                beta_home = multiplier * beta_home
            else:
                beta_away = multiplier * beta_away
        else:
            # Unreachable while Scenario validates every op (unknown
            # ops are refused at construction) — refusing here too so
            # no transform can ever be silently inert.
            raise ValueError(f"unknown transform op {transform.op!r}")

    lambda_home, lambda_away = lambda_pair(
        fitted.mu,
        alpha_home,
        beta_away,
        alpha_away,
        beta_home,
        home_advantage,
    )
    matrix = build_scoreline_matrix(
        lambda_home,
        lambda_away,
        fitted.config.max_goals,
        fitted.convergence_status,
        fitted.insufficient_data,
        fitted.insufficient_teams,
    )
    return ScenarioMatrix(scenario=scenario, matrix=matrix)


__all__ = ["ScenarioMatrix", "scenario_matrix"]
