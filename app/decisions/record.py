"""The frozen decision report and its two nested records (stage 8).

A ``DecisionReport`` is a deterministic, in-process VIEW of an existing
frozen ``Forecast``: a flat rendering of already cutoff-enforced output,
copied at full precision and chained back to the source forecast through
``forecast_version`` + ``forecast_content_hash``. It is generated in
process and never stored — no table, no schema, no route. The field
contract is pinned by Phase 7 criterion 2 (Phases 9+ depend on it);
``content_hash`` is computed at construction from every other field
under this package's own canonicalization spec of record, so no caller
ever supplies it. No scoring metric ships this phase. Uncertainty is
flag echo only — no interval, no standard error, no numeric reliability
band exists on a report — and every number is an in-sample estimate
restating the source forecast, never new evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain import OptionalValue
from app.models import ConvergenceStatus
from app.scenarios import Transform

from .canonicalization import content_hash as compute_content_hash


@dataclass(frozen=True)
class ScenarioComparison:
    """One LABELED hypothetical, side by side with its own deltas.

    ``label`` and ``transforms`` echo the scenario verbatim so every
    hypothetical is fully labeled; ``outcome_*`` are the analytic
    ``outcome_probs`` of this scenario's matrix at full precision;
    ``delta_*`` is the arithmetic difference between this entry and its
    own baseline report numbers (``entry.outcome_* - report.outcome_*``)
    — descriptive, computed at full precision, never rounded and never
    a ``value`` claim. Baseline numbers live once, in the report's own
    ``outcome_*`` fields, never duplicated per entry.
    """

    label: str
    transforms: tuple[Transform, ...]
    outcome_home: float
    outcome_draw: float
    outcome_away: float
    delta_home: float
    delta_draw: float
    delta_away: float


@dataclass(frozen=True)
class ScenarioSpread:
    """Per-outcome min/max/spread across labeled hypotheticals.

    The ONLY cross-scenario aggregation this system ships: ``minimum``
    and ``maximum`` over the entries' analytic probabilities for one
    outcome, and ``spread == maximum - minimum``. No mean, no average —
    a mean would be an invented ensemble (brief decision 7; criterion 9
    pins its absence). ``outcome`` is the fixed outcome name.
    """

    outcome: str
    minimum: float
    maximum: float
    spread: float


@dataclass(frozen=True)
class DecisionReport:
    """One frozen report over one frozen forecast (the exact D contract).

    Field set and order are pinned verbatim by Phase 7 criterion 2 —
    fixture block, provenance echoes, top-level flags, the fixed
    disclaimer, estimate numbers, scenario comparisons, spread,
    ``content_hash`` — in exactly that order. ``content_hash`` is
    computed at construction from every other field under the
    canonicalization spec of record; it is ``init=False`` because no
    caller ever supplies it. Flags ride TOP-LEVEL (never nested into a
    block): a screaming flag beside plausible-looking normalized
    numbers is the structural disagreement both kept visible.
    """

    # Fixture block (echoed; kickoff MISSING never defaulted).
    competition: str
    season: str
    date: str
    home: str
    away: str
    kickoff: OptionalValue
    as_of: str  # == forecast.as_of exactly (day granularity)
    # Provenance echoes (full provenance chains through the forecast).
    report_version: str  # the REPORT_VERSION contract constant
    model_version: str
    input_digest: str
    forecast_version: str
    forecast_content_hash: str
    # Pre-cutoff sample echoes.
    sample_matches: int
    sample_goals: int
    # Flags, top level.
    convergence_status: ConvergenceStatus
    insufficient_data: bool
    insufficient_teams: tuple[str, ...]
    # The fixed disclaimer (constants.DISCLAIMER, exactly).
    disclaimer: str
    # Estimate numbers — copies of the forecast's analytic values.
    lambda_home: float
    lambda_away: float
    max_goals: int
    dropped_mass: float  # truncation disclosure, not an uncertainty band
    outcome_home: float
    outcome_draw: float
    outcome_away: float
    # Labeled-hypothetical comparisons and the min/max spread.
    scenario_comparisons: tuple[ScenarioComparison, ...]
    scenario_spread: tuple[ScenarioSpread, ...] | None
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_hash", compute_content_hash(self))


__all__ = ["DecisionReport", "ScenarioComparison", "ScenarioSpread"]
