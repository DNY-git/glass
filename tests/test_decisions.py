"""Phase 7 acceptance criteria 1-7: the decision report builder and record.

Signature pinning (1), pinned 28-field contract with double-run
determinism (2), poisoned-future byte-identity (3), full provenance echo
(4), top-level flags and disclaimer honesty (5), the golden two-scenario
content hash (6), hash recomputability/sensitivity (7). Tests may use
randomness; app/decisions may not. No scoring metric ships this phase.
"""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import inspect
import json
import re
from pathlib import Path

import pytest

from app.decisions import REPORT_VERSION, DecisionReport, build_decision_report
from app.decisions import constants as decision_constants
from app.decisions.canonicalization import canonical_payload
from app.decisions.record import ScenarioComparison, ScenarioSpread
from app.domain import Fixture, MatchCollection, OptionalValue
from app.forecasts import Forecast, build_forecast
from app.ingestion import import_fixture
from app.models import ConvergenceStatus
from app.scenarios import Transform, TransformOp, build_scenario

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool (Phase 3 convention): 2 seasons, 60 matches,
# 6 teams. Passed UNFILTERED — nothing here applies a cutoff; the
# cutoff lives inside build_forecast and reports cannot see history.
ALL_MATCHES: tuple
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

# The golden fixture pair (criterion 6): dated early season two, so the
# fit CONVERGES with a real pre-cutoff sample yet flags stay non-trivial
# (insufficient_data True, all six teams insufficient — flags exercised),
# no history match shares its natural key, and scenario deltas/spread
# are non-zero (non-trivial comparisons, not the empty-scenario case).
GOLDEN_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2024-08-31",
    home="Coralgate Athletic",
    away="Harbourlight Comets",
    kickoff=OptionalValue.missing(),
)

# The Phase 3 early-cutoff fixture (criterion 5): SINGULAR_SYSTEM +
# insufficient flags scream while the probabilities stay normalized.
EARLY_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2024-08-17",
    home="Coralgate Athletic",
    away="Harbourlight Comets",
    kickoff=OptionalValue.missing(),
)

# The D field contract, pinned in order (criterion 2; Phases 9+ depend
# on it — brief design decision 4): fixture block, provenance echoes,
# sample, flags, disclaimer, estimates, comparisons, spread, hash.
REPORT_FIELD_NAMES = (
    "competition", "season", "date", "home", "away", "kickoff", "as_of",
    "report_version", "model_version", "input_digest", "forecast_version",
    "forecast_content_hash", "sample_matches", "sample_goals",
    "convergence_status", "insufficient_data", "insufficient_teams",
    "disclaimer", "lambda_home", "lambda_away", "max_goals", "dropped_mass",
    "outcome_home", "outcome_draw", "outcome_away",
    "scenario_comparisons", "scenario_spread", "content_hash",
)
COMPARISON_FIELD_NAMES = (
    "label", "transforms", "outcome_home", "outcome_draw", "outcome_away",
    "delta_home", "delta_draw", "delta_away",
)
SPREAD_FIELD_NAMES = ("outcome", "minimum", "maximum", "spread")

# GOLDEN PIN (criterion 6), from a REAL run of this code on this
# interpreter (CPython 3.12.3; json floats = shortest round-trip repr):
#   fc = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
#   fc.content_hash == 53df65d135d2cca725f1c38901434c42f7c9677ba6d03d3db68e102b198d3f16
#   s1 = build_scenario(fc.fitted, (Transform("Coralgate Athletic",
#         TransformOp.ATTACK, 1.15),), label="home-sharper")
#   s2 = build_scenario(fc.fitted, (Transform("Harbourlight Comets",
#         TransformOp.DEFENCE, 0.85),), label="away-leakier")
#   build_decision_report(fc, scenarios=(s1, s2)).content_hash == <literal below>
# Provenance (forecast hash 53df65...), flags (CONVERGED +
# insufficient_data True + six insufficient teams, sample 9/21),
# comparisons (delta_home -0.01627140195579818 / +0.007036092188271614)
# and spread (home 0.023307494144069796, non-zero) are exercised.
# Version-local: re-derive (never widen) on any interpreter,
# canonicalization, or REPORT_VERSION change.
GOLDEN_CONTENT_HASH = "00929af76bb833b741db5ae038a08913321eed976d775e654c36094009224768"
GOLDEN_FORECAST_HASH = "53df65d135d2cca725f1c38901434c42f7c9677ba6d03d3db68e102b198d3f16"


def _golden_scenarios(forecast: Forecast) -> tuple:
    """The documented golden pair: two labeled scenarios on own fitted."""
    return (
        build_scenario(
            forecast.fitted,
            (Transform("Coralgate Athletic", TransformOp.ATTACK, 1.15),),
            label="home-sharper",
        ),
        build_scenario(
            forecast.fitted,
            (Transform("Harbourlight Comets", TransformOp.DEFENCE, 0.85),),
            label="away-leakier",
        ),
    )


def _walk_values(value):
    """Yield every nested value of frozen dataclasses/tuples (record walk)."""
    yield value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _walk_values(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _walk_values(item)


def _string_values(value) -> list[str]:
    return [item for item in _walk_values(value) if isinstance(item, str)]


def _numeric_values(value) -> list[float]:
    return [
        item
        for item in _walk_values(value)
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    ]


def _extreme_match(
    date: str, home_goals: int, away_goals: int, *, home: str = "Coralgate Athletic"
):
    """An in-schema match with an extreme scoreline, for poisoning."""
    from app.domain import Match, Score

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


def test_build_decision_report_signature_pins_no_matches_no_time() -> None:
    # Criterion 1 (A2; decision 2): signature is exactly (forecast, *,
    # scenarios=()) — no matches/as_of/cutoff/date/history parameter.
    parameters = inspect.signature(build_decision_report).parameters
    assert tuple(parameters) == ("forecast", "scenarios")
    for banned in ("matches", "as_of", "cutoff", "date", "history", "seed"):
        assert banned not in parameters
    assert parameters["forecast"].default is inspect.Parameter.empty
    assert parameters["scenarios"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["scenarios"].default == ()

    # Type-pinned input: non-Forecast raises; scenarios is keyword-only.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    with pytest.raises(TypeError):
        build_decision_report("not a forecast")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        build_decision_report(ALL_MATCHES)  # type: ignore[arg-type]
    scenario = _golden_scenarios(forecast)[0]
    with pytest.raises(TypeError):
        build_decision_report(forecast, [scenario])  # type: ignore[misc]

    # Contract version pinned (developer answer Q1) and echoed.
    assert REPORT_VERSION == "decision-report-v1"
    assert build_decision_report(forecast).report_version == REPORT_VERSION
    report = build_decision_report(forecast, scenarios=_golden_scenarios(forecast))
    assert report.report_version == REPORT_VERSION
    assert report.as_of == forecast.as_of == GOLDEN_FIXTURE.date

    # The record is frozen (setattr raises).
    with pytest.raises(AttributeError):
        report.content_hash = "x" * 64  # type: ignore[misc]

    # A6/decision 8: constants.py defines exactly REPORT_VERSION and
    # DISCLAIMER — no threshold, knob, or decision-rule constant.
    module_names = {name for name in vars(decision_constants) if not name.startswith("__")}
    assert module_names == {"REPORT_VERSION", "DISCLAIMER"}


def test_field_contract_frozen_and_double_run_identical() -> None:
    # Criterion 2 (A5; decision 4): exact pinned 28-field contract in
    # order plus nested contracts; two calls on the same input are
    # field-for-field identical; no field value is a dict/set/list.
    assert tuple(f.name for f in dataclasses.fields(DecisionReport)) == REPORT_FIELD_NAMES
    assert tuple(f.name for f in dataclasses.fields(ScenarioComparison)) == COMPARISON_FIELD_NAMES
    assert tuple(f.name for f in dataclasses.fields(ScenarioSpread)) == SPREAD_FIELD_NAMES

    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    scenarios = _golden_scenarios(forecast)
    first = build_decision_report(forecast, scenarios=scenarios)
    second = build_decision_report(forecast, scenarios=scenarios)
    assert first == second
    assert first.content_hash == second.content_hash
    assert repr(first) == repr(second)
    assert re.fullmatch(r"[0-9a-f]{64}", first.content_hash)

    for field in dataclasses.fields(DecisionReport):
        value = getattr(first, field.name)
        assert not isinstance(value, (dict, set, list)), field.name
    for nested in (*first.scenario_comparisons, *(first.scenario_spread or ())):
        for field in dataclasses.fields(type(nested)):
            value = getattr(nested, field.name)
            assert not isinstance(value, (dict, set, list)), field.name

    # String fields are only names/dates/enum-ish/64-hex/disclaimer.
    strings = _string_values(first)
    assert strings, "expected string fields on the report"
    for text in strings:
        if re.fullmatch(r"[0-9a-f]{64}", text):
            continue
        if text == decision_constants.DISCLAIMER:
            continue
        assert re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9 _.'\-]*", text), text
    joined = "|".join(strings)
    assert str(REPO_ROOT) not in joined  # no path string anywhere
    assert not re.search(r"\d{4}-\d\d-\d\dT", joined)  # no ISO datetime
    assert not re.search(r"\d{2}:\d{2}", joined)  # no clock-time string

    # No field named after a banned quantity or advice framing.
    banned = {
        "mc_stderr", "n_sims", "seed", "frequency", "mean", "average",
        "ensemble", "aggregate", "recommendation", "pick", "tip", "advice",
        "value", "edge", "confidence", "ev",
    }
    for record_type in (DecisionReport, ScenarioComparison, ScenarioSpread):
        for field in dataclasses.fields(record_type):
            assert field.name not in banned, field.name
            assert not field.name.startswith("counts_"), field.name


def test_poisoned_future_cannot_change_report() -> None:
    # Criterion 3 (A2): poisoned future matches dated AT the fixture
    # date and later (extreme scorelines, injected teams) must yield a
    # field-for-field identical forecast and report including both
    # content hashes — strict < inside fit excludes them silently.
    clean_forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    clean_report = build_decision_report(
        clean_forecast, scenarios=_golden_scenarios(clean_forecast)
    )

    poisoned = list(ALL_MATCHES) + [
        # Dated AT the fixture date (strict < excludes it) and later;
        # extreme scorelines; none shares the fixture's exact natural
        # key (that separate refusal is build_forecast's criterion 2).
        _extreme_match("2024-08-31", 20, 0),
        _extreme_match("2024-09-15", 0, 19, home="Quarryhill Zenith"),
        _extreme_match("2025-01-10", 18, 1, home="Silverpine Rovers"),
        _extreme_match("2024-10-01", 9, 9, home="Northwind Pharos"),
    ]
    poisoned_forecast = build_forecast(poisoned, GOLDEN_FIXTURE)
    poisoned_report = build_decision_report(
        poisoned_forecast, scenarios=_golden_scenarios(poisoned_forecast)
    )

    assert poisoned_forecast == clean_forecast  # frozen ==: incl. hash
    assert poisoned_forecast.content_hash == clean_forecast.content_hash
    assert poisoned_report == clean_report  # frozen ==: incl. hash
    assert poisoned_report.content_hash == clean_report.content_hash
    assert poisoned_forecast.fitted.teams == clean_forecast.fitted.teams
    assert "Northwind Pharos" not in poisoned_forecast.fitted.teams


def test_forecast_provenance_echo() -> None:
    # Criterion 4 (A5): every echo equals its source exactly, kickoff
    # MISSING is never defaulted, outcomes are copied (never
    # recomputed), and an equal-but-distinct Forecast re-derives a
    # byte-identical report.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    report = build_decision_report(
        forecast, scenarios=_golden_scenarios(forecast)
    )

    assert report.forecast_version == forecast.forecast_version
    assert report.forecast_content_hash == forecast.content_hash
    assert report.model_version == forecast.fitted.model_version
    assert report.input_digest == forecast.fitted.input_digest
    assert report.as_of == forecast.as_of
    assert report.sample_matches == forecast.fitted.sample_size.matches
    assert report.sample_goals == forecast.fitted.sample_size.goals

    # Fixture block copied; kickoff MISSING never defaulted.
    assert report.competition == forecast.competition
    assert report.season == forecast.season
    assert report.date == forecast.date
    assert report.home == forecast.home
    assert report.away == forecast.away
    assert report.kickoff == forecast.kickoff
    assert report.kickoff.availability.value == "MISSING"
    assert report.kickoff.value is None

    # Matrix essentials and analytic outcomes copied at full precision.
    assert report.lambda_home == forecast.lambda_home
    assert report.lambda_away == forecast.lambda_away
    assert report.max_goals == forecast.max_goals
    assert report.dropped_mass == forecast.dropped_mass
    assert report.outcome_home == forecast.outcome_home
    assert report.outcome_draw == forecast.outcome_draw
    assert report.outcome_away == forecast.outcome_away

    # An equal-but-distinct Forecast re-derives a byte-identical report.
    rebuilt = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    assert rebuilt is not forecast and rebuilt == forecast
    twin = build_decision_report(rebuilt, scenarios=_golden_scenarios(rebuilt))
    assert twin == report
    assert twin.content_hash == report.content_hash
    assert canonical_payload(twin) == canonical_payload(report)
    assert repr(twin) == repr(report)


def test_flags_at_top_level_and_disclaimer_honesty() -> None:
    # Criterion 5 (A1/A4): flags are TOP-LEVEL DecisionReport fields;
    # an early-cutoff SINGULAR_SYSTEM/insufficient forecast shows its
    # flags beside plausible-looking normalized probabilities — both
    # visible, no threshold judging it (A6).
    for flag in ("convergence_status", "insufficient_data", "insufficient_teams", "dropped_mass"):
        assert flag in REPORT_FIELD_NAMES, flag
        assert flag not in COMPARISON_FIELD_NAMES, flag
        assert flag not in SPREAD_FIELD_NAMES, flag

    forecast = build_forecast(ALL_MATCHES, EARLY_FIXTURE)
    report = build_decision_report(forecast)
    assert report.convergence_status is ConvergenceStatus.SINGULAR_SYSTEM
    assert report.convergence_status.value == "SINGULAR_SYSTEM"
    assert report.insufficient_data is True
    assert report.insufficient_teams  # flags scream, all six teams
    # Plausible-looking normalized probabilities stay present beside
    # the screaming flags (no field hidden, no threshold applied).
    for outcome in (report.outcome_home, report.outcome_draw, report.outcome_away):
        assert 0.0 < outcome < 1.0
    total = report.outcome_home + report.outcome_draw + report.outcome_away
    assert abs(total - 1.0) < 1e-12

    # disclaimer == constants.DISCLAIMER exactly, containing every
    # pinned substring (A1: the anti-ensemble clause answered, not
    # silent — no-second-independent-model / never-averaged included).
    assert report.disclaimer == decision_constants.DISCLAIMER
    for substring in (
        "In-sample analytic estimates",  # the in-sample-estimate statement
        "synthetic fixture data",  # the synthetic-data caveat
        "pending chronological evaluation in Phases 9 and 11",  # pending
        "not evidence of accuracy",  # the not-evidence statement
        "No second independent model exists",  # no second model
        "never averaged or ensembled",  # never averaged/ensembled
    ):
        assert substring in report.disclaimer, substring


def test_golden_report_content_hash() -> None:
    # Criterion 6 (A5; version-local golden discipline): one golden
    # pin on the documented (forecast, two-scenario) pair above —
    # exercises provenance, flags, comparisons, and spread; never the
    # empty-scenario trivial case. Re-derive, never widen.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    assert forecast.content_hash == GOLDEN_FORECAST_HASH
    report = build_decision_report(forecast, scenarios=_golden_scenarios(forecast))
    assert report.content_hash == GOLDEN_CONTENT_HASH
    assert re.fullmatch(r"[0-9a-f]{64}", GOLDEN_CONTENT_HASH)
    # The pair is genuinely non-trivial: two comparisons, a three-way
    # spread, and non-zero deltas (derivation comments pinned above).
    assert len(report.scenario_comparisons) == 2
    assert report.scenario_spread is not None and len(report.scenario_spread) == 3
    assert any(
        comparison.delta_home != 0.0 for comparison in report.scenario_comparisons
    )
    assert all(entry.spread > 0.0 for entry in report.scenario_spread)
    assert report.insufficient_data is True  # flags exercised, not default


def test_content_hash_recomputable_and_sensitive() -> None:
    # Criterion 7 (A5): content_hash recomputed from the record's
    # fields alone (fields minus content_hash, under the canonicalization
    # spec of record) equals the stored value; an independent
    # sha256(canonical_payload.encode()).hexdigest() agrees; one
    # perturbed top-level field and one perturbed nested field each
    # change the hash; the payload carries no timestamp-looking, path-
    # looking, environment, seed, random, or MC-quantity substring.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    report = build_decision_report(forecast, scenarios=_golden_scenarios(forecast))

    payload = canonical_payload(report)
    recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    assert recomputed == report.content_hash

    # Recomputed from the fields minus content_hash: the payload's key
    # set is exactly the record's field set minus content_hash.
    parsed = json.loads(payload)
    assert set(parsed) == set(REPORT_FIELD_NAMES) - {"content_hash"}
    # The key itself is absent (the substring also occurs inside
    # "forecast_content_hash", so match the quoted key).
    assert '"content_hash":' not in payload

    # Sensitivity: one perturbed top-level field changes the hash.
    perturbed_top = dataclasses.replace(report, season="2025-26-rebuilt")
    assert perturbed_top.content_hash != report.content_hash

    # Nested coverage: one perturbed nested field (a scenario label)
    # changes the report hash.
    perturbed_nested = dataclasses.replace(
        report,
        scenario_comparisons=tuple(
            dataclasses.replace(entry, label=entry.label + "-x")
            for entry in report.scenario_comparisons
        ),
    )
    assert perturbed_nested.content_hash != report.content_hash

    # The canonical payload contains no timestamp-looking, path-looking,
    # environment, seed, random, or MC-quantity substring.
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", payload)
    assert "/" not in payload and "\\" not in payload
    assert str(REPO_ROOT) not in payload
    for environment_token in ("PATH", "HOME", "USER", "PYTHON"):
        assert environment_token not in payload, environment_token
    for banned_substring in (
        "seed", "random", "mc_stderr", "counts_home", "counts_draw",
        "counts_away", "n_sims", "sim_version", "frequency",
    ):
        assert banned_substring not in payload, banned_substring
