"""The frozen feature record (stage 4, decision 4 / F3).

A ``FeatureVector`` is a deterministic value object: identical
``(matches, fixture)`` produce a field-for-field identical record
including ``content_hash`` — no seed field exists anywhere. It lives
BESIDE the Forecast, never inside it (F3): features are consumed by
nothing this phase (decision 11), and no forecast field,
``FORECAST_VERSION`` value, storage schema, or Phase 5 golden touches
this type. History-dependent fields are ``OptionalValue``s under the
domain's two-state availability taxonomy — MISSING holds value ``None``
exactly, never 0 (constitution prohibition 4); the two count fields are
plain ``int`` because 0 is a true exact fact (estimates are MISSING,
counts are facts).

Every field is a historical summary of past matches — not a
probability, not a model output, not evidence (STATISTICAL-
ASSUMPTIONS section 9g); the synthetic-data caveat rides every record.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain import OptionalValue

from .canonicalization import content_hash as compute_content_hash


@dataclass(frozen=True)
class FeatureVector:
    """One immutable feature vector for one fixture (the decision-4 contract).

    Field set and order are pinned by Phase 6 criterion 4 — Phases 9/11
    depend on them. ``content_hash`` is computed at construction from
    every other field under the canonicalization spec of record; it is
    ``init=False`` because no caller ever supplies it.
    """

    competition: str
    season: str
    date: str
    home: str
    away: str
    kickoff: OptionalValue  # fixture echo; MISSING never defaulted
    as_of: str  # == fixture.date exactly (the cutoff, day granularity)
    feature_version: str  # the FEATURE_VERSION contract constant
    input_digest: str  # sha256 of canonical_state() of the pre-cutoff set
    home_goals_scored_form: OptionalValue  # window mean or MISSING
    home_goals_conceded_form: OptionalValue  # window mean or MISSING
    home_rest_days: OptionalValue  # int days or MISSING (WITHIN_SEASON)
    home_xg_form: OptionalValue  # mean over available xG or MISSING
    home_xg_n: int  # exact count of xG in window, 0 is a fact
    home_prior_matches: int  # exact pre-cutoff count, 0 is a fact
    away_goals_scored_form: OptionalValue
    away_goals_conceded_form: OptionalValue
    away_rest_days: OptionalValue
    away_xg_form: OptionalValue
    away_xg_n: int
    away_prior_matches: int
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_hash", compute_content_hash(self))


__all__ = ["FeatureVector"]
