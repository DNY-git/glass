"""The walk-forward harness: strictly chronological, one entry point.

``run_walk_forward(matches, *, fixture_file_sha256s=(),
interpreter_version=None)`` — the package's ONLY public function
(AMENDMENT A1's registered entry point; criterion 7 pins the exact
signature — the first parameter is named exactly ``matches``, no
config/spec/variant/seed knob of any kind exists on this surface).

Per target, in canonical chronological order: the per-fixture ``Fixture``
is the natural key plus the kickoff echo (**never the score** — the
score is never copied onto a prediction target); the fit pool is the
input **minus the target's natural key** and the cutoff is enforced
inside ``build_forecast`` (E3: an unfiltered pool minus the target
cannot leak, only crash). A ``ValueError`` becomes a first-class
``RefusalRecord`` carrying the original message — never a silent skip,
never a fabricated uniform. Baselines come from the private baseline
module (the package's only realized-score consumer); this module never
reads a score.

The manifest echoes caller-supplied identity fields verbatim (design
decision 1) and derives everything else from the input alone — no
wall clock, no environment, no randomness. ``run_digest`` covers ONLY
the ordered (fixture key, content_hash) list of the emitted
predictions: refusals carry no hash and sit outside the digest.
"""

from __future__ import annotations

from typing import Sequence

from app.domain import (
    Fixture,
    IngestedRecord,
    Match,
    MatchCollection,
    Provenance,
    RecordLocation,
    canonical_state,
)
from app.forecasts import FORECAST_VERSION, Forecast, build_forecast, config_identity

from .baselines import _baseline_record
from .canonicalization import FixtureKey, entries_digest, sha256_hex
from .constants import BACKTEST_VERSION
from .record import (
    REFUSED_NO_PRE_CUTOFF_HISTORY,
    BaselineRecord,
    RefusalRecord,
    RunManifest,
    WalkForwardRun,
)

__all__ = ["run_walk_forward"]


def _fixture_for(match: Match) -> Fixture:
    """The per-target Fixture: natural key + kickoff echo, never the score.

    The ``Fixture`` type structurally has no score field, so a realized
    result can never ride along onto a prediction target; the kickoff
    does ride because it participates in forecast content identity.
    """
    return Fixture(
        competition=match.competition,
        season=match.season,
        date=match.date,
        home=match.home,
        away=match.away,
        kickoff=match.kickoff,
    )


def _is_flagged(forecast: Forecast) -> bool:
    """Exactly the section-5 flag set: the emitted prediction is flagged
    iff it carries insufficient data, insufficient teams, or a
    convergence status other than CONVERGED.

    Compared stringly on purpose: ``app.models`` is outside this pure
    package's import allowlist (AMENDMENT A3), so the enum is read via
    its ``.value`` rather than imported.
    """
    fitted = forecast.fitted
    return (
        bool(fitted.insufficient_data)
        or bool(fitted.insufficient_teams)
        or fitted.convergence_status.value != "CONVERGED"
    )


def _history_digest(matches: Sequence[Match]) -> str:
    """sha256 of ``canonical_state()`` over the full sorted input pool.

    The run's input identity (design decision 6): per-target consumed
    histories already ride each prediction's own ``input_digest``. The
    provenance/location values are dummy pure-code values — neither
    enters ``canonical_state``.
    """
    collection = MatchCollection()
    for index, match in enumerate(matches):
        collection.add(IngestedRecord(
            match=match,
            provenance=Provenance(source_path="", sha256=""),
            location=RecordLocation(source_path="", index=index),
        ))
    return sha256_hex(canonical_state(collection))


def run_walk_forward(
    matches: Sequence[Match],
    *,
    fixture_file_sha256s: tuple[tuple[str, str], ...] = (),
    interpreter_version: str | None = None,
) -> WalkForwardRun:
    """One deterministic walk-forward run over every input match.

    Targets are the full input ordered by ``canonical_sort_key`` (date
    primary; same-date ties by competition, season, home, away — never
    input order). Every target yields exactly one baseline record and
    either one prediction or one refusal: nothing is silently skipped
    or dropped. Identical inputs produce an identical ordered run,
    byte for byte, including ``run_digest``.
    """
    targets = tuple(sorted(matches, key=lambda match: match.canonical_sort_key))
    predictions: list[Forecast] = []
    refusals: list[RefusalRecord] = []
    baselines: list[BaselineRecord] = []
    n_flagged = 0
    for match in targets:
        baselines.append(_baseline_record(targets, match.natural_key, match.date))
        pool = tuple(m for m in targets if m.natural_key != match.natural_key)
        try:
            prediction = build_forecast(pool, _fixture_for(match))
        except ValueError as error:
            refusals.append(RefusalRecord(
                fixture_key=match.natural_key,
                status=REFUSED_NO_PRE_CUTOFF_HISTORY,
                message=str(error),
            ))
            continue
        predictions.append(prediction)
        if _is_flagged(prediction):
            n_flagged += 1

    entries: tuple[tuple[FixtureKey, str], ...] = tuple(
        ((p.competition, p.season, p.date, p.home, p.away), p.content_hash)
        for p in predictions
    )
    first = predictions[0] if predictions else None
    manifest = RunManifest(
        backtest_version=BACKTEST_VERSION,
        forecast_version=FORECAST_VERSION,
        model_version=first.fitted.model_version if first else "",
        config_identity=config_identity(first.fitted.config) if first else "",
        history_canonical_state_digest=_history_digest(targets),
        fixture_file_sha256s=tuple(fixture_file_sha256s),
        interpreter_version=interpreter_version,
        run_digest=entries_digest(entries),
    )
    return WalkForwardRun(
        predictions=tuple(predictions),
        refusals=tuple(refusals),
        baselines=tuple(baselines),
        n_targets=len(targets),
        n_predictions=len(predictions),
        n_refusals=len(refusals),
        n_flagged=n_flagged,
        n_clean=len(predictions) - n_flagged,
        manifest=manifest,
    )
