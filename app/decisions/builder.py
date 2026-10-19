"""Pipeline stage 8: build one frozen decision report (pure, in process).

``build_decision_report(forecast, *, scenarios=())`` — the exact Phase 7
signature (glass-quant ruling A2; brief decision 2): **no ``matches``
argument and no time-like parameter exists to forget**. The report is a
serialization of an already cutoff-enforced artifact: the cutoff was
enforced once, inside ``build_forecast``, when the Forecast was frozen,
so this renderer of frozen bytes cannot see any history at all — no new
leakage surface (the poisoned-future byte-identity regression still
ships in the tests). Determinism: no RNG, no wall clock, no environment
reads; identical ``(forecast, scenarios)`` input yields a field-for-
field identical report including its ``content_hash``, with comparisons
in canonical label order so shuffled scenario input changes nothing.

Refusals are explicit and never silent: a non-``Forecast`` raises
``TypeError`` (``scenarios`` is keyword-only, so passing it positionally
raises ``TypeError`` before any work); a scenario whose baseline fails
frozen **value equality** with the forecast's own ``FittedParams``
raises ``ValueError`` naming the mismatch (never reconciled, never
re-labeled — mirroring ``simulate``'s provenance refusal); duplicate
labels raise ``ValueError`` (ambiguity refused, never averaged); an
inapplicable transform propagates its ``ValueError`` from evaluation —
never a silently inert hypothetical number identical to baseline.
Probabilities come from the ONE analytic cell-math path
(``scenario_matrix`` + ``outcome_probs``) at full precision; deltas are
exact subtractions, never rounded.

Disagreement is reported, never collapsed (IX-7): comparisons are
labeled hypotheticals side by side with deltas, the ONLY cross-scenario
aggregation is the per-outcome min/max/spread over two or more entries
(a mean would be an invented ensemble and exists nowhere), and the
fixed disclaimer states that no second independent model exists so no
cross-model agreement is claimed. Uncertainty is flag echo only — the
top-level convergence/insufficient flags and truncation disclosure; no
interval or reliability band exists on a report. No scoring metric
ships this phase.
"""

from __future__ import annotations

from typing import Sequence

from app.forecasts import Forecast
from app.models import outcome_probs
from app.scenarios import Scenario, scenario_matrix

from .constants import DISCLAIMER, REPORT_VERSION
from .record import DecisionReport, ScenarioComparison, ScenarioSpread

# The fixed outcome order of the spread record (brief criterion 10):
# exactly these three entries, in exactly this order.
_SPREAD_OUTCOMES = ("home", "draw", "away")


def build_decision_report(
    forecast: Forecast,
    *,
    scenarios: Sequence[Scenario] = (),
) -> DecisionReport:
    """One frozen report over one frozen forecast (+ labeled scenarios).

    The signature is the contract: ``(forecast, *, scenarios=())`` —
    no ``matches``, no ``as_of``/``cutoff``/``date``/``history`` or
    any time-like parameter (A2; criterion 1). ``TypeError`` on a
    non-``Forecast`` and on non-``Scenario`` entries; the scenario
    refusals of criterion 11 are ``ValueError`` and happen here, inside
    the calculation, never only at the call site. Scenario entries are
    canonically ordered by label, so caller order is irrelevant to the
    produced record and its hash.
    """
    if not isinstance(forecast, Forecast):
        raise TypeError(
            "build_decision_report requires a frozen Forecast "
            f"(got {type(forecast).__name__})"
        )

    scenario_entries = tuple(scenarios)
    for scenario in scenario_entries:
        if not isinstance(scenario, Scenario):
            raise TypeError(
                "build_decision_report scenarios must be Scenario records "
                f"(got {type(scenario).__name__})"
            )

    # Provenance refusal (criterion 11): a baseline that is not the
    # forecast's own fitted parameters by frozen VALUE equality would
    # mislabel every comparison — refused with ValueError naming the
    # mismatch, never reconciled or re-labeled.
    for scenario in scenario_entries:
        if scenario.baseline != forecast.fitted:
            raise ValueError(
                f"scenario {scenario.label!r}: baseline does not equal the "
                "forecast's FittedParams (a mismatched baseline would "
                "mislabel the comparison; refused, never reconciled)"
            )

    # Ambiguity refusal (criterion 11): duplicate labels are refused,
    # never averaged or resolved silently.
    seen_labels: set[str] = set()
    for scenario in scenario_entries:
        if scenario.label in seen_labels:
            raise ValueError(
                f"duplicate scenario label {scenario.label!r}: ambiguity is "
                "refused, never averaged"
            )
        seen_labels.add(scenario.label)

    # Canonical order by label (decision 10): shuffled caller order
    # produces a field-for-field identical report including its hash.
    ordered = tuple(sorted(scenario_entries, key=lambda item: item.label))

    comparisons: list[ScenarioComparison] = []
    for scenario in ordered:
        # The ONE cell-math path (analytic-first): scenario_matrix
        # applies parameter arithmetic and delegates to the shared
        # constructors; outcome_probs is analytic, exact under
        # truncation — never a Monte-Carlo frequency. Inapplicable
        # transforms raise ValueError here and propagate untouched.
        evaluated = scenario_matrix(scenario, forecast.home, forecast.away)
        outcome_home, outcome_draw, outcome_away = outcome_probs(evaluated.matrix)
        comparisons.append(
            ScenarioComparison(
                label=scenario.label,
                transforms=scenario.transforms,
                outcome_home=outcome_home,
                outcome_draw=outcome_draw,
                outcome_away=outcome_away,
                # Full precision, never rounded: arithmetic difference
                # between this labeled hypothetical and its own
                # baseline report numbers (descriptive, never a claim).
                delta_home=outcome_home - forecast.outcome_home,
                delta_draw=outcome_draw - forecast.outcome_draw,
                delta_away=outcome_away - forecast.outcome_away,
            )
        )

    # The ONLY cross-scenario aggregation this system ships: per-outcome
    # min/max/spread, and only over two or more hypotheticals — with
    # exactly one entry there is nothing to disagree about, and with
    # zero there is no spread at all (criterion 10: None in both cases).
    # A mean is an invented ensemble: it exists nowhere below (criterion 9).
    spread: tuple[ScenarioSpread, ...] | None = None
    if len(comparisons) >= 2:
        entries: list[ScenarioSpread] = []
        for outcome in _SPREAD_OUTCOMES:
            values = [
                getattr(comparison, f"outcome_{outcome}") for comparison in comparisons
            ]
            minimum = min(values)
            maximum = max(values)
            entries.append(
                ScenarioSpread(
                    outcome=outcome,
                    minimum=minimum,
                    maximum=maximum,
                    spread=maximum - minimum,
                )
            )
        spread = tuple(entries)

    return DecisionReport(
        # Fixture block: exact echo, kickoff MISSING never defaulted.
        competition=forecast.competition,
        season=forecast.season,
        date=forecast.date,
        home=forecast.home,
        away=forecast.away,
        kickoff=forecast.kickoff,
        as_of=forecast.as_of,
        # Provenance echoes: full provenance chains through the source
        # forecast (config, pooling, parameters reachable via the hash).
        report_version=REPORT_VERSION,
        model_version=forecast.fitted.model_version,
        input_digest=forecast.fitted.input_digest,
        forecast_version=forecast.forecast_version,
        forecast_content_hash=forecast.content_hash,
        # Pre-cutoff sample echoes.
        sample_matches=forecast.fitted.sample_size.matches,
        sample_goals=forecast.fitted.sample_size.goals,
        # Flags, TOP LEVEL: a screaming flag beside plausible-looking
        # normalized numbers is the structural disagreement, both kept
        # visible, neither hidden, judged by no threshold (A6).
        convergence_status=forecast.fitted.convergence_status,
        insufficient_data=forecast.fitted.insufficient_data,
        insufficient_teams=forecast.fitted.insufficient_teams,
        # The fixed disclaimer: identical on every report.
        disclaimer=DISCLAIMER,
        # Estimate numbers — copies of the forecast's analytic values,
        # never recomputed here, never Monte Carlo.
        lambda_home=forecast.lambda_home,
        lambda_away=forecast.lambda_away,
        max_goals=forecast.max_goals,
        dropped_mass=forecast.dropped_mass,
        outcome_home=forecast.outcome_home,
        outcome_draw=forecast.outcome_draw,
        outcome_away=forecast.outcome_away,
        scenario_comparisons=tuple(comparisons),
        scenario_spread=spread,
    )


__all__ = ["build_decision_report"]
