"""Defect reports: outputs of validation, never state.

A Defect names what is wrong and where (repo-relative file + index in
the matches array). A DefectReport is deterministically ordered so
re-validation of the same file yields a byte-identical report.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from app.domain.models import IngestedRecord, RecordLocation


class Severity(enum.Enum):
    """Error: record excluded from accepted state. Warning: record retained."""

    ERROR = "ERROR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class Defect:
    """One reported defect: code, severity, location, human-readable message."""

    code: str
    severity: Severity
    location: RecordLocation
    message: str


def _defect_sort_key(defect: Defect) -> tuple[str, int, str, str]:
    return (
        defect.location.source_path,
        defect.location.index,
        defect.code,
        defect.message,
    )


@dataclass(frozen=True)
class DefectReport:
    """Deterministically ordered tuple of defects (empty means clean)."""

    defects: tuple[Defect, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "defects", tuple(sorted(self.defects, key=_defect_sort_key)))

    def __bool__(self) -> bool:
        return bool(self.defects)


@dataclass(frozen=True)
class ValidationOutcome:
    """Result of validating one file's records: accepted + report."""

    records: tuple[IngestedRecord, ...]  # accepted, in file order
    report: DefectReport
