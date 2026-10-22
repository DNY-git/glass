"""Phase 9 acceptance criteria 1-12: backtesting machinery (IX-9).

Criterion 1 is the A2 s11(b) test-first poison gate (written before any
harness output existed), doubling as AMENDMENT A1's registry poison
entry. Then: accounting (2), frozen recomputation + kickoff echo (3),
golden run digest (4), double-run idempotence (5), cutoff-at-source E3
form (6), the single-spec signature pin (7), the no-join surface scans
(8), hand-computed chronological baselines (9-10), caller-side
persistence (11), and the manifest contract + amendment pins (12).
Machinery only: no metric of any kind is computed here; n stays 0.
"""
from __future__ import annotations

import ast, dataclasses, hashlib, inspect, json, math, re, sqlite3
from pathlib import Path

import pytest

import test_fixtures_and_hygiene as hygiene
import test_phase7_separation as phase7
import test_temporal_integrity as temporal
import test_vocab_guards as vocab

from app.backtesting import (
    BACKTEST_VERSION, BaselineRecord, BaselineStatus, RefusalRecord,
    RunManifest, WalkForwardRun, run_walk_forward,
)
from app.decisions import build_decision_report
from app.domain import (
    Fixture, IngestedRecord, Match, MatchCollection, OptionalValue,
    Provenance, RecordLocation, Score, canonical_state,
)
from app.features import compute_features
from app.forecasts import (
    FORECAST_VERSION, Forecast, ForecastConflictError, build_forecast, config_identity,
)
from app.ingestion import import_fixture
from app.models import MODEL_VERSION, FitConfig, fit
from app.storage import forecasts_db

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKTESTING_DIR = REPO_ROOT / "app" / "backtesting"
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# The full synthetic pool (Phase 3): passed UNFILTERED; cutoffs inside.
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES: tuple[Match, ...] = tuple(r.match for r in _collection.records())
TARGETS = tuple(sorted(ALL_MATCHES, key=lambda m: m.canonical_sort_key))

FIRST_DATE = "2024-08-10"
# The three structural refusals: the first date's fixtures, canonical order.
FIRST_DATE_KEYS = (
    ("Obsidian Coast League", "2024-25", FIRST_DATE, "Coralgate Athletic", "Thistledown Wanderers"),
    ("Obsidian Coast League", "2024-25", FIRST_DATE, "Quarryhill Zenith", "Harbourlight Comets"),
    ("Obsidian Coast League", "2024-25", FIRST_DATE, "Silverpine Rovers", "Emberfield Kestrels"),
)
# Criterion 9 (E4): strictly-pre-cutoff n per target, all 60 — three
# targets per matchday: 0,0,0, 3,3,3, 6,6,6, ..., 57,57,57.
EXPECTED_NS = (
    0, 0, 0, 3, 3, 3, 6, 6, 6, 9, 9, 9, 12, 12, 12, 15, 15, 15,
    18, 18, 18, 21, 21, 21, 24, 24, 24, 27, 27, 27, 30, 30, 30,
    33, 33, 33, 36, 36, 36, 39, 39, 39, 42, 42, 42, 45, 45, 45,
    48, 48, 48, 51, 51, 51, 54, 54, 54, 57, 57, 57,
)
# GOLDEN PIN (criterion 4), derived from a REAL run of this code on the
# frozen checked-in fixtures (Phase 3-7 golden discipline):
#   run = run_walk_forward(ALL_MATCHES)
#   entries = [[[p.competition, p.season, p.date, p.home, p.away],
#               p.content_hash] for p in run.predictions]
#   sha256(json.dumps(entries, sort_keys=True, separators=(",", ":"),
#                    ensure_ascii=True).encode("utf-8")).hexdigest()
# -> the ordered (fixture key, content_hash) list of the 57 predictions,
# canonical serialization, sha256 hex. Version-local to
# backtest-walkforward-v1 + poisson-mle-v1 + these fixtures; re-derive
# and re-document on any change — never widen, never delete.
GOLDEN_RUN_DIGEST = "150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f"
# Fixture 4's pinned flags (criterion 2): only the three 2024-08-10
# matches are history, so every one of the six teams appears exactly
# once (< MIN_MATCHES_PER_TEAM) — hence the full sorted tuple.
FIXTURE4_TEAMS = (
    "Coralgate Athletic", "Emberfield Kestrels", "Harbourlight Comets",
    "Quarryhill Zenith", "Silverpine Rovers", "Thistledown Wanderers",
)


def _fixture_for(match: Match) -> Fixture:
    """The per-target Fixture: natural key + kickoff echo, never the score."""
    return Fixture(
        competition=match.competition, season=match.season, date=match.date,
        home=match.home, away=match.away, kickoff=match.kickoff,
    )


def _poison(date: str, home: str, away: str, hg: int, ag: int) -> Match:
    """An in-schema poison match (the Phase 3-8 per-file pattern)."""
    return Match(
        competition="Obsidian Coast League", season="2025-26", date=date, home=home,
        away=away, score=Score(hg, ag), round_label=None,
        kickoff=OptionalValue.missing(), xg=OptionalValue.missing(),
    )


def _canonical_entries(predictions) -> list:
    """The ordered (fixture key, content_hash) list, keys as arrays."""
    return [[[p.competition, p.season, p.date, p.home, p.away], p.content_hash] for p in predictions]


def _entries_digest(entries) -> str:
    """sha256 over the canonical serialization of an entries list."""
    return hashlib.sha256(
        json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()


def _flagged(forecast: Forecast) -> bool:
    """Exactly the section-5 flag set: insufficient data/teams or non-convergence."""
    fitted = forecast.fitted
    return bool(fitted.insufficient_data) or bool(fitted.insufficient_teams) or \
        fitted.convergence_status.value != "CONVERGED"


def _backtesting_sources() -> list[tuple[str, str]]:
    """Source of every .py under the real app/backtesting/ tree."""
    assert BACKTESTING_DIR.is_dir(), "app/backtesting/ must exist"
    return [
        (str(p.relative_to(REPO_ROOT)), p.read_text(encoding="utf-8"))
        for p in sorted(BACKTESTING_DIR.rglob("*.py"))
    ]


def _module_reference_violations(source: str, display: str, roots: tuple[str, ...]) -> list[str]:
    """Import or bare reference of any banned root module, probes both ways."""
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in roots:
                    violations.append(f"{display}: import {alias.name!r}")
                    if alias.asname:
                        aliases.add(alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            if (node.module or "").split(".")[0] in roots:
                violations.append(f"{display}: from-import {(node.module or '')!r}")
                for alias in node.names:
                    if alias.name != "*":
                        aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and (node.id in roots or node.id in aliases):
            violations.append(f"{display}: reference {node.id!r}")
    return violations


def _strict_pattern(tokens) -> re.Pattern[str]:
    """The Phase 8 strict-segment compilation form, reused verbatim."""
    return re.compile(
        r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, tokens)) + r")(?![A-Za-z0-9])",
        re.IGNORECASE,
    )


_JOIN_PATTERN = _strict_pattern(phase7.SCORING_TOKENS + vocab.OUTCOME_COMPARATIVE_TOKENS)
FORECAST_FIELDS = frozenset(field.name for field in dataclasses.fields(Forecast))


def _cooccurrence_violations(source: str, display: str) -> list[str]:
    """Functions touching BOTH a Forecast-field surface and `.score`.

    The mechanical form of "pairing a prediction field with a realized
    field" (decision 11): an attribute on a `.score` chain (e.g. the
    `.home` of `match.score.home`) is realized-field access, not a
    prediction-surface access; anything else named as a Forecast field
    is the prediction surface. Probes pin both directions below.
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        score_surface = forecast_surface = False
        for child in ast.walk(node):
            if not isinstance(child, ast.Attribute):
                continue
            if child.attr == "score":
                score_surface = True
            elif child.attr in FORECAST_FIELDS:
                receiver = child.value
                if not (isinstance(receiver, ast.Attribute) and receiver.attr == "score"):
                    forecast_surface = True
        if score_surface and forecast_surface:
            violations.append(f"{display}:{node.lineno} {node.name}")
    return violations


@pytest.fixture(scope="module")
def canonical_run() -> WalkForwardRun:
    """The canonical clean run, computed once and reused (decision 16)."""
    return run_walk_forward(ALL_MATCHES)


# --- Criterion 1 (A2 s11(b) test-first gate; A1's registry poison entry). ---
def test_poisoned_remaining_future_freezes_earlier_predictions() -> None:
    cutoff = "2025-08-09"  # mid-sample matchday (index 10 of 20, season 2's opener)
    assert cutoff in {match.date for match in ALL_MATCHES}
    clean = run_walk_forward(ALL_MATCHES)
    # Poison everywhere strictly beyond k's date: later real scorelines
    # turned extreme, an injected never-seen team (at later dates,
    # off-season, and far-future), and a same-day sibling added to a
    # later matchday.
    frozen_base = [m for m in ALL_MATCHES if m.date <= cutoff]
    beyond = [m for m in ALL_MATCHES if m.date > cutoff]
    assert beyond  # the poison surface is real history, not an empty branch
    poisoned = list(frozen_base)
    poisoned += [dataclasses.replace(m, score=Score(20, 0)) for m in beyond]
    injected_team = "Northwind Pharos"  # never a fixture team: leaks if a cutoff fails
    poisoned += [
        _poison("2025-09-06", injected_team, "Coralgate Athletic", 20, 0),  # same-day sibling
        _poison("2025-11-01", injected_team, "Emberfield Kestrels", 0, 19),
        _poison("2027-01-01", injected_team, "Harbourlight Comets", 18, 1),
    ]
    assert len(poisoned) > len(ALL_MATCHES)
    assert all(m.date > cutoff for m in poisoned[len(frozen_base):])
    poisoned_run = run_walk_forward(poisoned)  # the poison never raises out
    assert isinstance(poisoned_run, WalkForwardRun)
    frozen_targets = [m for m in TARGETS if m.date <= cutoff]
    assert len(frozen_targets) == 33  # eleven matchdays, three targets each

    clean_frozen = [p for p in clean.predictions if p.date <= cutoff]
    poisoned_frozen = [p for p in poisoned_run.predictions if p.date <= cutoff]
    assert len(poisoned_frozen) == len(clean_frozen)
    assert clean_frozen == poisoned_frozen  # field-for-field, incl. content_hash
    # The frozen predictions are the ordered PREFIX of each run's list.
    clean_flags = [p.date <= cutoff for p in clean.predictions]
    poisoned_flags = [p.date <= cutoff for p in poisoned_run.predictions]
    n = len(clean_frozen)
    assert clean_flags == [True] * n + [False] * (len(clean_flags) - n)
    assert poisoned_flags[:n] == [True] * n
    # Those targets' baselines are identical (incl. content hashes).
    clean_b = [b for b in clean.baselines if b.fixture_key[2] <= cutoff]
    poisoned_b = [b for b in poisoned_run.baselines if b.fixture_key[2] <= cutoff]
    assert clean_b == poisoned_b
    # Refusals for frozen targets are identical; nothing silently moved.
    frozen_refusals = [r for r in clean.refusals if r.fixture_key[2] <= cutoff]
    assert frozen_refusals == [r for r in poisoned_run.refusals if r.fixture_key[2] <= cutoff]
    assert len(frozen_refusals) == 3
    # The ordered (fixture key, content_hash) PREFIX and its canonical
    # PREFIX DIGEST are identical; targets beyond k may differ (that is
    # correct, not asserted away).
    clean_entries = _canonical_entries(clean.predictions)
    poisoned_entries = _canonical_entries(poisoned_run.predictions)
    assert clean_entries[:n] == poisoned_entries[:n]
    assert _entries_digest(clean_entries[:n]) == _entries_digest(poisoned_entries[:n])


# --- Criterion 2 (E1; A1): the auditable refusal/flagged/clean accounting.
def test_walk_forward_refusal_flagged_clean_accounting(canonical_run: WalkForwardRun) -> None:
    assert canonical_run.n_targets == 60
    assert canonical_run.n_refusals == 3
    assert canonical_run.n_flagged == 27
    assert canonical_run.n_clean == 30
    assert canonical_run.n_predictions == 57
    assert 60 == 3 + 27 + 30  # nothing silently skipped or dropped
    assert 57 == 27 + 30
    assert len(canonical_run.predictions) + len(canonical_run.refusals) == 60
    # The three refusals are exactly the first date's three fixtures,
    # each a first-class RefusalRecord carrying the original message.
    assert tuple(r.fixture_key for r in canonical_run.refusals) == FIRST_DATE_KEYS
    for refusal in canonical_run.refusals:
        assert isinstance(refusal, RefusalRecord)
        assert refusal.status == "REFUSED_NO_PRE_CUTOFF_HISTORY"
        assert "is not in this fit's teams" in refusal.message
    # Never a uniform: the refusal targets' baselines are MISSING (c10).
    assert all(b.status is BaselineStatus.MISSING_NO_HISTORY for b in canonical_run.baselines[:3])

    flagged = [p for p in canonical_run.predictions if _flagged(p)]
    clean = [p for p in canonical_run.predictions if not _flagged(p)]
    assert len(flagged) == canonical_run.n_flagged == 27
    assert len(clean) == canonical_run.n_clean == 30
    for prediction in clean:  # clean = emitted with none of the section-5 flags
        assert not prediction.fitted.insufficient_data
        assert prediction.fitted.insufficient_teams == ()
        assert prediction.fitted.convergence_status.value == "CONVERGED"
    # Spot-pin fixture 4's SINGULAR_SYSTEM-class flags (2024-08-17).
    fixture4 = next(
        p for p in canonical_run.predictions
        if p.date == "2024-08-17" and p.home == "Emberfield Kestrels"
    )
    assert fixture4.fitted.convergence_status.value == "SINGULAR_SYSTEM"
    assert fixture4.fitted.insufficient_data is True
    assert fixture4.fitted.insufficient_teams == FIXTURE4_TEAMS


# --- Criterion 3 (A3; A4): frozen recomputation with kickoff echo.
def test_every_prediction_is_the_frozen_recomputation_with_kickoff_echo(
    canonical_run: WalkForwardRun,
) -> None:
    # The Fixture type structurally has no score field (never copied).
    assert "score" not in {field.name for field in dataclasses.fields(Fixture)}
    for match in TARGETS:  # kickoff echoed from the source Match, all 60
        assert _fixture_for(match).kickoff == match.kickoff
    recomputed, refused = [], []
    for match in TARGETS:
        pool = [m for m in TARGETS if m.natural_key != match.natural_key]
        try:
            recomputed.append(build_forecast(pool, _fixture_for(match)))
        except ValueError:
            refused.append(match.natural_key)
    assert refused == list(FIRST_DATE_KEYS)
    # Field-for-field including content_hash, in canonical target order.
    assert recomputed == list(canonical_run.predictions)
    for prediction in canonical_run.predictions:
        assert dataclasses.is_dataclass(prediction) and prediction.__dataclass_params__.frozen
        assert len(prediction.content_hash) == 64


# --- Criterion 4 (A7 s11(c); golden discipline).
def test_run_digest_golden_pin_and_independent_rederivation(
    canonical_run: WalkForwardRun,
) -> None:
    assert canonical_run.manifest.run_digest == GOLDEN_RUN_DIGEST
    # Independent re-derivation: sha256 over the canonical serialization
    # of the ordered (fixture key, content_hash) list.
    entries = _canonical_entries(canonical_run.predictions)
    assert _entries_digest(entries) == GOLDEN_RUN_DIGEST
    # Per-prediction input_digest + content_hash ride the Forecast objects.
    for prediction in canonical_run.predictions:
        assert len(prediction.content_hash) == 64 and len(prediction.fitted.input_digest) == 64
        assert set(prediction.content_hash) <= set("0123456789abcdef")
        assert set(prediction.fitted.input_digest) <= set("0123456789abcdef")
    # The four version echoes, exactly.
    manifest = canonical_run.manifest
    assert manifest.backtest_version == BACKTEST_VERSION == "backtest-walkforward-v1"
    assert manifest.forecast_version == FORECAST_VERSION
    assert manifest.model_version == MODEL_VERSION
    assert manifest.model_version == canonical_run.predictions[0].fitted.model_version
    assert manifest.config_identity == config_identity(FitConfig())
    # The single model spec: every prediction carries the same versions.
    assert {p.fitted.model_version for p in canonical_run.predictions} == {MODEL_VERSION}
    assert {p.forecast_version for p in canonical_run.predictions} == {FORECAST_VERSION}
    # The full-pool history_canonical_state_digest, recomputed independently.
    collection = MatchCollection()
    for index, match in enumerate(TARGETS):
        collection.add(IngestedRecord(
            match=match, provenance=Provenance(source_path="", sha256=""),
            location=RecordLocation(source_path="", index=index),
        ))
    recomputed_history = hashlib.sha256(canonical_state(collection).encode("utf-8")).hexdigest()
    assert manifest.history_canonical_state_digest == recomputed_history


# --- Criterion 5 (s11(c); A3): double-run idempotence, frozen ==.
def test_double_run_idempotent_ordered_output(canonical_run: WalkForwardRun) -> None:
    second = run_walk_forward(ALL_MATCHES)
    assert second == canonical_run  # predictions/refusals/baselines/counts/manifest
    assert second.manifest.run_digest == canonical_run.manifest.run_digest
    assert second.baselines == canonical_run.baselines  # incl. content hashes
    assert tuple(p.content_hash for p in second.predictions) == tuple(
        p.content_hash for p in canonical_run.predictions
    )


# --- Criterion 6 (E3 form; constitution Part V).
def test_cutoff_at_source_unfiltered_pool_identical_and_key_refusal(
    canonical_run: WalkForwardRun,
) -> None:
    filtered_entries = []
    for match in TARGETS:
        pool = [m for m in TARGETS if m.natural_key != match.natural_key]
        fixture = _fixture_for(match)
        try:
            unfiltered = build_forecast(pool, fixture)  # harness form: minus target only
        except ValueError:
            continue  # a structural refusal — no prediction in either form
        filtered = build_forecast([m for m in pool if m.date < match.date], fixture)
        assert unfiltered == filtered  # field-for-field, incl. content_hash
        assert unfiltered.content_hash == filtered.content_hash
        assert unfiltered.fitted.input_digest == filtered.fitted.input_digest
        filtered_entries.append([[*match.natural_key], filtered.content_hash])
    # The digest over the pre-cutoff-filtered recomputations is the run digest.
    assert _entries_digest(filtered_entries) == canonical_run.manifest.run_digest
    # The underlying natural-key-in-history guard is unchanged.
    target = TARGETS[-1]
    with pytest.raises(ValueError) as excinfo:
        build_forecast(list(TARGETS), _fixture_for(target))
    assert "its own history" in str(excinfo.value)


# --- Criterion 7 (A2; criterion-8 extension, declared).
def test_single_model_spec_surface_pinned_no_config_loop() -> None:
    parameters = inspect.signature(run_walk_forward).parameters
    assert tuple(parameters) == ("matches", "fixture_file_sha256s", "interpreter_version")
    # The param-renaming ban, mechanized: first parameter named exactly `matches`.
    assert tuple(parameters)[0] == "matches"
    assert parameters["matches"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["fixture_file_sha256s"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["interpreter_version"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["matches"].default is inspect.Parameter.empty
    assert parameters["fixture_file_sha256s"].default == ()
    assert parameters["interpreter_version"].default is None
    assert not any(
        p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
        for p in parameters.values()
    )
    banned = {"spec", "specs", "config", "configs", "variant", "variants", "candidate", "seed", "best"}
    # The harness surface itself carries NO knob of any kind (design 13).
    assert not (set(parameters) & banned)
    # Phase 8 criterion 8's scan, extended to the five entry points
    # (declared): its banned set, plus `config`/`best` on every entry
    # except fit's sanctioned single-spec `config` identity.
    banned_entry = {"spec", "specs", "configs", "variant", "variants", "candidate", "seed"}
    for entry in (fit, build_forecast, compute_features, build_decision_report, run_walk_forward):
        names = set(inspect.signature(entry).parameters)
        assert not (names & banned_entry), (entry.__name__, names & banned_entry)
    for entry in (build_forecast, compute_features, build_decision_report, run_walk_forward):
        assert "config" not in inspect.signature(entry).parameters, entry.__name__
        assert "best" not in inspect.signature(entry).parameters, entry.__name__
    # Phase 8 criterion 8's legacy pins stay green here as well.
    assert tuple(inspect.signature(fit).parameters) == ("matches", "as_of", "config")
    assert tuple(inspect.signature(build_forecast).parameters) == ("matches", "fixture")
    assert tuple(inspect.signature(compute_features).parameters) == ("matches", "fixture")


# --- Criterion 8 (A1 BLOCKER): the no-join surface, mechanically.
def test_no_realized_result_join_surface() -> None:
    # (a) Source-token scan: Phase 8 scoring tokens + the new outcome-
    # comparative tokens, imported single-source — zero hits anywhere
    # under app/backtesting/.
    sources = _backtesting_sources()
    assert len(sources) == 6  # the five modules + __init__.py
    for display, text in sources:
        assert _JOIN_PATTERN.search(text) is None, display
        assert phase7._scoring_hits(text) == [], display
    # (b) Function-level co-occurrence AST scan: zero functions touch
    # both a Forecast field surface and .score.
    for display, text in sources:
        assert _cooccurrence_violations(text, display) == [], display
    # Positive-control probes, flagged both ways:
    assert _cooccurrence_violations(
        "def probe(forecast, match):\n    return forecast.outcome_home + match.score.home\n",
        "<probe>",
    )
    assert _cooccurrence_violations(
        "def probe(forecast):\n    return forecast.outcome_home\n", "<probe>"
    ) == []
    assert _cooccurrence_violations(
        "def probe(match):\n    return match.score.home\n", "<probe>"
    ) == []
    # (c) Public-surface census: run_walk_forward is the ONLY public
    # matches-parameter function; every baselines.py function is private.
    assert temporal.census_matches_entry_points(sources) == {"run_walk_forward"}
    baselines_source = next(text for d, text in sources if d.endswith("baselines.py"))
    public = [
        node.name
        for node in ast.walk(ast.parse(baselines_source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
        and node.col_offset == 0
    ]
    assert public == []
    # No random / time / datetime / os / sys reference anywhere under
    # app/backtesting/ (positive-control probes pin the scanners).
    for display, text in sources:
        assert temporal.random_references(text, display) == [], display
        assert _module_reference_violations(text, display, ("time", "datetime", "os", "sys")) == [], display
    assert _module_reference_violations("import os\n", "<probe>", ("os",))
    assert _module_reference_violations("from datetime import datetime\n", "<probe>", ("datetime",))
    assert _module_reference_violations("import sys as s\ns.exit()\n", "<probe>", ("sys",))
    assert _module_reference_violations("import json\nx = json.dumps({})\n", "<probe>", ("os",)) == []


# --- Criterion 9 (A5; hand-derived arithmetic over the real fixtures).
def test_baselines_chronological_hand_computed(canonical_run: WalkForwardRun) -> None:
    baselines = canonical_run.baselines
    assert len(baselines) == 60
    assert tuple(b.fixture_key for b in baselines) == tuple(m.natural_key for m in TARGETS)
    # Fixture 4 (2024-08-17): the three 2024-08-10 results 2-1 (H), 0-0
    # (D), 1-3 (A) -> exactly (1/3, 1/3, 1/3), n = 3, COMPUTED.
    fixture4 = baselines[3]
    assert fixture4.fixture_key == (
        "Obsidian Coast League", "2024-25", "2024-08-17",
        "Emberfield Kestrels", "Harbourlight Comets",
    )
    assert fixture4.n == 3
    assert fixture4.status is BaselineStatus.COMPUTED
    assert (fixture4.home_frequency, fixture4.draw_frequency, fixture4.away_frequency) == (
        1 / 3, 1 / 3, 1 / 3,
    )
    # Fixture 36 (2025-08-16): hand-computed counts H = 15, D = 8, A = 10
    # over the 33 strictly-pre-cutoff matches -> (15/33, 8/33, 10/33).
    fixture36 = baselines[35]
    assert fixture36.fixture_key == (
        "Obsidian Coast League", "2025-26", "2025-08-16",
        "Thistledown Wanderers", "Quarryhill Zenith",
    )
    assert fixture36.n == 33
    assert (fixture36.home_frequency, fixture36.draw_frequency, fixture36.away_frequency) == (
        15 / 33, 8 / 33, 10 / 33,
    )
    for record in baselines:
        if record.status is BaselineStatus.COMPUTED:
            assert record.n > 0
            total = record.home_frequency + record.draw_frequency + record.away_frequency
            assert abs(total - 1.0) <= 1e-12
    # The E4 n sequence, exactly.
    assert tuple(record.n for record in baselines) == EXPECTED_NS
    # Same-date siblings never contribute to each other (strict date <).
    n_by_date: dict[str, set[int]] = {}
    for match, record in zip(TARGETS, baselines):
        n_by_date.setdefault(match.date, set()).add(record.n)
    assert len(n_by_date) == 20 and all(len(ns) == 1 for ns in n_by_date.values())
    # Each record's content hash re-derives from its own canonical payload.
    for record in baselines:
        payload = {
            "away_frequency": record.away_frequency,
            "draw_frequency": record.draw_frequency,
            "fixture_key": list(record.fixture_key),
            "home_frequency": record.home_frequency,
            "n": record.n,
            "status": record.status.value,
        }
        expected = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        assert record.content_hash == expected


# --- Criterion 10 (A5 BLOCKER): MISSING at the first date's three.
def test_baselines_missing_at_first_date_fixtures(canonical_run: WalkForwardRun) -> None:
    for record in canonical_run.baselines[:3]:
        assert record.fixture_key in FIRST_DATE_KEYS
        assert record.n == 0
        assert record.status is BaselineStatus.MISSING_NO_HISTORY
        assert record.home_frequency is None
        assert record.draw_frequency is None
        assert record.away_frequency is None
        assert len(record.content_hash) == 64  # MISSING still carries a hash
    first = canonical_run.baselines[0]
    # Never the fake uniform (1/3, 1/3, 1/3), never a full-sample fallback:
    # a full-sample baseline would be non-None at target 1 — asserted absent.
    assert (first.home_frequency, first.draw_frequency, first.away_frequency) != (1 / 3, 1 / 3, 1 / 3)
    assert first.home_frequency is None


# --- Criterion 11 (A4 BLOCKER): caller-side persistence, idempotent.
def test_predictions_persisted_caller_side_idempotent_and_collision(
    canonical_run: WalkForwardRun, tmp_path: Path
) -> None:
    db = tmp_path / "walk-forward.db"
    writer = forecasts_db.open_forecasts_db(str(db))
    first_pass = [forecasts_db.insert_forecast(writer, p) for p in canonical_run.predictions]
    assert first_pass == [True] * 57  # store-level idempotence IS the run proof
    second_pass = [forecasts_db.insert_forecast(writer, p) for p in canonical_run.predictions]
    assert second_pass == [False] * 57  # zero INSERTs on the identical re-run
    reader = forecasts_db.open_read_connection(str(db))
    verified = forecasts_db.verify_all(reader)  # hash-verified on every row
    assert len(verified) == 57
    canonically_sorted = tuple(
        sorted(verified, key=lambda p: (p.date, p.competition, p.season, p.home, p.away))
    )
    assert canonically_sorted == canonical_run.predictions
    reader.close()
    # Collision: same identity, nextafter on outcome_home -> hard error,
    # the stored row untouched.
    target = canonical_run.predictions[0]
    mutated = dataclasses.replace(target, outcome_home=math.nextafter(target.outcome_home, math.inf))
    assert mutated.content_hash != target.content_hash
    with pytest.raises(ForecastConflictError):
        forecasts_db.insert_forecast(writer, mutated)
    after_collision = forecasts_db.verify_all(forecasts_db.open_read_connection(str(db)))
    assert tuple(
        sorted(after_collision, key=lambda p: (p.date, p.competition, p.season, p.home, p.away))
    ) == canonical_run.predictions
    writer.close()
    # Schema introspection: exactly the 21 pinned columns, SCHEMA_VERSION
    # 1, exactly one table, and NO baseline row/column/table anywhere.
    raw = sqlite3.connect(str(db))
    columns = tuple(row[1] for row in raw.execute("PRAGMA table_info(forecasts)"))
    assert columns == forecasts_db.COLUMN_NAMES and len(columns) == 21
    tables = tuple(row[0] for row in raw.execute("SELECT name FROM sqlite_master WHERE type = 'table'"))
    assert tables == ("forecasts",)
    assert not any("baseline" in column.lower() for column in columns)
    raw.close()
    assert forecasts_db.SCHEMA_VERSION == 1
    assert db.parent == tmp_path  # no DB file is ever committed; all writes under tmp_path


# --- Criterion 12 (A7; A1/A2/A3/A3' exactness pins).
def test_manifest_contract_no_timestamp_and_amendments_exact(
    canonical_run: WalkForwardRun,
) -> None:
    # The manifest field names are exactly the design-6 contract.
    assert tuple(field.name for field in dataclasses.fields(RunManifest)) == (
        "backtest_version", "forecast_version", "model_version", "config_identity",
        "history_canonical_state_digest", "fixture_file_sha256s",
        "interpreter_version", "run_digest",
    )
    # No timestamp field exists anywhere in the record surface.
    for record_type in (RunManifest, WalkForwardRun, BaselineRecord, RefusalRecord):
        names = [field.name for field in dataclasses.fields(record_type)]
        assert not any("time" in name or "stamp" in name or "clock" in name for name in names)
    # Caller-supplied identity fields are echoed verbatim; a changed
    # echo changes the manifest but NOT run_digest (the digest covers
    # only the ordered predictions list).
    sha256s = (("season-1.json", "a" * 64), ("season-2.json", "b" * 64))
    echoed = run_walk_forward(
        ALL_MATCHES, fixture_file_sha256s=sha256s, interpreter_version="CPython 3.12.0"
    )
    assert echoed.manifest.fixture_file_sha256s == sha256s
    assert echoed.manifest.interpreter_version == "CPython 3.12.0"
    assert echoed.manifest.run_digest == canonical_run.manifest.run_digest
    assert echoed.predictions == canonical_run.predictions
    assert echoed.manifest == dataclasses.replace(
        canonical_run.manifest,
        fixture_file_sha256s=sha256s,
        interpreter_version="CPython 3.12.0",
    )
    # None stays None, never fabricated; the default echo is empty.
    assert canonical_run.manifest.interpreter_version is None
    assert canonical_run.manifest.fixture_file_sha256s == ()
    # No time/datetime/os/sys reference exists in the package (AST).
    for display, text in _backtesting_sources():
        assert _module_reference_violations(text, display, ("time", "datetime", "os", "sys")) == [], display
    # AMENDMENT A1 exactness: the registry of six and the census of four.
    assert temporal.PHASE8_CHECKPOINT == "ea92667"
    assert set(temporal.POISON_REGISTRY) == {
        "fit", "build_forecast", "compute_features", "build_decision_report",
        "storage.get_forecast/verify_all", "run_walk_forward",
    }
    assert temporal.POISON_REGISTRY["run_walk_forward"] == (
        "test_backtesting", "test_poisoned_remaining_future_freezes_earlier_predictions",
    )
    assert temporal.MATCHES_ENTRY_POINTS == (
        "fit", "build_forecast", "compute_features", "run_walk_forward",
    )
    # AMENDMENT A2 exactness: the rescoped byte-pin's constants.
    assert set(temporal.PRE_EXISTING_APP) == {
        "app/__init__.py", "app/api", "app/decisions", "app/domain",
        "app/features", "app/forecasts", "app/ingestion", "app/models",
        "app/scenarios", "app/simulation", "app/storage", "app/validation",
    }
    assert "app/backtesting" not in temporal.PRE_EXISTING_APP
    # AMENDMENT A3/A3' exactness: thirteen keys, the self-inclusive
    # value, the five-package pure set.
    assert len(hygiene.ALLOWED_APP_IMPORTS) == 13
    assert hygiene.ALLOWED_APP_IMPORTS["app.backtesting"] == {
        "app.domain", "app.forecasts", "app.backtesting",
    }
    assert hygiene.PURE_PACKAGES == {
        "app.domain", "app.validation", "app.features", "app.decisions", "app.backtesting",
    }
