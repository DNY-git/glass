"""Phase 12 acceptance criteria 1-10: integration and verification (IX-12).

One composed pass is the module-scoped substrate: checked-in fixture
files -> ingestion -> walk-forward -> evaluation -> record -> tmp store
(both tables) -> verified read-back.  Every assertion CONSUMES the
Phase 9/11 pinned values and recomputes nothing (ADV-12.2: an inequality
is RED, never a re-pin).  Tests-only, zero production surface, zero
amendments; no skip/xfail, no harness subsetting, no test-side timeout
(E2).  "Determinism"/"replay" are provenance statements, never
validation vocabulary.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import test_temporal_integrity as temporal

from app.backtesting import WalkForwardRun, run_walk_forward
from app.domain import Match, MatchCollection
from app.evaluation import EvaluationRecord, EvaluationResult, evaluate_predictions
from app.evaluation.evaluate import build_evaluation_record
from app.forecasts import Forecast
from app.ingestion import import_fixture
from app.simulation import DEFAULT_N_SIMS, SimulationResult, simulate
from app.storage import forecasts_db

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"
FIXTURE_FILES = ("season-1.json", "season-2.json")
CHECKPOINT = "02b86cd"

# Consumed pin (criterion 1): the Phase 9 golden run digest, asserted before
# any evaluation call.  golden: first green run; re-derive, never widen.
GOLDEN_RUN_DIGEST = "150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f"

# Criterion 2 consumption literals, re-declared from the Phase 11 pins
# (tests/test_evaluation.py:55-80), byte-matching their source.
# golden: first green run; re-derive, never widen, never delete.
GOLDEN_METRICS = {
    "primary.model": (30, 1.0893088945036264, 0.657717020755589, 0.23748019128548054),
    "primary.baseline": (30, 1.0756660244986818, 0.6513262608006456, 0.2350484286002546),
    "secondary.model": (57, 1.172910978563622, 0.7110877726071556, 0.2599049808350038),
    "secondary.baseline": (57, 1.10026212693129, 0.6659747894436246, 0.2385794979516648),
}
GOLDEN_BINS = {
    "primary": ((2, 0.1922355541990161, 0.5), (73, 0.3068857322030056, 0.3013698630136986),
                (15, 0.48085802938550376, 0.4666666666666667), (0, None, None), (0, None, None)),
    "secondary": ((6, 0.16572509513274955, 0.6666666666666666), (137, 0.30851337436509413, 0.32116788321167883),
                  (27, 0.4853685454016753, 0.3333333333333333), (1, 0.6343664153403693, 0.0), (0, None, None)),
}
GOLDEN_DOMINANT_SHARE = {"primary": 0.8111111111111111, "secondary": 0.8011695906432749}
GOLDEN_DRAW_DEFICIT = {"primary": -0.03437540133650058, "secondary": -0.025271786352718206}

# Criterion 8's new golden.  golden: first green run on CPython 3.12.3 — a
# deterministic re-render of the Phase 11-pinned values through sanctioned
# code (consumption, ADV-12.2).  Derivation: one composed pass,
# sha256(record.payload.encode("utf-8")).  Re-derive on interpreter/spec
# change, never widen, never delete.
GOLDEN_RECORD_HASH = "ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47"

# Criterion 5: the only seeded leg reuses Phase 4's registered golden seed
# (tests/test_simulation.py:65 GOLDEN_SEED) — not a new number.  n_sims is
# imported from app.simulation, never re-literal'd.
REPLAY_SEED = 20261017

# Criterion 6 poison: existing teams only, extreme scores, one entry ON the
# final fixture date (2025-10-11) and two strictly after it.  Every natural
# key is new, so no clean key is duplicated.
POISON_ADDITIONS = (
    {"round": "11", "date": "2025-10-11", "team1": "Coralgate Athletic", "team2": "Emberfield Kestrels", "score": {"ft": [9, 0]}},
    {"round": "11", "date": "2025-10-18", "team1": "Silverpine Rovers", "team2": "Harbourlight Comets", "score": {"ft": [7, 0]}},
    {"round": "11", "date": "2025-10-25", "team1": "Emberfield Kestrels", "team2": "Quarryhill Zenith", "score": {"ft": [0, 8]}},
)

# Criterion 10: the four pinned honest-negation sentences (S1-S4) and the §6
# consumption sentence, verbatim (line-wrap-normalized) from docs/EVALUATION.md.
HONESTY_SENTENCES = (
    "These numbers are descriptive evaluations of a small synthetic sample; they are not evidence of predictive skill.",
    "Model and baseline values appear side by side as absolute quantities; no difference, ratio, ranking, or verdict between them is computed or claimed.",
    "Calibration bins are counts and frequencies only; no reliability or goodness-of-fit claim follows from them.",
    "No forecast is called validated, accurate, or beating anything.",
)
CONSUMPTION_SENTENCE = (
    "Phase 12 consumes this phase's records and recomputes nothing; every evaluation entry point stays re-runnable and read-only."
)

# Criterion 4: stdlib + app.* only, full chain, ONE canonical JSON line.
# `python -c` puts cwd on sys.path, so cwd=REPO_ROOT needs no PYTHONPATH.
_CROSS_PROCESS_SCRIPT = r"""
import hashlib, json
from pathlib import Path
from app.domain import MatchCollection
from app.ingestion import import_fixture
from app.backtesting import run_walk_forward
from app.evaluation import evaluate_predictions
from app.evaluation.evaluate import build_evaluation_record
root = Path.cwd()
fixtures = root / "fixtures" / "openfootball" / "valid"
names = ("season-1.json", "season-2.json")
collection = MatchCollection()
for name in names:
    import_fixture(fixtures / name, collection)
matches = tuple(record.match for record in collection.records())
run = run_walk_forward(matches)
digest = run.manifest.run_digest
result = evaluate_predictions(run.predictions, run.baselines, matches, run_digest=digest, expected_run_digest=digest)
hashes = tuple((name, hashlib.sha256((fixtures / name).read_bytes()).hexdigest()) for name in names)
record = build_evaluation_record(result, run_digest=digest, fixture_file_sha256s=hashes)
accounting = result.accounting
print(json.dumps({
    "run_digest": digest,
    "accounting": [accounting.n_targets, accounting.n_predictions, accounting.n_refusals,
                   accounting.n_flagged, accounting.n_clean],
    "payload_sha256": hashlib.sha256(record.payload.encode("utf-8")).hexdigest(),
    "record_content_hash": record.content_hash,
}, sort_keys=True))
"""


def _prediction_key(prediction: Forecast) -> tuple[str, str, str, str, str]:
    """The prediction's natural key: field order identical to Match's."""
    return (prediction.competition, prediction.season, prediction.date, prediction.home, prediction.away)


def _pairs(predictions: tuple[Forecast, ...]) -> tuple[tuple[tuple[str, str, str, str, str], str], ...]:
    """Ordered (natural key, content_hash) pairs of a prediction tuple."""
    return tuple((_prediction_key(p), p.content_hash) for p in predictions)


def _fixture_hashes() -> tuple[tuple[str, str], ...]:
    """Real sha256 of each fixture file's bytes, in the pinned name order."""
    return tuple((name, hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest()) for name in FIXTURE_FILES)


def _entries_digest(predictions: tuple[Forecast, ...]) -> str:
    """sha256 over the ordered (fixture key, content_hash) list of predictions."""
    entries = [[[p.competition, p.season, p.date, p.home, p.away], p.content_hash] for p in predictions]
    return hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _load_matches() -> tuple[Match, ...]:
    """Ingest the two checked-in fixture files into one ordered pool."""
    collection = MatchCollection()
    import_fixture(FIXTURES / "season-1.json", collection)
    import_fixture(FIXTURES / "season-2.json", collection)
    return tuple(record.match for record in collection.records())


def _git(*arguments: str) -> str:
    """One `git <arguments>` stdout; exit 0 enforced (test_operational pattern)."""
    completed = subprocess.run(["git", *arguments], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout


def _canonical_simulation_json(result: SimulationResult) -> str:
    """Byte-identical canonical JSON; `default` renders the ConvergenceStatus value."""
    return json.dumps(dataclasses.asdict(result), sort_keys=True, separators=(",", ":"),
                      default=lambda value: value.value)


@dataclasses.dataclass(frozen=True)
class Composed:
    """One composed pass's artifacts, captured for 1:1 criterion assertions."""

    matches: tuple[Match, ...]
    run: WalkForwardRun
    result: EvaluationResult
    record: EvaluationRecord
    insert_results: tuple[bool, ...]
    record_inserted: bool
    dump_before: list[tuple]
    dump_after: list[tuple]
    evaluation_rows: list[tuple]
    read_back: tuple[Forecast, ...]


def _compose(matches: tuple[Match, ...], db_path: Path) -> Composed:
    """ONE full pass: harness -> evaluation -> record -> store -> read-back.

    The digest gate is asserted here, before any evaluation call (ADV-6 at
    chain scope).  No metric is asserted here: assertions live in the tests.
    """
    run = run_walk_forward(matches)
    assert run.manifest.run_digest == GOLDEN_RUN_DIGEST
    result = evaluate_predictions(run.predictions, run.baselines, matches,
                                  run_digest=GOLDEN_RUN_DIGEST, expected_run_digest=GOLDEN_RUN_DIGEST)
    record = build_evaluation_record(result, run_digest=GOLDEN_RUN_DIGEST, fixture_file_sha256s=_fixture_hashes())
    writer = forecasts_db.open_forecasts_db(str(db_path))
    insert_results = tuple(forecasts_db.insert_forecast(writer, p) for p in run.predictions)
    dump_sql = "SELECT * FROM forecasts ORDER BY competition, season, date, home, away"
    dump_before = writer.execute(dump_sql).fetchall()
    record_inserted = forecasts_db.insert_evaluation_record(writer, record)
    dump_after = writer.execute(dump_sql).fetchall()
    evaluation_rows = writer.execute(
        "SELECT evaluation_version, run_digest, fixture_file_sha256s, content_hash FROM evaluations").fetchall()
    writer.close()
    reader = forecasts_db.open_read_connection(str(db_path))
    try:
        read_back = tuple(forecasts_db.verify_all(reader))
    finally:
        reader.close()
    return Composed(matches, run, result, record, insert_results, record_inserted,
                    dump_before, dump_after, evaluation_rows, read_back)


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory: pytest.TempPathFactory) -> Composed:
    """The one composed pass shared by criteria 1, 2, 4, 5, 7 and 8."""
    return _compose(_load_matches(), tmp_path_factory.mktemp("phase12") / "pipeline.db")


def test_one_pass_composition_fixture_files_through_record_and_readback(pipeline: Composed) -> None:
    run, result = pipeline.run, pipeline.result
    assert (run.n_targets, run.n_predictions, run.n_refusals, run.n_flagged, run.n_clean) == (60, 57, 3, 27, 30)
    accounting = result.accounting
    assert (accounting.n_targets, accounting.n_predictions) == (60, 57)
    assert (accounting.n_refusals, accounting.n_flagged, accounting.n_clean) == (3, 27, 30)
    assert accounting.n_targets == 3 + 27 + 30 == 60  # 60 = 3 + 27 + 30
    assert pipeline.insert_results == (True,) * 57 and pipeline.record_inserted is True
    assert len(pipeline.read_back) == 57
    read_back_pairs = _pairs(pipeline.read_back)
    expected_pairs = _pairs(tuple(sorted(run.predictions, key=lambda p: (p.competition, p.season, p.date, p.home, p.away))))
    assert read_back_pairs == expected_pairs  # hash-clean round trip
    assert pipeline.dump_after == pipeline.dump_before  # record insert never altered forecasts
    assert len(pipeline.evaluation_rows) == 1
    version, digest, stored_hashes, stored_content = pipeline.evaluation_rows[0]
    assert version == pipeline.record.evaluation_version == 1
    assert digest == pipeline.record.run_digest == GOLDEN_RUN_DIGEST
    assert tuple(tuple(pair) for pair in json.loads(stored_hashes)) == pipeline.record.fixture_file_sha256s
    assert stored_content == pipeline.record.content_hash


def test_composed_run_consumes_pinned_metrics_bins_and_diagnostics(pipeline: Composed) -> None:
    result = pipeline.result
    for name in ("primary", "secondary"):
        population = getattr(result, name)
        for side in ("model", "baseline"):
            triple = getattr(population, side)
            assert (triple.n, triple.log_loss, triple.brier, triple.rps) == GOLDEN_METRICS[f"{name}.{side}"]
        table = population.calibration
        assert len(table.bins) == 5  # always five bins
        assert tuple((b.n, b.mean_p, b.realized_frequency) for b in table.bins) == GOLDEN_BINS[name]
        assert sum(b.n for b in table.bins) == table.n_pairs == 3 * population.n_matches
        assert max(b.n for b in table.bins) / table.n_pairs == GOLDEN_DOMINANT_SHARE[name]
    for name, independent_draws in (("primary", 7), ("secondary", 14)):
        population = getattr(result, name)
        assert sum(1 for c in population.contributions if c.outcome == "D") == independent_draws
        assert population.draw_deficit == GOLDEN_DRAW_DEFICIT[name]
    diagnostic = result.overdispersion
    assert diagnostic.n == 114 and diagnostic.mean == 149 / 114
    assert round(diagnostic.mean, 3) == 1.307
    assert round(diagnostic.variance, 3) == 0.967  # ddof = 0
    ddof_one = diagnostic.variance * 114 / 113
    assert round(ddof_one, 4) == 0.9757 and diagnostic.variance != ddof_one  # denominator pinned
    first_date = min(match.date for match in pipeline.matches)
    expected_refusals = tuple(sorted(
        (match.natural_key for match in pipeline.matches if match.date == first_date),
        key=lambda key: (key[2], key[0], key[1], key[3], key[4])))
    assert len(expected_refusals) == 3
    assert result.accounting.refusal_keys == expected_refusals
    accounting_fields = {field.name for field in dataclasses.fields(type(result.accounting))}
    assert accounting_fields == {"n_targets", "n_predictions", "n_refusals", "n_flagged", "n_clean", "refusal_keys"}
    assert not accounting_fields & {"log_loss", "brier", "rps"}  # no metric container for n = 60


def test_double_run_in_process_byte_identity(pipeline: Composed, tmp_path: Path) -> None:
    second = _compose(pipeline.matches, tmp_path / "second-pass.db")
    assert second.run.manifest.run_digest == pipeline.run.manifest.run_digest == GOLDEN_RUN_DIGEST
    assert _pairs(second.run.predictions) == _pairs(pipeline.run.predictions)
    assert _entries_digest(second.run.predictions) == _entries_digest(pipeline.run.predictions)
    assert second.result == pipeline.result  # frozen dataclasses, exact floats
    assert second.record.payload == pipeline.record.payload  # byte equality
    assert second.record.content_hash == pipeline.record.content_hash
    assert second.read_back == pipeline.read_back and len(second.read_back) == 57


def test_cross_process_determinism_distinct_hash_seeds(pipeline: Composed) -> None:
    lines = []
    for hash_seed in ("0", "424242"):
        completed = subprocess.run([sys.executable, "-c", _CROSS_PROCESS_SCRIPT], cwd=REPO_ROOT,
                                   env={**os.environ, "PYTHONHASHSEED": hash_seed},
                                   capture_output=True, text=True, check=False)
        assert completed.returncode == 0, completed.stderr
        assert completed.stderr == ""
        lines.append(completed.stdout)
    assert lines[0] == lines[1]  # cross-process bit-identity
    assert lines[0].count("\n") == 1  # one canonical JSON line
    assert json.loads(lines[0]) == {
        "run_digest": GOLDEN_RUN_DIGEST,
        "accounting": [60, 57, 3, 27, 30],
        "payload_sha256": hashlib.sha256(pipeline.record.payload.encode("utf-8")).hexdigest(),
        "record_content_hash": GOLDEN_RECORD_HASH,
    }


def test_seeded_simulation_leg_replayed_twice_identical(pipeline: Composed) -> None:
    prediction = pipeline.run.predictions[-1]  # the only seeded leg, one fixture
    first = simulate(prediction.fitted, prediction.home, prediction.away, seed=REPLAY_SEED, n_sims=DEFAULT_N_SIMS)
    second = simulate(prediction.fitted, prediction.home, prediction.away, seed=REPLAY_SEED, n_sims=DEFAULT_N_SIMS)
    assert REPLAY_SEED == 20261017  # Phase 4's registered GOLDEN_SEED
    assert DEFAULT_N_SIMS == 10_000
    assert first == second  # frozen-dataclass equality
    assert _canonical_simulation_json(first) == _canonical_simulation_json(second)
    assert (first.seed, first.n_sims, first.sim_version) == (REPLAY_SEED, DEFAULT_N_SIMS, "sim-categorical-v1")
    assert first.counts_home + first.counts_draw + first.counts_away == DEFAULT_N_SIMS
    # Analytic-first (§7e): the simulation result feeds no metric anywhere.
    assert not {"log_loss", "brier", "rps"} & {field.name for field in dataclasses.fields(SimulationResult)}


def test_composite_poison_at_ingestion_input_freezes_every_artifact_hash(
    pipeline: Composed, tmp_path: Path
) -> None:
    for name in FIXTURE_FILES:
        payload = json.loads((FIXTURES / name).read_text(encoding="utf-8"))
        if name == "season-2.json":
            payload["matches"].extend(POISON_ADDITIONS)
        (tmp_path / name).write_text(json.dumps(payload), encoding="utf-8")
    collection = MatchCollection()
    for name in FIXTURE_FILES:
        assert import_fixture(tmp_path / name, collection, root=tmp_path).report.defects == ()
    poisoned_matches = tuple(record.match for record in collection.records())
    assert len(poisoned_matches) == 63  # the 3 poisons entered the pool
    poisoned_run = run_walk_forward(poisoned_matches)
    assert len(poisoned_run.predictions) == 60  # positive control: poisons were targets
    original_keys = {match.natural_key for match in pipeline.matches}
    filtered_predictions = tuple(p for p in poisoned_run.predictions if _prediction_key(p) in original_keys)
    filtered_baselines = tuple(b for b in poisoned_run.baselines if b.fixture_key in original_keys)
    assert (len(filtered_predictions), len(filtered_baselines)) == (57, 60)
    clean_hashes = {_prediction_key(p): p.content_hash for p in pipeline.run.predictions}
    assert all(clean_hashes[_prediction_key(p)] == p.content_hash for p in filtered_predictions)
    assert _entries_digest(filtered_predictions) == GOLDEN_RUN_DIGEST
    clean_baselines = {b.fixture_key: b for b in pipeline.run.baselines}
    assert all(clean_baselines[b.fixture_key] == b for b in filtered_baselines)
    poisoned_result = evaluate_predictions(filtered_predictions, filtered_baselines, pipeline.matches,
                                           run_digest=GOLDEN_RUN_DIGEST, expected_run_digest=GOLDEN_RUN_DIGEST)
    assert poisoned_result == pipeline.result  # field-for-field, exact floats
    poisoned_record = build_evaluation_record(poisoned_result, run_digest=GOLDEN_RUN_DIGEST,
                                              fixture_file_sha256s=_fixture_hashes())
    assert poisoned_record.content_hash == GOLDEN_RECORD_HASH


def test_write_once_across_both_tables_in_one_store(pipeline: Composed, tmp_path: Path) -> None:
    db = tmp_path / "both-tables.db"
    connection = forecasts_db.open_forecasts_db(str(db))
    try:
        assert [forecasts_db.insert_forecast(connection, p) for p in pipeline.run.predictions] == [True] * 57
        trace: list[str] = []
        connection.set_trace_callback(trace.append)
        assert forecasts_db.insert_forecast(connection, pipeline.run.predictions[0]) is False
        assert [sql for sql in trace if "INSERT INTO forecasts" in sql] == []  # zero INSERTs
        for statement in ("UPDATE forecasts SET lambda_home = lambda_home", "DELETE FROM forecasts"):
            with pytest.raises(sqlite3.IntegrityError, match="forecasts are immutable: (UPDATE|DELETE) refused"):
                connection.execute(statement)
            connection.rollback()
        assert forecasts_db.insert_evaluation_record(connection, pipeline.record) is True
        trace.clear()
        assert forecasts_db.insert_evaluation_record(connection, pipeline.record) is False
        assert [sql for sql in trace if "INSERT INTO" in sql] == []  # zero INSERTs
        for statement in ("UPDATE evaluations SET content_hash = content_hash", "DELETE FROM evaluations"):
            with pytest.raises(sqlite3.IntegrityError, match="evaluations are immutable: (UPDATE|DELETE) refused"):
                connection.execute(statement)
            connection.rollback()
        assert connection.execute("SELECT COUNT(*) FROM evaluations").fetchone() == (1,)
        assert forecasts_db.SCHEMA_VERSION == 2
    finally:
        connection.close()
    reader = forecasts_db.open_read_connection(str(db))
    try:
        verified = tuple(forecasts_db.verify_all(reader))
    finally:
        reader.close()
    assert len(verified) == 57 and verified == pipeline.read_back


def test_record_content_hash_matches_new_golden_consumption(pipeline: Composed) -> None:
    record = pipeline.record
    assert record.content_hash == GOLDEN_RECORD_HASH
    assert record.content_hash == hashlib.sha256(record.payload.encode("utf-8")).hexdigest()
    payload = json.loads(record.payload)
    for name in ("primary", "secondary"):
        for side in ("model", "baseline"):
            block = payload[name][side]
            assert (block["n"], block["log_loss"], block["brier"], block["rps"]) == GOLDEN_METRICS[f"{name}.{side}"]
    assert json.dumps(json.loads(record.payload), sort_keys=True, separators=(",", ":")) == record.payload
    assert re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", record.payload) is None  # no clock form
    assert record.fixture_file_sha256s == _fixture_hashes()  # the pinned EVALUATION.md §6 values


def test_zero_new_app_production_surface() -> None:
    assert _git("diff", CHECKPOINT, "--", "app/") == ""  # zero production changes
    assert set(_git("diff", "--name-only", CHECKPOINT, "--", "tests/").split()) <= {"tests/test_integration.py"}
    assert not (REPO_ROOT / "app" / "improvement").exists() and not (REPO_ROOT / "app" / "state").exists()
    registry = temporal.POISON_REGISTRY
    assert set(registry) == {
        "fit", "build_forecast", "compute_features", "build_decision_report",
        "storage.get_forecast/verify_all", "run_walk_forward", "evaluate_predictions",
    }
    resolved = temporal.validate_registry(registry)
    assert set(resolved) == set(registry) and all(callable(test) for test in resolved.values())
    assert temporal.MATCHES_ENTRY_POINTS == (
        "fit", "build_forecast", "compute_features", "run_walk_forward", "evaluate_predictions"
    )  # census unchanged at 5
    assert temporal.PHASE10_CHECKPOINT == "8abe1ca"
    for line in _git("status", "--porcelain").splitlines():
        status, path = line[:2], line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        assert not path.startswith("app/"), (status, path)
        if path.startswith("tests/"):
            assert (status, path) == ("??", "tests/test_integration.py"), (status, path)


def test_docs_honesty_pins_s1_s4_consumption_no_section14() -> None:
    evaluation_text = (REPO_ROOT / "docs" / "EVALUATION.md").read_text(encoding="utf-8")
    normalized = " ".join(evaluation_text.split())
    for sentence in HONESTY_SENTENCES:
        assert sentence in normalized, sentence
    assert CONSUMPTION_SENTENCE in normalized
    assumptions_text = (REPO_ROOT / "docs" / "STATISTICAL-ASSUMPTIONS.md").read_text(encoding="utf-8")
    assert re.search(r"^##\s+14(?:\.|\s|$)", assumptions_text, re.MULTILINE) is None  # no §14
    assert re.findall(r"^##\s+(\d+)\.", assumptions_text, re.MULTILINE)[-1] == "13"  # ends at §13
