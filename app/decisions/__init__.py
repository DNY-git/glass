"""Stage 8 DECISION ANALYSIS: comparison without a silent ensemble.

One pure package whose single entry point, ``build_decision_report``,
produces a frozen ``DecisionReport`` — a deterministic in-process VIEW
of an existing frozen ``Forecast`` (identical input yields a
field-for-field identical report including its ``content_hash``): no
storage, no route, no clock, no randomness, no history surface. Zero
scoring — no scoring metric ships this phase; evidence begins at
Phases 9/11. Disagreement is reported, never collapsed: labeled
hypothetical scenarios stand side by side with a min/max spread, and
the fixed disclaimer says plainly that no second independent model
exists, so this system never presents an ensemble or a cross-model
agreement. Probabilities are in-sample estimates, not claims of
quality, and reports are re-derivable views — they are never stored.
"""

from .builder import build_decision_report
from .constants import REPORT_VERSION
from .record import DecisionReport

__all__ = ["REPORT_VERSION", "DecisionReport", "build_decision_report"]
