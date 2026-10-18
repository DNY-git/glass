"""The canonicalization spec of record for forecast content hashes.

This module IS the written spec (STATISTICAL-ASSUMPTIONS section 8c,
Phase 5 brief decision 5): ``content_hash(f)`` is defined to be
``sha256(utf-8 bytes of canonical_payload(f))`` where the canonical
payload is built from exactly the ``Forecast`` field set minus
``content_hash`` itself, under these fixed rules:

* keys sorted lexicographically (``json.dumps(..., sort_keys=True)``);
* fixed separators ``(",", ":")``, ``ensure_ascii=True``, no trailing
  newline;
* strings as-is; ints decimal; **floats via Python's shortest
  round-trip repr — full precision, no rounding ever**; bools as JSON
  ``true``/``false``; enums as their ``.value`` strings
  (``convergence_status``, kickoff ``availability``); tuples as JSON
  arrays in order; ``None`` as JSON ``null``;
* nested frozen objects as nested canonical objects under the fixed
  key names below: ``FitConfig`` under ``config``, ``PoolingRecord``
  under ``pooling``, ``SampleSize`` under ``sample_size``,
  ``OptionalValue`` under ``kickoff`` (keys ``availability``/``value``);
* **no timestamp, no filesystem path, no environment value, no seed,
  and no Monte Carlo quantity may appear in the hashed payload**
  (AST-enforced, criterion 24).

``FORECAST_VERSION`` is part of the hashed content; any change to the
hashed field set, this spec, or the derivation semantics requires a
``FORECAST_VERSION`` bump. A hash mismatch is a hard error, never a
warning; the read path recomputes from stored fields alone and compares
on every row it returns.

``fitted_payload``/``fitted_from_payload`` are the ONE mapping between
``FittedParams`` and its canonical nested object; ``app.storage`` stores
that exact object verbatim, so a stored row re-serializes to the very
bytes that were hashed. Reconstruction is the same spec read backwards.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from app.models import (
    ConvergenceStatus,
    FitConfig,
    FittedParams,
    PoolingRecord,
    SampleSize,
)

if TYPE_CHECKING:  # annotation-only; no runtime cycle with .record
    from .record import Forecast

# The one fixed JSON shape used everywhere in this module.
_JSON_OPTIONS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": True,
}


def config_identity(config: FitConfig) -> str:
    """Canonical serialization of a FitConfig — the identity component.

    Brief decision 6: forecast identity includes ``config`` as the
    canonical serialization of the FitConfig fields, so two fits under
    different effective configurations are different identities.
    """
    return json.dumps(_config_payload(config), **_JSON_OPTIONS)


def _config_payload(config: FitConfig) -> dict[str, Any]:
    return {
        "damping": config.damping,
        "max_goals": config.max_goals,
        "max_iterations": config.max_iterations,
        "newton_tol": config.newton_tol,
        "ridge": config.ridge,
    }


def _sample_size_payload(sample_size: SampleSize) -> dict[str, Any]:
    return {"goals": sample_size.goals, "matches": sample_size.matches}


def _pooling_payload(pooling: PoolingRecord) -> dict[str, Any]:
    return {
        "as_of": pooling.as_of,
        "competition": pooling.competition,
        "sample_size": _sample_size_payload(pooling.sample_size),
        "seasons": list(pooling.seasons),
    }


def fitted_payload(fitted: FittedParams) -> dict[str, Any]:
    """The canonical nested ``fitted`` object (fixed key names)."""
    return {
        "alpha": list(fitted.alpha),
        "beta": list(fitted.beta),
        "config": _config_payload(fitted.config),
        "convergence_status": fitted.convergence_status.value,
        "home_advantage": fitted.home_advantage,
        "input_digest": fitted.input_digest,
        "insufficient_data": fitted.insufficient_data,
        "insufficient_teams": list(fitted.insufficient_teams),
        "iterations": fitted.iterations,
        "model_version": fitted.model_version,
        "mu": fitted.mu,
        "pooling": _pooling_payload(fitted.pooling),
        "sample_size": _sample_size_payload(fitted.sample_size),
        "teams": list(fitted.teams),
    }


def fitted_from_payload(payload: dict[str, Any]) -> FittedParams:
    """Rebuild a ``FittedParams`` from its canonical nested object.

    The exact inverse of ``fitted_payload`` under this spec: floats come
    back bit-identical (JSON floats round-trip via Python's exact
    repr), tuples are restored from arrays, and the enum from its
    ``.value`` string. This is how a stored row's ``FittedParams`` is
    reconstructed for hash recomputation — nothing is re-fitted,
    nothing is re-derived.
    """
    config_payload = payload["config"]
    pooling_payload = payload["pooling"]
    sample_payload = payload["sample_size"]
    pooling_sample_payload = pooling_payload["sample_size"]
    return FittedParams(
        model_version=payload["model_version"],
        config=FitConfig(
            newton_tol=config_payload["newton_tol"],
            max_iterations=config_payload["max_iterations"],
            damping=config_payload["damping"],
            max_goals=config_payload["max_goals"],
            ridge=config_payload["ridge"],
        ),
        pooling=PoolingRecord(
            competition=pooling_payload["competition"],
            seasons=tuple(pooling_payload["seasons"]),
            as_of=pooling_payload["as_of"],
            sample_size=SampleSize(
                matches=pooling_sample_payload["matches"],
                goals=pooling_sample_payload["goals"],
            ),
        ),
        input_digest=payload["input_digest"],
        teams=tuple(payload["teams"]),
        mu=payload["mu"],
        home_advantage=payload["home_advantage"],
        alpha=tuple(payload["alpha"]),
        beta=tuple(payload["beta"]),
        iterations=payload["iterations"],
        convergence_status=ConvergenceStatus(payload["convergence_status"]),
        sample_size=SampleSize(
            matches=sample_payload["matches"], goals=sample_payload["goals"]
        ),
        insufficient_data=payload["insufficient_data"],
        insufficient_teams=tuple(payload["insufficient_teams"]),
    )


def _kickoff_payload(forecast: Forecast) -> dict[str, Any]:
    return {
        "availability": forecast.kickoff.availability.value,
        "value": forecast.kickoff.value,
    }


def _payload_object(forecast: Forecast) -> dict[str, Any]:
    """Exactly the F2 field set minus ``content_hash`` — nothing else."""
    return {
        "as_of": forecast.as_of,
        "away": forecast.away,
        "competition": forecast.competition,
        "date": forecast.date,
        "dropped_mass": forecast.dropped_mass,
        "fitted": fitted_payload(forecast.fitted),
        "forecast_version": forecast.forecast_version,
        "home": forecast.home,
        "kickoff": _kickoff_payload(forecast),
        "lambda_away": forecast.lambda_away,
        "lambda_home": forecast.lambda_home,
        "max_goals": forecast.max_goals,
        "outcome_away": forecast.outcome_away,
        "outcome_draw": forecast.outcome_draw,
        "outcome_home": forecast.outcome_home,
        "season": forecast.season,
    }


def canonical_payload(forecast: Forecast) -> str:
    """The canonical JSON string of a forecast's hashed content."""
    return json.dumps(_payload_object(forecast), **_JSON_OPTIONS)


def content_hash(forecast: Forecast) -> str:
    """sha256 hex digest of the canonical payload (the F3 contract)."""
    return hashlib.sha256(canonical_payload(forecast).encode("utf-8")).hexdigest()


__all__ = [
    "canonical_payload",
    "config_identity",
    "content_hash",
    "fitted_from_payload",
    "fitted_payload",
]
