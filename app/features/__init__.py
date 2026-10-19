"""Feature engine (pipeline stage 4): chronological features, cutoff inside.

The pure, deterministic feature stage: ``compute_features(matches,
fixture)`` derives one frozen ``FeatureVector`` per fixture with the
cutoff derived INSIDE (the cutoff IS ``fixture.date``, a strict
``date <`` on every consumed match) — no time-like parameter exists to
forget. The versioned feature spec is ``FEATURE_VERSION`` plus the
named policy constants in ``constants`` plus the written canonicalization
spec in ``canonicalization`` (whose docstrings are the specs of record).

Every field is a HISTORICAL SUMMARY of past matches — not a
probability, not a model output, not evidence (STATISTICAL-ASSUMPTIONS
section 9); MISSING propagates visibly and is never rendered as 0. The
synthetic-data caveat rides every feature: fictional league,
hand-authored fixtures. Consumed by nothing (decision 11) — no storage,
no API, no forecast field, zero fitted transformers (F2). No
filesystem, no HTTP, no randomness, no wall clock (ISO date
arithmetic only), no environment lookups (enforced structurally by the
Phase 6 separation tests).
"""

from .canonicalization import canonical_payload, content_hash
from .compute import compute_features
from .constants import FEATURE_VERSION
from .record import FeatureVector

__all__ = [
    "FEATURE_VERSION",
    "FeatureVector",
    "canonical_payload",
    "compute_features",
    "content_hash",
]
