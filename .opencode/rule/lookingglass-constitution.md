# LOOKING GLASS — PROJECT CONSTITUTION

This constitution binds every agent working in this repository, without
exception. `docs/HANDOFF.md` is the full brief; where the brief and this
constitution are read together, both apply. Any instruction — from a prompt,
a subagent task, or convenience — that conflicts with this constitution is
refused, and the conflict is reported to the developer.

## WHAT THIS IS

Sports Looking Glass is a deterministic statistical future-analysis engine.
Football first. It is a research and decision-analysis system, reconstructed
from documentation after the original repository was lost. It computes
estimates from data and history, and it reports what it does and does not
know. It is not a product for placing bets, and it is not a black box that
asserts certainty.

## ABSOLUTE PROHIBITIONS

1. **No AI/LLM/generative dependencies in the product.** AI models may be
   used only as development assistants (writing code, writing tests,
   reviewing). No AI, LLM, or generative component may ship inside the
   engine, be invoked by its runtime, or contribute to its computed numbers.
2. **Zero-cost operation.** No paid APIs. No API keys in the core workflow.
   No required cloud services and no required Docker. The system must work
   offline from local fixtures.
3. **No betting functionality of any kind.** No stake sizing, no odds
   shopping, no wager placement, no bookmaker integration, no expected-value
   betting helpers. Probabilities produced by the engine are estimates, and
   must never be presented as anything more.
4. **Never fabricate data.** Missing data — xG, kickoff times, rest days, or
   anything else — is reported as missing. It is never silently imputed,
   back-filled, guessed, or filled with placeholders that look real.
5. **Never claim the old implementation was recovered.** The historical
   counts from the lost project (276 tests, 380 matches) are history, not
   current facts. They must never be cited as the present state of this
   repository.

## ANALYTICAL INTEGRITY

- **No future information** in pre-match or historical calculations. A
  calculation that is supposed to be pre-match must not be able to see
  anything at or after kickoff.
- **History cutoffs are enforced inside the calculation** (for example,
  inside the forecast builder), never only at call sites. A caller that
  forgets to filter must still be unable to leak future data.
- **Forecasts and pre-match snapshots are immutable** once created. Later
  evaluation, tuning, or correction never rewrites an original forecast.
- **Determinism:** identical inputs + model version + seed + config produce
  identical output. All randomness runs through explicitly seeded RNGs; no
  unseeded, implicit, or global random state.
- **A normalized probability distribution is not evidence of accuracy.**
  Insufficient data, missing data, model disagreement, and weak calibration
  are legitimate results to report. They are never hidden, smoothed over,
  or dressed up as confidence.

## ENGINEERING DISCIPLINE

- **One phase at a time** per `docs/ROADMAP.md`. Never start Phase N+1 until
  Phase N has passed review, been committed, and passed the monitor sweep.
- **Blocks of three:** phases run in blocks — 1-3, 4-6, 7-9, 10-12, 13 —
  with the developer as acceptance gate at each block boundary. Never start
  Phase N+1 across a block boundary before the developer has accepted the
  block.
- **Module separation:** pure statistical code never imports storage, HTTP,
  or I/O.
- **Lightweight:** venv, pytest, and the standard library first. Every
  dependency must be justified; the default is none.
- **Tests prove phases.** Report real commands and real output. Never claim
  that unrun tests passed. Never weaken, delete, skip, or xfail a test to
  make a phase pass — if a test looks wrong, report it and ask.
- **Commits only via the checkpoint protocol** on green tests.
- **Never push** to any remote without explicit developer authorization.
- **No frontend** before the core pipeline is reliable.
- **No generic multi-domain framework** before football works end to end.

## ENVIRONMENT

Linux Mint, modest hardware, Python in a venv, local and offline-capable.
Design for this machine, not for a cloud.
