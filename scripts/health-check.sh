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
    "$PY" -m compileall -q app tests 2>&1 || true
else
    echo "skipped"
fi

# Phase 10 AMENDMENT A1 (architect-sanctioned run-structure rework,
# docs/briefs/phase-10.md): exactly THREE inner pytest executions
# replace the former five. The old skips run was flags-identical to
# run 2, and the determinism sums re-ran the suite twice more; those
# redundant EXECUTIONS are eliminated, no CHECK. Each run's stdout
# and stderr are captured ONCE into a temp dir; the display tails,
# the skips/xfails grep, and the determinism sums are DERIVED from
# the captures (stdout-only for grep/sums and combined for display =
# the exact Phase 9 A4 input classes). Determinism keeps two
# IDENTICAL plain-flag runs (run 1 and run 3) with the A4 mechanism
# verbatim: counts-only strip, COUNTS_RE gate, loud UNPARSEABLE.
# All nine section headers are byte-identical to the Phase 1 pins.
CAPTURES="$(mktemp -d)"
trap 'rm -rf "$CAPTURES"' EXIT

echo
echo "== pytest run 1 =="
"$PY" -m pytest -q --tb=no >"$CAPTURES/run1.out" 2>"$CAPTURES/run1.err" || true
cat "$CAPTURES/run1.out" "$CAPTURES/run1.err" | tail -n 20

echo
echo "== pytest run 2 (with skip/xfail reasons) =="
"$PY" -m pytest -q --tb=no -rsxX >"$CAPTURES/run2.out" 2>"$CAPTURES/run2.err" || true
cat "$CAPTURES/run2.out" "$CAPTURES/run2.err" | tail -n 30

echo
echo "== skips/xfails =="
grep -E 'SKIPPED|XFAIL|XPASS' "$CAPTURES/run2.out" || echo "none"

echo
echo "== determinism comparison (timings stripped) =="
# Phase 9 AMENDMENT A4 mechanism, unchanged: strip BOTH timing forms;
# counts-only comparison, never timings; UNPARSEABLE is loud, never
# a silent OK. Phase 10 A1: SUM1 derives from run 1's PLAIN stdout
# capture; run 3 (below) executes silently and its PLAIN stdout
# capture yields SUM2 -- two identical-flag executions, byte-
# identical A4 extraction semantics on both sides.
strip_summary() {
    sed -E 's/in [0-9.]+s//; s/ +\([0-9]+:[0-9]+:[0-9]+\)//; s/ +$//'
}
COUNTS_RE='^[0-9]+ [a-z]+(, [0-9]+ [a-z]+)*$'
"$PY" -m pytest -q --tb=no >"$CAPTURES/run3.out" 2>"$CAPTURES/run3.err" || true
SUM1=$(grep -E '^[0-9]+ (passed|failed)|passed|failed|error' "$CAPTURES/run1.out" | tail -n 1 | strip_summary)
SUM2=$(grep -E '^[0-9]+ (passed|failed)|passed|failed|error' "$CAPTURES/run3.out" | tail -n 1 | strip_summary)
if ! [[ "$SUM1" =~ $COUNTS_RE ]] || ! [[ "$SUM2" =~ $COUNTS_RE ]]; then
    echo "UNPARSEABLE (counts-only comparison expected after stripping):"
    echo "sum 1: $SUM1"
    echo "sum 2: $SUM2"
elif [ "$SUM1" = "$SUM2" ]; then
    echo "OK: $SUM1"
else
    echo "MISMATCH"
    echo "sum 1: $SUM1"
    echo "sum 2: $SUM2"
fi

echo
echo "== pip check =="
"$PY" -m pip check 2>&1 | tail -n 5 || true

echo
echo "== five largest .py files (app/ and tests/) =="
find app tests -name '*.py' -type f 2>/dev/null | xargs wc -l 2>/dev/null | sort -rn | sed -n '2,6p'
