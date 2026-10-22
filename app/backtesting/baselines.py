"""Chronological per-fixture baselines: pooled pre-cutoff H/D/A frequencies.

The ONLY module under app/backtesting that consumes realized scores
(AMENDMENT A1's review surface): every function here is underscore-
private (census-exempt by the probe-tested rule in
tests/test_temporal_integrity.py), so the walk-forward harness stays
the package's single public entry point.

Definition (STATISTICAL-ASSUMPTIONS section 12, design decision 7): per
target fixture, the pooled long-run home/draw/away frequencies over
realized matches with strictly ``date < fixture.date`` — uniform
weighting (one vote per historical match), no decay, no home/away
split, no train/validation split, no tuning. With no pre-cutoff match
the record is MISSING: n = 0, frequencies ``None``, status
``MISSING_NO_HISTORY`` — never a fabricated uniform (1/3, 1/3, 1/3),
never a full-sample fallback (those would see the future and leak it).

Weaknesses that ride every baseline here: tiny early n (0-3 for the
first date), synthetic hand-authored data, and the section-2f
independent-Poisson draw bias (the draw frequency is the baseline the
model is structurally weakest against). The IX-9 phrase "long-run" is
realized as the cumulative strictly-pre-cutoff window; a truly
full-sample "long-run" frequency would see the future and is banned.
"""

from __future__ import annotations

from typing import Sequence

from app.domain import Match

from .canonicalization import FixtureKey
from .record import BaselineRecord, BaselineStatus

__all__: list[str] = []


def _outcome_code(match: Match) -> str:
    """'H'/'D'/'A' by goal comparison of one realized match's score.

    Baselines pool realized outcomes of past matches, so this reads
    final scores; the pre-match prediction surfaces stay score-free.
    Unplayed input is an error, never guessed.
    """
    if match.score is None:
        raise ValueError(f"baseline cannot pool unplayed match: {match.natural_key}")
    if match.score.home > match.score.away:
        return "H"
    if match.score.home < match.score.away:
        return "A"
    return "D"


def _pre_cutoff(matches: Sequence[Match], cutoff_date: str) -> tuple[Match, ...]:
    """Select matches strictly earlier than ``cutoff_date``.

    Strict inequality is the leakage boundary: a match played on the
    target's own date is *not* history for that target, and neither is
    any later one. The caller passes the explicit cutoff; nothing here
    consults a clock or an environment variable.
    """
    if not cutoff_date:
        raise ValueError("baseline requires a non-empty cutoff date string")
    return tuple(match for match in matches if match.date < cutoff_date)


def _baseline_record(
    matches: Sequence[Match], target_key: FixtureKey, cutoff_date: str
) -> BaselineRecord:
    """Build the pooled-frequency baseline record for one target.

    The pooled frequencies are the uniform relative frequencies of
    home wins, draws, and away wins over *all* strictly pre-cutoff
    matches (goal comparison decides H/D/A). No decay, no weighting,
    no split, no tuning. With no pre-cutoff match the frequencies stay
    ``None`` — never a fabricated guess.
    """
    eligible = _pre_cutoff(matches, cutoff_date)
    n = len(eligible)
    if n == 0:
        return BaselineRecord(
            fixture_key=target_key,
            home_frequency=None,
            draw_frequency=None,
            away_frequency=None,
            n=0,
            status=BaselineStatus.MISSING_NO_HISTORY,
        )
    counts = {"H": 0, "D": 0, "A": 0}
    for match in eligible:
        counts[_outcome_code(match)] += 1
    return BaselineRecord(
        fixture_key=target_key,
        home_frequency=counts["H"] / n,
        draw_frequency=counts["D"] / n,
        away_frequency=counts["A"] / n,
        n=n,
        status=BaselineStatus.COMPUTED,
    )
