"""The canonicalization spec of record for decision-report content hashes.

This module IS the written spec (STATISTICAL-ASSUMPTIONS section 10a,
Phase 7 brief decision 4): ``content_hash(r)`` is defined to be
``sha256(utf-8 bytes of canonical_payload(r))`` where the canonical
payload is built from exactly the ``DecisionReport`` field set minus
``content_hash`` itself, under these fixed rules:

* keys sorted lexicographically (``json.dumps(..., sort_keys=True)``);
* fixed separators ``(",", ":")``, ``ensure_ascii=True``, no trailing
  newline;
* strings as-is; ints decimal; **floats via Python's shortest
  round-trip repr — full precision, no rounding ever**; bools as JSON
  ``true``/``false``; enums as their ``.value`` strings
  (``convergence_status``, kickoff ``availability``, transform ``op``);
  tuples as JSON arrays in order; ``None`` as JSON ``null``;
* nested frozen records as nested canonical objects under the fixed key
  names below: ``ScenarioComparison`` (keys ``delta_*``, ``label``,
  ``outcome_*``, ``transforms``), ``ScenarioSpread`` (keys ``maximum``,
  ``minimum``, ``outcome``, ``spread``), each ``Transform`` (keys
  ``multiplier``, ``op``, ``team``), ``OptionalValue`` under ``kickoff``
  (keys ``availability``/``value``);
* **no timestamp, no filesystem path, no environment value, no seed,
  and no Monte Carlo quantity may appear in the hashed payload.**

This is the package's OWN spec of record: no import crosses the stage
boundary (``app/forecasts/canonicalization.py`` is never touched by,
nor imported into, this package). ``REPORT_VERSION`` is part of the
hashed content; any change to the hashed field set, this spec, or the
derivation semantics requires a ``REPORT_VERSION`` bump. Reports are
never stored, so there is no read path: a hash mismatch simply cannot
be persisted — re-deriving the view re-derives the hash.
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # annotation-only; no runtime cycle with .record
    from .record import DecisionReport, ScenarioComparison, ScenarioSpread

# The one fixed JSON shape used everywhere in this module.
_JSON_OPTIONS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": True,
}


def _kickoff_payload(report: DecisionReport) -> dict[str, Any]:
    return {
        "availability": report.kickoff.availability.value,
        "value": report.kickoff.value,
    }


def _transform_payload(transform: Any) -> dict[str, Any]:
    return {
        "multiplier": transform.multiplier,
        "op": transform.op.value,
        "team": transform.team,
    }


def _comparison_payload(comparison: ScenarioComparison) -> dict[str, Any]:
    return {
        "delta_away": comparison.delta_away,
        "delta_draw": comparison.delta_draw,
        "delta_home": comparison.delta_home,
        "label": comparison.label,
        "outcome_away": comparison.outcome_away,
        "outcome_draw": comparison.outcome_draw,
        "outcome_home": comparison.outcome_home,
        "transforms": [_transform_payload(t) for t in comparison.transforms],
    }


def _spread_payload(spread: ScenarioSpread) -> dict[str, Any]:
    return {
        "maximum": spread.maximum,
        "minimum": spread.minimum,
        "outcome": spread.outcome,
        "spread": spread.spread,
    }


def _payload_object(report: DecisionReport) -> dict[str, Any]:
    """Exactly the D field set minus ``content_hash`` — nothing else."""
    return {
        "as_of": report.as_of,
        "away": report.away,
        "competition": report.competition,
        "convergence_status": report.convergence_status.value,
        "date": report.date,
        "disclaimer": report.disclaimer,
        "dropped_mass": report.dropped_mass,
        "forecast_content_hash": report.forecast_content_hash,
        "forecast_version": report.forecast_version,
        "home": report.home,
        "insufficient_data": report.insufficient_data,
        "insufficient_teams": list(report.insufficient_teams),
        "input_digest": report.input_digest,
        "kickoff": _kickoff_payload(report),
        "lambda_away": report.lambda_away,
        "lambda_home": report.lambda_home,
        "max_goals": report.max_goals,
        "model_version": report.model_version,
        "outcome_away": report.outcome_away,
        "outcome_draw": report.outcome_draw,
        "outcome_home": report.outcome_home,
        "report_version": report.report_version,
        "sample_goals": report.sample_goals,
        "sample_matches": report.sample_matches,
        "scenario_comparisons": [
            _comparison_payload(comparison)
            for comparison in report.scenario_comparisons
        ],
        "scenario_spread": (
            None
            if report.scenario_spread is None
            else [_spread_payload(entry) for entry in report.scenario_spread]
        ),
        "season": report.season,
    }


def canonical_payload(report: DecisionReport) -> str:
    """The canonical JSON string of a report's hashed content."""
    return json.dumps(_payload_object(report), **_JSON_OPTIONS)


def content_hash(report: DecisionReport) -> str:
    """sha256 hex digest of the canonical payload (the D-hash contract)."""
    return hashlib.sha256(canonical_payload(report).encode("utf-8")).hexdigest()


__all__ = ["canonical_payload", "content_hash"]
