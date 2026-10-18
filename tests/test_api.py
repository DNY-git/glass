"""Phase 5 acceptance criteria 16-21: the read-only HTTP surface.

Minimal GET-only surface on 127.0.0.1 with ephemeral ports and
context-managed server threads (16), top-level provenance echo + flags
+ disclaimer with no nesting deeper than one key (17), byte-deterministic
full-precision bodies (18), 404/400 semantics with no fabricated
defaults (19), no timestamps and no betting-surface tokens in any body
(20), and store-then-serve: the API serves the stored snapshot only
(21). No skips, no xfails, tmp_path DBs exclusively.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import re
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.api import DISCLAIMER, ForecastHTTPServer, create_server, forecast_body, forecast_payload
from app.domain import Fixture, MatchCollection, OptionalValue
from app.forecasts import build_forecast
from app.ingestion import import_fixture
from app.storage import get_forecast, insert_forecast, open_forecasts_db, open_read_connection
from test_phase5_separation import BANNED_BETTING_TOKENS

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

ALL_MATCHES: tuple
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

STORED_FIXTURE = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Coralgate Athletic",
    away="Thistledown Wanderers",
    kickoff=OptionalValue.missing(),
)
FLAGGED_FIXTURE = Fixture(  # the Phase 3 measured SINGULAR_SYSTEM case
    competition="Obsidian Coast League",
    season="2025-26",
    date="2024-08-17",
    home="Coralgate Athletic",
    away="Harbourlight Comets",
    kickoff=OptionalValue.missing(),
)
BUILDABLE_UNSORTED_FIXTURE = Fixture(  # buildable but never stored (21)
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Quarryhill Zenith",
    away="Silverpine Rovers",
    kickoff=OptionalValue.missing(),
)

FORECAST_PATH = (
    "/forecasts/Obsidian%20Coast%20League/2025-26/2025-12-31/"
    "Coralgate%20Athletic/Thistledown%20Wanderers"
)

# The exact top-level key set of a forecast response (criterion 17:
# key-path pinned; no nesting deeper than one key).
PINNED_RESPONSE_KEYS = {
    "as_of",
    "away",
    "competition",
    "content_hash",
    "convergence_status",
    "date",
    "disclaimer",
    "dropped_mass",
    "forecast_version",
    "home",
    "input_digest",
    "insufficient_data",
    "insufficient_teams",
    "kickoff",
    "lambda_away",
    "lambda_home",
    "max_goals",
    "model_version",
    "outcome_probs",
    "season",
}


def _stored_db(path: Path) -> Path:
    """A tmp_path store holding the stored and flagged forecasts."""
    db = path / "forecasts.db"
    connection = open_forecasts_db(str(db))
    for fixture in (STORED_FIXTURE, FLAGGED_FIXTURE):
        assert insert_forecast(connection, build_forecast(ALL_MATCHES, fixture))
    connection.close()
    return db


@contextlib.contextmanager
def running_server(db_path: Path) -> Iterator[ForecastHTTPServer]:
    """Ephemeral-port server on 127.0.0.1; deterministic teardown, no sleeps."""
    server = create_server(str(db_path))
    assert server.server_address[0] == "127.0.0.1"
    thread = threading.Thread(target=server.serve_forever)
    with server:
        thread.start()
        try:
            yield server  # type: ignore[misc]
        finally:
            server.shutdown()
            thread.join()


def request(
    server: ForecastHTTPServer, method: str, path: str
) -> tuple[int, dict[str, str], bytes]:
    port = server.server_address[1]
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    try:
        connection.request(method, path)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def test_minimal_surface_get_only_and_localhost_bind(tmp_path: Path) -> None:
    # Criterion 16 (A1): GET-only two-route surface bound to 127.0.0.1
    # on an ephemeral port; generation is not an HTTP verb: POST, PUT
    # and DELETE on BOTH routes answer 405; unknown paths answer 404.
    db = _stored_db(tmp_path)
    with running_server(db) as server:
        assert server.server_address[0] == "127.0.0.1"  # never 0.0.0.0
        assert server.server_address[1] != 0  # ephemeral port was bound

        status, _, body = request(server, "GET", "/health")
        assert status == 200
        assert json.loads(body) == {"status": "ok"}

        status, _, body = request(server, "GET", FORECAST_PATH)
        assert status == 200
        assert json.loads(body)["home"] == "Coralgate Athletic"

        for method in ("POST", "PUT", "DELETE"):
            for path in ("/health", FORECAST_PATH):
                status, headers, _ = request(server, method, path)
                assert status == 405, (method, path)
                assert headers.get("Allow") == "GET"

        status, _, body = request(server, "GET", "/unknown")
        assert status == 404
        assert json.loads(body) == {"error": "not_found"}


def test_forecast_response_provenance_echo_flags_top_level_and_disclaimer(
    tmp_path: Path,
) -> None:
    # Criterion 17 (A3/H1): full provenance echo, the four honesty
    # flags, the fixture block incl. kickoff availability, the analytic
    # outcome_probs, and the disclaimer — ALL at top level (key set
    # pinned; nothing deeper than one key); no field name carries a
    # banned flavor word; and a stored SINGULAR_SYSTEM forecast serves
    # with its flags screaming at the top, never a silent plausible 200.
    db = _stored_db(tmp_path)
    with running_server(db) as server:
        status, _, body = request(server, "GET", FORECAST_PATH)
        assert status == 200
        payload = json.loads(body)

        assert set(payload) == PINNED_RESPONSE_KEYS
        forecast = build_forecast(ALL_MATCHES, STORED_FIXTURE)
        assert payload["as_of"] == forecast.as_of == STORED_FIXTURE.date
        assert payload["model_version"] == forecast.fitted.model_version
        assert payload["input_digest"] == forecast.fitted.input_digest
        assert payload["forecast_version"] == forecast.forecast_version
        assert payload["content_hash"] == forecast.content_hash
        assert payload["convergence_status"] == "CONVERGED"
        assert payload["insufficient_data"] is False
        assert payload["insufficient_teams"] == []
        assert payload["dropped_mass"] == forecast.dropped_mass
        assert payload["kickoff"] == {"availability": "MISSING", "time": None}
        assert set(payload["outcome_probs"]) == {"home", "draw", "away"}
        assert payload["outcome_probs"]["home"] == forecast.outcome_home
        assert isinstance(payload["disclaimer"], str) and payload["disclaimer"]
        assert "in-sample" in payload["disclaimer"].lower()
        assert "pending" in payload["disclaimer"].lower()

        # Nothing deeper than one key: every value is a scalar, or a
        # flat dict of scalars (or a list of scalars for teams).
        for value in payload.values():
            if isinstance(value, dict):
                for nested in value.values():
                    assert not isinstance(nested, (dict, list))
            elif isinstance(value, list):
                for item in value:
                    assert not isinstance(item, (dict, list))

        # No field name contains a banned flavor word (word-boundary:
        # "insufficient" must not trip a bare "ci" substring check).
        flavor_tokens = ("confidence", "ci", "stderr", "edge", "kelly", "value")
        def keys_of(value: object) -> list[str]:
            if isinstance(value, dict):
                return list(value) + [k for v in value.values() for k in keys_of(v)]
            return []
        for key in keys_of(payload):
            for token in flavor_tokens:
                assert not re.search(rf"\b{token}\b", key.lower()), key

        # A stored SINGULAR_SYSTEM forecast: flags at top level.
        flagged_path = (
            "/forecasts/Obsidian%20Coast%20League/2025-26/2024-08-17/"
            "Coralgate%20Athletic/Harbourlight%20Comets"
        )
        status, _, flagged_body = request(server, "GET", flagged_path)
        assert status == 200
        flagged = json.loads(flagged_body)
        assert flagged["convergence_status"] == "SINGULAR_SYSTEM"
        assert flagged["insufficient_data"] is True
        assert flagged["insufficient_teams"]  # every team below threshold
        assert set(flagged) == PINNED_RESPONSE_KEYS  # same pinned shape


def test_response_json_byte_deterministic_and_full_precision(tmp_path: Path) -> None:
    # Criterion 18 (S3/A3): two GETs of the same row return
    # byte-identical bodies; floats round-trip to exactly the stored
    # values (full-precision repr, no rounding); the body parses with
    # no float drift.
    db = _stored_db(tmp_path)
    with running_server(db) as server:
        first = request(server, "GET", FORECAST_PATH)
        second = request(server, "GET", FORECAST_PATH)
        assert first[2] == second[2]  # raw bytes, identical
        assert first[0] == second[0] == 200

        payload = json.loads(first[2])
        forecast = build_forecast(ALL_MATCHES, STORED_FIXTURE)
        assert payload["lambda_home"] == forecast.lambda_home
        assert payload["lambda_away"] == forecast.lambda_away
        assert payload["dropped_mass"] == forecast.dropped_mass
        assert payload["outcome_probs"]["home"] == forecast.outcome_home
        assert payload["outcome_probs"]["draw"] == forecast.outcome_draw
        assert payload["outcome_probs"]["away"] == forecast.outcome_away

        # Byte-for-byte with the store's own serialization of the
        # record read directly from the store (no drift anywhere).
        reader = open_read_connection(str(db))
        stored = get_forecast(
            reader, "Obsidian Coast League", "2025-26", "2025-12-31",
            "Coralgate Athletic", "Thistledown Wanderers",
        )
        assert stored is not None
        assert first[2] == forecast_body(stored)
        assert payload == forecast_payload(stored)
        reader.close()


def test_unknown_404_malformed_400_no_defaults(tmp_path: Path) -> None:
    # Criterion 19 (A3): an unstored-but-well-formed fixture key is a
    # 404 with the pinned explicit JSON error name; a malformed date
    # and an invalid percent-escape are 400s; neither error body ever
    # looks like a forecast or carries a fabricated default.
    db = _stored_db(tmp_path)
    with running_server(db) as server:
        status, _, body = request(
            server, "GET", "/forecasts/Obsidian%20Coast%20League/2025-26/2025-12-31/Northwind%20Pharos/Coralgate%20Athletic"
        )
        assert status == 404
        assert json.loads(body) == {"error": "unknown_fixture"}

        for malformed in (
            "/forecasts/Obsidian%20Coast%20League/2025-26/2024-8-1/Coralgate%20Athletic/Thistledown%20Wanderers",
            "/forecasts/Obsidian%20Coast%20League/2025-26/not-a-date/Coralgate%20Athletic/Thistledown%20Wanderers",
            "/forecasts/Obsidian%20Coast%20League/2025-26/2025-12-31/Coralgate%2/Thistledown%20Wanderers",
            "/forecasts/Obsidian%20Coast%20League/2025-26/2025-12-31/%zz/Thistledown%20Wanderers",
            "/forecasts/Obsidian%20Coast%20League/2025-26/2025-12-31/Coralgate%20Athletic/%E0%A4%A",
        ):
            status, _, body = request(server, "GET", malformed)
            assert status == 400, malformed
            error_payload = json.loads(body)
            assert set(error_payload) == {"error"}
            assert error_payload["error"] == "bad_request"
            assert "outcome_probs" not in body.decode("utf-8")
            assert "content_hash" not in body.decode("utf-8")


def test_no_timestamps_and_no_betting_tokens_in_any_body(tmp_path: Path) -> None:
    # Criterion 20 (S2/A2): no key or string value in /health or the
    # forecast body resembles a timestamp/date-time (the HTTP Date
    # HEADER is allowed and is not part of the body), and no key or
    # value carries any betting-surface token from the shared banned
    # list (word-boundary, single source of truth in the separation
    # test).
    db = _stored_db(tmp_path)
    timestamp_pattern = re.compile(
        r"\d{4}-\d\d-\d\dT|\d{2}:\d{2}:\d{2}|\b\d{2}:\d{2}\b|\b1[0-9]{9}\b"
    )
    betting_pattern = re.compile(
        r"\b(" + "|".join(map(re.escape, BANNED_BETTING_TOKENS)) + r")\b",
        re.IGNORECASE,
    )
    with running_server(db) as server:
        bodies = [
            request(server, "GET", "/health")[2],
            request(server, "GET", FORECAST_PATH)[2],
        ]
    for body in bodies:
        payload = json.loads(body)
        for key, value in _walk(payload):
            assert not timestamp_pattern.search(key), key
            assert not betting_pattern.search(key), key
            if isinstance(value, str):
                assert not timestamp_pattern.search(value), value
                assert not betting_pattern.search(value), value


def test_api_serves_stored_snapshot_only(tmp_path: Path) -> None:
    # Criterion 21 (A1 store-then-serve): a fixture that is buildable
    # but NOT stored answers 404 — proof the server never computes —
    # and a stored 200 body equals the serialization of the stored
    # record read directly from the store: the API adds nothing,
    # rounds nothing, derives nothing.
    db = _stored_db(tmp_path)
    buildable = build_forecast(ALL_MATCHES, BUILDABLE_UNSORTED_FIXTURE)  # it exists
    assert buildable.content_hash
    with running_server(db) as server:
        status, _, body = request(
            server, "GET", "/forecasts/Obsidian%20Coast%20League/2025-26/2025-12-31/Quarryhill%20Zenith/Silverpine%20Rovers"
        )
        assert status == 404
        assert json.loads(body) == {"error": "unknown_fixture"}

        status, _, served = request(server, "GET", FORECAST_PATH)
        assert status == 200
        reader = open_read_connection(str(db))
        stored = get_forecast(
            reader, "Obsidian Coast League", "2025-26", "2025-12-31",
            "Coralgate Athletic", "Thistledown Wanderers",
        )
        assert stored is not None
        assert served == forecast_body(stored)  # key-for-key, float-for-float
        reader.close()
    assert DISCLAIMER  # the honesty companion ships with every body


def _walk(value: object, prefix: str = "") -> Iterator[tuple[str, object]]:
    if isinstance(value, dict):
        for key, nested in value.items():
            yield prefix + str(key), nested
            yield from _walk(nested, prefix + str(key) + ".")
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item, prefix)
