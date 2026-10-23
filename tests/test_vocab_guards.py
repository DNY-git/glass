"""Phase 8 acceptance criteria 9-13: vocabulary-guard hardening (A4).

The amended scoring guard's segment boundaries with suffixed positive
controls (9), the app-wide scoring scan with its pinned single negation
allowlist (10), the accuracy-trio identifier scan (11), the field-name
shape bans with the score-vocabulary negative regression (12), and the
non-reach pins (13). Single source of truth: SCORING_TOKENS, the
_SCORING_PATTERN machinery and _ACCURACY_PATTERN are IMPORTED from
tests/test_phase7_separation (the Phase 4/5/6 cross-file pattern);
AMENDMENT A1 changed exactly one line there (this file asserts it).

Phase 9 criteria 13-14 (A7, extend-not-weaken) append the outcome-comparative
token set (defined ONCE here; test_backtesting imports it), the field-name-
scope extension of "accuracy", and the extended scans — verbatim else.
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

# Criterion (Phase 11): the ONE structural exemption — the evaluation
# package's own metric identifiers (log_loss, brier, rps + variants) are
# legal HERE and only here. Prefix-scoped, never a per-sentence allowlist.
SCORING_EXEMPT_PREFIXES: tuple[str, ...] = ("app/evaluation/",)

# Criterion 11: the accuracy trio DERIVED from Phase 7's guard of
# record (imported machinery, never a copied list) and pinned.
ACCURACY_TRIO = frozenset(
    re.search(r"\((.*)\)", phase7._ACCURACY_PATTERN.pattern).group(1).split("|")
)

# Criterion 12: segment shapes banned on dataclass field names. The
# score/scoreline/scored vocabulary is deliberately ABSENT — legit
# domain language, 75 real uses (A4; design decision 12). Phase 9 c13
# (A7): "accuracy" JOINS, field-name scope ONLY — prose stays legal.
FIELD_BAN_SEGMENTS = ("performance", "rank", "ranking", "correct", "correctness", "best", "accuracy")
_FIELD_BAN_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, FIELD_BAN_SEGMENTS)) + r")(?![A-Za-z0-9])",
    re.IGNORECASE,
)

# Phase 9 criterion 13 (A7 BLOCKER; design decision 14): the outcome-
# comparative token set — a finite explicit enumeration (the repo's
# banned-set pattern) — compiled STRICT-SEGMENT and defined ONCE here
# (single source; test_backtesting imports it; retools nothing).
OUTCOME_COMPARATIVE_TOKENS = (
    "outperform", "outperforms", "outperformed", "outperforming",
    "beat", "beats", "beaten", "beating", "hit", "hits",
    "winner", "champion", "preferred",
)
_COMPARATIVE_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, OUTCOME_COMPARATIVE_TOKENS)) + r")(?![A-Za-z0-9])",
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
    if rel_path.startswith(SCORING_EXEMPT_PREFIXES):
        return []
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
        if rel.startswith(SCORING_EXEMPT_PREFIXES):
            continue
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
    # NONE of the six pinned-free words; Phase 9 c13 EXTENDS the union.
    banned_union = (
        set(phase7.SCORING_TOKENS) | set(ACCURACY_TRIO)
        | set(FIELD_BAN_SEGMENTS) | set(OUTCOME_COMPARATIVE_TOKENS)
    )
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


# --- Phase 9 criterion 13 (A7 BLOCKER; extend-not-weaken). ---
def test_outcome_comparative_token_guard_positive_and_negative_probes() -> None:
    # The exact 13-tuple of design decision 14, strict-segment, defined ONCE (test_backtesting imports it).
    assert OUTCOME_COMPARATIVE_TOKENS == (
        "outperform", "outperforms", "outperformed", "outperforming",
        "beat", "beats", "beaten", "beating", "hit", "hits",
        "winner", "champion", "preferred",
    )
    assert _COMPARATIVE_PATTERN.pattern == (
        r"(?<![A-Za-z0-9])(" + "|".join(map(re.escape, OUTCOME_COMPARATIVE_TOKENS)) + r")(?![A-Za-z0-9])"
    )
    hits = lambda text: [match.group(0).lower() for match in _COMPARATIVE_PATTERN.finditer(text)]
    # Positive controls: every token bare/suffixed/case-variant flagged;
    # segment-adjacent identifiers flag too (the boundary discipline).
    for token in OUTCOME_COMPARATIVE_TOKENS:
        for form in (token, token.upper(), token.capitalize()):
            for probe in (f"{form} = 1\n", f'x = "{form}"\n', f'"""{form} the field."""\n'):
                assert hits(probe) == [token], (token, probe)
    for probe in ("x_hits", "_hit_", "self.beats", "hit_rate_total", "champion_x"):
        assert hits(probe), probe
    # The existing scoring tokens are UNAFFECTED (extend, never retool).
    assert phase7.SCORING_TOKENS == ("log_loss", "logloss", "brier", "rps", "hit_rate", "calibration")
    assert phase7._scoring_hits("outperform the field\n") == []
    assert phase7._scoring_hits("brier_score = 0.5\n")  # scoring positives intact
    # `accuracy` as a FIELD NAME is flagged; in prose NOT source-banned.
    probe_source = "@dataclass(frozen=True)\nclass Probe:\n    accuracy: float = 0.0\n"
    assert ("Probe", "accuracy") in dataclass_fields(probe_source, "<probe>")
    for name in ("accuracy", "model_accuracy", "Accuracy"):
        assert _FIELD_BAN_PATTERN.search(name), name
    prose = '"""The accuracy of this estimate is not evidence of skill."""\n'
    assert _COMPARATIVE_PATTERN.search(prose) is None
    assert phase7._scoring_hits(prose) == []
    assert phase7._ACCURACY_PATTERN.search(prose) is None  # source scope stays the trio
    # The recorded honesty-docstring uses (probe E7) stay legal app-wide:
    # exactly the recorded (file, line) sites carry the word; no field does.
    recorded_uses = {
        ("app/api/serialize.py", 30), ("app/api/serialize.py", 34), ("app/decisions/constants.py", 31),
        ("app/forecasts/__init__.py", 9), ("app/forecasts/builder.py", 16), ("app/forecasts/record.py", 9),
        ("app/models/__init__.py", 8), ("app/models/poisson.py", 246),
        ("app/models/scoreline.py", 8), ("app/models/scoreline.py", 91),
    }
    found = {
        (rel_of(path), index) for path in app_corpus()
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if re.search(r"(?<![A-Za-z0-9])accuracy(?![A-Za-z0-9])", line, re.IGNORECASE)
    }
    assert found == recorded_uses
    # Negative controls (Phase 8's regression EXTENDED, never replaced):
    # score vocabulary legal everywhere; baseline/metric/word free.
    for name in ("score", "scoreline", "scored", "Score", "invalid_score_shape"):
        assert _COMPARATIVE_PATTERN.search(name) is None, name
        assert not _FIELD_BAN_PATTERN.search(name), name
        assert phase7._scoring_hits(name) == [], name
        assert name.lower() not in ACCURACY_TRIO, name
    banned_union = (
        set(phase7.SCORING_TOKENS) | set(ACCURACY_TRIO)
        | set(FIELD_BAN_SEGMENTS) | set(OUTCOME_COMPARATIVE_TOKENS)
    )
    assert banned_union.isdisjoint({"baseline", "metric", "word", "score", "scoreline", "scored"})


# --- Phase 9 criterion 14 (A7): extended guards, app-wide + app/backtesting. ---
def test_backtesting_package_clean_under_extended_vocab_guards() -> None:
    # (a) App-wide strict-segment scan PLUS comparative tokens: hits at
    # exactly the one pinned allowlist site — no new site added.
    files_with_hits: set[str] = set()
    for path in app_corpus():
        rel = rel_of(path)
        text = path.read_text(encoding="utf-8")
        assert _COMPARATIVE_PATTERN.search(text) is None, rel  # zero comparative hits app-wide
        if rel.startswith(SCORING_EXEMPT_PREFIXES):
            continue
        if phase7._SCORING_PATTERN.search(text):
            files_with_hits.add(rel)
        assert scoring_violations(text, rel) == [], rel
    assert files_with_hits == {SIMULATION_INIT}
    # (b) The extended guards over app/backtesting/**: zero of everything.
    backtesting = sorted((APP_DIR / "backtesting").rglob("*.py"))
    assert len(backtesting) == 6  # the five modules + __init__.py
    for path in backtesting:
        rel = rel_of(path)
        text = path.read_text(encoding="utf-8")
        assert phase7._scoring_hits(text) == [], rel
        assert _COMPARATIVE_PATTERN.search(text) is None, rel
        for class_name, field_name in dataclass_fields(text, rel):
            assert not _FIELD_BAN_PATTERN.search(field_name), (rel, class_name, field_name)
        assert not (identifiers(text, rel) & ACCURACY_TRIO), rel
    # (c) A private scoring or comparative helper in an app/backtesting
    # probe source is flagged INSTANTLY (the no-scoring-helper clause).
    assert phase7._scoring_hits("def brier(matches):\n    return 0.5\n")
    assert _COMPARATIVE_PATTERN.search("def outperform(other):\n    return other\n")
    # (d) match.score reads in baselines.py are NOT flagged (legal domain).
    assert "match.score" in (APP_DIR / "backtesting" / "baselines.py").read_text(encoding="utf-8")
    for probe in ("match.score.home", "outcome = self.score.home > self.score.away",
                  'x = "invalid_score_shape"'):
        assert phase7._scoring_hits(probe) == [], probe
        assert _COMPARATIVE_PATTERN.search(probe) is None, probe


# --- Phase 11 criterion (A8): the ONE structural exemption, both ways. ---
def test_scoring_exemption_prefix_boundary_both_directions() -> None:
    """Scoring identifiers pass ONLY under the app/evaluation/ prefix."""
    probe = "def model_score(predictions):\n    return log_loss(outcome, predictions) * brier(outcome)\n"
    assert scoring_violations(probe, "app/evaluation/metrics.py") == []
    assert scoring_violations(probe, "app/evaluation/evaluate.py") == []
    # Every other path — including siblings of the exempt package —
    # still flags identical text: prefix-scoped, never a wider allowlist.
    for rel in ("app/models/probe.py", "app/backtesting/probe.py",
                "app/evaluationx/probe.py", "app/eval/probe.py"):
        assert scoring_violations(probe, rel), rel
