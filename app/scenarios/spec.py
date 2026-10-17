"""Stage 7 SCENARIO EXPLORATION: the bounded scenario specification.

ONE op kind ships (Phase 4 brief decision 8): a multiplicative
transform on a named parameter — ``attack`` (alpha of a named team),
``defence`` (beta), or ``home_advantage`` (h of the fixture's home
side). Semantics are literal **parameter-scale** (developer decision,
docs/STATISTICAL-ASSUMPTIONS.md section 7d):

    alpha' = m * alpha,  beta' = m * beta,  h' = m * h

so a multiplier dulls (m < 1) or amplifies (m > 1) the parameter's
deviation from league mean — the direction of the effect on lambda
depends on the parameter's sign. Bounds are inclusive named constants
``MULTIPLIER_MIN``/``MULTIPLIER_MAX``; out-of-range, non-finite or
non-numeric multipliers raise ``ValueError`` — **never silent
clamping** (clamping would be fabricated data, constitution
prohibition 4). Every scenario is a labeled hypothetical: a non-empty
caller label is echoed on every output, transforms are canonically
ordered so shuffled inputs yield field-for-field identical objects,
duplicate ``(team, op)`` pairs are refused (ambiguity is never
averaged away), and scenarios are never averaged or ensembled — one
scenario per call, side by side, disagreement reported (brief
decision 10, criterion 14).

Pure: no randomness, no cell math, no wall clock, no I/O — and never
a constructor, clone, or modifier of ``FittedParams`` (AST-enforced by
tests/test_scenarios.py and tests/test_phase4_separation.py).
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass

from app.models import FittedParams

# Inclusive bounds of the single transform op kind (brief decision 8,
# developer answer to open question 1): a multiplier must satisfy
# MULTIPLIER_MIN <= m <= MULTIPLIER_MAX; anything else is a ValueError,
# never a clamp. Named and documented so every scenario output can echo
# the bounds it respected.
MULTIPLIER_MIN = 0.5
MULTIPLIER_MAX = 2.0


class TransformOp(enum.Enum):
    """The three named parameters a transform may scale (decision 8)."""

    ATTACK = "attack"
    DEFENCE = "defence"
    HOME_ADVANTAGE = "home_advantage"


@dataclass(frozen=True)
class Transform:
    """One bounded multiplicative transform of a named parameter.

    A plain immutable value record; all validation (bounds, finiteness,
    op type, label, duplicates, team membership) happens when a
    ``Scenario`` is constructed, so every scenario in existence is
    valid and no invalid transform can reach evaluation.
    """

    team: str
    op: TransformOp
    multiplier: float


def _validate_multiplier(multiplier: float) -> float:
    """Refuse a non-numeric, non-finite or out-of-bounds multiplier.

    Returns the multiplier as a float; raises ValueError otherwise.
    Out of range means strictly outside [MULTIPLIER_MIN,
    MULTIPLIER_MAX] — both bounds themselves are accepted (inclusive).
    No clamping path exists anywhere (constitution prohibition 4).
    """
    if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
        raise ValueError(
            f"multiplier must be a number, got {type(multiplier).__name__}"
        )
    value = float(multiplier)
    if not math.isfinite(value):
        raise ValueError(f"multiplier must be finite, got {value!r}")
    if not MULTIPLIER_MIN <= value <= MULTIPLIER_MAX:
        raise ValueError(
            f"multiplier {value!r} outside the documented inclusive bounds "
            f"[{MULTIPLIER_MIN}, {MULTIPLIER_MAX}] (never clamped)"
        )
    return value


@dataclass(frozen=True)
class Scenario:
    """A labeled, bounded hypothetical: baseline fit + transforms + label.

    ``baseline`` is embedded by reference, full provenance intact —
    a scenario never constructs, clones, or modifies a FittedParams
    (brief decision 9). ``transforms`` is canonicalized on
    construction: sorted by the spec key ``(team, op, multiplier)``
    (op ordered by its value), so shuffled caller orders produce
    field-for-field identical scenarios (criterion 13). Duplicate
    ``(team, op)`` pairs and unknown teams are refused as ValueError —
    ambiguity is never resolved silently, let alone averaged.
    """

    baseline: FittedParams
    transforms: tuple[Transform, ...]
    label: str

    def __post_init__(self) -> None:
        if not isinstance(self.baseline, FittedParams):
            raise ValueError(
                f"scenario baseline must be a FittedParams, got "
                f"{type(self.baseline).__name__}"
            )
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("scenario label must be a non-empty string")

        transforms = tuple(self.transforms)
        if not transforms:
            raise ValueError("a scenario needs at least one transform")

        for transform in transforms:
            if not isinstance(transform, Transform):
                raise ValueError(
                    f"scenario transforms must be Transform records, got "
                    f"{type(transform).__name__}"
                )
            if not isinstance(transform.team, str) or not transform.team:
                raise ValueError("transform team must be a non-empty string")
            if not isinstance(transform.op, TransformOp):
                raise ValueError(
                    f"transform op must be a TransformOp, got {transform.op!r}"
                )
            _validate_multiplier(transform.multiplier)

        seen: set[tuple[str, TransformOp]] = set()
        for transform in transforms:
            key = (transform.team, transform.op)
            if key in seen:
                raise ValueError(
                    f"duplicate transform for team {transform.team!r} with op "
                    f"{transform.op.value!r}: ambiguity is refused, never "
                    f"averaged or silently resolved"
                )
            seen.add(key)

        for transform in transforms:
            if transform.team not in self.baseline.teams:
                raise ValueError(
                    f"team {transform.team!r} is not in this fit's teams "
                    f"{self.baseline.teams!r}"
                )

        canonical = tuple(
            sorted(
                transforms,
                key=lambda t: (t.team, t.op.value, t.multiplier),
            )
        )
        object.__setattr__(self, "transforms", canonical)


def build_scenario(
    fitted: FittedParams,
    transforms: tuple[Transform, ...],
    *,
    label: str,
) -> Scenario:
    """Build a validated Scenario: canonical order, bounds, label, teams.

    All validation lives on ``Scenario`` (above), so the scenario
    object itself — not only this factory — is the invariant holder.
    Signature pinned by criterion 9/13: ``(fitted, transforms, *,
    label)`` — label is keyword-only and required (no default to
    forget).
    """
    return Scenario(baseline=fitted, transforms=tuple(transforms), label=label)


__all__ = [
    "MULTIPLIER_MAX",
    "MULTIPLIER_MIN",
    "Scenario",
    "Transform",
    "TransformOp",
    "build_scenario",
]
