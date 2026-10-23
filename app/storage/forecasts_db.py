"""Durable write-once sqlite store for frozen snapshots and evaluations.

Two pinned tables (forecasts, evaluations), one schema version, no
migrations framework, no ORM, no pooling: direct SQL over stdlib sqlite3
(AMENDMENT A2 permits sqlite3 in this package only). Write-once is
enforced **at the schema level**
by BEFORE UPDATE / BEFORE DELETE triggers raising ABORT inside the
database file, so it survives any client including the sqlite3 CLI;
the application layer itself contains no UPDATE/DELETE SQL at all
(AST-scanned). The read path recomputes every returned row's content
hash from the stored fields alone and raises a hard error on any
mismatch — tamper evidence by construction. The DB path is always a
caller-passed argument: never an environment lookup, never a default.
No timestamp column exists anywhere: the hash must be recomputable
from stored fields alone (S2).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.domain import Availability, OptionalValue
from app.evaluation import EvaluationConflictError, EvaluationRecord
from app.forecasts import (
    Forecast,
    ForecastConflictError,
    ForecastIntegrityError,
    config_identity,
    fitted_from_payload,
    fitted_payload,
)

# Schema of the two pinned tables (forecasts, evaluations); version bump
# = new brief.
SCHEMA_VERSION = 2

_FORECASTS_TABLE_DDL = (
    "CREATE TABLE IF NOT EXISTS forecasts ("
    "competition TEXT NOT NULL, "
    "season TEXT NOT NULL, "
    "date TEXT NOT NULL, "
    "home TEXT NOT NULL, "
    "away TEXT NOT NULL, "
    "as_of TEXT NOT NULL, "
    "model_version TEXT NOT NULL, "
    "input_digest TEXT NOT NULL, "
    "config TEXT NOT NULL, "
    "forecast_version TEXT NOT NULL, "
    "kickoff_value TEXT, "
    "kickoff_availability TEXT NOT NULL, "
    "lambda_home REAL NOT NULL, "
    "lambda_away REAL NOT NULL, "
    "max_goals INTEGER NOT NULL, "
    "dropped_mass REAL NOT NULL, "
    "outcome_home REAL NOT NULL, "
    "outcome_draw REAL NOT NULL, "
    "outcome_away REAL NOT NULL, "
    "fitted TEXT NOT NULL, "
    "content_hash TEXT NOT NULL, "
    "UNIQUE (competition, season, date, home, away, as_of, "
    "model_version, input_digest, config, forecast_version)"
    ")"
)

# The schema-level immutability triggers (S1): the sanctioned
# application-layer literals containing the words UPDATE/DELETE (none
# matches a data-statement form, AST-scanned); the forecasts pair is
# pinned verbatim by tests/test_phase5_separation.py criterion 23.
IMMUTABLE_UPDATE_TRIGGER_DDL = (
    "CREATE TRIGGER IF NOT EXISTS forecasts_immutable_update "
    "BEFORE UPDATE ON forecasts "
    "BEGIN SELECT RAISE(ABORT, 'forecasts are immutable: UPDATE refused'); END"
)
IMMUTABLE_DELETE_TRIGGER_DDL = (
    "CREATE TRIGGER IF NOT EXISTS forecasts_immutable_delete "
    "BEFORE DELETE ON forecasts "
    "BEGIN SELECT RAISE(ABORT, 'forecasts are immutable: DELETE refused'); END"
)

# The evaluation table (Phase 11, decision 1): five pinned columns, no
# timestamp, the natural identity as the UNIQUE backstop.
_EVALUATIONS_TABLE_DDL = (
    "CREATE TABLE IF NOT EXISTS evaluations ("
    "evaluation_version INTEGER NOT NULL, "
    "run_digest TEXT NOT NULL, "
    "fixture_file_sha256s TEXT NOT NULL, "
    "payload TEXT NOT NULL, "
    "content_hash TEXT NOT NULL, "
    "UNIQUE (evaluation_version, run_digest, fixture_file_sha256s)"
    ")"
)

# The evaluations table's own schema-level immutability triggers,
# mirroring the forecasts pair (S1/decision 1); private, not exported.
_EVALUATIONS_UPDATE_TRIGGER_DDL = (
    "CREATE TRIGGER IF NOT EXISTS evaluations_immutable_update "
    "BEFORE UPDATE ON evaluations "
    "BEGIN SELECT RAISE(ABORT, 'evaluations are immutable: UPDATE refused'); END"
)
_EVALUATIONS_DELETE_TRIGGER_DDL = (
    "CREATE TRIGGER IF NOT EXISTS evaluations_immutable_delete "
    "BEFORE DELETE ON evaluations "
    "BEGIN SELECT RAISE(ABORT, 'evaluations are immutable: DELETE refused'); END"
)

# Creation order pins the sqlite_master table order (criterion 17).
_DDL = (
    _FORECASTS_TABLE_DDL,
    IMMUTABLE_UPDATE_TRIGGER_DDL,
    IMMUTABLE_DELETE_TRIGGER_DDL,
    _EVALUATIONS_TABLE_DDL,
    _EVALUATIONS_UPDATE_TRIGGER_DDL,
    _EVALUATIONS_DELETE_TRIGGER_DDL,
)

# Identity columns (brief decision 6) and the full column order of the
# table (criterion 15 pins this list; there is deliberately no
# timestamp column — content-hash recomputability, S2).
IDENTITY_COLUMNS: tuple[str, ...] = (
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
)
COLUMN_NAMES: tuple[str, ...] = IDENTITY_COLUMNS + (
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

_FITTED_JSON_OPTIONS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": True,
}


def open_forecasts_db(path: str) -> sqlite3.Connection:
    """Open (creating if needed) the forecasts DB at the caller path."""
    connection = sqlite3.connect(path)
    for statement in _DDL:
        connection.execute(statement)
    connection.commit()
    return connection


def open_read_connection(path: str) -> sqlite3.Connection:
    """A read connection: physically unable to write (PRAGMA query_only)."""
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA query_only = 1")
    return connection


def _identity_of(forecast: Forecast) -> tuple[str, ...]:
    return (
        forecast.competition,
        forecast.season,
        forecast.date,
        forecast.home,
        forecast.away,
        forecast.as_of,
        forecast.fitted.model_version,
        forecast.fitted.input_digest,
        config_identity(forecast.fitted.config),
        forecast.forecast_version,
    )


def _values_of(forecast: Forecast) -> tuple[Any, ...]:
    kickoff_value = (
        None
        if forecast.kickoff.availability is Availability.MISSING
        else forecast.kickoff.value
    )
    return _identity_of(forecast) + (
        kickoff_value,
        forecast.kickoff.availability.value,
        forecast.lambda_home,
        forecast.lambda_away,
        forecast.max_goals,
        forecast.dropped_mass,
        forecast.outcome_home,
        forecast.outcome_draw,
        forecast.outcome_away,
        json.dumps(fitted_payload(forecast.fitted), **_FITTED_JSON_OPTIONS),
        forecast.content_hash,
    )


def insert_forecast(connection: sqlite3.Connection, forecast: Forecast) -> bool:
    """Insert one forecast write-once; True = inserted, False = no-op.

    One INSERT per forecast inside a single BEGIN IMMEDIATE transaction
    that also contains the identity check, so check-then-insert is
    atomic against concurrent writers (S4). Identical identity +
    identical content hash is an idempotent no-op (zero INSERTs, no
    error — the dedup token is the content hash); identical identity +
    different content hash raises ForecastConflictError and never
    overwrites (the original row is untouched; the UNIQUE identity
    constraint is the schema-level backstop).
    """
    identity_where = " AND ".join(f"{column} = ?" for column in IDENTITY_COLUMNS)
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing = connection.execute(
            f"SELECT content_hash FROM forecasts WHERE {identity_where}",
            _identity_of(forecast),
        ).fetchone()
        if existing is not None:
            if existing[0] == forecast.content_hash:
                connection.commit()
                return False
            raise ForecastConflictError(
                f"identity collision with different content for fixture "
                f"{(forecast.competition, forecast.season, forecast.date, forecast.home, forecast.away)!r}: "
                f"stored {existing[0]}, incoming {forecast.content_hash}"
            )
        column_list = ", ".join(COLUMN_NAMES)
        placeholders = ", ".join("?" for _ in COLUMN_NAMES)
        connection.execute(
            f"INSERT INTO forecasts ({column_list}) VALUES ({placeholders})",
            _values_of(forecast),
        )
        connection.commit()
        return True
    except BaseException:
        connection.rollback()
        raise


def insert_evaluation_record(
    connection: sqlite3.Connection, record: EvaluationRecord
) -> bool:
    """Insert one evaluation write-once; True = inserted, False = no-op.

    The same transaction shape as insert_forecast: BEGIN IMMEDIATE,
    identity check, then one INSERT, so check-then-insert is atomic
    against concurrent writers (S4). Identical natural identity +
    identical content hash is an idempotent no-op (zero INSERTs, no
    error — the dedup token is the content hash); identical identity +
    different content hash raises EvaluationConflictError and never
    overwrites (the original row is untouched; the UNIQUE identity
    constraint is the schema-level backstop). The forecast rows are
    never touched from this function — one INSERT on a separate table
    only (criterion 18).
    """
    fixture_hash_text = json.dumps(
        record.fixture_file_sha256s, **_FITTED_JSON_OPTIONS
    )
    identity = (
        record.evaluation_version,
        record.run_digest,
        fixture_hash_text,
    )
    connection.execute("BEGIN IMMEDIATE")
    try:
        existing = connection.execute(
            "SELECT content_hash FROM evaluations "
            "WHERE evaluation_version = ? "
            "AND run_digest = ? AND fixture_file_sha256s = ?",
            identity,
        ).fetchone()
        if existing is not None:
            if existing[0] == record.content_hash:
                connection.commit()
                return False
            raise EvaluationConflictError(
                f"identity collision with different content for evaluation "
                f"{(record.evaluation_version, record.run_digest)!r}: "
                f"stored {existing[0]}, incoming {record.content_hash}"
            )
        connection.execute(
            "INSERT INTO evaluations (evaluation_version, run_digest, "
            "fixture_file_sha256s, payload, content_hash) "
            "VALUES (?, ?, ?, ?, ?)",
            identity + (record.payload, record.content_hash),
        )
        connection.commit()
        return True
    except BaseException:
        connection.rollback()
        raise


def _integrity_error(mapping: dict[str, Any]) -> ForecastIntegrityError:
    key = (
        mapping["competition"],
        mapping["season"],
        mapping["date"],
        mapping["home"],
        mapping["away"],
    )
    return ForecastIntegrityError(
        f"content hash mismatch for fixture {key!r}: stored "
        f"{mapping['content_hash']}, recomputed from stored fields"
    )


def _forecast_from_mapping(mapping: dict[str, Any]) -> Forecast:
    """Reconstruct a Forecast from stored fields alone.

    Construction recomputes content_hash under the canonicalization
    spec, so the caller compares it against the stored hash — nothing
    else verifies itself.
    """
    return Forecast(
        competition=mapping["competition"],
        season=mapping["season"],
        date=mapping["date"],
        home=mapping["home"],
        away=mapping["away"],
        kickoff=OptionalValue(
            value=mapping["kickoff_value"],
            availability=Availability(mapping["kickoff_availability"]),
        ),
        as_of=mapping["as_of"],
        fitted=fitted_from_payload(json.loads(mapping["fitted"])),
        lambda_home=mapping["lambda_home"],
        lambda_away=mapping["lambda_away"],
        max_goals=mapping["max_goals"],
        dropped_mass=mapping["dropped_mass"],
        outcome_home=mapping["outcome_home"],
        outcome_draw=mapping["outcome_draw"],
        outcome_away=mapping["outcome_away"],
        forecast_version=mapping["forecast_version"],
    )


def _verified_forecast_from_mapping(mapping: dict[str, Any]) -> Forecast:
    forecast = _forecast_from_mapping(mapping)
    if forecast.content_hash != mapping["content_hash"]:
        raise _integrity_error(mapping)
    return forecast


def get_forecast(
    connection: sqlite3.Connection,
    competition: str,
    season: str,
    date: str,
    home: str,
    away: str,
) -> Forecast | None:
    """One stored forecast by natural key, hash-verified, or None (404).

    The connection is put into PRAGMA query_only = 1 first — the read
    path is physically unable to write (criterion 13). The hash is
    recomputed from the stored fields and compared on EVERY returned
    row; any mismatch raises ForecastIntegrityError, never a warning,
    never partial data (criteria 10/11).
    """
    connection.execute("PRAGMA query_only = 1")
    cursor = connection.execute(
        "SELECT * FROM forecasts WHERE competition = ? AND season = ? "
        "AND date = ? AND home = ? AND away = ? "
        "ORDER BY as_of, input_digest",
        (competition, season, date, home, away),
    )
    columns = [description[0] for description in cursor.description]
    row = cursor.fetchone()
    if row is None:
        return None
    return _verified_forecast_from_mapping(dict(zip(columns, row)))


def verify_all(connection: sqlite3.Connection) -> tuple[Forecast, ...]:
    """Bulk recompute-and-compare over every row (Phase 9's friend).

    Deterministic order (canonical key), every row verified, the first
    mismatch raising ForecastIntegrityError.
    """
    connection.execute("PRAGMA query_only = 1")
    cursor = connection.execute(
        "SELECT * FROM forecasts ORDER BY competition, season, date, home, away"
    )
    columns = [description[0] for description in cursor.description]
    verified = []
    for row in cursor:
        verified.append(_verified_forecast_from_mapping(dict(zip(columns, row))))
    return tuple(verified)


def backup_forecasts(source_path: str, destination_path: str) -> None:
    """Consistent copy via sqlite3.Connection.backup — the only sanctioned
    mechanism (a consistent snapshot even under concurrent readers;
    shell-copying the file while a writer is active is not)."""
    source = sqlite3.connect(source_path)
    try:
        destination = sqlite3.connect(destination_path)
        try:
            source.backup(destination)
            destination.commit()
        finally:
            destination.close()
    finally:
        source.close()


__all__ = [
    "COLUMN_NAMES",
    "IDENTITY_COLUMNS",
    "IMMUTABLE_DELETE_TRIGGER_DDL",
    "IMMUTABLE_UPDATE_TRIGGER_DDL",
    "SCHEMA_VERSION",
    "backup_forecasts",
    "get_forecast",
    "insert_evaluation_record",
    "insert_forecast",
    "open_forecasts_db",
    "open_read_connection",
    "verify_all",
]
