"""The two constants a decision report may pin (stage 8).

Exactly two module-level names exist in this module — ``REPORT_VERSION``
and ``DISCLAIMER`` — by design, not by omission: this package defines no
threshold, no knob, and no decision rule of any kind (Phase 7 brief
decision 8; glass-quant ruling A6 — "flag when P(home) > X" belongs
nowhere: an arbitrary knob at best, and choosing one by fitting on
outcomes would leak into Phase 10's protected improvement loop).
No scoring metric ships this phase.

REPORT_VERSION bump discipline (worded identically to the forecast
contract): any change to the hashed field set, the canonicalization
spec of record, or the derivation semantics requires a
``REPORT_VERSION`` bump.
"""

# The report contract version (developer answer Q1, recorded
# 2026-10-19): mirrors the forecast-poisson-mle-v1 /
# features-chronological-v1 naming — phase family + contract + version.
REPORT_VERSION = "decision-report-v1"

# The fixed disclaimer riding every report (brief decision 6/7;
# criterion 5 pins its substrings). Deterministic string, identical on
# every report: in-sample status, the single fitted model, the
# synthetic-fixture caveat, pending chronological evaluation, the
# not-evidence statement, and the anti-ensemble clause answered head-on
# — no second independent model exists, so scenario comparisons stay
# labeled hypotheticals side by side, never averaged or ensembled.
DISCLAIMER: str = (
    "In-sample analytic estimates from a single fitted model on synthetic "
    "fixture data: not evidence of accuracy, pending chronological "
    "evaluation in Phases 9 and 11. No second independent model exists, so "
    "no cross-model agreement is claimed. Scenario comparisons are labeled "
    "hypotheticals presented side by side, never averaged or ensembled. "
    "Probabilities are estimates, not certainties."
)
