"""Deterministic serialization of stored forecasts for the read-only API.

Every body is byte-deterministic JSON (``json.dumps(..., sort_keys=True,
separators=(",", ":"))`` encoded UTF-8, full-precision floats, no
timestamp anywhere in any body — S2), so two GETs of the same row
produce byte-identical bodies. The forecast payload carries, at TOP
LEVEL and never buried: the four honesty flags (convergence_status,
insufficient_data, insufficient_teams, dropped_mass — a flagged
forecast screams, never a silent plausible 200), the full provenance
echo (as_of, model_version, input_digest, forecast_version,
content_hash), the natural key, the kickoff block with its availability
(MISSING stays MISSING, never a default time), the matrix essentials,
the analytic outcome probabilities, and the fixed honest
``disclaimer`` companion field. Field names say estimate/probability;
the A2-banned flavor words never appear as names anywhere. No
uncertainty field exists anywhere (dropped_mass is truncation
disclosure, not an uncertainty band).
"""

from __future__ import annotations

import json
from typing import Any

from app.forecasts import Forecast

# The honest companion field (H1): a fixed deterministic string. It
# names what the numbers are (in-sample analytic estimates pending
# chronological evaluation) and what they are not (evidence of
# accuracy). Deliberately free of banned betting-surface words.
DISCLAIMER = (
    "In-sample analytic estimate from the fitted model; pending "
    "chronological evaluation against realized results (Phases 9 and "
    "11). Not evidence of accuracy."
)

_JSON_OPTIONS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
}


def forecast_payload(forecast: Forecast) -> dict[str, Any]:
    """One stored forecast as a flat response dict (max one level deep)."""
    return {
        "as_of": forecast.as_of,
        "away": forecast.away,
        "competition": forecast.competition,
        "content_hash": forecast.content_hash,
        "convergence_status": forecast.fitted.convergence_status.value,
        "date": forecast.date,
        "disclaimer": DISCLAIMER,
        "dropped_mass": forecast.dropped_mass,
        "forecast_version": forecast.forecast_version,
        "home": forecast.home,
        "input_digest": forecast.fitted.input_digest,
        "insufficient_data": forecast.fitted.insufficient_data,
        "insufficient_teams": list(forecast.fitted.insufficient_teams),
        "kickoff": {
            "availability": forecast.kickoff.availability.value,
            "time": forecast.kickoff.value,
        },
        "lambda_away": forecast.lambda_away,
        "lambda_home": forecast.lambda_home,
        "max_goals": forecast.max_goals,
        "model_version": forecast.fitted.model_version,
        "outcome_probs": {
            "away": forecast.outcome_away,
            "draw": forecast.outcome_draw,
            "home": forecast.outcome_home,
        },
        "season": forecast.season,
    }


def forecast_body(forecast: Forecast) -> bytes:
    """The byte-deterministic JSON body of one stored forecast."""
    return json.dumps(forecast_payload(forecast), **_JSON_OPTIONS).encode("utf-8")


def error_body(error: str) -> bytes:
    """The explicit JSON error body (never a fabricated forecast, A3)."""
    return json.dumps({"error": error}, **_JSON_OPTIONS).encode("utf-8")


def health_body() -> bytes:
    """The deterministic health body."""
    return json.dumps({"status": "ok"}, **_JSON_OPTIONS).encode("utf-8")


__all__ = [
    "DISCLAIMER",
    "error_body",
    "forecast_body",
    "forecast_payload",
    "health_body",
]
