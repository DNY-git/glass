"""Phase 5 acceptance criteria 22-26: separation for the new packages.

The phase's OWN separation test (the hygiene file keeps its amended
rules and never grows again here): per-package import allowlists and
layering direction with positive+negative probes (22), the no-mutating-
SQL literal scan with the pinned trigger carve-out (23), the
betting-surface token scan over forecasts and api (24), the pinned
A1/A2 amendments with a clean relocated full-tree scan (25), and the
Phase 2 wall-clock/environment machinery re-asserted over the three
new packages (26). Reuses Phase 2's scan machinery — extended, never
weakened.
"""

from __future__ import annotations

import ast
import dataclasses
import re
from pathlib import Path

import test_fixtures_and_hygiene as hygiene
from app.forecasts import Forecast
from app.storage import forecasts_db

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
FORECASTS_DIR = APP_DIR / "forecasts"
STORAGE_DIR = APP_DIR / "storage"
API_DIR = APP_DIR / "api"

# Criterion 22: per-package stdlib + app allowlists (the brief's exact
# sets; `urllib` is whitelisted-but-unused in app.api, Phase 4's
# hashlib precedent — the Phase 2 ban on urllib stays fully active for
# every package, A2 probes pin it, so the entry can never be exercised).
PACKAGE_STDLIB: dict[str, set[str]] = {
    "app.forecasts": {"__future__", "dataclasses", "typing", "enum", "json", "hashlib"},
    "app.storage": {"__future__", "typing", "json", "sqlite3", "pathlib", "os"},
    "app.api": {"__future__", "typing", "json", "http", "urllib"},
}
PACKAGE_APP_IMPORTS: dict[str, set[str]] = {
    "app.forecasts": {"app.domain", "app.models", "app.forecasts"},
    "app.storage": {"app.domain", "app.forecasts", "app.storage"},
    "app.api": {"app.domain", "app.forecasts", "app.storage", "app.api"},
}

# Criterion 24: the shared banned betting-surface token list (single
# source of truth; tests/test_api.py criterion 20 imports it). Matched
# word-boundary case-insensitively — "insufficient" must never trip a
# bare "ci" substring check, and `.values()` is an attribute, not a
# literal.
BANNED_BETTING_TOKENS = (
    "odds",
    "odd",
    "stake",
    "kelly",
    "edge",
    "ev",
    "expected_value",
    "value_bet",
    "wager",
    "bet",
    "bookmaker",
    "confidence",
    "profit",
    "return",
    "bankroll",
)
_BETTING_PATTERN = re.compile(
    r"\b(" + "|".join(map(re.escape, BANNED_BETTING_TOKENS)) + r")\b", re.IGNORECASE
)

# Criterion 23: UPDATE/DELETE data STATEMENTS anywhere under app/ are
# violations — matched by statement shape (UPDATE <table> SET …, DELETE
# FROM …) in any casing and any string-literal form, so ordinary prose
# ("an update step below the tolerance") is not a statement — except the
# two schema-level immutability trigger DDLs of app/storage/forecasts_db.py,
# pinned verbatim below.
_MUTATING_SQL_PATTERN = re.compile(
    r"\bUPDATE\b[^\n]{0,120}?\bSET\b|\bDELETE\b[^\n]{0,120}?\bFROM\b",
    re.IGNORECASE,
)
PINNED_UPDATE_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS forecasts_immutable_update "
    "BEFORE UPDATE ON forecasts "
    "BEGIN SELECT RAISE(ABORT, 'forecasts are immutable: UPDATE refused'); END"
)
PINNED_DELETE_TRIGGER = (
    "CREATE TRIGGER IF NOT EXISTS forecasts_immutable_delete "
    "BEFORE DELETE ON forecasts "
    "BEGIN SELECT RAISE(ABORT, 'forecasts are immutable: DELETE refused'); END"
)
_TRIGGER_DDL_LITERALS = {
    forecasts_db.IMMUTABLE_UPDATE_TRIGGER_DDL,
    forecasts_db.IMMUTABLE_DELETE_TRIGGER_DDL,
}
_FORECASTS_DB_DISPLAY = "app/storage/forecasts_db.py"


def scan_phase5_imports(
    source: str, display: str, base_parts: list[str], package: str
) -> list[str]:
    """Criterion 22 violations in one module of a Phase 5 package.

    Stdlib allowlist + app allowlist + the Phase 2 banned-import sets
    relocated per AMENDMENT A2 (via the amended hygiene constants — the
    ban is package-scoped exception, never removed) + open() + the
    wall-clock/environment machinery resolved through Phase 2's alias
    handling.
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    stdlib = PACKAGE_STDLIB[package]
    app_allowed = PACKAGE_APP_IMPORTS[package]

    def complain(message: str, lineno: int) -> None:
        violations.append(f"{display}: {message} (line {lineno})")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = hygiene.resolve_from(base_parts, node.level, node.module)
            targets = [base]
            for alias in node.names:
                if alias.name == "*":
                    continue
                target = f"{base}.{alias.name}" if base else alias.name
                if target in hygiene.WALL_CLOCK_CALLS or hygiene.is_environment_path(
                    target
                ):
                    complain(f"banned import {target!r}", node.lineno)
        else:
            continue
        for target in targets:
            top_level = target.split(".")[0]
            # A2 relocation: the ban is unchanged except for exactly
            # the sanctioned package-scoped exceptions.
            if top_level in hygiene.BANNED_TOP_LEVEL_IMPORTS and top_level not in (
                hygiene.BANNED_IMPORT_EXCEPTIONS.get(package, set())
            ):
                complain(f"banned import {target!r}", node.lineno)
            if hygiene.is_environment_path(target):
                complain(f"banned import {target!r}", node.lineno)
            if (
                isinstance(node, ast.ImportFrom)
                and target in hygiene.BANNED_STAR_IMPORTS
                and any(alias.name == "*" for alias in node.names)
            ):
                complain(f"banned star import {target!r}", node.lineno)
            if target == "app" or target.startswith("app."):
                if not hygiene.allowed_app_import(target, app_allowed):
                    complain(f"app import {target!r} outside allowed set", node.lineno)
            elif top_level not in stdlib:
                complain(
                    f"import {target!r} outside the package stdlib allowlist",
                    node.lineno,
                )

    # No filesystem access in any Phase 5 package: no open() calls.
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            complain("open() call", node.lineno)

    # Wall clock and environment reads via Phase 2's alias machinery.
    aliases = hygiene.collect_aliases(tree, base_parts)
    inner_attributes = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or id(node) in inner_attributes:
            continue
        path = hygiene.dotted_attribute_path(node, aliases)
        if path is None:
            continue
        if path in hygiene.WALL_CLOCK_CALLS:
            complain(f"wall-clock access {path}", node.lineno)
        elif hygiene.is_environment_path(path):
            complain(f"environment access {path}", node.lineno)

    return violations


def scan_mutating_sql(source: str, display: str) -> list[str]:
    """Criterion 23 violations: UPDATE/DELETE string literals under app/.

    The scan targets UPDATE/DELETE data statements in any casing and
    any string-literal form. The ONLY carve-out is the file-scoped,
    verbatim-pinned pair of immutability-trigger DDL literals in
    app/storage/forecasts_db.py — the sanctioned RAISE(ABORT) bodies
    that enforce write-once at the schema level.
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if not _MUTATING_SQL_PATTERN.search(node.value):
            continue
        if display == _FORECASTS_DB_DISPLAY and node.value in _TRIGGER_DDL_LITERALS:
            continue
        violations.append(
            f"{display}: mutating SQL literal {node.value!r} (line {node.lineno})"
        )
    return violations


def scan_betting_tokens(source: str, display: str) -> list[str]:
    """Criterion 24 violations: banned tokens as string literals,
    identifiers (incl. dataclass field names), or dict-literal keys."""
    tree = ast.parse(source, filename=display)
    violations: list[str] = []

    def check(text: str, what: str, lineno: int) -> None:
        match = _BETTING_PATTERN.search(text)
        if match:
            violations.append(
                f"{display}: betting-surface {what} {text!r} (line {lineno})"
            )

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            check(node.value, "string literal", node.lineno)
        elif isinstance(node, ast.Name):
            check(node.id, "identifier", node.lineno)
        elif isinstance(node, ast.arg):
            check(node.arg, "parameter name", node.lineno)
        elif isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            check(node.name, "definition name", node.lineno)
    return violations


def scan_wall_clock_env(source: str, display: str, base_parts: list[str]) -> list[str]:
    """Criterion 26: the Phase 2 machinery (unmodified) over new files."""
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    aliases = hygiene.collect_aliases(tree, base_parts)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base = hygiene.resolve_from(base_parts, node.level, node.module)
            for alias in node.names:
                if alias.name == "*":
                    continue
                target = f"{base}.{alias.name}" if base else alias.name
                if target in hygiene.WALL_CLOCK_CALLS or hygiene.is_environment_path(
                    target
                ):
                    violations.append(f"{display}: banned import {target!r}")
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if hygiene.is_environment_path(alias.name):
                    violations.append(f"{display}: banned import {alias.name!r}")
    inner_attributes = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or id(node) in inner_attributes:
            continue
        path = hygiene.dotted_attribute_path(node, aliases)
        if path is None:
            continue
        if path in hygiene.WALL_CLOCK_CALLS:
            violations.append(f"{display}: wall-clock access {path}")
        elif hygiene.is_environment_path(path):
            violations.append(f"{display}: environment access {path}")
    return violations


def test_new_package_import_allowlists_and_layering_with_probes() -> None:
    # Criterion 22: the exact allowlists hold over every module of the
    # three new packages; layering direction is strict (no reverse
    # imports, Phase 1-4 packages untouched by Phase 5); probes pin
    # both directions; and the serving package never computes.
    for directory, package in (
        (FORECASTS_DIR, "app.forecasts"),
        (STORAGE_DIR, "app.storage"),
        (API_DIR, "app.api"),
    ):
        package_files = sorted(directory.rglob("*.py"))
        assert package_files, f"no Python files found under {directory}"
        violations = [
            violation
            for path in package_files
            for violation in scan_phase5_imports(
                path.read_text(),
                str(path.relative_to(REPO_ROOT)),
                hygiene.import_base_parts_for(path),
                package,
            )
        ]
        assert violations == [], "\n".join(violations)

    def probe(source: str, package: str) -> list[str]:
        return scan_phase5_imports(
            source, "<probe>", ["app", package.split(".")[1]], package
        )

    # Positive controls: the same banned forms flagged where banned.
    assert probe("import sqlite3\n", "app.forecasts")
    assert probe("import sqlite3\n", "app.api")
    assert probe("import http.server\n", "app.forecasts")
    assert probe("import http.server\n", "app.storage")
    assert probe("import urllib.parse\n", "app.api")  # A2: urllib banned everywhere
    assert probe("import os\n", "app.forecasts")
    assert probe("import os\n", "app.api")
    assert probe("import collections\n", "app.forecasts")  # outside stdlib allowlist
    assert probe("from app.storage import insert_forecast\n", "app.forecasts")
    assert probe("from app.api import create_server\n", "app.forecasts")
    assert probe("from app.api import create_server\n", "app.storage")

    # Negative controls: the sanctioned shapes stay clean.
    assert probe("import sqlite3\n", "app.storage") == []
    assert probe("import http.server\n", "app.api") == []
    assert probe("from app.forecasts import Forecast\n", "app.storage") == []
    assert probe("from app.domain import Fixture\n", "app.forecasts") == []
    assert probe("from app.storage import get_forecast\n", "app.api") == []
    legit = (
        "from __future__ import annotations\n"
        "import json\n"
        "from typing import Any\n"
        "from app.forecasts import Forecast\n"
        "def serve(forecast: Forecast) -> dict[str, Any]:\n"
        "    return json.loads('{}')\n"
    )
    assert probe(legit, "app.api") == []

    # app.models/app.scenarios/app/simulation stay untouched by Phase 5
    # imports (allowlists + a text guard over the unchanged files).
    for package in ("app.models", "app.scenarios", "app.simulation"):
        flagged = hygiene.scan_source(
            "from app.forecasts import Forecast\n", "<probe>", ["app", package.split(".")[1]], package
        )
        assert any("outside allowed set" in violation for violation in flagged), package
    for directory in ("models", "scenarios", "simulation"):
        for path in sorted((APP_DIR / directory).rglob("*.py")):
            text = path.read_text()
            assert "app.forecasts" not in text and "app.storage" not in text
            assert "app.api" not in text, path

    # Store-then-serve, AST + text: no generation logic in the API —
    # the builder name appears in no app/api source at all.
    for path in sorted(API_DIR.rglob("*.py")):
        text = path.read_text()
        assert "build_forecast" not in text, path
        for node in ast.walk(ast.parse(text, filename=str(path))):
            if isinstance(node, ast.Name):
                assert node.id != "build_forecast", path


def test_no_mutating_sql_under_app() -> None:
    # Criterion 23 (S1): no UPDATE/DELETE data statement literal
    # appears anywhere in the application layer, except the verbatim-
    # pinned immutability-trigger DDL pair of app/storage/forecasts_db.py.
    assert forecasts_db.IMMUTABLE_UPDATE_TRIGGER_DDL == PINNED_UPDATE_TRIGGER
    assert forecasts_db.IMMUTABLE_DELETE_TRIGGER_DDL == PINNED_DELETE_TRIGGER

    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    violations = [
        violation
        for path in app_files
        for violation in scan_mutating_sql(
            path.read_text(), str(path.relative_to(REPO_ROOT))
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str, display: str = "<probe>") -> list[str]:
        return scan_mutating_sql(source, display)

    # Positive controls: data statements in any casing, flagged.
    assert probe("SQL = 'UPDATE forecasts SET x = 1'\n")
    assert probe("sql = 'update forecasts set x = 1'\n")
    assert probe('Q = "DELETE FROM forecasts"\n')
    assert probe('Q = "delete from forecasts where x = 1"\n')
    assert probe('Q = "UPDATE forecasts SET a = 1, b = 2 WHERE c = 3"\n')
    # Negative controls: other statements and honest prose stay allowed.
    assert probe("Q = 'SELECT * FROM forecasts'\n") == []
    assert probe("Q = 'INSERT INTO forecasts (a) VALUES (1)'\n") == []
    assert probe("Q = 'CREATE TABLE forecasts (a)'\n") == []
    assert probe(
        "Q = \"CREATE TRIGGER t AFTER INSERT ON forecasts "
        "BEGIN SELECT RAISE(ABORT, 'no'); END\"\n"
    ) == []
    assert probe(
        "# the Newton fit applies an update step below NEWTON_TOL, then "
        "reports whether the step was accepted\n"
    ) == []
    # The carve-out is file-scoped and literal-exact: the sanctioned
    # trigger DDLs pass only in their own module (both directions
    # pinned), and a raw data statement in that same module is still
    # flagged — the carve-out is no blanket exemption. The probes wrap
    # each DDL in a Python string literal, exactly as it appears in the
    # module source.
    assert probe(f'TRIGGER = """{PINNED_UPDATE_TRIGGER}"""\n', _FORECASTS_DB_DISPLAY) == []
    assert probe(f'TRIGGER = """{PINNED_DELETE_TRIGGER}"""\n', _FORECASTS_DB_DISPLAY) == []
    assert probe("SQL = 'UPDATE forecasts SET x = 1'\n", _FORECASTS_DB_DISPLAY)


def test_no_betting_surface_tokens_in_forecasts_and_api() -> None:
    # Criterion 24 (A2): no banned betting-surface token appears as a
    # string literal, identifier, dataclass field name, or emitted JSON
    # key under app/forecasts/** and app/api/** — probes pin detection
    # and the legitimate `.values()` shape; runtime re-asserts the
    # record's own field names.
    for directory in (FORECASTS_DIR, API_DIR):
        package_files = sorted(directory.rglob("*.py"))
        assert package_files, f"no Python files found under {directory}"
        violations = [
            violation
            for path in package_files
            for violation in scan_betting_tokens(
                path.read_text(), str(path.relative_to(REPO_ROOT))
            )
        ]
        assert violations == [], "\n".join(violations)

    def probe(source: str) -> list[str]:
        return scan_betting_tokens(source, "<probe>")

    # Positive controls: every token form flagged.
    assert probe('payload = {"odds": 1.5}\n')
    assert probe('payload = {"confidence": 0.9, "edge": 0.1}\n')
    assert probe("odds = 2\n")
    assert probe("def stake(amount: float) -> float:\n    return amount\n")
    assert probe("kelly = 0.1\n")
    assert probe("wager: float = 1.0\n")
    assert probe('flag = "BANKROLL"\n')  # case-insensitive

    # Negative controls: legitimate shapes must NOT be flagged — the
    # dict .values() method is an attribute, not a literal; word
    # boundaries keep ordinary words ("returns", "insufficient",
    # "evaluation") clean, while the bare tokens themselves do not.
    assert probe("values = d.values()\n") == []
    assert probe('payload = {"home": 0.4, "draw": 0.3, "away": 0.3}\n') == []
    assert probe('doc = "two GETs of the same row yield identical bodies"\n') == []
    assert probe('doc = "the read path returns every row hash-verified"\n') == []
    assert probe('doc = "insufficient_teams are reported results"\n') == []
    assert probe('doc = "chronological evaluation begins at Phase 9"\n') == []

    # Runtime: the record's own field names carry no banned token.
    for field in (field.name for field in dataclasses.fields(Forecast)):
        assert not _BETTING_PATTERN.search(field), field


def test_hygiene_amendments_pinned_and_full_tree_scan_clean() -> None:
    # Criterion 25: AMENDMENT A1 pinned — exactly eleven keys; the seven
    # legacy values are exactly the Phase 1-4 sets (append-only
    # protection); the three Phase 5 values exactly as sanctioned; the
    # A2 relocation exactly the declared exception map — with probes
    # pinning both directions; AMENDMENT A3 (Phase 6) sets 10 -> 11 for
    # the app.features entry — and a clean relocated scan proves nothing relaxed.
    expected_legacy: dict[str, set[str]] = {
        "app": set(),
        "app.domain": {"app.domain"},
        "app.validation": {"app.domain", "app.validation"},
        "app.ingestion": {"app.domain", "app.validation", "app.ingestion"},
        "app.models": {"app.domain", "app.models"},
        "app.scenarios": {"app.domain", "app.models", "app.scenarios"},
        "app.simulation": {"app.models", "app.scenarios", "app.simulation"},
    }
    assert len(hygiene.ALLOWED_APP_IMPORTS) == 11
    assert set(hygiene.ALLOWED_APP_IMPORTS) == set(expected_legacy) | {
        "app.forecasts",
        "app.storage",
        "app.api",
        "app.features",
    }
    for package, allowed in expected_legacy.items():
        assert hygiene.ALLOWED_APP_IMPORTS[package] == allowed
    assert hygiene.ALLOWED_APP_IMPORTS["app.forecasts"] == {
        "app.domain",
        "app.models",
        "app.forecasts",
    }
    assert hygiene.ALLOWED_APP_IMPORTS["app.storage"] == {
        "app.domain",
        "app.forecasts",
        "app.storage",
    }
    assert hygiene.ALLOWED_APP_IMPORTS["app.api"] == {
        "app.domain",
        "app.forecasts",
        "app.storage",
        "app.api",
    }

    # AMENDMENT A2 pinned: the exception map is exactly the sanctioned
    # two entries — no banned name was removed from the ban itself.
    assert hygiene.BANNED_IMPORT_EXCEPTIONS == {
        "app.storage": {"sqlite3"},
        "app.api": {"http"},
    }
    assert "sqlite3" in hygiene.BANNED_TOP_LEVEL_IMPORTS
    assert "http" in hygiene.BANNED_TOP_LEVEL_IMPORTS

    def probe(source: str, package: str) -> list[str]:
        return hygiene.scan_source(source, "<probe>", [], package)

    # Relocated-ban probes, both directions (criterion 25 + A2 section
    # 2, verbatim): sqlite3 flagged in every package except
    # app.storage; http flagged in every package except app.api; every
    # OTHER banned name flagged everywhere, exception-holders included.
    assert probe("import sqlite3\n", "app.forecasts")
    assert probe("import sqlite3\n", "app.api")
    assert probe("import sqlite3\n", "app.models")
    assert probe("import sqlite3\n", "app.ingestion")
    assert probe("import sqlite3\n", "app.storage") == []
    assert probe("import http.server\n", "app.storage")
    assert probe("import http.server\n", "app.forecasts")
    assert probe("import http.server\n", "app.models")
    assert probe("import http.server\n", "app.api") == []
    for banned in ("urllib", "socket", "requests", "httpx", "fastapi"):
        for package in (
            "app.storage",
            "app.api",
            "app.forecasts",
            "app.models",
            "app.domain",
        ):
            assert probe(f"import {banned}\n", package), (banned, package)

    # The relocated full-tree scan: every .py under app/ completes
    # with zero violations and no KeyError — the coverage gaps closed
    # without relaxing any check anywhere else.
    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    for path in app_files:
        violations = hygiene.scan_file(path)
        assert violations == [], f"{path}: {violations}"


def test_wall_clock_and_environment_scan_still_clean_app_wide() -> None:
    # Criterion 26 (S2/S5): the Phase 2 machinery (unmodified — this
    # re-asserts coverage, it does not extend it) scans the three new
    # packages with zero violations; probes pin detection both ways.
    for directory in (FORECASTS_DIR, STORAGE_DIR, API_DIR):
        package_files = sorted(directory.rglob("*.py"))
        assert package_files, f"no Python files found under {directory}"
        violations = [
            violation
            for path in package_files
            for violation in scan_wall_clock_env(
                path.read_text(),
                str(path.relative_to(REPO_ROOT)),
                hygiene.import_base_parts_for(path),
            )
        ]
        assert violations == [], "\n".join(violations)

    def probe(source: str) -> list[str]:
        return scan_wall_clock_env(source, "<probe>", ["app", "forecasts"])

    assert any("wall-clock access datetime.datetime.now" in v for v in probe(
        "import datetime\nx = datetime.datetime.now()\n"
    ))
    assert any("wall-clock access time.time" in v for v in probe(
        "import time\nx = time.time()\n"
    ))
    assert any("environment access os.environ" in v for v in probe(
        "import os\nx = os.environ['K']\n"
    ))
    assert probe("import json\nx = json.dumps({})\n") == []
