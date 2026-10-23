"""Phase 10 acceptance criteria 1-8: operational reliability (HANDOFF IX-10).

TEST-ONLY phase content: the error-handling strand (corrupted-store loud
failure; interrupted multi-insert batch atomicity -- both PINNED AS
PROBED, zero production change), the compile-checks strand extended to
tests/, and source-level structural pins over the architect-sanctioned
AMENDMENT A1 run-structure rework of scripts/health-check.sh (exactly
three inner runs; the Phase 9 A4 determinism mechanism verbatim), the
A2/A4 two-line valve-amendment pattern in tests/test_health_script.py,
and the version-local byte-pins of app/ plus the Phase 9 golden/guard
test files (criterion 8, invariant 9).

No test in this file uses skip or xfail (invariant 6). Load position
(ADV-5): no wall-clock SLA is asserted anywhere here; runtime figures
this phase produces carry their load averages in the protocol docs.
"""

from __future__ import annotations

import dataclasses
import math
import re
import sqlite3
import subprocess
from pathlib import Path

import pytest

# SECTION_HEADERS single source of truth (criterion 6; cross-file import
# in-pattern, as test_backtesting imports test_vocab_guards).
import test_health_script as health

from app.domain import Fixture, MatchCollection, OptionalValue
from app.forecasts import (
    Forecast,
    ForecastConflictError,
    ForecastIntegrityError,
    build_forecast,
    config_identity,
)
from app.ingestion import import_fixture
from app.storage import (
    IDENTITY_COLUMNS,
    get_forecast,
    insert_forecast,
    open_forecasts_db,
    open_read_connection,
    verify_all,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
HEALTH_SCRIPT = REPO_ROOT / "scripts" / "health-check.sh"
HEALTH_TEST = REPO_ROOT / "tests" / "test_health_script.py"
FIXTURES = REPO_ROOT / "fixtures" / "openfootball" / "valid"

# Criterion 8: the version-local byte-pin base (Phase 10's commit). A
# future phase re-points this by named amendment, never widens it.
# Re-pointed by Phase 11 AMENDMENT A10 (8abe1ca), never widened.
PHASE11_COMMIT = "8abe1ca"

# Criterion 8 (Phase 11 AMENDMENT A10, C3 architect-ratified): the
# golden-pin files at this checkpoint, byte-pinned (six files; the
# three amended guards + test_evaluation re-enter at the next re-point).
GOLDEN_PIN_FILES = (
    "tests/test_forecasts.py",
    "tests/test_features.py",
    "tests/test_decisions.py",
    "tests/test_simulation.py",
    "tests/test_poisson_fit.py",
    "tests/test_scoreline_matrix.py",
)

# Criterion 6: the nine pinned header strings in the pinned order --
# an independent local pin AND asserted equal to health.SECTION_HEADERS
# (the tuple may only change through one shared, deliberate edit).
PINNED_SECTION_HEADERS = (
    "last commit",
    "working tree",
    "compile",
    "pytest run 1",
    "pytest run 2",
    "skips/xfails",
    "determinism comparison",
    "pip check",
    "five largest .py files",
)

_collection = MatchCollection()
import_fixture(FIXTURES / "season-1.json", _collection)
import_fixture(FIXTURES / "season-2.json", _collection)
ALL_MATCHES = tuple(record.match for record in _collection.records())

FIXTURE_A = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Coralgate Athletic",
    away="Thistledown Wanderers",
    kickoff=OptionalValue.missing(),
)
FIXTURE_B = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2025-12-31",
    home="Quarryhill Zenith",
    away="Harbourlight Comets",
    kickoff=OptionalValue.missing(),
)
# A third, distinct identity for the interrupted-batch test (criterion 2).
FIXTURE_C = Fixture(
    competition="Obsidian Coast League",
    season="2025-26",
    date="2026-01-02",
    home="Coralgate Athletic",
    away="Quarryhill Zenith",
    kickoff=OptionalValue.missing(),
)


def _forecast_a() -> Forecast:
    return build_forecast(ALL_MATCHES, FIXTURE_A)


def _key(fixt: Fixture) -> tuple[str, str, str, str, str]:
    return (fixt.competition, fixt.season, fixt.date, fixt.home, fixt.away)


def _git_diff(*paths: str) -> str:
    """`git diff <checkpoint commit> -- <paths>` stdout; must exit 0."""
    result = subprocess.run(
        ["git", "diff", PHASE11_COMMIT, "--", *paths],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_corrupted_store_fails_loudly_never_silently(tmp_path: Path) -> None:
    """Criterion 1 (ADV-6): corrupted stores fail LOUDLY, never silently.

    Probe result (2026-10-22, this platform): both corruption shapes
    raise sqlite3.DatabaseError at the FIRST read through the normal
    read path -- the 4 KiB garbage file gives "file is not a database",
    the 512-byte-truncated real DB gives "database disk image is
    malformed" (messages observed, not asserted; the pinned contract is
    the loud TYPE). This is deliberately NOT ForecastIntegrityError:
    that one is the structurally-valid-row content-hash-mismatch path
    (sqlite presents a well-formed row, we recompute and disagree) --
    a different mechanism from "sqlite cannot present a row at all".
    Pinned platform/sqlite-version-local by the golden-discipline rule:
    re-probe on interpreter/sqlite change, never widen the pin to bare
    Exception. The invariant under ANY loud type: raises -- never an
    empty tuple, never garbage, never a warning.
    """
    # (a) 4 KiB of non-sqlite garbage bytes.
    garbage = tmp_path / "garbage.db"
    garbage.write_bytes(b"\xde\xad\xbe\xef" * 1024)
    reader = open_read_connection(str(garbage))  # lazy connect: no read yet
    with pytest.raises(sqlite3.DatabaseError) as verify_error:
        verify_all(reader)
    assert not isinstance(
        verify_error.value, (ForecastIntegrityError, ForecastConflictError)
    )
    with pytest.raises(sqlite3.DatabaseError):
        get_forecast(reader, *_key(FIXTURE_A))
    reader.close()

    # (b) a REAL one-row forecast DB truncated to its first 512 bytes.
    valid = tmp_path / "valid.db"
    writer = open_forecasts_db(str(valid))
    forecast = _forecast_a()
    assert insert_forecast(writer, forecast)
    writer.close()
    truncated = tmp_path / "truncated.db"
    truncated.write_bytes(valid.read_bytes()[:512])

    reader = open_read_connection(str(truncated))
    with pytest.raises(sqlite3.DatabaseError):
        verify_all(reader)
    # The VALID key of the row that existed before truncation: still loud.
    with pytest.raises(sqlite3.DatabaseError):
        get_forecast(reader, *_key(FIXTURE_A))
    reader.close()


def test_interrupted_multi_insert_batch_prior_rows_intact_verify_clean(
    tmp_path: Path,
) -> None:
    # Criterion 2 (ADV-6, journal atomicity pinned as observed): A and B
    # committed; a caller-side batch then inserts C (succeeds) and D --
    # a dataclasses.replace copy of C with dropped_mass nudged by one
    # ulp, so D shares C's identity with different content -- which
    # raises ForecastConflictError MID-BATCH. After the raised exception:
    # prior rows intact, C committed, verify_all returns exactly A, B, C
    # in canonical order with every content hash recomputing clean, the
    # raw row count is exactly 3, and zero partial row for D exists
    # (full-identity probe). No production code changes make this pass --
    # the property is pinned as observed in insert_forecast's per-call
    # BEGIN IMMEDIATE transaction with rollback on exception (the
    # caller-side loop shape is what a batch caller gets for free).
    db = tmp_path / "batch.db"
    writer = open_forecasts_db(str(db))
    forecast_a = _forecast_a()
    forecast_b = build_forecast(ALL_MATCHES, FIXTURE_B)
    forecast_c = build_forecast(ALL_MATCHES, FIXTURE_C)
    assert insert_forecast(writer, forecast_a)
    assert insert_forecast(writer, forecast_b)

    with pytest.raises(ForecastConflictError):
        # The batch: C lands, then D conflicts and rolls back its own
        # transaction only -- the raise is the "interruption".
        assert insert_forecast(writer, forecast_c) is True
        perturbed = dataclasses.replace(
            forecast_c,
            dropped_mass=math.nextafter(forecast_c.dropped_mass, math.inf),
        )
        assert perturbed.content_hash != forecast_c.content_hash  # same identity
        insert_forecast(writer, perturbed)

    # Prior rows intact and hash-clean; C committed; canonical order.
    reader = open_read_connection(str(db))
    verified = verify_all(reader)
    canonical = tuple(
        sorted(
            (forecast_a, forecast_b, forecast_c),
            key=lambda f: (f.competition, f.season, f.date, f.home, f.away),
        )
    )
    assert verified == canonical  # exactly A, B, C, canonical order
    assert tuple(f.content_hash for f in verified) == tuple(
        f.content_hash for f in canonical
    )  # every recomputed content hash equals the original
    reader.close()

    # Zero partial row for D: raw count exactly 3, and exactly one row
    # carries C/D's full identity (D shares every identity column with C).
    raw = sqlite3.connect(str(db))
    assert raw.execute("SELECT COUNT(*) FROM forecasts").fetchone()[0] == 3
    assert len(IDENTITY_COLUMNS) == 10
    identity_where = " AND ".join(f"{column} = ?" for column in IDENTITY_COLUMNS)
    c_identity = (
        forecast_c.competition,
        forecast_c.season,
        forecast_c.date,
        forecast_c.home,
        forecast_c.away,
        forecast_c.as_of,
        forecast_c.fitted.model_version,
        forecast_c.fitted.input_digest,
        config_identity(forecast_c.fitted.config),
        forecast_c.forecast_version,
    )
    assert len(IDENTITY_COLUMNS) == 10
    identity_count = raw.execute(
        f"SELECT COUNT(*) FROM forecasts WHERE {identity_where}", c_identity
    ).fetchone()[0]
    assert identity_count == 1  # only C; no partial/phantom D row
    raw.close()
    writer.close()


def test_compile_section_covers_app_and_tests() -> None:
    # Criterion 3 (decision 8, IX-10 compile checks): the compile
    # invocation covers the whole repo Python surface -- app AND tests --
    # pinned as the exact literal; the section header still precedes it;
    # the section keeps quiet-on-success semantics (-q, `|| true`).
    lines = HEALTH_SCRIPT.read_text(encoding="utf-8").splitlines()
    compile_indices = [i for i, line in enumerate(lines) if "compileall" in line]
    assert len(compile_indices) == 1, compile_indices
    compile_index = compile_indices[0]
    assert "compileall -q app tests" in lines[compile_index]
    assert "-q" in lines[compile_index] and "|| true" in lines[compile_index]
    header_indices = [
        i for i, line in enumerate(lines) if line == 'echo "== compile =="'
    ]
    assert len(header_indices) == 1, header_indices
    assert header_indices[0] < compile_index


def test_health_script_exactly_three_inner_runs_one_rsx_x_sums_from_plain_captures() -> None:
    # Criterion 4 (ADV-2/ADV-4, decisions 1/4/5): the A1 run-structure
    # pin -- exactly THREE `-m pytest` invocations and exactly ONE
    # `-rsxX` in the whole script; the SUM1/SUM2 extraction lines
    # consume PLAIN captures only (run1.out / run3.out -- stable
    # literals fixed by AMENDMENT A1), never a `-m pytest` execution or
    # `-rsxX` output, and both go through the strip_summary pipe. This
    # is the source-level run-count pin (decision 5): behavior is
    # separately pinned end-to-end by the untouched health tests.
    source = HEALTH_SCRIPT.read_text(encoding="utf-8")
    assert source.count("-m pytest") == 3
    assert source.count("-rsxX") == 1
    lines = source.splitlines()
    sum1_lines = [line for line in lines if "SUM1=$(" in line]
    sum2_lines = [line for line in lines if "SUM2=$(" in line]
    assert len(sum1_lines) == 1, sum1_lines
    assert len(sum2_lines) == 1, sum2_lines
    sum1_line, sum2_line = sum1_lines[0], sum2_lines[0]
    for line in (sum1_line, sum2_line):
        assert "-m pytest" not in line
        assert "-rsxX" not in line
        assert "| strip_summary" in line
    assert '"$CAPTURES/run1.out"' in sum1_line
    assert '"$CAPTURES/run3.out"' in sum2_line


def test_health_script_determinism_mechanism_a4_verbatim() -> None:
    # Criterion 5 (invariants 1-2): the Phase 9 A4 determinism mechanism
    # survives A1 byte-verbatim -- strip both timing forms, the
    # counts-only COUNTS_RE pattern, the loud UNPARSEABLE branch echoing
    # both sides, MISMATCH only when both sides parse, the OK emission,
    # and the recursion guard line byte-identical to the committed form.
    source = HEALTH_SCRIPT.read_text(encoding="utf-8")
    assert (
        r"""sed -E 's/in [0-9.]+s//; s/ +\([0-9]+:[0-9]+:[0-9]+\)//; s/ +$//'"""
        in source
    )
    assert r"COUNTS_RE='^[0-9]+ [a-z]+(, [0-9]+ [a-z]+)*$'" in source
    assert (
        'echo "UNPARSEABLE (counts-only comparison expected after stripping):"'
        in source
    )
    assert 'echo "sum 1: $SUM1"' in source
    assert 'echo "sum 2: $SUM2"' in source
    assert 'echo "MISMATCH"' in source
    assert 'echo "OK: $SUM1"' in source
    assert (
        "export PYTEST_ADDOPTS=\"${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }"
        "-k 'not health_script'\"" in source
    )


def test_health_script_section_headers_exactly_nine_verbatim() -> None:
    # Criterion 6 (ADV-7 invariant 3): exactly NINE header-emitting
    # `echo "== ... =="` lines exist (a tenth would fail the untouched
    # header test), and in source order each contains the matching
    # SECTION_HEADERS substring; the shared tuple itself is unchanged --
    # the nine pinned strings, in the pinned order.
    source = HEALTH_SCRIPT.read_text(encoding="utf-8")
    header_lines = [
        line
        for line in source.splitlines()
        if re.fullmatch(r'echo "== .+=="', line)
    ]
    assert len(header_lines) == 9, header_lines
    assert health.SECTION_HEADERS == PINNED_SECTION_HEADERS
    for line, expected in zip(header_lines, PINNED_SECTION_HEADERS):
        assert expected in line, (expected, line)


def test_health_valve_amendment_two_line_pattern_105_lines() -> None:
    # Criterion 7 (ADV-4/ADV-3, A2/A4 pattern discipline): the health
    # test file received EXACTLY the two in-place line edits AMENDMENT
    # A2 pre-authorizes -- module docstring valve figure + citation and
    # the HEALTH_TIMEOUT_S constant line -- 105 -> 105 lines, no
    # assertion changed. (The figure's arithmetic against the
    # load-labeled measurements in PROGRESS-LOG is the reviewer's
    # checklist item, not re-derived here.) No skip/xfail MECHANISM
    # exists in the file; its three test functions remain (the
    # header strings and test names legitimately contain the words).
    text = HEALTH_TEST.read_text(encoding="utf-8")
    lines = text.splitlines()
    assert len(lines) == 105, len(lines)

    constant_lines = [
        line for line in lines if line.startswith("HEALTH_TIMEOUT_S")
    ]
    assert len(constant_lines) == 1, constant_lines
    constant = constant_lines[0]
    figure_match = re.search(r"HEALTH_TIMEOUT_S\s*=\s*(\d+)", constant)
    assert figure_match, constant
    figure = figure_match.group(1)
    assert "AMENDMENT A2 (Phase 10)" in constant
    assert "docs/briefs/phase-10.md" in constant

    # The module docstring's matching valve figure + citation (the other
    # sanctioned line).
    closing = next(
        index
        for index, line in enumerate(lines)
        if index > 0 and line.rstrip().endswith('"""')
    )
    docstring = "\n".join(lines[: closing + 1])
    assert f"timeout {figure} s" in docstring, docstring
    assert "AMENDMENT A2 (Phase 10)" in docstring
    assert "docs/briefs/phase-10.md" in docstring

    for mechanism in (
        "pytest.mark.skip",
        "pytest.mark.xfail",
        "pytest.skip(",
        "pytest.xfail(",
        "skipif",
    ):
        assert mechanism not in text, mechanism
    assert len(re.findall(r"(?m)^def test_", text)) == 3


def test_app_and_golden_files_byte_pinned_vs_phase11() -> None:
    # Criterion 8 (decision 10, invariant 7/E2 + invariant 9): the app/
    # tree is byte-identical to 8abe1ca EXCEPT the two Phase 11
    # sanctioned surfaces (app/storage schema work; the new
    # app/evaluation/ absent at the pinned commit), and the golden-pin
    # and guard test files are byte-identical to that commit. Pin is
    # version-local: a future phase re-points PHASE11_COMMIT by named
    # amendment, never widens.
    assert _git_diff("app/", ":(exclude)app/storage", ":(exclude)app/evaluation") == ""
    assert _git_diff(*GOLDEN_PIN_FILES) == ""
