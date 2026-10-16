"""Phase 1 acceptance criteria 1-6: foundation wiring.

Hermetic by construction: local subprocesses only, no network, no wall
clock, no randomness. Every subprocess runs from the repository root
with any inherited PYTEST_ADDOPTS removed.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
VENV_PYTEST = REPO_ROOT / ".venv" / "bin" / "pytest"

SUBPROCESS_TIMEOUT_S = 120


def clean_env() -> dict[str, str]:
    """Inherited environment with any inherited PYTEST_ADDOPTS removed."""
    return {
        key: value
        for key, value in os.environ.items()
        if key != "PYTEST_ADDOPTS"
    }


def run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command from the repo root, capturing text output."""
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=env if env is not None else clean_env(),
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT_S,
    )


def node_ids(collect_stdout: str) -> set[str]:
    """Extract test node IDs from `pytest --collect-only -q` output."""
    return {
        line.strip()
        for line in collect_stdout.splitlines()
        if "::" in line
    }


def test_venv_exists_and_is_ignored() -> None:
    # .venv/bin/python exists at the repo root...
    assert VENV_PYTHON.is_file(), f"missing {VENV_PYTHON}"
    # ...and reports Python >= 3.10.
    result = run(
        [
            str(VENV_PYTHON),
            "-c",
            "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')",
        ]
    )
    assert result.returncode == 0, result.stderr
    major, minor = (int(part) for part in result.stdout.strip().split("."))
    assert (major, minor) >= (3, 10), f"Python {major}.{minor} < 3.10"
    # .gitignore contains an entry for .venv/.
    gitignore_entries = {
        line.strip()
        for line in (REPO_ROOT / ".gitignore").read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    assert ".venv/" in gitignore_entries or ".venv" in gitignore_entries


def test_pip_available_in_venv() -> None:
    # Needed by the health script's `python -m pip check`.
    result = run([str(VENV_PYTHON), "-m", "pip", "--version"])
    assert result.returncode == 0, result.stderr
    assert "pip" in result.stdout


def test_pytest_installed_in_venv() -> None:
    result = run([str(VENV_PYTHON), "-m", "pytest", "--version"])
    assert result.returncode == 0, result.stderr
    version_output = result.stdout + result.stderr
    assert re.search(r"pytest\s+\d+", version_output), version_output


def test_app_package_importable() -> None:
    result = run([str(VENV_PYTHON), "-c", "import app; print(app.__name__)"])
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "app"


def test_pytest_wiring_both_invocations() -> None:
    env = clean_env()
    # --collect-only so this test never recursively executes the suite.
    via_module = run(
        [str(VENV_PYTHON), "-m", "pytest", "--collect-only", "-q"], env=env
    )
    via_script = run([str(VENV_PYTEST), "--collect-only", "-q"], env=env)
    assert via_module.returncode == 0, via_module.stdout + via_module.stderr
    assert via_script.returncode == 0, via_script.stdout + via_script.stderr

    module_ids = node_ids(via_module.stdout)
    script_ids = node_ids(via_script.stdout)
    assert module_ids, "direct collection yielded no test node IDs"
    assert module_ids == script_ids, (
        f"invocation mismatch:\n{sorted(module_ids)}\nvs\n{sorted(script_ids)}"
    )
    # The health tests belong to every direct (unguarded) collection:
    # the recursion guard must live only inside scripts/health-check.sh.
    assert any(
        node_id.startswith("tests/test_health_script.py::")
        for node_id in module_ids
    ), "health-script tests missing from direct collection"


def test_app_compiles() -> None:
    result = run([str(VENV_PYTHON), "-m", "compileall", "-q", "app"])
    combined = result.stdout + result.stderr
    # compileall exits 0 even when the target directory does not exist
    # ("Can't list 'app'" on stderr, exit 0), so the exit status alone is
    # not proof that anything was compiled. Require that no such warning
    # was emitted and that app's bytecode cache is present.
    assert "Can't list" not in combined, combined
    assert result.returncode == 0, combined
    pycache = REPO_ROOT / "app" / "__pycache__"
    assert pycache.is_dir(), f"missing {pycache}"
    assert list(pycache.glob("*.pyc")), f"no .pyc under {pycache}"
