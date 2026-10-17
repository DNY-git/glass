"""Stage 7 SCENARIO EXPLORATION: bounded, labeled-hypothetical multipliers.

Public surface pinned by criterion 14 — exactly one transform op kind
with inclusive documented bounds, one scenario per call, labels echoed
on every output, and **no averaging or ensembling anywhere**: scenarios
are presented side by side by the caller and their disagreement is
reported, never collapsed into a silently invented ensemble (comparison
belongs to Phase 7). Scenario numbers are hypothetical, conditioned on
the in-sample fit and all caveats of
docs/STATISTICAL-ASSUMPTIONS.md section 7 — arbitrary documented
knobs, not empirical claims.

No randomness lives in this package (designated-randomness rule:
``random`` appears only in ``app/simulation/simulate.py``; enforced by
tests/test_phase4_separation.py), and no cell math: evaluation
delegates to the shared constructors of ``app/models/scoreline.py``.
"""

from .apply import ScenarioMatrix, scenario_matrix
from .spec import (
    MULTIPLIER_MAX,
    MULTIPLIER_MIN,
    Scenario,
    Transform,
    TransformOp,
    build_scenario,
)

__all__ = [
    "MULTIPLIER_MAX",
    "MULTIPLIER_MIN",
    "Scenario",
    "ScenarioMatrix",
    "Transform",
    "TransformOp",
    "build_scenario",
    "scenario_matrix",
]
