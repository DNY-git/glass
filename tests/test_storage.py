"""Phase 5 acceptance criteria 8-15: the write-once sqlite store.

Schema-level immutability triggers surviving raw connections (8),
idempotent no-op + identity-conflict hard error + UNIQUE backstop (9),
store/read round trip recomputing the hash on every row (10), tamper
detection as a hard error (11), the nasty-float battery through REAL
columns and JSON tuple encodings (12), the query_only read path (13),
exactly-one-INSERT statement counting + backup verification (14), and
the timestamp-free pinned schema (15). Criterion 8's exception type is
sqlite3.IntegrityError per the architect ruling (ERRATUM 2026-10-17 at
criterion 8 under AMENDMENTS A3–A5 in docs/briefs/phase-5.md: every
sqlite3 RAISE variant inside a trigger surfaces as IntegrityError; the
ABORT message is asserted either way).
"""

from __future__ import annotations

import ast
import dataclasses
import json
import math
import sqlite3
from pathlib import Path

import pytest

from app.domain import Fixture, MatchCollection, OptionalValue
from app.forecasts import (
    FORECAST_VERSION,
    Forecast,
    ForecastConflictError,
    ForecastIntegrityError,
    build_forecast,
)
from app.ingestion import import_fixture
from app.models import (
    ConvergenceStatus,
    FitConfig,
    FittedParams,
    PoolingRecord,
    SampleSize,
)
from app.storage import (
    COLUMN_NAMES,
    backup_forecasts,
    get_forecast,
    insert_forecast,
    open_forecasts_db,
    open_read_connection,
    verify_all,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"
APP_DIR = REPO_ROOT / "app"

ALL_MATCHES: tuple
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

FIXTURE_A = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Coralgate Athletic",
    away="Thistledown Wanderers",
    kickoff=OptionalValue.missing(),
)
FIXTURE_B = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Quarryhill Zenith",
    away="Harbourlight Comets",
    kickoff=OptionalValue.missing(),
)

# The pinned schema (criterion 15): the exact column-name list, and no
# created_at/timestamp/mtime-like column anywhere (S2: the hash must be
# recomputable from stored fields alone).
PINNED_COLUMNS = (
    "competition",
    "season",
    "date",
    "home",
    "away",
    "as_of",
    "model_version",
    "input_digest",
    "config",
    "forecast_version",
    "kickoff_value",
    "kickoff_availability",
    "lambda_home",
    "lambda_away",
    "max_goals",
    "dropped_mass",
    "outcome_home",
    "outcome_draw",
    "outcome_away",
    "fitted",
    "content_hash",
)


def _forecast_a() -> Forecast:
    return build_forecast(ALL_MATCHES, FIXTURE_A)


def _forecast_b() -> Forecast:
    return build_forecast(ALL_MATCHES, FIXTURE_B)


def _key(fixt: Fixture) -> tuple[str, str, str, str, str]:
    return (fixt.competition, fixt.season, fixt.date, fixt.home, fixt.away)


def test_forecasts_table_write_once_triggers_abort_raw_writes(tmp_path: Path) -> None:
    # Criterion 8 (S1): enforcement lives in the database file itself —
    # a FRESH RAW sqlite3 connection (CLI-equivalent access) cannot
    # UPDATE or DELETE rows; the ABORT message is present and the
    # original rows are byte-identical afterwards. (Exception type is
    # sqlite3.IntegrityError: the Python mapping of a trigger's
    # RAISE(ABORT); architect ruling, ERRATUM 2026-10-17 at criterion
    # 8 under AMENDMENTS A3–A5 in docs/briefs/phase-5.md.)
    db = tmp_path / "forecasts.db"
    connection = open_forecasts_db(str(db))
    assert insert_forecast(connection, _forecast_a())
    assert insert_forecast(connection, _forecast_b())
    connection.close()

    raw = sqlite3.connect(str(db))
    before = raw.execute("SELECT * FROM forecasts ORDER BY home").fetchall()
    assert len(before) == 2
    with pytest.raises(sqlite3.IntegrityError) as update_error:
        raw.execute("UPDATE forecasts SET lambda_home = 0.0")
    assert "immutable" in str(update_error.value)
    assert "UPDATE refused" in str(update_error.value)
    with pytest.raises(sqlite3.IntegrityError) as delete_error:
        raw.execute("DELETE FROM forecasts")
    assert "immutable" in str(delete_error.value)
    assert "DELETE refused" in str(delete_error.value)
    after = raw.execute("SELECT * FROM forecasts ORDER BY home").fetchall()
    assert after == before  # byte-identical rows
    raw.close()


def test_insert_idempotent_noop_and_conflicting_hash_hard_error(tmp_path: Path) -> None:
    # Criterion 9 (F4): identical identity + identical content hash =
    # idempotent no-op (one row, no error, dedup token = content hash);
    # identical identity + different content hash = hard error, never
    # an overwrite; the UNIQUE identity constraint is the backstop.
    db = tmp_path / "forecasts.db"
    connection = open_forecasts_db(str(db))
    forecast = _forecast_a()
    assert insert_forecast(connection, forecast) is True
    assert insert_forecast(connection, forecast) is False  # documented no-op
    count = connection.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0]
    assert count == 1  # row count unchanged by the no-op

    perturbed = dataclasses.replace(
        forecast, dropped_mass=math.nextafter(forecast.dropped_mass, math.inf)
    )
    assert perturbed.content_hash != forecast.content_hash  # same identity
    with pytest.raises(ForecastConflictError):
        insert_forecast(connection, perturbed)

    stored = connection.execute(
        "SELECT content_hash, dropped_mass FROM forecasts"
    ).fetchone()
    assert stored[0] == forecast.content_hash  # original hash intact
    assert stored[1] == forecast.dropped_mass  # original row untouched

    # UNIQUE identity backstop: a raw duplicate-identity INSERT with
    # different content is refused by the schema itself.
    row = connection.execute("SELECT * FROM forecasts").fetchone()
    columns = list(COLUMN_NAMES)
    backstop = list(row)
    backstop[columns.index("content_hash")] = "0" * 64
    placeholders = ", ".join("?" for _ in columns)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            f"INSERT INTO forecasts ({', '.join(columns)}) VALUES ({placeholders})",
            tuple(backstop),
        )
    connection.close()


def test_store_read_round_trip_recomputes_hash_every_row(tmp_path: Path) -> None:
    # Criterion 10 (F3/S3): build -> insert -> get_forecast equals the
    # original field-for-field (frozen ==), and the hash recomputed
    # from the stored DB fields alone equals both the stored hash and
    # the object's — per row, every row, not spot checks; verify_all
    # passes over the whole file.
    db = tmp_path / "forecasts.db"
    connection = open_forecasts_db(str(db))
    first, second = _forecast_a(), _forecast_b()
    assert insert_forecast(connection, first)
    assert insert_forecast(connection, second)
    connection.close()

    reader = open_read_connection(str(db))
    for original, key in ((first, _key(FIXTURE_A)), (second, _key(FIXTURE_B))):
        loaded = get_forecast(reader, *key)
        assert loaded == original  # field-for-field, incl. recomputed hash
        assert loaded is not None
        stored_hash = reader.execute(
            "SELECT content_hash FROM forecasts WHERE home = ?", (original.home,)
        ).fetchone()[0]
        assert stored_hash == original.content_hash == loaded.content_hash
    verified = verify_all(reader)
    assert len(verified) == 2
    assert first in verified and second in verified
    reader.close()


def test_tampered_content_is_hard_error_never_warning(tmp_path: Path) -> None:
    # Criterion 11 (F3): one REAL perturbed by 1 ulp relative to its
    # stored hash fails verification with the pinned integrity
    # exception — never a warning, never a returned value — the
    # message identifies the fixture key, and the abort leaves the
    # stored row exactly as it was found.
    db = tmp_path / "forecasts.db"
    connection = open_forecasts_db(str(db))
    forecast = _forecast_a()
    assert insert_forecast(connection, forecast)
    connection.close()

    # Doctor the row: the triggers guard UPDATE, so drop only the
    # update trigger on this throwaway tmp DB, then nudge one REAL by
    # a single ulp (the read path — not the triggers — must catch it).
    raw = sqlite3.connect(str(db))
    original_lambda = raw.execute(
        "SELECT lambda_home FROM forecasts WHERE home = ?", (forecast.home,)
    ).fetchone()[0]
    perturbed_lambda = math.nextafter(original_lambda, math.inf)
    raw.execute("DROP TRIGGER forecasts_immutable_update")
    raw.execute(
        "UPDATE forecasts SET lambda_home = ? WHERE home = ?",
        (perturbed_lambda, forecast.home),
    )
    raw.commit()
    raw.close()

    reader = open_read_connection(str(db))
    with pytest.raises(ForecastIntegrityError) as excinfo:
        get_forecast(reader, *_key(FIXTURE_A))
    message = str(excinfo.value)
    assert FIXTURE_A.home in message and FIXTURE_A.away in message
    assert "content hash mismatch" in message

    # After the abort the stored row is unchanged — still tampered,
    # still detected, never rewritten by the failed read.
    verify_again = open_read_connection(str(db))
    with pytest.raises(ForecastIntegrityError):
        verify_all(verify_again)
    raw_again = sqlite3.connect(str(db))
    still = raw_again.execute(
        "SELECT lambda_home, content_hash FROM forecasts WHERE home = ?",
        (forecast.home,),
    ).fetchone()
    assert still[0] == perturbed_lambda
    assert still[1] == forecast.content_hash
    raw_again.close()
    reader.close()
    verify_again.close()


def test_float_round_trip_real_and_json_exact(tmp_path: Path) -> None:
    # Criterion 12 (S3): the nasty-float battery survives BOTH sqlite
    # REAL columns and the JSON tuple encodings (teams' alpha/beta
    # arrays) bit-exactly on read-back, and the hash still verifies.
    golden = _forecast_a()
    nasty = (0.1, math.pi, math.e, 1e-300, 5e-324)  # incl. a subnormal
    fitted = FittedParams(
        model_version=golden.fitted.model_version,
        config=FitConfig(),
        pooling=PoolingRecord(
            competition="Obsidian Coast League",
            seasons=("2024-25",),
            as_of="2025-12-31",
            sample_size=SampleSize(matches=10, goals=25),
        ),
        input_digest="a" * 64,
        teams=("Alpha United", "Beta Rovers"),
        mu=nasty[0],
        home_advantage=nasty[1],
        alpha=(nasty[2], nasty[3]),
        beta=(nasty[4], nasty[0]),
        iterations=7,
        convergence_status=ConvergenceStatus.CONVERGED,
        sample_size=SampleSize(matches=10, goals=25),
        insufficient_data=False,
        insufficient_teams=(),
    )
    # A full-precision lambda from the real fixture fit rides the REAL
    # columns alongside the battery.
    hand_made = Forecast(
        competition="Obsidian Coast League",
        season="2025-26",
        date="2025-12-31",
        home="Alpha United",
        away="Beta Rovers",
        kickoff=OptionalValue.missing(),
        as_of="2025-12-31",
        fitted=fitted,
        lambda_home=golden.lambda_home,
        lambda_away=nasty[0],
        max_goals=10,
        dropped_mass=nasty[1],
        outcome_home=nasty[0],
        outcome_draw=nasty[1],
        outcome_away=nasty[2],
        forecast_version=FORECAST_VERSION,
    )

    db = tmp_path / "floats.db"
    connection = open_forecasts_db(str(db))
    assert insert_forecast(connection, hand_made)
    connection.close()

    reader = open_read_connection(str(db))
    loaded = get_forecast(
        reader, "Obsidian Coast League", "2025-26", "2025-12-31", "Alpha United", "Beta Rovers"
    )
    assert loaded == hand_made  # every float bit-identical, incl. hash
    assert loaded is not None
    assert loaded.fitted.alpha == (nasty[2], nasty[3])  # JSON tuple encoding
    assert loaded.fitted.beta == (nasty[4], nasty[0])
    assert loaded.fitted.mu == nasty[0]
    assert loaded.lambda_home == golden.lambda_home  # REAL column
    assert loaded.dropped_mass == nasty[1]
    assert verify_all(reader) == (hand_made,)
    reader.close()


def test_read_path_opens_query_only(tmp_path: Path) -> None:
    # Criterion 13 (S1/A3): the connection used by get_forecast is put
    # into PRAGMA query_only = 1 — behaviorally, an INSERT on that
    # same connection raises sqlite3.OperationalError.
    db = tmp_path / "forecasts.db"
    writer = open_forecasts_db(str(db))
    assert insert_forecast(writer, _forecast_a())
    writer.close()

    connection = sqlite3.connect(str(db))
    loaded = get_forecast(connection, *_key(FIXTURE_A))
    assert loaded is not None
    pragma = connection.execute("PRAGMA query_only").fetchone()[0]
    assert pragma == 1
    with pytest.raises(sqlite3.OperationalError):
        connection.execute(
            "INSERT INTO forecasts (competition) VALUES ('x')"
        )
    connection.close()

    # The dedicated read opener sets the same pragma at open time.
    dedicated = open_read_connection(str(db))
    assert dedicated.execute("PRAGMA query_only").fetchone()[0] == 1
    dedicated.close()


def test_single_insert_in_immediate_transaction_and_backup_verifies(tmp_path: Path) -> None:
    # Criterion 14 (S4): statement tracing proves a fresh insert runs
    # exactly one INSERT (plus the identity SELECT) inside a BEGIN
    # IMMEDIATE transaction; the idempotent no-op path runs zero
    # INSERTs; backup_forecasts (Connection.backup) yields a file
    # whose rows all pass hash verification through the normal read
    # path.
    db = tmp_path / "forecasts.db"
    connection = open_forecasts_db(str(db))
    statements: list[str] = []
    connection.set_trace_callback(statements.append)

    forecast = _forecast_a()
    assert insert_forecast(connection, forecast)
    inserts = [s for s in statements if s.strip().upper().startswith("INSERT")]
    assert len(inserts) == 1, statements
    assert any(s.strip().upper().startswith("BEGIN IMMEDIATE") for s in statements)
    assert any(s.strip().upper().startswith("SELECT") for s in statements)

    statements.clear()
    assert insert_forecast(connection, forecast) is False
    assert not [s for s in statements if s.strip().upper().startswith("INSERT")]
    connection.close()

    backup_path = tmp_path / "backup.db"
    backup_forecasts(str(db), str(backup_path))
    verified = verify_all(open_read_connection(str(backup_path)))
    assert verified == (forecast,)
    assert verified[0].content_hash == forecast.content_hash


def test_schema_has_no_timestamp_column(tmp_path: Path) -> None:
    # Criterion 15 (S2): the exact column list is pinned; no
    # created_at/timestamp/mtime-like column exists; and neither
    # app/storage/*.py nor app/forecasts/*.py imports datetime or time
    # (AST — also enforced by criterion 22's allowlists).
    db = tmp_path / "schema.db"
    connection = open_forecasts_db(str(db))
    names = tuple(
        row[1] for row in connection.execute("PRAGMA table_info(forecasts)")
    )
    connection.close()
    assert names == PINNED_COLUMNS
    assert tuple(COLUMN_NAMES) == PINNED_COLUMNS
    banned_fragments = ("created", "modified", "updated", "stamp", "time", "clock")
    for name in names:
        assert not any(fragment in name.lower() for fragment in banned_fragments), name

    for package in ("storage", "forecasts"):
        for path in sorted((APP_DIR / package).rglob("*.py")):
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    targets = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    targets = [node.module or ""]
                else:
                    continue
                for target in targets:
                    root = target.split(".")[0]
                    assert root not in {"datetime", "time"}, f"{path}: {target}"


def test_evaluations_table_write_once_no_timestamp_schema_v2(tmp_path: Path) -> None:
    # NOTE: Semantics per criterion 16 as
    # amended 2026-10-23 — the second
    # identical insert is the idempotent
    # False no-op (zero INSERTs); only a
    # DIFFERING payload under the same natural
    # identity raises EvaluationConflictError.
    import test_fixtures_and_hygiene as hygiene

    from app.evaluation import EVALUATION_VERSION, EvaluationConflictError, EvaluationRecord
    from app.storage import forecasts_db

    assert forecasts_db.SCHEMA_VERSION == 2
    assert hygiene.BANNED_IMPORT_EXCEPTIONS == {"app.storage": {"sqlite3"}, "app.api": {"http"}}
    db = tmp_path / "evaluations-schema.db"
    connection = open_forecasts_db(str(db))
    record = EvaluationRecord(
        evaluation_version=EVALUATION_VERSION,
        run_digest="probe-digest",
        fixture_file_sha256s=(("season-1.json", "a" * 64),),
        payload='{"probe":1}',
    )
    assert forecasts_db.insert_evaluation_record(connection, record) is True
    assert forecasts_db.insert_evaluation_record(connection, record) is False  # criterion 16
    differing = dataclasses.replace(record, payload='{"probe":2}')
    assert differing.content_hash != record.content_hash
    with pytest.raises(EvaluationConflictError):  # write-once: differing content, same identity
        forecasts_db.insert_evaluation_record(connection, differing)
    connection.close()

    raw = sqlite3.connect(str(db))
    tables = tuple(row[0] for row in raw.execute("SELECT name FROM sqlite_master WHERE type = 'table'"))
    assert tables == ("forecasts", "evaluations")  # creation order pinned, never set()
    evaluations_columns = tuple(row[1] for row in raw.execute("PRAGMA table_info(evaluations)"))
    assert evaluations_columns == (
        "evaluation_version", "run_digest", "fixture_file_sha256s", "payload", "content_hash",
    )
    banned_fragments = ("created", "modified", "updated", "stamp", "time", "clock")
    for name in evaluations_columns:  # no timestamp-like column anywhere
        assert not any(fragment in name.lower() for fragment in banned_fragments), name
    # Raw CLI-equivalent UPDATE/DELETE abort: the trigger pair lives in
    # the file itself, message convention mirrored from the forecasts
    # triggers (sqlite3 RAISE(ABORT) surfaces as IntegrityError).
    rows_before = raw.execute("SELECT * FROM evaluations").fetchall()
    assert len(rows_before) == 1
    with pytest.raises(sqlite3.IntegrityError) as update_error:
        raw.execute("UPDATE evaluations SET payload = '{}'")
    assert "immutable" in str(update_error.value)
    with pytest.raises(sqlite3.IntegrityError) as delete_error:
        raw.execute("DELETE FROM evaluations")
    assert "immutable" in str(delete_error.value)
    assert raw.execute("SELECT * FROM evaluations").fetchall() == rows_before  # untouched
    # The forecasts surface is untouched: exactly the 21 pinned columns.
    forecasts_columns = tuple(row[1] for row in raw.execute("PRAGMA table_info(forecasts)"))
    assert forecasts_columns == tuple(COLUMN_NAMES) and len(forecasts_columns) == 21
    raw.close()
