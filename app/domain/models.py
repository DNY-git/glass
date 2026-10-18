"""Immutable domain models for football match data.

Pure domain: imports only the standard library — no filesystem, no HTTP,
no environment lookups (enforced structurally by the Phase 2 hygiene
test). Everything here is a frozen value object; missing optional data
is availability ``MISSING`` with value ``None``, never imputed.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any


class Availability(enum.Enum):
    """Whether an optional value is present; missing is never imputed."""

    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"


@dataclass(frozen=True)
class OptionalValue:
    """An optional value paired with its availability status.

    Invariant (enforced in __post_init__): availability MISSING holds
    exactly value None; availability AVAILABLE holds a real value.
    """

    value: Any
    availability: Availability

    def __post_init__(self) -> None:
        if self.availability is Availability.MISSING and self.value is not None:
            raise ValueError("MISSING availability must carry value None")
        if self.availability is Availability.AVAILABLE and self.value is None:
            raise ValueError("AVAILABLE availability must carry a non-None value")

    @classmethod
    def available(cls, value: Any) -> "OptionalValue":
        if value is None:
            raise ValueError("available() requires a non-None value")
        return cls(value, Availability.AVAILABLE)

    @classmethod
    def missing(cls) -> "OptionalValue":
        return cls(None, Availability.MISSING)


@dataclass(frozen=True)
class Score:
    """Full-time scoreline; integer goal counts, never clamped."""

    home: int
    away: int


@dataclass(frozen=True)
class Xg:
    """Expected-goals pair (documented synthetic fixture extension)."""

    home: float
    away: float


@dataclass(frozen=True)
class Provenance:
    """Where a record came from: repo-relative path + sha256 of raw bytes.

    Deliberately carries no mtime, no absolute path, and no timestamp —
    environment data must never enter state (determinism).
    """

    source_path: str
    sha256: str


@dataclass(frozen=True)
class RecordLocation:
    """Location of one record: repo-relative file + index in matches[]."""

    source_path: str
    index: int


# Natural identity of a match (design decision 5): round labels are
# metadata, not identity.
NaturalKey = tuple[str, str, str, str, str]  # (competition, season, date, home, away)


@dataclass(frozen=True)
class Match:
    """One accepted match: required results plus optional data."""

    competition: str
    season: str
    date: str  # ISO calendar date, validated at ingestion
    home: str
    away: str
    score: Score
    round_label: str | None  # metadata, not identity
    kickoff: OptionalValue  # value: "HH:MM" str or None
    xg: OptionalValue  # value: Xg pair or None

    @property
    def natural_key(self) -> NaturalKey:
        return (self.competition, self.season, self.date, self.home, self.away)

    @property
    def canonical_sort_key(self) -> tuple[str, str, str, str, str]:
        """Canonical order (design decision 7): chronological primary."""
        return (self.date, self.competition, self.season, self.home, self.away)


@dataclass(frozen=True)
class Fixture:
    """One forecast target: an upcoming fixture with no result.

    Phase 5 design decision 3: deliberately NO ``score`` field exists —
    a forecast target that cannot even represent a result is
    structurally incapable of consuming its own future, while ``Match``
    stays the realized, scored history type (its required ``score`` is
    what the fitter's goal arithmetic and validation rely on). Kickoff
    rides as an OptionalValue: MISSING stays MISSING, never defaulted.
    """

    competition: str
    season: str
    date: str  # ISO calendar date, day granularity (the forecast cutoff)
    home: str
    away: str
    kickoff: OptionalValue

    @property
    def natural_key(self) -> NaturalKey:
        return (self.competition, self.season, self.date, self.home, self.away)

    @property
    def canonical_sort_key(self) -> tuple[str, str, str, str, str]:
        """Canonical order (design decision 7): chronological primary."""
        return (self.date, self.competition, self.season, self.home, self.away)


@dataclass(frozen=True)
class RawRecord:
    """One record parsed from a fixture file, before validation.

    Field values are raw JSON values (Any): validation interprets and
    judges them; ingestion never guesses. ``competition``/``season``
    come from file-level metadata and are stamped onto every record.
    """

    location: RecordLocation
    provenance: Provenance
    competition: str
    season: str
    round: Any
    date: Any
    time: Any
    team1: Any
    team2: Any
    score: Any
    xg: Any


@dataclass(frozen=True)
class IngestedRecord:
    """A validated match with its provenance and source location."""

    match: Match
    provenance: Provenance
    location: RecordLocation
