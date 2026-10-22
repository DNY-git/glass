"""The four frozen backtest records: baselines, refusals, manifest, run.

All value objects here are frozen dataclasses with construction-time
content hashes where declared; **no timestamp field exists anywhere in
this module** (pinned by criterion 12) — a run is identified by its
input digest and ordered run digest, never by when it happened. The
manifest echoes caller-supplied identity fields verbatim (fixture-file
sha256s, interpreter version); this pure package never reads ``sys``
or ``os`` to obtain them (design decision 1). Refusal records carry no
content hash and sit outside the run digest; their keys are pinned by
the accounting criterion instead (decision 6).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from app.forecasts import Forecast

from .canonicalization import FixtureKey, baseline_content_hash

# The one refusal status literal: a target with zero strictly-pre-
# cutoff history is REFUSED as a first-class reported status — never a
# silent skip, never a dropped target, never a fabricated uniform.
REFUSED_NO_PRE_CUTOFF_HISTORY = "REFUSED_NO_PRE_CUTOFF_HISTORY"


class BaselineStatus(enum.Enum):
    """Outcome of one per-fixture baseline computation (A5)."""

    COMPUTED = "COMPUTED"
    MISSING_NO_HISTORY = "MISSING_NO_HISTORY"


@dataclass(frozen=True)
class BaselineRecord:
    """One per-fixture chronological baseline: triple + n + status.

    The frequencies are pooled long-run home/draw/away frequencies over
    realized matches with strictly ``date < fixture.date`` (uniform
    weighting, no decay, no split); ``None`` iff status is MISSING_NO_HISTORY.
    Content-hashed in-process at construction, re-derivable from the
    matches alone, and NEVER stored. Weaknesses ride every record: tiny
    early n, synthetic hand-authored data, and the independent-Poisson
    draw bias (STATISTICAL-ASSUMPTIONS §12).
    """

    fixture_key: FixtureKey
    home_frequency: float | None
    draw_frequency: float | None
    away_frequency: float | None
    n: int
    status: BaselineStatus
    content_hash: str = field(default="", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "content_hash", baseline_content_hash(self))


@dataclass(frozen=True)
class RefusalRecord:
    """One refused target: fixture key, the status literal, the message.

    First-class and ordered with the rest of the run; carries the
    original ``ValueError`` message so the refusal chain stays auditable.
    """

    fixture_key: FixtureKey
    status: str
    message: str


@dataclass(frozen=True)
class RunManifest:
    """The run's identity: versions, input digest, echoes, run digest.

    §11(c) in substance. ``fixture_file_sha256s`` is an ordered tuple of
    ``(label, sha256)`` pairs supplied by the caller and echoed
    verbatim; ``interpreter_version`` is caller-supplied and echoed
    (``None`` stays ``None``, never fabricated). ``run_digest`` covers
    ONLY the ordered (fixture key, content_hash) list of the emitted
    predictions — a changed echo changes the manifest, never the digest.
    No timestamp, no wall-clock value appears in any field (criterion 12).
    """

    backtest_version: str
    forecast_version: str
    model_version: str
    config_identity: str
    history_canonical_state_digest: str
    fixture_file_sha256s: tuple[tuple[str, str], ...]
    interpreter_version: str | None
    run_digest: str


@dataclass(frozen=True)
class WalkForwardRun:
    """One complete walk-forward run: ordered outputs + counts + manifest.

    Counts make the accounting auditable: ``n_targets == n_refusals +
    n_predictions`` and ``n_predictions == n_flagged + n_clean`` on every
    run — every target is either a refusal record or an emitted
    prediction, nothing is silently skipped or dropped.
    """

    predictions: tuple[Forecast, ...]
    refusals: tuple[RefusalRecord, ...]
    baselines: tuple[BaselineRecord, ...]
    n_targets: int
    n_predictions: int
    n_refusals: int
    n_flagged: int
    n_clean: int
    manifest: RunManifest


__all__ = [
    "REFUSED_NO_PRE_CUTOFF_HISTORY",
    "BaselineRecord",
    "BaselineStatus",
    "RefusalRecord",
    "RunManifest",
    "WalkForwardRun",
]
