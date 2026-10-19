"""Phase 6 acceptance criteria 8-14: named feature-window policies.

Window policy constants pinned (8), the WITHIN_SEASON rest-day policy
with calendar-day arithmetic verified independently (9), xG policy
honesty against quant's measured availability table (10), kickoff echo
never consumed (11), independent home/away side coverage (12), the
version-local golden content hash (13), and content-hash recomputability
plus sensitivity (14).

Pool facts re-derived here by real runs over the checked-in fixtures
(the brief's measured table): 60 matches; xG on exactly 10/60 (season
2025-26 only, 4 dates); goals-form MISSING on 30/120 appearances; no
prior ever 6/120; no same-season prior 12/120; strict last-5-all-xG
window 0/120. Hand-computed goldens carry their derivations in comments
(version-local golden discipline).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from datetime import date
from pathlib import Path

from app.domain import Fixture, Match, MatchCollection, OptionalValue, Score, Xg
from app.features import FEATURE_VERSION, FeatureVector, canonical_payload, compute_features
from app.features.constants import (
    FORM_WINDOW,
    FORM_WINDOW_POLICY,
    REST_DAYS_POLICY,
    XG_FORM_POLICY,
)
from app.ingestion import import_fixture

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool (Phase 3/5 convention), passed UNFILTERED —
# compute_features applies the cutoff inside; this call site never does.
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES: tuple[Match, ...] = tuple(record.match for record in _collection.records())

# The golden fixture pair (same as test_features.py): mid-late season 2,
# after the xG onset, both sides' form fields AVAILABLE, xG branch with
# n_xg >= 1; its natural key matches no pool match.
GOLDEN_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-09-06",
    home="Emberfield Kestrels",
    away="Silverpine Rovers",
    kickoff=OptionalValue.missing(),
)

# A late season-2 fixture (away side's window mixes xG-available and
# xG-missing matches), used for the n_xg-branch assertions.
LATE_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-09-13",
    home="Coralgate Athletic",
    away="Quarryhill Zenith",
    kickoff=OptionalValue.missing(),
)


def _without(keys: tuple) -> list:
    """The pool minus the given natural keys (never pre-cutoff-filtered)."""
    excluded = set(keys)
    return [m for m in ALL_MATCHES if m.natural_key not in excluded]


def _fixture_for(match: Match) -> Fixture:
    """The scoreless target for one pool match (kickoff MISSING echo)."""
    return Fixture(
        competition=match.competition,
        season=match.season,
        date=match.date,
        home=match.home,
        away=match.away,
        kickoff=OptionalValue.missing(),
    )


def _match(
    date_text: str,
    home: str,
    away: str,
    home_goals: int,
    away_goals: int,
    *,
    competition: str,
    season: str,
) -> Match:
    """One in-schema synthetic match (all optional data MISSING)."""
    return Match(
        competition=competition,
        season=season,
        date=date_text,
        home=home,
        away=away,
        score=Score(home_goals, away_goals),
        round_label=None,
        kickoff=OptionalValue.missing(),
        xg=OptionalValue.missing(),
    )


# One vector per pool appearance (60 fixtures, each computed from the
# pool minus its own natural key — the target is never its own history).
# Deterministic module-level census data for the measured-table pins.
APPEARANCES: tuple[tuple[Match, FeatureVector], ...] = tuple(
    (m, compute_features(_without((m.natural_key,)), _fixture_for(m))) for m in ALL_MATCHES
)


# ---------------------------------------------------------------- criterion 8


def test_form_window_policy_constants_pinned_and_missing_never_zero() -> None:
    # Named constants (decision 5): pinned literals, never silent defaults.
    assert FORM_WINDOW == 5
    assert FORM_WINDOW_POLICY == "MISSING_UNTIL_FULL_WINDOW"
    assert REST_DAYS_POLICY == "WITHIN_SEASON"
    assert XG_FORM_POLICY == "MEAN_OVER_AVAILABLE_WITH_N"

    # Zero priors -> both form fields MISSING (value None, never 0.0),
    # while the count fields disclose 0 as the exact fact it is.
    empty = Fixture(
        competition="Obsidian Coast League", season="2024-25", date="2024-08-10",
        home="Nowhere United", away="Null County", kickoff=OptionalValue.missing(),
    )
    zero = compute_features([], empty)
    for side in ("home", "away"):
        scored = getattr(zero, f"{side}_goals_scored_form")
        conceded = getattr(zero, f"{side}_goals_conceded_form")
        assert scored.value is None and scored.availability.value == "MISSING"
        assert conceded.value is None and conceded.availability.value == "MISSING"
        assert getattr(zero, f"{side}_prior_matches") == 0

    # 1-4 priors -> MISSING under the named policy (window > available
    # history; a partial window is never averaged), with prior_matches
    # disclosing the true count. 2024-08-17: Coralgate/Thistledown each
    # have exactly one prior (the 2024-08-10 opener).
    one = Fixture(
        competition="Obsidian Coast League", season="2024-25", date="2024-08-17",
        home="Coralgate Athletic", away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    )
    assert one.natural_key not in {m.natural_key for m in ALL_MATCHES}
    short_one = compute_features(_without((one.natural_key,)), one)
    assert short_one.home_prior_matches == 1
    assert short_one.away_prior_matches == 1
    assert short_one.home_goals_scored_form.value is None
    assert short_one.away_goals_scored_form.value is None

    # 3 priors: 2024-08-31 Silverpine (08-10, 08-17, 08-24) and
    # Emberfield (08-10, 08-17, 08-24) — still below the window, still
    # MISSING, counts disclosed.
    two = Fixture(
        competition="Obsidian Coast League", season="2024-25", date="2024-08-31",
        home="Silverpine Rovers", away="Emberfield Kestrels",
        kickoff=OptionalValue.missing(),
    )
    assert two.natural_key not in {m.natural_key for m in ALL_MATCHES}
    short_two = compute_features(_without((two.natural_key,)), two)
    assert short_two.home_prior_matches == 3
    assert short_two.away_prior_matches == 3
    assert short_two.home_goals_scored_form.value is None
    assert short_two.away_goals_scored_form.value is None

    # >= 5 priors -> AVAILABLE with the hand-computed window mean.
    # Golden (Emberfield, 2025-09-06) window in canonical order:
    #   2024-10-12 (2-2 vs Coralgate)  scored 2 conceded 2
    #   2025-08-09 (0-2 at Silverpine) scored 0 conceded 2
    #   2025-08-16 (1-1 vs Harbourlight) scored 1 conceded 1
    #   2025-08-23 (2-1 vs Thistledown) scored 2 conceded 1
    #   2025-08-30 (2-2 at Quarryhill) scored 2 conceded 2
    #   scored   = 2+0+1+2+2 = 7 -> 7/5 = 1.4
    #   conceded = 2+2+1+1+2 = 8 -> 8/5 = 1.6
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert full.home_prior_matches == 14
    assert full.home_goals_scored_form.value == 7 / 5 == 1.4
    assert full.home_goals_conceded_form.value == 8 / 5 == 1.6
    assert full.home_goals_scored_form.availability.value == "AVAILABLE"

    # Measured over the real pool: goals-form is MISSING on exactly the
    # 30/120 appearances with fewer than FORM_WINDOW priors (each team's
    # first five career matches: 6 teams x 5), and prior_matches == 0 on
    # exactly the 6/120 season-opening appearances. The independent
    # recomputation below re-derives each appearance's pre-cutoff count
    # from the pool itself (target excluded), never trusting the vector.
    scored_missing = 0
    conceded_missing = 0
    zero_prior = 0
    for match, vector in APPEARANCES:
        for side, team in (("home", match.home), ("away", match.away)):
            priors = sum(
                1
                for m in ALL_MATCHES
                if m.natural_key != match.natural_key
                and m.date < match.date
                and team in (m.home, m.away)
            )
            assert getattr(vector, f"{side}_prior_matches") == priors
            scored = getattr(vector, f"{side}_goals_scored_form")
            conceded = getattr(vector, f"{side}_goals_conceded_form")
            if priors < FORM_WINDOW:
                assert scored.value is None, (match.date, side)
                assert conceded.value is None, (match.date, side)
                assert scored.availability.value == "MISSING"
            else:
                assert scored.value is not None, (match.date, side)
                assert scored.availability.value == "AVAILABLE"
            scored_missing += scored.value is None
            conceded_missing += conceded.value is None
            zero_prior += priors == 0
    assert (scored_missing, conceded_missing, zero_prior) == (30, 30, 6)


# ---------------------------------------------------------------- criterion 9


def test_rest_days_within_season_policy_pinned() -> None:
    assert REST_DAYS_POLICY == "WITHIN_SEASON"

    # Golden: both sides' most recent SAME-SEASON prior is 2025-08-30;
    # the gap to the fixture date is verified here independently via
    # datetime.date arithmetic, not by trusting the vector.
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    for side, team in (("home", GOLDEN_FIXTURE.home), ("away", GOLDEN_FIXTURE.away)):
        same_season = sorted(
            (
                m for m in ALL_MATCHES
                if team in (m.home, m.away) and m.season == GOLDEN_FIXTURE.season
                and m.date < GOLDEN_FIXTURE.date
            ),
            key=lambda m: m.canonical_sort_key,
        )
        expected = (date.fromisoformat(GOLDEN_FIXTURE.date) - date.fromisoformat(same_season[-1].date)).days
        rest = getattr(full, f"{side}_rest_days")
        assert same_season[-1].date == "2025-08-30"
        assert expected == 7
        assert rest.value == expected == 7
        assert rest.availability.value == "AVAILABLE"

    # Non-7 calendar gaps, both sides in one call (synthetic league so
    # the gaps are hand-set): Harbour Ridge last played 2025-08-30 (21
    # days before the 2025-09-20 target), Kingsmoor City last played
    # 2025-09-06 (14 days). A "days since" implementation that always
    # reported the pool's weekly cadence would fail both.
    history = [
        _match("2025-08-30", "Harbour Ridge FC", "Beacon United", 1, 0, competition="Night Owl League", season="2024-25"),
        _match("2025-09-06", "Kingsmoor City", "Beacon United", 2, 1, competition="Night Owl League", season="2024-25"),
    ]
    target = Fixture(
        competition="Night Owl League", season="2024-25", date="2025-09-20",
        home="Harbour Ridge FC", away="Kingsmoor City", kickoff=OptionalValue.missing(),
    )
    vector = compute_features(history, target)
    assert vector.home_rest_days.value == (date(2025, 9, 20) - date(2025, 8, 30)).days == 21
    assert vector.away_rest_days.value == (date(2025, 9, 20) - date(2025, 9, 6)).days == 14
    assert vector.home_rest_days.availability.value == "AVAILABLE"
    assert vector.away_rest_days.availability.value == "AVAILABLE"

    # Season opener with PRIOR history in the other season: MISSING,
    # never the cross-season value. Silverpine/Emberfield on 2025-08-09
    # both last played 2024-10-12 — a 301-day off-season gap that the
    # WITHIN_SEASON policy explicitly refuses to report as "rest".
    opener = Fixture(
        competition="Obsidian Coast League", season="2025-26", date="2025-08-09",
        home="Silverpine Rovers", away="Emberfield Kestrels",
        kickoff=OptionalValue.missing(),
    )
    assert opener.natural_key in {m.natural_key for m in ALL_MATCHES}  # real pairing
    opener_vector = compute_features(_without((opener.natural_key,)), opener)
    cross_season = (date(2025, 8, 9) - date(2024, 10, 12)).days
    assert cross_season == 301
    for side in ("home", "away"):
        rest = getattr(opener_vector, f"{side}_rest_days")
        assert rest.value is None and rest.availability.value == "MISSING"
        assert rest.value != cross_season

    # No prior match ever -> MISSING (2024-08-10 season-1 opener, both
    # sides at zero priors).
    first = Fixture(
        competition="Obsidian Coast League", season="2024-25", date="2024-08-10",
        home="Coralgate Athletic", away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    )
    assert first.natural_key in {m.natural_key for m in ALL_MATCHES}
    first_vector = compute_features(_without((first.natural_key,)), first)
    assert first_vector.home_prior_matches == 0
    assert first_vector.away_prior_matches == 0
    assert first_vector.home_rest_days.value is None
    assert first_vector.away_rest_days.value is None

    # Sides resolve independently IN THE SAME CALL: Newtown Albion has
    # no history at all (MISSING) while its opponent Emberfield has a
    # same-season prior (AVAILABLE) — measured on the same vector.
    mixed = Fixture(
        competition="Obsidian Coast League", season="2025-26", date="2025-09-20",
        home="Newtown Albion", away="Emberfield Kestrels",
        kickoff=OptionalValue.missing(),
    )
    mixed_vector = compute_features(ALL_MATCHES, mixed)
    assert mixed_vector.home_rest_days.value is None
    assert mixed_vector.home_rest_days.availability.value == "MISSING"
    assert mixed_vector.away_rest_days.value == 7
    assert mixed_vector.away_rest_days.availability.value == "AVAILABLE"

    # Measured over the real pool: rest_days is MISSING on exactly the
    # 12/120 season-opening appearances — every appearance on the two
    # seasons' first dates (3 fixtures x 2 sides x 2 seasons), and on no
    # other appearance; every non-missing value is the verified 7-day
    # cadence.
    opening_dates = {"2024-08-10", "2025-08-09"}
    missing_count = 0
    observed_values = set()
    for match, vector in APPEARANCES:
        for side in ("home", "away"):
            rest = getattr(vector, f"{side}_rest_days")
            assert (rest.value is None) == (match.date in opening_dates), (match.date, side)
            if rest.value is None:
                missing_count += 1
            else:
                observed_values.add(rest.value)
    assert missing_count == 12
    assert observed_values == {7}


# ---------------------------------------------------------------- criterion 10


def test_xg_policy_honesty_and_measured_availability() -> None:
    assert XG_FORM_POLICY == "MEAN_OVER_AVAILABLE_WITH_N"

    # n_xg == 0 -> xg_form MISSING, NEVER 0.0 — and the goals-form
    # fields can be AVAILABLE in the same call (10 priors, all from
    # season 1 where no xG exists). Both 2025-08-09 openers qualify.
    before_onset = Fixture(
        competition="Obsidian Coast League", season="2025-26", date="2025-08-09",
        home="Coralgate Athletic", away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    )
    assert before_onset.natural_key in {m.natural_key for m in ALL_MATCHES}
    early = compute_features(_without((before_onset.natural_key,)), before_onset)
    for side in ("home", "away"):
        xg = getattr(early, f"{side}_xg_form")
        assert getattr(early, f"{side}_xg_n") == 0
        assert xg.value is None and xg.availability.value == "MISSING"
        assert xg.value != 0.0
    assert early.home_prior_matches == 10  # season-1 priors, goals AVAILABLE
    assert early.home_goals_scored_form.value is not None

    # n_xg >= 1 -> the mean over the window's xG-AVAILABLE SUBSET ONLY,
    # n_xg disclosed, and the value differs from the zero-substituted
    # mean (missing xG never participates as 0.0). Golden home window
    # xG in canonical order: [None, 1.0, 0.3, 1.6, None] -> sum 2.9,
    # n_xg 3 -> 2.9/3 = 0.9666666666666667; zero-substituted it would
    # be 2.9/5 = 0.58.
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert full.home_xg_n == 3
    assert full.home_xg_form.value == 2.9 / 3 == 0.9666666666666667
    assert full.home_xg_form.value != 2.9 / 5
    # Golden away window xG: [None, 1.0, 2.0, 0.9, None] -> sum 3.9,
    # n_xg 3 -> 3.9/3 = 1.3.
    assert full.away_xg_n == 3
    assert full.away_xg_form.value == 3.9 / 3 == 1.3
    assert full.away_xg_form.value != 3.9 / 5

    # Late season-2 fixture: home window xG [1.2, 0.7, 0.9, 1.1, None]
    # -> 3.9/4 = 0.975; away window [0.5, 0.4, 1.3, None, None] ->
    # 2.2/3 = 0.7333333333333334. Both differ from their
    # zero-substituted means.
    late = compute_features(ALL_MATCHES, LATE_FIXTURE)
    assert late.home_xg_n == 4
    assert late.home_xg_form.value == 3.9 / 4 == 0.975
    assert late.home_xg_form.value != 3.9 / 5
    assert late.away_xg_n == 3
    assert late.away_xg_form.value == 2.2 / 3 == 0.7333333333333334
    assert late.away_xg_form.value != 2.2 / 5
    for side in ("home", "away"):
        assert 1 <= getattr(late, f"{side}_xg_n") <= FORM_WINDOW
        assert getattr(late, f"{side}_xg_form").availability.value == "AVAILABLE"

    # Measured availability (quant's table, re-derived over the pool):
    # xG present on exactly 10/60 matches, season 2025-26 ONLY, on
    # exactly 4 distinct dates.
    xg_matches = [m for m in ALL_MATCHES if m.xg.availability.value == "AVAILABLE"]
    assert len(ALL_MATCHES) == 60
    assert len(xg_matches) == 10
    assert {m.season for m in xg_matches} == {"2025-26"}
    assert len({m.date for m in xg_matches}) == 4

    # Every season-1 fixture -> BOTH sides xg MISSING (30 fixtures x 2
    # sides = 60 appearances), and every 2025-08-09 season-2 opener ->
    # both sides MISSING with n_xg 0 (pre-onset history).
    season_one_missing = 0
    for match, vector in APPEARANCES:
        for side in ("home", "away"):
            xg = getattr(vector, f"{side}_xg_form")
            n_xg = getattr(vector, f"{side}_xg_n")
            assert 0 <= n_xg <= FORM_WINDOW
            assert (xg.value is None) == (n_xg == 0)  # MISSING <=> n_xg == 0
            if match.season == "2024-25":
                assert xg.value is None, (match.date, side)
                season_one_missing += 1
            if match.date == "2025-08-09":
                assert xg.value is None and n_xg == 0, (match.date, side)
    assert season_one_missing == 60

    # The strict last-5-all-xG window covers 0/120 pool appearances —
    # the documented reason that stricter estimator is NOT shipped.
    strict_all_xg = sum(
        getattr(vector, f"{side}_xg_n") == FORM_WINDOW
        for _, vector in APPEARANCES
        for side in ("home", "away")
    )
    assert strict_all_xg == 0


# ---------------------------------------------------------------- criterion 11


def test_kickoff_echoed_not_consumed_missing_never_defaulted() -> None:
    # MISSING kickoff echoes MISSING — no fabricated "00:00"/"12:00"
    # default ever appears in the canonical payload.
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert full.kickoff.value is None
    assert full.kickoff.availability.value == "MISSING"
    payload = canonical_payload(full)
    assert "00:00" not in payload
    assert "12:00" not in payload
    assert not re.search(r"\d{2}:\d{2}", payload)  # no time string at all

    # Two otherwise-identical fixtures differing ONLY in the kickoff
    # echo: identical computed feature values (the twelve computed
    # fields), differing only in kickoff, kickoff availability and the
    # content hash — disclosure, never consumption.
    with_kickoff = Fixture(
        competition=GOLDEN_FIXTURE.competition, season=GOLDEN_FIXTURE.season,
        date=GOLDEN_FIXTURE.date, home=GOLDEN_FIXTURE.home, away=GOLDEN_FIXTURE.away,
        kickoff=OptionalValue.available("12:30"),
    )
    echoed = compute_features(ALL_MATCHES, with_kickoff)
    differing = [
        name
        for name in (f.name for f in dataclasses.fields(FeatureVector))
        if getattr(full, name) != getattr(echoed, name)
    ]
    assert sorted(differing) == ["content_hash", "kickoff"]
    assert echoed.kickoff.value == "12:30"
    assert echoed.kickoff.availability.value == "AVAILABLE"
    assert "12:30" in canonical_payload(echoed)  # the fixture's own time, verbatim
    assert "12:30" not in payload  # absent while MISSING — never defaulted

    # No COMPUTED feature field carries an "HH:MM"-shaped value — the
    # twelve computed fields are counts, day counts, or window means
    # (never strings), even when the fixture carries a kickoff.
    computed_fields = (
        "home_goals_scored_form", "home_goals_conceded_form", "home_rest_days",
        "home_xg_form", "home_xg_n", "home_prior_matches",
        "away_goals_scored_form", "away_goals_conceded_form", "away_rest_days",
        "away_xg_form", "away_xg_n", "away_prior_matches",
    )
    for name in computed_fields:
        value = getattr(echoed, name)
        inner = value.value if isinstance(value, OptionalValue) else value
        assert not isinstance(inner, str), (name, inner)


# ---------------------------------------------------------------- criterion 12


def test_home_and_away_sides_covered_independently() -> None:
    # One call returns both sides' six fields, each echoing the correct
    # team via the natural key (no side-swap anywhere).
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert (full.competition, full.season, full.date, full.home, full.away) == GOLDEN_FIXTURE.natural_key
    # Golden home/away differ (hand-derived in test_features.py C7 /
    # test_features_policies.py C8): scored 1.4 vs 0.8, xG 2.9/3 vs
    # 3.9/3 — a swapped implementation could not produce both.
    assert full.home_goals_scored_form.value == 1.4
    assert full.away_goals_scored_form.value == 0.8
    assert full.home_xg_form.value == 2.9 / 3
    assert full.away_xg_form.value == 3.9 / 3

    # The swapped fixture (sides exchanged, same date) swaps every
    # side-dependent field exactly — the strongest no-swap pin.
    swapped = Fixture(
        competition=GOLDEN_FIXTURE.competition, season=GOLDEN_FIXTURE.season,
        date=GOLDEN_FIXTURE.date, home=GOLDEN_FIXTURE.away, away=GOLDEN_FIXTURE.home,
        kickoff=OptionalValue.missing(),
    )
    mirror = compute_features(ALL_MATCHES, swapped)
    for name in (
        "goals_scored_form", "goals_conceded_form", "rest_days", "xg_form",
        "xg_n", "prior_matches",
    ):
        assert getattr(mirror, f"home_{name}") == getattr(full, f"away_{name}"), name
        assert getattr(mirror, f"away_{name}") == getattr(full, f"home_{name}"), name

    # Independent availability in one call: a zero-history team (all six
    # fields MISSING/0) beside a full-history team (AVAILABLE) — the
    # short side never contaminates the long side.
    mixed = compute_features(
        ALL_MATCHES,
        Fixture(
            competition="Obsidian Coast League", season="2025-26", date="2025-09-20",
            home="Newtown Albion", away="Emberfield Kestrels",
            kickoff=OptionalValue.missing(),
        ),
    )
    assert mixed.home_prior_matches == 0
    assert mixed.home_goals_scored_form.value is None
    assert mixed.home_xg_form.value is None
    assert mixed.home_xg_n == 0
    assert mixed.home_rest_days.value is None
    assert mixed.away_prior_matches == 16
    assert mixed.away_goals_scored_form.value == 1.4
    assert mixed.away_goals_scored_form.availability.value == "AVAILABLE"
    assert mixed.away_rest_days.value == 7


# ---------------------------------------------------------------- criterion 13


def test_golden_feature_vector_hash() -> None:
    # One version-local golden pin (F7): the SAME documented pair as the
    # window goldens above — form fields AVAILABLE on both sides and the
    # xG branch exercised (n_xg 3, not an all-MISSING vector).
    #
    # Derivation of the hashed content (canonical payload = these 21
    # fields, sorted keys, compact separators): home scored 7/5 = 1.4,
    # conceded 8/5 = 1.6, rest 7, xG 2.9/3, xg_n 3, priors 14; away
    # scored 4/5 = 0.8, conceded 5/5 = 1.0, rest 7, xG 3.9/3 = 1.3,
    # xg_n 3, priors 14; kickoff MISSING (null); as_of 2025-09-06;
    # feature_version "features-chronological-v1"; input_digest
    # b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78
    # (sha256 of canonical_state() over the 42 strictly-pre-cutoff
    # matches). Literal from a real run of THIS spec on this data;
    # re-derive (never widen) on any spec change.
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert full.home_goals_scored_form.value == 1.4
    assert full.away_xg_form.value == 1.3
    assert full.home_xg_n == 3 and full.away_xg_n == 3
    assert full.content_hash == (
        "8da6751447bd0320ed61839cd5d97562127ff80948e878ac5f07d53eb7a10b05"
    )
    assert re.fullmatch(r"[0-9a-f]{64}", full.content_hash)


# ---------------------------------------------------------------- criterion 14


def test_content_hash_recomputable_and_sensitive() -> None:
    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)

    # Recomputed from the record's fields ALONE under the canonicalization
    # spec of record (fields minus content_hash itself; sorted keys,
    # (",", ":") separators, ensure_ascii; OptionalValue nested under its
    # own field name as {availability, value}): an INDEPENDENT rebuild in
    # this test, never a call into the implementation.
    def nested(value: OptionalValue) -> dict:
        return {"availability": value.availability.value, "value": value.value}

    independent = {
        "as_of": full.as_of,
        "away": full.away,
        "away_goals_conceded_form": nested(full.away_goals_conceded_form),
        "away_goals_scored_form": nested(full.away_goals_scored_form),
        "away_prior_matches": full.away_prior_matches,
        "away_rest_days": nested(full.away_rest_days),
        "away_xg_form": nested(full.away_xg_form),
        "away_xg_n": full.away_xg_n,
        "competition": full.competition,
        "date": full.date,
        "feature_version": full.feature_version,
        "home": full.home,
        "home_goals_conceded_form": nested(full.home_goals_conceded_form),
        "home_goals_scored_form": nested(full.home_goals_scored_form),
        "home_prior_matches": full.home_prior_matches,
        "home_rest_days": nested(full.home_rest_days),
        "home_xg_form": nested(full.home_xg_form),
        "home_xg_n": full.home_xg_n,
        "input_digest": full.input_digest,
        "kickoff": nested(full.kickoff),
        "season": full.season,
    }
    assert set(independent) == {
        f.name for f in dataclasses.fields(FeatureVector)
    } - {"content_hash"}
    independent_payload = json.dumps(
        independent, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    recomputed = hashlib.sha256(independent_payload.encode("utf-8")).hexdigest()
    assert recomputed == full.content_hash
    # ...and equals sha256 of the implementation's own canonical payload.
    assert full.content_hash == hashlib.sha256(
        canonical_payload(full).encode("utf-8")
    ).hexdigest()
    assert independent_payload == canonical_payload(full)

    # No timestamp-looking, path-looking, seed or random substring can
    # enter the hashed payload (golden has kickoff MISSING, so no time
    # string either).
    assert not re.search(r"\d{4}-\d\d-\d\dT", independent_payload)
    assert not re.search(r"\d{2}:\d{2}", independent_payload)
    assert "/" not in independent_payload
    assert "\\" not in independent_payload
    lowered = independent_payload.lower()
    assert "seed" not in lowered
    assert "random" not in lowered
    assert "mtime" not in lowered

    # Sensitivity: one perturbed field yields a different hash; the
    # FEATURE_VERSION string is itself part of the hashed content.
    perturbed_value = dataclasses.replace(
        full, home_goals_scored_form=OptionalValue.available(999.0)
    )
    assert perturbed_value.content_hash != full.content_hash
    perturbed_version = dataclasses.replace(
        full, feature_version="features-chronological-v2"
    )
    assert perturbed_version.content_hash != full.content_hash
    # A perturbed kickoff echo changes the hash too (echo is hashed
    # content, never consumed).
    perturbed_kickoff = dataclasses.replace(
        full, kickoff=OptionalValue.available("09:45")
    )
    assert perturbed_kickoff.content_hash != full.content_hash
    # Tamper-evidence: the stored value is always recomputed from the
    # record's own fields (construction), so equal records hash equal.
    again = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert again.content_hash == full.content_hash
    assert again == full
