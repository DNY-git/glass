"""Phase 2 acceptance criteria 12-14: import hygiene and fixture discipline.

Criterion 12 is a standing AST scan: module separation, no network or
storage imports, pure domain/validation (no filesystem), no wall clock
and no environment lookups anywhere under app/. Criteria 13-14 pin
deterministic replay and the checked-in synthetic fixture convention.
"""

from __future__ import annotations

import ast
import json
import random
from pathlib import Path

from app.domain import MatchCollection, canonical_state
from app.ingestion import import_fixture

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
FIXTURES = REPO_ROOT / "fixtures" / "openfootball"
VALID_1 = FIXTURES / "valid" / "season-1.json"

EXPECTED_FIXTURES = {
    REPO_ROOT / "fixtures" / "openfootball" / "valid" / "season-1.json",
    REPO_ROOT / "fixtures" / "openfootball" / "valid" / "season-2.json",
    REPO_ROOT / "fixtures" / "openfootball" / "defects" / "defect-sample.json",
}

# Criterion 12: no network/storage imports anywhere under app/.
BANNED_TOP_LEVEL_IMPORTS = {
    "urllib",
    "http",
    "socket",
    "requests",
    "httpx",
    "fastapi",
    "sqlite3",
}
# AMENDMENT A2 (Phase 5): the sanctioned sqlite backend (app.storage) and
# stdlib HTTP server (app.api) are the ONLY packages permitted these imports.
BANNED_IMPORT_EXCEPTIONS: dict[str, set[str]] = {
    "app.storage": {"sqlite3"},
    "app.api": {"http"},
}
# Criterion 12: domain and validation are pure — no filesystem plumbing.
BANNED_PURITY_IMPORTS = {"os", "sys", "pathlib", "io"}
# Criterion 12: allowed app.* import sets per package.
ALLOWED_APP_IMPORTS: dict[str, set[str]] = {
    "app": set(),
    "app.domain": {"app.domain"},  # intra-package only; imports nothing outside
    "app.validation": {"app.domain", "app.validation"},
    "app.ingestion": {"app.domain", "app.validation", "app.ingestion"},
    "app.models": {"app.domain", "app.models"},  # Phase 3: models imports stdlib + app.domain only
    "app.scenarios": {"app.domain", "app.models", "app.scenarios"},  # Phase 4: scenarios imports stdlib + app.domain/app.models only
    "app.simulation": {"app.models", "app.scenarios", "app.simulation"},  # Phase 4: simulation imports stdlib + app.models/app.scenarios only
    "app.forecasts": {"app.domain", "app.models", "app.forecasts"},  # Phase 5: forecasts imports stdlib + app.domain/app.models only (pure)
    "app.storage": {"app.domain", "app.forecasts", "app.storage"},  # Phase 5: storage imports stdlib sqlite3 + app.domain/app.forecasts only
    "app.api": {"app.domain", "app.forecasts", "app.storage", "app.api"},  # Phase 5: api imports stdlib http + app.domain/app.forecasts/app.storage only
    "app.features": {"app.domain", "app.features"},  # Phase 6: features imports stdlib + app.domain only (pure)
}
PURE_PACKAGES = {"app.domain", "app.validation", "app.features"}
# Criterion 12: resolved module paths that read the wall clock. Names are
# the *real* dotted paths after alias resolution (e.g. `dt.datetime.now()`
# and `from datetime import datetime as DT; DT.now()` both resolve to
# "datetime.datetime.now"). Banned is exactly what the set below lists:
# the current-time readers (datetime.date.today; datetime.datetime's
# now/utcnow/today; the bare datetime.now/utcnow fallback spellings)
# and the time-module readers time, time_ns, gmtime,
# localtime, strftime, ctime, clock_gettime, clock_gettime_ns, asctime —
# asctime() with no arguments returns the current local time, identical
# semantics to ctime(). No completeness is claimed for this list or for
# ENVIRONMENT_PATHS: both are explicit finite enumerations maintained by
# hand, and their completeness is enforced by reviewer audits of the
# stdlib for missed twins (time.clock_gettime_ns was caught exactly that
# way), never asserted by a comment. Deliberately off this set:
# time.monotonic, time.perf_counter, datetime constructors,
# .fromisoformat, and the TZ lookups (time.tzset/tzname/altzone/daylight/timezone),
# which are environment lookups and live in ENVIRONMENT_PATHS.
WALL_CLOCK_CALLS = {
    "datetime.datetime.now",
    "datetime.datetime.utcnow",
    "datetime.datetime.today",
    "datetime.date.today",
    "datetime.now",  # bare/invalid form; caught via the root fallback
    "datetime.utcnow",
    "time.time",
    "time.time_ns",
    "time.gmtime",
    "time.localtime",
    "time.strftime",
    "time.ctime",
    "time.asctime",
    "time.clock_gettime",
    "time.clock_gettime_ns",
}
# Criterion 12: resolved module paths that read the environment. Any
# attribute access under os.environ or os.environb (including .get and
# subscripting) is a lookup; os.environb is the bytes-valued twin of
# os.environ and must not slip through the os.environ/ prefix match.
# The time-module TZ family is environment-derived the same way and is
# flagged by plain reference, not only by call: time.tzset() re-reads the
# TZ variable via libc, while time.tzname / time.altzone /
# time.daylight / time.timezone are TZ-derived module attributes read as
# bare references (`x = time.tzname` is an environment read exactly like
# `x = os.environ`). time.timezone is likewise TZ-derived — verified
# empirically in this repo: TZ=UTC -> 0, TZ=America/New_York -> 18000,
# TZ unset -> -3600 — so it is a member of this set, not a negative
# control.
ENVIRONMENT_PATHS = {
    "os.environ",
    "os.environb",
    "os.getenv",
    "time.tzset",
    "time.tzname",
    "time.altzone",
    "time.daylight",
    "time.timezone",
}
ENVIRONMENT_PREFIXES = ("os.environ.", "os.environb.")
# Bare canonical module names resolve to themselves even when a probe (or
# a broken module) references them without an import statement.
FALLBACK_ROOTS = {"datetime", "time", "os"}
# Criterion 12: star imports FROM these modules are violations at the
# import statement itself (BUG-T2). `from os import *` binds the banned
# environment names (environ, getenv, environb) as bare Names, and
# `from time import *` / `from datetime import *` bind the wall-clock
# names the same way; collect_aliases() intentionally skips "*", so no
# later use of a star-imported name can ever resolve to its banned path.
# The import statement is therefore the only precise place to flag, and
# it is caught no matter how the imported names are subsequently used.
# Submodules are deliberately NOT in the set: `from os.path import *`
# exports no os names (environ/getenv/environb live in os, not os.path),
# and star imports from other modules (e.g. json) export no banned names.
BANNED_STAR_IMPORTS = {"os", "time", "datetime"}


def is_environment_path(path: str) -> bool:
    return path in ENVIRONMENT_PATHS or path.startswith(ENVIRONMENT_PREFIXES)


def module_name_for(path: Path) -> str:
    parts = list(path.relative_to(REPO_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def import_base_parts_for(path: Path) -> list[str]:
    """Parts relative imports resolve against (the containing package).

    For a package __init__ the containing package is the package directory
    itself, so the "__init__" leaf drops exactly like a module leaf: both
    app/domain/__init__.py and app/domain/collection.py resolve against
    ["app", "domain"]. Keeping "__init__" would resolve level >= 2 relative
    imports one package too deep (``from ..storage`` in app/domain/__init__.py
    -> "app.domain.storage" instead of the true target "app.storage"), which
    the allowed-set prefix match would silently accept.
    """
    parts = list(path.relative_to(REPO_ROOT).with_suffix("").parts)
    return parts[:-1]


def package_name_for(path: Path) -> str:
    parts = module_name_for(path).split(".")
    if len(parts) >= 2 and parts[0] == "app":
        return ".".join(parts[:2])
    return "app"


def resolve_from(base_parts: list[str], level: int, imported: str | None) -> str:
    """Resolve an ImportFrom target to an absolute module name."""
    if level == 0:
        return imported or ""
    base = base_parts[: len(base_parts) - (level - 1)]
    if imported:
        return ".".join(base + imported.split("."))
    return ".".join(base)


def allowed_app_import(target: str, allowed: set[str]) -> bool:
    return any(target == entry or target.startswith(entry + ".") for entry in allowed)


def collect_aliases(tree: ast.AST, import_base_parts: list[str]) -> dict[str, str]:
    """Map every name bound by an import to its real dotted module path.

    `import datetime as dt`  -> {"dt": "datetime"}
    `from datetime import datetime as DT` -> {"DT": "datetime.datetime"}
    `import os.path` -> {"os": "os"} (unaliased imports bind the root).
    """
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    aliases[alias.asname] = alias.name
                else:
                    root = alias.name.split(".")[0]
                    aliases.setdefault(root, root)
        elif isinstance(node, ast.ImportFrom):
            base = resolve_from(import_base_parts, node.level, node.module)
            for alias in node.names:
                if alias.name == "*":
                    continue
                target = f"{base}.{alias.name}" if base else alias.name
                aliases[alias.asname or alias.name] = target
    return aliases


def resolve_root(name: str, aliases: dict[str, str]) -> str | None:
    """Real module path for a bare name, or None if it is not one."""
    if name in aliases:
        return aliases[name]
    if name in FALLBACK_ROOTS:
        return name
    return None


def dotted_attribute_path(node: ast.Attribute, aliases: dict[str, str]) -> str | None:
    """Fully resolved dotted path of an outermost attribute chain.

    `datetime.datetime.now` -> "datetime.datetime.now"; `dt.datetime.now`
    with `import datetime as dt` -> the same. Chains not rooted in a plain
    Name (e.g. `get_os().environ`) are unresolvable -> None.
    """
    parts = [node.attr]
    current: ast.expr = node.value
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    base = resolve_root(current.id, aliases)
    if base is None:
        return None
    return ".".join([base, *reversed(parts)])


def scan_file(path: Path) -> list[str]:
    """All criterion-12 violations in one app/ module."""
    return scan_source(
        path.read_text(),
        str(path.relative_to(REPO_ROOT)),
        import_base_parts_for(path),
        package_name_for(path),
    )


def scan_source(
    source: str, display: str, import_base_parts: list[str], package: str
) -> list[str]:
    """All criterion-12 violations in one module's source text."""
    tree = ast.parse(source, filename=display)
    violations: list[str] = []

    def complain(message: str) -> None:
        violations.append(f"{display}: {message}")

    # Import hygiene.
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            targets = [resolve_from(import_base_parts, node.level, node.module)]
        else:
            continue
        for target in targets:
            top_level = target.split(".")[0]
            if top_level in BANNED_TOP_LEVEL_IMPORTS and top_level not in BANNED_IMPORT_EXCEPTIONS.get(package, set()):
                complain(f"banned import {target!r} (line {node.lineno})")
            # Environment lookups are also banned at the import statement
            # itself, for both spellings: `import os.environ as env2`
            # (module-alias form, whose uses `env2['PATH']`/`dict(env2)`
            # are plain Names the attribute scan cannot resolve) and
            # `import os.environb`. The ImportFrom twin is caught by the
            # per-name loop below, since resolve_from() yields only the
            # module here (`os`), not `os.environ`.
            if is_environment_path(target):
                complain(f"banned import {target!r} (line {node.lineno})")
            # Star-import evasion (BUG-T2): `from os import *` /
            # `from time import *` / `from datetime import *` bind the
            # banned environment and wall-clock names as bare Names, which
            # collect_aliases() skips ("*"), so every later use would be
            # invisible to the use-site scan below. The import statement
            # itself is therefore flagged — and that flag covers the
            # statement regardless of how the star-imported names are used
            # afterwards. Use-site detection for star-imported names is
            # intentionally out of scope: the import is already caught.
            if (
                isinstance(node, ast.ImportFrom)
                and target in BANNED_STAR_IMPORTS
                and any(alias.name == "*" for alias in node.names)
            ):
                complain(f"banned star import {target!r} (line {node.lineno})")
            if target == "app" or target.startswith("app."):
                if not allowed_app_import(target, ALLOWED_APP_IMPORTS[package]):
                    complain(f"app import {target!r} outside allowed set (line {node.lineno})")
            if package in PURE_PACKAGES and top_level in BANNED_PURITY_IMPORTS:
                complain(f"filesystem/environment import {target!r} in pure package (line {node.lineno})")

    # Purity: no open() in domain/validation.
    if package in PURE_PACKAGES:
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "open"
            ):
                complain(f"open() call in pure package (line {node.lineno})")

    # Wall clock and environment lookups are banned everywhere under app/.
    # Imports are resolved to their real modules first, so aliased forms
    # (`import datetime as dt`, `from datetime import datetime as DT`)
    # cannot escape.
    aliases = collect_aliases(tree, import_base_parts)
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        base = resolve_from(import_base_parts, node.level, node.module)
        for alias in node.names:
            if alias.name == "*":
                continue
            target = f"{base}.{alias.name}" if base else alias.name
            if target in WALL_CLOCK_CALLS or is_environment_path(target):
                complain(f"banned import {target!r} (line {node.lineno})")
    # Only outermost attribute chains are checked, so `os.environ.get(...)`
    # is reported once, as `os.environ.get`.
    inner_attributes = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Attribute)
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or id(node) in inner_attributes:
            continue
        path = dotted_attribute_path(node, aliases)
        if path is None:
            continue
        if path in WALL_CLOCK_CALLS:
            complain(f"wall-clock access {path} (line {node.lineno})")
        elif is_environment_path(path):
            complain(f"environment access {path} (line {node.lineno})")

    return violations


def test_module_separation_and_no_network_imports() -> None:
    # Criterion 12: AST scan of every .py under app/.
    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    violations = [
        violation for path in app_files for violation in scan_file(path)
    ]
    assert violations == [], "\n".join(violations)


def test_wall_clock_env_scan_flags_every_banned_form() -> None:
    # Criterion 12 positive control: synthetic probe modules mirror the
    # qualified, aliased, direct and from-import wall-clock/environment
    # idioms; the scan must flag every one, so its detection can never
    # silently regress to the pre-fix gaps (qualified `datetime.datetime
    # .now()` missed, aliased imports escaping, dead ImportFrom branch,
    # `os.getenv` uncaught). It also pins relative-import resolution for
    # package __init__ files (base = package directory, see below). Probes
    # are parsed in memory — nothing is written into app/ or anywhere in
    # the repo.
    def probe(source: str) -> list[str]:
        return scan_source(source, "<probe>", [], "app")

    # Expected substrings; a tuple means every one must appear in the
    # report (used where both the import statement and the resolved use
    # of an alias must flag).
    banned_forms: dict[str, str | tuple[str, ...]] = {
        # Reviewer probe 1: qualified attribute chains.
        "import datetime\nx = datetime.datetime.now()\n": "wall-clock access datetime.datetime.now",
        "import datetime\nx = datetime.datetime.utcnow()\n": "wall-clock access datetime.datetime.utcnow",
        "import time\nx = time.time()\n": "wall-clock access time.time",
        "import os\nx = os.environ\n": "environment access os.environ",
        "import os\nx = os.environ['PATH']\n": "environment access os.environ",
        "import os\nx = os.environ.get('HOME')\n": "environment access os.environ.get",
        "import os\nx = os.getenv('HOME')\n": "environment access os.getenv",
        # Reviewer probe 2: aliased imports.
        "import datetime as dt\nx = dt.datetime.now()\n": "wall-clock access datetime.datetime.now",
        "import time as t\nx = t.time()\n": "wall-clock access time.time",
        "import os as o\nx = o.environ\n": "environment access os.environ",
        "import os as o\nx = o.getenv('HOME')\n": "environment access os.getenv",
        # Reviewer probe 3: from-imported names used directly.
        "from datetime import datetime\nx = datetime.now()\n": "wall-clock access datetime.datetime.now",
        "from datetime import datetime as DT\nx = DT.now()\n": "wall-clock access datetime.datetime.now",
        "from time import time\nx = time()\n": "banned import 'time.time'",
        "from os import environ\n": "banned import 'os.environ'",
        "from os import getenv\n": "banned import 'os.getenv'",
        # Reviewer probe 4 (B1): module-alias environment spellings. The
        # import statement itself must flag, and attribute uses of the
        # alias resolve back to os.environ.
        "import os.environ as env2\nx = env2['PATH']\n": "banned import 'os.environ'",
        "import os.environ as env2\nd = dict(env2)\n": "banned import 'os.environ'",
        "import os.environ as env2\nx = env2.get('PATH')\n": (
            "banned import 'os.environ'",
            "environment access os.environ.get",
        ),
        # Reviewer probe 5 (B1): os.environb — real environment lookup in
        # every spelling (bare attribute, subscript, .get, module alias,
        # from-import plain and aliased).
        "import os\nx = os.environb['X']\n": "environment access os.environb",
        "import os\nx = os.environb.get('X')\n": "environment access os.environb.get",
        "import os.environb as eb\nd = dict(eb)\n": "banned import 'os.environb'",
        "from os import environb\n": "banned import 'os.environb'",
        "from os import environb as eb\n": "banned import 'os.environb'",
        # Reviewer probe 6 (B2): current-time / wall-clock family, each
        # member qualified first...
        "import datetime\nx = datetime.date.today()\n": "wall-clock access datetime.date.today",
        "import datetime\nx = datetime.datetime.today()\n": "wall-clock access datetime.datetime.today",
        "import time\nx = time.time_ns()\n": "wall-clock access time.time_ns",
        "import time\nx = time.gmtime()\n": "wall-clock access time.gmtime",
        "import time\nx = time.localtime()\n": "wall-clock access time.localtime",
        "import time\nx = time.strftime('%Y-%m-%d')\n": "wall-clock access time.strftime",
        "import time\nx = time.ctime()\n": "wall-clock access time.ctime",
        "import time\nx = time.clock_gettime(0)\n": "wall-clock access time.clock_gettime",
        "import time\nx = time.clock_gettime_ns(0)\n": "wall-clock access time.clock_gettime_ns",
        # ...then through module aliases...
        "import datetime as dt\nx = dt.date.today()\n": "wall-clock access datetime.date.today",
        "import datetime as dt\nx = dt.datetime.today()\n": "wall-clock access datetime.datetime.today",
        "import time as t\nx = t.time_ns()\n": "wall-clock access time.time_ns",
        "import time as t\nx = t.gmtime()\n": "wall-clock access time.gmtime",
        "import time as t\nx = t.localtime()\n": "wall-clock access time.localtime",
        "import time as t\nx = t.strftime('%Y')\n": "wall-clock access time.strftime",
        "import time as t\nx = t.ctime()\n": "wall-clock access time.ctime",
        "import time as t\nx = t.clock_gettime(0)\n": "wall-clock access time.clock_gettime",
        "import time as t\nx = t.clock_gettime_ns(0)\n": "wall-clock access time.clock_gettime_ns",
        # ...and through from-import aliases (including the exact
        # `from datetime import date as _d; _d.today()` shape).
        "from datetime import date as _d\nx = _d.today()\n": "wall-clock access datetime.date.today",
        "from datetime import datetime as DT\nx = DT.today()\n": "wall-clock access datetime.datetime.today",
        "from time import time_ns\n": "banned import 'time.time_ns'",
        "from time import gmtime\n": "banned import 'time.gmtime'",
        "from time import localtime as lt\n": "banned import 'time.localtime'",
        "from time import strftime\n": "banned import 'time.strftime'",
        "from time import ctime\n": "banned import 'time.ctime'",
        "from time import clock_gettime\n": "banned import 'time.clock_gettime'",
        "from time import clock_gettime_ns\n": "banned import 'time.clock_gettime_ns'",
        # Reviewer probe 6b (BUG-T1): time.asctime() with no arguments
        # returns the current local time — identical semantics to
        # time.ctime — in every spelling (qualified, module alias,
        # from-import; the from-import flags at the import statement,
        # exactly like `from time import time`).
        "import time\nx = time.asctime()\n": "wall-clock access time.asctime",
        "import time as t\nx = t.asctime()\n": "wall-clock access time.asctime",
        "from time import asctime\n": "banned import 'time.asctime'",
        "from time import asctime as asc\n": "banned import 'time.asctime'",
        # Reviewer probe 7 (BUG-T2): star imports from the banned modules
        # are violations at the import statement itself, wherever they
        # appear under app/. A star import from these modules makes their
        # wall-clock/environment names untraceable (collect_aliases skips
        # "*", so bare environ/date/ctime are unresolvable Names), so the
        # import itself must be banned.
        "from os import *\n": "banned star import 'os'",
        "from time import *\n": "banned star import 'time'",
        "from datetime import *\n": "banned star import 'datetime'",
        # The previously-evading USES (BUG-T2) are then covered by the
        # import-level flag: `environ['HOME']`, `date.today()` and
        # `ctime()` are bare Names the use-site scan cannot resolve, but
        # the statement is caught regardless of how the star-imported
        # names are used. Use-site detection for star-imported names is
        # intentionally out of scope because the import is already
        # flagged.
        "from os import *\nx = environ['HOME']\n": "banned star import 'os'",
        "from datetime import *\nx = date.today()\n": "banned star import 'datetime'",
        "from time import *\nx = ctime()\n": "banned star import 'time'",
        # Reviewer probe 8 (B4): the TZ environment family. time.tzset()
        # re-reads the TZ variable via libc and resolves statically in the
        # scan exactly like every other time-module member (qualified,
        # module alias, from-import). time.tzname / time.altzone /
        # time.daylight / time.timezone are not callables — they are
        # TZ-derived module data read by plain attribute reference, so
        # their probes are references (`x = time.tzname`), mirroring the
        # bare `x = os.environ` reference probe above.
        "import time\nx = time.tzset()\n": "environment access time.tzset",
        "import time as t\nx = t.tzset()\n": "environment access time.tzset",
        "from time import tzset\n": "banned import 'time.tzset'",
        "import time\nx = time.tzname\n": "environment access time.tzname",
        "import time as t\nx = t.tzname\n": "environment access time.tzname",
        "from time import tzname\n": "banned import 'time.tzname'",
        "import time\nx = time.altzone\n": "environment access time.altzone",
        "import time as t\nx = t.altzone\n": "environment access time.altzone",
        "from time import altzone\n": "banned import 'time.altzone'",
        "import time\nx = time.daylight\n": "environment access time.daylight",
        "import time as t\nx = t.daylight\n": "environment access time.daylight",
        "from time import daylight\n": "banned import 'time.daylight'",
        # Reviewer probe 9 (B4 follow-up): time.timezone, the last member
        # of the TZ-derived family — empirically TZ-dependent (TZ=UTC ->
        # 0, TZ=America/New_York -> 18000, TZ unset -> -3600), so it is
        # an environment read in every spelling, reference not call.
        "import time\nx = time.timezone\n": "environment access time.timezone",
        "import time as t\nx = t.timezone\n": "environment access time.timezone",
        "from time import timezone\n": "banned import 'time.timezone'",
    }
    for source, expected in banned_forms.items():
        found = probe(source)
        expectations = (expected,) if isinstance(expected, str) else expected
        for expected_text in expectations:
            assert any(expected_text in v for v in found), (
                f"scan missed {expected_text!r} in {source!r}: {found}"
            )

    # Negative control: the legit datetime use app/ actually has
    # (app/validation/checks.py: `from datetime import date as _date`,
    # used as the `_date(year, month, day)` constructor) plus the
    # non-wall-clock readers and record-attribute `time` (e.g. `raw.time`)
    # must stay clean — over-broadening the family fails here loudly.
    legit = probe(
        "from datetime import date as _date\n"
        "_valid = _date.fromisoformat('2024-01-01')\n"
        "_constructed = _date(2024, 1, 1)\n"
        "_kickoff = entry.time\n"
        "import datetime\n"
        "_iso = datetime.date.fromisoformat('2024-01-01')\n"
        "_ctor_date = datetime.date(2024, 1, 1)\n"
        "_ctor_dt = datetime.datetime(2024, 1, 1, 12, 0)\n"
        "import time\n"
        "_monotonic = time.monotonic()\n"
        "_perf = time.perf_counter()\n"
    )
    assert legit == [], legit

    # Negative control (BUG-T2): only star imports from os, time and
    # datetime are flagged. `from os.path import *` / `from os.path
    # import join` export no os environment names (environ/getenv/
    # environb live in os, not os.path), and `from json import *` exports
    # no banned names at all — a precise three-module rule, not a blanket
    # star-import ban; over-broadening fails here loudly.
    star_clean = probe(
        "from os.path import join\n"
        "from os.path import *\n"
        "from json import *\n"
        "_joined = join('a', 'b')\n"
    )
    assert star_clean == [], star_clean

    # Criterion 12 positive control (relative-import resolution): inside a
    # package __init__ the import base is the package directory itself, never
    # the __init__ module. Otherwise `from ..storage import store` in
    # app/domain/__init__.py resolves one package too deep to
    # "app.domain.storage", which the allowed-set prefix match would accept
    # instead of flagging the true target "app.storage" — a silent evasion
    # of the "no app.storage" clause.
    domain_init_base = import_base_parts_for(APP_DIR / "domain" / "__init__.py")
    assert domain_init_base == ["app", "domain"], domain_init_base
    assert resolve_from(domain_init_base, 2, "storage") == "app.storage"
    assert resolve_from(domain_init_base, 1, "models") == "app.domain.models"

    def init_probe(source: str) -> list[str]:
        return scan_source(
            source, "app/domain/__init__.py", domain_init_base, "app.domain"
        )

    # Regression: level-2 relative import in an app/<pkg>/__init__.py MUST flag.
    flagged = init_probe("from ..storage import store\n")
    assert any("app.storage" in v for v in flagged), flagged

    # Negative control: the level-1 form the real app/domain/__init__.py uses
    # (`from .models import ...`) MUST stay unflagged after the base change.
    unflagged = init_probe("from .models import Match\n")
    assert unflagged == [], unflagged


def test_deterministic_replay_and_order_insensitive_state(tmp_path: Path) -> None:
    # Criterion 13: same file twice in one process -> byte-identical
    # canonical state; a shuffled rewrite in tmp_path -> identical state
    # (iteration is sorted, input order is irrelevant, no randomness).
    first = MatchCollection()
    import_fixture(VALID_1, first)
    second = MatchCollection()
    import_fixture(VALID_1, second)
    assert canonical_state(first) == canonical_state(second)

    payload = json.loads(VALID_1.read_text())
    shuffled = list(payload["matches"])
    random.Random(20261016).shuffle(shuffled)
    assert shuffled != payload["matches"], "seeded shuffle must permute the records"
    copy = tmp_path / "season-1-shuffled.json"
    copy.write_text(json.dumps(payload, indent=2) + "\n")

    from_shuffled = MatchCollection()
    import_fixture(copy, from_shuffled, root=tmp_path)
    assert len(from_shuffled) == len(first)
    assert canonical_state(from_shuffled) == canonical_state(first)


def test_fixtures_checked_in_declare_synthetic() -> None:
    # Criterion 14: every *.json under fixtures/ parses, carries the
    # in-band "synthetic": true marker, and lives under fixtures/ (not
    # the git-ignored data/); fixture paths are repo-root relative.
    fixture_files = set((REPO_ROOT / "fixtures").rglob("*.json"))
    assert fixture_files == EXPECTED_FIXTURES

    for path in sorted(fixture_files):
        payload = json.loads(path.read_text())
        assert payload.get("synthetic") is True, f"{path} lacks the synthetic marker"
        assert path.is_relative_to(REPO_ROOT / "fixtures")
        relative = path.relative_to(REPO_ROOT)
        assert relative.parts[0] == "fixtures", relative

    # Nothing synthetic-marked leaks into the git-ignored data/ area.
    data_dir = REPO_ROOT / "data"
    if data_dir.exists():
        for path in data_dir.rglob("*.json"):
            payload = json.loads(path.read_text())
            assert payload.get("synthetic") is not True, f"{path} is a fixture in data/"

    # The fixtures/ tree is not git-ignored (checked in, per the brief).
    gitignore = {
        line.strip()
        for line in (REPO_ROOT / ".gitignore").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert "fixtures" not in gitignore
    assert "fixtures/" not in gitignore

    # All fixture paths used by this suite resolve relative to the repo root.
    for path in EXPECTED_FIXTURES:
        assert path.is_relative_to(REPO_ROOT)
        assert path.exists()
