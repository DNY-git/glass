"""Phase 4 acceptance criteria 16-19: separation rules for the new packages.

The phase's OWN new separation test — the 614-line hygiene file keeps
its unconditional network/star/wall-clock/environment scans over both
new packages (via AMENDMENT A1's two entries) and never grows again
here. These tests enforce the stricter Phase 4 rules with positive and
negative probes pinning every ban in both directions: `random`
confined to the designated simulation module (16), RNG discipline in
the simulation module — no global seeding, no module-level RNG state,
no unseeded or non-`seed` Random, no hash()/time/urandom/secrets/uuid/
id() seed sources, `random()`-only draws (17), stdlib+app import
allowlists for both packages (18), and the pinned AMENDMENT A1 entries
with a clean full-app hygiene scan (19).
"""

from __future__ import annotations

import ast
from pathlib import Path

# Reuse Phase 2's scan machinery: import resolution, alias handling,
# wall-clock/environment detection — extended, never weakened.
import test_fixtures_and_hygiene as hygiene

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
SIMULATION_DIR = APP_DIR / "simulation"
SCENARIOS_DIR = APP_DIR / "scenarios"

# Criterion 16: the ONE module under app/ permitted to import `random`
# (file-level allowlist constant — the designated randomness module).
DESIGNATED_RANDOM_MODULE = "app.simulation.simulate"


def scan_random_usage(source: str, display: str, *, package: str) -> list[str]:
    """Criterion 16 violations: `random` outside the designated module.

    Flags every `import random` / `from random import ...` form and
    every bare `random` name reference, except when the scan context
    IS the designated module (file-level allowlist). Package is the
    dotted module name (hygiene.module_name_for), e.g.
    "app.scenarios.apply" or "app.simulation.simulate".
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []
    designated = package == DESIGNATED_RANDOM_MODULE

    def complain(message: str, lineno: int) -> None:
        violations.append(f"{display}: {message} (line {lineno})")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "random" or alias.name.startswith("random."):
                    if not designated:
                        complain(f"randomness import {alias.name!r}", node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            module = node.module or ""
            if module == "random" or module.startswith("random."):
                if not designated:
                    complain(f"randomness import {module!r}", node.lineno)

    if not designated:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "random":
                complain("random reference outside the designated module", node.lineno)

    return violations


# Criterion 17: draw methods banned in the simulation module — only
# rng.random() is sequence-stable across Python versions (A2).
BANNED_DRAW_METHODS = {
    "randrange",
    "randint",
    "choice",
    "choices",
    "sample",
    "getrandbits",
    "shuffle",
}
# Criterion 17: modules banned as seed sources (A1).
BANNED_SEED_SOURCE_IMPORTS = {"time", "secrets", "uuid"}


def _target_names(target: ast.expr) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(target):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names


def _rng_construction_message(call: ast.Call) -> str | None:
    """Unseeded / non-seed-argument complaint for one constructor call.

    Shared by EVERY spelling of the RNG-constructor ban — the
    qualified ``random.Random(...)`` and every renamed alias (an
    import alias such as ``Random as R2`` or a local binding such as
    ``r = random.Random``) — so a rename can never loosen the seeding
    rule (tester hardening F1, evasions a and e).
    """
    if not call.args and not call.keywords:
        return "unseeded random.Random()"
    bare_seed = (
        len(call.args) == 1
        and not call.keywords
        and isinstance(call.args[0], ast.Name)
        and call.args[0].id == "seed"
    )
    if not bare_seed:
        return "random.Random() with a non-seed argument"
    return None


def scan_rng_discipline(source: str, display: str) -> list[str]:
    """Criterion 17 violations in one simulation-module source.

    Banned forms (each pinned by a positive probe below): global
    seeding via .seed(...); a module-level RNG binding (target named
    Random/random, or any module-scope assignment constructing or
    binding random.Random); random.Random() with zero args (unseeded);
    random.Random(<arg>) where the arg is not the bare identifier
    `seed`; any hash() call; time/secrets/uuid imports, os.urandom,
    and id() calls as seed sources; and .randrange/.randint/.choice/
    .choices/.sample/.getrandbits/.shuffle attribute calls on any
    receiver.

    Renamed spellings of the very same bans are caught on top (tester
    hardening F1 — every evasion below was probed green before the
    fix): (a) any ``from random import Random`` under ANY alias, with
    calls to that alias checked by the same unseeded/non-seed rule;
    (b) any ``from random import <banned draw method>`` under any
    alias, with calls to that alias flagged as the banned draw;
    (c) ``_inst`` attribute/name access — the module-global RNG
    instance (``random._inst``), in any binding form;
    (d) ``SystemRandom`` anywhere (OS entropy: output can never be
    bit-identical), qualified, from-imported, or locally aliased;
    (e) names bound from the ``random.Random`` class itself
    (``r = random.Random``), whose calls obey the construction rule.
    Every ``from random import ...`` of any other name is flagged too
    — the module's contract is ``import random`` + qualified access
    only, so no imported symbol can smuggle global or unseeded state.
    """
    tree = ast.parse(source, filename=display)
    violations: list[str] = []

    def complain(message: str, lineno: int) -> None:
        violations.append(f"{display}: {message} (line {lineno})")

    # --- Pass 1: names bound to the banned random-module objects, so
    # a renamed spelling is known before any call site is inspected.
    random_ctor_names: set[str] = set()
    system_rng_names: set[str] = set()
    banned_draw_aliases: dict[str, str] = {}

    # F1(a)/(b)/(d)/(c): every `from random import ...` form — and the
    # Random / SystemRandom / banned-draw / _inst names are tracked so
    # their ALIASED call sites are checked as well.
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level != 0:
            continue
        module = node.module or ""
        if module != "random" and not module.startswith("random."):
            continue
        for alias in node.names:
            complain(f"banned from-import of {alias.name!r} from {module!r}", node.lineno)
            bound = alias.asname or alias.name
            if alias.name == "Random":
                random_ctor_names.add(bound)
            elif alias.name == "SystemRandom":
                system_rng_names.add(bound)
            elif alias.name in BANNED_DRAW_METHODS:
                banned_draw_aliases[bound] = alias.name

    # F1(e)/(d): names bound from the banned class objects themselves
    # (``r = random.Random``, ``SR = random.SystemRandom``) in any
    # scope — only the class reference binds, never its construction.
    def bound_random_class(value: ast.expr) -> str | None:
        if isinstance(value, ast.Attribute):
            return value.attr if value.attr in {"Random", "SystemRandom"} else None
        if isinstance(value, ast.Name):
            if value.id in random_ctor_names:
                return "Random"
            if value.id in system_rng_names:
                return "SystemRandom"
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        bound_class = bound_random_class(value)
        if bound_class is None:
            continue
        for target in targets:
            for name in _target_names(target):
                if bound_class == "Random":
                    random_ctor_names.add(name)
                else:
                    system_rng_names.add(name)

    for node in ast.walk(tree):
        # R1: global seeding — .seed(...) on any receiver.
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "seed"
        ):
            complain("global seeding via .seed()", node.lineno)
            continue

        # R3/R4: construction of the RNG itself — the qualified
        # spelling AND every renamed alias (F1 a/e).
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "Random":
                message = _rng_construction_message(node)
            elif isinstance(node.func, ast.Name) and node.func.id in random_ctor_names:
                message = _rng_construction_message(node)
            else:
                message = None
            if message is not None:
                complain(message, node.lineno)

            # F1(b): a banned draw method called under an alias bound
            # from `from random import <method> ...`.
            if isinstance(node.func, ast.Name) and node.func.id in banned_draw_aliases:
                complain(
                    f"banned draw method .{banned_draw_aliases[node.func.id]}",
                    node.lineno,
                )

            # F1(d): a SystemRandom constructor called under a renamed
            # alias (the literal `SystemRandom` spelling is flagged by
            # the general rule below).
            if (
                isinstance(node.func, ast.Name)
                and node.func.id in system_rng_names
                and node.func.id != "SystemRandom"
            ):
                complain("non-deterministic random.SystemRandom", node.lineno)

        # R5: hash()-derived seeds (salted per process for str; would
        # also break cross-process bit-identity).
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "hash":
                complain("hash() call", node.lineno)
            elif node.func.id == "id":
                complain("id() call as a seed source", node.lineno)

        # R6: urandom as a seed source, on any receiver.
        if isinstance(node, ast.Attribute) and node.attr == "urandom":
            complain("urandom access", node.lineno)

        # R7: banned draw methods on any receiver (A2: random() only).
        if isinstance(node, ast.Attribute) and node.attr in BANNED_DRAW_METHODS:
            complain(f"banned draw method .{node.attr}", node.lineno)

        # F1(c)/(d): the private module-global RNG instance and the
        # OS-entropy RNG, under any receiver spelling (qualified or
        # aliased module binding) and any bare-name binding.
        if isinstance(node, ast.Attribute):
            if node.attr == "_inst":
                complain(
                    "module-global RNG instance binding via random._inst",
                    node.lineno,
                )
            elif node.attr == "SystemRandom":
                complain("non-deterministic random.SystemRandom", node.lineno)
        elif isinstance(node, ast.Name):
            if node.id == "_inst":
                complain(
                    "module-global RNG instance binding via random._inst",
                    node.lineno,
                )
            elif node.id == "SystemRandom":
                complain("non-deterministic random.SystemRandom", node.lineno)

    # R6: time/secrets/uuid imports banned in the simulation module.
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            targets = [node.module or ""]
        else:
            continue
        for target in targets:
            if target.split(".")[0] in BANNED_SEED_SOURCE_IMPORTS:
                complain(f"banned seed-source import {target!r}", node.lineno)

    # R2: module-level RNG binding — no global random state may exist.
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
            value: ast.expr | None = statement.value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets = [statement.target]
            value = statement.value
        else:
            continue
        if any(_target_names(target) & {"Random", "random"} for target in targets):
            complain("module-level RNG binding", statement.lineno)
        if value is not None:
            for node in ast.walk(value):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == "Random":
                        complain("module-level RNG binding", statement.lineno)
                        break
                elif isinstance(node, ast.Attribute) and node.attr == "Random":
                    complain("module-level RNG binding", statement.lineno)
                    break

    return violations


# Criterion 18: per-package import allowlists (brief's exact sets;
# hashlib whitelisted-but-unused so the reserved child-seed mechanism
# sha256(master || canonical_key) can never force an allowlist edit).
PACKAGE_STDLIB: dict[str, set[str]] = {
    "app.simulation": {
        "__future__",
        "dataclasses",
        "typing",
        "math",
        "enum",
        "random",
        "bisect",
        "hashlib",
    },
    "app.scenarios": {"__future__", "dataclasses", "typing", "enum", "math"},
}
PACKAGE_APP_IMPORTS: dict[str, set[str]] = {
    "app.simulation": {"app.models", "app.scenarios", "app.simulation"},
    "app.scenarios": {"app.domain", "app.models", "app.scenarios"},
}


def scan_package_imports(
    source: str, display: str, base_parts: list[str], package: str
) -> list[str]:
    """Criterion 18 violations in one module of a new package.

    Stdlib whitelist + per-package app allowlist + the Phase 2 banned
    sets (network, filesystem, star imports), open() — and the
    wall-clock/environment detection resolved through the same alias
    machinery as Phase 2's criterion-12 scan (reused, never weakened).
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
            if top_level in hygiene.BANNED_TOP_LEVEL_IMPORTS:
                complain(f"banned import {target!r}", node.lineno)
            if top_level in hygiene.BANNED_PURITY_IMPORTS:
                complain(f"filesystem/environment import {target!r}", node.lineno)
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
                    complain(
                        f"app import {target!r} outside allowed set", node.lineno
                    )
            elif top_level not in stdlib:
                complain(
                    f"import {target!r} outside the package stdlib allowlist",
                    node.lineno,
                )

    # No open() anywhere in either new package (no I/O, ever).
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "open"
        ):
            complain("open() call", node.lineno)

    # Wall-clock and environment reads, resolved through Phase 2's
    # alias machinery (qualified, aliased, from-imported spellings).
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


def test_random_confined_to_designated_simulation_module_with_probes() -> None:
    # Criterion 16: AST scan of every .py under app/ — any `import
    # random` / `from random import ...` form (and any bare `random`
    # name reference) is flagged except in the designated module
    # app/simulation/simulate.py (file-level allowlist). Both
    # directions pinned by probes.
    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    violations = [
        violation
        for path in app_files
        for violation in scan_random_usage(
            path.read_text(),
            str(path.relative_to(REPO_ROOT)),
            package=hygiene.module_name_for(path),
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str, package: str) -> list[str]:
        return scan_random_usage(source, "<probe>", package=package)

    # Positive controls: the same banned forms flagged in every
    # non-designated context — app.scenarios, app.models, the
    # simulation package's own __init__/constants, and any other app
    # package.
    banned_forms = ("import random\n", "from random import Random\n")
    non_designated = (
        "app.scenarios.apply",
        "app.scenarios.spec",
        "app.models.scoreline",
        "app.simulation",
        "app.simulation.constants",
        "app.domain",
        "app.ingestion",
    )
    for source in banned_forms:
        for package in non_designated:
            found = probe(source, package)
            assert found, f"scan missed {source!r} under {package}"
    # Aliased import form and the bare name reference.
    assert probe("import random as rr\n", "app.scenarios.apply")
    assert probe("x = random.random()\n", "app.models.poisson")

    # Negative control: under the designated module context the very
    # same import is allowed — and a legit non-random module stays
    # clean (over-broadening fails here loudly).
    for source in banned_forms:
        assert probe(source, DESIGNATED_RANDOM_MODULE) == []
    legit = "import math\ndef rate(mu: float, alpha: float) -> float:\n    return math.exp(mu + alpha)\n"
    assert probe(legit, "app.models.scoreline") == []
    assert probe(legit, DESIGNATED_RANDOM_MODULE) == []


def test_simulation_rng_discipline_ast() -> None:
    # Criterion 17: AST scan of app/simulation/*.py, each banned form
    # flagged by a probe (positive controls), every legitimate shape
    # passing (negative controls).
    simulation_files = sorted(SIMULATION_DIR.rglob("*.py"))
    assert simulation_files, "no Python files found under app/simulation/"
    violations = [
        violation
        for path in simulation_files
        for violation in scan_rng_discipline(
            path.read_text(), str(path.relative_to(REPO_ROOT))
        )
    ]
    assert violations == [], "\n".join(violations)

    def probe(source: str) -> list[str]:
        return scan_rng_discipline(source, "<probe>")

    # Positive controls: source -> every expected report substring.
    banned_forms: dict[str, str | tuple[str, ...]] = {
        # Global seeding (never random.seed(), instance-only only).
        "import random\nrandom.seed(42)\n": "global seeding via .seed()",
        # Module-level RNG binding, both spellings.
        "_rng = random.Random(seed)\n": "module-level RNG binding",
        "random = None\n": "module-level RNG binding",
        # Unseeded instance.
        "def make():\n    return random.Random()\n": "unseeded random.Random()",
        # Non-seed arguments: digests, parameter values, hash().
        "def make(d):\n    return random.Random(d)\n": (
            "random.Random() with a non-seed argument",
        ),
        "def make(p):\n    return random.Random(p.input_digest)\n": (
            "random.Random() with a non-seed argument",
        ),
        "def make():\n    return random.Random(hash(salt))\n": (
            "random.Random() with a non-seed argument",
            "hash() call",
        ),
        # hash() / id() as seed sources.
        "x = hash(salt)\n": "hash() call",
        "x = id(obj)\n": "id() call as a seed source",
        # time / secrets / uuid imports; os.urandom.
        "import time\n": "banned seed-source import 'time'",
        "import secrets\n": "banned seed-source import 'secrets'",
        "import uuid\n": "banned seed-source import 'uuid'",
        "import os\nx = os.urandom(4)\n": "urandom access",
        # Banned draw methods, on any receiver.
        "def go(seed):\n    rng = random.Random(seed)\n    rng.randrange(10)\n": (
            "banned draw method .randrange"
        ),
        "def go(seed):\n    rng = random.Random(seed)\n    rng.randint(0, 1)\n": (
            "banned draw method .randint"
        ),
        "def go(seed):\n    rng = random.Random(seed)\n    rng.choice([1])\n": (
            "banned draw method .choice"
        ),
        "def go(seed):\n    rng = random.Random(seed)\n    rng.choices([1])\n": (
            "banned draw method .choices"
        ),
        "def go(seed):\n    rng = random.Random(seed)\n    rng.sample([1], 1)\n": (
            "banned draw method .sample"
        ),
        "def go(seed):\n    rng = random.Random(seed)\n    rng.getrandbits(8)\n": (
            "banned draw method .getrandbits"
        ),
        "def go(seed):\n    rng = random.Random(seed)\n    rng.shuffle([1])\n": (
            "banned draw method .shuffle"
        ),
        "random.choice([1, 2])\n": "banned draw method .choice",
        # F1(a): renamed constructor via from-import — flagged at the
        # import (even the seeded spelling) AND at the unseeded /
        # non-seed-argument call site.
        "from random import Random as R2\ndef f(seed):\n    return R2(seed)\n": (
            "banned from-import of 'Random' from 'random'",
        ),
        "from random import Random as R2\ndef f():\n    return R2()\n": (
            "banned from-import of 'Random' from 'random'",
            "unseeded random.Random()",
        ),
        "from random import Random as R2\ndef f(d):\n    return R2(d)\n": (
            "banned from-import of 'Random' from 'random'",
            "random.Random() with a non-seed argument",
        ),
        "from random import Random\ndef f():\n    return Random()\n": (
            "banned from-import of 'Random' from 'random'",
            "unseeded random.Random()",
        ),
        # F1(b): from-imported banned draw method, aliased and plain —
        # the import AND the aliased call are both flagged (qualified
        # `random.randrange(10)` / `random.choice(...)` above).
        "from random import randrange as rr\ndef f():\n    return rr(3)\n": (
            "banned from-import of 'randrange' from 'random'",
            "banned draw method .randrange",
        ),
        "from random import choice\ndef f():\n    return choice([1])\n": (
            "banned from-import of 'choice' from 'random'",
            "banned draw method .choice",
        ),
        # F1(c): the private module-global RNG instance, under the
        # qualified, aliased-module, and from-import spellings.
        "import random\n_GLOBAL = random._inst\n": (
            "module-global RNG instance binding via random._inst",
        ),
        "import random as rnd\n_GLOBAL = rnd._inst\n": (
            "module-global RNG instance binding via random._inst",
        ),
        "from random import _inst\n_GLOBAL = _inst\n": (
            "banned from-import of '_inst' from 'random'",
            "module-global RNG instance binding via random._inst",
        ),
        # F1(d): OS-entropy RNG — qualified, aliased import, and
        # aliased class binding.
        "import random\nx = random.SystemRandom().random()\n": (
            "non-deterministic random.SystemRandom",
        ),
        "import random\n_R = random.SystemRandom\n": (
            "non-deterministic random.SystemRandom",
        ),
        "from random import SystemRandom as SR\ndef f():\n    return SR().random()\n": (
            "banned from-import of 'SystemRandom' from 'random'",
            "non-deterministic random.SystemRandom",
        ),
        # F1(e): aliased unseeded / non-seed construction.
        "import random\ndef f():\n    r = random.Random\n    return r()\n": (
            "unseeded random.Random()",
        ),
        "import random\ndef f(d):\n    r = random.Random\n    return r(d)\n": (
            "random.Random() with a non-seed argument",
        ),
        # Every other from-random import is refused too (module
        # contract: `import random` + qualified access only).
        "from random import random as _draw\ndef f():\n    return _draw()\n": (
            "banned from-import of 'random' from 'random'",
        ),
        "from random import *\n": "banned from-import of '*' from 'random'",
    }
    for source, expected in banned_forms.items():
        found = probe(source)
        expectations = (expected,) if isinstance(expected, str) else expected
        for expected_text in expectations:
            assert any(expected_text in v for v in found), (
                f"scan missed {expected_text!r} in {source!r}: {found}"
            )

    # Negative controls: the shapes the real module legitimately uses
    # must stay clean — over-broadening fails here loudly.
    legit_module = (
        "import bisect\n"
        "import random\n"
        "def run(seed, table, u):\n"
        "    rng = random.Random(seed)\n"
        "    value = rng.random()\n"
        "    return bisect.bisect_left(table, value) + u\n"
    )
    assert probe(legit_module) == [], probe(legit_module)
    assert probe("import random\n") == []
    assert probe("def make(seed):\n    rng = random.Random(seed)\n    return rng\n") == []
    assert probe("import bisect\ndef at(table, u):\n    return bisect.bisect_left(table, u)\n") == []
    assert probe("def draw(rng):\n    return rng.random()\n") == []
    # Module-level constants are not RNG bindings.
    assert probe("DEFAULT_N_SIMS = 10_000\n") == []
    # F1 negative controls: an INSTANCE alias (a fresh seeded
    # construction — not the class itself) stays a legal local binding,
    # and the sanctioned draw under an aliased `import random as ...`
    # stays legal — over-broadening from the F1 hardening fails loudly.
    assert (
        probe(
            "import random\ndef f(seed):\n"
            "    r = random.Random(seed)\n"
            "    return r.random()\n"
        )
        == []
    )
    assert (
        probe(
            "import random as rnd\ndef f(seed):\n"
            "    r = rnd.Random(seed)\n"
            "    return r.random()\n"
        )
        == []
    )


def test_new_package_import_allowlists() -> None:
    # Criterion 18: app/simulation imports only its stdlib whitelist
    # plus app.models/app.scenarios/app.simulation; app/scenarios only
    # its stdlib whitelist plus app.domain/app.models/app.scenarios;
    # both packages: no open()/os/sys/pathlib/io, no network or
    # database, no wall-clock or environment forms (Phase 2 machinery
    # reused). Probes pin both directions for BOTH packages.
    for directory, package in (
        (SIMULATION_DIR, "app.simulation"),
        (SCENARIOS_DIR, "app.scenarios"),
    ):
        package_files = sorted(directory.rglob("*.py"))
        assert package_files, f"no Python files found under {directory}"
        violations = [
            violation
            for path in package_files
            for violation in scan_package_imports(
                path.read_text(),
                str(path.relative_to(REPO_ROOT)),
                hygiene.import_base_parts_for(path),
                package,
            )
        ]
        assert violations == [], "\n".join(violations)

    def probe(source: str, package: str) -> list[str]:
        return scan_package_imports(
            source, "<probe>", ["app", package.split(".")[1]], package
        )

    banned_forms: dict[str, str | tuple[str, ...]] = {
        # Filesystem/environment plumbing (both packages).
        "import os\n": "filesystem/environment import 'os'",
        "import sys\n": "filesystem/environment import 'sys'",
        "import pathlib\nx = pathlib.Path('.')\n": (
            "filesystem/environment import 'pathlib'"
        ),
        "from io import open\n": "filesystem/environment import 'io'",
        "x = open('data.json')\n": "open() call",
        # Storage/network/database (both packages).
        "import sqlite3\n": "banned import 'sqlite3'",
        "import urllib.request\n": "banned import 'urllib.request'",
        "import http.client\n": "banned import 'http.client'",
        "import socket\n": "banned import 'socket'",
        "import requests\n": "banned import 'requests'",
        "import fastapi\n": "banned import 'fastapi'",
        # Outside the stdlib whitelist of either package.
        "import json\n": "outside the package stdlib allowlist",
        # Wall-clock and environment forms (Phase 2 detection reused).
        "import datetime\nx = datetime.datetime.now()\n": (
            "outside the package stdlib allowlist",
            "wall-clock access datetime.datetime.now",
        ),
        "import time\nx = time.time()\n": ("wall-clock access time.time",),
        "import os\nx = os.environ['PATH']\n": "environment access os.environ",
        "import os\nx = os.getenv('HOME')\n": "environment access os.getenv",
        "from time import gmtime\n": "banned import 'time.gmtime'",
        "from os import environ\n": "filesystem/environment import 'os'",
        "from os import *\n": (
            "banned star import 'os'",
            "filesystem/environment import 'os'",
        ),
        # app imports outside the package's own allowlist.
        "from app.storage import store\n": "outside allowed set",
        "import app.api\n": "outside allowed set",
    }
    for source, expected in banned_forms.items():
        for package in ("app.simulation", "app.scenarios"):
            found = probe(source, package)
            expectations = (expected,) if isinstance(expected, str) else expected
            for expected_text in expectations:
                assert any(expected_text in v for v in found), (
                    f"{package} scan missed {expected_text!r} in {source!r}: {found}"
                )

    # Package-specific app allowlist: app.domain is legal in
    # app/scenarios (A1) but NOT in app/simulation (A1: no app.domain).
    assert probe("from app.domain import Match\n", "app.scenarios") == []
    assert probe("from app.domain import Match\n", "app.simulation")
    # Intra-package imports stay legal in both.
    assert probe("from .spec import Scenario\n", "app.scenarios") == []
    assert probe("from .constants import DEFAULT_N_SIMS\n", "app.simulation") == []

    # Negative control: the real shapes each package uses must stay
    # clean (whitelisted-but-used, whitelisted-but-unused alike).
    legit_simulation = (
        "from __future__ import annotations\n"
        "import bisect\n"
        "import math\n"
        "import random\n"
        "from dataclasses import dataclass\n"
        "from typing import Sequence\n"
        "from app.models import FittedParams, ScorelineMatrix\n"
        "from app.scenarios import Scenario, scenario_matrix\n"
        "from .constants import DEFAULT_N_SIMS, SIM_VERSION\n"
        "@dataclass(frozen=True)\n"
        "class Record:\n"
        "    seed: int\n"
        "def run(seed: int, table: Sequence[float]) -> int:\n"
        "    rng = random.Random(seed)\n"
        "    return bisect.bisect_left(table, rng.random())\n"
    )
    assert probe(legit_simulation, "app.simulation") == []

    legit_scenarios = (
        "from __future__ import annotations\n"
        "import enum\n"
        "import math\n"
        "from dataclasses import dataclass\n"
        "from typing import Sequence\n"
        "from app.domain import Match\n"
        "from app.models import FittedParams\n"
        "from .spec import Scenario\n"
        "def apply(match: Match, scenario: Scenario, factor: float) -> float:\n"
        "    return math.isfinite(factor)\n"
    )
    assert probe(legit_scenarios, "app.scenarios") == []


def test_hygiene_amendment_entries_pinned_and_scan_clean() -> None:
    # Criterion 19: AMENDMENT A1 pinned — exactly seven keys, the five
    # legacy values untouched (append-only protection), the two new
    # values exactly as sanctioned; and hygiene.scan_file over every
    # .py under app/ completes with zero violations and no KeyError —
    # proof the amendment closed the coverage gap without relaxing
    # any check (a KeyError would fail this test as an error).
    expected_legacy: dict[str, set[str]] = {
        "app": set(),
        "app.domain": {"app.domain"},
        "app.validation": {"app.domain", "app.validation"},
        "app.ingestion": {"app.domain", "app.validation", "app.ingestion"},
        "app.models": {"app.domain", "app.models"},
    }
    assert len(hygiene.ALLOWED_APP_IMPORTS) == 7
    assert set(hygiene.ALLOWED_APP_IMPORTS) == set(expected_legacy) | {
        "app.scenarios",
        "app.simulation",
    }
    for package, allowed in expected_legacy.items():
        assert hygiene.ALLOWED_APP_IMPORTS[package] == allowed

    # AMENDMENT A1's two sanctioned values, quoted verbatim (brief
    # section "Source of truth for the allowed sets").
    assert hygiene.ALLOWED_APP_IMPORTS["app.scenarios"] == {
        "app.domain",
        "app.models",
        "app.scenarios",
    }
    assert hygiene.ALLOWED_APP_IMPORTS["app.simulation"] == {
        "app.models",
        "app.scenarios",
        "app.simulation",
    }

    app_files = sorted(APP_DIR.rglob("*.py"))
    assert app_files, "no Python files found under app/"
    for path in app_files:
        violations = hygiene.scan_file(path)
        assert violations == [], f"{path}: {violations}"
