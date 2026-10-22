#!/usr/bin/env bash
# Mechanical health sweep for Sports Looking Glass.
# set -u only: one failing check must not abort the sweep (no set -e).
set -u

cd "$(dirname "$0")/.." || exit 1

PY=".venv/bin/python"

# Recursion guard: the health script's own pytest runs must not
# execute the tests that spawn this script. They run in the direct
# suite instead (pytest, from the repo root).
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+$PYTEST_ADDOPTS }-k 'not health_script'"

if [ ! -x "$PY" ]; then
    echo "There is nothing to check yet: $PY does not exist."
    echo "This is expected before Phase 1 completes."
    exit 0
fi

echo "== last commit =="
git log -1 --oneline 2>&1 || true

echo
echo "== working tree =="
git status --porcelain 2>&1 || true

echo
echo "== compile =="
if [ -d app ]; then
    "$PY" -m compileall -q app 2>&1 || true
else
    echo "skipped"
fi

echo
echo "== pytest run 1 =="
"$PY" -m pytest -q --tb=no 2>&1 | tail -n 20 || true

echo
echo "== pytest run 2 (with skip/xfail reasons) =="
"$PY" -m pytest -q --tb=no -rsxX 2>&1 | tail -n 30 || true

echo
echo "== skips/xfails =="
"$PY" -m pytest -q --tb=no -rsxX 2>/dev/null | grep -E 'SKIPPED|XFAIL|XPASS' || echo "none"

echo
echo "== determinism comparison (timings stripped) =="
# Phase 9 AMENDMENT A4 (architect-sanctioned): strip BOTH timing forms.
# pytest prints "in 122.11s" and, for runs >= 60 s, appends a
# "(0:MM:SS)"/"(H:MM:SS)" wall-clock parenthetical the old regex did
# not strip -- IDENTICAL outcomes compared MISMATCH. Counts-only
# comparison, never timings; the counts-only shape is now pinned
# (UNPARSEABLE is loud, never a silent OK).
strip_summary() {
    sed -E 's/in [0-9.]+s//; s/ +\([0-9]+:[0-9]+:[0-9]+\)//; s/ +$//'
}
COUNTS_RE='^[0-9]+ [a-z]+(, [0-9]+ [a-z]+)*$'
SUM1=$("$PY" -m pytest -q --tb=no 2>/dev/null | grep -E '^[0-9]+ (passed|failed)|passed|failed|error' | tail -n 1 | strip_summary)
SUM2=$("$PY" -m pytest -q --tb=no 2>/dev/null | grep -E '^[0-9]+ (passed|failed)|passed|failed|error' | tail -n 1 | strip_summary)
if ! [[ "$SUM1" =~ $COUNTS_RE ]] || ! [[ "$SUM2" =~ $COUNTS_RE ]]; then
    echo "UNPARSEABLE (counts-only comparison expected after stripping):"
    echo "run 1: $SUM1"
    echo "run 2: $SUM2"
elif [ "$SUM1" = "$SUM2" ]; then
    echo "OK: $SUM1"
else
    echo "MISMATCH"
    echo "run 1: $SUM1"
    echo "run 2: $SUM2"
fi

echo
echo "== pip check =="
"$PY" -m pip check 2>&1 | tail -n 5 || true

echo
echo "== five largest .py files (app/ and tests/) =="
find app tests -name '*.py' -type f 2>/dev/null | xargs wc -l 2>/dev/null | sort -rn | sed -n '2,6p'
