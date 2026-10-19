"""Phase 7 acceptance criteria 8-12: scenario comparisons, spread, refusals.

Side-by-side comparisons with full-precision deltas and canonical order
(8), the no-collapse absence pins (9), min/max/spread reported and never
collapsed (10), provenance/applicability refusals (11), and the
analytic-only probability contract with a fixed-seed Monte-Carlo foil
unequal to every report number (12). Tests may use randomness; the
report package may not. No scoring metric ships this phase.
"""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
from pathlib import Path

import pytest

from app.decisions import build_decision_report
from app.decisions import constants as decision_constants
from app.decisions.canonicalization import canonical_payload
from app.decisions.record import DecisionReport, ScenarioComparison, ScenarioSpread
from app.domain import Fixture, MatchCollection, OptionalValue
from app.forecasts import Forecast, build_forecast
from app.ingestion import import_fixture
from app.models import FittedParams, outcome_probs
from app.scenarios import (
    MULTIPLIER_MAX,
    MULTIPLIER_MIN,
    Scenario,
    Transform,
    TransformOp,
    build_scenario,
    scenario_matrix,
)
from app.simulation import simulate

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool (Phase 3 convention), unfiltered — the cutoff
# lives inside build_forecast.
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

# The golden fixture pair of criterion 6, reused for criteria 8-12 so
# every scenario number in this file derives from one documented fit.
GOLDEN_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2024-08-31",
    home="Coralgate Athletic",
    away="Harbourlight Comets",
    kickoff=OptionalValue.missing(),
)

# The documented golden pair, built from the forecast's own fitted.
# Canonical label order: away-leakier < home-sharper.
HOME_SHARPENER = Transform("Coralgate Athletic", TransformOp.ATTACK, 1.15)
AWAY_LEAKIER = Transform("Harbourlight Comets", TransformOp.DEFENCE, 0.85)


def _golden_pair(forecast: Forecast) -> tuple[Scenario, Scenario]:
    return (
        build_scenario(forecast.fitted, (HOME_SHARPENER,), label="home-sharper"),
        build_scenario(forecast.fitted, (AWAY_LEAKIER,), label="away-leakier"),
    )


def _analytic(scenario: Scenario, forecast: Forecast) -> tuple[float, float, float]:
    """Independent recomputation through the ONE cell-math path —
    outcome_probs(scenario_matrix(...).matrix), the exact expression
    the builder uses; every asserted number is this tuple, not a copy.
    """
    return outcome_probs(scenario_matrix(scenario, forecast.home, forecast.away).matrix)


def _walk_numbers(value):
    """Yield every nested numeric value of the frozen records."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _walk_numbers(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _walk_numbers(item)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield value


def _all_keys(value) -> set[str]:
    """Every mapping key appearing anywhere in a parsed payload."""
    keys: set[str] = set()
    if isinstance(value, dict):
        keys.update(value)
        for item in value.values():
            keys.update(_all_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.update(_all_keys(item))
    return keys


def test_scenario_comparisons_side_by_side_with_deltas() -> None:
    # Criterion 8 (A1): two labeled scenarios from the forecast's own
    # fitted, two entries in canonical label order, order-independent
    # to the byte, verbatim echo, analytic outcomes at full precision,
    # exact deltas against the report's own baseline numbers.
    assert MULTIPLIER_MIN <= HOME_SHARPENER.multiplier <= MULTIPLIER_MAX
    assert MULTIPLIER_MIN <= AWAY_LEAKIER.multiplier <= MULTIPLIER_MAX

    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    first, second = _golden_pair(forecast)
    report = build_decision_report(forecast, scenarios=(first, second))

    assert len(report.scenario_comparisons) == 2
    # Canonical order by label, regardless of the caller's order.
    assert tuple(c.label for c in report.scenario_comparisons) == (
        "away-leakier",
        "home-sharper",
    )

    # Shuffled input yields a field-for-field identical report.
    shuffled = build_decision_report(forecast, scenarios=(second, first))
    assert shuffled == report
    assert shuffled.content_hash == report.content_hash

    # Verbatim echo of label and transforms on every entry.
    by_label = {c.label: c for c in report.scenario_comparisons}
    assert by_label["home-sharper"].transforms == (HOME_SHARPENER,)
    assert by_label["away-leakier"].transforms == (AWAY_LEAKIER,)

    # Each entry's outcome_* equals the analytic path EXACTLY (full
    # precision; real-run derivation):
    #   home-sharper (0.1645582842462347, 0.38599292907976274, 0.44944878667400257)
    #   away-leakier (0.1878657783903045, 0.3799194293169669, 0.4322147922927287)
    for scenario in (first, second):
        home_p, draw_p, away_p = _analytic(scenario, forecast)
        entry = by_label[scenario.label]
        assert entry.outcome_home == home_p
        assert entry.outcome_draw == draw_p
        assert entry.outcome_away == away_p

    # Deltas are exact arithmetic differences against the report's own
    # baseline numbers, never rounded (real-run derivation):
    #   home-sharper home -0.01627140195579818, draw +0.004203810592329993,
    #                 away +0.012067591363468189
    #   away-leakier home +0.007036092188271614, draw -0.0018696891704658714,
    #                 away -0.0051664030178056874
    for entry in report.scenario_comparisons:
        assert entry.delta_home == entry.outcome_home - report.outcome_home
        assert entry.delta_draw == entry.outcome_draw - report.outcome_draw
        assert entry.delta_away == entry.outcome_away - report.outcome_away

    # Baseline numbers live once, on the report; no entry duplicates
    # them (the entry contract has no baseline or lambda field).
    for entry in report.scenario_comparisons:
        names = {f.name for f in dataclasses.fields(entry)}
        assert not any(n.startswith(("baseline", "lambda")) for n in names)
        assert entry.outcome_home != report.outcome_home  # entries differ


def test_no_collapse_no_mean_no_ensemble() -> None:
    # Criterion 9 (A1/A7 BLOCKER; A6): (i) no record field and no
    # payload key is a collapse name; (ii) no weight/aggregate/combine
    # parameter; (iii) the arithmetic-mean triple of the two entries
    # appears NOWHERE in the report. Only min/max/spread aggregate.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    first, second = _golden_pair(forecast)
    report = build_decision_report(forecast, scenarios=(first, second))

    # (i) Field names and payload keys: no collapse vocabulary.
    collapse = {"mean", "average", "ensemble", "aggregate", "blend", "composite"}
    for record_type in (DecisionReport, ScenarioComparison, ScenarioSpread):
        for field in dataclasses.fields(record_type):
            assert field.name not in collapse, field.name

    payload_keys = _all_keys(json.loads(canonical_payload(report)))
    assert payload_keys.isdisjoint(collapse)

    # (ii) No weight, aggregate, or combine parameter exists.
    parameters = inspect.signature(build_decision_report).parameters
    assert tuple(parameters) == ("forecast", "scenarios")
    assert collapse.isdisjoint(parameters)
    for banned in ("weight", "weights", "combine", "blend"):
        assert banned not in parameters

    # (iii) The computed arithmetic-mean triple appears nowhere. Both
    # entries genuinely differ on every outcome (real-run means:
    # home 0.1762120313182696, draw 0.3829561791983648,
    # away 0.44083178948336565), each different from BOTH entries.
    by_label = {c.label: c for c in report.scenario_comparisons}
    a = by_label["home-sharper"]
    b = by_label["away-leakier"]
    numeric_values = set(_walk_numbers(report))
    for outcome in ("home", "draw", "away"):
        left = getattr(a, f"outcome_{outcome}")
        right = getattr(b, f"outcome_{outcome}")
        mean = (left + right) / 2
        assert mean != left and mean != right, outcome  # differs from both
        assert mean not in numeric_values, outcome  # pinned by absence

    # The only cross-scenario aggregation shipped is min/max/spread
    # (criterion 10), and no threshold constant converts it into a
    # decision (A6; criterion 1's constants pin).
    assert report.scenario_spread is not None
    for entry in report.scenario_spread:
        assert tuple(f.name for f in dataclasses.fields(entry)) == (
            "outcome",
            "minimum",
            "maximum",
            "spread",
        )
    assert {name for name in vars(decision_constants) if not name.startswith("__")} == {
        "REPORT_VERSION",
        "DISCLAIMER",
    }


def test_scenario_spread_disagreement_reported_not_collapsed() -> None:
    # Criterion 10 (A1; decision 7): >= 2 scenarios -> exactly 3 spread
    # entries in fixed order home, draw, away; min/max from the
    # entries' analytic values (derivations below); spread ==
    # maximum - minimum exactly; 1 scenario -> None; 0 -> None.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    first, second = _golden_pair(forecast)
    report = build_decision_report(forecast, scenarios=(first, second))

    assert report.scenario_spread is not None
    spread_entries = report.scenario_spread
    assert len(spread_entries) == 3
    assert tuple(entry.outcome for entry in spread_entries) == ("home", "draw", "away")

    # Independent recomputation of both entries' analytic values, with
    # the resulting spreads (real-run derivation):
    #   home 0.1645582842462347 / 0.1878657783903045 -> 0.023307494144069796
    #   draw 0.38599292907976274 / 0.3799194293169669 -> 0.006073499762795864
    #   away 0.44944878667400257 / 0.4322147922927287 -> 0.017233994381273876
    pairs = {
        "home": (0.1645582842462347, 0.1878657783903045),
        "draw": (0.38599292907976274, 0.3799194293169669),
        "away": (0.44944878667400257, 0.4322147922927287),
    }
    for entry in spread_entries:
        first_p, second_p = pairs[entry.outcome]
        analytic_first = _analytic(first, forecast)
        analytic_second = _analytic(second, forecast)
        index = {"home": 0, "draw": 1, "away": 2}[entry.outcome]
        assert analytic_first[index] == first_p  # derivation check
        assert analytic_second[index] == second_p
        assert entry.minimum == min(first_p, second_p)
        assert entry.maximum == max(first_p, second_p)
        assert entry.spread == entry.maximum - entry.minimum

    # Exactly 1 scenario: no spread exists over one hypothetical.
    single = build_decision_report(forecast, scenarios=(first,))
    assert len(single.scenario_comparisons) == 1
    assert single.scenario_spread is None

    # 0 scenarios: the trivial case must never masquerade as agreement.
    empty = build_decision_report(forecast)
    assert empty.scenario_comparisons == ()
    assert empty.scenario_spread is None

    # The spread never equals any mean of the entries.
    for entry in spread_entries:
        index = {"home": 0, "draw": 1, "away": 2}[entry.outcome]
        values = (
            _analytic(first, forecast)[index],
            _analytic(second, forecast)[index],
        )
        mean = (values[0] + values[1]) / 2
        assert entry.spread != mean
        assert entry.minimum != mean and entry.maximum != mean


def test_scenario_provenance_refusals() -> None:
    # Criterion 11 (A2): a baseline failing value inequality is
    # refused by name; a distinct-but-value-equal FittedParams is
    # accepted (value equality IS the contract); duplicate labels are
    # refused; inapplicable transforms propagate their ValueError —
    # never a silently inert number identical to baseline.
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    good = build_scenario(forecast.fitted, (HOME_SHARPENER,), label="home-sharper")

    # Baseline value inequality: a DIFFERENT fit is refused by name.
    other_forecast = build_forecast(
        ALL_MATCHES,
        dataclasses.replace(GOLDEN_FIXTURE, date="2024-09-14"),
    )
    assert other_forecast.fitted != forecast.fitted
    mismatched = build_scenario(
        other_forecast.fitted, (HOME_SHARPENER,), label="home-sharper"
    )
    with pytest.raises(ValueError, match="baseline does not equal"):
        build_decision_report(forecast, scenarios=(mismatched,))

    # Value equality, not identity: a value-equal copy is accepted.
    twin_fitted = dataclasses.replace(forecast.fitted)
    assert twin_fitted == forecast.fitted and twin_fitted is not forecast.fitted
    twin_scenario = build_scenario(twin_fitted, (HOME_SHARPENER,), label="home-sharper")
    report = build_decision_report(forecast, scenarios=(twin_scenario,))
    direct = build_decision_report(forecast, scenarios=(good,))
    assert report == direct
    assert report.content_hash == direct.content_hash

    # Duplicate labels: refused, never averaged or resolved silently.
    first, _ = _golden_pair(forecast)
    duplicate_a = build_scenario(forecast.fitted, (HOME_SHARPENER,), label="same")
    duplicate_b = build_scenario(forecast.fitted, (AWAY_LEAKIER,), label="same")
    with pytest.raises(ValueError, match="duplicate scenario label"):
        build_decision_report(forecast, scenarios=(duplicate_a, duplicate_b))

    # Inapplicable transform 1: a fit team NOT in this fixture — the
    # object constructs, but evaluation refuses rather than producing
    # an inert number identical to baseline.
    nonplaying = build_scenario(
        forecast.fitted,
        (Transform("Quarryhill Zenith", TransformOp.ATTACK, 1.2),),
        label="ghost",
    )
    with pytest.raises(ValueError, match="does not play in fixture"):
        build_decision_report(forecast, scenarios=(nonplaying,))

    # Inapplicable transform 2: home_advantage naming the AWAY side.
    wrong_side = build_scenario(
        forecast.fitted,
        (Transform("Harbourlight Comets", TransformOp.HOME_ADVANTAGE, 1.1),),
        label="wrong-side",
    )
    with pytest.raises(ValueError, match="not the home side"):
        build_decision_report(forecast, scenarios=(wrong_side,))


def test_analytic_only_probabilities_no_mc_quantities() -> None:
    # Criterion 12 (A4; decision 6): every comparison probability is
    # the analytic outcome_probs of its scenario matrix at full
    # precision; a fixed-seed simulate run's frequencies are asserted
    # UNEQUAL to the report's values; field contracts carry no
    # simulation quantity; no file under app/decisions imports
    # app.simulation (AST, with probes).
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    first, second = _golden_pair(forecast)
    report = build_decision_report(forecast, scenarios=(first, second))
    by_label = {c.label: c for c in report.scenario_comparisons}

    # Analytic equality at full precision through the _analytic path.
    for scenario in (first, second):
        home_p, draw_p, away_p = _analytic(scenario, forecast)
        entry = by_label[scenario.label]
        assert (entry.outcome_home, entry.outcome_draw, entry.outcome_away) == (
            home_p,
            draw_p,
            away_p,
        )

    # Fixed-seed Monte-Carlo foil (seed pinned; real run with
    # seed=20261019, n_sims=20000): baseline frequencies
    # 0.17825 / 0.3786 / 0.44315, home-sharper 0.16155 / 0.3868 /
    # 0.45165 — none equals its analytic counterpart, so a frequency
    # can never sneak in as a report number by construction here.
    foil = simulate(forecast.fitted, forecast.home, forecast.away, seed=20261019, n_sims=20000)
    baseline_freqs = (
        foil.counts_home / foil.n_sims,
        foil.counts_draw / foil.n_sims,
        foil.counts_away / foil.n_sims,
    )
    for freq, analytic in zip(
        baseline_freqs,
        (report.outcome_home, report.outcome_draw, report.outcome_away),
    ):
        assert freq != analytic

    scenario_foil = simulate(
        forecast.fitted,
        forecast.home,
        forecast.away,
        seed=20261019,
        n_sims=20000,
        scenario=first,
    )
    scenario_freqs = (
        scenario_foil.counts_home / scenario_foil.n_sims,
        scenario_foil.counts_draw / scenario_foil.n_sims,
        scenario_foil.counts_away / scenario_foil.n_sims,
    )
    entry = by_label["home-sharper"]
    for freq, analytic in zip(
        scenario_freqs,
        (entry.outcome_home, entry.outcome_draw, entry.outcome_away),
    ):
        assert freq != analytic
    # And the foil itself is outside the report's provenance surface.
    assert foil.seed == 20261019 and foil.n_sims == 20000

    # Runtime field contracts: no simulation quantity in any record.
    for record_type in (DecisionReport, ScenarioComparison, ScenarioSpread):
        for field in dataclasses.fields(record_type):
            name = field.name
            assert name not in {
                "mc_stderr",
                "n_sims",
                "seed",
                "sim_version",
                "analytic_outcome",
            }, name
            assert not name.startswith("counts_"), name

    # AST: no file under app/decisions imports app.simulation.
    decisions_dir = REPO_ROOT / "app" / "decisions"
    sources = sorted(decisions_dir.glob("*.py"))
    assert sources, "expected app/decisions modules"

    def simulation_imports(tree: ast.AST) -> list[str]:
        found: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0:2] == ["app", "simulation"]:
                        found.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if module.split(".")[0:2] == ["app", "simulation"]:
                    found.append(module)
        return found

    for path in sources:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        assert simulation_imports(tree) == [], path.name

    # Probes: app.simulation flagged, app.scenarios not.
    flagged = ast.parse("from app.simulation import simulate")
    assert simulation_imports(flagged) == ["app.simulation"]
    flagged_direct = ast.parse("import app.simulation")
    assert simulation_imports(flagged_direct) == ["app.simulation"]
    clean = ast.parse("from app.scenarios import scenario_matrix")
    assert simulation_imports(clean) == []
