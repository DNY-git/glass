"""Phase 1 acceptance criteria 7-9: scripts/health-check.sh end to end.

ONE module-scoped subprocess run of the health script is shared by all
three tests: clean environment (any inherited PYTEST_ADDOPTS removed),
cwd = repo root, timeout 300 s (AMENDMENT A2). The script's own pytest runs deselect
these tests via the PYTEST_ADDOPTS recursion guard, so the nested suite
cannot re-spawn the script.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

HEALTH_TIMEOUT_S = 300  # AMENDMENT A2 (Phase 4): 120 -> 300 s, evidence-based; see docs/briefs/phase-4.md

SECTION_HEADERS = (
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


def clean_env() -> dict[str, str]:
    """Inherited environment with any inherited PYTEST_ADDOPTS removed."""
    return {
        key: value
        for key, value in os.environ.items()
        if key != "PYTEST_ADDOPTS"
    }


@pytest.fixture(scope="module")
def health_result() -> subprocess.CompletedProcess[str]:
    """The single shared execution of the health script."""
    return subprocess.run(
        ["bash", "scripts/health-check.sh"],
        cwd=REPO_ROOT,
        env=clean_env(),
        capture_output=True,
        text=True,
        timeout=HEALTH_TIMEOUT_S,
    )


def section(output: str, header: str) -> str:
    """Body of the `== <header> ... ==` section: lines until the next header."""
    lines = output.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("== ") and header in line:
            start = index + 1
            break
    if start is None:
        raise AssertionError(f"section header not found: {header!r}")
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("== "):
            break
        body.append(line)
    return "\n".join(body)


def test_health_script_runs_to_completion(
    health_result: subprocess.CompletedProcess[str],
) -> None:
    assert health_result.returncode == 0, (
        f"exit {health_result.returncode}\n"
        f"stdout:\n{health_result.stdout}\nstderr:\n{health_result.stderr}"
    )
    output = health_result.stdout + health_result.stderr
    assert "There is nothing to check yet" not in output
    for header in SECTION_HEADERS:
        assert header in output, f"missing section header: {header!r}"


def test_health_script_determinism_ok(
    health_result: subprocess.CompletedProcess[str],
) -> None:
    output = health_result.stdout + health_result.stderr
    determinism = section(output, "determinism comparison")
    assert re.search(r"^OK:", determinism, re.MULTILINE), determinism
    assert "MISMATCH" not in output


def test_health_script_no_skips_no_broken_deps(
    health_result: subprocess.CompletedProcess[str],
) -> None:
    output = health_result.stdout + health_result.stderr
    skips = section(output, "skips/xfails")
    assert re.search(r"(?m)^none\s*$", skips), skips
    pip_section = section(output, "pip check")
    assert "No broken requirements found." in pip_section, pip_section
