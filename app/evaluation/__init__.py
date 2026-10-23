"""Forecast evaluation (IX-11): the evidence gate's public surface.

Exactly twelve names, the gate's contract surface (criterion 1): the one
entry point, the frozen result/record containers it produces, the metric
and calibration value objects, the conflict error, and the record
version.  Everything else in this package is private machinery.
"""

from .calibration import (
    CalibrationBin,
    CalibrationTable,
    OverdispersionDiagnostic,
)
from .evaluate import (
    EVALUATION_VERSION,
    EvaluationAccounting,
    EvaluationConflictError,
    EvaluationRecord,
    EvaluationResult,
    MetricTriple,
    PopulationScores,
    ScoredContribution,
    evaluate_predictions,
)

__all__ = [
    "evaluate_predictions",
    "EvaluationResult",
    "EvaluationAccounting",
    "PopulationScores",
    "MetricTriple",
    "ScoredContribution",
    "CalibrationTable",
    "CalibrationBin",
    "OverdispersionDiagnostic",
    "EvaluationRecord",
    "EvaluationConflictError",
    "EVALUATION_VERSION",
]
