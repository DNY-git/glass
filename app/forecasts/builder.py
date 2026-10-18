"""The forecast builder: pipeline stage 6, cutoff enforced inside.

``build_forecast(matches, fixture)`` — there is no ``as_of``,
``cutoff``, ``date``, or any time-like parameter to forget (F1/L1):
the cutoff **is ``fixture.date``**, a strict day-granularity date
string, derived inside the builder. The cutoff is enforced twice: the
builder refuses a fixture whose natural key appears in ``matches`` (the
target must not be its own history), and ``fit`` applies its strict
``date < as_of`` filter underneath — so nothing dated on or after the
fixture date can ever enter the fit (matches there are simply excluded,
never an error: that silent exclusion IS the leakage defense).

The output is analytic and deterministic: matrix essentials plus the
analytic ``outcome_probs`` at full precision; no seed, no Monte Carlo,
no scenario, no baseline (Phases 9/11 own those). In-sample estimates
pending chronological evaluation — never evidence of accuracy.
"""

from __future__ import annotations

from typing import Sequence

from app.domain import Fixture, Match
from app.models import outcome_probs, fit, scoreline_log_probs

from .constants import FORECAST_VERSION
from .record import Forecast


def build_forecast(matches: Sequence[Match], fixture: Fixture) -> Forecast:
    """One frozen analytic forecast for ``fixture`` from ``matches``.

    The target's own date is the cutoff (computed here, inside — the
    calculation enforces it, never only the call site). Raises
    ``TypeError`` if the target is not a scoreless ``Fixture`` and
    ``ValueError`` if the fixture's natural key appears in ``matches``.
    """
    if not isinstance(fixture, Fixture):
        raise TypeError(
            "build_forecast requires a scoreless Fixture as the target "
            f"(got {type(fixture).__name__})"
        )
    fixture_key = fixture.natural_key
    for match in matches:
        if match.natural_key == fixture_key:
            raise ValueError(
                f"fixture {fixture_key!r} is present in the matches history; "
                "the forecast target must not be its own history"
            )

    # The cutoff is fixture.date, day granularity, enforced inside fit
    # as a strict `date < as_of` filter (Phase 3, unchanged).
    fitted = fit(matches, fixture.date)
    matrix = scoreline_log_probs(fitted, fixture.home, fixture.away)
    outcome_home, outcome_draw, outcome_away = outcome_probs(matrix)

    return Forecast(
        competition=fixture.competition,
        season=fixture.season,
        date=fixture.date,
        home=fixture.home,
        away=fixture.away,
        kickoff=fixture.kickoff,
        as_of=fixture.date,
        fitted=fitted,
        lambda_home=matrix.lambda_home,
        lambda_away=matrix.lambda_away,
        max_goals=matrix.max_goals,
        dropped_mass=matrix.dropped_mass,
        outcome_home=outcome_home,
        outcome_draw=outcome_draw,
        outcome_away=outcome_away,
        forecast_version=FORECAST_VERSION,
    )


__all__ = ["build_forecast"]
