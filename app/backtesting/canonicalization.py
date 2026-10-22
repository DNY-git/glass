"""The canonicalization spec of record for backtest content hashes.

This module IS the written spec for this package's own hashes (the
walk-forward records are hashed independently of the forecast spec —
no import crosses the stage boundary into ``app.forecasts``
canonicalization; design decision 4). Fixed rules, everywhere:

* keys sorted lexicographically (``json.dumps(..., sort_keys=True)``);
* fixed separators ``(",", ":")``, ``ensure_ascii=True``, no trailing
  newline;
* strings as-is; ints decimal; floats via Python's shortest round-trip
  repr (full precision, no rounding ever); enums as their ``.value``
  strings; tuples as JSON arrays in order; ``None`` as JSON ``null``;
* **no timestamp, no filesystem path, no environment value, and no
  seed may appear in any hashed payload** — the manifest echoes
  caller-supplied identity fields but they are covered by no hash
  except the run digest's own ordered entries list.

``baseline_payload``/``baseline_content_hash`` are the ONE mapping
for a baseline record's canonical payload; ``entries_payload``/
``entries_digest`` serialize an ordered (fixture key, content_hash)
list — the run digest's and the poison-gate prefix digest's shared
form (design decision 6).
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:  # annotation-only; no runtime cycle with .record
    from .record import BaselineRecord

# The one fixed JSON shape used everywhere in this module.
_JSON_OPTIONS: dict[str, Any] = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": True,
}

FixtureKey = tuple[str, str, str, str, str]


def canonical_json(payload: Any) -> str:
    """The canonical JSON string under the spec of record."""
    return json.dumps(payload, **_JSON_OPTIONS)


def sha256_hex(text: str) -> str:
    """sha256 hex digest of the UTF-8 bytes of a canonical string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def baseline_payload(record: BaselineRecord) -> dict[str, Any]:
    """Exactly the baseline record's fields minus ``content_hash``."""
    return {
        "away_frequency": record.away_frequency,
        "draw_frequency": record.draw_frequency,
        "fixture_key": list(record.fixture_key),
        "home_frequency": record.home_frequency,
        "n": record.n,
        "status": record.status.value,
    }


def baseline_content_hash(record: BaselineRecord) -> str:
    """sha256 hex digest of the baseline record's canonical payload."""
    return sha256_hex(canonical_json(baseline_payload(record)))


def entries_payload(entries: Sequence[tuple[FixtureKey, str]]) -> str:
    """Canonical JSON of an ordered (fixture key, content_hash) list.

    Order is the caller's and IS content: the list is serialized as an
    array in sequence (no set iteration, no re-sorting here), with each
    fixture key as an array of its five strings.
    """
    return canonical_json([[list(key), digest] for key, digest in entries])


def entries_digest(entries: Sequence[tuple[FixtureKey, str]]) -> str:
    """sha256 hex digest of an ordered entries list (run/prefix digest)."""
    return sha256_hex(entries_payload(entries))


__all__ = [
    "FixtureKey",
    "baseline_content_hash",
    "baseline_payload",
    "canonical_json",
    "entries_digest",
    "entries_payload",
    "sha256_hex",
]
