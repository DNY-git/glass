"""Phase 4 acceptance criteria 1-8: seeded simulation over the matrix.

Signature pinning (required keyword-only seed, no RNG object, no
cutoff parameter to forget), bit-identity under a repeated seed, the
ONE fixed-seed golden with exact integer counts, the A4 statistical
tolerance bound at the 2e5 cap plus the draw-helper clamp probe,
dropped-mass propagation with the documented deviation bound, the
pinned SimulationResult field contract and mc_stderr expression, flag
ride-through (plausible-looking garbage stays flagged), and n_sims
validation with the default echo. Every run uses a fixed seed, so
each tolerance result is a deterministic fact of a recorded run —
never a flake. One criterion-adjacent strengthening closes the
baseline-mismatch gap: a scenario whose embedded baseline is not
value-equal to the given `fitted` raises ValueError, while a
value-equal (identity-distinct) copy is accepted.
"""

from __future__ import annotations

import dataclasses
import inspect
import math
import re
from pathlib import Path

import pytest

from app.domain import MatchCollection
from app.ingestion import import_fixture
from app.models import (
    MODEL_VERSION,
    ConvergenceStatus,
    FitConfig,
    FittedParams,
    PoolingRecord,
    SampleSize,
    fit,
    outcome_probs,
    scoreline_log_probs,
)
from app.scenarios import Transform, TransformOp, build_scenario
from app.simulation import DEFAULT_N_SIMS, SIM_VERSION, SimulationResult, simulate
from app.simulation.simulate import _draw_cell

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

FULL_AS_OF = "2025-12-31"
HOME = "Coralgate Athletic"
AWAY = "Emberfield Kestrels"

# One module-level fit shared by all eight tests (the fixture pool
# fitted at full history, same recipe as Phase 3's fixture_fit).
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())
FITTED = fit(ALL_MATCHES, FULL_AS_OF)

# Recorded golden counts (criterion 3): real output of
# simulate(FITTED, "Coralgate Athletic", "Emberfield Kestrels",
# seed=20261017, n_sims=10_000) on CPython 3.12.3, pasted verbatim.
# Golden literals are interpreter-local by documented policy: they are
# re-derived and re-documented (never widened) on interpreter change.
GOLDEN_SEED = 20261017
GOLDEN_N_SIMS = 10_000
GOLDEN_COUNTS = (5798, 2106, 2096)


def _walk_values(value):
    """Yield every nested value of frozen dataclasses/tuples (A7 walk)."""
    yield value
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            yield from _walk_values(getattr(value, field.name))
    elif isinstance(value, tuple):
        for item in value:
            yield from _walk_values(item)


def _string_values(value):
    for item in _walk_values(value):
        if isinstance(item, str):
            yield item


def test_simulate_signature_pins_required_keyword_only_seed_no_rng_object() -> None:
    # Criterion 1: inspect.signature(simulate) is exactly the pinned
    # shape — seed KEYWORD_ONLY with an EMPTY default (a missing seed
    # is a TypeError, never system entropy), no RNG-object parameter
    # anywhere, and no as_of/history/matches/time parameter to forget
    # (cutoff discipline lives in fit alone — A9).
    signature = inspect.signature(simulate)
    parameters = list(signature.parameters.values())
    assert [p.name for p in parameters] == [
        "fitted",
        "home",
        "away",
        "seed",
        "n_sims",
        "scenario",
    ]
    assert all(
        parameters[index].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        for index in range(3)
    )
    assert all(
        parameters[index].kind is inspect.Parameter.KEYWORD_ONLY
        for index in range(3, 6)
    )
    assert parameters[3].default is inspect.Parameter.empty  # seed: no default
    assert parameters[4].default == DEFAULT_N_SIMS
    assert parameters[5].default is None

    with pytest.raises(TypeError):
        simulate(FITTED, HOME, AWAY)  # missing required seed

    banned_names = (
        "rng",
        "random_state",
        "generator",
        "as_of",
        "history",
        "matches",
        "cutoff",
        "time",
    )
    for parameter in parameters:
        assert not any(banned in parameter.name for banned in banned_names), (
            parameter.name
        )

    assert isinstance(DEFAULT_N_SIMS, int) and DEFAULT_N_SIMS == 10_000
    assert isinstance(SIM_VERSION, str)
    assert SIM_VERSION == "sim-categorical-v1"


def test_simulate_bit_identity_double_run_and_seed_sensitivity() -> None:
    # Criterion 2: identical (fitted, home, away, seed=42, n_sims=1_000)
    # twice in one process -> field-for-field identical frozen output
    # and equal repr (PLAN layer 2); seed=1 vs seed=2 yields different
    # count triples — pinned to the counts recorded at build, so this
    # is a deterministic fact of the recorded seeds, not a flake.
    first = simulate(FITTED, HOME, AWAY, seed=42, n_sims=1_000)
    second = simulate(FITTED, HOME, AWAY, seed=42, n_sims=1_000)
    assert first == second
    assert repr(first) == repr(second)

    seed_one = simulate(FITTED, HOME, AWAY, seed=1, n_sims=1_000)
    seed_two = simulate(FITTED, HOME, AWAY, seed=2, n_sims=1_000)
    counts_one = (
        seed_one.counts_home,
        seed_one.counts_draw,
        seed_one.counts_away,
    )
    counts_two = (
        seed_two.counts_home,
        seed_two.counts_draw,
        seed_two.counts_away,
    )
    assert counts_one == (592, 205, 203)  # recorded at build (seed=1)
    assert counts_two == (600, 202, 198)  # recorded at build (seed=2)
    assert counts_one != counts_two
    assert first.counts_home + first.counts_draw + first.counts_away == 1_000


def test_simulate_golden_fixed_seed_exact_counts() -> None:
    # Criterion 3: the ONE golden pin — exact literal integer counts
    # from a real run (derivation = real output, pasted above), the
    # echoed seed/n_sims/sim_version literals, the analytic target
    # exactly equal to outcome_probs, and dropped_mass exactly equal
    # to the matrix's. Pins counts; never asserts frequency-vs-analytic.
    result = simulate(FITTED, HOME, AWAY, seed=GOLDEN_SEED, n_sims=GOLDEN_N_SIMS)
    assert (
        result.counts_home,
        result.counts_draw,
        result.counts_away,
    ) == GOLDEN_COUNTS
    assert result.seed == GOLDEN_SEED == 20261017
    assert result.n_sims == GOLDEN_N_SIMS == 10_000
    assert result.sim_version == SIM_VERSION == "sim-categorical-v1"
    assert result.scenario is None

    matrix = scoreline_log_probs(FITTED, HOME, AWAY)
    assert result.analytic_outcome == outcome_probs(matrix)
    assert result.dropped_mass == matrix.dropped_mass


def test_simulate_frequencies_within_statistical_tolerance() -> None:
    # Criterion 4: one run at the 2e5 cap with a fixed recorded seed;
    # for each outcome the A4 bound verbatim — never exact equality of
    # frequency and analytic probability anywhere.
    n_sims = 200_000
    result = simulate(FITTED, HOME, AWAY, seed=42, n_sims=n_sims)
    d = result.dropped_mass
    p = outcome_probs(scoreline_log_probs(FITTED, HOME, AWAY))
    frequencies = (
        result.counts_home / n_sims,
        result.counts_draw / n_sims,
        result.counts_away / n_sims,
    )
    for frequency, analytic in zip(frequencies, p):
        bound = 5 * math.sqrt(analytic * (1.0 - analytic) / n_sims) + d / (1.0 - d)
        assert abs(frequency - analytic) <= bound

    # Draw-helper edge probe (factorable because the helper takes u):
    # u at or past the final cumulative entry returns the LAST cell.
    # The first probe exercises the fp-epsilon clamp guard itself —
    # a table whose final entry sits below 1.0 makes bisect_left run
    # past the final index, and the clamp must land on the last cell.
    assert _draw_cell([0.25, 0.5, 0.9999999999999999], 1.0) == 2
    assert _draw_cell([0.25, 0.5, 1.0], 1.0) == 2  # u >= cumulative[-1]
    assert _draw_cell([0.5, 1.0], 0.7) == 1
    assert _draw_cell([0.5, 1.0], 0.0) == 0
    assert _draw_cell([0.5, 1.0], 0.4999) == 0


def test_simulate_dropped_mass_propagation_and_documented_deviation_bound() -> None:
    # Criterion 5: dropped_mass equals the baseline matrix's at full
    # precision; the fixture fit sits under the documented K=10 bound
    # (d <= 6e-4) and the sampling-deviation bound d/(1-d) <= 6.004e-4
    # — the same figure STATISTICAL-ASSUMPTIONS section 7 quotes
    # (docs/code agreement).
    matrix = scoreline_log_probs(FITTED, HOME, AWAY)
    result = simulate(FITTED, HOME, AWAY, seed=11, n_sims=1_000)
    assert result.dropped_mass == matrix.dropped_mass

    d = result.dropped_mass
    assert 0.0 < d <= 6e-4  # documented K=10 bound
    assert d / (1.0 - d) <= 6.004e-4  # documented sampling deviation


def test_simulation_result_field_contract_and_mc_stderr() -> None:
    # Criterion 6: the exact A9 field set (Phase 11/12 depend on it),
    # integer counts summing to n_sims, mc_stderr bit-exact in the
    # pinned expression order from the ANALYTIC p, frozen output,
    # tuple-only values, full-precision analytic floats, and strings
    # limited to sim_version / team names / provenance echoes.
    expected_fields = (
        "baseline",
        "scenario",
        "seed",
        "n_sims",
        "sim_version",
        "counts_home",
        "counts_draw",
        "counts_away",
        "analytic_outcome",
        "mc_stderr",
        "dropped_mass",
        "convergence_status",
        "insufficient_data",
        "insufficient_teams",
    )
    field_names = tuple(f.name for f in dataclasses.fields(SimulationResult))
    assert field_names == expected_fields

    n_sims = 1_000
    result = simulate(FITTED, HOME, AWAY, seed=42, n_sims=n_sims)
    counts = (result.counts_home, result.counts_draw, result.counts_away)
    assert all(type(count) is int for count in counts)
    assert sum(counts) == n_sims

    p = outcome_probs(scoreline_log_probs(FITTED, HOME, AWAY))
    assert result.analytic_outcome == p  # full-precision identical
    for k in range(3):
        assert result.mc_stderr[k] == math.sqrt(p[k] * (1.0 - p[k]) / n_sims)
    assert "mc_stderr" in field_names
    assert not any(
        "confidence" in name or "error" in name for name in field_names
    )

    with pytest.raises(AttributeError):
        result.seed = 1  # frozen

    for value in _walk_values(result):
        assert not isinstance(value, (dict, set, list)), type(value)

    # Strings: only sim_version, caller-supplied/team names, and
    # provenance echoes (model_version, 64-hex input_digest, pooling
    # record) — nothing timestamp-, path-, or environment-derived.
    assert re.fullmatch(r"[0-9a-f]{64}", FITTED.input_digest)
    allowed_strings = {
        SIM_VERSION,
        MODEL_VERSION,
        FITTED.input_digest,
        *FITTED.teams,
        FITTED.pooling.competition,
        *FITTED.pooling.seasons,
        FITTED.pooling.as_of,
    }
    for text in _string_values(result):
        assert text in allowed_strings, text
        assert not re.search(r"\d{2}:\d{2}", text)  # no clock time
        assert not re.search(r"\d{4}-\d\d-\d\dT", text)  # no ISO timestamp
    assert str(REPO_ROOT) not in repr(result)


def test_simulate_flags_ride_through_from_fitted() -> None:
    # Criterion 7: plausible-looking numbers from a flagged fit must
    # stay flagged. (a) the early-cutoff fixture fit (SINGULAR_SYSTEM
    # + insufficient flags, as measured in Phase 3); (b) a hand-built
    # NO_DATA FittedParams with teams; (c) a true empty-history NO_DATA
    # fit -> ValueError from team lookup, so an unflagged result is
    # impossible either way.
    early = fit(ALL_MATCHES, "2024-08-17")
    assert early.convergence_status is ConvergenceStatus.SINGULAR_SYSTEM
    assert early.insufficient_data is True
    assert early.insufficient_teams == early.teams
    early_home, early_away = early.teams[0], early.teams[1]
    early_matrix = scoreline_log_probs(early, early_home, early_away)
    early_result = simulate(early, early_home, early_away, seed=5, n_sims=1_000)
    assert early_result.convergence_status is early.convergence_status
    assert early_result.convergence_status is early_matrix.convergence_status
    assert early_result.insufficient_data == early.insufficient_data
    assert early_result.insufficient_teams == early.insufficient_teams
    assert (
        early_result.counts_home
        + early_result.counts_draw
        + early_result.counts_away
        == 1_000
    )

    # (b) NO_DATA-flagged fit carrying teams (public frozen dataclass,
    # Phase 3 golden precedent): it simulates and the flag rides.
    sample = SampleSize(matches=0, goals=0)
    no_data = FittedParams(
        model_version=MODEL_VERSION,
        config=FitConfig(),
        pooling=PoolingRecord(
            competition="Test Cup",
            seasons=("2024-25",),
            as_of="2025-01-01",
            sample_size=sample,
        ),
        input_digest="e" * 64,
        teams=("Ashford City", "Brookton United"),
        mu=0.0,
        home_advantage=0.0,
        alpha=(0.0, 0.0),
        beta=(0.0, 0.0),
        iterations=0,
        convergence_status=ConvergenceStatus.NO_DATA,
        sample_size=sample,
        insufficient_data=True,
        insufficient_teams=("Ashford City", "Brookton United"),
    )
    no_data_result = simulate(
        no_data, "Ashford City", "Brookton United", seed=6, n_sims=500
    )
    assert no_data_result.convergence_status is ConvergenceStatus.NO_DATA
    assert no_data_result.insufficient_data is True
    assert (
        no_data_result.counts_home
        + no_data_result.counts_draw
        + no_data_result.counts_away
        == 500
    )

    # (c) true empty-history NO_DATA fit: teams is (), so team lookup
    # raises ValueError — a result with lost flags cannot be produced.
    empty = fit([], FULL_AS_OF)
    assert empty.teams == ()
    with pytest.raises(ValueError):
        simulate(empty, HOME, AWAY, seed=6, n_sims=100)


def test_simulate_n_sims_validation_and_default_echo() -> None:
    # Criterion 8: n_sims < 1 and non-int inputs are ValueErrors
    # (never a silent coercion), and omitting n_sims echoes the
    # documented default on the result (A2).
    with pytest.raises(ValueError):
        simulate(FITTED, HOME, AWAY, seed=1, n_sims=0)
    with pytest.raises(ValueError):
        simulate(FITTED, HOME, AWAY, seed=1, n_sims=-5)
    with pytest.raises(ValueError):
        simulate(FITTED, HOME, AWAY, seed=1, n_sims="100")
    with pytest.raises(ValueError):
        simulate(FITTED, HOME, AWAY, seed=1, n_sims=10.0)

    result = simulate(FITTED, HOME, AWAY, seed=1)
    assert result.n_sims == DEFAULT_N_SIMS == 10_000
    assert (
        result.counts_home + result.counts_draw + result.counts_away
        == DEFAULT_N_SIMS
    )


def test_simulate_scenario_baseline_mismatch_refused_by_value_equality() -> None:
    # Criterion-adjacent strengthening (criterion 12's provenance
    # pairing, `SimulationResult.baseline == result.scenario.baseline`):
    # simulate()'s baseline-mismatch check — a scenario whose embedded
    # baseline does not equal the given `fitted` is refused rather than
    # silently reconciled. Pinned so a refactor that drops the check
    # fails loudly (tester finding F2).
    #
    # The mismatch scenario is built from the EARLY-CUTOFF fit (same
    # recipe as criterion 7) — value-distinct from FITTED (different
    # input_digest) yet otherwise perfectly valid for this fixture
    # (HOME and AWAY are in its teams), so without the check simulate
    # would happily return a result. First prove the scenario itself
    # is fine against its OWN baseline.
    early = fit(ALL_MATCHES, "2024-08-17")
    assert early != FITTED
    assert early.input_digest != FITTED.input_digest
    transforms = (Transform(HOME, TransformOp.ATTACK, 1.5),)
    foreign = build_scenario(early, transforms, label="early-cutoff baseline")
    own_baseline = simulate(
        early, HOME, AWAY, seed=3, n_sims=200, scenario=foreign
    )
    assert own_baseline.baseline == early
    assert own_baseline.convergence_status is early.convergence_status

    # The very same scenario paired with the full-history fit is a
    # ValueError — never a run labeled with the wrong provenance.
    with pytest.raises(ValueError):
        simulate(FITTED, HOME, AWAY, seed=3, n_sims=200, scenario=foreign)

    # Value equality, not identity: a value-equal copy of the fitted
    # (dataclasses.replace — a distinct object) is ACCEPTED, and the
    # output is field-for-field identical to the same scenario built
    # from FITTED itself.
    copy = dataclasses.replace(FITTED)
    assert copy is not FITTED and copy == FITTED
    label = "value-equal baseline"
    accepted = simulate(
        FITTED, HOME, AWAY, seed=3, n_sims=200,
        scenario=build_scenario(copy, transforms, label=label),
    )
    reference = simulate(
        FITTED, HOME, AWAY, seed=3, n_sims=200,
        scenario=build_scenario(FITTED, transforms, label=label),
    )
    assert accepted == reference
    assert accepted.baseline is FITTED
    assert (
        accepted.counts_home + accepted.counts_draw + accepted.counts_away
        == 200
    )
