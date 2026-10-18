"""Read-only API layer over stored forecast snapshots (stdlib http.server).

Two GET routes, localhost-only bind, store-then-serve: the API never
computes, generates, or mutates anything — it serves the durable
write-once snapshots of app.storage with full provenance and honesty
flags at top level. Zero third-party dependencies (developer decision,
2026-10-17: stdlib http.server over FastAPI).
"""

from .serialize import (
    DISCLAIMER,
    error_body,
    forecast_body,
    forecast_payload,
    health_body,
)
from .server import (
    ForecastHTTPServer,
    ForecastRequestHandler,
    create_server,
    decode_segment,
    looks_like_iso_date,
)

__all__ = [
    "DISCLAIMER",
    "ForecastHTTPServer",
    "ForecastRequestHandler",
    "create_server",
    "decode_segment",
    "error_body",
    "forecast_body",
    "forecast_payload",
    "health_body",
    "looks_like_iso_date",
]
