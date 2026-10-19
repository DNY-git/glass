"""Named policy constants of the versioned feature spec (decision 5, F1).

Every policy here exists as a NAMED, DOCUMENTED constant rather than a
silent default inside computation (F1: boundary-case policies are named
documented constants, never silent). The versioned feature spec
(HANDOFF IX-6) is ``FEATURE_VERSION`` plus these policy constants plus
the inventory of STATISTICAL-ASSUMPTIONS section 9 — no separate spec
object exists (decision 8, the lean default).

Bump discipline, worded identically to ``FORECAST_VERSION``'s (F7):
any change to the hashed field set, the canonicalization spec, or the
derivation semantics requires a ``FEATURE_VERSION`` bump — the constant
is the contract's version.

Features are historical summaries of synthetic fixture history — not
probabilities, not model outputs, not evidence (section 9g); the
synthetic-data caveat rides every feature.
"""

from __future__ import annotations

# Why: the spec's identity, echoed on every FeatureVector. The string
# names the shape (chronological windows) and the contract version;
# bump it under the discipline above, never re-spec in silence.
FEATURE_VERSION = "features-chronological-v1"

# Why: the estimator window — the team's last FORM_WINDOW strictly-
# pre-cutoff matches. 5 is a defensible short-form window on 20-match-
# per-team synthetic histories (developer answer Q5, 2026-10-19).
FORM_WINDOW = 5

# Why: window > available history keeps a form field MISSING until the
# full window exists — one constant estimator window, no partial-
# window ambiguity (F1 named per-feature choice; developer answer
# Q1 = a). The affected appearances are honestly MISSING (measured:
# 30/120 pool appearances), never a shorter-window mean.
FORM_WINDOW_POLICY = "MISSING_UNTIL_FULL_WINDOW"

# Why: rest days measure days since the most recent SAME-SEASON prior
# match; a season opener is MISSING rather than reporting the ~301-day
# off-season gap as "rest" — that gap is a different quantity and is
# rejected (F1 named choice; developer answer Q3 = a; measured: the
# 12/120 season-opening appearances report MISSING).
REST_DAYS_POLICY = "WITHIN_SEASON"

# Why: xg_form averages the window's xG-AVAILABLE matches only, with
# n_xg disclosed — missing xG never participates as 0.0, and the field
# is MISSING at n_xg = 0 (developer answer Q2 = a). This is a
# DIFFERENT estimator-of-form than a strict rolling-xG window
# (measured 0/120 on this data), documented as such wherever used.
XG_FORM_POLICY = "MEAN_OVER_AVAILABLE_WITH_N"

__all__ = [
    "FEATURE_VERSION",
    "FORM_WINDOW",
    "FORM_WINDOW_POLICY",
    "REST_DAYS_POLICY",
    "XG_FORM_POLICY",
]
