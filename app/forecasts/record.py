"""The frozen forecast record and its integrity/conflict errors (stage 6).

A ``Forecast`` is a deterministic value object: identical
``(matches, fixture)`` + model version + config produce a field-for-
field identical record including ``content_hash``. There is no seed
field anywhere — Monte-Carlo quantities never touch a forecast; the
outcome probabilities stored are the analytic ones (STATISTICAL-
ASSUMPTIONS section 8b). Every number here is an in-sample point
estimate pending chronological evaluation, never evidence of accuracy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain import OptionalValue
from app.models import FittedParams

from .canonicalization import content_hash as compute_content_hash


class ForecastIntegrityError(RuntimeError):
    """A forecast's recomputed content hash disagrees with its stored one.

    Raised on mismatch, never warned about and never partially served
    (brief decision 5, criteria 10/11): tamper evidence by construction.
    """


class ForecastConflictError(RuntimeError):
    """Identity collision with different content — never an overwrite.

    Identical identity + identical content hash is an idempotent no-op;
    identical identity + different content hash is this hard error, with
    the original row untouched (brief decision 6, criterion 9).
    """


@dataclass(frozen=True)
class Forecast:
    """One immutable analytic forecast snapshot (the exact F2 contract).

    Field set and order are pinned by Phase 5 criterion 4 — Phases 9/11
    depend on them. ``content_hash`` is computed at construction from
    every other field under the canonicalization spec of record; it is
    init=False because no caller ever supplies it.
    """

    competition: str
    season: str
    date: str
    home: str
    away: str
    kickoff: OptionalValue  # fixture echo; MISSING never defaulted
    as_of: str  # == fixture.date exactly (day granularity, L1)
    fitted: FittedParams  # full object by value: all provenance
    lambda_home: float  # matrix essentials (disclosure + hash cover)
    lambda_away: float
    max_goals: int
    dropped_mass: float  # exact truncation mass outside the matrix
    outcome_home: float  # analytic outcome_probs — NEVER MC counts
    outcome_draw: float
    outcome_away: float
    forecast_version: str  # the FORECAST_VERSION contract constant
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_hash", compute_content_hash(self))


__all__ = ["Forecast", "ForecastConflictError", "ForecastIntegrityError"]
