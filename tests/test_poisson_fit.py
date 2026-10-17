"""Phase 3 acceptance criteria 1-8: the Poisson fitter.

Leakage (cutoff inside `fit`), poisoned-future immunity, deterministic
replay, reported non-convergence, insufficient-data flags, estimated
home advantage, the log-linear form with sum-to-zero and pooling
provenance, and frozen full-provenance output with the input digest.
Tests may use randomness; app/models may not (criterion 13).
"""

from __future__ import annotations

import dataclasses
import hashlib
import math
import random
import re
from collections import Counter
from pathlib import Path

import pytest

from app.domain import (
    IngestedRecord,
    Match,
    MatchCollection,
    OptionalValue,
    Provenance,
    RecordLocation,
    Score,
    canonical_state,
)
from app.ingestion import import_fixture
from app.models import (
    DAMPING,
    MAX_GOALS,
    MAX_ITERATIONS,
    MIN_MATCHES_PER_TEAM,
    MIN_TOTAL_GOALS,
    MIN_TOTAL_MATCHES,
    MODEL_VERSION,
    NEWTON_TOL,
    SUM_TO_ZERO_EPSILON,
    ConvergenceStatus,
    FitConfig,
    fit,
    scoreline_log_probs,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool: 2 seasons (2024-25 + 2025-26) of the
# Obsidian Coast League, 60 matches, 6 teams, 156 goals. Tests pass this
# list to `fit` UNFILTERED — the cutoff must be applied inside `fit`.
ALL_MATCHES: tuple[Match, ...]
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

FULL_AS_OF = "2025-12-31"  # after both seasons: all 60 matches pre-cutoff


def _pre_cutoff(as_of: str, matches: tuple[Match, ...] = ALL_MATCHES) -> list[Match]:
    """The test's own independent strict `date < as_of` filter."""
    return [match for match in matches if match.date < as_of]


def _extreme_match(date: str, home_goals: int, away_goals: int) -> Match:
    """An in-schema match with an extreme scoreline, for poisoning."""
    return Match(
        competition="Obsidian Coast League",
        season="2025-26",
        date=date,
        home="Coralgate Athletic",
        away="Thistledown Wanderers",
        score=Score(home_goals, away_goals),
        round_label=None,
        kickoff=OptionalValue.missing(),
        xg=OptionalValue.missing(),
    )


def test_fit_filters_history_internal_to_cutoff() -> None:
    # Criterion 1: `fit` receives the full unfiltered history with an
    # as_of inside it; the cutoff is enforced INSIDE the calculation,
    # not at the call site. Strict inequality: matches dated exactly at
    # the cutoff are refused, as are later ones.
    as_of = "2024-10-12"  # a date that actually occurs in the history
    assert any(match.date == as_of for match in ALL_MATCHES), "as_of must fall inside history"

    expected = _pre_cutoff(as_of)
    assert len(expected) == 27  # 9 matchdays x 3 matches before 2024-10-12
    expected_goals = sum(m.score.home + m.score.away for m in expected)

    fitted = fit(ALL_MATCHES, as_of)
    assert fitted.sample_size.matches == len(expected)
    assert fitted.sample_size.goals == expected_goals

    # A match dated exactly AT the cutoff (a 20-0, so inclusion would
    # also distort goals/parameters) and one dated after it are both
    # refused: sample sizes still equal the independent strict-filter
    # counts, and the whole object is field-for-field the same fit.
    poisoned = list(ALL_MATCHES) + [
        _extreme_match(as_of, 20, 0),
        _extreme_match("2024-10-13", 0, 20),
    ]
    independently_filtered = [
        m for m in poisoned if m.date < as_of
    ]  # the two injected matches do not qualify
    assert len(independently_filtered) == len(expected)

    refitted = fit(poisoned, as_of)
    assert refitted.sample_size == fitted.sample_size
    assert refitted == fitted


def test_poisoned_future_match_cannot_alter_parameters() -> None:
    # Criterion 2: extreme future scorelines dated at and after the
    # cutoff cannot alter anything about a fit for an earlier as_of —
    # frozen-dataclass equality (field for field), equal input_digest,
    # equal iterations, equal repr (quant G1).
    as_of = "2025-01-01"  # between the two seasons: 30 matches pre-cutoff
    clean = fit(ALL_MATCHES, as_of)
    assert clean.sample_size.matches == 30

    poisoned_list = list(ALL_MATCHES) + [
        _extreme_match(as_of, 20, 0),  # dated exactly at the cutoff
        _extreme_match("2025-06-01", 19, 1),  # dated after it
        _extreme_match("2026-01-01", 0, 18),  # far future
    ]
    poisoned_fit = fit(poisoned_list, as_of)

    assert poisoned_fit == clean
    assert poisoned_fit.input_digest == clean.input_digest
    assert poisoned_fit.iterations == clean.iterations
    assert repr(poisoned_fit) == repr(clean)
    assert poisoned_fit.teams == clean.teams  # no future-only team sneaks in


def test_fit_deterministic_replay_and_order_insensitive() -> None:
    # Criterion 3: parameters are a pure function of the arguments.
    # Same fit twice in one process: identical at full float precision
    # across every field including the digest. A shuffled copy of the
    # same matches: bit-identical (teams sorted, matches iterated in
    # Phase 2 canonical order; no randomness in app/models).
    first = fit(ALL_MATCHES, FULL_AS_OF)
    second = fit(ALL_MATCHES, FULL_AS_OF)
    assert first == second
    assert first.input_digest == second.input_digest
    assert repr(first) == repr(second)

    shuffled = list(ALL_MATCHES)
    random.Random(20261016).shuffle(shuffled)
    assert shuffled != list(ALL_MATCHES), "seeded shuffle must permute the input"

    replay = fit(shuffled, FULL_AS_OF)
    assert replay == first
    assert replay.input_digest == first.input_digest
    assert replay.mu == first.mu  # exact float equality, no tolerance
    assert replay.home_advantage == first.home_advantage
    assert replay.alpha == first.alpha
    assert replay.beta == first.beta


def test_convergence_status_is_reported_never_silent() -> None:
    # Criterion 4: the default full-fixture fit converges, with the
    # status on the object; forcing the iteration cap to 1 returns a
    # NON-converged status on the object and in its repr — a parameter
    # vector is never emitted without a status (quant B2/D2). Either
    # way the provenance fields (criterion 8) are all present, so the
    # flag can never be lost downstream.
    converged = fit(ALL_MATCHES, FULL_AS_OF)
    assert converged.convergence_status is ConvergenceStatus.CONVERGED
    assert converged.iterations >= 1
    assert converged.iterations < MAX_ITERATIONS  # well under the cap

    capped = fit(ALL_MATCHES, FULL_AS_OF, config=FitConfig(max_iterations=1))
    assert capped.config.max_iterations == 1  # the override is echoed
    assert capped.convergence_status is ConvergenceStatus.MAX_ITERATIONS
    assert "MAX_ITERATIONS" in repr(capped)
    assert capped.iterations == 1

    for fitted in (converged, capped):
        # All decision-5 provenance fields exist on either status.
        assert fitted.model_version == MODEL_VERSION
        assert fitted.config is not None
        assert fitted.pooling.as_of == FULL_AS_OF
        assert re.fullmatch(r"[0-9a-f]{64}", fitted.input_digest)
        assert fitted.teams
        assert fitted.sample_size.matches == 60
        assert isinstance(fitted.insufficient_data, bool)


def test_insufficient_data_flags_and_sample_size() -> None:
    # Criterion 5: thresholds are named documented constants; the flags
    # attach to the fitted output and are never hidden. Full pool passes
    # cleanly; a first-matchday cutoff trips the overall flag, sits
    # below the thresholds, and flags every team per-team.
    assert (MIN_MATCHES_PER_TEAM, MIN_TOTAL_MATCHES, MIN_TOTAL_GOALS) == (10, 20, 60)

    pooled = fit(ALL_MATCHES, FULL_AS_OF)
    assert pooled.sample_size.matches == 60
    assert pooled.sample_size.goals == 156  # measured fixture reality
    expected_goals = sum(m.score.home + m.score.away for m in ALL_MATCHES)
    assert pooled.sample_size.goals == expected_goals
    assert pooled.insufficient_data is False
    assert pooled.insufficient_teams == ()

    as_of = "2024-08-17"  # strictly before the second matchday
    early = fit(ALL_MATCHES, as_of)
    early_matches = _pre_cutoff(as_of)
    assert len(early_matches) == 3 < MIN_TOTAL_MATCHES
    assert early.sample_size.matches == len(early_matches)
    assert early.sample_size.goals == sum(
        m.score.home + m.score.away for m in early_matches
    ) < MIN_TOTAL_GOALS
    assert early.insufficient_data is True

    # Every team has exactly one pre-cutoff match — all below the
    # per-team threshold, all flagged, in sorted-team order.
    counts: Counter[str] = Counter()
    for match in early_matches:
        counts[match.home] += 1
        counts[match.away] += 1
    assert set(counts) == set(early.teams)
    assert all(counts[team] < MIN_MATCHES_PER_TEAM for team in early.teams)
    assert early.insufficient_teams == early.teams
    assert set(early.insufficient_teams) == {
        team for team, count in counts.items() if count < MIN_MATCHES_PER_TEAM
    }


def test_home_advantage_is_estimated_not_hardcoded() -> None:
    # Criterion 6: h is a fitted float on FittedParams; provenance
    # records it as ESTIMATED (the config carries no hardcoded home
    # constant); and its value is data-dependent — the early-cutoff fit
    # yields a different h than the full-pool fit (quant B3).
    pooled = fit(ALL_MATCHES, FULL_AS_OF)
    early = fit(ALL_MATCHES, "2024-08-17")

    assert isinstance(pooled.home_advantage, float)
    assert math.isfinite(pooled.home_advantage)
    assert not hasattr(pooled.config, "home_advantage")  # no hardcoded term in config

    assert pooled.home_advantage != early.home_advantage
    assert math.isfinite(early.home_advantage)


def test_model_form_sum_to_zero_and_pooling_record() -> None:
    # Criterion 7: the log-linear form reconstructs exactly — for every
    # ordered team pair, exp(mu + alpha_home + beta_away + h) and
    # exp(mu + alpha_away + beta_home) reproduce the evaluator's
    # lambdas bit-for-bit (the evaluator evaluates the same formula in
    # the same order); sum-to-zero holds within the documented epsilon;
    # teams are sorted with alpha/beta aligned; the pooling record
    # names the competition, both seasons, and the consumed cutoff.
    fitted = fit(ALL_MATCHES, FULL_AS_OF)

    for home_index, home in enumerate(fitted.teams):
        for away_index, away in enumerate(fitted.teams):
            if home_index == away_index:
                continue
            matrix = scoreline_log_probs(fitted, home, away)
            expected_home = math.exp(
                fitted.mu + fitted.alpha[home_index] + fitted.beta[away_index] + fitted.home_advantage
            )
            expected_away = math.exp(
                fitted.mu + fitted.alpha[away_index] + fitted.beta[home_index]
            )
            assert matrix.lambda_home == expected_home
            assert matrix.lambda_away == expected_away

    assert abs(sum(fitted.alpha)) <= SUM_TO_ZERO_EPSILON
    assert abs(sum(fitted.beta)) <= SUM_TO_ZERO_EPSILON
    assert fitted.teams == tuple(sorted(fitted.teams))
    assert len(fitted.alpha) == len(fitted.teams) == len(fitted.beta)

    assert fitted.pooling.competition == "Obsidian Coast League"
    assert fitted.pooling.seasons == ("2024-25", "2025-26")
    assert fitted.pooling.as_of == FULL_AS_OF
    assert fitted.pooling.sample_size == fitted.sample_size


def test_fitted_params_frozen_provenance_and_digest() -> None:
    # Criterion 8: frozen (assignment raises AttributeError); version,
    # config echo (tol, cap, damping, MAX_GOALS, ridge=None — the
    # pooled seasons ride the provenance echo per decision 5, in the
    # pooling record), input_digest equal to an independently recomputed
    # sha256 of the pre-cutoff canonical_state(), fitted floats exact,
    # no timestamp / absolute path / environment value anywhere.
    fitted = fit(ALL_MATCHES, FULL_AS_OF)

    with pytest.raises(AttributeError):
        fitted.mu = 0.0  # type: ignore[misc]

    assert fitted.model_version == "poisson-mle-v1"
    assert fitted.config.newton_tol == NEWTON_TOL
    assert fitted.config.max_iterations == MAX_ITERATIONS
    assert fitted.config.damping == DAMPING
    assert fitted.config.max_goals == MAX_GOALS
    assert fitted.config.ridge is None  # unpenalized MLE (C2)
    assert fitted.pooling.seasons == ("2024-25", "2025-26")  # pooled seasons echoed

    # Independent digest recomputation: the test's own strict filter +
    # the Phase 2 canonical serialization, hashed exactly per decision 5.
    pre = _pre_cutoff(FULL_AS_OF)
    assert len(pre) == 60
    collection = MatchCollection()
    for index, match in enumerate(pre):
        collection.add(
            IngestedRecord(
                match=match,
                provenance=Provenance(source_path="", sha256=""),
                location=RecordLocation(source_path="", index=index),
            )
        )
    expected_digest = hashlib.sha256(
        canonical_state(collection).encode("utf-8")
    ).hexdigest()
    assert fitted.input_digest == expected_digest

    # Fitted floats assert full precision: an identical replay matches
    # exactly (no tolerance) on every float, and all are finite.
    replay = fit(ALL_MATCHES, FULL_AS_OF)
    assert fitted.mu == replay.mu and math.isfinite(fitted.mu)
    assert fitted.home_advantage == replay.home_advantage
    assert fitted.alpha == replay.alpha
    assert fitted.beta == replay.beta

    # Determinism of the object: no wall-clock timestamp, no absolute
    # path, no environment value appears anywhere in it (the as_of
    # calendar date and the sha256 hex digest are required provenance;
    # a generation timestamp or path would not be).
    representation = repr(fitted)
    assert str(REPO_ROOT) not in representation
    assert not re.search(r"\d{2}:\d{2}", representation)  # no clock time
    assert not re.search(r"\d{4}-\d\d-\d\dT", representation)  # no ISO timestamp

    # Unpenalized contract: a non-None ridge is refused loudly, never
    # silently ignored or silently shrunk.
    with pytest.raises(ValueError):
        fit(ALL_MATCHES, FULL_AS_OF, config=FitConfig(ridge=0.5))
