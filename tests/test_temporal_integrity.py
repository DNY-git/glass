"""Phase 8 acceptance criteria 1-8: temporal-integrity defenses (IX-8).

The poison-coverage registry + AST census (1-2), cutoff-at-source
bit-identity over unfiltered pools (3-4), same-day invisibility as
declared design (5), the snapshot immutability audit (6), the seedless
pin + app/ byte-pin (7), nothing-to-tune single-config (8). Defenses
only: no predictions, no baselines, no metrics ship this phase (A0).
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
import inspect
import math
import sqlite3
import subprocess
from pathlib import Path
from typing import Callable, Iterable, Mapping

import pytest

from app.decisions import build_decision_report
from app.domain import Fixture, Match, MatchCollection, OptionalValue, Score
from app.features import compute_features
from app.forecasts import ForecastIntegrityError, build_forecast
from app.ingestion import import_fixture
from app.models import FitConfig, fit
from app.storage import forecasts_db

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# Criterion 7: the app/ byte-pin is version-local to this checkpoint.
PHASE7_CHECKPOINT = "1e1c1ac"
HISTORY_PACKAGES = ("app/models", "app/forecasts", "app/features", "app/decisions")
SANCTIONED_RANDOM_MODULE = "app/simulation/simulate.py"

# The full synthetic pool (Phase 3): passed UNFILTERED; cutoffs inside.
ALL_MATCHES: tuple[Match, ...]
_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

# A real matchday: 3 real same-day siblings sit AT this cutoff; 27 pre.
CUTOFF_MATCHDAY = "2024-10-12"

# The golden target (Phase 5): dated after all 60 matches.
GOLDEN_FIXTURE = Fixture(
    competition="Obsidian Coast League", season="2025-26", date="2025-12-31",
    home="Coralgate Athletic", away="Thistledown Wanderers",
    kickoff=OptionalValue.missing(),
)
INJECTED_TEAM = "Northwind Pharos"  # never a fixture team: leaks if a cutoff fails


def _poison(date: str, home: str, away: str, home_goals: int, away_goals: int) -> Match:
    """A local in-schema poison match (per-file construction, Phase 3-7 pattern)."""
    return Match(
        competition="Obsidian Coast League", season="2025-26", date=date, home=home,
        away=away, score=Score(home_goals, away_goals), round_label=None,
        kickoff=OptionalValue.missing(), xg=OptionalValue.missing(),
    )


def _fixture_keyed_to(match: Match) -> Fixture:
    """The natural-key twin of a history match (the refusal target)."""
    return Fixture(
        competition=match.competition, season=match.season, date=match.date,
        home=match.home, away=match.away, kickoff=OptionalValue.missing(),
    )


# --- Criteria 1-2: the poison-matrix coverage registry machinery. ---
# A1 BLOCKER: the pinned five history-consuming entry points, each to
# its REAL, resolvable poison/tamper test (Phases 3-7 + this file's 6).
POISON_REGISTRY: dict[str, tuple[str, str]] = {
    "fit": ("test_poisson_fit", "test_poisoned_future_match_cannot_alter_parameters"),
    "build_forecast": ("test_forecasts", "test_build_forecast_poisoned_future_cannot_change_forecast"),
    "compute_features": ("test_features", "test_poisoned_future_cannot_change_features"),
    "build_decision_report": ("test_decisions", "test_poisoned_future_cannot_change_report"),
    "storage.get_forecast/verify_all": ("test_temporal_integrity", "test_snapshot_immutability_audit_update_delete_tamper"),
}

# The registry's matches-parameter subset = today's AST census of
# public `matches` entry points under app/ (criterion 1).
MATCHES_ENTRY_POINTS = ("fit", "build_forecast", "compute_features")


def validate_registry(registry: Mapping[str, tuple[str, str]]) -> dict[str, Callable[..., object]]:
    """Resolve every registry entry to a real test; LookupError on a gap.

    Pure over inputs: a gap entry fails the suite (PLAN 6, layer 4).
    """
    resolved: dict[str, Callable[..., object]] = {}
    for key in sorted(registry):
        module_name, test_name = registry[key]
        try:
            module = importlib.import_module(module_name)
        except ImportError as error:
            raise LookupError(f"registry entry {key!r}: module {module_name!r} not importable") from error
        test = getattr(module, test_name, None)
        if not (callable(test) and test_name.startswith("test_")):
            raise LookupError(f"registry entry {key!r}: no resolvable test {module_name}::{test_name}")
        resolved[key] = test
    return resolved


def census_matches_entry_points(sources: Iterable[tuple[str, str]]) -> set[str]:
    """Public functions taking a `matches` parameter, over (display, source)."""
    census: set[str] = set()
    for display, source in sources:
        tree = ast.parse(source, filename=display)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name.startswith("_"):
                continue  # only public functions; private helpers are exempt
            parameters = [a.arg for a in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)]
            if "matches" in parameters:
                census.add(node.name)
    return census


def uncatalogued(census: set[str], registered: set[str]) -> set[str]:
    """Census hits absent from the registry: fails until registered + poisoned."""
    return census - registered


def app_sources() -> list[tuple[str, str]]:
    """Census corpus: source of every .py under the REAL app/ tree."""
    return [(str(p.relative_to(REPO_ROOT)), p.read_text(encoding="utf-8")) for p in sorted(APP_DIR.rglob("*.py"))]


def random_references(source: str, display: str) -> list[str]:
    """Every `random` reference of any spelling; NO module allowlist.

    Flags aliased `import random`, aliased `from random import ...`,
    bare `random` names, and names bound by a random import alias —
    A3 defense-in-depth over Phase 4 criterion 16 (never weakened).
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    aliases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] == "random":
                    violations.append(f"{display}: randomness import {alias.name!r} (line {node.lineno})")
                    if alias.asname:
                        aliases.add(alias.asname)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or "").split(".")[0] == "random":
            violations.append(f"{display}: randomness import {(node.module or '')!r} (line {node.lineno})")
            for alias in node.names:
                if alias.name != "*":
                    aliases.add(alias.asname or alias.name)
    for node in ast.walk(tree):  # second pass: references after imports collected
        if isinstance(node, ast.Name) and (node.id == "random" or node.id in aliases):
            violations.append(f"{display}: random reference {node.id!r} (line {node.lineno})")
    return violations


def _docstrings(path: Path) -> str:
    """All docstrings of one module (module, class, function) joined."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    docs = [ast.get_docstring(tree) or ""]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            docs.append(ast.get_docstring(node) or "")
    return "\n".join(docs)


def test_poison_coverage_registry_bijection_and_census() -> None:
    # A1 BLOCKER: exactly five keys, each pinned to its named REAL
    # test; every entry RESOLVES (imported, not merely named).
    assert set(POISON_REGISTRY) == {
        "fit", "build_forecast", "compute_features", "build_decision_report",
        "storage.get_forecast/verify_all"}
    assert POISON_REGISTRY["fit"] == ("test_poisson_fit", "test_poisoned_future_match_cannot_alter_parameters")
    assert POISON_REGISTRY["build_forecast"] == ("test_forecasts", "test_build_forecast_poisoned_future_cannot_change_forecast")
    assert POISON_REGISTRY["compute_features"] == ("test_features", "test_poisoned_future_cannot_change_features")
    assert POISON_REGISTRY["build_decision_report"] == ("test_decisions", "test_poisoned_future_cannot_change_report")
    assert POISON_REGISTRY["storage.get_forecast/verify_all"] == ("test_temporal_integrity", "test_snapshot_immutability_audit_update_delete_tamper")
    resolved = validate_registry(POISON_REGISTRY)
    assert set(resolved) == set(POISON_REGISTRY)
    assert all(test.__name__.startswith("test_") for test in resolved.values())

    # The AST census of every PUBLIC `matches` parameter under app/
    # equals the registry's matches subset — a future entry fails here.
    sources = app_sources()
    assert sources, "no Python files found under app/"
    census = census_matches_entry_points(sources)
    assert census == set(MATCHES_ENTRY_POINTS)
    assert set(MATCHES_ENTRY_POINTS) <= set(POISON_REGISTRY)
    assert not uncatalogued(census, set(POISON_REGISTRY))


def test_poison_coverage_registry_negative_probes() -> None:
    # (a) A registry copy with an unresolvable extra entry FAILS
    # validation — a future entry point without a poison test fails.
    with pytest.raises(LookupError):
        validate_registry({**POISON_REGISTRY, "future_entry": ("test_temporal_integrity", "test_absent_poison")})
    with pytest.raises(LookupError):
        validate_registry({**POISON_REGISTRY, "future_entry": ("no_such_module_xyz", "test_x")})
    assert validate_registry(POISON_REGISTRY)  # the real registry validates

    # (b) The census flags an uncatalogued public `matches` entry point.
    probe = "<probe>"
    flagged = census_matches_entry_points([(probe, "def new_thing(matches):\n    return matches\n")])
    assert flagged == {"new_thing"}
    assert uncatalogued(flagged, set(POISON_REGISTRY)) == {"new_thing"}

    # (c) A source with no public `matches` function is clean.
    assert census_matches_entry_points([(probe, "def unrelated(value):\n    return value\n")]) == set()

    # (d) Private (underscore-prefixed) helpers are exempt from the census.
    assert census_matches_entry_points([(probe, "def _helper(matches):\n    return matches\n")]) == set()


def test_cutoff_at_source_fit_unfiltered_pool_bit_identical() -> None:
    # A1 (constitution Part V): fit over the FULL unfiltered pool (real
    # same-day siblings stay in; plus same-day/later extremes and a
    # future-only team) is bit-identical to the filtered pool; poisons
    # are never filtered at the call site and never raise.
    assert any(match.date == CUTOFF_MATCHDAY for match in ALL_MATCHES), "cutoff must be a real matchday"
    poisoned_pool = list(ALL_MATCHES) + [
        _poison(CUTOFF_MATCHDAY, INJECTED_TEAM, "Coralgate Athletic", 20, 0),
        _poison("2025-06-01", INJECTED_TEAM, "Emberfield Kestrels", 0, 19),
        _poison("2026-01-01", INJECTED_TEAM, "Harbourlight Comets", 18, 1),
    ]
    filtered_pool = [match for match in poisoned_pool if match.date < CUTOFF_MATCHDAY]
    assert len(filtered_pool) == 27
    assert len(poisoned_pool) > len(filtered_pool)
    unfiltered = fit(poisoned_pool, CUTOFF_MATCHDAY)  # the poisons never raise
    filtered = fit(filtered_pool, CUTOFF_MATCHDAY)
    clean = fit(ALL_MATCHES, CUTOFF_MATCHDAY)

    assert unfiltered == filtered  # frozen ==, field for field
    assert unfiltered == clean
    assert unfiltered.input_digest == filtered.input_digest
    assert unfiltered.convergence_status == filtered.convergence_status
    assert repr(unfiltered) == repr(filtered)
    assert unfiltered.sample_size.matches == 27
    assert INJECTED_TEAM not in unfiltered.teams  # no future-only team


def test_cutoff_at_source_forecast_and_features_unfiltered_pool_bit_identical() -> None:
    # A1: same unfiltered-vs-filtered bit-identity for build_forecast
    # and compute_features (incl. content_hash); key-in-history refusal.
    poisoned_pool = list(ALL_MATCHES) + [
        _poison(GOLDEN_FIXTURE.date, INJECTED_TEAM, "Emberfield Kestrels", 20, 0),
        _poison("2026-01-15", INJECTED_TEAM, "Harbourlight Comets", 0, 19),
        _poison("2026-06-30", INJECTED_TEAM, "Quarryhill Zenith", 18, 1),
    ]
    filtered_pool = [match for match in poisoned_pool if match.date < GOLDEN_FIXTURE.date]
    assert filtered_pool == list(ALL_MATCHES)  # all 60 real matches pre-cutoff

    forecast_unfiltered = build_forecast(poisoned_pool, GOLDEN_FIXTURE)
    forecast_filtered = build_forecast(filtered_pool, GOLDEN_FIXTURE)
    assert forecast_unfiltered == forecast_filtered  # field-for-field, incl. hash
    assert forecast_unfiltered.content_hash == forecast_filtered.content_hash
    assert forecast_unfiltered.fitted.input_digest == forecast_filtered.fitted.input_digest
    assert INJECTED_TEAM not in forecast_unfiltered.fitted.teams

    features_unfiltered = compute_features(poisoned_pool, GOLDEN_FIXTURE)
    features_filtered = compute_features(filtered_pool, GOLDEN_FIXTURE)
    assert features_unfiltered == features_filtered  # incl. content_hash
    assert features_unfiltered.content_hash == features_filtered.content_hash
    assert features_unfiltered.input_digest == features_filtered.input_digest

    target = max(ALL_MATCHES, key=lambda match: match.canonical_sort_key)
    colliding = _fixture_keyed_to(target)
    for entry in (build_forecast, compute_features):
        with pytest.raises(ValueError) as excinfo:
            entry(list(ALL_MATCHES), colliding)
        assert "its own history" in str(excinfo.value)


def test_same_day_invisibility_is_declared_design_not_bug() -> None:
    # A1 (KNOWN-LIMITATIONS Phase 5 item 1): a match dated EXACTLY at
    # the target date changes no field of any of the three outputs —
    # declared DESIGN, never fixed (a domain change would need a brief).
    same_day_cutoff = _poison(CUTOFF_MATCHDAY, INJECTED_TEAM, "Coralgate Athletic", 20, 0)
    fit_clean = fit(ALL_MATCHES, CUTOFF_MATCHDAY)
    fit_same_day = fit(list(ALL_MATCHES) + [same_day_cutoff], CUTOFF_MATCHDAY)
    assert fit_same_day == fit_clean
    assert fit_same_day.input_digest == fit_clean.input_digest
    assert fit_same_day.convergence_status == fit_clean.convergence_status
    assert repr(fit_same_day) == repr(fit_clean)

    same_day_target = _poison(GOLDEN_FIXTURE.date, INJECTED_TEAM, "Emberfield Kestrels", 0, 19)
    forecast_clean = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    forecast_same_day = build_forecast(list(ALL_MATCHES) + [same_day_target], GOLDEN_FIXTURE)
    assert forecast_same_day == forecast_clean
    assert forecast_same_day.content_hash == forecast_clean.content_hash

    features_clean = compute_features(ALL_MATCHES, GOLDEN_FIXTURE)
    features_same_day = compute_features(list(ALL_MATCHES) + [same_day_target], GOLDEN_FIXTURE)
    assert features_same_day == features_clean
    assert features_same_day.content_hash == features_clean.content_hash

    # Source-text pin: the day-granularity strict-`<` discipline is
    # stated in the builders' DOCSTRINGS — in-pattern phrasing pin.
    poisson_docs = _docstrings(APP_DIR / "models" / "poisson.py")
    assert "date < as_of" in poisson_docs
    assert "strictly" in poisson_docs
    assert "dated exactly at the cutoff" in poisson_docs
    builder_docs = _docstrings(APP_DIR / "forecasts" / "builder.py")
    assert "strict day-granularity date" in builder_docs
    assert "date < as_of" in builder_docs


def test_snapshot_immutability_audit_update_delete_tamper(tmp_path: Path) -> None:
    # IX-8: independent immutability re-execution (defense in depth):
    # raw UPDATE/DELETE -> IntegrityError; triggers dropped, a tampered
    # row fails BOTH read paths naming the key; re-armed = refused.
    db = tmp_path / "temporal-audit.db"
    writer = forecasts_db.open_forecasts_db(str(db))
    forecast = build_forecast(ALL_MATCHES, GOLDEN_FIXTURE)
    assert forecasts_db.insert_forecast(writer, forecast)
    writer.close()

    raw = sqlite3.connect(str(db))
    before = raw.execute("SELECT * FROM forecasts").fetchall()
    assert len(before) == 1
    with pytest.raises(sqlite3.IntegrityError) as update_error:
        raw.execute("UPDATE forecasts SET lambda_home = 0.0")
    assert "forecasts are immutable: UPDATE refused" in str(update_error.value)
    with pytest.raises(sqlite3.IntegrityError) as delete_error:
        raw.execute("DELETE FROM forecasts")
    assert "forecasts are immutable: DELETE refused" in str(delete_error.value)
    assert raw.execute("SELECT * FROM forecasts").fetchall() == before

    # The hostile path: drop BOTH write triggers, then tamper for real.
    raw.execute("DROP TRIGGER forecasts_immutable_update")
    raw.execute("DROP TRIGGER forecasts_immutable_delete")
    tampered = math.nextafter(forecast.lambda_home, math.inf)
    raw.execute("UPDATE forecasts SET lambda_home = ? WHERE home = ?", (tampered, forecast.home))
    raw.commit()
    raw.close()

    # Read-path hash recompute catches what triggers cannot: both
    # get_forecast and verify_all raise, naming the fixture key.
    key = (forecast.competition, forecast.season, forecast.date, forecast.home, forecast.away)
    reader = forecasts_db.open_read_connection(str(db))
    with pytest.raises(ForecastIntegrityError) as get_error:
        forecasts_db.get_forecast(reader, *key)
    message = str(get_error.value)
    assert "content hash mismatch" in message
    assert forecast.home in message and forecast.away in message
    reader.close()

    verifier = forecasts_db.open_read_connection(str(db))
    with pytest.raises(ForecastIntegrityError) as verify_error:
        forecasts_db.verify_all(verifier)
    assert forecast.home in str(verify_error.value) and forecast.away in str(verify_error.value)
    verifier.close()

    # Re-arm the triggers: raw writes are refused again, immediately.
    armed = sqlite3.connect(str(db))
    armed.execute(forecasts_db.IMMUTABLE_UPDATE_TRIGGER_DDL)
    armed.execute(forecasts_db.IMMUTABLE_DELETE_TRIGGER_DDL)
    armed.commit()
    with pytest.raises(sqlite3.IntegrityError):
        armed.execute("UPDATE forecasts SET lambda_home = 1.0")
    with pytest.raises(sqlite3.IntegrityError):
        armed.execute("DELETE FROM forecasts")
    armed.close()


def test_no_rng_in_history_consuming_modules_and_app_untouched() -> None:
    # A3 (decision 8): no `random` reference of any spelling under the
    # four history-consuming packages, with probes for every spelling.
    files = [p for package in HISTORY_PACKAGES for p in sorted((REPO_ROOT / package).rglob("*.py"))]
    assert files
    for path in files:
        assert random_references(path.read_text(encoding="utf-8"), str(path.relative_to(REPO_ROOT))) == [], path

    # Positive controls (NO allowlist in this scanner): every banned
    # spelling flags in each context; ordinary sources stay clean.
    for package in HISTORY_PACKAGES:
        for probe in ("import random\n", "from random import Random\n", "random.seed(1)\n"):
            assert random_references(probe, f"{package}/probe.py"), (package, probe)
    assert random_references("import math\nrate = math.exp(1.0)\n", "<probe>") == []

    # App-wide: `import random` — and any random reference — exists in
    # EXACTLY app/simulation/simulate.py, the sanctioned seeded home.
    import_files: set[str] = set()
    reference_files: set[str] = set()
    for path in sorted(APP_DIR.rglob("*.py")):
        rel = str(path.relative_to(REPO_ROOT))
        found = random_references(path.read_text(encoding="utf-8"), rel)
        if any("randomness import" in violation for violation in found):
            import_files.add(rel)
        if found:
            reference_files.add(rel)
    assert import_files == {SANCTIONED_RANDOM_MODULE}
    assert reference_files == {SANCTIONED_RANDOM_MODULE}

    # Byte-pin (decision 1): zero production code changed — `git diff
    # 1e1c1ac -- app/` exits 0 with empty output (version-local).
    result = subprocess.run(
        ["git", "diff", PHASE7_CHECKPOINT, "--", "app/"],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", result.stdout
    assert result.stderr == "", result.stderr


def test_single_config_identity_no_tuning_surface() -> None:
    # A2 BLOCKER: exactly one config identity — fit is exactly
    # (matches, as_of, *, config=None): names, order, kinds, default.
    parameters = inspect.signature(fit).parameters
    assert tuple(parameters) == ("matches", "as_of", "config")
    assert parameters["matches"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["as_of"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameters["config"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["config"].default is None
    assert not any(p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD) for p in parameters.values())

    # FitConfig's fields are exactly the five pinned names, in order.
    assert tuple(field.name for field in dataclasses.fields(FitConfig)) == (
        "newton_tol", "max_iterations", "damping", "max_goals", "ridge")
    # The existing unpenalized-MLE refusal (poisson.py:250), pinned.
    with pytest.raises(ValueError):
        fit(ALL_MATCHES, CUTOFF_MATCHDAY, config=FitConfig(ridge=0.5))

    # No second config/spec/variant/knob parameter anywhere; `config`
    # exists ONLY on fit; the other three keep Phase 5/7 signatures.
    banned = {"spec", "specs", "configs", "variant", "variants", "candidate", "seed"}
    for entry in (fit, build_forecast, compute_features, build_decision_report):
        names = set(inspect.signature(entry).parameters)
        assert not (names & banned), (entry.__name__, names & banned)
    for entry in (build_forecast, compute_features, build_decision_report):
        assert "config" not in inspect.signature(entry).parameters, entry.__name__
    assert tuple(inspect.signature(build_forecast).parameters) == ("matches", "fixture")
    assert tuple(inspect.signature(compute_features).parameters) == ("matches", "fixture")
    assert tuple(inspect.signature(build_decision_report).parameters) == ("forecast", "scenarios")
