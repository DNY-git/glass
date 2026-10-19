"""Phase 6 acceptance criteria 1-7: the feature engine core.

Signature pinning with the cutoff inside (1), fixture-in-history
refusal (2), poisoned-future byte-identity (3), the pinned decision-4
field contract with double-run determinism (4), input-digest parity
with FittedParams (5), input-order independence with canonical
tie-break and dedup (6), and the strictly-before-cutoff window golden
(7). Hand-built goldens are derived in comments from these exact
inputs (version-local golden discipline).
"""

from __future__ import annotations

import dataclasses
import inspect
import re
from pathlib import Path

import pytest

from app.domain import (
    Fixture,
    Match,
    MatchCollection,
    OptionalValue,
    Score,
    Xg,
)
from app.features import FEATURE_VERSION, FeatureVector, compute_features
from app.forecasts import build_forecast
from app.ingestion import import_fixture

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool (Phase 3/5 convention): 2 seasons, 60
# matches, 6 teams, passed UNFILTERED — the cutoff must be applied
# inside compute_features, never at this call site.
ALL_MATCHES: tuple[Match, ...]
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

# The golden fixture pair: mid-late season 2, after the xG onset (the
# first ten 2025-26 matches carry xG), so both sides' form fields are
# AVAILABLE and the xG branch runs with n_xg >= 1. Its natural key
# matches no pool match (that day's real pairings differ).
GOLDEN_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-09-06",
    home="Emberfield Kestrels",
    away="Silverpine Rovers",
    kickoff=OptionalValue.missing(),
)

# The decision-4 field contract, pinned in order (criterion 4;
# Phases 9/11 depend on it — brief design decision 4).
FEATURE_VECTOR_FIELD_NAMES = (
    "competition",
    "season",
    "date",
    "home",
    "away",
    "kickoff",
    "as_of",
    "feature_version",
    "input_digest",
    "home_goals_scored_form",
    "home_goals_conceded_form",
    "home_rest_days",
    "home_xg_form",
    "home_xg_n",
    "home_prior_matches",
    "away_goals_scored_form",
    "away_goals_conceded_form",
    "away_rest_days",
    "away_xg_form",
    "away_xg_n",
    "away_prior_matches",
    "content_hash",
)

# History-dependent fields must be OptionalValue (MISSING <=> None);
# the count fields are plain ints (0 is a true exact fact).
HISTORY_DEPENDENT_FIELDS = (
    "home_goals_scored_form",
    "home_goals_conceded_form",
    "home_rest_days",
    "home_xg_form",
    "away_goals_scored_form",
    "away_goals_conceded_form",
    "away_rest_days",
    "away_xg_form",
)
COUNT_FIELDS = ("home_xg_n", "home_prior_matches", "away_xg_n", "away_prior_matches")


def _match(
    date: str,
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
        date=date,
        home=home,
        away=away,
        score=Score(home_goals, away_goals),
        round_label=None,
        kickoff=OptionalValue.missing(),
        xg=OptionalValue.missing(),
    )


def _extreme_match(date: str, home_goals: int, away_goals: int) -> Match:
    """An in-schema match with an extreme scoreline, for poisoning."""
    return Match(
        competition="Obsidian Coast League",
        season="2025-26",
        date=date,
        home="Quarryhill Zenith",
        away="Harbourlight Comets",
        score=Score(home_goals, away_goals),
        round_label=None,
        kickoff=OptionalValue.missing(),
        xg=OptionalValue.available(Xg(home=19.5, away=0.1)),
    )


def test_compute_features_signature_pins_no_time_parameter() -> None:
    # Criterion 1 (F1): the signature is exactly (matches, fixture) —
    # no as_of, cutoff, date, history, seed, or any time-like parameter
    # exists to forget; the cutoff IS fixture.date, derived inside.
    parameters = inspect.signature(compute_features).parameters
    assert tuple(parameters) == ("matches", "fixture")
    for banned in ("as_of", "cutoff", "date", "history", "seed"):
        assert banned not in parameters
    # Calling without the fixture is a TypeError, not a default cutoff.
    with pytest.raises(TypeError):
        compute_features(ALL_MATCHES)  # type: ignore[call-arg]

    # A scored Match where the scoreless Fixture is required: TypeError.
    with pytest.raises(TypeError):
        compute_features(ALL_MATCHES, ALL_MATCHES[0])  # type: ignore[arg-type]

    # The contract version is pinned, and every vector echoes it and
    # as_of == fixture.date exactly (a plain date string, not a datetime).
    assert FEATURE_VERSION == "features-chronological-v1"
    for target in (GOLDEN_FIXTURE,):
        vector = compute_features(ALL_MATCHES, target)
        assert vector.feature_version == FEATURE_VERSION
        assert vector.as_of == target.date
        assert isinstance(vector.as_of, str)
        assert not re.search(r"\d{4}-\d\d-\d\dT", vector.as_of)

    # The record is frozen: no caller can overwrite a computed field.
    with pytest.raises(AttributeError):
        vector.content_hash = "x" * 64  # type: ignore[misc]


def test_compute_features_refuses_fixture_present_in_history() -> None:
    # Criterion 2 (F1): a fixture whose natural key appears in the
    # matches list is refused with ValueError naming the collision —
    # the target must not be its own history.
    target = max(ALL_MATCHES, key=lambda match: match.canonical_sort_key)
    colliding = Fixture(
        competition=target.competition,
        season=target.season,
        date=target.date,
        home=target.home,
        away=target.away,
        kickoff=OptionalValue.missing(),
    )
    with pytest.raises(ValueError) as excinfo:
        compute_features(ALL_MATCHES, colliding)
    message = str(excinfo.value)
    assert target.home in message and target.away in message
    assert "its own history" in message

    # The same list minus that match computes fine (nothing else about
    # the pool changed; the remaining same-date matches sit outside the
    # window silently — that is the leakage defense, not an error).
    history = [match for match in ALL_MATCHES if match.natural_key != target.natural_key]
    vector = compute_features(history, colliding)
    assert vector.as_of == target.date


def test_poisoned_future_cannot_change_features() -> None:
    # Criterion 3 (F1; PLAN section 6 layer 4 standing regression): a
    # fixture pool plus poisoned future matches — dated AT the fixture
    # date and later, extreme scorelines with extreme xG, injected
    # future teams — is field-for-field identical to the clean run,
    # including content_hash (frozen __eq__); the poisons never raise,
    # because nothing dated on/after fixture.date can enter a window.
    clean = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)

    on_date = _extreme_match("2025-09-06", 20, 0)
    poisons = [
        # Dated AT the fixture date (strict < excludes it silently) and
        # later; none shares the fixture's exact natural key — that
        # separate refusal is criterion 2.
        on_date,
        _extreme_match("2026-01-15", 0, 19),
        _extreme_match("2026-06-30", 18, 1),
        Match(  # an injected future team that must never appear
            competition="Obsidian Coast League",
            season="2025-26",
            date="2026-01-01",
            home="Northwind Pharos",
            away="Coralgate Athletic",
            score=Score(9, 9),
            round_label=None,
            kickoff=OptionalValue.missing(),
            xg=OptionalValue.missing(),
        ),
    ]
    assert any(match.date == GOLDEN_FIXTURE.date for match in poisons)
    rebuilt = compute_features(list(ALL_MATCHES) + poisons, GOLDEN_FIXTURE)

    assert rebuilt == clean  # frozen dataclass: field-for-field, incl. hash
    assert rebuilt.content_hash == clean.content_hash
    assert "Northwind Pharos" not in (rebuilt.home, rebuilt.away)


def test_field_contract_frozen_and_double_run_identical() -> None:
    # Criterion 4 (F3): the exact pinned field set in order (decision
    # 4); every history-dependent field is an OptionalValue whose
    # MISSING <=> value is None; the count fields are plain ints; two
    # runs on the same (matches, fixture) are identical including
    # content_hash and repr; no field value is a mutable collection;
    # string fields are only names, dates, the version string, and
    # 64-hex digests — no timestamp or path string anywhere.
    assert tuple(field.name for field in dataclasses.fields(FeatureVector)) == (
        FEATURE_VECTOR_FIELD_NAMES
    )

    full = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    empty_target = Fixture(
        competition="Obsidian Coast League",
        season="2025-26",
        date="2025-06-01",
        home="Nowhere United",
        away="Null County",
        kickoff=OptionalValue.missing(),
    )
    for vector in (full, compute_features([], empty_target)):
        for name in HISTORY_DEPENDENT_FIELDS:
            value = getattr(vector, name)
            assert isinstance(value, OptionalValue), name
            assert (value.value is None) == (value.availability.value == "MISSING"), name
        for name in COUNT_FIELDS:
            assert isinstance(getattr(vector, name), int), name

    second = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    assert full == second
    assert full.content_hash == second.content_hash
    assert repr(full) == repr(second)

    for field in dataclasses.fields(FeatureVector):
        value = getattr(full, field.name)
        assert not isinstance(value, (dict, set, list)), field.name

    string_values = [
        value
        for field in dataclasses.fields(FeatureVector)
        if isinstance(value := getattr(full, field.name), str)
    ]
    assert all(isinstance(value, str) for value in string_values)
    joined = "|".join(string_values)
    assert str(REPO_ROOT) not in joined  # no path string anywhere
    assert "/home/" not in joined
    assert not re.search(r"\d{2}:\d{2}", joined)  # no clock-time string
    assert not re.search(r"\d{4}-\d\d-\d\dT", joined)  # date, not datetime
    for digest in (full.input_digest, full.content_hash):
        assert re.fullmatch(r"[0-9a-f]{64}", digest)
    assert full.date == full.as_of == GOLDEN_FIXTURE.date
    assert re.fullmatch(r"\d{4}-\d\d-\d\d", full.date)
    assert full.kickoff.availability.value in ("AVAILABLE", "MISSING")


def test_input_digest_parity_with_fitted_params_cutoff_equivalence() -> None:
    # Criterion 5 (F1's sanctioned cross-check; F3/F7): the private
    # poisson helper may not be extracted (F4 byte pins), so equivalence
    # of cutoff semantics with fit is pinned by digest parity — for
    # several fixtures, compute_features(...).input_digest ==
    # build_forecast(...).fitted.input_digest EXACTLY: both consumed
    # the byte-identical strictly-pre-cutoff set under canonical_state.
    early = Fixture(  # thin pre-cutoff history (3 matches before it)
        competition="Obsidian Coast League",
        season="2024-25",
        date="2024-08-17",
        home="Coralgate Athletic",
        away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    )
    mid = Fixture(  # 3 pool matches share this date; many later ones
        competition="Obsidian Coast League",
        season="2025-26",
        date="2025-08-16",
        home="Quarryhill Zenith",
        away="Emberfield Kestrels",
        kickoff=OptionalValue.missing(),
    )
    late = Fixture(  # the whole pool is pre-cutoff
        competition="Obsidian Coast League",
        season="2025-26",
        date="2025-12-31",
        home="Coralgate Athletic",
        away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    )
    assert sum(1 for match in ALL_MATCHES if match.date == mid.date) == 3
    assert any(match.date > mid.date for match in ALL_MATCHES)

    digests = []
    for fixture in (early, mid, late, GOLDEN_FIXTURE):
        assert all(match.natural_key != fixture.natural_key for match in ALL_MATCHES)
        vector = compute_features(ALL_MATCHES, fixture)
        forecast = build_forecast(ALL_MATCHES, fixture)
        assert vector.input_digest == forecast.fitted.input_digest
        assert re.fullmatch(r"[0-9a-f]{64}", vector.input_digest)
        digests.append(vector.input_digest)
    # Different pre-cutoff sets must yield different digests.
    assert len(set(digests)) == len(digests)


def test_input_order_independence_and_canonical_tie_break() -> None:
    # Criterion 6 (F1/decision 10): the same matches permuted by a
    # LITERAL index list (no RNG anywhere) yield a field-for-field
    # identical vector — input order never leaks.
    permutation = [
        59, 0, 58, 1, 57, 2, 56, 3, 55, 4, 54, 5, 53, 6, 52, 7, 51, 8,
        50, 9, 49, 10, 48, 11, 47, 12, 46, 13, 45, 14, 44, 15, 43, 16,
        42, 17, 41, 18, 40, 19, 39, 20, 38, 21, 37, 22, 36, 23, 35, 24,
        34, 25, 33, 26, 32, 27, 31, 28, 30, 29,
    ]
    assert sorted(permutation) == list(range(60))
    forward = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    permuted = compute_features([ALL_MATCHES[i] for i in permutation], GOLDEN_FIXTURE)
    assert permuted == forward

    # Hand-built history: TWO same-date matches for one team (the tie)
    # straddle the window boundary — canonical order, never input
    # order, decides which one is the 5th-oldest and enters the window.
    # Pumas < Zebras in the (home, away) tie-break, so the 9-0 Pumas
    # match is the excluded one; a mean including it would be 2.6, not
    # 8/5 = 1.6.
    tie_history = [
        _match("2026-01-05", "Anchor Tigers", "Pumas United", 9, 0, competition="Tie Cup", season="2025-26"),
        _match("2026-01-05", "Anchor Tigers", "Zebras FC", 1, 0, competition="Tie Cup", season="2025-26"),
        _match("2026-01-12", "Anchor Tigers", "Zebras FC", 2, 1, competition="Tie Cup", season="2025-26"),
        _match("2026-01-19", "Anchor Tigers", "Pumas United", 0, 3, competition="Tie Cup", season="2025-26"),
        _match("2026-01-26", "Anchor Tigers", "Zebras FC", 1, 1, competition="Tie Cup", season="2025-26"),
        _match("2026-02-02", "Anchor Tigers", "Pumas United", 4, 2, competition="Tie Cup", season="2025-26"),
    ]
    tie_fixture = Fixture(
        competition="Tie Cup",
        season="2025-26",
        date="2026-02-09",
        home="Anchor Tigers",
        away="Pumas United",
        kickoff=OptionalValue.missing(),
    )
    canonical = compute_features(tie_history, tie_fixture)
    assert canonical.home_goals_scored_form.value == 8 / 5  # (1+2+0+1+4)/5
    assert canonical.home_prior_matches == 6
    reversed_run = compute_features(list(reversed(tie_history)), tie_fixture)
    assert reversed_run == canonical  # tie-break and window never input-ordered

    # Duplicated identical entries collapse by natural key (mirroring
    # MatchCollection semantics) — prior_matches and every field stay.
    duplicated = compute_features(tie_history + [tie_history[2]], tie_fixture)
    assert duplicated == canonical
    assert duplicated.home_prior_matches == 6


def test_window_golden_strictly_before_cutoff() -> None:
    # Criterion 7 (F1): hand-computed golden for this documented pair.
    # The window is exactly the team's last FORM_WINDOW=5 matches
    # strictly BEFORE fixture.date in canonical order — the Alpha match
    # dated exactly AT the cutoff (9-0) is excluded, which is why
    # prior_matches is 5, not 6.
    # Derivation (window in canonical order, Alpha Rovers' goals):
    #   scored   = 1 + 2 + 4 + 1 + 3 = 11  -> 11/5 = 2.2
    #   conceded = 0 + 1 + 0 + 2 + 1 =  4  ->  4/5 = 0.8
    # Beta City's window:
    #   scored   = 0 + 1 + 2 + 5 + 4 = 12  -> 12/5 = 2.4
    #   conceded = 2 + 1 + 3 + 0 + 1 =  7  ->  7/5 = 1.4
    # Full float precision: sum/5 at the literal values, no rounding.
    at_cutoff = _match(
        "2026-03-01", "Alpha Rovers", "Gamma Wanderers", 9, 0,
        competition="Continental Cup", season="2025-26",
    )
    history = [
        _match("2026-01-05", "Alpha Rovers", "Gamma Wanderers", 1, 0, competition="Continental Cup", season="2025-26"),
        _match("2026-01-12", "Delta Mariners", "Alpha Rovers", 1, 2, competition="Continental Cup", season="2025-26"),
        _match("2026-01-19", "Alpha Rovers", "Gamma Wanderers", 4, 0, competition="Continental Cup", season="2025-26"),
        _match("2026-01-26", "Delta Mariners", "Alpha Rovers", 2, 1, competition="Continental Cup", season="2025-26"),
        _match("2026-02-02", "Alpha Rovers", "Gamma Wanderers", 3, 1, competition="Continental Cup", season="2025-26"),
        at_cutoff,  # dated exactly at fixture.date — must stay outside
        _match("2026-01-06", "Beta City", "Gamma Wanderers", 0, 2, competition="Continental Cup", season="2025-26"),
        _match("2026-01-13", "Beta City", "Delta Mariners", 1, 1, competition="Continental Cup", season="2025-26"),
        _match("2026-01-20", "Epsilon United", "Beta City", 3, 2, competition="Continental Cup", season="2025-26"),
        _match("2026-01-27", "Beta City", "Gamma Wanderers", 5, 0, competition="Continental Cup", season="2025-26"),
        _match("2026-02-03", "Epsilon United", "Beta City", 1, 4, competition="Continental Cup", season="2025-26"),
    ]
    fixture = Fixture(
        competition="Continental Cup",
        season="2025-26",
        date="2026-03-01",
        home="Alpha Rovers",
        away="Beta City",
        kickoff=OptionalValue.missing(),
    )
    vector = compute_features(history, fixture)

    # The at-cutoff match never enters: prior_matches == 5 for both
    # full-history sides, and dropping it entirely yields the identical
    # record (same consumed set, same digest, same hash).
    assert vector.home_prior_matches == 5
    assert vector.away_prior_matches == 5
    without = compute_features(
        [match for match in history if match.natural_key != at_cutoff.natural_key],
        fixture,
    )
    assert without == vector

    # Exact hand-computed means at full precision.
    assert vector.home_goals_scored_form.value == 11 / 5 == 2.2
    assert vector.home_goals_conceded_form.value == 4 / 5 == 0.8
    assert vector.away_goals_scored_form.value == 12 / 5 == 2.4
    assert vector.away_goals_conceded_form.value == 7 / 5 == 1.4
    # Would the 9-0 leak in, the home mean would be (11+9)/6, not 2.2.
    assert vector.home_goals_scored_form.value != 20 / 6
