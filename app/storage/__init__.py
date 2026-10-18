"""Durable storage layer: the write-once sqlite backend for forecasts.

Instantiated in Phase 5 (the Phase 2 deferral, resolved): one sqlite
file, one schema version, schema-level immutability triggers, hash
verification on every read. Stdlib sqlite3 only — no ORM, no
migrations framework, no pooling, no services. The DB path is always
caller-passed.
"""

from .forecasts_db import (
    COLUMN_NAMES,
    IDENTITY_COLUMNS,
    IMMUTABLE_DELETE_TRIGGER_DDL,
    IMMUTABLE_UPDATE_TRIGGER_DDL,
    SCHEMA_VERSION,
    backup_forecasts,
    get_forecast,
    insert_forecast,
    open_forecasts_db,
    open_read_connection,
    verify_all,
)

__all__ = [
    "COLUMN_NAMES",
    "IDENTITY_COLUMNS",
    "IMMUTABLE_DELETE_TRIGGER_DDL",
    "IMMUTABLE_UPDATE_TRIGGER_DDL",
    "SCHEMA_VERSION",
    "backup_forecasts",
    "get_forecast",
    "insert_forecast",
    "open_forecasts_db",
    "open_read_connection",
    "verify_all",
]
