"""The canonicalization spec of record for feature-vector content hashes.

This module IS the written spec (STATISTICAL-ASSUMPTIONS section 9b,
Phase 6 brief decision 4/F3): ``content_hash(v)`` is defined to be
``sha256(utf-8 bytes of canonical_payload(v))`` where the canonical
payload is built from exactly the ``FeatureVector`` field set minus
``content_hash`` itself, under these fixed rules:

* keys sorted lexicographically (``json.dumps(..., sort_keys=True)``);
* fixed separators ``(",", ":")``, ``ensure_ascii=True``, no trailing
  newline;
* strings as-is; ints decimal; **floats via Python's shortest
  round-trip repr — full precision, no rounding ever**; ``None`` as
  JSON ``null``; enums as their ``.value`` strings (kickoff
  ``availability``); tuples as JSON arrays in order;
* nested frozen objects as nested canonical objects under the fixed
  key names: ``OptionalValue`` under its own field name with the keys
  ``availability``/``value``;
* **no timestamp, no filesystem path, no environment value, no seed,
  and no random quantity may appear in the hashed payload** (pinned by
  criterion 14).

``FEATURE_VERSION`` is part of the hashed content; any change to the
hashed field set, this spec, or the derivation semantics requires a
``FEATURE_VERSION`` bump — worded identically to ``FORECAST_VERSION``'s
(section 9b, F7). The stored value is recomputed from the record's own
fields alone (criterion 14) — tamper evidence, never a warning path.

Own module: no import crosses the stage boundary — this package never
imports ``app.forecasts`` (or anything but the stdlib and
``app.domain``), and ``app/forecasts/canonicalization.py`` is
untouched (F3/F4).
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from app.domain import OptionalValue

if TYPE_CHECKING:  # annotation-only; no runtime cycle with .record
    from .record import FeatureVector


def _optional_value_payload(value: OptionalValue) -> dict[str, Any]:
    """Canonical nested object of an OptionalValue (keys fixed)."""
    return {"availability": value.availability.value, "value": value.value}


def _payload_object(vector: FeatureVector) -> dict[str, Any]:
    """Exactly the decision-4 field set minus ``content_hash`` — nothing else."""
    return {
        "as_of": vector.as_of,
        "away": vector.away,
        "away_goals_conceded_form": _optional_value_payload(
            vector.away_goals_conceded_form
        ),
        "away_goals_scored_form": _optional_value_payload(
            vector.away_goals_scored_form
        ),
        "away_prior_matches": vector.away_prior_matches,
        "away_rest_days": _optional_value_payload(vector.away_rest_days),
        "away_xg_form": _optional_value_payload(vector.away_xg_form),
        "away_xg_n": vector.away_xg_n,
        "competition": vector.competition,
        "date": vector.date,
        "feature_version": vector.feature_version,
        "home": vector.home,
        "home_goals_conceded_form": _optional_value_payload(
            vector.home_goals_conceded_form
        ),
        "home_goals_scored_form": _optional_value_payload(
            vector.home_goals_scored_form
        ),
        "home_prior_matches": vector.home_prior_matches,
        "home_rest_days": _optional_value_payload(vector.home_rest_days),
        "home_xg_form": _optional_value_payload(vector.home_xg_form),
        "home_xg_n": vector.home_xg_n,
        "input_digest": vector.input_digest,
        "kickoff": _optional_value_payload(vector.kickoff),
        "season": vector.season,
    }


def canonical_payload(vector: FeatureVector) -> str:
    """The canonical JSON string of a feature vector's hashed content."""
    return json.dumps(
        _payload_object(vector),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def content_hash(vector: FeatureVector) -> str:
    """sha256 hex digest of the canonical payload (the F3 contract)."""
    return hashlib.sha256(canonical_payload(vector).encode("utf-8")).hexdigest()


__all__ = ["canonical_payload", "content_hash"]
