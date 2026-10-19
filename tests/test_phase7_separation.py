"""Phase 7 acceptance criteria 13-17: separation for app/decisions.

Scoring-token guard (13, A3 blocker), the vocabulary contract
extending the shared Phase 5 list (14), the AST import allowlist and
both-direction layering (15), the no-storage/API/schema/timestamp pins
vs the Phase 6 checkpoint (16), and the pinned A1-A4 amendments with a
clean full-tree scan (17). No scoring metric ships this phase.
"""

from __future__ import annotations

import ast
import dataclasses
import io
import keyword
import re
import subprocess
import tokenize
from pathlib import Path

import test_decisions as decision_contract
import test_fixtures_and_hygiene as hygiene
import test_phase5_separation as phase5
from app.decisions import build_decision_report
from app.decisions import constants as decision_constants
from app.decisions.canonicalization import canonical_payload
from app.decisions.record import DecisionReport, ScenarioComparison, ScenarioSpread
from app.forecasts import build_forecast
from app.storage import forecasts_db

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
DECISIONS_DIR = APP_DIR / "decisions"

# Criterion 16: the Phase 6 checkpoint (`cfde3a6`) the byte-diff pin is
# version-local to; a future change needs its own named amendment.
PHASE6_CHECKPOINT = "cfde3a67bc513890115106b2b774515e1735d4e6"
PROTECTED_PACKAGES = (
    "app/domain", "app/models", "app/forecasts", "app/scenarios",
    "app/simulation", "app/features", "app/storage", "app/api",
    "app/ingestion", "app/validation",
)

# Criterion 13 (A3): the pinned scoring-token tuple (extend-not-weaken)
# and the five quant-named families of ruling A1 it must cover.
SCORING_TOKENS = ("log_loss", "logloss", "brier", "rps", "hit_rate", "calibration")
QUANT_FAMILIES = ("log_loss", "brier", "rps", "hit_rate", "calibration")
_SCORING_PATTERN = re.compile(r"\b(" + "|".join(map(re.escape, SCORING_TOKENS)) + r")\b", re.IGNORECASE)

# Criterion 14 (A4): the shared Phase 5 list IMPORTED (single source of
# truth) plus exactly the Phase 7 advice-framing extension; the
# accuracy claims stay banned until Phases 9/11.
EXTENSION_TOKENS = ("recommendation", "pick", "tip", "advice")
DECISIONS_TOKENS = phase5.BANNED_BETTING_TOKENS + EXTENSION_TOKENS
_VOCAB_PATTERN = re.compile(r"\b(" + "|".join(map(re.escape, DECISIONS_TOKENS)) + r")\b", re.IGNORECASE)
_ACCURACY_PATTERN = re.compile(r"\b(validated|accurate|beating)\b", re.IGNORECASE)

# Criterion 15 (decision 1): the exact allowlists for app/decisions.
DECISIONS_STDLIB = {"__future__", "dataclasses", "typing", "enum", "json", "hashlib"}
DECISIONS_APP = {
    "app.domain", "app.models", "app.forecasts", "app.scenarios", "app.decisions",
}


def _decisions_files() -> list[Path]:
    files = sorted(DECISIONS_DIR.rglob("*.py"))
    assert files, "no Python files found under app/decisions/"
    return files


def _scoring_hits(text: str) -> list[str]:
    """Every scoring-token occurrence in raw source text (criterion 13)."""
    return [match.group(0) for match in _SCORING_PATTERN.finditer(text)]


def _vocab_hits(source: str) -> list[str]:
    """Criterion 14 matches over identifiers, strings, comments, docstrings.

    Tokenized rather than raw-matched for one documented reason: Python
    KEYWORD tokens are skipped — the shared list's ``return`` is
    statement syntax (Phase 5's AST scanner has the same semantics: an
    ``ast.Return`` is not a Name). Every STRING, COMMENT and non-keyword
    NAME occurrence still trips, strictly more than Phase 5 covers.
    """
    hits: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME and keyword.iskeyword(token.string):
            continue
        if token.type in (tokenize.NAME, tokenize.STRING, tokenize.COMMENT):
            match = _VOCAB_PATTERN.search(token.string)
            if match:
                hits.append(match.group(0))
    return hits


def _banned_field_name(name: str) -> bool:
    """Runtime field-name ban: tokens (word-boundary) or bare `value`."""
    return name == "value" or _VOCAB_PATTERN.search(name) is not None


def scan_decisions_imports(source: str, display: str, base_parts: list[str]) -> list[str]:
    """Criterion 15: package allowlists + the Phase 2 machinery.

    Delegates banned network/storage imports, purity (A1's
    PURE_PACKAGES strengthening), star imports, open(), and the
    wall-clock/environment rules to the unchanged Phase 2 scanner.
    """
    violations = hygiene.scan_source(source, display, base_parts, "app.decisions")
    tree = ast.parse(source, filename=display)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            targets = [hygiene.resolve_from(base_parts, node.level, node.module)]
        else:
            continue
        for target in targets:
            if target == "app" or target.startswith("app."):
                if not hygiene.allowed_app_import(target, DECISIONS_APP):
                    violations.append(
                        f"{display}: app import {target!r} outside allowed set "
                        f"(line {node.lineno})"
                    )
            elif target.split(".")[0] not in DECISIONS_STDLIB:
                violations.append(
                    f"{display}: import {target!r} outside the package stdlib "
                    f"allowlist (line {node.lineno})"
                )
    return violations


def test_no_scoring_quantities_anywhere_under_app_decisions() -> None:
    # Criterion 13 (A3 BLOCKER; extend-not-weaken): word-boundary,
    # case-insensitive guard over the RAW source text of every module.
    assert SCORING_TOKENS == ("log_loss", "logloss", "brier", "rps", "hit_rate", "calibration")
    # Superset pin: every quant-named family of ruling A1 is covered.
    assert set(QUANT_FAMILIES) <= set(SCORING_TOKENS)

    files = _decisions_files()
    for path in files:
        assert _scoring_hits(path.read_text(encoding="utf-8")) == [], path.name

    # Positive controls: each token flagged in every spelling form.
    for token in SCORING_TOKENS:
        for form in (token, token.upper(), token.capitalize()):
            for probe in (
                f"{form} = 0.5\n", f'x = "{form}"\n',
                f"# {form} of the model\n", f'"""{form} estimates."""\n',
            ):
                assert _scoring_hits(probe), (token, probe)

    # Negative controls: legitimate siblings stay clean.
    for clean in (
        "log_probs", "probability", "outcome_home",
        "dropped_mass", "insufficient", "scenario_matrix",
    ):
        for probe in (
            f"{clean} = 0.5\n", f'"{clean}"\n', f"# {clean}\n", f"total += {clean}\n",
        ):
            assert _scoring_hits(probe) == [], probe

    # Docstring discipline: "scoring" appears only in the sanctioned
    # honest negation, so no negation trips the guard above.
    for path in files:
        text = re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))
        if re.search(r"\bscoring\b", text, re.IGNORECASE):
            assert re.search(r"no scoring metric ships this phase", text, re.I), path.name


def test_decisions_vocabulary_contract() -> None:
    # Criterion 14 (A4): shared BANNED_BETTING_TOKENS IMPORTED from
    # test_phase5_separation (single source of truth), extended by
    # exactly the four advice-framing tokens; a word-boundary scan
    # over app/decisions/** finds none; no field name carries one.
    shared = phase5.BANNED_BETTING_TOKENS
    assert DECISIONS_TOKENS[: len(shared)] == shared  # extends, not copies
    assert DECISIONS_TOKENS[len(shared) :] == EXTENSION_TOKENS
    assert EXTENSION_TOKENS == ("recommendation", "pick", "tip", "advice")

    files = _decisions_files()
    for path in files:
        source = path.read_text(encoding="utf-8")
        assert _vocab_hits(source) == [], path.name
        # The Phase 5 scanner (imported machinery) also runs.
        assert phase5.scan_betting_tokens(source, str(path.relative_to(REPO_ROOT))) == [], path.name
        assert not _ACCURACY_PATTERN.search(source), path.name

    # Runtime: no record field name matches a token or equals `value`.
    for record_type in (DecisionReport, ScenarioComparison, ScenarioSpread):
        for field in dataclasses.fields(record_type):
            assert not _banned_field_name(field.name), field.name

    # Criterion 2's pinned contract: no pick-shaped or argmax field.
    assert tuple(f.name for f in dataclasses.fields(DecisionReport)) == decision_contract.REPORT_FIELD_NAMES
    assert tuple(f.name for f in dataclasses.fields(ScenarioComparison)) == decision_contract.COMPARISON_FIELD_NAMES
    assert tuple(f.name for f in dataclasses.fields(ScenarioSpread)) == decision_contract.SPREAD_FIELD_NAMES
    pick_shaped = {
        "pick", "favorite", "favourite", "argmax", "best", "winner",
        "favored", "recommended", "most_likely", "choice", "verdict",
    }
    side_fields = {
        "home", "away", "lambda_home", "lambda_away",
        "outcome_home", "outcome_draw", "outcome_away",
        "delta_home", "delta_draw", "delta_away",
    }
    for record_type in (DecisionReport, ScenarioComparison, ScenarioSpread):
        for field in dataclasses.fields(record_type):
            assert field.name not in pick_shaped, field.name
            if field.name in ("home", "away") or re.search(
                r"_(home|draw|away)$", field.name
            ):
                assert field.name in side_fields, field.name

    # The disclaimer's sanctioned negation: "not evidence of accuracy"
    # never matches `accurate` under word boundaries; the three
    # accuracy claims stay banned until Phases 9/11.
    assert "not evidence of accuracy" in decision_constants.DISCLAIMER
    assert not _ACCURACY_PATTERN.search(decision_constants.DISCLAIMER)

    # Negative controls: the OptionalValue TYPE name and .value /
    # .values() attribute access are ordinary domain vocabulary, never
    # flagged (the `value` ban is field-name-only, above).
    assert _vocab_hits("from app.domain import OptionalValue\n") == []
    assert _vocab_hits("x = record.value\n") == []
    assert _vocab_hits("d = record.values()\n") == []
    assert not _banned_field_name("kickoff")

    # Positive-control probes: every extension token flagged as both a
    # source token and a field name; the shared list's `return` stays
    # guarded in string form (keyword syntax is the only skip).
    for token in EXTENSION_TOKENS:
        assert _vocab_hits(f'payload = {{ "{token}": 1 }}\n'), token
        assert _vocab_hits(f"# {token} framing\n"), token
        assert _vocab_hits(f"{token} = 1\n"), token
        assert _banned_field_name(token), token
    assert _vocab_hits('payload = {"return": 1}\n')  # string form guarded
    assert _vocab_hits("def f():\n    return 1\n") == []  # keyword = syntax
    for token in shared:
        assert _vocab_hits(f'x = "{token}"\n'), token


def test_app_decisions_import_allowlist_and_layering_with_probes() -> None:
    # Criterion 15 (A1/A2; decision 1): the AST allowlist holds over
    # every module; layering is strict in BOTH directions — nothing
    # outside imports app.decisions — and Phase 2 scans it clean.
    for path in _decisions_files():
        violations = scan_decisions_imports(
            path.read_text(encoding="utf-8"),
            str(path.relative_to(REPO_ROOT)),
            hygiene.import_base_parts_for(path),
        )
        assert violations == [], "\n".join(violations)

    def probe(source: str, package: str = "app.decisions") -> list[str]:
        return scan_decisions_imports(source, "<probe>", ["app", package.split(".")[1]])

    # Positive controls: every banned import form flagged inside the
    # package — sibling app packages, filesystem/RNG, network/storage.
    for banned_import in (
        "from app.features import compute_features",
        "from app.storage import forecasts_db",
        "from app.api import create_server",
        "from app.simulation import simulate",
        "from app.ingestion import import_fixture",
        "from app.validation import validate_raw",
        "import http.server",
        "import urllib.parse",
        "from os import environ",
        "x = open('data.db')",
    ):
        assert probe(f"{banned_import}\n"), banned_import
    for banned_module in ("os", "sys", "pathlib", "io", "time", "random", "sqlite3"):
        assert probe(f"import {banned_module}\n"), banned_module

    # Negative controls: the exact sanctioned shapes stay clean.
    for allowed in (
        "from app.forecasts import Forecast",
        "from app.domain import Fixture",
        "from app.models import outcome_probs",
        "from app.scenarios import scenario_matrix",
        "from .constants import REPORT_VERSION",
        "from .record import DecisionReport",
        "import json\nimport hashlib\nfrom dataclasses import dataclass\n"
        "from typing import Sequence",
    ):
        assert probe(f"{allowed}\n") == [], allowed

    # Phase 2's wall-clock/environment machinery scans app/decisions
    # clean, and its probes still fire here (retargeted, not weakened).
    for path in _decisions_files():
        assert hygiene.scan_file(path) == [], path
    for probe_source, expected in (
        ("import datetime\nx = datetime.date.today()\n",
         "wall-clock access datetime.date.today"),
        ("import os\nx = os.environ['PATH']\n", "environment access os.environ"),
        ("import os\n", "in pure package"),  # A1 PURE_PACKAGES strengthening
    ):
        found = hygiene.scan_source(probe_source, "<probe>", ["app", "decisions"], "app.decisions")
        assert any(expected in violation for violation in found), expected

    # Reverse layering: no file OUTSIDE app/decisions imports the
    # package or names its entry point — nothing consumes reports;
    # persistence/serving is a future brief (storage/api/forecasts).
    for path in sorted(APP_DIR.rglob("*.py")):
        if path.parent == DECISIONS_DIR or DECISIONS_DIR in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        assert "app.decisions" not in text, path
        assert "build_decision_report" not in text, path
        for node in ast.walk(ast.parse(text, filename=str(path))):
            if isinstance(node, ast.Name):
                assert node.id != "build_decision_report", path
            if isinstance(node, ast.Attribute):
                assert node.attr != "build_decision_report", path

    # The machinery itself also flags the reverse direction.
    reverse = hygiene.scan_source(
        "from app.decisions import build_decision_report\n",
        "<probe>", ["app", "api"], "app.api",
    )
    assert any("outside allowed set" in violation for violation in reverse)


def test_no_storage_no_api_no_schema_no_timestamps() -> None:
    # Criterion 16 (A5): byte-diff pin — no protected package changed
    # since the Phase 6 checkpoint (no sqlite table or schema bump rode
    # in on this phase); plus the SQL/API/timestamp bans.
    result = subprocess.run(
        ["git", "diff", PHASE6_CHECKPOINT, "--", *PROTECTED_PACKAGES],
        cwd=REPO_ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", result.stdout
    assert result.stderr == "", result.stderr
    assert forecasts_db.SCHEMA_VERSION == 1  # unchanged

    # No SQL literal and no sqlite3/http/urllib import under app/
    # decisions (an in-process renderer touches no storage/network).
    sql_pattern = re.compile(r"\bCREATE\s+TABLE\b|\bINSERT\b|\bALTER\b", re.IGNORECASE)
    for path in _decisions_files():
        source = path.read_text(encoding="utf-8")
        assert not sql_pattern.search(source), path.name
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                roots = [(node.module or "").split(".")[0]]
            else:
                continue
            for banned in ("sqlite3", "http", "urllib"):
                assert banned not in roots, (path.name, banned)

    # No API route: build_decision_report appears nowhere under app/api,
    # and no timestamp field exists in any record of the contract.
    for path in sorted((APP_DIR / "api").rglob("*.py")):
        assert "build_decision_report" not in path.read_text(), path
    for record_type in (DecisionReport, ScenarioComparison, ScenarioSpread):
        for field in dataclasses.fields(record_type):
            assert field.name not in {
                "generated_at", "created_at", "timestamp", "generated",
            }, field.name

    # The canonical payload carries no ISO datetime or clock-time form.
    forecast = build_forecast(decision_contract.ALL_MATCHES, decision_contract.GOLDEN_FIXTURE)
    report = build_decision_report(forecast, scenarios=decision_contract._golden_scenarios(forecast))
    payload = canonical_payload(report)
    assert not re.search(r"\d{4}-\d{2}-\d{2}T", payload), payload
    assert not re.search(r"\b\d{2}:\d{2}:\d{2}\b", payload), payload


def test_amendments_pinned_and_full_tree_scan_clean() -> None:
    # Criterion 17 (A1-A4): exactly 12 keys; the eleven legacy values
    # exactly the Phase 1-6 sets (append-only convention protected); A1
    # exactly the sanctioned five; PURE_PACKAGES the four-package
    # strengthening; the exception map untouched; the A2/A3/A4 pin
    # updates in place; the full-tree scan completes with zero
    # violations and no KeyError.
    expected_legacy: dict[str, set[str]] = {
        "app": set(),
        "app.domain": {"app.domain"},
        "app.validation": {"app.domain", "app.validation"},
        "app.ingestion": {"app.domain", "app.validation", "app.ingestion"},
        "app.models": {"app.domain", "app.models"},
        "app.scenarios": {"app.domain", "app.models", "app.scenarios"},
        "app.simulation": {"app.models", "app.scenarios", "app.simulation"},
        "app.forecasts": {"app.domain", "app.models", "app.forecasts"},
        "app.storage": {"app.domain", "app.forecasts", "app.storage"},
        "app.api": {"app.domain", "app.forecasts", "app.storage", "app.api"},
    }
    assert len(hygiene.ALLOWED_APP_IMPORTS) == 12
    assert set(hygiene.ALLOWED_APP_IMPORTS) == set(expected_legacy) | {
        "app.features", "app.decisions",
    }
    for package, allowed in expected_legacy.items():
        assert hygiene.ALLOWED_APP_IMPORTS[package] == allowed, package
    # The eleven legacy values (ten + app.features) end exactly here.
    assert hygiene.ALLOWED_APP_IMPORTS["app.features"] == {
        "app.domain", "app.features",
    }
    # AMENDMENT A1's entry, verbatim.
    assert hygiene.ALLOWED_APP_IMPORTS["app.decisions"] == {
        "app.domain", "app.models", "app.forecasts", "app.scenarios", "app.decisions",
    }
    assert hygiene.PURE_PACKAGES == {
        "app.domain", "app.validation", "app.features", "app.decisions",
    }
    assert hygiene.BANNED_IMPORT_EXCEPTIONS == {
        "app.storage": {"sqlite3"}, "app.api": {"http"},
    }

    # The exception map is untouched: no exception exists for
    # app.decisions, so sqlite3 and http are flagged there too.
    for banned in ("sqlite3", "http.server", "urllib", "socket", "requests",
                   "httpx", "fastapi"):
        violations = hygiene.scan_source(f"import {banned}\n", "<probe>", [], "app.decisions")
        assert violations, banned

    # The A2/A3/A4 pin updates are verified IN PLACE: all three amended
    # separation files assert the exact 12-key universe with
    # app.decisions in the union, and neither the `== 10` nor the
    # `== 11` pin form survives anywhere.
    for name in (
        "test_phase4_separation.py",
        "test_phase5_separation.py",
        "test_phase6_separation.py",
    ):
        source = (REPO_ROOT / "tests" / name).read_text(encoding="utf-8")
        assert "len(hygiene.ALLOWED_APP_IMPORTS) == 12" in source, name
        assert '"app.decisions"' in source and '"app.features"' in source, name
        assert "len(hygiene.ALLOWED_APP_IMPORTS) == 10" not in source, name
        assert "len(hygiene.ALLOWED_APP_IMPORTS) == 11" not in source, name

    # The full-tree scan: every .py under app/ completes with zero
    # violations and no KeyError — no amendment relaxed any check.
    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    for path in app_files:
        violations = hygiene.scan_file(path)
        assert violations == [], f"{path}: {violations}"
