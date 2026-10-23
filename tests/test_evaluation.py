"""Phase 11 acceptance criteria 1-16 and 18-22: forecast evaluation (IX-11).

Module-scoped re-derivation of the run (Phase 9 pattern): the golden
digest is asserted BEFORE the first evaluation call, every golden literal
is derived in-test from the checked-in fixtures ("golden: first green
run; re-derive, never widen"), poison probes are positive-control, and
the amendment surface is pinned exactly (ADV-7/ADV-9).  Criterion 17
lives in tests/test_storage.py (A9); criterion 19 is the suite-level
execution gate recorded by the tester.  No skip, no xfail.
"""

import ast
import dataclasses
import hashlib
import inspect
import json
import math
import re
import sqlite3
from pathlib import Path

import pytest

import test_fixtures_and_hygiene as hygiene
import test_phase7_separation as phase7
import test_temporal_integrity as temporal
import test_vocab_guards as vocab
from test_backtesting import ALL_MATCHES

import app.evaluation.evaluate as evaluate_module
from app.backtesting import BaselineStatus, WalkForwardRun, run_walk_forward
from app.domain import Match, Score
from app.evaluation import (
    EVALUATION_VERSION, CalibrationBin, EvaluationAccounting, EvaluationConflictError,
    EvaluationRecord, EvaluationResult, MetricTriple, OverdispersionDiagnostic,
    evaluate_predictions,
)
from app.evaluation.calibration import BIN_EDGES, bin_index, calibration_table
from app.evaluation.evaluate import build_evaluation_record
from app.evaluation.metrics import brier, log_loss, rps
from app.forecasts import Forecast
from app.storage import forecasts_db

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_SOURCES = tuple(sorted((REPO_ROOT / "app" / "evaluation").glob("*.py")))
FIXTURE_FILES = ("season-1.json", "season-2.json")

# Criterion 1: the walk-forward digest with default echoes — asserted
# before any evaluation call (golden: first green run; re-derive).
GOLDEN_RUN_DIGEST = "150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f"

H, D, A = "H", "D", "A"

# Criterion 9 golden pins. golden: first green run; re-derive, never widen.
GOLDEN_METRICS = {
    "primary.model": (30, 1.0893088945036264, 0.657717020755589, 0.23748019128548054),
    "primary.baseline": (30, 1.0756660244986818, 0.6513262608006456, 0.2350484286002546),
    "secondary.model": (57, 1.172910978563622, 0.7110877726071556, 0.2599049808350038),
    "secondary.baseline": (57, 1.10026212693129, 0.6659747894436246, 0.2385794979516648),
}
# Criterion 10 golden bins: (n, mean_p, realized_frequency) per population.
GOLDEN_BINS = {
    "primary": (
        (2, 0.1922355541990161, 0.5),
        (73, 0.3068857322030056, 0.3013698630136986),
        (15, 0.48085802938550376, 0.4666666666666667),
        (0, None, None),
        (0, None, None),
    ),
    "secondary": (
        (6, 0.16572509513274955, 0.6666666666666666),
        (137, 0.30851337436509413, 0.32116788321167883),
        (27, 0.4853685454016753, 0.3333333333333333),
        (1, 0.6343664153403693, 0.0),
        (0, None, None),
    ),
}
GOLDEN_DOMINANT_SHARE = {"primary": 0.8111111111111111, "secondary": 0.8011695906432749}
# Criterion 11 goldens: realized draw rate minus mean predicted draw p.
GOLDEN_DRAW_DEFICIT = {"primary": -0.03437540133650058, "secondary": -0.025271786352718206}

_MATCHES_BY_KEY = {match.natural_key: match for match in ALL_MATCHES}


def _prediction_key(prediction: Forecast) -> tuple[str, str, str, str, str]:
    """The prediction's natural key: field order identical to Match's."""
    return (
        prediction.competition,
        prediction.season,
        prediction.date,
        prediction.home,
        prediction.away,
    )


def _outcome_of(match: Match) -> str:
    """Independent in-test H/D/A by goal comparison (never production's)."""
    if match.score.home > match.score.away:
        return H
    if match.score.home < match.score.away:
        return A
    return D


def _fixture_hashes() -> tuple[tuple[str, str], ...]:
    """Real sha256 of each fixture file's bytes, in the pinned name order."""
    return tuple(
        (name, hashlib.sha256((REPO_ROOT / "fixtures" / "openfootball" / "valid" / name).read_bytes()).hexdigest())
        for name in FIXTURE_FILES
    )


def _insert_predictions(connection: sqlite3.Connection, predictions: tuple[Forecast, ...]) -> None:
    """Insert every prediction write-once (Phase 9 caller-side pattern)."""
    assert [forecasts_db.insert_forecast(connection, prediction) for prediction in predictions] == [True] * len(predictions)


def _forecasts_dump(connection: sqlite3.Connection) -> list[tuple]:
    """Ordered full-table dump of the forecasts rows (untouched proof)."""
    return connection.execute(
        "SELECT * FROM forecasts ORDER BY competition, season, date, home, away"
    ).fetchall()


def _verify(db: Path) -> tuple[Forecast, ...]:
    """Hash-verified read-back tuple; the read connection always closes."""
    reader = forecasts_db.open_read_connection(str(db))
    try:
        return tuple(forecasts_db.verify_all(reader))
    finally:
        reader.close()


def _evaluate(
    run: WalkForwardRun,
    matches: tuple[Match, ...] = ALL_MATCHES,
    run_digest: str = GOLDEN_RUN_DIGEST,
) -> EvaluationResult:
    """The evaluation call shape (criterion 1 pins the explicit form)."""
    return evaluate_predictions(
        run.predictions, run.baselines, matches,
        run_digest=run_digest, expected_run_digest=GOLDEN_RUN_DIGEST,
    )


def _record(result: EvaluationResult) -> EvaluationRecord:
    """The one record-build shape: golden digest, real fixture hashes."""
    return build_evaluation_record(
        result, run_digest=GOLDEN_RUN_DIGEST, fixture_file_sha256s=_fixture_hashes()
    )


@pytest.fixture(scope="module")
def golden_run() -> WalkForwardRun:
    """The canonical run re-derived once (default echoes), digest FIRST."""
    run = run_walk_forward(ALL_MATCHES)
    # ADV-6: asserted before this fixture returns, i.e. before any
    # evaluation call — golden_result depends on this fixture.
    assert run.manifest.run_digest == GOLDEN_RUN_DIGEST
    return run


@pytest.fixture(scope="module")
def golden_result(golden_run: WalkForwardRun) -> EvaluationResult:
    return evaluate_predictions(
        golden_run.predictions,
        golden_run.baselines,
        ALL_MATCHES,
        run_digest=GOLDEN_RUN_DIGEST,
        expected_run_digest=GOLDEN_RUN_DIGEST,
    )


def test_rederived_run_matches_golden_digest_and_first_evaluation_n_positive(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    assert golden_run.manifest.run_digest == GOLDEN_RUN_DIGEST
    # The first evaluated n > 0 in the project's history: asserted here.
    assert golden_result.secondary.n_matches == 57 > 0
    assert golden_result.primary.n_matches == 30


def test_tampered_run_digest_refuses_before_any_metric_computes(
    golden_run: WalkForwardRun, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = {"n": 0}
    real_log_loss = evaluate_module.log_loss

    def counting_log_loss(*args: object, **kwargs: object) -> float:
        calls["n"] += 1
        return real_log_loss(*args, **kwargs)

    monkeypatch.setattr(evaluate_module, "log_loss", counting_log_loss)
    # Positive control: the seam is live — a golden call records calls.
    _evaluate(golden_run)
    assert calls["n"] > 0
    calls["n"] = 0
    flipped = "0" if GOLDEN_RUN_DIGEST[-1] != "0" else "1"
    with pytest.raises(ValueError, match="run_digest"):
        _evaluate(golden_run, run_digest=GOLDEN_RUN_DIGEST[:-1] + flipped)
    # The gate fired first: zero metric calls — no result, no record.
    assert calls["n"] == 0


def test_population_accounting_pinned_prescore_60_3_27_30(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    # ADV-1 BLOCKER: all six numbers were counted pre-score; no metric
    # container exists for n=60 (the accounting carries counts only).
    accounting = golden_result.accounting
    assert (accounting.n_targets, accounting.n_predictions, accounting.n_refusals) == (60, 57, 3)
    assert (accounting.n_flagged, accounting.n_clean) == (27, 30)
    first_date = min(match.date for match in ALL_MATCHES)
    expected_refusals = tuple(sorted(
        (match.natural_key for match in ALL_MATCHES if match.date == first_date),
        key=lambda key: (key[2], key[0], key[1], key[3], key[4]),
    ))
    assert len(expected_refusals) == 3  # hand-derived from min(m.date)
    assert accounting.refusal_keys == expected_refusals
    primary, secondary = golden_result.primary, golden_result.secondary
    assert (primary.n_matches, secondary.n_matches) == (30, 57)
    for population in (primary, secondary):
        assert population.model.n == population.baseline.n == population.n_matches
        assert population.calibration.n_matches == population.n_matches
        assert population.calibration.n_pairs == 3 * population.n_matches
    assert {population.model.n for population in (primary, secondary)} == {30, 57}
    accounting_fields = {field.name for field in dataclasses.fields(EvaluationAccounting)}
    assert not accounting_fields & {"log_loss", "brier", "rps"}  # counts, never metrics


def test_missing_baseline_symmetry_with_refusal_targets(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    # ADV-1: status-driven, never filled — MISSING_NO_HISTORY targets
    # carry None triples (no fabricated uniform) and are exactly the
    # prediction-less matches, exactly the refusal keys.
    missing = {b.fixture_key for b in golden_run.baselines
               if b.status is BaselineStatus.MISSING_NO_HISTORY}
    prediction_keys = {_prediction_key(p) for p in golden_run.predictions}
    match_keys = {match.natural_key for match in ALL_MATCHES}
    refusal_keys = set(golden_result.accounting.refusal_keys)
    assert missing == refusal_keys == match_keys - prediction_keys
    assert len(refusal_keys) == 3
    for population in (golden_result.primary, golden_result.secondary):
        assert population.baseline.n == population.model.n == population.n_matches
    baselines_by_key = {baseline.fixture_key: baseline for baseline in golden_run.baselines}
    scored_keys = {c.natural_key for c in golden_result.secondary.contributions}
    assert scored_keys == prediction_keys and scored_keys.isdisjoint(missing)
    for key in scored_keys:
        baseline = baselines_by_key[key]
        assert baseline.status is BaselineStatus.COMPUTED  # never a None on a scored target
        assert None not in (baseline.home_frequency, baseline.draw_frequency, baseline.away_frequency)
    for baseline in golden_run.baselines:
        if baseline.fixture_key in missing:
            assert (baseline.home_frequency, baseline.draw_frequency, baseline.away_frequency) == (None, None, None)


def test_hand_computed_single_prediction_values() -> None:
    # ADV-10: every expectation is expanded in-test — no production
    # helper derives it. Golden: first green run; re-derive, never widen.
    expected_log_loss = -math.log(0.55)  # -ln(0.55)
    expected_brier = 0.04 + 0.09 + 0.25  # (0.2-0)^2 + (0.3-0)^2 + (0.5-1)^2
    expected_rps = 0.5 * (0.4 ** 2 + (0.75 - 1.0) ** 2)  # F_p=(0.4,0.75), F_o=(0,1)
    assert abs(log_loss((0.55, 0.25, 0.20), H) - expected_log_loss) <= 1e-12
    assert abs(brier((0.2, 0.3, 0.5), A) - expected_brier) <= 1e-12
    assert abs(rps((0.4, 0.35, 0.25), D) - expected_rps) <= 1e-12
    assert abs(rps((0.4, 0.35, 0.25), D) - 0.11125) <= 1e-12  # the 0.11125 literal


def test_zero_probability_on_realized_outcome_hard_refusal_no_clamp(
    golden_run: WalkForwardRun,
) -> None:
    with pytest.raises(ValueError, match="zero probability"):
        log_loss((0.0, 0.5, 0.5), H)
    for path in EVAL_SOURCES:
        text = path.read_text(encoding="utf-8")
        for banned in ("epsilon", "clamp", "clip", "sys.float_info", "1e-"):
            assert banned not in text, (path.name, banned)
    # Golden: first green run; re-derive, never widen — the smallest
    # component over every scored pair: clamp question moot (always >0.1).
    smallest = min(min(p.outcome_home, p.outcome_draw, p.outcome_away) for p in golden_run.predictions)
    assert smallest == 0.12816022966803042
    assert smallest > 0.1


def test_brier_full_three_outcome_sum_no_halving_uniform_reference(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    probe = brier((0.2, 0.3, 0.5), A)
    assert probe == 0.38 == 0.04 + 0.09 + 0.25  # criterion 5's hand value
    assert abs(probe - 0.38 / 2) > 1e-15  # no /2 halving
    assert abs(probe - 0.38 / 3) > 1e-15  # no /3 either
    for outcome in (H, D, A):  # uniform reference, all three outcomes
        assert abs(brier((1 / 3, 1 / 3, 1 / 3), outcome) - 2 / 3) <= 1e-15
    baselines_by_key = {baseline.fixture_key: baseline for baseline in golden_run.baselines}
    for population in (golden_result.primary, golden_result.secondary):
        for contribution in population.contributions:
            assert 0.0 <= contribution.brier <= 2.0
            baseline = baselines_by_key[contribution.natural_key]
            triple = (baseline.home_frequency, baseline.draw_frequency, baseline.away_frequency)
            outcome = _outcome_of(_MATCHES_BY_KEY[contribution.natural_key])
            assert 0.0 <= brier(triple, outcome) <= 2.0  # baseline side too


def test_rps_half_scaled_ordinal_form_not_scoreline_variant(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    value = rps((0.4, 0.35, 0.25), D)
    assert abs(value - 0.11125) <= 1e-12  # hand-expanded cumulative form
    assert abs(value - 0.2225) > 1e-15  # != the unscaled sum: pins the 1/2
    assert abs(rps((1 / 3, 1 / 3, 1 / 3), H) - 5 / 18) <= 1e-15
    baselines_by_key = {baseline.fixture_key: baseline for baseline in golden_run.baselines}
    for population in (golden_result.primary, golden_result.secondary):
        for contribution in population.contributions:
            assert 0.0 <= contribution.rps <= 1.0
            baseline = baselines_by_key[contribution.natural_key]
            triple = (baseline.home_frequency, baseline.draw_frequency, baseline.away_frequency)
            assert 0.0 <= rps(triple, contribution.outcome) <= 1.0
    # AST pin: no scoreline-matrix machinery can exist here (S13(a)).
    for path in EVAL_SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                target = hygiene.resolve_from(["app", "evaluation"], node.level, node.module)
                assert target not in {"app.models", "app.simulation"}, (path.name, target)
            elif isinstance(node, ast.Import):
                assert not any(alias.name in {"app.models", "app.simulation"} for alias in node.names), path.name


def test_golden_mean_metrics_model_and_baseline_both_populations(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    # Exact-equality pins. golden: first green run; re-derive, never widen.
    baselines_by_key = {baseline.fixture_key: baseline for baseline in golden_run.baselines}
    for name in ("primary", "secondary"):
        population = getattr(golden_result, name)
        for side in ("model", "baseline"):
            triple = getattr(population, side)
            expected = GOLDEN_METRICS[f"{name}.{side}"]
            assert (triple.n, triple.log_loss, triple.brier, triple.rps) == expected
    metric_functions = {"log_loss": log_loss, "brier": brier, "rps": rps}
    for name in ("primary", "secondary"):
        population = getattr(golden_result, name)
        outcomes = [_outcome_of(_MATCHES_BY_KEY[c.natural_key]) for c in population.contributions]
        triples = [
            tuple(getattr(baselines_by_key[c.natural_key], f)
                  for f in ("home_frequency", "draw_frequency", "away_frequency"))
            for c in population.contributions
        ]
        for field_name, function in metric_functions.items():
            model_values = [getattr(c, field_name) for c in population.contributions]
            assert sum(model_values) / len(model_values) == getattr(population.model, field_name)
            baseline_values = [function(t, o) for t, o in zip(triples, outcomes)]
            assert sum(baseline_values) / len(baseline_values) == getattr(population.baseline, field_name)


def test_calibration_five_equal_width_bins_boundaries_and_empty_bin_honesty(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    assert BIN_EDGES == (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
    boundary_probes = ((0.0, 0), (0.2, 1), (0.4, 2), (0.6, 3), (0.8, 4), (1.0, 4), (0.3999, 1), (0.7999, 3))
    for probability, expected in boundary_probes:
        assert bin_index(probability) == expected, probability
    predictions_by_key = {_prediction_key(p): p for p in golden_run.predictions}
    edges = BIN_EDGES
    for name in ("primary", "secondary"):
        population = getattr(golden_result, name)
        table = population.calibration
        assert len(table.bins) == 5  # always five — never merged
        assert table.n_pairs == 3 * table.n_matches == (90 if name == "primary" else 171)
        assert sum(b.n for b in table.bins) == table.n_pairs
        # Independent in-test arithmetic over the pooled pairs (same
        # addition order => exact floats). golden: first green run.
        counts, p_sums, f_sums = [0] * 5, [0.0] * 5, [0.0] * 5
        for contribution in population.contributions:
            prediction = predictions_by_key[contribution.natural_key]
            outcome = _outcome_of(_MATCHES_BY_KEY[contribution.natural_key])
            probabilities = (prediction.outcome_home, prediction.outcome_draw, prediction.outcome_away)
            for position, probability in enumerate(probabilities):
                slot = next((i for i in range(4) if probability < edges[i + 1]), 4)
                counts[slot] += 1
                p_sums[slot] += probability
                f_sums[slot] += 1 if (H, D, A)[position] == outcome else 0
        recomputed = tuple(
            (counts[i], p_sums[i] / counts[i] if counts[i] else None,
             f_sums[i] / counts[i] if counts[i] else None)
            for i in range(5)
        )
        assert recomputed == GOLDEN_BINS[name]  # golden: first green run
        assert tuple((b.n, b.mean_p, b.realized_frequency) for b in table.bins) == recomputed
        dominant_share = max(b.n for b in table.bins) / table.n_pairs
        assert dominant_share == GOLDEN_DOMINANT_SHARE[name]  # the ~80% figure
    # Empty bins: n=0 with None averages, tuple never length 4.
    assert tuple(f.name for f in dataclasses.fields(CalibrationBin)) == ("n", "mean_p", "realized_frequency")
    partial = calibration_table([(0.1, 1)] * 3, n_matches=1)  # 3 pairs, one bin only
    assert len(partial.bins) == 5
    assert [(b.n, b.mean_p, b.realized_frequency) for b in partial.bins[1:]] == [(0, None, None)] * 4


def test_draw_aggregate_deficit_both_populations(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    predictions_by_key = {_prediction_key(p): p for p in golden_run.predictions}
    for name, independent_draws in (("primary", 7), ("secondary", 14)):
        population = getattr(golden_result, name)
        outcomes = [_outcome_of(_MATCHES_BY_KEY[c.natural_key]) for c in population.contributions]
        draws = sum(1 for outcome in outcomes if outcome == D)  # counted in-test
        assert draws == independent_draws
        realized_rate = draws / population.n_matches
        mean_p = sum(predictions_by_key[c.natural_key].outcome_draw
                     for c in population.contributions) / population.n_matches
        assert population.draw_deficit == realized_rate - mean_p
        # golden: first green run; re-derive, never widen.
        assert population.draw_deficit == GOLDEN_DRAW_DEFICIT[name]
        reconstructed = population.draw_deficit + mean_p
        assert abs(reconstructed - draws / population.n_matches) <= 1e-15


def test_overdispersion_diagnostic_n114_population_variance(
    golden_result: EvaluationResult,
) -> None:
    goals: list[int] = []
    for contribution in golden_result.secondary.contributions:
        score = _MATCHES_BY_KEY[contribution.natural_key].score  # hand-extracted
        goals += [score.home, score.away]
    assert len(goals) == 114 == 2 * golden_result.secondary.n_matches
    assert sum(goals) == 149
    average = sum(goals) / 114
    assert golden_result.overdispersion.n == 114
    assert golden_result.overdispersion.mean == average == 149 / 114
    assert round(average, 3) == 1.307
    variance = sum((goal - average) ** 2 for goal in goals) / 114  # ddof=0
    assert golden_result.overdispersion.variance == variance
    assert round(variance, 3) == 0.967
    ddof_one = sum((goal - average) ** 2 for goal in goals) / 113
    assert golden_result.overdispersion.variance != ddof_one  # denominator pinned
    assert round(ddof_one, 4) == 0.9757
    docstring = OverdispersionDiagnostic.__doc__ or ""
    assert "no test" in docstring and "no verdict" in docstring  # descriptive only


def test_baseline_side_by_side_absolute_no_delta_no_ci_surface(
    golden_result: EvaluationResult,
) -> None:
    for population in (golden_result.primary, golden_result.secondary):
        for side in ("model", "baseline"):
            triple = getattr(population, side)
            assert isinstance(triple, MetricTriple) and triple.n == population.n_matches
            assert all(isinstance(value, float) for value in (triple.log_loss, triple.brier, triple.rps))
    banned = ("delta", "diff", "difference", "ratio", "pct", "percent", "improvement",
              "uplift", "better", "worse", "advantage", "edge", "gap", "gain",
              "superior", "ci", "confidence", "lower", "upper")
    banned_pattern = re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, banned)) + r")(?![A-Za-z0-9])", re.IGNORECASE
    )
    verdict_pattern = re.compile(
        r"(?<![A-Za-z0-9])(verdict|interval|comparison|compare)(?![A-Za-z0-9])", re.IGNORECASE
    )
    methods: list[str] = []
    for path in EVAL_SOURCES:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(REPO_ROOT))
        for identifier in vocab.identifiers(text, rel):
            assert not banned_pattern.search(identifier), (rel, identifier)
        for class_name, field_name in vocab.dataclass_fields(text, rel):
            assert not banned_pattern.search(field_name), (class_name, field_name)
            assert not verdict_pattern.search(field_name), (class_name, field_name)
        tree = ast.parse(text, filename=rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods += [m.name for m in node.body
                            if isinstance(m, ast.FunctionDef) and not m.name.startswith("__")]
    assert methods == []  # no method surface exists to suggest anything


def test_join_refuses_zero_and_multiple_matches_get_forecast_never_load_bearing(
    golden_run: WalkForwardRun, golden_result: EvaluationResult, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_prediction = min(
        golden_run.predictions,
        key=lambda p: (p.date, p.competition, p.season, p.home, p.away),
    )
    first_key = _prediction_key(first_prediction)
    # (a) zero matches: explicit refusal carrying the offending key.
    with pytest.raises(ValueError) as zero_error:
        _evaluate(golden_run, matches=())
    assert "no match" in str(zero_error.value)
    assert repr(first_key) in str(zero_error.value)
    # (a2) two Matches sharing the key: refused (join before baseline).
    duplicate_match = next(m for m in ALL_MATCHES if m.natural_key == first_key)
    with pytest.raises(ValueError) as duplicate_error:
        _evaluate(golden_run, matches=ALL_MATCHES + (duplicate_match,))
    assert "more than one match" in str(duplicate_error.value)
    assert repr(first_key) in str(duplicate_error.value)
    # (b) get_forecast appears nowhere in the evaluation sources.
    for path in EVAL_SOURCES:
        assert "get_forecast" not in path.read_text(encoding="utf-8"), path.name
    # (c) read-path pins: signature, fetchone (ambiguity retained, never
    # silently fixed), the exact __all__ surface, no content-hash fetch.
    signature = inspect.signature(forecasts_db.get_forecast)
    assert tuple(signature.parameters) == ("connection", "competition", "season", "date", "home", "away")
    assert all(p.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD for p in signature.parameters.values())
    assert signature.return_annotation == "Forecast | None"
    assert "fetchone" in inspect.getsource(forecasts_db.get_forecast)
    pre_existing_names = (
        "COLUMN_NAMES", "IDENTITY_COLUMNS", "IMMUTABLE_DELETE_TRIGGER_DDL",
        "IMMUTABLE_UPDATE_TRIGGER_DDL", "SCHEMA_VERSION", "backup_forecasts",
        "get_forecast", "insert_forecast", "open_forecasts_db",
        "open_read_connection", "verify_all",
    )  # 11 pre-existing names (criterion 14(c) as amended 2026-10-23)
    assert set(forecasts_db.__all__) == set(pre_existing_names) | {"insert_evaluation_record"}
    assert len(forecasts_db.__all__) == 12
    assert not any("content_hash" in name for name in forecasts_db.__all__)
    # A raising replacement cannot affect any evaluation path.
    def explode(*args: object, **kwargs: object) -> object:
        raise AssertionError("get_forecast must never be load-bearing in evaluation")
    monkeypatch.setattr(forecasts_db, "get_forecast", explode)
    assert _evaluate(golden_run) == golden_result  # get_forecast never consulted


def test_db_roundtrip_metrics_equal_and_read_phase_byte_identical(
    golden_run: WalkForwardRun, golden_result: EvaluationResult, tmp_path: Path
) -> None:
    db = tmp_path / "roundtrip-evaluation.db"
    assert db.parent == tmp_path  # all writes stayed under tmp_path
    writer = forecasts_db.open_forecasts_db(str(db))
    _insert_predictions(writer, golden_run.predictions)
    bytes_before = hashlib.sha256(db.read_bytes()).hexdigest()
    verify_before = _verify(db)
    read_back = tuple(sorted(verify_before, key=lambda p: (p.date, p.competition, p.season, p.home, p.away)))
    evaluated = evaluate_predictions(
        read_back, golden_run.baselines, ALL_MATCHES,
        run_digest=GOLDEN_RUN_DIGEST, expected_run_digest=GOLDEN_RUN_DIGEST,
    )
    verify_after = _verify(db)
    bytes_after = hashlib.sha256(db.read_bytes()).hexdigest()
    assert evaluated == golden_result  # field-for-field, exact floats
    assert verify_before == verify_after and len(verify_after) == 57
    assert bytes_before == bytes_after  # the read/evaluate phase wrote nothing


def test_evaluation_record_idempotent_content_hashed_no_clock(
    golden_run: WalkForwardRun, golden_result: EvaluationResult, tmp_path: Path
) -> None:
    fixture_hashes = _fixture_hashes()
    assert [name for name, _digest in fixture_hashes] == list(FIXTURE_FILES)
    record = _record(golden_result)
    assert tuple(f.name for f in dataclasses.fields(EvaluationRecord)) == (
        "evaluation_version", "run_digest", "fixture_file_sha256s", "payload", "content_hash"
    )
    assert EVALUATION_VERSION == 1 and record.evaluation_version == EVALUATION_VERSION
    assert record.run_digest == GOLDEN_RUN_DIGEST
    assert record.fixture_file_sha256s == fixture_hashes
    assert record.content_hash == hashlib.sha256(record.payload.encode("utf-8")).hexdigest()
    assert json.dumps(json.loads(record.payload), sort_keys=True, separators=(",", ":")) == record.payload
    assert isinstance(json.loads(record.payload), dict)  # json.loads round-trips
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", record.payload) is None  # no clock form
    db = tmp_path / "evaluation-record.db"
    writer = forecasts_db.open_forecasts_db(str(db))
    trace: list[str] = []
    writer.set_trace_callback(trace.append)
    assert forecasts_db.insert_evaluation_record(writer, record) is True
    trace.clear()
    assert forecasts_db.insert_evaluation_record(writer, record) is False  # idempotent
    assert [sql for sql in trace if "INSERT INTO" in sql] == []  # zero INSERTs
    rows_before = writer.execute("SELECT * FROM evaluations").fetchall()
    assert len(rows_before) == 1
    assert rows_before[0][0] == EVALUATION_VERSION == 1  # version echoed into the row
    stored_identity = writer.execute(
        "SELECT run_digest, fixture_file_sha256s FROM evaluations"
    ).fetchone()
    assert stored_identity[0] == GOLDEN_RUN_DIGEST
    assert tuple(tuple(pair) for pair in json.loads(stored_identity[1])) == fixture_hashes
    # Same natural identity, one metric perturbed by math.nextafter.
    payload_object = json.loads(record.payload)
    payload_object["secondary"]["model"]["log_loss"] = math.nextafter(
        payload_object["secondary"]["model"]["log_loss"], math.inf
    )
    mutated = dataclasses.replace(
        record, payload=json.dumps(payload_object, sort_keys=True, separators=(",", ":"))
    )
    with pytest.raises(EvaluationConflictError):
        forecasts_db.insert_evaluation_record(writer, mutated)
    assert writer.execute("SELECT * FROM evaluations").fetchall() == rows_before  # untouched
    writer.close()
    # Compute-level idempotence: two consecutive evaluations are equal.
    assert _evaluate(golden_run) == golden_result
    # No time/datetime import or field exists in app/evaluation/**.
    for path in EVAL_SOURCES:
        text = path.read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(text, filename=str(path))):
            if isinstance(node, ast.Import):
                assert not any(a.name.split(".")[0] in {"time", "datetime"} for a in node.names), path.name
            elif isinstance(node, ast.ImportFrom):
                assert not (node.module and node.module.split(".")[0] in {"time", "datetime"}), path.name
        for _class_name, field_name in vocab.dataclass_fields(text, str(path.relative_to(REPO_ROOT))):
            assert re.search(r"time|stamp|clock", field_name, re.I) is None, field_name


def test_evaluation_writes_never_alter_forecasts_or_verify_all(
    golden_run: WalkForwardRun, golden_result: EvaluationResult, tmp_path: Path
) -> None:
    db = tmp_path / "evaluation-writes.db"
    writer = forecasts_db.open_forecasts_db(str(db))
    _insert_predictions(writer, golden_run.predictions)
    dump_before = _forecasts_dump(writer)
    verify_before = _verify(db)
    assert forecasts_db.insert_evaluation_record(writer, _record(golden_result)) is True
    dump_after = _forecasts_dump(writer)
    verify_after = _verify(db)
    assert dump_after == dump_before  # the forecasts rows never altered
    assert verify_before == verify_after and len(verify_after) == 57
    assert writer.execute("SELECT COUNT(*) FROM evaluations").fetchone() == (1,)
    writer.close()


def test_poisoned_scored_outcome_edit_changes_that_contribution_and_aggregates(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    # ADV-12a positive control: flip a SCORED clean target's outcome so
    # its realized component moves to a different probability (every
    # metric then differs by selection, not by luck).
    predictions_by_key = {_prediction_key(p): p for p in golden_run.predictions}
    chosen: tuple[tuple[str, str, str, str, str], str] | None = None
    for contribution in golden_result.primary.contributions:
        prediction = predictions_by_key[contribution.natural_key]
        triple = (prediction.outcome_home, prediction.outcome_draw, prediction.outcome_away)
        flipped = {"H": A, "A": H, "D": H}[contribution.outcome]
        if (
            log_loss(triple, contribution.outcome) != log_loss(triple, flipped)
            and brier(triple, contribution.outcome) != brier(triple, flipped)
            and rps(triple, contribution.outcome) != rps(triple, flipped)
        ):
            chosen = (contribution.natural_key, flipped)
            break
    assert chosen is not None  # a qualifying clean target exists
    key, flipped = chosen
    flipped_goals = {"H": (2, 0), "D": (1, 1), "A": (0, 2)}[flipped]
    poisoned = tuple(
        match if match.natural_key != key else dataclasses.replace(
            match, score=Score(home=flipped_goals[0], away=flipped_goals[1])
        )
        for match in ALL_MATCHES
    )
    prediction_hashes_before = tuple(p.content_hash for p in golden_run.predictions)
    result = _evaluate(golden_run, matches=poisoned)
    original = next(c for c in golden_result.secondary.contributions if c.natural_key == key)
    altered = next(c for c in result.secondary.contributions if c.natural_key == key)
    assert altered.outcome == flipped != original.outcome
    assert altered.log_loss != original.log_loss  # all three metrics differ
    assert altered.brier != original.brier
    assert altered.rps != original.rps
    assert result.secondary.model != golden_result.secondary.model  # aggregates move
    assert result.primary.model != golden_result.primary.model
    # forecasts remain untouched (no storage path exists in evaluation).
    assert tuple(p.content_hash for p in golden_run.predictions) == prediction_hashes_before


def test_poisoned_refusal_target_score_edit_changes_nothing(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    # ADV-12b: a first-date (refusal-target) match's score is edited;
    # it never joins, so the whole result and record stay identical.
    first_date = min(match.date for match in ALL_MATCHES)
    refusal_match = next(match for match in ALL_MATCHES if match.date == first_date)
    poisoned = tuple(
        match if match.natural_key != refusal_match.natural_key
        else dataclasses.replace(match, score=Score(home=9, away=0))
        for match in ALL_MATCHES
    )
    result = _evaluate(golden_run, matches=poisoned)
    assert result == golden_result  # accounting, populations, diagnostics
    assert _record(result).content_hash == _record(golden_result).content_hash


def test_poisoned_extra_matches_leave_evaluation_unchanged(
    golden_run: WalkForwardRun, golden_result: EvaluationResult
) -> None:
    # POISON_REGISTRY["evaluate_predictions"]: synthetic FUTURE matches
    # with distinct natural keys append to the input and simply never
    # join (the baseline set is what fixes the refusal keys).
    future_matches = tuple(
        dataclasses.replace(
            match,
            date=f"2099-12-{index + 1:02d}",
            home=f"Synthetic Future Home {index}",
            away=f"Synthetic Future Away {index}",
        )
        for index, match in enumerate(ALL_MATCHES[:2])
    )
    match_keys = {match.natural_key for match in ALL_MATCHES}
    prediction_keys = {_prediction_key(p) for p in golden_run.predictions}
    assert all(m.natural_key not in match_keys | prediction_keys for m in future_matches)
    poisoned = ALL_MATCHES + future_matches
    result = _evaluate(golden_run, matches=poisoned)
    assert result == golden_result  # byte-identical: extra rows never join
    assert _record(result).content_hash == _record(golden_result).content_hash


def test_amendment_surface_exact_and_guards_extended_not_weakened() -> None:
    # (a) temporal: registry exact seven + resolution + census + base.
    assert set(temporal.POISON_REGISTRY) == {
        "fit", "build_forecast", "compute_features", "build_decision_report",
        "storage.get_forecast/verify_all", "run_walk_forward", "evaluate_predictions",
    }
    assert temporal.POISON_REGISTRY["evaluate_predictions"] == (
        "test_evaluation", "test_poisoned_extra_matches_leave_evaluation_unchanged"
    )
    resolved = temporal.validate_registry(temporal.POISON_REGISTRY)
    assert set(resolved) == set(temporal.POISON_REGISTRY)
    assert all(test.__name__.startswith("test_") for test in resolved.values())
    assert temporal.MATCHES_ENTRY_POINTS == (
        "fit", "build_forecast", "compute_features", "run_walk_forward", "evaluate_predictions"
    )
    assert temporal.PHASE10_CHECKPOINT == "8abe1ca"
    # (b) hygiene: fourteen keys, the evaluation value, storage inclusion,
    # and the exact six-set with app.evaluation (C2, architect-ratified).
    assert len(hygiene.ALLOWED_APP_IMPORTS) == 14
    assert hygiene.ALLOWED_APP_IMPORTS["app.evaluation"] == {
        "app.domain", "app.forecasts", "app.backtesting", "app.evaluation"
    }
    assert "app.evaluation" in hygiene.ALLOWED_APP_IMPORTS["app.storage"]
    assert hygiene.PURE_PACKAGES == {
        "app.domain", "app.validation", "app.features", "app.decisions",
        "app.backtesting", "app.evaluation",
    }
    # (c) vocab/phase7: the ONE prefix exemption; every other set pinned.
    assert vocab.SCORING_EXEMPT_PREFIXES == ("app/evaluation/",)
    assert len(vocab.SCORING_ALLOWLIST) == 1
    assert phase7.SCORING_TOKENS == ("log_loss", "logloss", "brier", "rps", "hit_rate", "calibration")
    assert len(vocab.OUTCOME_COMPARATIVE_TOKENS) == 13
    assert vocab.ACCURACY_TRIO == {"validated", "accurate", "beating"}
    # extend-not-weaken: a scoring token passes ONLY under the prefix.
    scoring_probe = "def model_score(predictions):\n    return log_loss(outcome, predictions)\n"
    assert vocab.scoring_violations(scoring_probe, "app/evaluation/x.py") == []
    assert vocab.scoring_violations(scoring_probe, "app/models/x.py") != []
    # comparative token, accuracy-trio identifier, FIELD_BAN field — all
    # STILL flag when the text sits inside app/evaluation/.
    comparative_probe = "the model beats a naive baseline"
    for rel in ("app/evaluation/x.py", "app/models/x.py"):
        assert vocab._COMPARATIVE_PATTERN.search(comparative_probe) is not None, rel
    accuracy_probe = "def probe(validated=1):\n    return validated\n"
    assert vocab.identifiers(accuracy_probe, "app/evaluation/x.py") & vocab.ACCURACY_TRIO == {"validated"}
    field_probe = "from dataclasses import dataclass\n@dataclass\nclass P:\n    performance_score: float\n"
    assert vocab.dataclass_fields(field_probe, "app/evaluation/x.py") == [("P", "performance_score")]
    assert vocab._FIELD_BAN_PATTERN.search("performance_score") is not None
    # Signature pin (criterion 1's positional call form: three positionals).
    parameters = inspect.signature(evaluate_predictions).parameters
    assert tuple(parameters) == (
        "predictions", "baselines", "matches", "run_digest", "expected_run_digest"
    )
    assert parameters["matches"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["run_digest"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["expected_run_digest"].kind is inspect.Parameter.KEYWORD_ONLY
    # AST: import roots of app/evaluation/** within the pinned set.
    allowed_roots = {
        "app.domain", "app.forecasts", "app.backtesting",
        "dataclasses", "hashlib", "json", "math", "typing",
    }
    for path in EVAL_SOURCES:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name in allowed_roots, (path.name, alias.name)
            elif isinstance(node, ast.ImportFrom):
                target = (
                    hygiene.resolve_from(["app", "evaluation"], node.level, node.module)
                    if node.level else (node.module or "")
                )
                if target.startswith("app.evaluation"):
                    continue
                parts = target.split(".")
                root = ".".join(parts[:2]) if target.startswith("app") else parts[0]
                assert root in allowed_roots, (path.name, target)
    # Zero validated/accurate/beating/accuracy occurrences anywhere there.
    for path in EVAL_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert re.search(r"\b(validated|accurate|beating|accuracy)\b", text, re.I) is None, path.name
