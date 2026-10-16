"""Phase 2 acceptance criteria 8-11: validation reports defects, never repairs.

Valid fixtures validate clean; the defect fixture reports exactly the
seven planted defects once each; error-severity records are excluded
without any value being coerced into state; availability counts treat
missing as a first-class result.
"""

from __future__ import annotations

from pathlib import Path

from app.domain import (
    Availability,
    AvailabilityCounts,
    MatchCollection,
    availability_counts,
    canonical_state,
)
from app.ingestion import import_fixture, load_records
from app.validation import Severity, validate_records

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball"
VALID_1 = FIXTURES / "valid" / "season-1.json"
VALID_2 = FIXTURES / "valid" / "season-2.json"
DEFECTS = FIXTURES / "defects" / "defect-sample.json"

DEFECT_SOURCE = "fixtures/openfootball/defects/defect-sample.json"


def test_valid_fixtures_validate_clean() -> None:
    # Criterion 8: empty defect report; absent optional fields are
    # missing availability, explicitly not defects.
    for path in (VALID_1, VALID_2):
        outcome = validate_records(load_records(path))
        assert outcome.report.defects == ()
        assert not outcome.report


def test_planted_defects_reported_exactly_once_each() -> None:
    # Criterion 9: exactly the seven planted defects, each code once,
    # with severity, file path, and record index — and nothing else.
    outcome = validate_records(load_records(DEFECTS))
    assert [(d.code, d.severity, d.location.index) for d in outcome.report.defects] == [
        ("invalid_date", Severity.ERROR, 3),
        ("missing_home_team", Severity.ERROR, 4),
        ("invalid_score_shape", Severity.ERROR, 5),
        ("invalid_score_value", Severity.ERROR, 6),
        ("invalid_kickoff_time", Severity.WARNING, 7),
        ("invalid_xg_value", Severity.WARNING, 8),
        ("conflicting_duplicate", Severity.ERROR, 10),
    ]
    for defect in outcome.report.defects:
        assert defect.location.source_path == DEFECT_SOURCE


def test_validation_reports_without_repairing() -> None:
    # Criterion 10: accepted count = imported minus error-severity;
    # nothing malformed is coerced into state; every defect is complete.
    collection = MatchCollection()
    result = import_fixture(DEFECTS, collection)
    imported = len(load_records(DEFECTS))
    errors = [d for d in result.report.defects if d.severity is Severity.ERROR]
    warnings = [d for d in result.report.defects if d.severity is Severity.WARNING]
    assert imported == 12
    assert len(errors) == 5
    assert len(warnings) == 2
    assert len(collection) == imported - len(errors) == 7
    assert len(result.validated_records) == 7

    matches = [r.match for r in collection.records()]
    known_teams = {
        "Coralgate Athletic",
        "Emberfield Kestrels",
        "Harbourlight Comets",
        "Quarryhill Zenith",
        "Silverpine Rovers",
        "Thistledown Wanderers",
    }
    # The bad date never becomes any date; no team defaulted or invented.
    assert all(m.date != "2024-13-40" for m in matches)
    assert all(m.home in known_teams and m.away in known_teams for m in matches)
    assert all(m.home and m.away for m in matches)
    # Scores are never clamped: no negative goals anywhere, and the
    # [-1, 3] record's match is simply absent.
    assert all(m.score.home >= 0 and m.score.away >= 0 for m in matches)
    assert not any(
        m.date == "2024-09-15" and m.home == "Coralgate Athletic" for m in matches
    )
    # The conflicting copy is never merged: exactly one record at the key.
    assert (
        sum(
            1
            for m in matches
            if m.date == "2024-09-28"
            and m.home == "Silverpine Rovers"
            and m.away == "Emberfield Kestrels"
        )
        == 1
    )
    # Warning records are retained with the malformed value dropped.
    kickoff_dropped = [m for m in matches if m.date == "2024-09-21" and m.home == "Thistledown Wanderers"]
    assert len(kickoff_dropped) == 1
    assert kickoff_dropped[0].kickoff.availability is Availability.MISSING
    assert kickoff_dropped[0].kickoff.value is None
    xg_dropped = [m for m in matches if m.date == "2024-09-21" and m.home == "Harbourlight Comets"]
    assert len(xg_dropped) == 1
    assert xg_dropped[0].xg.availability is Availability.MISSING
    assert xg_dropped[0].xg.value is None

    # Every defect carries code, severity, location, and a message.
    for defect in result.report.defects:
        assert defect.code
        assert defect.severity in (Severity.ERROR, Severity.WARNING)
        assert defect.location.source_path == DEFECT_SOURCE
        assert defect.location.index >= 0
        assert defect.message and isinstance(defect.message, str)


def test_availability_summary_counts_missing() -> None:
    # Criterion 11: the two valid fixtures report availability exactly:
    # kickoff 30/30, xG 10/50, sums to 60, no imputed values in state.
    collection = MatchCollection()
    import_fixture(VALID_1, collection)
    import_fixture(VALID_2, collection)
    assert len(collection) == 60

    counts = availability_counts(collection)
    assert counts == AvailabilityCounts(
        kickoff_available=30,
        kickoff_missing=30,
        xg_available=10,
        xg_missing=50,
    )
    assert counts.kickoff_available + counts.kickoff_missing == 60
    assert counts.xg_available + counts.xg_missing == 60

    state = canonical_state(collection)
    assert state.count('"kickoff":null') == 30
    assert state.count('"xg":null') == 50
    assert '"xg":0.0' not in state
    assert '"kickoff":""' not in state
    assert '"kickoff":"00:00"' not in state
