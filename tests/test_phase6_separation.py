"""Phase 6 acceptance criteria 15-20: separation for app/features.

Zero fitted state or transformers under the new package (15), the F4
byte-diff pins on the untouched Phase 3-5 packages (16), the import
allowlist and layering both directions with probes (17), the Phase 2
wall-clock/environment/purity machinery re-asserted over the package
(18), the pinned A1/A2/A3 amendments with a clean full-tree scan (19),
and the Phase 5 betting-token scan extended to app/features (20).
Reuses Phase 2/4/5 machinery by import — extended, never weakened.
"""

from __future__ import annotations

import ast
import dataclasses
import subprocess
from pathlib import Path

import test_fixtures_and_hygiene as hygiene
import test_phase5_separation as phase5
from app.features import FeatureVector

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
FEATURES_DIR = APP_DIR / "features"

# The F4 checkpoint pin: app/models, app/forecasts and app/storage are
# byte-identical to Phase 5's commit (criterion 16, version-local by
# declaration — a future phase touching any of them needs its own named
# amendment, never a silent edit).
PHASE5_CHECKPOINT = "44b43ea951fe59db95994da9a34c2ad086139cf8"

# Criterion 15: the ML/numeric stack and RNG are structurally absent.
ML_STACK_IMPORTS = ("sklearn", "numpy", "scipy", "pandas")
FITTED_METHOD_NAMES = ("fit", "transform", "fit_transform")
MODULE_LEVEL_CALL_NAMES = ("list", "dict", "set", "compute_features", "FeatureVector")

# Criterion 17: the exact stdlib + app allowlists (brief decision 1).
FEATURES_STDLIB = {"__future__", "dataclasses", "typing", "enum", "json", "hashlib", "datetime"}
FEATURES_APP = {"app.domain", "app.features"}


def _feature_files() -> list[Path]:
    files = sorted(FEATURES_DIR.rglob("*.py"))
    assert files, "no Python files found under app/features/"
    return files


def scan_features_purity(source: str, display: str) -> list[str]:
    """Criterion 15 violations in one module of app/features.

    No ML/numeric-stack import, no random import, no class defines a
    fit/transform method, no module-level mutable singleton or cached
    computed object (list/dict/set displays, or calls to the record/
    entry-point constructors), and no team-name encoding machinery (no
    ord() calls, no enumerate-driven dict/set comprehensions).
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []

    def complain(message: str, lineno: int) -> None:
        violations.append(f"{display}: {message} (line {lineno})")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = ".".join(["app", "features"][: -(node.level - 1)] if node.level > 1 else ["app", "features"])
            else:
                base = node.module or ""
            targets = [base]
        else:
            continue
        for target in targets:
            root = target.split(".")[0]
            if root in ML_STACK_IMPORTS:
                complain(f"ML/numeric-stack import {target!r}", node.lineno)
            if root == "random":
                complain(f"random import {target!r}", node.lineno)

    # No class anywhere in the package defines a fitted-transformer
    # method (F2: zero fitted transformers, stated structurally).
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name in FITTED_METHOD_NAMES:
                    complain(
                        f"class {node.name!r} defines fitted method {item.name!r}",
                        item.lineno,
                    )

    # Module-level state: no mutable display and no call whose result
    # could be a cached computed object. The only permitted module-level
    # names are constants (literal strings/ints) and __all__ (a tuple or
    # a list of literal strings — the export inventory, not state).
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            value = node.value
            if targets == ["__all__"]:
                continue
            if isinstance(value, (ast.List, ast.Dict, ast.Set)):
                complain(f"module-level mutable display {targets!r}", node.lineno)
            if isinstance(value, ast.Call):
                called = value.func.id if isinstance(value.func, ast.Name) else (
                    value.func.attr if isinstance(value.func, ast.Attribute) else ""
                )
                if called in MODULE_LEVEL_CALL_NAMES:
                    complain(f"module-level call assigning {targets!r}", node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if node.target.id == "__all__":
                continue
            if isinstance(node.value, (ast.List, ast.Dict, ast.Set)):
                complain(f"module-level mutable display {[node.target.id]!r}", node.lineno)

    # Team-encoding machinery (F2): identity is the name string, never
    # an ordinal — flag ord() calls and enumerate-driven dict/set
    # comprehensions either way.
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "ord":
            complain("ord() call (name-encoding machinery)", node.lineno)
        if isinstance(node, (ast.DictComp, ast.SetComp)) and "enumerate" in ast.dump(node):
            complain("enumerate-driven comprehension (index-keyed machinery)", node.lineno)

    return violations


def scan_features_imports(
    source: str, display: str, base_parts: list[str], package: str = "app.features"
) -> list[str]:
    """Criterion 17 violations in one module of app/features.

    Stdlib allowlist + app allowlist + the Phase 2 banned-import sets
    (no exception applies to this package) + open() + the wall-clock/
    environment machinery resolved through Phase 2's alias handling.
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []

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
                if target in hygiene.WALL_CLOCK_CALLS or hygiene.is_environment_path(target):
                    complain(f"banned import {target!r}", node.lineno)
        else:
            continue
        for target in targets:
            top_level = target.split(".")[0]
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
                if not hygiene.allowed_app_import(target, FEATURES_APP):
                    complain(f"app import {target!r} outside allowed set", node.lineno)
            elif top_level not in FEATURES_STDLIB:
                complain(
                    f"import {target!r} outside the package stdlib allowlist",
                    node.lineno,
                )

    # Purity: no filesystem plumbing under the pure package.
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            complain("open() call", node.lineno)
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


def test_no_fitted_state_or_transformers_under_app_features() -> None:
    # Criterion 15 (F2): AST over app/features/** — no ML/numeric-stack
    # import, no random import, no class defines fit/transform, no
    # module-level mutable singleton or cached computed object, no
    # team-name encoding machinery; probes pin every direction.
    violations = [
        violation
        for path in _feature_files()
        for violation in scan_features_purity(
            path.read_text(), str(path.relative_to(REPO_ROOT))
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str) -> list[str]:
        return scan_features_purity(source, "<probe>")

    # Positive controls: every banned shape flagged.
    for banned in ML_STACK_IMPORTS:
        assert probe(f"import {banned}\n"), banned
    assert probe("from sklearn.linear_model import LogisticRegression\n")
    assert probe("import random\n")
    assert probe("from random import Random\n")
    assert probe("class Model:\n    def fit(self, data):\n        pass\n")
    assert probe("class Model:\n    def transform(self, data):\n        pass\n")
    assert probe("class Model:\n    def fit_transform(self, data):\n        pass\n")
    assert probe("CACHE = []\n")
    assert probe("STATE = {}\n")
    assert probe("SEEN = {1, 2}\n")
    assert probe("TABLE = compute_features(matches, fixture)\n")
    assert probe("VECTORS = [FeatureVector()]\n")
    assert probe("def code(team: str) -> int:\n    return ord(team[0])\n")
    assert probe("CODES = {i: t for i, t in enumerate(teams)}\n")

    # Negative controls: the sanctioned shapes stay clean.
    assert probe("FEATURE_VERSION = 'features-chronological-v1'\n") == []
    assert probe("FORM_WINDOW = 5\n") == []
    assert probe('__all__ = ["compute_features"]\n') == []
    assert probe("__all__ = tuple(sorted(names))\n") == []
    assert probe("from dataclasses import dataclass\n") == []
    assert probe("from datetime import date\nx = date.fromisoformat('2024-01-01')\n") == []
    assert probe("class Model:\n    def predict(self, params):\n        return params\n") == []


def test_f4_no_model_change_zero_byte_diff_pins() -> None:
    # Criterion 16 (F4/F3): git diff of the three pinned packages
    # against the Phase 5 checkpoint exits 0 with empty output — fit,
    # FitConfig, MODEL_VERSION, build_forecast, the Forecast record and
    # its canonicalization/builder, and the storage schema are
    # byte-identical to Phase 5.
    result = subprocess.run(
        [
            "git", "diff", PHASE5_CHECKPOINT, "--",
            "app/models", "app/forecasts", "app/storage",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "", result.stdout
    assert result.stderr == "", result.stderr


def test_app_features_import_allowlist_and_layering_with_probes() -> None:
    # Criterion 17 (F5): the exact allowlists hold over every module;
    # layering is strict in both directions — the package imports only
    # stdlib + app.domain (and itself), and NOTHING outside imports it
    # (consumed by nothing, decision 11); probes pin each direction.
    violations = [
        violation
        for path in _feature_files()
        for violation in scan_features_imports(
            path.read_text(),
            str(path.relative_to(REPO_ROOT)),
            hygiene.import_base_parts_for(path),
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str, package: str = "app.features") -> list[str]:
        return scan_features_imports(
            source, "<probe>", ["app", package.split(".")[1]], package
        )

    # Positive controls: banned forms flagged inside the package.
    assert probe("from app.models import fit\n")
    assert probe("from app.forecasts import build_forecast\n")
    assert probe("from app.storage import forecasts_db\n")
    assert probe("from app.api import create_server\n")
    assert probe("from app.ingestion import import_fixture\n")
    assert probe("from app.validation import validate_raw\n")
    assert probe("from app.scenarios import Scenario\n")
    assert probe("from app.simulation import run_simulation\n")
    assert probe("import os\n")
    assert probe("import sqlite3\n")
    assert probe("import http.server\n")
    assert probe("import urllib.parse\n")
    assert probe("import time\n")
    assert probe("from os import environ\n")

    # Negative controls: the sanctioned shapes stay clean.
    assert probe("import datetime\n") == []
    assert probe("import json\nimport hashlib\n") == []
    assert probe("from app.domain import Fixture\n") == []
    assert probe("from .constants import FORM_WINDOW\n") == []
    assert probe("from .record import FeatureVector\n") == []
    legit = (
        "from __future__ import annotations\n"
        "import hashlib\n"
        "from datetime import date\n"
        "from app.domain import Match\n"
        "from .constants import FORM_WINDOW\n"
        "def gap(a: str, b: str) -> int:\n"
        "    return (date.fromisoformat(a) - date.fromisoformat(b)).days\n"
    )
    assert probe(legit) == []

    # Reverse layering: no file OUTSIDE app/features imports it.
    for path in sorted(APP_DIR.rglob("*.py")):
        if FEATURES_DIR in path.parents or path.parent == FEATURES_DIR:
            continue
        text = path.read_text()
        assert "app.features" not in text, path
        assert "compute_features" not in text, path
        for node in ast.walk(ast.parse(text, filename=str(path))):
            if isinstance(node, ast.Name):
                assert node.id != "compute_features", path
            if isinstance(node, ast.Attribute):
                assert node.attr != "compute_features", path

    # The reverse direction is also flagged by the machinery itself: a
    # forecasts module importing app.features trips its allowlist.
    reverse = hygiene.scan_source(
        "from app.features import compute_features\n",
        "<probe>",
        ["app", "forecasts"],
        "app.forecasts",
    )
    assert any("outside allowed set" in violation for violation in reverse)


def test_wall_clock_env_and_purity_scan_covers_app_features() -> None:
    # Criterion 18 (F5): the UNCHANGED Phase 2 machinery scans the new
    # package with zero violations — the sanctioned date-arithmetic
    # shapes pass, wall-clock readers, star imports and filesystem
    # plumbing (via A1's PURE_PACKAGES strengthening) are all flagged.
    for path in _feature_files():
        violations = hygiene.scan_file(path)
        assert violations == [], f"{path}: {violations}"

    def probe(source: str) -> list[str]:
        return hygiene.scan_source(
            source, "<probe>", ["app", "features"], "app.features"
        )

    # Positive controls (the machinery's own probes, retargeted here):
    # a wall-clock read inside app.features is flagged...
    assert any(
        "wall-clock access datetime.date.today" in v for v in probe(
            "import datetime\nx = datetime.date.today()\n"
        )
    )
    assert any(
        "wall-clock access datetime.datetime.now" in v for v in probe(
            "from datetime import datetime\nx = datetime.now()\n"
        )
    )
    # ...a star import from datetime is flagged...
    assert any("banned star import 'datetime'" in v for v in probe(
        "from datetime import *\n"
    ))
    # ...and `import os` is flagged UNDER app.features via A1's
    # PURE_PACKAGES strengthening (both directions pinned: flagged in
    # the pure package, allowed in a non-pure one).
    assert any("in pure package" in v for v in probe("import os\n"))
    assert any("in pure package" in v for v in probe("import sys\n"))
    assert any("in pure package" in v for v in probe("import pathlib\n"))
    assert any("in pure package" in v for v in probe("import io\n"))
    non_pure = hygiene.scan_source(
        "import os\n", "<probe>", ["app", "storage"], "app.storage"
    )
    assert non_pure == [], non_pure

    # Negative controls (the machinery's own sanctioned shapes): ISO
    # date arithmetic — fromisoformat and constructors — stays clean.
    assert probe(
        "from datetime import date\n"
        "_a = date.fromisoformat('2024-01-01')\n"
        "_b = date(2024, 1, 2)\n"
        "_gap = (_b - _a).days\n"
    ) == []
    assert probe("import json\nx = json.dumps({}, sort_keys=True)\n") == []


def test_hygiene_amendments_pinned_and_full_tree_scan_clean() -> None:
    # Criterion 19 (F5): AMENDMENT A1 pinned — exactly TWELVE keys; the
    # ten legacy values are exactly the Phase 1-5 sets (append-only
    # convention protected); the A1 value is exactly the sanctioned
    # {"app.domain", "app.features"}; PURE_PACKAGES is exactly the
    # sanctioned four-package strengthening (Phase 7's A1 adds
    # app.decisions); the exception map is untouched; and hygiene.scan_file
    # over every .py under app/ completes with zero violations and no KeyError.
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
    assert set(hygiene.ALLOWED_APP_IMPORTS) == set(expected_legacy) | {"app.features", "app.decisions"}
    for package, allowed in expected_legacy.items():
        assert hygiene.ALLOWED_APP_IMPORTS[package] == allowed, package
    assert hygiene.ALLOWED_APP_IMPORTS["app.features"] == {
        "app.domain",
        "app.features",
    }
    assert hygiene.PURE_PACKAGES == {"app.domain", "app.validation", "app.features", "app.decisions"}
    assert hygiene.BANNED_IMPORT_EXCEPTIONS == {
        "app.storage": {"sqlite3"},
        "app.api": {"http"},
    }

    def probe(source: str, package: str) -> list[str]:
        return hygiene.scan_source(source, "<probe>", [], package)

    # The exception map is untouched: sqlite3 and http are still flagged
    # under app.features (no exception exists for it), and so is every
    # other banned name everywhere.
    assert probe("import sqlite3\n", "app.features")
    assert probe("import http.server\n", "app.features")
    for banned in ("urllib", "socket", "requests", "httpx", "fastapi"):
        assert probe(f"import {banned}\n", "app.features"), banned

    # The A2/A3 pin updates are verified IN PLACE in the amended files:
    # both declare the 12-key universe with app.features and app.decisions
    # in the union, and both still assert every legacy value — extending,
    # never weakening (the files also execute in this same suite).
    phase4_source = (REPO_ROOT / "tests" / "test_phase4_separation.py").read_text()
    phase5_source = (REPO_ROOT / "tests" / "test_phase5_separation.py").read_text()
    for amended, name in ((phase4_source, "phase4"), (phase5_source, "phase5")):
        assert "len(hygiene.ALLOWED_APP_IMPORTS) == 12" in amended, name
        assert '"app.features"' in amended and '"app.decisions"' in amended, name
        assert all(f"len(hygiene.ALLOWED_APP_IMPORTS) == {n}" not in amended for n in (10, 11)), name

    # The full-tree scan: every .py under app/ (now including the new
    # package) completes with zero violations and no KeyError.
    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    for path in app_files:
        violations = hygiene.scan_file(path)
        assert violations == [], f"{path}: {violations}"


def test_betting_token_scan_extends_to_app_features() -> None:
    # Criterion 20 (F5): the Phase 5 machinery REUSED by import (token
    # list and scanner — single source of truth, never copied): no
    # banned betting-surface token appears in any app/features string
    # literal, identifier, dataclass field name or dict key; the
    # decision-4 field contract carries no token; probes pin both
    # directions.
    violations = [
        violation
        for path in _feature_files()
        for violation in phase5.scan_betting_tokens(
            path.read_text(), str(path.relative_to(REPO_ROOT))
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str) -> list[str]:
        return phase5.scan_betting_tokens(source, "<probe>")

    # Positive control: the machinery detects every token form here too.
    for token in phase5.BANNED_BETTING_TOKENS:
        assert probe(f'payload = {{ "{token}": 1 }}\n'), token

    # Negative controls: the legitimate shapes in this package are not
    # flagged — the OptionalValue TYPE name and its .value attribute
    # access are ordinary domain vocabulary, and the canonical payload's
    # literal "value" key is the sanctioned nested-object key, not a
    # betting surface (word-boundary discipline; the bare "value" token
    # is deliberately NOT in the banned list — criterion 20 guards the
    # FIELD NAMES below, not the word).
    assert probe("from app.domain import OptionalValue\n") == []
    assert probe("x = record.value\n") == []
    assert probe("d = record.values()\n") == []
    assert probe('payload = {"availability": "MISSING", "value": None}\n') == []

    # Runtime: the decision-4 field contract contains none of the
    # criterion-20 field bans — no field named edge/confidence/value/ev
    # (the explicit four the brief names) nor any banned token.
    banned_field_names = {"edge", "confidence", "value", "ev"}
    for field in (field.name for field in dataclasses.fields(FeatureVector)):
        assert field not in banned_field_names, field
        assert not phase5._BETTING_PATTERN.search(field), field
