"""Phase 4 acceptance criteria 9-15: bounded scenario exploration.

Construction validation (bounds inclusive, never clamped; NaN/inf/
non-numeric refused; label, empties, duplicates, unknown teams),
strict fixture applicability ValueErrors, the shared cell-math path
with hand-derived full-precision lambdas and an AST proof that no
FittedParams is forged and no formula is copied, flags/label/spec/
provenance echo on every output, canonical ordering under shuffled
inputs, the no-averaging/no-ensemble surface pin, and output hygiene
(frozen, tuple-only, full precision, no clock/path/env strings).
"""

from __future__ import annotations

import ast
import dataclasses
import enum
import inspect
import math
import re
from pathlib import Path

import pytest

from app.domain import MatchCollection
from app.ingestion import import_fixture
from app.models import (
    MODEL_VERSION,
    ScorelineMatrix,
    fit,
    outcome_probs,
    scoreline_log_probs,
)
from app.models.scoreline import build_scoreline_matrix, lambda_pair
from app.scenarios import (
    MULTIPLIER_MAX,
    MULTIPLIER_MIN,
    Scenario,
    ScenarioMatrix,
    Transform,
    TransformOp,
    build_scenario,
    scenario_matrix,
)
from app.simulation import simulate

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"
SCENARIOS_DIR = REPO_ROOT / "app" / "scenarios"

FULL_AS_OF = "2025-12-31"
HOME = "Coralgate Athletic"
AWAY = "Emberfield Kestrels"
NOT_PLAYING = "Harbourlight Comets"  # in the fit, not in this fixture

_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())
FITTED = fit(ALL_MATCHES, FULL_AS_OF)
HOME_INDEX = FITTED.teams.index(HOME)
AWAY_INDEX = FITTED.teams.index(AWAY)


def _build(transforms, label: str = "test scenario") -> Scenario:
    return build_scenario(FITTED, tuple(transforms), label=label)


def _walk_values(value):
    """Yield every nested value of frozen dataclasses/tuples (A7 walk)."""
    yield value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _walk_values(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _walk_values(item)


def _string_values(value):
    for item in _walk_values(value):
        if isinstance(item, str):
            yield item


def test_scenario_construction_validation_bounds_and_label() -> None:
    # Criterion 9: every invalid construction is a ValueError — out of
    # bounds on both sides (never clamped), NaN/inf, non-numeric,
    # empty label, empty transforms, duplicate (team, op) with
    # different multipliers (ambiguity refused), unknown team — while
    # the inclusive exact bounds and a valid multi-transform tuple
    # build. Signature pinned: (fitted, transforms, *, label).
    signature_parameters = list(inspect.signature(build_scenario).parameters.values())
    assert [p.name for p in signature_parameters] == [
        "fitted",
        "transforms",
        "label",
    ]
    assert signature_parameters[2].kind is inspect.Parameter.KEYWORD_ONLY
    assert signature_parameters[2].default is inspect.Parameter.empty  # required

    # Bounds: strictly below / above the inclusive constants refused.
    with pytest.raises(ValueError):
        _build([Transform(HOME, TransformOp.ATTACK, MULTIPLIER_MIN - 0.01)])
    with pytest.raises(ValueError):
        _build([Transform(HOME, TransformOp.ATTACK, MULTIPLIER_MAX + 0.01)])
    with pytest.raises(ValueError):
        _build([Transform(HOME, TransformOp.ATTACK, 0.49)])
    with pytest.raises(ValueError):
        _build([Transform(HOME, TransformOp.ATTACK, 2.01)])

    # Exact bounds accepted — documented inclusive at both ends.
    assert _build(
        [Transform(HOME, TransformOp.ATTACK, MULTIPLIER_MIN)]
    ).transforms[0].multiplier == 0.5
    assert _build(
        [Transform(HOME, TransformOp.ATTACK, MULTIPLIER_MAX)]
    ).transforms[0].multiplier == 2.0
    assert (MULTIPLIER_MIN, MULTIPLIER_MAX) == (0.5, 2.0)

    # NaN / inf / -inf refused (finite check precedes bounds).
    for bad in (float("nan"), float("inf"), float("-inf")):
        with pytest.raises(ValueError):
            _build([Transform(HOME, TransformOp.ATTACK, bad)])

    # Non-numeric multipliers refused.
    for bad in ("1.5", None, "high"):
        with pytest.raises(ValueError):
            _build([Transform(HOME, TransformOp.ATTACK, bad)])  # type: ignore[arg-type]

    # Empty label and empty transforms refused.
    with pytest.raises(ValueError):
        build_scenario(FITTED, (Transform(HOME, TransformOp.ATTACK, 1.2),), label="")
    with pytest.raises(ValueError):
        build_scenario(FITTED, (), label="no transforms")

    # Duplicate (team, op) pair with different multipliers: refused,
    # never resolved silently or averaged.
    with pytest.raises(ValueError):
        _build(
            [
                Transform(HOME, TransformOp.ATTACK, 0.6),
                Transform(HOME, TransformOp.ATTACK, 1.4),
            ]
        )

    # Team not in the fit refused.
    with pytest.raises(ValueError):
        _build([Transform("Nonexistent FC", TransformOp.ATTACK, 1.2)])

    # A valid multi-transform tuple builds.
    scenario = _build(
        [
            Transform(HOME, TransformOp.ATTACK, 1.5),
            Transform(AWAY, TransformOp.DEFENCE, 0.75),
            Transform(HOME, TransformOp.HOME_ADVANTAGE, 1.2),
        ],
        label="three transforms",
    )
    assert isinstance(scenario, Scenario)
    assert len(scenario.transforms) == 3
    assert scenario.label == "three transforms"


def test_scenario_applicability_value_errors() -> None:
    # Criterion 10: a transform that cannot fire must raise at
    # scenario_matrix — team not in the fixture, home_advantage on
    # anyone but the fixture's home side (away side included), unknown
    # home/away names — while a fully applicable set builds a
    # well-formed ScenarioMatrix. Signature pinned: (scenario, home, away).
    signature_parameters = list(inspect.signature(scenario_matrix).parameters.values())
    assert [p.name for p in signature_parameters] == ["scenario", "home", "away"]
    assert all(
        p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for p in signature_parameters
    )

    # Team in the fit but NOT playing in this fixture.
    not_playing = _build([Transform(NOT_PLAYING, TransformOp.ATTACK, 1.2)])
    with pytest.raises(ValueError):
        scenario_matrix(not_playing, HOME, AWAY)

    # home_advantage naming the AWAY side -> ValueError (decision 11).
    away_advantage = _build(
        [Transform(AWAY, TransformOp.HOME_ADVANTAGE, 1.5)]
    )
    with pytest.raises(ValueError):
        scenario_matrix(away_advantage, HOME, AWAY)

    # home_advantage naming a non-playing team -> ValueError too.
    spectator_advantage = _build(
        [Transform(NOT_PLAYING, TransformOp.HOME_ADVANTAGE, 1.5)]
    )
    with pytest.raises(ValueError):
        scenario_matrix(spectator_advantage, HOME, AWAY)

    # Unknown home / away for the fixture.
    applicable = _build([Transform(HOME, TransformOp.ATTACK, 1.5)])
    with pytest.raises(ValueError):
        scenario_matrix(applicable, "Nonexistent FC", AWAY)
    with pytest.raises(ValueError):
        scenario_matrix(applicable, HOME, "Nonexistent FC")

    # A fully applicable transform set builds a well-formed output.
    full = _build(
        [
            Transform(HOME, TransformOp.ATTACK, 1.5),
            Transform(AWAY, TransformOp.DEFENCE, 0.75),
            Transform(HOME, TransformOp.HOME_ADVANTAGE, 1.2),
        ],
        label="fully applicable",
    )
    result = scenario_matrix(full, HOME, AWAY)
    assert isinstance(result, ScenarioMatrix)
    assert isinstance(result.matrix, ScorelineMatrix)
    assert result.scenario is full
    assert len(result.matrix.log_probs) == FITTED.config.max_goals + 1
    assert all(
        len(row) == FITTED.config.max_goals + 1 for row in result.matrix.log_probs
    )


def test_scenario_shared_cell_math_no_forged_params() -> None:
    # Criterion 11: (a) hand-derived lambdas at full precision;
    # (b) the baseline is untouched and NO FittedParams( / fit( call
    # exists anywhere in app/scenarios (AST — no forged parameters);
    # (c) no cell math is copied (no lgamma/exp/log) and the shared
    # constructors are imported from app.models; (d) the refactored
    # baseline path is field-for-field identical to the shared
    # constructor invoked with the baseline lambdas.
    scenario = _build([Transform(HOME, TransformOp.ATTACK, 1.5)])
    matrix = scenario_matrix(scenario, HOME, AWAY).matrix

    # Derivation: transform first (alpha' = 1.5 * alpha), then the
    # documented formula (STATISTICAL-ASSUMPTIONS section 1):
    #   lambda_home = exp(mu + alpha_home + beta_away + h)
    #   lambda_away = exp(mu + alpha_away + beta_home)
    expected_home = math.exp(
        FITTED.mu
        + 1.5 * FITTED.alpha[HOME_INDEX]
        + FITTED.beta[AWAY_INDEX]
        + FITTED.home_advantage
    )
    expected_away = math.exp(
        FITTED.mu + FITTED.alpha[AWAY_INDEX] + FITTED.beta[HOME_INDEX]
    )
    assert matrix.lambda_home == expected_home
    assert matrix.lambda_away == expected_away

    # Defence + home_advantage derivation (two transforms, both sides):
    #   beta_away' = 0.75 * beta_away,  h' = 1.5 * h
    mixed = _build(
        [
            Transform(AWAY, TransformOp.DEFENCE, 0.75),
            Transform(HOME, TransformOp.HOME_ADVANTAGE, 1.5),
        ]
    )
    mixed_matrix = scenario_matrix(mixed, HOME, AWAY).matrix
    mixed_home = math.exp(
        FITTED.mu
        + FITTED.alpha[HOME_INDEX]
        + 0.75 * FITTED.beta[AWAY_INDEX]
        + 1.5 * FITTED.home_advantage
    )
    mixed_away = math.exp(
        FITTED.mu + FITTED.alpha[AWAY_INDEX] + FITTED.beta[HOME_INDEX]
    )
    assert mixed_matrix.lambda_home == mixed_home
    assert mixed_matrix.lambda_away == mixed_away

    # (b) the baseline FittedParams is untouched: fields identical
    # before/after evaluation, and the object is frozen.
    fields_before = tuple(
        (field.name, getattr(FITTED, field.name))
        for field in dataclasses.fields(FITTED)
    )
    scenario_matrix(scenario, HOME, AWAY)
    scenario_matrix(mixed, HOME, AWAY)
    fields_after = tuple(
        (field.name, getattr(FITTED, field.name))
        for field in dataclasses.fields(FITTED)
    )
    assert fields_after == fields_before
    with pytest.raises(AttributeError):
        FITTED.mu = 0.0  # type: ignore[misc]

    # AST: no FittedParams( or fit( call in app/scenarios/*.py.
    trees = [
        (path, ast.parse(path.read_text(), filename=str(path)))
        for path in sorted(SCENARIOS_DIR.rglob("*.py"))
    ]
    assert trees, "no Python files found under app/scenarios/"
    for path, tree in trees:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name):
                assert node.func.id not in ("FittedParams", "fit"), path
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in ("FittedParams", "fit"), path

    # (c) no cell math copied: lgamma and the Poisson/exp/log formula
    # names are absent from every app/scenarios source (AST, so
    # docstrings/comments mentioning them do not count), and both
    # shared constructors are imported from app.models.
    imported_from_models: set[str] = set()
    for path, tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id not in ("lgamma", "exp", "log"), (path, node.id)
            elif isinstance(node, ast.Attribute):
                assert node.attr not in ("lgamma", "exp", "log"), (path, node.attr)
            if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                if node.module == "app.models" or node.module.startswith("app.models."):
                    for alias in node.names:
                        imported_from_models.add(alias.name)
    assert {"lambda_pair", "build_scoreline_matrix"} <= imported_from_models

    # (d) the refactored baseline path delegates: scoreline_log_probs
    # is field-for-field identical to the shared constructors invoked
    # with the baseline lambda pair (Phase 3 goldens stay green and
    # unmodified — proven by the whole suite, not changed here).
    lambda_home, lambda_away = lambda_pair(
        FITTED.mu,
        FITTED.alpha[HOME_INDEX],
        FITTED.beta[AWAY_INDEX],
        FITTED.alpha[AWAY_INDEX],
        FITTED.beta[HOME_INDEX],
        FITTED.home_advantage,
    )
    delegated = build_scoreline_matrix(
        lambda_home,
        lambda_away,
        FITTED.config.max_goals,
        FITTED.convergence_status,
        FITTED.insufficient_data,
        FITTED.insufficient_teams,
    )
    assert scoreline_log_probs(FITTED, HOME, AWAY) == delegated


def test_scenario_outputs_echo_flags_spec_label_and_provenance() -> None:
    # Criterion 12: the matrix echoes the BASELINE's flags; the spec
    # rides in canonical order; the label is echoed on every output
    # (Scenario, ScenarioMatrix, and via simulate on
    # SimulationResult.scenario); provenance is field-identical; and
    # SimulationResult.baseline == result.scenario.baseline.
    label = "hypothetical stronger home attack"
    transforms = (Transform(HOME, TransformOp.ATTACK, 1.5),)
    scenario = _build(transforms, label=label)
    result = scenario_matrix(scenario, HOME, AWAY)

    assert result.matrix.convergence_status is FITTED.convergence_status
    assert result.matrix.insufficient_data == FITTED.insufficient_data
    assert result.matrix.insufficient_teams == FITTED.insufficient_teams

    assert scenario.transforms == transforms  # input already canonical
    assert scenario.label == label
    assert result.label == label
    assert result.scenario.label == label

    assert scenario.baseline == FITTED
    assert scenario.baseline.model_version == FITTED.model_version == MODEL_VERSION
    assert scenario.baseline.input_digest == FITTED.input_digest
    assert scenario.baseline.config == FITTED.config
    assert scenario.baseline.pooling == FITTED.pooling

    simulation = simulate(
        FITTED, HOME, AWAY, seed=9, n_sims=500, scenario=scenario
    )
    assert simulation.scenario is scenario
    assert simulation.scenario.label == label
    assert simulation.baseline == simulation.scenario.baseline
    assert simulation.baseline == FITTED
    assert simulation.convergence_status is FITTED.convergence_status
    assert (
        simulation.counts_home + simulation.counts_draw + simulation.counts_away
        == 500
    )


def test_scenario_canonical_ordering_shuffled_inputs_identical() -> None:
    # Criterion 13: the same transform set in two different caller
    # orders yields field-for-field identical Scenarios (canonical key
    # (team, op, multiplier)) and identical scenario matrices —
    # deterministic regardless of caller iteration order (A7).
    transforms_a = (
        Transform(HOME, TransformOp.ATTACK, 1.5),
        Transform(AWAY, TransformOp.DEFENCE, 0.75),
        Transform(HOME, TransformOp.HOME_ADVANTAGE, 1.2),
    )
    transforms_b = tuple(reversed(transforms_a))  # shuffled caller order

    scenario_a = build_scenario(FITTED, transforms_a, label="same label")
    scenario_b = build_scenario(FITTED, transforms_b, label="same label")
    assert scenario_a == scenario_b
    assert repr(scenario_a) == repr(scenario_b)

    # The canonical order itself: (team, op.value, multiplier) ascending.
    assert scenario_a.transforms == (
        Transform(HOME, TransformOp.ATTACK, 1.5),
        Transform(HOME, TransformOp.HOME_ADVANTAGE, 1.2),
        Transform(AWAY, TransformOp.DEFENCE, 0.75),
    )

    matrix_a = scenario_matrix(scenario_a, HOME, AWAY)
    matrix_b = scenario_matrix(scenario_b, HOME, AWAY)
    assert matrix_a == matrix_b
    assert repr(matrix_a) == repr(matrix_b)


def test_no_scenario_averaging_or_ensembling() -> None:
    # Criterion 14: the public surface is exactly the decision-10
    # name set; no public callable takes more than one scenario/matrix
    # argument or a sequence of scenarios; no output dataclass holds a
    # collection of scenarios or matrices; two scenarios evaluated
    # side by side stay two independent results echoing only their own
    # spec — disagreement surfaces, never collapsed (A6; Phase 7 owns
    # comparison).
    import app.scenarios as scenarios_package

    expected_surface = {
        "TransformOp",
        "Transform",
        "Scenario",
        "ScenarioMatrix",
        "build_scenario",
        "scenario_matrix",
        "MULTIPLIER_MIN",
        "MULTIPLIER_MAX",
    }
    assert set(scenarios_package.__all__) == expected_surface
    assert len(scenarios_package.__all__) == len(expected_surface)  # no dupes

    # Signature inspection: at most one scenario-ish parameter per
    # public callable, and no parameter annotated as a collection of
    # scenarios or matrices.
    collection_pattern = re.compile(
        r"(Sequence|list|tuple|Iterable|Collection)\s*[\[\(][^\]]*\bScenario\b"
        r"|[Ss]equence\s*of\s*scenario"
    )
    for name in ("build_scenario", "scenario_matrix"):
        signature = inspect.signature(getattr(scenarios_package, name))
        scenario_params = 0
        for parameter in signature.parameters.values():
            text = str(parameter.annotation)
            assert not collection_pattern.search(text), (name, text)
            if re.search(r"\bScenario\b", text) or re.search(
                r"\bScorelineMatrix\b", text
            ):
                scenario_params += 1
        assert scenario_params <= 1, name

    # Field-type walk: no output dataclass holds a collection of
    # scenarios or matrices (no ensemble type exists).
    scenario = _build([Transform(HOME, TransformOp.ATTACK, 1.5)], label="A-side")
    matrix_output = scenario_matrix(scenario, HOME, AWAY)
    for root in (scenario, matrix_output):
        for field in dataclasses.fields(root):
            value = getattr(root, field.name)
            if isinstance(value, tuple):
                assert not any(
                    isinstance(item, (Scenario, ScorelineMatrix))
                    for item in value
                ), field.name
    for value in _walk_values(matrix_output):
        assert not isinstance(value, (list, set, dict))

    # Side by side: two independent results, each echoing only its
    # own spec; the disagreement (different analytic targets) surfaces.
    scenario_a = _build([Transform(HOME, TransformOp.ATTACK, 1.5)], label="A")
    scenario_b = _build([Transform(HOME, TransformOp.ATTACK, 0.5)], label="B")
    result_a = simulate(FITTED, HOME, AWAY, seed=13, n_sims=2_000, scenario=scenario_a)
    result_b = simulate(FITTED, HOME, AWAY, seed=13, n_sims=2_000, scenario=scenario_b)
    assert result_a.scenario == scenario_a
    assert result_b.scenario == scenario_b
    assert result_a.scenario != result_b.scenario
    assert result_a.scenario.label != result_b.scenario.label
    assert result_a.analytic_outcome != result_b.analytic_outcome
    # Each result holds exactly one scenario field — no collapse into
    # an average or ensemble of the two.
    assert result_a.scenario.label == "A"
    assert result_b.scenario.label == "B"


def test_scenario_output_hygiene_frozen_tuples_no_env_full_precision() -> None:
    # Criterion 15: frozen (setattr raises on every output type),
    # tuple-only values throughout (including matrix.log_probs as
    # tuple-of-tuples), full-precision floats against hand literals,
    # no timestamp/absolute-path/environment string anywhere, and
    # equal inputs give equal repr (A7).
    transforms = (Transform(HOME, TransformOp.ATTACK, 1.5),)
    scenario = _build(transforms, label="hygiene probe")
    output = scenario_matrix(scenario, HOME, AWAY)

    with pytest.raises(AttributeError):
        transforms[0].multiplier = 2.0  # type: ignore[index]
    with pytest.raises(AttributeError):
        scenario.label = "changed"  # type: ignore[misc]
    with pytest.raises(AttributeError):
        scenario.transforms = ()  # type: ignore[misc]
    with pytest.raises(AttributeError):
        output.matrix = None  # type: ignore[misc]
    with pytest.raises(AttributeError):
        output.scenario = scenario  # type: ignore[misc]

    # Deep walk: only scalars, tuples, enums, and frozen dataclasses —
    # no dict, set, or list anywhere (including matrix.log_probs).
    allowed_types = (str, int, float, bool, type(None), tuple, enum.Enum)
    for value in _walk_values(scenario):
        assert isinstance(value, allowed_types) or dataclasses.is_dataclass(value)
    for value in _walk_values(output):
        assert isinstance(value, allowed_types) or dataclasses.is_dataclass(value)
    assert isinstance(output.matrix.log_probs, tuple)
    assert all(isinstance(row, tuple) for row in output.matrix.log_probs)

    # Full precision against hand literals:
    # lambda_home = exp(mu + 1.5*alpha_home + beta_away + h)
    expected_home = math.exp(
        FITTED.mu
        + 1.5 * FITTED.alpha[HOME_INDEX]
        + FITTED.beta[AWAY_INDEX]
        + FITTED.home_advantage
    )
    expected_away = math.exp(
        FITTED.mu + FITTED.alpha[AWAY_INDEX] + FITTED.beta[HOME_INDEX]
    )
    assert output.matrix.lambda_home == expected_home
    assert output.matrix.lambda_away == expected_away

    log_rate_home = math.log(output.matrix.lambda_home)
    log_rate_away = math.log(output.matrix.lambda_away)
    assert output.matrix.log_probs[2][1] == (
        (2 * log_rate_home - output.matrix.lambda_home - math.lgamma(3.0))
        + (1 * log_rate_away - output.matrix.lambda_away - math.lgamma(2.0))
    )
    cdf_home = 0.0
    cdf_away = 0.0
    for k in range(output.matrix.max_goals + 1):
        cdf_home += math.exp(
            k * log_rate_home - output.matrix.lambda_home - math.lgamma(k + 1.0)
        )
        cdf_away += math.exp(
            k * log_rate_away - output.matrix.lambda_away - math.lgamma(k + 1.0)
        )
    assert output.matrix.dropped_mass == 1.0 - cdf_home * cdf_away

    # No timestamp / absolute-path / environment string in any field
    # or in the repr.
    for text in list(_string_values(scenario)) + list(_string_values(output)):
        assert str(REPO_ROOT) not in text
        assert not re.search(r"\d{2}:\d{2}", text)  # no clock time
        assert not re.search(r"\d{4}-\d\d-\d\dT", text)  # no ISO timestamp
    assert str(REPO_ROOT) not in repr(scenario)
    assert str(REPO_ROOT) not in repr(output)

    # Equal inputs -> equal repr.
    scenario_again = _build(transforms, label="hygiene probe")
    output_again = scenario_matrix(scenario_again, HOME, AWAY)
    assert repr(scenario) == repr(scenario_again)
    assert repr(output) == repr(output_again)
    assert outcome_probs(output.matrix) == outcome_probs(output_again.matrix)
