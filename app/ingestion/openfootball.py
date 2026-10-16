"""OpenFootball-format match-list ingestion from local JSON fixtures.

Filesystem yes; network never. Reads a local JSON file, parses records,
attaches provenance (repo-relative path + sha256 of raw bytes — no
mtime, no absolute path, no timestamps), validates them purely via
app.validation, and merges accepted records into a collection with
idempotent semantics: identical duplicates collapse silently, a
conflicting duplicate is reported and excluded.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.domain.collection import MatchCollection, MergeOutcome
from app.domain.models import IngestedRecord, Provenance, RawRecord, RecordLocation
from app.validation.checks import validate_records
from app.validation.report import Defect, DefectReport, Severity, ValidationOutcome

# Repo root, derived from this module's location (not the environment).
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ImportResult:
    """Outcome of importing one fixture file into a collection."""

    validated_records: tuple[IngestedRecord, ...]  # accepted by validation, file order
    report: DefectReport  # validation defects + merge conflict defects


def _repo_relative(path: Path, root: Path) -> str:
    resolved = path.resolve()
    base = root.resolve()
    try:
        return resolved.relative_to(base).as_posix()
    except ValueError as exc:
        raise ValueError(f"{resolved} is not under root {base}") from exc


def load_records(path: Path, *, root: Path | None = None) -> tuple[RawRecord, ...]:
    """Parse a local OpenFootball-shaped JSON match list into raw records.

    Structural requirements (raise ValueError): top-level object with
    non-empty string ``competition`` and ``season`` and a ``matches``
    array of objects. Record-level defects are not raised here — they
    are reported by validation.

    ``root`` is the directory the provenance path is made relative to;
    it defaults to the repository root. Pass root=tmp_path when loading
    a copy of a fixture written to a temp directory.
    """
    base = root if root is not None else REPO_ROOT
    source_path = _repo_relative(path, base)
    raw_bytes = path.resolve().read_bytes()
    provenance = Provenance(
        source_path=source_path,
        sha256=hashlib.sha256(raw_bytes).hexdigest(),
    )

    payload = json.loads(raw_bytes.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{source_path}: top level must be a JSON object")
    competition = payload.get("competition")
    season = payload.get("season")
    if not (isinstance(competition, str) and competition):
        raise ValueError(f"{source_path}: missing or invalid 'competition'")
    if not (isinstance(season, str) and season):
        raise ValueError(f"{source_path}: missing or invalid 'season'")
    matches = payload.get("matches")
    if not isinstance(matches, list):
        raise ValueError(f"{source_path}: missing or invalid 'matches' array")

    records: list[RawRecord] = []
    for index, entry in enumerate(matches):
        if not isinstance(entry, dict):
            raise ValueError(f"{source_path}: matches[{index}] is not a JSON object")
        records.append(
            RawRecord(
                location=RecordLocation(source_path=source_path, index=index),
                provenance=provenance,
                competition=competition,
                season=season,
                round=entry.get("round"),
                date=entry.get("date"),
                time=entry.get("time"),
                team1=entry.get("team1"),
                team2=entry.get("team2"),
                score=entry.get("score"),
                xg=entry.get("xg"),
            )
        )
    return tuple(records)


def merge_records(
    collection: MatchCollection, records: Iterable[IngestedRecord]
) -> tuple[Defect, ...]:
    """Merge validated records into the collection; return merge defects.

    Identical-content duplicates collapse silently (re-import is a
    no-op); a conflicting record (same natural key, different content)
    is excluded with one `conflicting_duplicate` error naming both
    record locations — the collection's first occurrence is retained.
    """
    defects: list[Defect] = []
    for record in records:
        outcome = collection.add(record)
        if outcome is MergeOutcome.CONFLICTING:
            existing = collection.get(record.match.natural_key)
            assert existing is not None  # CONFLICTING implies an existing record
            defects.append(
                Defect(
                    code="conflicting_duplicate",
                    severity=Severity.ERROR,
                    location=record.location,
                    message=f"record at {record.location.source_path}[{record.location.index}] "
                    "conflicts with earlier record at "
                    f"{existing.location.source_path}[{existing.location.index}] "
                    "(same natural key, different content); later record excluded",
                )
            )
    return tuple(defects)


def import_fixture(
    path: Path, collection: MatchCollection, *, root: Path | None = None
) -> ImportResult:
    """Import one fixture file: load, validate, merge. Idempotent."""
    records = load_records(path, root=root)
    outcome: ValidationOutcome = validate_records(records)
    merge_defects = merge_records(collection, outcome.records)
    report = DefectReport(outcome.report.defects + merge_defects)
    return ImportResult(validated_records=outcome.records, report=report)
