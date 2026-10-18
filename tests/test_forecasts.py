"""Phase 5 acceptance criteria 1-7: the forecast builder and record.

Signature pinning with the cutoff inside (1), fixture-in-history
refusal (2), poisoned-future byte-identity (3), the pinned F2 field
contract with double-run determinism (4), the scoreless Fixture
representation (5), analytic fields and flags riding every record (6),
and the golden content hash with the canonicalization spec properties
(7). Tests may use randomness; app/forecasts may not.
"""

from __future__ import annotations

import dataclasses
import hashlib
import inspect
import math
import re
from pathlib import Path

import pytest

from app.domain import (
    Availability,
    Fixture,
    IngestedRecord,
    Match,
    MatchCollection,
    OptionalValue,
    Provenance,
    RecordLocation,
    Score,
    canonical_state,
)
from app.forecasts import (
    FORECAST_VERSION,
    Forecast,
    build_forecast,
    canonical_payload,
    content_hash,
)
from app.ingestion import import_fixture
from app.models import MODEL_VERSION, outcome_probs, scoreline_log_probs

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool (Phase 3 convention): 2 seasons, 60 matches,
# 6 teams. Passed UNFILTERED — the cutoff must be applied inside.
ALL_MATCHES: tuple[Match, ...]
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

# The golden fixture pair (criterion 7): dated after both seasons, so
# all 60 matches are pre-cutoff and the fit CONVERGES; no history match
# shares its natural key.
GOLDEN_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Coralgate Athletic",
    away="Thistledown Wanderers",
    kickoff=OptionalValue.missing(),
)

# The F2 field contract, pinned in order (criterion 4; Phases 9/11
# depend on it — brief design decision 4).
FORECAST_FIELD_NAMES = (
    "competition",
    "season",
    "date",
    "home",
    "away",
    "kickoff",
    "as_of",
    "fitted",
    "lambda_home",
    "lambda_away",
    "max_goals",
    "dropped_mass",
    "outcome_home",
    "outcome_draw",
    "outcome_away",
    "forecast_version",
    "content_hash",
)

# GOLDEN PIN (criterion 7), derived from a REAL run of this code on
# this interpreter (CPython 3.12.3; json floats = shortest round-trip
# repr), on the exact inputs above:
#   fc = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
#   fc.content_hash == <literal below>
#   fc.lambda_home  == 1.9390883757535111   (pinned alongside)
#   fc.lambda_away  == 1.3298142918755258   (pinned alongside)
# The fit is CONVERGED with sample_size 60/156. Version-local by the
# Phase 3 golden discipline: re-derive (never widen) on any
# interpreter, canonicalization, or FORECAST_VERSION change.
GOLDEN_CONTENT_HASH = "2e428d60978b251ca2ebc04b12f7d50b8a95c3a9460bf0d4b608fd7aafc346ba"
GOLDEN_LAMBDA_HOME = 1.9390883757535111
GOLDEN_LAMBDA_AWAY = 1.3298142918755258


def _extreme_match(
    date: str, home_goals: int, away_goals: int, *, home: str = "Coralgate Athletic"
) -> Match:
    """An in-schema match with an extreme scoreline, for poisoning."""
    return Match(
        competition="Obsidian Coast League",
        season="2025-26",
        date=date,
        home=home,
        away="Thistledown Wanderers",
        score=Score(home_goals, away_goals),
        round_label=None,
        kickoff=OptionalValue.missing(),
        xg=OptionalValue.missing(),
    )


def test_build_forecast_signature_pins_no_as_of_parameter() -> None:
    # Criterion 1 (F1/L1): the signature is exactly (matches, fixture)
    # — no as_of, cutoff, date, history, or any time-like parameter
    # exists to forget; the cutoff IS fixture.date, derived inside.
    parameters = inspect.signature(build_forecast).parameters
    assert tuple(parameters) == ("matches", "fixture")
    for banned in ("as_of", "cutoff", "date", "history", "seed"):
        assert banned not in parameters
    # Calling without the fixture is a TypeError, not a default cutoff.
    with pytest.raises(TypeError):
        build_forecast(ALL_MATCHES)  # type: ignore[call-arg]

    # The contract version is a non-empty string, and the record has
    # no seed field or parameter anywhere (F2: a deterministic object).
    assert isinstance(FORECAST_VERSION, str) and FORECAST_VERSION
    assert FORECAST_VERSION == "forecast-poisson-mle-v1"
    field_names = tuple(field.name for field in dataclasses.fields(Forecast))
    assert "seed" not in field_names
    assert "seed" not in inspect.signature(Forecast).parameters


def test_build_forecast_refuses_fixture_present_in_history() -> None:
    # Criterion 2 (F1): a fixture whose natural key appears in the
    # matches list is refused — the target must not be its own history
    # — and the refusal message names the collision.
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
        build_forecast(ALL_MATCHES, colliding)
    message = str(excinfo.value)
    assert target.home in message and target.away in message
    assert "its own history" in message

    # The same list minus that match builds fine (the cutoff excludes
    # the remaining same-date matches silently; all teams still fit).
    history = [match for match in ALL_MATCHES if match.natural_key != target.natural_key]
    forecast = build_forecast(history, colliding)
    assert forecast.as_of == target.date


def test_build_forecast_poisoned_future_cannot_change_forecast() -> None:
    # Criterion 3 (PLAN section 6, layer 4 standing regression): a
    # fixture pool plus poisoned future matches — dated AT the fixture
    # date and later, extreme scorelines, injected future teams — is
    # field-for-field identical to the clean build, including the
    # content hash; the poisoned matches never raise, because nothing
    # dated on/after fixture.date can enter the fit (strict <).
    clean = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)

    poisoned = list(ALL_MATCHES) + [
        # Dated AT the fixture date (strict < excludes it silently) and
        # later; extreme scorelines; none shares the fixture's exact
        # natural key — that separate refusal is criterion 2.
        _extreme_match("2025-12-31", 20, 0, home="Quarryhill Zenith"),
        _extreme_match("2026-01-15", 0, 19, home="Silverpine Rovers"),
        _extreme_match("2026-06-30", 18, 1, home="Emberfield Kestrels"),
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
    rebuilt = build_forecast(poisoned, GOLDEN_FIXTURE)

    assert rebuilt == clean  # frozen dataclass: field-for-field, incl. hash
    assert rebuilt.content_hash == clean.content_hash
    assert rebuilt.fitted.teams == clean.fitted.teams  # no future-only team
    assert "Northwind Pharos" not in rebuilt.fitted.teams


def test_forecast_field_contract_frozen_and_bit_identical_double_run() -> None:
    # Criterion 4 (F2): the exact pinned field set in order; frozen;
    # as_of == fixture.date exactly (a date string, never a datetime);
    # two builds on the same (matches, fixture) are identical including
    # content_hash and repr; no field value is a mutable collection;
    # string fields are only names/dates/enum strings/digests.
    assert tuple(field.name for field in dataclasses.fields(Forecast)) == FORECAST_FIELD_NAMES

    first = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    with pytest.raises(AttributeError):
        first.content_hash = "x" * 64  # type: ignore[misc]

    assert first.as_of == GOLDEN_FIXTURE.date
    assert isinstance(first.as_of, str)
    assert not re.search(r"\d{4}-\d\d-\d\dT", first.as_of)  # date, not datetime

    second = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    assert first == second
    assert first.content_hash == second.content_hash
    assert repr(first) == repr(second)

    for field in dataclasses.fields(Forecast):
        value = getattr(first, field.name)
        assert not isinstance(value, (dict, set, list)), field.name

    string_values = [
        value
        for field in dataclasses.fields(Forecast)
        for value in ([getattr(first, field.name)] if isinstance(getattr(first, field.name), str) else [])
    ]
    assert all(isinstance(value, str) for value in string_values)
    joined = "|".join(string_values)
    assert str(REPO_ROOT) not in joined  # no path string anywhere
    assert not re.search(r"\d{2}:\d{2}", joined)  # no clock-time string
    assert re.fullmatch(r"[0-9a-f]{64}", first.content_hash)


def test_scoreless_fixture_representation() -> None:
    # Criterion 5 (F5/decision 3): Fixture is a frozen value object in
    # app.domain with NO score attribute at all and exactly the
    # decision-3 field set; the builder's typed input accepts it; a
    # MISSING kickoff stays MISSING (never a default time); a scored
    # Match is a different type the builder refuses.
    fixture = Fixture(
        competition="Obsidian Coast League",
        season="2025-26",
        date="2025-12-31",
        home="Coralgate Athletic",
        away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    )
    assert dataclasses.is_dataclass(Fixture)
    assert Fixture.__dataclass_params__.frozen
    assert not hasattr(fixture, "score")
    assert tuple(field.name for field in dataclasses.fields(Fixture)) == (
        "competition",
        "season",
        "date",
        "home",
        "away",
        "kickoff",
    )
    with pytest.raises(AttributeError):
        fixture.home = "Someone Else"  # type: ignore[misc]

    # Type-pinned input: a Match is not a Fixture (distinct types).
    parameters = inspect.signature(build_forecast).parameters
    assert "fixture" in parameters
    assert parameters["fixture"].annotation in ("Fixture", Fixture)
    match = ALL_MATCHES[0]
    assert not isinstance(match, Fixture)
    with pytest.raises(TypeError):
        build_forecast(ALL_MATCHES, match)  # type: ignore[arg-type]

    # MISSING kickoff is echoed with its availability, never defaulted.
    forecast = build_forecast(ALL_MATCHES, fixture)
    assert forecast.kickoff.availability is Availability.MISSING
    assert forecast.kickoff.value is None


def test_forecast_analytic_fields_and_flags_ride() -> None:
    # Criterion 6 (F2/S7e): the stored probabilities are the ANALYTIC
    # outcome_probs at exact full precision (no counts, no frequencies,
    # no seed anywhere); the matrix essentials ride exactly; a flagged
    # fit's flags ride identically (plausible-looking garbage stays
    # flagged); model version and the pre-cutoff input digest ride.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)

    matrix = scoreline_log_probs(forecast.fitted, forecast.home, forecast.away)
    assert forecast.outcome_home == outcome_probs(matrix)[0]
    assert forecast.outcome_draw == outcome_probs(matrix)[1]
    assert forecast.outcome_away == outcome_probs(matrix)[2]
    # Exactly the fit's own analytic evaluation, bit-for-bit.
    from app.models import fit as fit_model

    reference = fit_model(ALL_MATCHES, GOLDEN_FIXTURE.date)
    reference_matrix = scoreline_log_probs(reference, forecast.home, forecast.away)
    assert (forecast.outcome_home, forecast.outcome_draw, forecast.outcome_away) == outcome_probs(
        reference_matrix
    )
    assert forecast.lambda_home == matrix.lambda_home
    assert forecast.lambda_away == matrix.lambda_away
    assert forecast.max_goals == matrix.max_goals
    assert forecast.dropped_mass == matrix.dropped_mass

    # The Phase 3 measured SINGULAR_SYSTEM case: a fixture dated
    # before the second matchday yields the identical flags as the
    # fit — a reported result, never a fallback estimate.
    early = Fixture(
        competition="Obsidian Coast League",
        season="2025-26",
        date="2024-08-17",
        home="Coralgate Athletic",
        away="Harbourlight Comets",
        kickoff=OptionalValue.missing(),
    )
    flagged = build_forecast(ALL_MATCHES, early)
    early_fit = fit_model(ALL_MATCHES, early.date)
    assert flagged.fitted.convergence_status is early_fit.convergence_status
    assert flagged.fitted.convergence_status.value == "SINGULAR_SYSTEM"
    assert flagged.fitted.insufficient_data is early_fit.insufficient_data is True
    assert flagged.fitted.insufficient_teams == early_fit.insufficient_teams

    # Provenance: model version and the sha256 digest of the strict
    # pre-cutoff canonical state (independently recomputed here).
    assert forecast.fitted.model_version == MODEL_VERSION
    assert re.fullmatch(r"[0-9a-f]{64}", forecast.fitted.input_digest)
    pre_cutoff = [match for match in ALL_MATCHES if match.date < GOLDEN_FIXTURE.date]
    assert len(pre_cutoff) == 60
    digest_source = MatchCollection()
    for index, match in enumerate(pre_cutoff):
        digest_source.add(
            IngestedRecord(
                match=match,
                provenance=Provenance(source_path="", sha256=""),
                location=RecordLocation(source_path="", index=index),
            )
        )
    expected_digest = hashlib.sha256(canonical_state(digest_source).encode("utf-8")).hexdigest()
    assert forecast.fitted.input_digest == expected_digest


def test_content_hash_golden_and_canonicalization_spec() -> None:
    # Criterion 7 (F3): the golden pin (derivation in the comments at
    # GOLDEN_CONTENT_HASH), hash sensitivity to any covered-field
    # change, and the canonicalization spec properties: sorted keys,
    # enums as .value strings, no timestamp / path / seed / random
    # substring in the payload, and an independent sha256 recomputation.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    assert forecast.lambda_home == GOLDEN_LAMBDA_HOME  # full-precision golden
    assert forecast.lambda_away == GOLDEN_LAMBDA_AWAY
    assert forecast.content_hash == GOLDEN_CONTENT_HASH
    assert re.fullmatch(r"[0-9a-f]{64}", GOLDEN_CONTENT_HASH)

    # Sensitivity: a hand-constructed valid Forecast with one REAL
    # perturbed by 1 ulp yields a different hash; so does a perturbed
    # flag (the hash covers every field, minus itself).
    perturbed_float = dataclasses.replace(
        forecast, lambda_home=math.nextafter(forecast.lambda_home, math.inf)
    )
    assert perturbed_float.content_hash != forecast.content_hash
    perturbed_flag = dataclasses.replace(
        forecast,
        fitted=dataclasses.replace(forecast.fitted, insufficient_data=True),
    )
    assert perturbed_flag.content_hash != forecast.content_hash

    # Canonical payload: keys sorted lexicographically at every level,
    # enums serialized as their .value strings.
    payload_text = canonical_payload(forecast)
    import json

    def key_orders(value: object) -> list[list[str]]:
        if isinstance(value, dict):
            return [list(value.keys())] + [
                order
                for nested in value.values()
                for order in key_orders(nested)
            ]
        if isinstance(value, list):
            return [
                order for nested in value for order in key_orders(nested)
            ]
        return []

    parsed = json.loads(payload_text)
    for order in key_orders(parsed):
        assert order == sorted(order), order
    assert '"convergence_status":"CONVERGED"' in payload_text
    assert '"availability":"MISSING"' in payload_text
    assert '"forecast_version":"forecast-poisson-mle-v1"' in payload_text

    # Out of the payload, always: no timestamp-looking, path-looking,
    # seed, or random substring.
    lowered = payload_text.lower()
    assert not re.search(r"\d{4}-\d\d-\d\dt", lowered)
    assert not re.search(r"\d{2}:\d{2}", lowered)
    assert "seed" not in lowered
    assert "random" not in lowered
    assert str(REPO_ROOT).lower() not in lowered
    assert "/home/" not in lowered

    # content_hash == sha256(canonical_payload.encode()).hexdigest(),
    # recomputed independently in this test.
    recomputed = hashlib.sha256(payload_text.encode("utf-8")).hexdigest()
    assert forecast.content_hash == recomputed == content_hash(forecast)
