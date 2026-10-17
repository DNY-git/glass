"""Phase 3 acceptance criterion 13: module separation for app/models.

Extends Phase 2's criterion-12 AST machinery (tests/
test_fixtures_and_hygiene.py — imported, never modified; its own
positive/negative-control probe battery stays untouched and running
there) with the models-specific rules: a stdlib whitelist plus
app.domain/app.models only, no randomness, no open()/filesystem, no
wall-clock or environment forms, and no module-level fitted singleton
— nothing at module level may construct a FittedParams or the result
of fit (G1, PLAN layer 5).
"""

from __future__ import annotations

import ast
from pathlib import Path

# Reuse Phase 2's scan machinery: constants, alias resolution, and the
# wall-clock/environment detection rules — extended, never weakened.
import test_fixtures_and_hygiene as hygiene

REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "app" / "models"

# Criterion 13: the only modules app/models may import from the stdlib
# (the brief's whitelist; itertools is whitelisted but not used this
# phase). Everything else — os, sys, pathlib, io, random, datetime,
# time, json, collections, ... — is refused by the whitelist itself.
STDLIB_WHITELIST = {
    "__future__",
    "math",
    "dataclasses",
    "typing",
    "enum",
    "hashlib",
    "itertools",
}

# Criterion 13: the only app packages app/models may import. app.domain
# (types + canonical_state) and app.models itself (intra-package).
# Notably absent: app.storage, app.ingestion, app.validation, app.api.
ALLOWED_APP_IMPORTS = {"app.domain", "app.models"}

# Names whose module-level construction or binding is banned: a fitted
# singleton at module scope would become hidden state that later phases
# could leak from (no module-level fitted singleton, G1).
FITTED_SINGLETON_CALLS = {"fit", "FittedParams"}


def scan_models_source(
    source: str,
    display: str,
    import_base_parts: list[str],
    package: str = "app.models",
) -> list[str]:
    """All criterion-13 violations in one app/models module's source."""
    tree = ast.parse(source, filename=display)
    violations: list[str] = []

    def complain(message: str) -> None:
        violations.append(f"{display}: {message}")

    # Import hygiene: banned-first (reusing Phase 2's explicit sets for
    # precise messages), then the app allowlist, then the stdlib
    # whitelist that subsumes every other ban by enumeration.
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = hygiene.resolve_from(import_base_parts, node.level, node.module)
            targets = [base]
            for alias in node.names:
                if alias.name == "*":
                    continue
                target = f"{base}.{alias.name}" if base else alias.name
                if target in hygiene.WALL_CLOCK_CALLS or hygiene.is_environment_path(target):
                    complain(f"banned import {target!r} (line {node.lineno})")
        else:
            continue
        for target in targets:
            top_level = target.split(".")[0]
            if top_level in hygiene.BANNED_TOP_LEVEL_IMPORTS:
                complain(f"banned import {target!r} (line {node.lineno})")
            if top_level in hygiene.BANNED_PURITY_IMPORTS:
                complain(f"filesystem/environment import {target!r} (line {node.lineno})")
            if top_level == "random":
                complain(f"randomness import {target!r} (line {node.lineno})")
            if (
                isinstance(node, ast.ImportFrom)
                and target in hygiene.BANNED_STAR_IMPORTS
                and any(alias.name == "*" for alias in node.names)
            ):
                complain(f"banned star import {target!r} (line {node.lineno})")
            if target == "app" or target.startswith("app."):
                if not any(
                    target == entry or target.startswith(entry + ".")
                    for entry in ALLOWED_APP_IMPORTS
                ):
                    complain(f"app import {target!r} outside allowed set (line {node.lineno})")
            elif top_level not in STDLIB_WHITELIST:
                complain(
                    f"import {target!r} outside the stdlib whitelist (line {node.lineno})"
                )

    # No open() anywhere in app/models (no I/O, ever).
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            complain(f"open() call (line {node.lineno})")

    # Wall-clock and environment reads, resolved through the same alias
    # machinery as Phase 2's criterion-12 scan.
    aliases = hygiene.collect_aliases(tree, import_base_parts)
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
            complain(f"wall-clock access {path} (line {node.lineno})")
        elif hygiene.is_environment_path(path):
            complain(f"environment access {path} (line {node.lineno})")

    # No module-level fitted singleton: no top-level assignment may
    # construct a FittedParams or call fit (directly or nested inside a
    # larger expression). Assignments INSIDE functions are the normal
    # local flow and are not flagged.
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            value: ast.AST | None = statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            value = statement.value
        else:
            continue
        for node in ast.walk(value):
            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in FITTED_SINGLETON_CALLS:
                complain(
                    f"module-level fitted singleton: call to {node.func.id!r} "
                    f"(line {node.lineno})"
                )
            elif isinstance(node.func, ast.Attribute) and node.func.attr in FITTED_SINGLETON_CALLS:
                complain(
                    f"module-level fitted singleton: call to .{node.func.attr} "
                    f"(line {node.lineno})"
                )

    return violations


def test_models_module_separation_ast() -> None:
    # Criterion 13: AST scan of every .py under app/models — stdlib
    # whitelist + app.domain/app.models only; no app.storage, no
    # app.ingestion, no app.validation, no app.api, no sqlite3, no
    # network, no os/sys/pathlib/io, no open(); no randomness (D1); no
    # wall-clock or environment forms (Phase 2's detection reused, its
    # own battery still running untouched in the hygiene file); and no
    # module-level fitted singleton (G1).
    model_files = sorted(MODELS_DIR.rglob("*.py"))
    assert model_files, "no Python files found under app/models/"
    violations = [
        violation
        for path in model_files
        for violation in scan_models_source(
            path.read_text(),
            str(path.relative_to(REPO_ROOT)),
            hygiene.import_base_parts_for(path),
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str, base: list[str] | None = None) -> list[str]:
        return scan_models_source(
            source, "<probe>", base if base is not None else ["app", "models"]
        )

    # Positive controls: every banned form must be flagged. These mirror
    # Phase 2's probe shapes (qualified, aliased, from-import) so the
    # extended scan can never silently regress to missing a form the
    # original scan catches.
    banned_forms: dict[str, str | tuple[str, ...]] = {
        # Storage/network/database imports.
        "import sqlite3\n": "banned import 'sqlite3'",
        "import urllib.request\n": "banned import 'urllib.request'",
        "import http.client\n": "banned import 'http.client'",
        "import socket\n": "banned import 'socket'",
        "import requests\n": "banned import 'requests'",
        "import fastapi\n": "banned import 'fastapi'",
        # Filesystem/environment plumbing.
        "import os\nx = os.environ['PATH']\n": (
            "filesystem/environment import 'os'",
            "environment access os.environ",
        ),
        "import os\nx = os.getenv('HOME')\n": "environment access os.getenv",
        "import sys\n": "filesystem/environment import 'sys'",
        "import pathlib\n": "filesystem/environment import 'pathlib'",
        "from io import open\n": "filesystem/environment import 'io'",
        "x = open('data.json')\n": "open() call",
        # Randomness (estimation contains none, D1).
        "import random\n": "randomness import 'random'",
        "import random as r\nx = r.random()\n": "randomness import 'random'",
        "from random import Random\n": "randomness import 'random'",
        # Wall-clock forms, caught both at import and at use (Phase 2
        # detection extended, not weakened). In app/models the module
        # import itself is additionally refused by the whitelist.
        "import datetime\nx = datetime.datetime.now()\n": (
            "outside the stdlib whitelist",
            "wall-clock access datetime.datetime.now",
        ),
        "from datetime import datetime as DT\nx = DT.now()\n": (
            "outside the stdlib whitelist",
            "wall-clock access datetime.datetime.now",
        ),
        "import time\nx = time.time()\n": (
            "outside the stdlib whitelist",
            "wall-clock access time.time",
        ),
        "from time import gmtime\n": "banned import 'time.gmtime'",
        "import time\nx = time.tzname\n": "environment access time.tzname",
        "import time\nx = time.timezone\n": "environment access time.timezone",
        # Star imports from the environment/wall-clock modules.
        "from os import *\n": (
            "banned star import 'os'",
            "filesystem/environment import 'os'",
        ),
        # app-layer imports outside the allowlist.
        "from app.storage import store\n": (
            "app import 'app.storage' outside allowed set"
        ),
        "from app.ingestion import import_fixture\n": (
            "app import 'app.ingestion' outside allowed set"
        ),
        "from app.validation import validate_records\n": (
            "app import 'app.validation' outside allowed set"
        ),
        "from app.api import router\n": "app import 'app.api' outside allowed set",
        "import app.storage\n": "app import 'app.storage' outside allowed set",
        # Relative-import escape from the package (Phase 2's pinned
        # resolution, in the app/models context).
        "from ..storage import store\n": "app import 'app.storage' outside allowed set",
        # Anything outside the stdlib whitelist.
        "import json\n": "outside the stdlib whitelist",
        "import collections.abc\n": "outside the stdlib whitelist",
        # No module-level fitted singleton (G1, PLAN layer 5).
        "_fitted = fit(matches, as_of)\n": "module-level fitted singleton: call to 'fit'",
        "_params = FittedParams()\n": (
            "module-level fitted singleton: call to 'FittedParams'"
        ),
        "_wrapped = [fit(m, d) for m in ms]\n": (
            "module-level fitted singleton: call to 'fit'"
        ),
        "fitted: FittedParams = models.fit(m, d)\n": (
            "module-level fitted singleton: call to .fit"
        ),
    }
    for source, expected in banned_forms.items():
        found = probe(source)
        expectations = (expected,) if isinstance(expected, str) else expected
        for expected_text in expectations:
            assert any(expected_text in v for v in found), (
                f"scan missed {expected_text!r} in {source!r}: {found}"
            )

    # Negative controls: the shapes app/models legitimately uses must
    # stay clean — over-broadening fails here loudly.
    legit_module = (
        "from __future__ import annotations\n"
        "import math\n"
        "import enum\n"
        "import hashlib\n"
        "from dataclasses import dataclass\n"
        "from typing import Iterable\n"
        "from .constants import MAX_GOALS\n"
        "from .params import FitConfig\n"
        "from app.domain import Match\n"
        "@dataclass(frozen=True)\n"
        "class Result:\n"
        "    digest: str\n"
        "def rate(mu: float, alpha: float, beta: float) -> float:\n"
        "    return math.exp(mu + alpha + beta)\n"
    )
    assert probe(legit_module) == [], probe(legit_module)

    # A call to fit inside a function body is normal local flow — the
    # singleton rule is module-level only.
    local_flow = "def helper(matches, as_of):\n    fitted = fit(matches, as_of)\n    return fitted\n"
    assert probe(local_flow) == [], probe(local_flow)

    # Record-attribute names like `raw.time` are data, not module reads.
    attribute_names = "_kickoff = raw.time\n_eta = match.date\n"
    assert probe(attribute_names) == [], probe(attribute_names)
