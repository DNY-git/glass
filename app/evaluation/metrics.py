"""The three evaluation metric formulas — the only legal forms (S13(a)).

Log loss is the natural logarithm of the realized outcome's probability;
Brier is the full three-outcome squared-error sum; RPS is the half-scaled
three-category ordinal score over the fixed H < D < A ordering.  All
three are one-prediction pure functions taking an (H, D, A) probability
triple plus the realized outcome code, plus one aggregate arithmetic mean
for the population containers.

A realized probability of exactly zero is a NAMED HARD REFUSAL for log
loss (ValueError): never a substitute value, never smoothed, never
repaired (constitution prohibition 4, S13(a)).  On the registered
populations the smallest component is far from zero, so the question
never arises in practice (criterion 6).

Uniform references, pinned: (1/3, 1/3, 1/3) gives Brier 2/3 against any
outcome and RPS 5/18 against H.  The scoreline-matrix variant of RPS is
rejected (S13(a)) and cannot be built here: this package imports no
scoreline machinery.
"""

import math
from typing import Sequence

OutcomeProbs = tuple[float, float, float]

# The ordinal outcome ordering: home < draw < away, fixed pre-score.
_OUTCOME_ORDER = ("H", "D", "A")


def _realized_index(outcome: str) -> int:
    """0/1/2 for "H"/"D"/"A"; an unknown code is a ValueError, not a default."""
    try:
        return _OUTCOME_ORDER.index(outcome)
    except ValueError:
        raise ValueError(f"unknown outcome code {outcome!r}") from None


def log_loss(outcome_probs: OutcomeProbs, outcome: str) -> float:
    """-ln(p) of the realized component, natural log, applied directly.

    A realized component of exactly 0.0 raises ValueError whose message
    contains "zero probability" — a hard refusal, never a substitute
    score (criterion 6).
    """
    p_realized = outcome_probs[_realized_index(outcome)]
    if p_realized == 0.0:
        raise ValueError(f"zero probability on realized outcome {outcome!r}")
    return -math.log(p_realized)


def brier(outcome_probs: OutcomeProbs, outcome: str) -> float:
    """The full three-outcome sum of squared errors: range [0, 2], uniform 2/3.

    No halving and no rescaling: sum over all three outcomes of
    (forecast - indicator)^2, where the realized outcome's indicator is 1.
    """
    index = _realized_index(outcome)
    total = 0.0
    for position, probability in enumerate(outcome_probs):
        indicator = 1.0 if position == index else 0.0
        total += (probability - indicator) ** 2
    return total


def rps(outcome_probs: OutcomeProbs, outcome: str) -> float:
    """The half-scaled three-category ordinal probability score: range [0, 1].

    1/2 * [(F_p(H) - F_o(H))^2 + (F_p(D) - F_o(D))^2] over cumulative
    one-hot indicators F_o and cumulative forecast F_p on the H < D < A
    ordering (the A term is identically zero, both cumulatives being 1).
    Uniform against H scores exactly 5/18.
    """
    index = _realized_index(outcome)
    running = 0.0
    total = 0.0
    for position in range(2):  # categories H and D only, per the K-1 rule
        running += outcome_probs[position]
        observed = 1.0 if position >= index else 0.0
        total += (running - observed) ** 2
    return 0.5 * total


def mean(values: Sequence[float]) -> float:
    """The arithmetic mean of a non-empty sequence (the aggregate helper).

    Plain sum/len in sequence order: the population triples are exactly
    this arithmetic over the stored contribution order.
    """
    if not values:
        raise ValueError("mean of an empty sequence")
    return sum(values) / len(values)
