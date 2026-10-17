"""Fitted-parameter records for the Poisson goal model (poisson-mle-v1).

All value objects here are frozen dataclasses: a fit is immutable once
created (constitution: forecasts and pre-match snapshots are immutable;
the fitted parameter object is their statistical seed). No timestamps,
no absolute paths, no environment values appear in any field — only
numbers, config echoes, and the sha256 input digest (determinism,
HANDOFF Part V).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

from .constants import DAMPING, MAX_GOALS, MAX_ITERATIONS, MODEL_VERSION, NEWTON_TOL


class ConvergenceStatus(enum.Enum):
    """Reported outcome of the Newton fit; never omitted, never silent.

    CONVERGED — an update step below NEWTON_TOL was applied; the MLE
        (under the documented model form) was reached to tolerance.
    MAX_ITERATIONS — the hard step cap was reached first; the parameter
        vector is a reported iterate, explicitly marked non-converged.
    SINGULAR_SYSTEM — the Newton system was singular or produced a
        non-finite update (typically thin pre-cutoff history: fewer
        independent equations than unknowns). The parameter vector is
        the last well-defined iterate, explicitly marked; never a
        crash, never a silent fallback (quant B2, brief risk section).
    NO_DATA — no matches (or no distinct teams) remained strictly
        before the cutoff, so no likelihood exists to fit. Fields carry
        neutral zeros; the object is well-formed and flagged.
    """

    CONVERGED = "CONVERGED"
    MAX_ITERATIONS = "MAX_ITERATIONS"
    SINGULAR_SYSTEM = "SINGULAR_SYSTEM"
    NO_DATA = "NO_DATA"


@dataclass(frozen=True)
class FitConfig:
    """Effective configuration of one fit, echoed on every result.

    The defaults are the documented named constants; tests may override
    them (e.g. force the iteration cap) and the override is echoed per
    fit (brief decision 6). ``ridge`` exists as an explicit field
    defaulting to None (unpenalized MLE, brief decision 8): poisson-mle-v1
    implements no shrinkage, so a non-None value is refused by ``fit``
    with a ValueError rather than silently ignored — no silent
    shrinkage, ever.
    """

    newton_tol: float = NEWTON_TOL
    max_iterations: int = MAX_ITERATIONS
    damping: float = DAMPING
    max_goals: int = MAX_GOALS
    ridge: float | None = None

    def __post_init__(self) -> None:
        if self.max_iterations < 1:
            raise ValueError("max_iterations must be >= 1")
        if not self.newton_tol > 0.0:
            raise ValueError("newton_tol must be > 0")
        if self.max_goals < 0:
            raise ValueError("max_goals must be >= 0")


@dataclass(frozen=True)
class SampleSize:
    """Pre-cutoff sample a fit rests on: matches used, goals observed."""

    matches: int
    goals: int


@dataclass(frozen=True)
class PoolingRecord:
    """What the fit pooled: competition, seasons, cutoff, sample sizes.

    Records the pooling actually consumed (brief decision 4, quant
    C3) — both fixture seasons pooled under a stationarity assumption
    (docs/STATISTICAL-ASSUMPTIONS.md section 2e). ``competition`` names
    the sole competition of the consumed matches; if a caller pools
    several, they are listed comma-separated in sorted order.
    """

    competition: str
    seasons: tuple[str, ...]
    as_of: str
    sample_size: SampleSize


@dataclass(frozen=True)
class FittedParams:
    """One fitted Poisson model: parameters + full provenance (D2).

    ``teams`` is sorted; ``alpha``/``beta`` align to it element-wise and
    each sums to zero within SUM_TO_ZERO_EPSILON (identifiability).
    ``home_advantage`` is the estimated log-term h — never hardcoded
    (quant B3). ``input_digest`` is the sha256 of the canonical_state()
    serialization of the strictly pre-cutoff match set. A
    non-converged fit is a reported result: the status rides on the
    object and in its repr, and a parameter vector is never emitted
    without it.
    """

    model_version: str
    config: FitConfig
    pooling: PoolingRecord
    input_digest: str
    teams: tuple[str, ...]
    mu: float
    home_advantage: float
    alpha: tuple[float, ...]
    beta: tuple[float, ...]
    iterations: int
    convergence_status: ConvergenceStatus
    sample_size: SampleSize
    insufficient_data: bool
    insufficient_teams: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.model_version != MODEL_VERSION:
            raise ValueError(
                f"unknown model_version {self.model_version!r}; "
                f"this package fits {MODEL_VERSION!r}"
            )
        if len(self.teams) != len(self.alpha) or len(self.teams) != len(self.beta):
            raise ValueError("teams, alpha and beta must align element-wise")
        if self.teams != tuple(sorted(self.teams)):
            raise ValueError("teams must be sorted")


__all__ = [
    "ConvergenceStatus",
    "FitConfig",
    "FittedParams",
    "PoolingRecord",
    "SampleSize",
]
