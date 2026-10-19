"""Phase 8 acceptance criteria 9-13: vocabulary-guard hardening (A4).

The amended scoring guard's segment boundaries with suffixed positive
controls (9), the app-wide scoring scan with its pinned single negation
allowlist (10), the accuracy-trio identifier scan (11), the field-name
shape bans with the score-vocabulary negative regression (12), and the
non-reach pins (13). Single source of truth: SCORING_TOKENS, the
_SCORING_PATTERN machinery and _ACCURACY_PATTERN are IMPORTED from
tests/test_phase7_separation (the Phase 4/5/6 cross-file pattern);
AMENDMENT A1 changed exactly one line there (this file asserts it).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import test_phase7_separation as phase7

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "app"
SIMULATION_INIT = "app/simulation/__init__.py"

# Criterion 10: the ONE pinned (file, exact sentence) negation site —
# the honest docstring, preserved by allowlist, NEVER by deletion.
SCORING_ALLOWLIST: tuple[tuple[str, str], ...] = (
    (SIMULATION_INIT, "MC noise never contaminates log loss, Brier, or RPS."),
)

# Criterion 11: the accuracy trio DERIVED from Phase 7's guard of
# record (imported machinery, never a copied list) and pinned.
ACCURACY_TRIO = frozenset(
    re.search(r"\((.*)\)", phase7._ACCURACY_PATTERN.pattern).group(1).split("|")
)

# Criterion 12: segment shapes banned on dataclass field names. The
# score/scoreline/scored vocabulary is deliberately ABSENT — legit
# domain language, 75 real uses (A4; design decision 12).
FIELD_BAN_SEGMENTS = ("performance", "rank", "ranking", "correct", "correctness", "best")
_FIELD_BAN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, FIELD_BAN_SEGMENTS)) + r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)


def app_corpus() -> list[Path]:
    """Every .py under the REAL app/ tree — the pinned scan corpus."""
    return sorted(APP_DIR.rglob("*.py"))


def rel_of(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _allowlist_spans(text: str, rel_path: str) -> list[tuple[int, int]]:
    """Span of each pinned verbatim sentence for this file; asserts existence."""
    spans = []
    for site_file, sentence in SCORING_ALLOWLIST:
        if site_file != rel_path:
            continue
        start = text.find(sentence)
        assert start >= 0, f"allowlisted sentence missing verbatim in {site_file}"
        spans.append((start, start + len(sentence)))
    return spans


def scoring_violations(text: str, rel_path: str) -> list[str]:
    """Scoring-token hits outside the pinned allowlist spans of this file."""
    spans = _allowlist_spans(text, rel_path)
    return [
        f"{rel_path}: unallowlisted scoring token {match.group(0)!r}"
        for match in phase7._SCORING_PATTERN.finditer(text)
        if not any(start <= match.start() and match.end() <= end for start, end in spans)
    ]


def _is_dataclass(node: ast.ClassDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Name) and target.id == "dataclass":
            return True
        if isinstance(target, ast.Attribute) and target.attr == "dataclass":
            return True
    return False


def dataclass_fields(source: str, display: str) -> list[tuple[str, str]]:
    """(class, field) pairs for every @dataclass under one source."""
    tree = ast.parse(source, filename=display)
    fields: list[tuple[str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and _is_dataclass(node):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    fields.append((node.name, statement.target.id))
    return fields


def identifiers(source: str, display: str) -> set[str]:
    """Lowercased function/class/arg/attribute/keyword/field/Name identifiers."""
    tree = ast.parse(source, filename=display)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[0])
        elif isinstance(node, ast.Name):
            names.add(node.id)
        if isinstance(node, ast.ClassDef) and _is_dataclass(node):
            for statement in node.body:
                if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
                    names.add(statement.target.id)
    return {name.lower() for name in names}


def test_scoring_guard_strict_boundaries_suffixed_positive_control() -> None:
    # A4 BLOCKER (extend-not-weaken): AMENDMENT A1's single line is IN
    # PLACE — the guard of record compiles the segment-boundary form.
    assert phase7._SCORING_PATTERN.pattern == (
        r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, phase7.SCORING_TOKENS)) + r")(?![A-Za-z0-9])"
    )
    assert phase7.SCORING_TOKENS == ("log_loss", "logloss", "brier", "rps", "hit_rate", "calibration")
    assert set(phase7.QUANT_FAMILIES) <= set(phase7.SCORING_TOKENS)

    hits = lambda text: [match.group(0) for match in phase7._SCORING_PATTERN.finditer(text)]

    # Suffixed positive controls: the Phase 7 item-11 gap is CLOSED.
    for probe in ("brier_score = 0.5", "def brier_score(x):\n    return x\n", "x_brier",
                  "_rps_", "self.brier_score", "log_loss_total", "hit_rate_2024"):
        assert hits(probe), probe

    # Every bare token still flags in every spelling form (no Phase 7
    # positive control regressed).
    for token in phase7.SCORING_TOKENS:
        for form in (token, token.upper(), token.capitalize()):
            for probe in (f"{form} = 0.5\n", f'x = "{form}"\n', f"# {form} of the model\n",
                          f'"""{form} estimates."""\n'):
                assert hits(probe), (token, probe)

    # Negative controls: legitimate siblings stay clean.
    for clean in ("log_probs", "probability", "outcome_home", "dropped_mass",
                  "insufficient", "scenario_matrix"):
        for probe in (f"{clean} = 0.5\n", f'"{clean}"\n', f"# {clean}\n", f"total += {clean}\n"):
            assert hits(probe) == [], probe

    # Strict superset of the former \b-form on ASCII (never weakened):
    # every legacy match position is still a match position.
    legacy = re.compile(r"\b(" + "|".join(map(re.escape, phase7.SCORING_TOKENS)) + r")\b", re.IGNORECASE)
    battery = ["brier_score = 1", "x_brier", "_rps_", "calibration_curve", "LOG_LOSS",
               "log_probs", "probability", "scenario_matrix", "insufficient", "dropped_mass"]
    for probe in battery:
        legacy_positions = {match.start() for match in legacy.finditer(probe)}
        strict_positions = {match.start() for match in phase7._SCORING_PATTERN.finditer(probe)}
        assert legacy_positions <= strict_positions, probe


def test_app_wide_scoring_scan_with_pinned_negation_allowlist() -> None:
    # A4: strict-segment scan over the source text of EVERY .py under
    # the real app/ tree; hits permitted at exactly one pinned site.
    scanned = [rel_of(path) for path in app_corpus()]
    assert scanned == [rel_of(path) for path in sorted(APP_DIR.rglob("*.py"))]  # no scope reduction
    for sentinel in ("app/models/poisson.py", "app/forecasts/builder.py", "app/features/compute.py",
                     "app/decisions/builder.py", SIMULATION_INIT, "app/storage/forecasts_db.py"):
        assert sentinel in scanned, sentinel

    # The allowlist is exact and SINGULAR: one (file, exact sentence);
    # a second site anywhere fails the scan below.
    assert SCORING_ALLOWLIST == (
        (SIMULATION_INIT, "MC noise never contaminates log loss, Brier, or RPS."),
    )
    assert len(SCORING_ALLOWLIST) == 1

    # The pinned sentence exists VERBATIM in the named file — deleting
    # or rewording the honest negation docstring fails right here.
    sentence = SCORING_ALLOWLIST[0][1]
    assert sentence in (APP_DIR / "simulation" / "__init__.py").read_text(encoding="utf-8")

    # Every hit of every file lands inside the pinned sentence span.
    files_with_hits: set[str] = set()
    for path in app_corpus():
        rel = rel_of(path)
        text = path.read_text(encoding="utf-8")
        if phase7._SCORING_PATTERN.search(text):
            files_with_hits.add(rel)
        assert scoring_violations(text, rel) == [], rel
    assert files_with_hits == {SIMULATION_INIT}

    # Positive-control probe: a suffixed scoring identifier outside the
    # allowlist is flagged — even appended INSIDE the allowlisted file
    # (only the pinned sentence is ever permitted). Clean probes pass.
    assert scoring_violations("def brier_score(x):\n    return x\n", "app/probe.py")
    allowlisted_text = (APP_DIR / "simulation" / "__init__.py").read_text(encoding="utf-8")
    assert scoring_violations(allowlisted_text + "\n# brier\n", SIMULATION_INIT)
    assert scoring_violations("def ordinary(x):\n    return x\n", "app/probe.py") == []


def test_accuracy_trio_app_wide_identifier_scan() -> None:
    # A4 (design decision 11): identifier scope, NOT source text, over
    # every .py under app/: no function/class/arg/attribute/keyword/
    # dataclass-field name EQUALS the trio (case-insensitive).
    assert ACCURACY_TRIO == {"validated", "accurate", "beating"}
    identifier_hits: set[tuple[str, frozenset[str]]] = set()
    for path in app_corpus():
        found = identifiers(path.read_text(encoding="utf-8"), rel_of(path)) & ACCURACY_TRIO
        if found:
            identifier_hits.add((rel_of(path), frozenset(found)))
    assert identifier_hits == set()

    # Positive controls: each trio token flagged as an identifier.
    for probe, token in (
        ("def validated(): ...\n", "validated"),
        ("class Accurate: ...\n", "accurate"),
        ("def f(beating=1):\n    return beating\n", "beating"),
        ("x = report.validated\n", "validated"),
        ("render(validated=True)\n", "validated"),
        ("import audited as validated\n", "validated"),
    ):
        assert identifiers(probe, "<probe>") & ACCURACY_TRIO == {token}, probe
    # Negative control: the real composite `validated_records` is NOT flagged.
    assert not (identifiers("def validated_records(): ...\n", "<probe>") & ACCURACY_TRIO)

    # WHY source-text scope is not claimed: the five recorded validation-
    # vocabulary (stage sense) comment/docstring uses trip any whole-word
    # source scan by construction — app/domain/models.py:98 and :169,
    # app/ingestion/openfootball.py:103, app/models/poisson.py:84,
    # app/scenarios/spec.py:171. Identifier scope above is clean.
    source_uses = {
        (rel_of(path), index)
        for path in app_corpus()
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if phase7._ACCURACY_PATTERN.search(line)
    }
    assert source_uses == {
        ("app/domain/models.py", 98),
        ("app/domain/models.py", 169),
        ("app/ingestion/openfootball.py", 103),
        ("app/models/poisson.py", 84),
        ("app/scenarios/spec.py", 171),
    }

    # Phase 7's in-package source-text _ACCURACY_PATTERN stays untouched
    # and green in the same suite (extend, never replace).
    assert phase7._ACCURACY_PATTERN.pattern == r"\b(validated|accurate|beating)\b"
    for path in sorted((APP_DIR / "decisions").rglob("*.py")):
        assert not phase7._ACCURACY_PATTERN.search(path.read_text(encoding="utf-8")), path.name


def test_field_name_bans_performance_rank_correct_best_but_never_score() -> None:
    # A4 BLOCKER: the shape ban over every dataclass field under app/ —
    # zero real matches today (probed: 28 dataclasses, 186 fields).
    class_count = 0
    field_count = 0
    for path in app_corpus():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=rel_of(path))
        class_count += sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and _is_dataclass(node)
        )
        for class_name, field_name in dataclass_fields(source, rel_of(path)):
            field_count += 1
            assert not _FIELD_BAN_PATTERN.search(field_name), (rel_of(path), class_name, field_name)
    assert class_count > 0 and field_count > 0  # non-vacuous

    # Positive controls: the brief's probe shapes are all flagged.
    for probe in ("performance_score", "rank", "best_xg", "performance", "ranking",
                  "correct", "correctness", "Ranking"):
        assert _FIELD_BAN_PATTERN.search(probe), probe

    # NEGATIVE regression: score/scoreline/scored vocabulary is NEVER
    # flagged by ANY guard this phase — the ban must not overreach
    # (legitimate domain language; ambiguity recorded in KNOWN-LIMITATIONS).
    for name in ("Score", "score", "scoreline", "scored", "invalid_score_shape",
                 "home_goals_scored_form", "away_goals_scored_form"):
        assert not _FIELD_BAN_PATTERN.search(name), name
        assert phase7._scoring_hits(name) == [], name
        assert name.lower() not in ACCURACY_TRIO, name
    # Those names are REAL app vocabulary, not strawmen.
    from app.domain import Score  # noqa: F401 - the real domain class exists
    assert "invalid_score_shape" in (APP_DIR / "validation" / "checks.py").read_text(encoding="utf-8")
    assert (APP_DIR / "models" / "scoreline.py").exists()
    real_fields = {
        field_name
        for path in app_corpus()
        for _, field_name in dataclass_fields(path.read_text(encoding="utf-8"), rel_of(path))
    }
    assert {"score", "home_goals_scored_form", "away_goals_scored_form"} <= real_fields


def test_source_ban_non_reach_pinned_baseline_metric_word() -> None:
    # The union of every source-banned set this phase ships — scoring
    # tokens (IMPORTED), accuracy trio (DERIVED from the pattern of
    # record), field-name shapes (local, single source here) — reaches
    # NONE of the six pinned-free words, in both directions.
    banned_union = set(phase7.SCORING_TOKENS) | set(ACCURACY_TRIO) | set(FIELD_BAN_SEGMENTS)
    free_words = {"baseline", "metric", "word", "score", "scoreline", "scored"}
    assert banned_union.isdisjoint(free_words)
    for free_word in free_words:
        assert free_word not in banned_union
    for token in banned_union:
        assert token not in free_words

    # A probe carrying the sanctioned negation phrasing and every free
    # word passes EVERY guard this phase ships.
    probe = (
        '"""no scoring metric ships this phase: baseline, scoreline."""\n'
        "def evaluate(baseline, scoreline, metric, word, scored):\n"
        "    return baseline + scoreline + metric + word + scored\n"
    )
    assert phase7._scoring_hits(probe) == []
    assert not _FIELD_BAN_PATTERN.search(probe)
    assert not (identifiers(probe, "<probe>") & ACCURACY_TRIO)
    assert not (identifiers("baseline = 1\nscoreline = 2\nmetric = 3\n", "<probe>") & ACCURACY_TRIO)
