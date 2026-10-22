"""Backtesting (pipeline stage 9, IX-9): the walk-forward machinery.

Strictly chronological machinery only, under the §11 three-step line
(Phase 8 defenses -> Phase 9 machinery, STILL NO METRICS -> Phase 11
first scoring). The realized-result surface here is pre-cutoff history
ONLY (fit inputs and baseline windows consumed strictly `date <
fixture.date`): NO prediction-to-outcome join ships this phase, no
model-vs-baseline comparison exists, and no metric of any kind is
computed — evaluated observation n stays exactly 0. Pure package:
stdlib + app.domain + app.forecasts only; no storage import (the
CALLER persists predictions via app.storage), no filesystem, no
environment, no wall clock, no randomness.
"""

from __future__ import annotations

from .constants import BACKTEST_VERSION
from .harness import run_walk_forward
from .record import (
    BaselineRecord,
    BaselineStatus,
    RefusalRecord,
    RunManifest,
    WalkForwardRun,
)

__all__ = [
    "BACKTEST_VERSION",
    "BaselineRecord",
    "BaselineStatus",
    "RefusalRecord",
    "RunManifest",
    "WalkForwardRun",
    "run_walk_forward",
]
