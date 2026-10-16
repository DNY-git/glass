"""Phase 2 acceptance criteria 4-7: ingestion from local fixtures.

Golden-value, provenance, idempotency, and duplicate-handling checks.
All fixture paths resolve relative to the repository root; no network,
no wall clock, seeded RNG only.
"""

from __future__ import annotations

import hashlib
import dataclasses
from pathlib import Path

from app.domain import MatchCollection, Provenance, RawRecord, RecordLocation, canonical_state
from app.ingestion import import_fixture, load_records, merge_records
from app.validation import Severity, validate_records

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball"
VALID_1 = FIXTURES / "valid" / "season-1.json"
VALID_2 = FIXTURES / "valid" / "season-2.json"
DEFECTS = FIXTURES / "defects" / "defect-sample.json"

COMPETITION = "Obsidian Coast League"


def raw_record(index: int, **overrides: object) -> RawRecord:
    """A valid in-memory raw record; overrides simulate defect scenarios."""
    values: dict[str, object] = {
        "location": RecordLocation("fixtures/openfootball/valid/season-1.json", index),
        "provenance": Provenance("fixtures/openfootball/valid/season-1.json", "0" * 64),
        "competition": COMPETITION,
        "season": "2024-25",
        "round": "1",
        "date": "2024-08-10",
        "time": "15:00",
        "team1": "Coralgate Athletic",
        "team2": "Thistledown Wanderers",
        "score": {"ft": [2, 1]},
        "xg": None,
    }
    values.update(overrides)
    return RawRecord(**values)  # type: ignore[arg-type]


def test_load_valid_fixtures_exact_contents() -> None:
    # Criterion 4: 60 matches, 6 teams, both seasons, integer scorelines,
    # round labels, and exact golden first/last matches by canonical order.
    collection = MatchCollection()
    result_1 = import_fixture(VALID_1, collection)
    result_2 = import_fixture(VALID_2, collection)
    assert not result_1.report.defects
    assert not result_2.report.defects
    assert len(collection) == 60

    records = collection.records()
    teams = {r.match.home for r in records} | {r.match.away for r in records}
    assert len(teams) == 6
    assert {r.match.season for r in records} == {"2024-25", "2025-26"}
    assert all(isinstance(r.match.score.home, int) for r in records)
    assert all(isinstance(r.match.score.away, int) for r in records)
    assert {r.match.round_label for r in records} == {str(i) for i in range(1, 11)}

    # Golden tuples, checked against the fixture text (first record of
    # season-1.json and last record of season-2.json in canonical order).
    first = records[0].match
    assert (
        first.date,
        first.round_label,
        first.home,
        first.away,
        (first.score.home, first.score.away),
    ) == ("2024-08-10", "1", "Coralgate Athletic", "Thistledown Wanderers", (2, 1))
    last = records[-1].match
    assert (
        last.date,
        last.round_label,
        last.home,
        last.away,
        (last.score.home, last.score.away),
    ) == ("2025-10-11", "10", "Quarryhill Zenith", "Silverpine Rovers", (3, 2))


def test_provenance_path_and_digest_without_timestamps() -> None:
    # Criterion 5: sha256 of raw bytes, repo-relative path, and no
    # environment data (abs path, mtime, timestamp-like fields) in state.
    collection = MatchCollection()
    import_fixture(VALID_1, collection)
    raw_bytes = VALID_1.read_bytes()
    digest = hashlib.sha256(raw_bytes).hexdigest()

    for record in collection.records():
        assert record.provenance.sha256 == digest
        assert record.provenance.source_path == "fixtures/openfootball/valid/season-1.json"
        assert not Path(record.provenance.source_path).is_absolute()

    # Provenance has exactly these two fields: no mtime, no timestamp.
    assert {f.name for f in dataclasses.fields(Provenance)} == {"source_path", "sha256"}

    state = canonical_state(collection)
    assert str(REPO_ROOT) not in state
    mtime = VALID_1.stat().st_mtime
    assert str(mtime) not in state
    assert str(int(mtime)) not in state
    # Canonical records carry only match fields — no timestamp-like keys.
    import json

    for serialized in json.loads(state):
        assert set(serialized) == {
            "competition",
            "season",
            "date",
            "home",
            "away",
            "round",
            "score",
            "kickoff",
            "xg",
        }


def test_idempotent_import_same_file_twice() -> None:
    # Criterion 6: same file twice -> byte-identical canonical state and,
    # for the defect fixture, an identical defect report.
    collection = MatchCollection()
    import_fixture(VALID_1, collection)
    import_fixture(VALID_2, collection)
    state_once = canonical_state(collection)
    count_once = len(collection)

    import_fixture(VALID_1, collection)
    import_fixture(VALID_2, collection)
    assert canonical_state(collection) == state_once
    assert len(collection) == count_once == 60

    defect_collection = MatchCollection()
    first = import_fixture(DEFECTS, defect_collection)
    state_first = canonical_state(defect_collection)
    second = import_fixture(DEFECTS, defect_collection)
    assert canonical_state(defect_collection) == state_first
    assert first.report == second.report
    assert len(defect_collection) == 7


def test_duplicate_handling_identical_dedupes_conflict_defects() -> None:
    # Criterion 7: identical-content duplicates collapse with no defect
    # and no state change; a conflicting duplicate is exactly one error
    # naming both locations, first retained, later copy excluded.
    identical = [raw_record(1), raw_record(2)]
    outcome = validate_records(identical)
    assert len(outcome.records) == 1
    assert outcome.report.defects == ()

    collection = MatchCollection()
    merge_records(collection, outcome.records)
    state = canonical_state(collection)
    merge_records(collection, outcome.records)  # re-merge: identical content
    assert canonical_state(collection) == state
    assert len(collection) == 1

    # Conflicting duplicate across imports: same natural key, different score.
    conflict_collection = MatchCollection()
    first_score = validate_records([raw_record(0, date="2024-08-17", score={"ft": [2, 0]})])
    assert first_score.report.defects == ()
    assert merge_records(conflict_collection, first_score.records) == ()

    conflicting = validate_records([raw_record(1, date="2024-08-17", score={"ft": [2, 1]})])
    merge_defects = merge_records(conflict_collection, conflicting.records)
    assert len(merge_defects) == 1
    defect = merge_defects[0]
    assert defect.code == "conflicting_duplicate"
    assert defect.severity is Severity.ERROR
    # The message names both record locations (file + index each).
    assert "season-1.json[0]" in defect.message
    assert "season-1.json[1]" in defect.message
    # First occurrence retained in state; later copy excluded.
    assert len(conflict_collection) == 1
    retained = conflict_collection.records()[0].match
    assert (retained.score.home, retained.score.away) == (2, 0)

    # Same rule within one file (defect fixture): exactly one error,
    # message names both locations, first copy retained.
    defect_collection = MatchCollection()
    result = import_fixture(DEFECTS, defect_collection)
    conflicts = [d for d in result.report.defects if d.code == "conflicting_duplicate"]
    assert len(conflicts) == 1
    assert conflicts[0].location.index == 10
    assert "[9]" in conflicts[0].message and "[10]" in conflicts[0].message
    dup_key_matches = [
        r.match
        for r in defect_collection.records()
        if r.match.date == "2024-09-28"
        and r.match.home == "Silverpine Rovers"
        and r.match.away == "Emberfield Kestrels"
    ]
    assert len(dup_key_matches) == 1
    assert (dup_key_matches[0].score.home, dup_key_matches[0].score.away) == (2, 0)
