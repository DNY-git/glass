"""Calibration bins and descriptive diagnostics — the S13(c) block.

Five equal-width bins with fixed pre-score edges, pooled (forecast p,
realized indicator) pairs across the three outcomes, the one-number draw
aggregate, and the population-variance overdispersion diagnostic.
Everything here is DESCRIPTIVE: counts and frequencies only — no
smoothing, no merging of empty bins (an empty bin reports None for both
averages, never a fabricated 0.0), no fit or reliability claim (S13(c),
ADV-3/ADV-4/ADV-11).  Larger populations are a later phase's
registration.  The raw predicted-scoreline curve is NEVER reconstructed
from this module's inputs (ADV-11): pairs carry one probability and one
indicator, nothing scoreline-shaped.
"""

from dataclasses import dataclass
from typing import Sequence

# The five equal-width bin edges, fixed pre-score; last bin includes 1.0.
BIN_EDGES: tuple[float, ...] = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)

# The five-bin count used throughout (edges minus one, never merged).
_N_BINS = 5


@dataclass(frozen=True)
class CalibrationBin:
    """One bin's pinned triad: (n, mean forecast p, realized frequency).

    Both averages are None exactly when n is 0 — honest empty bins, and
    the triad's field set never gains or loses a member (criterion 10).
    """

    n: int
    mean_p: float | None
    realized_frequency: float | None


@dataclass(frozen=True)
class CalibrationTable:
    """One population's pooled table: always exactly five bins, no merging.

    ``n_matches`` is the scored population size, ``n_pairs`` the pooled
    pair count (three per scored match), both carried per S13(b)'s
    n-on-every-number rule.
    """

    n_matches: int
    n_pairs: int
    bins: tuple[CalibrationBin, ...]


@dataclass(frozen=True)
class OverdispersionDiagnostic:
    """Descriptive variance-versus-mean of realized team goals (ddof = 0).

    A number only: no test, no verdict, no significance of any kind
    (S13(c), decision 6(c)).
    """

    n: int
    mean: float
    variance: float


def bin_index(p: float) -> int:
    """The bin a forecast probability falls in; edges pinned pre-score.

    Left-inclusive and right-exclusive, except the last bin which
    includes 1.0; a probability outside the edges is a ValueError, never
    a silent default.
    """
    if p < BIN_EDGES[0] or p > BIN_EDGES[-1]:
        raise ValueError(f"probability {p!r} outside the pinned bin edges")
    index = 0
    while index < _N_BINS - 1 and p >= BIN_EDGES[index + 1]:
        index += 1
    return index


def calibration_table(
    pairs: Sequence[tuple[float, int]], *, n_matches: int
) -> CalibrationTable:
    """Pool (forecast p, realized indicator) pairs into the five pinned bins.

    Exactly three pairs per scored match are required (one per outcome);
    anything else is a ValueError rather than a quietly different
    denominator.  Empty bins are emitted, never merged away.
    """
    if len(pairs) != 3 * n_matches:
        raise ValueError(
            "expected three pairs per scored match "
            f"({3 * n_matches}), got {len(pairs)}"
        )
    counts = [0] * _N_BINS
    p_totals = [0.0] * _N_BINS
    indicator_totals = [0.0] * _N_BINS
    for p, indicator in pairs:
        slot = bin_index(p)
        counts[slot] += 1
        p_totals[slot] += p
        indicator_totals[slot] += indicator
    bins = tuple(
        CalibrationBin(
            n=counts[slot],
            mean_p=(p_totals[slot] / counts[slot]) if counts[slot] else None,
            realized_frequency=(
                indicator_totals[slot] / counts[slot]
            )
            if counts[slot]
            else None,
        )
        for slot in range(_N_BINS)
    )
    return CalibrationTable(
        n_matches=n_matches, n_pairs=len(pairs), bins=bins
    )


def draw_deficit(
    outcomes: Sequence[str], draw_probabilities: Sequence[float]
) -> float:
    """realized draw rate minus mean forecast draw probability (S13(b)).

    One number per population: the draw *aggregate*, never binned into
    the calibration table (decision 6(b)).
    """
    if not outcomes or len(outcomes) != len(draw_probabilities):
        raise ValueError("draw aggregate needs one forecast per scored match")
    realized_rate = sum(1 for code in outcomes if code == "D") / len(outcomes)
    mean_p = sum(draw_probabilities) / len(draw_probabilities)
    return realized_rate - mean_p


def overdispersion(goals: Sequence[int]) -> OverdispersionDiagnostic:
    """Population variance of realized team goals: denominator n (ddof = 0).

    Descriptive pairing of variance with mean only; it never becomes a
    weight, a rescaling, or a verdict on any other number (decision 6(c)).
    """
    if not goals:
        raise ValueError("overdispersion needs at least one goal observation")
    n = len(goals)
    average = sum(goals) / n
    spread = 0.0
    for goal in goals:
        spread += (goal - average) ** 2
    return OverdispersionDiagnostic(n=n, mean=average, variance=spread / n)
