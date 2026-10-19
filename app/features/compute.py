"""Feature computation: pipeline stage 4, cutoff enforced inside (F1).

``compute_features(matches, fixture) -> FeatureVector`` — there is no
``as_of``, ``cutoff``, ``date``, or any time-like parameter to forget:
the cutoff **IS ``fixture.date``**, derived inside the function. A
strict ``date < fixture.date`` filter is applied inside to every
consumed match: nothing dated on or after the fixture date can enter
any window (matches there sit silently outside — that silent
exclusion IS the leakage defense, never an error), while the fixture's
own natural key appearing in ``matches`` is refused with ``ValueError``
(the target must not be its own history). Windows are selected in
``canonical_sort_key`` order, so input order and same-date ties never
leak into any field. The shape mirrors ``build_forecast`` exactly:
``TypeError`` on a non-``Fixture`` target, ``ValueError`` on the
collision, then the cutoff inside.

Cutoff equivalence with ``fit`` is pinned by the digest-parity
cross-check (criterion 5), never by shared code: ``app/models`` is
byte-pinned (F4), so the strict-``<`` filter and the input digest are
reimplemented here over exported ``app.domain`` machinery only — the
neutral-carrier ``MatchCollection`` + ``canonical_state`` pattern,
giving the identical ``FittedParams.input_digest`` definition (sha256
over the strictly-pre-cutoff set's canonical state).

Policies applied are the named constants of ``.constants`` (decision
5): ``FORM_WINDOW`` under ``MISSING_UNTIL_FULL_WINDOW`` (no partial-
window means), ``WITHIN_SEASON`` rest days (a season opener is
MISSING, never an off-season gap), and ``MEAN_OVER_AVAILABLE_WITH_N``
xG with ``n_xg`` disclosed and MISSING at zero — a different estimator
than a strict rolling-xG window, documented as such. Pure function of
``(matches, fixture)``: zero fitted transformers (F2), no RNG, no wall
clock (ISO date arithmetic only), accumulation in exactly canonical
window order at full float precision. Features are historical
summaries of synthetic fixture history — not probabilities, not model
outputs, not evidence (section 9g).
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Sequence

from app.domain import (
    Availability,
    Fixture,
    IngestedRecord,
    Match,
    MatchCollection,
    OptionalValue,
    Provenance,
    RecordLocation,
    canonical_state,
)

from .constants import FEATURE_VERSION, FORM_WINDOW
from .record import FeatureVector

# The six per-side fields of the decision-4 contract, in the exact
# order _side_features yields them: goals_scored_form,
# goals_conceded_form, rest_days, xg_form (all OptionalValue), then
# xg_n, prior_matches (plain ints — 0 is a true exact fact).
_SideFields = tuple[OptionalValue, OptionalValue, OptionalValue, OptionalValue, int, int]


def _pre_cutoff(
    matches: Sequence[Match], as_of: str
) -> tuple[str, tuple[Match, ...]]:
    """The (input_digest, canonical history) pair of the strict pre-cutoff set.

    Only matches with ``date < as_of`` (strictly; a match dated exactly
    at the cutoff stays outside — that is the leakage defense) enter,
    sorted by ``canonical_sort_key`` (date, competition, season, home,
    away) so iteration order never depends on input order and same-date
    ties resolve there. Identical duplicates collapse by natural key
    via the neutral-carrier ``MatchCollection`` — the exact machinery
    and construction ``poisson._input_digest`` uses, so this digest has
    the IDENTICAL definition to ``FittedParams.input_digest``: sha256
    of ``canonical_state()`` over the strictly-pre-cutoff set. The
    helper may not be imported (F4 byte pins on ``app/models``), so
    criterion 5 pins parity with a cross-check test instead.
    """
    ordered = [match for match in matches if match.date < as_of]
    ordered.sort(key=lambda match: match.canonical_sort_key)
    collection = MatchCollection()
    for index, match in enumerate(ordered):
        collection.add(
            IngestedRecord(
                match=match,
                provenance=Provenance(source_path="", sha256=""),
                location=RecordLocation(source_path="", index=index),
            )
        )
    digest = hashlib.sha256(canonical_state(collection).encode("utf-8")).hexdigest()
    history = tuple(record.match for record in collection.records())
    return digest, history


def _team_history(history: Sequence[Match], team: str) -> tuple[Match, ...]:
    """One team's matches from canonical history, canonical order kept."""
    return tuple(
        match for match in history if team in (match.home, match.away)
    )


def _scored(match: Match, team: str) -> int:
    return match.score.home if match.home == team else match.score.away


def _conceded(match: Match, team: str) -> int:
    return match.score.away if match.home == team else match.score.home


def _side_features(
    history: Sequence[Match], team: str, fixture: Fixture
) -> _SideFields:
    """The six decision-4 fields for one side, named policies applied.

    Window: the team's last ``FORM_WINDOW`` strictly-pre-cutoff matches
    in canonical order (competition/season-agnostic scope, developer
    answer Q6). Under ``FORM_WINDOW_POLICY = "MISSING_UNTIL_FULL_WINDOW"`
    the two goals-form fields are MISSING until the full window exists
    (0-4 priors) — a partial window is never averaged. Under
    ``REST_DAYS_POLICY = "WITHIN_SEASON"`` rest days are the calendar
    days since the most recent same-season prior match, MISSING at
    season start. Under ``XG_FORM_POLICY = "MEAN_OVER_AVAILABLE_WITH_N"`
    xg_form averages the window's xG-available matches only (the
    per-feature available-prefix-with-n-disclosed shape F1 sanctions
    when history is short), n_xg disclosed, MISSING at n_xg = 0 —
    missing xG never participates as 0.0. Counts (xg_n, prior_matches)
    are plain ints: 0 is a true exact fact, never an imputed estimate.
    """
    team_matches = _team_history(history, team)
    prior_matches = len(team_matches)
    window = team_matches[-FORM_WINDOW:]

    if prior_matches >= FORM_WINDOW:
        scored_form: OptionalValue = OptionalValue.available(
            sum(_scored(match, team) for match in window) / FORM_WINDOW
        )
        conceded_form: OptionalValue = OptionalValue.available(
            sum(_conceded(match, team) for match in window) / FORM_WINDOW
        )
    else:
        scored_form = OptionalValue.missing()
        conceded_form = OptionalValue.missing()

    same_season = [
        match for match in team_matches if match.season == fixture.season
    ]
    if same_season:
        most_recent = same_season[-1]  # history is canonical: latest last
        rest_days: OptionalValue = OptionalValue.available(
            (date.fromisoformat(fixture.date) - date.fromisoformat(most_recent.date)).days
        )
    else:
        rest_days = OptionalValue.missing()

    xg_values = [
        match.xg.value.home if match.home == team else match.xg.value.away
        for match in window
        if match.xg.availability is Availability.AVAILABLE
    ]
    xg_n = len(xg_values)
    xg_form = (
        OptionalValue.available(sum(xg_values) / xg_n)
        if xg_n > 0
        else OptionalValue.missing()
    )

    return (
        scored_form,
        conceded_form,
        rest_days,
        xg_form,
        xg_n,
        prior_matches,
    )


def compute_features(matches: Sequence[Match], fixture: Fixture) -> FeatureVector:
    """One frozen feature vector for ``fixture`` from ``matches`` (F1).

    The target's own date is the cutoff — computed here, inside the
    calculation, never only at a call site. Raises ``TypeError`` if the
    target is not a scoreless ``Fixture`` and ``ValueError`` if the
    fixture's natural key appears in ``matches``.
    """
    if not isinstance(fixture, Fixture):
        raise TypeError(
            "compute_features requires a scoreless Fixture as the target "
            f"(got {type(fixture).__name__})"
        )
    fixture_key = fixture.natural_key
    for match in matches:
        if match.natural_key == fixture_key:
            raise ValueError(
                f"fixture {fixture_key!r} is present in the matches history; "
                "the feature target must not be its own history"
            )

    digest, history = _pre_cutoff(matches, fixture.date)

    home_scored, home_conceded, home_rest, home_xg, home_xg_n, home_prior = (
        _side_features(history, fixture.home, fixture)
    )
    away_scored, away_conceded, away_rest, away_xg, away_xg_n, away_prior = (
        _side_features(history, fixture.away, fixture)
    )

    return FeatureVector(
        competition=fixture.competition,
        season=fixture.season,
        date=fixture.date,
        home=fixture.home,
        away=fixture.away,
        kickoff=fixture.kickoff,  # echoed, never consumed (decision 9)
        as_of=fixture.date,
        feature_version=FEATURE_VERSION,
        input_digest=digest,
        home_goals_scored_form=home_scored,
        home_goals_conceded_form=home_conceded,
        home_rest_days=home_rest,
        home_xg_form=home_xg,
        home_xg_n=home_xg_n,
        home_prior_matches=home_prior,
        away_goals_scored_form=away_scored,
        away_goals_conceded_form=away_conceded,
        away_rest_days=away_rest,
        away_xg_form=away_xg,
        away_xg_n=away_xg_n,
        away_prior_matches=away_prior,
    )


__all__ = ["compute_features"]
