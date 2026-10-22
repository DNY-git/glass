"""The single version constant for the walk-forward backtest (no knobs).

Deliberately the ONLY module-level name here (Phase 7 criterion-1
pattern): the harness carries no threshold, no tolerance, no window
size, and no other tunable — a bump of this constant is required for
any change to the harness contract, the manifest shape, or the digest
serialization spec, so every run digest stays version-local.
"""

from __future__ import annotations

BACKTEST_VERSION = "backtest-walkforward-v1"
