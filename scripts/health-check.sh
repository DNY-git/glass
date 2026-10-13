#!/usr/bin/env bash
# Mechanical health sweep for Sports Looking Glass.
# set -u only: one failing check must not abort the sweep (no set -e).
set -u

cd "$(dirname "$0")/.." || exit 1

PY=".venv/bin/python"

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
SUM1=$("$PY" -m pytest -q --tb=no 2>/dev/null | grep -E '^[0-9]+ (passed|failed)|passed|failed|error' | tail -n 1 | sed -E 's/in [0-9.]+s//')
SUM2=$("$PY" -m pytest -q --tb=no 2>/dev/null | grep -E '^[0-9]+ (passed|failed)|passed|failed|error' | tail -n 1 | sed -E 's/in [0-9.]+s//')
if [ "$SUM1" = "$SUM2" ]; then
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
