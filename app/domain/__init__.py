"""Domain layer: immutable models, match collection, canonical state.

No imports outside this package (enforced by the Phase 2 hygiene test).
"""

from .collection import (
    AvailabilityCounts,
    MatchCollection,
    MergeOutcome,
    availability_counts,
    canonical_state,
)
from .models import (
    Availability,
    Fixture,
    IngestedRecord,
    Match,
    NaturalKey,
    OptionalValue,
    Provenance,
    RawRecord,
    RecordLocation,
    Score,
    Xg,
)

__all__ = [
    "Availability",
    "AvailabilityCounts",
    "Fixture",
    "IngestedRecord",
    "Match",
    "MatchCollection",
    "MergeOutcome",
    "NaturalKey",
    "OptionalValue",
    "Provenance",
    "RawRecord",
    "RecordLocation",
    "Score",
    "Xg",
    "availability_counts",
    "canonical_state",
]
