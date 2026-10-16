"""Pure validation of parsed records: defects reported, never guessed around.

Severity rule (Phase 2 design decision 4):
- error   (malformed required data: date, teams, score) -> record excluded;
- warning (malformed optional data: kickoff time, xG)   -> record retained,
  the malformed value dropped to availability MISSING (never converted
  into a value), and the defect reported.
An absent optional field is MISSING, not a defect; a present-but-
malformed optional field is both.

No filesystem, no HTTP, no wall clock — imports only stdlib and
app.domain (enforced by the Phase 2 hygiene test).
"""

from __future__ import annotations

import math
import re
from datetime import date as _date

from app.domain.models import (
    IngestedRecord,
    Match,
    OptionalValue,
    RawRecord,
    Score,
    Xg,
)
from app.validation.report import Defect, DefectReport, Severity, ValidationOutcome

_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
_KICKOFF_TIME = re.compile(r"([01]\d|2[0-3]):[0-5]\d")


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _defect(
    raw: RawRecord, code: str, severity: Severity, message: str
) -> Defect:
    return Defect(code=code, severity=severity, location=raw.location, message=message)


def _checked_date(raw: RawRecord) -> tuple[str | None, Defect | None]:
    """A real YYYY-MM-DD calendar date, or a defect."""
    value = raw.date
    if isinstance(value, str) and _ISO_DATE.fullmatch(value):
        year, month, day = (int(part) for part in value.split("-"))
        try:
            _date(year, month, day)
        except ValueError:
            pass
        else:
            return value, None
    return None, _defect(
        raw,
        "invalid_date",
        Severity.ERROR,
        f"date {value!r} is not a valid YYYY-MM-DD calendar date",
    )


def _checked_score(
    raw: RawRecord,
) -> tuple[Score | None, Defect | None]:
    """A non-negative integer ft pair, or a shape/value defect."""
    ft = raw.score.get("ft") if isinstance(raw.score, dict) else None
    shaped = (
        isinstance(ft, (list, tuple))
        and len(ft) == 2
        and all(_is_int(goal) for goal in ft)
    )
    if not shaped:
        return None, _defect(
            raw,
            "invalid_score_shape",
            Severity.ERROR,
            f"score 'ft' {ft!r} is not a 2-element pair of integers",
        )
    if ft[0] < 0 or ft[1] < 0:
        return None, _defect(
            raw,
            "invalid_score_value",
            Severity.ERROR,
            f"score 'ft' {ft!r} contains a negative goal count",
        )
    return Score(ft[0], ft[1]), None


def _checked_kickoff(raw: RawRecord) -> tuple[OptionalValue, Defect | None]:
    """Optional kickoff: absent is MISSING without defect; malformed is both."""
    if raw.time is None:
        return OptionalValue.missing(), None
    if isinstance(raw.time, str) and _KICKOFF_TIME.fullmatch(raw.time):
        return OptionalValue.available(raw.time), None
    return OptionalValue.missing(), _defect(
        raw,
        "invalid_kickoff_time",
        Severity.WARNING,
        f"kickoff time {raw.time!r} is not a valid HH:MM time; dropped to MISSING",
    )


def _checked_xg(raw: RawRecord) -> tuple[OptionalValue, Defect | None]:
    """Optional xG pair: absent is MISSING without defect; malformed is both.

    A present-but-malformed pair drops the whole pair to MISSING — the
    valid side is never kept alongside a fabricated partner.
    """
    if raw.xg is None:
        return OptionalValue.missing(), None
    home = raw.xg.get("home") if isinstance(raw.xg, dict) else None
    away = raw.xg.get("away") if isinstance(raw.xg, dict) else None
    valid = all(
        _is_number(side) and side >= 0 and math.isfinite(side) for side in (home, away)
    )
    if valid:
        return OptionalValue.available(Xg(float(home), float(away))), None
    return OptionalValue.missing(), _defect(
        raw,
        "invalid_xg_value",
        Severity.WARNING,
        f"xG values (home={home!r}, away={away!r}) must be non-negative "
        "numbers; pair dropped to MISSING",
    )


def _checked_round(raw: RawRecord) -> tuple[str | None, Defect | None]:
    """Round label is metadata: absent is None without defect."""
    if raw.round is None:
        return None, None
    if isinstance(raw.round, str):
        return raw.round, None
    return None, _defect(
        raw,
        "invalid_round",
        Severity.WARNING,
        f"round label {raw.round!r} is not a string; label dropped",
    )


def _checked_team(raw: RawRecord, side: str, field: str) -> tuple[str | None, Defect | None]:
    value = raw.team1 if side == "home" else raw.team2
    if isinstance(value, str) and value.strip():
        return value.strip(), None
    return None, _defect(
        raw,
        f"missing_{'home' if side == 'home' else 'away'}_team",
        Severity.ERROR,
        f"{side} team field {field!r} is missing or empty",
    )


def _validate_record(raw: RawRecord) -> tuple[IngestedRecord | None, list[Defect]]:
    """Validate one record; excluded iff any error-severity defect."""
    defects: list[Defect] = []

    home, defect = _checked_team(raw, "home", "team1")
    if defect is not None:
        defects.append(defect)
    away, defect = _checked_team(raw, "away", "team2")
    if defect is not None:
        defects.append(defect)

    date_value, defect = _checked_date(raw)
    if defect is not None:
        defects.append(defect)

    score, defect = _checked_score(raw)
    if defect is not None:
        defects.append(defect)

    kickoff, defect = _checked_kickoff(raw)
    if defect is not None:
        defects.append(defect)

    xg, defect = _checked_xg(raw)
    if defect is not None:
        defects.append(defect)

    round_label, defect = _checked_round(raw)
    if defect is not None:
        defects.append(defect)

    if any(defect.severity is Severity.ERROR for defect in defects):
        return None, defects

    assert home is not None and away is not None
    assert date_value is not None and score is not None
    match = Match(
        competition=raw.competition,
        season=raw.season,
        date=date_value,
        home=home,
        away=away,
        score=score,
        round_label=round_label,
        kickoff=kickoff,
        xg=xg,
    )
    return IngestedRecord(match=match, provenance=raw.provenance, location=raw.location), defects


def validate_records(records: list[RawRecord] | tuple[RawRecord, ...]) -> ValidationOutcome:
    """Validate one file's parsed records (file order).

    Within-file duplicates (same natural key): identical content collapses
    silently; a conflicting later copy is excluded with exactly one
    `conflicting_duplicate` error naming both record locations; the first
    occurrence in file order is retained.
    """
    defects: list[Defect] = []
    accepted: list[IngestedRecord] = []
    by_key: dict[tuple[str, str, str, str, str], IngestedRecord] = {}

    for raw in records:
        record, record_defects = _validate_record(raw)
        defects.extend(record_defects)
        if record is None:
            continue
        key = record.match.natural_key
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = record
            accepted.append(record)
        elif existing.match == record.match:
            continue  # identical duplicate: collapse silently
        else:
            defects.append(
                _defect(
                    raw,
                    "conflicting_duplicate",
                    Severity.ERROR,
                    f"record at {raw.location.source_path}[{raw.location.index}] "
                    "conflicts with earlier record at "
                    f"{existing.location.source_path}[{existing.location.index}] "
                    "(same natural key, different content); later record excluded",
                )
            )

    return ValidationOutcome(tuple(accepted), DefectReport(tuple(defects)))
