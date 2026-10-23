"""The evidence gate: one digest-gated, read-only evaluation entry (IX-11).

``evaluate_predictions`` re-checks the caller-supplied run digest before
any metric computes (ADV-6), joins each prediction to its realized match
on the one-line natural-key dict with hard refusals on zero matches and
on more than one match (ADV-5, message carries the offending key), and
returns the pre-scored populations of S13(b) — 60 targets = 3 refusals +
27 flagged + 30 clean; PRIMARY = the 30 clean, SECONDARY = all 57 — as
absolute model and baseline triples side by side with n on every
container.  Never a difference, a scoreline variant, or a verdict
(ADV-8/ADV-2).  The three-clause flag predicate is deliberately
duplicated from the byte-pinned harness module (decision 4) and guarded
by the 27/30 population count pins.  Read-only by construction: this
package opens no storage, reads no clock, never writes anything.

``build_evaluation_record`` renders a result into the write-once record
payload: canonical JSON of the whole result, content-hashed, identity
fields echoed, no time field anywhere (decision 10, criterion 16).
"""

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from typing import Sequence

from app.backtesting import BaselineRecord
from app.domain import Match
from app.forecasts import Forecast

from .calibration import (
    CalibrationTable,
    OverdispersionDiagnostic,
    calibration_table,
    draw_deficit,
    overdispersion,
)
from .metrics import brier, log_loss, mean, rps

# The record contract version: echoed verbatim into every stored row.
EVALUATION_VERSION = 1

# A natural key as this package handles it: the shared 5-tuple shape.
_NATURAL_KEY = tuple[str, str, str, str, str]


class EvaluationConflictError(RuntimeError):
    """Same natural identity, different payload: the second row never lands.

    Raised by the storage writer (criterion 16) when the unique identity
    already holds a record whose content hash differs from the caller's.
    """


@dataclass(frozen=True)
class MetricTriple:
    """One population's three absolute metrics, with its n carried along."""

    n: int
    log_loss: float
    brier: float
    rps: float


@dataclass(frozen=True)
class ScoredContribution:
    """One scored target: key, realized outcome, and the model's three values."""

    natural_key: _NATURAL_KEY
    outcome: str
    log_loss: float
    brier: float
    rps: float


@dataclass(frozen=True)
class EvaluationAccounting:
    """Population accounting only — no metric container exists for n=60."""

    n_targets: int
    n_predictions: int
    n_refusals: int
    n_flagged: int
    n_clean: int
    refusal_keys: tuple[_NATURAL_KEY, ...]


@dataclass(frozen=True)
class PopulationScores:
    """Both absolute triples, contributions, and diagnostics for one population."""

    n_matches: int
    model: MetricTriple
    baseline: MetricTriple
    contributions: tuple[ScoredContribution, ...]
    calibration: CalibrationTable
    draw_deficit: float


@dataclass(frozen=True)
class EvaluationResult:
    """The whole gate result: accounting, both populations, goals diagnostic."""

    accounting: EvaluationAccounting
    primary: PopulationScores
    secondary: PopulationScores
    overdispersion: OverdispersionDiagnostic


@dataclass(frozen=True)
class EvaluationRecord:
    """The write-once evaluation record: identity echoed, payload hashed.

    ``content_hash`` is computed at construction from the payload bytes
    alone and is therefore init=False, mirroring the forecast contract;
    no clock field exists anywhere in this record.
    """

    evaluation_version: int
    run_digest: str
    fixture_file_sha256s: tuple[tuple[str, str], ...]
    payload: str
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "content_hash", sha256(self.payload.encode("utf-8")).hexdigest()
        )


@dataclass(frozen=True)
class _ScoredTarget:
    """Internal bundle for one scored target: joined triple plus its outcome."""

    key: _NATURAL_KEY
    outcome: str
    model_probs: tuple[float, float, float]
    baseline_probs: tuple[float, float, float]
    goals: tuple[int, int]
    flagged: bool
    contribution: ScoredContribution


def _is_flagged(forecast: Forecast) -> bool:
    """The harness's three-clause flag predicate, duplicated per decision 4.

    Same clauses, same order: insufficient pre-cutoff data, any missing
    team, non-CONVERGED status.  The population count pins (27/30) guard
    this copy against silent drift.
    """
    fitted = forecast.fitted
    return (
        fitted.insufficient_data
        or bool(fitted.insufficient_teams)
        or fitted.convergence_status.value != "CONVERGED"
    )


def _prediction_key(prediction: Forecast) -> _NATURAL_KEY:
    """The prediction's natural key, field order identical to Match's."""
    return (
        prediction.competition,
        prediction.season,
        prediction.date,
        prediction.home,
        prediction.away,
    )


def _canonical_order(key: _NATURAL_KEY) -> tuple[str, str, str, str, str]:
    """Date-first canonical order, matching Match.canonical_sort_key."""
    return (key[2], key[0], key[1], key[3], key[4])


def _outcome_of(match: Match) -> str:
    """"H"/"D"/"A" by goal comparison of one realized match's score."""
    if match.score.home > match.score.away:
        return "H"
    if match.score.home < match.score.away:
        return "A"
    return "D"


def _population_scores(targets: Sequence[_ScoredTarget]) -> PopulationScores:
    """Absolute triples, pooled calibration, and draw aggregate for one set.

    Every number here is a mean or frequency over exactly ``targets`` —
    never a paired value against the baseline (ADV-8).
    """
    n = len(targets)
    contributions = tuple(target.contribution for target in targets)
    model = MetricTriple(
        n=n,
        log_loss=mean([item.log_loss for item in contributions]),
        brier=mean([item.brier for item in contributions]),
        rps=mean([item.rps for item in contributions]),
    )
    baseline = MetricTriple(
        n=n,
        log_loss=mean(
            [log_loss(target.baseline_probs, target.outcome) for target in targets]
        ),
        brier=mean(
            [brier(target.baseline_probs, target.outcome) for target in targets]
        ),
        rps=mean([rps(target.baseline_probs, target.outcome) for target in targets]),
    )
    pairs: list[tuple[float, int]] = []
    for target in targets:
        p_home, p_draw, p_away = target.model_probs
        outcome = target.outcome
        pairs.append((p_home, 1 if outcome == "H" else 0))
        pairs.append((p_draw, 1 if outcome == "D" else 0))
        pairs.append((p_away, 1 if outcome == "A" else 0))
    return PopulationScores(
        n_matches=n,
        model=model,
        baseline=baseline,
        contributions=contributions,
        calibration=calibration_table(pairs, n_matches=n),
        draw_deficit=draw_deficit(
            [target.outcome for target in targets],
            [target.model_probs[1] for target in targets],
        ),
    )


def evaluate_predictions(
    predictions: Sequence[Forecast],
    baselines: Sequence[BaselineRecord],
    matches: Sequence[Match],
    *,
    run_digest: str,
    expected_run_digest: str,
) -> EvaluationResult:
    """Evaluate the walk-forward predictions against realized outcomes.

    The digest gate is the first statement (ADV-6): a mismatch is a
    ValueError naming run_digest, raised before any metric function can
    be called.  The join then refuses explicitly — zero matches and more
    than one match each raise a ValueError carrying the offending key —
    so no prediction is ever silently scored against the wrong game
    (ADV-5).  Reads only; the caller owns all persistence.
    """
    if run_digest != expected_run_digest:
        raise ValueError(
            f"run_digest {run_digest!r} does not match the expected "
            f"run_digest {expected_run_digest!r}"
        )

    match_lists: dict[_NATURAL_KEY, list[Match]] = {}
    for match in matches:
        match_lists.setdefault(match.natural_key, []).append(match)
    baseline_by_key = {
        baseline.fixture_key: baseline for baseline in baselines
    }

    ordered = sorted(
        predictions,
        key=lambda prediction: (
            prediction.date,
            prediction.competition,
            prediction.season,
            prediction.home,
            prediction.away,
        ),
    )
    targets: list[_ScoredTarget] = []
    for prediction in ordered:
        key = _prediction_key(prediction)
        found = match_lists.get(key, [])
        if not found:
            raise ValueError(f"no match for prediction natural key {key!r}")
        if len(found) > 1:
            raise ValueError(f"more than one match for natural key {key!r}")
        baseline = baseline_by_key.get(key)
        if baseline is None:
            raise ValueError(f"no baseline record for natural key {key!r}")
        base_home, base_draw, base_away = (
            baseline.home_frequency,
            baseline.draw_frequency,
            baseline.away_frequency,
        )
        if base_home is None or base_draw is None or base_away is None:
            raise ValueError(f"baseline has no computed value for key {key!r}")
        match = found[0]
        outcome = _outcome_of(match)
        model_probs = (
            prediction.outcome_home,
            prediction.outcome_draw,
            prediction.outcome_away,
        )
        contribution = ScoredContribution(
            natural_key=key,
            outcome=outcome,
            log_loss=log_loss(model_probs, outcome),
            brier=brier(model_probs, outcome),
            rps=rps(model_probs, outcome),
        )
        targets.append(
            _ScoredTarget(
                key=key,
                outcome=outcome,
                model_probs=model_probs,
                baseline_probs=(base_home, base_draw, base_away),
                goals=(match.score.home, match.score.away),
                flagged=_is_flagged(prediction),
                contribution=contribution,
            )
        )

    scored_keys = {_prediction_key(prediction) for prediction in ordered}
    target_keys = {baseline.fixture_key for baseline in baselines}
    refusal_keys = tuple(
        sorted(target_keys - scored_keys, key=_canonical_order)
    )
    n_targets = len(baselines)
    n_predictions = len(targets)
    n_flagged = sum(1 for target in targets if target.flagged)
    accounting = EvaluationAccounting(
        n_targets=n_targets,
        n_predictions=n_predictions,
        n_refusals=n_targets - n_predictions,
        n_flagged=n_flagged,
        n_clean=n_predictions - n_flagged,
        refusal_keys=refusal_keys,
    )

    secondary_targets = tuple(targets)
    primary_targets = tuple(target for target in targets if not target.flagged)
    secondary = _population_scores(secondary_targets)
    primary = _population_scores(primary_targets)
    diagnostic = overdispersion(
        [goal for target in secondary_targets for goal in target.goals]
    )
    return EvaluationResult(
        accounting=accounting,
        primary=primary,
        secondary=secondary,
        overdispersion=diagnostic,
    )


def build_evaluation_record(
    result: EvaluationResult,
    *,
    run_digest: str,
    fixture_file_sha256s: tuple[tuple[str, str], ...],
) -> EvaluationRecord:
    """Render a result into the write-once payload: canonical, clock-free.

    The payload is ``asdict`` of the whole result under sorted keys and
    tight separators, so re-serialization is the identical string and
    every float round-trips exactly (criterion 16).
    """
    payload = json.dumps(asdict(result), sort_keys=True, separators=(",", ":"))
    return EvaluationRecord(
        evaluation_version=EVALUATION_VERSION,
        run_digest=run_digest,
        fixture_file_sha256s=fixture_file_sha256s,
        payload=payload,
    )
