"""Phase 2 acceptance criteria 1-3: domain models.

Pure domain checks: frozen value semantics over every dataclass the
builder introduced, missing data as availability (never imputed), and
deterministic canonical ordering. Seeded RNG only; no filesystem reads
outside construction of in-memory objects.
"""

from __future__ import annotations

import dataclasses
import random

import pytest

from app.domain import (
    Availability,
    AvailabilityCounts,
    Fixture,
    IngestedRecord,
    Match,
    MatchCollection,
    MergeOutcome,
    OptionalValue,
    Provenance,
    RawRecord,
    RecordLocation,
    Score,
    Xg,
    canonical_state,
)
from app.ingestion import ImportResult
from app.validation import Defect, DefectReport, Severity, ValidationOutcome

PROVENANCE = Provenance(
    source_path="fixtures/openfootball/valid/season-1.json", sha256="0" * 64
)
LOCATION = RecordLocation(source_path="fixtures/openfootball/valid/season-1.json", index=0)


def sample_match(**overrides: object) -> Match:
    """A fully specified, valid in-memory match."""
    values: dict[str, object] = {
        "competition": "Obsidian Coast League",
        "season": "2024-25",
        "date": "2024-08-10",
        "home": "Coralgate Athletic",
        "away": "Thistledown Wanderers",
        "score": Score(2, 1),
        "round_label": "1",
        "kickoff": OptionalValue.available("15:00"),
        "xg": OptionalValue.missing(),
    }
    values.update(overrides)
    return Match(**values)  # type: ignore[arg-type]


# One constructed sample per dataclass the builder introduced; criterion 1's
# test asserts this dict stays 1:1 complete with the dataclasses actually
# defined under app/.
DATACLASS_SAMPLES: dict[type, object] = {
    Score: Score(2, 1),
    Xg: Xg(1.2, 0.8),
    Provenance: PROVENANCE,
    RecordLocation: LOCATION,
    OptionalValue: OptionalValue.available("15:00"),
    Match: sample_match(),
    # AMENDMENT A4 (Phase 5): one sample for the Phase 5 Fixture value
    # object (additive; the 1:1 completeness pin now covers it too).
    Fixture: Fixture(
        competition="Obsidian Coast League",
        season="2024-25",
        date="2024-08-10",
        home="Coralgate Athletic",
        away="Thistledown Wanderers",
        kickoff=OptionalValue.missing(),
    ),
    RawRecord: RawRecord(
        location=LOCATION,
        provenance=PROVENANCE,
        competition="Obsidian Coast League",
        season="2024-25",
        round="1",
        date="2024-08-10",
        time="15:00",
        team1="Coralgate Athletic",
        team2="Thistledown Wanderers",
        score={"ft": [2, 1]},
        xg=None,
    ),
    IngestedRecord: IngestedRecord(sample_match(), PROVENANCE, LOCATION),
    AvailabilityCounts: AvailabilityCounts(1, 2, 3, 4),
    Defect: Defect(
        code="invalid_date",
        severity=Severity.ERROR,
        location=RecordLocation("fixtures/openfootball/defects/defect-sample.json", 3),
        message="sample defect",
    ),
    DefectReport: DefectReport(),
    ValidationOutcome: ValidationOutcome(records=(), report=DefectReport()),
    ImportResult: ImportResult(validated_records=(), report=DefectReport()),
}

APP_MODULES_FOR_DISCOVERY = (
    "app.domain.models",
    "app.domain.collection",
    "app.validation.report",
    "app.ingestion.openfootball",
)


def test_domain_models_frozen_value_semantics() -> None:
    # Criterion 1: every model is a frozen dataclass; assignment raises
    # AttributeError; structurally equal instances compare equal; the
    # dict above stays 1:1 complete with the dataclasses in app/.
    import importlib

    discovered: set[type] = set()
    for module_name in APP_MODULES_FOR_DISCOVERY:
        module = importlib.import_module(module_name)
        for name, obj in vars(module).items():
            if (
                isinstance(obj, type)
                and dataclasses.is_dataclass(obj)
                and getattr(obj, "__module__", None) == module_name
            ):
                discovered.add(obj)
    assert discovered == set(DATACLASS_SAMPLES), (
        f"dataclasses without samples: {discovered - set(DATACLASS_SAMPLES)}; "
        f"samples without dataclasses: {set(DATACLASS_SAMPLES) - discovered}"
    )

    for cls, sample in DATACLASS_SAMPLES.items():
        assert dataclasses.is_dataclass(cls)
        assert cls.__dataclass_params__.frozen, f"{cls.__name__} is not frozen"
        first_field = dataclasses.fields(cls)[0].name
        with pytest.raises(AttributeError):
            setattr(sample, first_field, None)  # type: ignore[misc]
        # Structurally equal instances compare equal.
        assert dataclasses.replace(sample) == sample  # type: ignore[arg-type]

    # Ingested records cannot be mutated after creation.
    record = IngestedRecord(sample_match(), PROVENANCE, LOCATION)
    with pytest.raises(AttributeError):
        record.match = sample_match(date="2024-08-11")  # type: ignore[misc]


def test_missing_data_is_availability_status_not_imputation() -> None:
    # Criterion 2: absent kickoff and absent xG are availability MISSING
    # with value None; canonical state carries no placeholder anywhere.
    match = sample_match(kickoff=OptionalValue.missing(), xg=OptionalValue.missing())
    assert match.kickoff.availability is Availability.MISSING
    assert match.kickoff.value is None
    assert match.xg.availability is Availability.MISSING
    assert match.xg.value is None

    collection = MatchCollection()
    assert collection.add(IngestedRecord(match, PROVENANCE, LOCATION)) is MergeOutcome.ADDED
    state = canonical_state(collection)
    assert '"kickoff":null' in state
    assert '"xg":null' in state
    assert "00:00" not in state  # no default kickoff
    assert '""' not in state  # no empty-string placeholders
    assert "0.0" not in state  # no imputed 0.0 xG (scores are ints, xG is null)
    assert match.date in state  # the real date, no default date

    # The invariant is structural: MISSING cannot carry a value.
    with pytest.raises(ValueError):
        OptionalValue(0.0, Availability.MISSING)
    with pytest.raises(ValueError):
        OptionalValue(None, Availability.AVAILABLE)


def test_matches_sort_deterministically() -> None:
    # Criterion 3: sorting a shuffled list yields exactly the canonical
    # order (date, competition, season, home, away); the natural key is
    # (competition, season, date, home, away); equal content compares equal.
    matches = [
        sample_match(
            competition=competition,
            season=season,
            date=date,
            home=home,
            away=away,
            score=Score(home_goals, away_goals),
            round_label=round_label,
        )
        for (competition, season, date, home, away, home_goals, away_goals, round_label) in [
            ("Obsidian Coast League", "2024-25", "2024-08-10", "Coralgate Athletic", "Thistledown Wanderers", 2, 1, "1"),
            ("Obsidian Coast League", "2024-25", "2024-08-10", "Silverpine Rovers", "Quarryhill Zenith", 0, 0, "1"),
            ("Obsidian Coast League", "2024-25", "2024-08-17", "Emberfield Kestrels", "Harbourlight Comets", 3, 1, "2"),
            ("Obsidian Coast League", "2025-26", "2025-08-09", "Coralgate Athletic", "Thistledown Wanderers", 1, 3, "1"),
            ("Winter Cup", "2024-25", "2024-08-10", "Coralgate Athletic", "Thistledown Wanderers", 1, 0, "Final"),
            ("Winter Cup", "2024-25", "2024-08-10", "Aurora Cup FC", "Beacon Hillside", 2, 2, "Final"),
        ]
    ]

    shuffled = list(matches)
    random.Random(20261016).shuffle(shuffled)
    sorted_matches = sorted(shuffled, key=lambda m: m.canonical_sort_key)
    expected = sorted(
        matches, key=lambda m: (m.date, m.competition, m.season, m.home, m.away)
    )
    assert sorted_matches == expected

    for match in matches:
        assert match.natural_key == (
            match.competition,
            match.season,
            match.date,
            match.home,
            match.away,
        )
        assert match.canonical_sort_key == (
            match.date,
            match.competition,
            match.season,
            match.home,
            match.away,
        )

    # Equal-content records with the same key compare equal.
    assert sample_match() == sample_match()
    assert sample_match() != sample_match(round_label="2")
