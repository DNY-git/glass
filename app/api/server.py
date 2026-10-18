"""Read-only HTTP surface over STORED forecast snapshots (stdlib only).

The whole serving posture: ``ThreadingHTTPServer`` from the standard
library bound to ``127.0.0.1`` (never 0.0.0.0), two GET routes —
``/health`` and ``/forecasts/{competition}/{season}/{date}/{home}/
{away}`` — and nothing else. Generation is NOT an HTTP verb: non-GET
methods on any path answer 405, and this package contains no
forecast-generation logic at all (store-then-serve: a compute-on-demand
endpoint would mint ephemeral forecasts Phase 11 could never score).
The no-auth posture holds only as a conjunction: localhost-only bind +
read-only methods + zero secrets in the system.

Path segments are percent-decoded by the small deterministic decoder
below (AMENDMENT A5 architect ruling 2026-10-17, recorded in
docs/briefs/phase-5.md: no urllib import anywhere under
app/ — urllib stays on the Phase 2 ban for every package; the decoder
also rejects invalid percent-escapes, which a permissive unquote never
could — malformed input is a 400, never a guess). Bodies are the
byte-deterministic JSON of ``app.api.serialize``; timestamps exist only
in HTTP ``Date`` headers, never in bodies (S2). One read connection
per request (PRAGMA query_only via the storage layer); the DB path is
a caller-passed argument — never an environment lookup.
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from app.forecasts import ForecastIntegrityError
from app.storage import get_forecast, open_read_connection

from .serialize import error_body, forecast_body, health_body

_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def decode_segment(segment: str) -> str:
    """Percent-decode one path segment; invalid encoding raises ValueError.

    ``%XX`` escapes become their raw byte; every other character is
    its UTF-8 bytes; the result must decode as UTF-8. A ``%`` not
    followed by two hex digits is malformed input — a ValueError the
    caller maps to 400, never a silently passed-through guess.
    """
    data = bytearray()
    index = 0
    length = len(segment)
    while index < length:
        char = segment[index]
        if char == "%":
            digits = segment[index + 1 : index + 3]
            if len(digits) < 2 or digits[0] not in _HEX_DIGITS or digits[1] not in _HEX_DIGITS:
                raise ValueError(f"invalid percent-escape in segment {segment!r}")
            data.append(int(digits, 16))
            index += 3
        else:
            data.extend(char.encode("utf-8"))
            index += 1
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"segment {segment!r} is not valid UTF-8") from error


def looks_like_iso_date(value: str) -> bool:
    """Day-granularity ISO shape check (no datetime module needed)."""
    return (
        len(value) == 10
        and value[0:4].isdigit()
        and value[4] == "-"
        and value[5:7].isdigit()
        and value[7] == "-"
        and value[8:10].isdigit()
    )


class ForecastHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer carrying the caller-passed store path."""

    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        db_path: str,
    ) -> None:
        super().__init__(server_address, handler_class)
        self.db_path = db_path


class ForecastRequestHandler(BaseHTTPRequestHandler):
    """The thin router: percent-decoding, route table, 404/400/405.

    All logic lives in app.forecasts/app.storage; this class only
    routes and writes bytes (HANDOFF Part IV: routers stay thin).
    """

    server: ForecastHTTPServer  # narrowed annotation; set by the server

    def do_GET(self) -> None:
        raw_path = self.path.split("?", 1)[0]
        if raw_path == "/health":
            self._send(200, health_body())
            return
        segments = raw_path.split("/")
        if segments[1:2] == ["forecasts"]:
            if len(segments) != 7:
                self._send(400, error_body("bad_request"))
                return
            self._serve_forecast(segments[2:])
            return
        self._send(404, error_body("not_found"))

    def do_POST(self) -> None:
        self._method_not_allowed()

    def do_PUT(self) -> None:
        self._method_not_allowed()

    def do_DELETE(self) -> None:
        self._method_not_allowed()

    def _serve_forecast(self, parts: list[str]) -> None:
        try:
            competition, season, date, home, away = (
                decode_segment(part) for part in parts
            )
        except ValueError:
            self._send(400, error_body("bad_request"))
            return
        if not looks_like_iso_date(date):
            self._send(400, error_body("bad_request"))
            return
        connection = open_read_connection(self.server.db_path)
        try:
            try:
                forecast = get_forecast(
                    connection, competition, season, date, home, away
                )
            except ForecastIntegrityError:
                self._send(500, error_body("integrity_error"))
                return
        finally:
            connection.close()
        if forecast is None:
            self._send(404, error_body("unknown_fixture"))
            return
        self._send(200, forecast_body(forecast))

    def _method_not_allowed(self) -> None:
        self._send(405, error_body("method_not_allowed"), (("Allow", "GET"),))

    def _send(
        self,
        status: int,
        body: bytes,
        headers: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def create_server(
    db_path: str, host: str = "127.0.0.1", port: int = 0
) -> ForecastHTTPServer:
    """A server over the caller-passed store; port 0 = ephemeral (tests).

    Localhost-only bind is the default and the tested posture; the
    server object is a context manager (``with server:``) and shuts
    down deterministically with ``server.shutdown()`` + thread join.
    """
    return ForecastHTTPServer((host, port), ForecastRequestHandler, db_path)


__all__ = [
    "ForecastHTTPServer",
    "ForecastRequestHandler",
    "create_server",
    "decode_segment",
    "looks_like_iso_date",
]
