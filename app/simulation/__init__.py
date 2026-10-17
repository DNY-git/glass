"""Seeded Monte Carlo simulation over the fitted scoreline matrix.

Why simulation exists (Phase 4 brief decision 7): (i) Phase 12's
replay machinery — same-seed end-to-end determinism replay and
stochastic path replay — and (ii) future aggregate/season-path
quantities with no closed form (season point totals, multi-stage
paths). A single-match probability has a closed form today
(``outcome_probs``), so **simulation never replaces the analytic
number**: MC noise never contaminates log loss, Brier, or RPS.

Designated-randomness rule: ``random`` is imported only inside
``simulate`` (the ``.simulate`` module) — never in this package
initializer or ``constants`` — AST-enforced by
tests/test_phase4_separation.py. ``mc_stderr`` on every result
measures simulation noise only; this system computes no confidence
intervals anywhere.
"""

from .constants import DEFAULT_N_SIMS, SIM_VERSION
from .simulate import SimulationResult, simulate

__all__ = ["DEFAULT_N_SIMS", "SIM_VERSION", "SimulationResult", "simulate"]
