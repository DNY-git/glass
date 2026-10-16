"""Sorted, deduplicating match collection and canonical serialization.

The collection is the one intentionally mutable object in the domain:
it is the import accumulator. Everything it yields is frozen. All
iteration and serialization is sorted by canonical order — input order
and dict/set iteration never leak into output.
"""

from __future__ import annotations

import enum
import json
from dataclasses import dataclass

from .models import Availability, IngestedRecord, Match, NaturalKey


class MergeOutcome(enum.Enum):
    """Result of adding a record to a MatchCollection."""

    ADDED = "ADDED"
    IDENTICAL_DUPLICATE = "IDENTICAL_DUPLICATE"
    CONFLICTING = "CONFLICTING"


def _canonical_sort_key_for_natural_key(key: NaturalKey) -> tuple[str, str, str, str, str]:
    """Natural key (competition, season, date, home, away) -> canonical order."""
    competition, season, date, home, away = key
    return (date, competition, season, home, away)


class MatchCollection:
    """Deduplicating match collection keyed by the natural key.

    add() never overwrites: an identical-content duplicate collapses
    silently (re-import is a no-op); a conflicting duplicate is reported
    as CONFLICTING and the first occurrence is retained.
    """

    def __init__(self) -> None:
        self._by_key: dict[NaturalKey, IngestedRecord] = {}

    def __len__(self) -> int:
        return len(self._by_key)

    def get(self, key: NaturalKey) -> IngestedRecord | None:
        return self._by_key.get(key)

    def add(self, record: IngestedRecord) -> MergeOutcome:
        key = record.match.natural_key
        existing = self._by_key.get(key)
        if existing is None:
            self._by_key[key] = record
            return MergeOutcome.ADDED
        if existing.match == record.match:
            return MergeOutcome.IDENTICAL_DUPLICATE
        return MergeOutcome.CONFLICTING

    def records(self) -> tuple[IngestedRecord, ...]:
        """All records in canonical order (date, competition, season, home, away)."""
        ordered_keys = sorted(self._by_key, key=_canonical_sort_key_for_natural_key)
        return tuple(self._by_key[key] for key in ordered_keys)


def _canonical_match_dict(match: Match) -> dict[str, object]:
    """Canonical serialization of one match; MISSING optionals are null."""
    xg = match.xg.value
    return {
        "competition": match.competition,
        "season": match.season,
        "date": match.date,
        "home": match.home,
        "away": match.away,
        "round": match.round_label,
        "score": {"ft": [match.score.home, match.score.away]},
        "kickoff": match.kickoff.value,
        "xg": None if xg is None else {"home": xg.home, "away": xg.away},
    }


def canonical_state(collection: MatchCollection) -> str:
    """The single canonical serialization entry point (decision 7).

    JSON: records in canonical order, sorted keys, fixed separators, no
    timestamps, no provenance (provenance is environment-derived path
    metadata, not match state). Byte-identical across runs for the same
    accepted records.
    """
    payload = [_canonical_match_dict(record.match) for record in collection.records()]
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class AvailabilityCounts:
    """Counts of optional-data availability across a collection."""

    kickoff_available: int
    kickoff_missing: int
    xg_available: int
    xg_missing: int

    @property
    def total(self) -> int:
        return (
            self.kickoff_available
            + self.kickoff_missing
            + self.xg_available
            + self.xg_missing
        )


def availability_counts(collection: MatchCollection) -> AvailabilityCounts:
    """Count kickoff and xG availability; missing stays missing."""
    kickoff = {Availability.AVAILABLE: 0, Availability.MISSING: 0}
    xg = {Availability.AVAILABLE: 0, Availability.MISSING: 0}
    for record in collection.records():
        kickoff[record.match.kickoff.availability] += 1
        xg[record.match.xg.availability] += 1
    return AvailabilityCounts(
        kickoff_available=kickoff[Availability.AVAILABLE],
        kickoff_missing=kickoff[Availability.MISSING],
        xg_available=xg[Availability.AVAILABLE],
        xg_missing=xg[Availability.MISSING],
    )
