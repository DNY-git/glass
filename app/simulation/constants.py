"""Named constants for the Phase 4 Monte Carlo layer.

Plain module-level literal bindings, identical on every run (no
environment or clock reads anywhere under app/). Kept RNG-free on
purpose: this module must never import ``random`` (designated-
randomness rule, brief decision 2 — AST-enforced by
tests/test_phase4_separation.py).
"""

# Version string identifying the sampling mechanics, echoed on every
# SimulationResult: categorical draws over the truncated, renormalized
# (K+1)^2 matrix via rng.random() (brief decisions 3/4). Any change to
# those mechanics is a visible version bump — the fixed-seed golden
# (criterion 3) pins this literal, so the version cannot drift
# silently (brief open question 7a).
SIM_VERSION = "sim-categorical-v1"

# Default draw count for one simulate() call: 10,000 samples per
# fixture is enough that the mc_stderr term is small relative to the
# outcome probabilities while staying far below the 2e5-per-test cap
# (KNOWN-LIMITATIONS item 2, 120 s health budget). Caller-overridable
# and ALWAYS echoed on the result (brief decisions 3/5, open
# question 5a).
DEFAULT_N_SIMS = 10_000

__all__ = ["DEFAULT_N_SIMS", "SIM_VERSION"]
