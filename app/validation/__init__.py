"""Validation layer (pipeline stage 2): defects reported, not guessed around.

Pure functions over parsed records; no filesystem, no HTTP.
"""

from .checks import validate_records
from .report import Defect, DefectReport, Severity, ValidationOutcome

__all__ = [
    "Defect",
    "DefectReport",
    "Severity",
    "ValidationOutcome",
    "validate_records",
]
