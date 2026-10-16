# PHASE 2 BRIEF — DOMAIN AND DATA

Status: proposed (2026-10-16, glass-architect). Per docs/ROADMAP.md this
is Block 1, Phase 2. Phase 3 is not planned until this phase passes
review, is committed at its checkpoint, and passes the monitor sweep
(block mode).

## Objective

Deliver pipeline stages 1–2 (DATA, VALIDATION) and the domain layer per
HANDOFF Part IX item 2 and Part III: domain models, OpenFootball-format
ingestion from local checked-in fixtures, validation that reports defects
rather than guessing around them, and idempotent imports — so every later
phase consumes one canonical, provenance-carrying, deterministically
ordered match state built entirely offline. No statistics, no features,
no storage, no API this phase.

## State verified before writing this brief (probed 2026-10-16)

- HEAD = `45ed27e` ("phase 1: foundation venv, pytest wiring, app
  package, health-check loop"); `866eba5` before it. Phase 1 reviewer
  verdict PASS; monitor sweep verdict WARN with two carried findings
  (below).
- Working tree is **not clean**: `git status --porcelain` →
  ` M docs/HEALTH-LOG.md`, ` M docs/PROGRESS-LOG.md`, ` M docs/ROADMAP.md`
  (diff verified docs-only, +27/−9 — the protocol-predictable post-commit
  records the monitor flagged). They must land in Phase 2's checkpoint
  commit (monitor finding 1).
- **No football data exists anywhere**: no `fixtures/`, no `data/`
  directory on disk; `.gitignore` contains `data/`; `docs/DATA-SOURCES.md`
  does not exist; `docs/briefs/` contains only `phase-1.md`.
- `docs/KNOWN-LIMITATIONS.md` item 2 still cites the stale "~85 s of that
  margin" figure the monitor could not reproduce (~105 s observed margin;
  PROGRESS-LOG records 15.78 s suite runs). Corrected in this phase's
  DOCS step (monitor finding 2).
- `README.md` "Current state" still says Phase 1 "checkpoint pending" —
  stale since 45ed27e.
- Suite today: 9 passed; `scripts/health-check.sh` unchanged since Phase 1
  (recursion guard present). Python 3.12.3, pytest 9.1.1 in `.venv`.
- No statistical design decisions exist yet, so glass-quant was not
  consulted for this brief (it becomes mandatory at Phase 3).

## Design decisions (this brief resolves them; PLAN/ARCHITECTURE flagged these for Phase 2)

1. **`app/storage/` is NOT created this phase.** PLAN §2 and
   ARCHITECTURE.md say the sqlite backend is "to be confirmed in the
   Phase 2 brief": confirmed as **deferred**. No durable state is needed
   by any criterion below; idempotency is proven at the loader/collection
   level. The sqlite proposal returns in the first brief that needs
   durable state (immutable snapshots, Phase 5+). Consequently `data/` is
   also not created (out of scope).
2. **Fixtures are small, synthetic, clearly fictional, OpenFootball-shaped
   JSON text files checked in under `fixtures/`** (open question 1 asks
   the developer to ratify this against the real-data alternative). No
   network touch, ever, at build time or runtime; no licensing discussion
   needed for hand-authored fictional data.
3. **JSON only this phase** (open question 3). The handoff mentions
   JSON/CSV encodings; CSV arrives only when a source needs it.
4. **Severity rule.** Defects have severity `error` or `warning`.
   *Error* (malformed required data: date, teams, score) → the record is
   excluded from accepted state; nothing is guessed to replace it.
   *Warning* (malformed optional data: kickoff `time`, `xg`) → the record
   is retained, the malformed value is dropped to availability `MISSING`
   (never converted into a value), and the defect is reported. An
   *absent* optional field is availability `MISSING`, not a defect; a
   *present-but-malformed* optional field is both.
5. **Natural key** = (competition, season, date, home team, away team).
   Round labels are metadata, not identity. Identical-content duplicates
   collapse silently (this is what makes re-import a no-op); a *conflicting*
   duplicate (same key, different content) is a defect: first occurrence
   retained in file order (deterministic), later copies excluded with an
   `error`.
6. **Defect reports are outputs, not state.** State = accepted records
   only; reports are recomputed per import and must be byte-identical
   across runs of the same file.
7. **Canonical order** for any collection iteration or serialization:
   (date, competition, season, home, away) — chronological primary,
   fully tie-broken. `canonical_state(collection) -> str` is the single
   canonical serialization entry point (sorted keys/records, no
   timestamps), used by the idempotency and determinism tests.
8. **Provenance** per ingested record: repo-relative source path + sha256
   of raw file bytes. Explicitly **no mtime, no absolute path, no
   wall-clock timestamp** (environment-dependent → nondeterministic).

## Files and directories to create or modify (BUILD step)

Create:

- `app/domain/__init__.py`, `app/domain/models.py` (indicative names;
  builder may split) — frozen dataclass models: `Team`, `Score`, `Match`,
  `Provenance`, availability enum (`AVAILABLE`/`MISSING`), a sorted
  deduplicating match collection keyed by the natural key, and
  `canonical_state()`.
- `app/ingestion/__init__.py`, `app/ingestion/openfootball.py` — reads a
  local JSON match-list file, parses records, attaches provenance,
  returns parsed payload; merge-into-collection function implementing
  idempotency. Filesystem yes; network never.
- `app/validation/__init__.py`, `app/validation/report.py`,
  `app/validation/checks.py` — `Defect` (code, severity, location =
  repo-relative file + index in `matches` array, message), `DefectReport`
  (deterministically ordered), and pure validation functions over parsed
  records. No filesystem, no HTTP.
- `fixtures/openfootball/valid/season-1.json`,
  `fixtures/openfootball/valid/season-2.json`,
  `fixtures/openfootball/defects/defect-sample.json` — per the fixture
  specification below.
- `tests/test_domain.py`, `tests/test_ingestion.py`,
  `tests/test_validation.py`, `tests/test_fixtures_and_hygiene.py` —
  criteria 1–14, 1:1.

DOCS step (phase loop; verified by reviewer inspection, not tests —
consistent with Phase 1):

- `docs/DATA-SOURCES.md` (**new**) — OpenFootball match-list JSON field
  mapping actually implemented; fixture provenance ("hand-authored
  synthetic data, fictional teams, no real-world entity"), the synthetic
  marker convention, the documented `xg` extension (open question 5),
  explicit "nothing downloads at runtime" statement.
- `docs/KNOWN-LIMITATIONS.md` — **fix item 2's stale ~85 s figure**
  (monitor-carried warning) with the observed ~105 s margin and recorded
  suite times, keeping the re-scope-not-weaken rule; add Phase 2
  limitations (synthetic fixtures diverge from real OpenFootball quirks;
  JSON only; no durable storage yet; natural-key collision limitation).
- `README.md` — Current state: Phase 2, real test count, Phase 1
  checkpoint 45ed27e.
- `docs/ARCHITECTURE.md` — instantiation table: `app/domain`,
  `app/ingestion`, `app/validation`, `fixtures/` now exist; `app/storage`
  deferred per decision 1.
- `docs/PLAN.md` §2 — replace "sqlite … to be confirmed in the Phase 2
  brief" with the confirmed deferral.
- `docs/ROADMAP.md`, `docs/PROGRESS-LOG.md` — standard end-of-phase
  status/log updates; the three currently uncommitted protocol docs
  (HEALTH-LOG, PROGRESS-LOG, ROADMAP) **must be included in the Phase 2
  checkpoint commit** (monitor warning 1).

Do not create or modify: `scripts/health-check.sh`, `pytest.ini`,
`conftest.py`, `data/`, any `app/` subpackage other than
domain/ingestion/validation, requirements/pyproject, CI, linters, Docker.

## Fixture specification (tests below are written against these numbers)

All three files: top-level shape `{"name": ..., "synthetic": true,
"matches": [ ... ]}` with OpenFootball-style records
`{"round", "date", "time", "team1", "team2", "score": {"ft": [h, a]},
"xg": {"home": ..., "away": ...}}` (`time` and `xg` optional). All dates
strictly in the past relative to build day. Teams: 6 clearly fictional
names (fictional by construction; reviewer verifies — a hardcoded
real-club list in a test would be fake assurance).

| File | Records | kickoff `time` | `xg` | Defects |
|---|---|---|---|---|
| `valid/season-1.json` — competition, season `2024-25`, 6 teams, double round-robin (10 matchdays × 3) | 30 | present on all 30 | absent | none |
| `valid/season-2.json` — same competition, season `2025-26` | 30 | absent on all 30 | present on exactly the first 10 by canonical order | none |
| `defects/defect-sample.json` | clean records + one per planted defect below | mixed | mixed | 7 planted, codes fixed: |

Planted defects (exactly one report entry each): `invalid_date`
("2024-13-40", error), `missing_home_team` (error),
`invalid_score_shape` (`ft` not a 2-element int pair, error),
`invalid_score_value` (`ft: [-1, 3]`, error), `invalid_kickoff_time`
(`"25:99"`, warning), `invalid_xg_value` (negative xG, warning),
`conflicting_duplicate` (two records, same natural key, different score —
first retained, second error). The fixture includes ≥3 clean records so
"first retained" is observable.

## Dependencies

- **None new.** stdlib only: `json` (fixture parsing), `dataclasses` /
  `typing` / `enum` (models), `hashlib` (provenance digest),
  `pathlib` (local file reads), `ast` (import-hygiene test).
- pytest — already installed in Phase 1's venv; justification unchanged
  (constitution-mandated test loop; health script invokes it).
- Explicitly refused: `jsonschema` or any schema library (hand-rolled
  checks suffice at this scale), `requests`/`httpx` (nothing fetches),
  numpy/pandas, FastAPI, sqlite3 usage this phase. Default is none.

## Acceptance criteria

Criteria 1–14 map 1:1 to pytest test functions. Criterion 15 is the
suite-level gate, verified by recorded executions (tester, reviewer ×2,
monitor) exactly as in Phase 1 — a test cannot assert its own suite's
greenness without circularity. No test may use skip or xfail.

1. `tests/test_domain.py::test_domain_models_frozen_value_semantics` —
   `Match`, `Score`, `Provenance` (and every other model the builder
   introduces) are frozen dataclasses: attribute assignment raises
   `AttributeError`; structurally equal instances compare equal;
   ingested records cannot be mutated after creation.
2. `tests/test_domain.py::test_missing_data_is_availability_status_not_imputation` —
   a match with absent kickoff and absent xG exposes availability
   `MISSING` with value `None` for both; `canonical_state()` of such a
   record contains no placeholder anywhere (no `0.0` xG, no `""`/`00:00`
   kickoff, no default date), asserting missing data is a first-class
   result, never imputed.
3. `tests/test_domain.py::test_matches_sort_deterministically` — sorting
   a shuffled list of matches yields exactly the canonical order
   (date, competition, season, home, away); the natural key equals
   (competition, season, date, home, away); equal-content records with
   the same key compare equal.
4. `tests/test_ingestion.py::test_load_valid_fixtures_exact_contents` —
   loading both valid fixtures yields exactly 60 matches, 6 distinct
   teams, seasons {`2024-25`, `2025-26`}, integer scorelines, round
   labels; first and last match by canonical order asserted as exact
   golden tuples (date, round, teams, score) checked against the fixture
   text.
5. `tests/test_ingestion.py::test_provenance_path_and_digest_without_timestamps` —
   every ingested match carries provenance whose sha256 equals an
   independently computed `hashlib.sha256(raw file bytes)` and whose path
   is repo-relative (`fixtures/...`); the provenance/canonical output
   contains no absolute repo path, no `st_mtime` value, and no
   timestamp-like field (determinism: environment data never enters
   state).
6. `tests/test_ingestion.py::test_idempotent_import_same_file_twice` —
   importing the same valid fixture twice into one collection leaves
   `canonical_state()` byte-identical to a single import (same count, no
   duplicates); importing the defect fixture twice likewise leaves
   identical state **and** an identical defect report.
7. `tests/test_ingestion.py::test_duplicate_handling_identical_dedupes_conflict_defects` —
   identical-content duplicate records collapse to one with no defect and
   no state change; a conflicting duplicate produces exactly one
   `conflicting_duplicate` error naming both record locations, the first
   occurrence is retained in state, the later copy is excluded.
8. `tests/test_validation.py::test_valid_fixtures_validate_clean` —
   validating both valid fixtures yields an empty defect report (absent
   optional fields are missing availability, explicitly *not* defects).
9. `tests/test_validation.py::test_planted_defects_reported_exactly_once_each` —
   validating the defect fixture yields exactly the seven entries listed
   in the fixture specification — each code once, with severity, file
   path and record index — and nothing else.
10. `tests/test_validation.py::test_validation_reports_without_repairing` —
    for the defect fixture: accepted-state record count equals imported
    records minus the error-severity ones; no malformed value is coerced
    into state (the bad date never becomes any date; no team is defaulted
    or invented; scores are never clamped; the conflicting copy is never
    merged); every defect carries code, severity, location, and a
    human-readable message — defects are reported, never guessed around.
11. `tests/test_validation.py::test_availability_summary_counts_missing` —
    loading only the two valid fixtures reports availability counts
    exactly: kickoff 30 `AVAILABLE` / 30 `MISSING`; xG 10 `AVAILABLE` /
    50 `MISSING`; counts sum to 60; no imputed value appears in canonical
    output.
12. `tests/test_fixtures_and_hygiene.py::test_module_separation_and_no_network_imports` —
    AST scan of every `.py` under `app/`: no module imports `urllib*`,
    `http*`, `socket`, `requests`, `httpx`, `fastapi`, `sqlite3`,
    `app.storage`, or any `app.*` module outside its allowed set
    (domain: none; validation: `app.domain`; ingestion: `app.domain`,
    `app.validation`); `app/domain` and `app/validation` contain no
    `open()` calls and no `os`/`sys`/`pathlib`/`io` imports (pure — no
    filesystem); no `datetime.now`, `utcnow`, `time.time`, or `os.environ`
    anywhere under `app/` (no wall clock, no environment lookups). Encodes
    "pure domain/validation imports no HTTP" and offline-only as a
    standing structural test.
13. `tests/test_fixtures_and_hygiene.py::test_deterministic_replay_and_order_insensitive_state` —
    loading the same file twice in one process produces byte-identical
    `canonical_state()` strings; a copy of a valid fixture rewritten into
    `tmp_path` with its `matches` array shuffled (same records) produces
    the identical canonical state — iteration is sorted, input order is
    irrelevant, no wall clock, no randomness.
14. `tests/test_fixtures_and_hygiene.py::test_fixtures_checked_in_declare_synthetic` —
    every `*.json` under `fixtures/` parses, carries the in-band
    `"synthetic": true` marker, and lives under `fixtures/` (not the
    git-ignored `data/`); no test or module reads data from outside the
    repository (all fixture paths resolved relative to the repo root).
15. Suite gate (recorded execution) — `.venv/bin/python -m pytest -q`
    from the repo root reports 0 failed, 0 errors, 0 skipped, 0 xfailed,
    0 xpassed. Executed and pasted by the tester; executed independently
    (twice) by the reviewer; re-executed by the monitor via the health
    script. `bash scripts/health-check.sh` still completes with a `OK:`
    determinism line, `none` skips/xfails, and clean pip check.

## Out of scope

- `app/storage/` and any durable persistence, sqlite, `data/` directory
  (deferred per design decision 1).
- CSV encodings (open question 3), real OpenFootball downloads (open
  question 1), any network access at build time or runtime.
- `app/state`, `app/features`, `app/models`, `app/forecasts`,
  `app/api` — later phases; no FastAPI this phase.
- Computing, estimating, or back-filling xG, kickoff times, or rest days —
  Phase 2 only records their availability.
- A generic schema-validation library, a pluggable multi-format loader
  framework, CLI/argparse entry points.
- Leakage/poisoned-future-match tests (Phase 8); all fixture dates are in
  the past by design so later phases start clean.
- Changes to `scripts/health-check.sh`, `pytest.ini`, `conftest.py`;
  planning Phase 3 (block mode).
- Any docs change outside the DOCS-step list above.

## Risks

- **Leakage:** no calculation consumes history yet, so the leakage
  surface is small — but imputation is the leakage-adjacent failure mode
  here: a "helpful" default (xG 0.0, kickoff midnight) would poison every
  later phase. Guarded by criteria 2, 10, 11; the reviewer must check no
  default lurks outside canonical output.
- **Determinism:** provenance must not carry mtime/abs-paths (env
  data — criterion 5); JSON dict order and set iteration must never leak
  into outputs (criteria 3, 7, 13); no timestamps in reports (criterion
  12). Any deviation will eventually flip the monitor's double-run
  comparison.
- **Data quality / format drift:** synthetic fixtures cannot reproduce
  every quirk of real OpenFootball files; if real data is later accepted
  (open question 1), the loader will need tolerance work and this phase's
  defect fixture may under-cover. Recorded as a KNOWN-LIMITATIONS entry.
- **Natural-key collisions:** (competition, season, date, home, away)
  cannot distinguish two distinct matches between the same pair on one
  day (double-header). Impossible in the synthetic fixtures; documented
  as a limitation, not silently accepted.
- **Overengineering:** resist a JSON-Schema engine, a format registry,
  premature sqlite, and speculative `app/storage` scaffolding; three
  small modules and hand-rolled checks are sufficient. Also resist
  inflating fixture scale beyond open question 2's answer.
- **Suite cost:** the health test spawns the suite five times; adding
  ~14 tests grows wall time roughly proportionally. Watch the 120 s
  timeout of `tests/test_health_script.py` (KNOWN-LIMITATIONS item 2,
  figure corrected this phase) — if it trips, that phase's brief re-scopes
  the mechanism; never weaken, skip, or xfail the test.
- **Docs drift:** three protocol docs are already uncommitted; they must
  ride the Phase 2 checkpoint or every future monitor sweep stays WARN.

## Open questions for the developer

1. **Fixture provenance (BLOCKING — decides the fixture section above):**
   a. **(Recommended)** Hand-authored **synthetic** OpenFootball-format
   fixtures with clearly fictional teams, checked in under `fixtures/` —
   zero network, zero licensing questions, marked `"synthetic": true`
   and documented in `docs/DATA-SOURCES.md`.
   b. **Real OpenFootball data** — requires your decision on
   provenance/license (to be recorded in `docs/DATA-SOURCES.md`), a
   one-time download outside the runtime, and likely loader-tolerance
   work; the brief's fixture specification would be re-issued before
   BUILD.
2. **Fixture scale (BLOCKING):**
   a. **(Recommended)** 6 fictional teams × 2 seasons × double
   round-robin = 60 valid matches + the defect fixture — enough
   chronological history that Phase 3+ do not force fixture re-authoring.
   b. Minimal now (~15 matches, one season), extended when a consuming
   phase needs more.
3. **Format coverage (default a if unanswered):**
   a. **(Recommended)** JSON match lists only this phase; CSV encodings
   when a source needs them.
   b. Both JSON and CSV loaders in Phase 2 (larger scope, second fixture
   set).
4. **Storage deferral confirmation (default a if unanswered):** PLAN §2
   reserved this for the Phase 2 brief.
   a. **(Recommended)** `app/storage/` is not created this phase;
   idempotency is proven at loader/collection level; the stdlib-sqlite
   proposal returns in the first brief that needs durable state.
   b. Build a minimal sqlite store now (adds persistence criteria,
   `data/`, and scope to this phase).
5. **Synthetic xG extension (default a if unanswered):** OpenFootball
   carries no xG.
   a. **(Recommended)** Fixture records may carry an optional documented
   `xg` extension (clearly synthetic), enabling both branches of the
   availability logic; recorded in `docs/DATA-SOURCES.md`.
   b. No `xg` in fixtures — all xG availability is `MISSING` until a real
   source arrives, and criterion 11 becomes 0 `AVAILABLE` / 60 `MISSING`
   for xG.

Questions 1 and 2 must be answered before BUILD begins; 3–5 fall back to
their recommended defaults if unanswered at build start.
