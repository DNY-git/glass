# DATA SOURCES — SPORTS LOOKING GLASS

Every data source used by the engine, its format, provenance, and
license. As of Phase 2 (Domain and data, 2026-10-16) the repository
contains **only hand-authored synthetic fixtures** — there is no real
match data in this repository, and nothing downloads at runtime or at
build time.

## Primary format: OpenFootball match-list JSON (as implemented)

The loader is `app/ingestion/openfootball.py` (`load_records` /
`import_fixture`). It reads a **local JSON file only** — no network code
exists under `app/` (structurally enforced by the criterion-12 AST
hygiene test, which bans `urllib*`, `http*`, `socket`, `requests`,
`httpx`, and `fastapi` imports everywhere under `app/`).

### File-level shape (what the loader requires)

The Phase 2 brief's fixture specification listed
`{"name", "synthetic", "matches"}`; the builder extended the shape with
top-level `"competition"` and `"season"` keys, and the loader **requires**
them — they are structural, not decorative:

| Key | Required | Loader treatment |
|---|---|---|
| `competition` | yes | Must be a non-empty string; missing/invalid raises `ValueError`. Stamped onto **every** record (records carry no per-record competition). |
| `season` | yes | Same rule as `competition`; stamped onto every record. |
| `matches` | yes | Must be an array of objects; missing/invalid raises `ValueError`. |
| `name` | no | Human-readable fixture label only; **ignored** by the loader. |
| `synthetic` | no (loader) | In-band synthetic marker; ignored by the loader but **asserted** for every `fixtures/**/*.json` by criterion 14 (`test_fixtures_checked_in_declare_synthetic`). |

Top-level `ValueError`s (bad file, non-object top level, missing
`competition`/`season`/`matches`) are loader contract violations — they
raise, they are not defect-report entries. Record-level problems are
**reported as defects**, never raised and never guessed around.

### Record-level field mapping (as implemented)

| JSON field | Required | Domain field | Validation rule (code, severity) |
|---|---|---|---|
| `date` | yes | `Match.date` (str, `YYYY-MM-DD`) | Real calendar date required; else `invalid_date`, **error** → record excluded. |
| `team1` | yes | `Match.home` (str) | Non-empty string required; else `missing_home_team`, **error** → excluded. |
| `team2` | yes | `Match.away` (str) | Non-empty string required; else `missing_away_team`, **error** → excluded. |
| `score.ft` | yes | `Match.score` (`Score(home, away)`) | 2-element pair of non-negative integers; wrong shape → `invalid_score_shape`, **error**; negative goals → `invalid_score_value`, **error**. Scores are never clamped. |
| `time` | no | `Match.kickoff` (`OptionalValue`) | Absent → availability `MISSING`, **not** a defect. Malformed (not `HH:MM` 24h) → `invalid_kickoff_time`, **warning** → record retained, value dropped to `MISSING` (never converted). |
| `xg` | no | `Match.xg` (`OptionalValue[Xg]`) | Documented **synthetic extension**, see below. Absent → `MISSING`, not a defect. Malformed (pair of non-negative finite numbers required) → `invalid_xg_value`, **warning** → whole pair dropped to `MISSING`; a valid side is never kept beside a fabricated partner. |
| `round` | no | `Match.round_label` (str \| None) | Metadata, **not identity** (the natural key is (competition, season, date, home, away)). Absent → `None`, not a defect. Non-string → `invalid_round`, **warning**, label dropped. |

Severity rule (Phase 2 design decision 4): *error* = malformed required
data → record excluded from accepted state, nothing guessed to replace
it; *warning* = malformed optional data → record retained, malformed
value dropped to `MISSING`, defect reported. An **absent** optional
field is `MISSING`, not a defect; a **present-but-malformed** optional
field is both.

Duplicates within or across imports (same natural key): identical
content collapses silently (re-import is a no-op); a conflicting copy
(same key, different content) yields one `conflicting_duplicate`
**error** naming both record locations — the first occurrence in file
order is retained, the later copy excluded.

### Provenance (as implemented)

Every ingested record carries `Provenance(source_path, sha256)`:
the **repo-relative** file path and the sha256 of the raw file bytes.
Deliberately **no mtime, no absolute path, no timestamp** — environment
data must never enter state (determinism). Provenance accompanies
records but is excluded from `canonical_state()` (it is path metadata,
not match state).

## The fixtures (provenance of what is checked in)

All data currently in the repository lives under `fixtures/openfootball/`
and is **hand-authored synthetic data**: fictional competition ("Obsidian
Coast League"), 6 clearly fictional teams (Coralgate Athletic,
Thistledown Wanderers, Quarryhill Zenith, Harbourlight Comets, Silverpine
Rovers, Emberfield Kestrels), fictional seasons 2024-25 and 2025-26, all
dates strictly in the past. No real-world entity is represented or
implied; the data is authored as part of this repository and carries no
external license. Every file carries the in-band marker `"synthetic": true`
(criterion 14 enforces this for every JSON file under `fixtures/`).

| File | Records | Notes | sha256 |
|---|---|---|---|
| `fixtures/openfootball/valid/season-1.json` | 30 | kickoff `time` on all 30; no `xg`; no defects | `f779fc0a952e00ecd904c8019b288c43326635cb5c5a698f2f74870b11d57e39` |
| `fixtures/openfootball/valid/season-2.json` | 30 | no `time`; `xg` on exactly the first 10 by canonical order; no defects | `5a9da621c678933b0a5f0320a79c8c245783b34bbaf59a73e0fd7d7609d916a9` |
| `fixtures/openfootball/defects/defect-sample.json` | 12 | ≥3 clean records plus 7 planted defects: `invalid_date`, `missing_home_team`, `invalid_score_shape`, `invalid_score_value`, `invalid_kickoff_time` (warning), `invalid_xg_value` (warning), `conflicting_duplicate` — each reported exactly once (criterion 9) | `f29b1301f33a07e501dc04864a9b6e4e8de60a474f317cc13350b8c03d5868ee` |

Together the two valid files yield exactly 60 accepted matches, 6
distinct teams, seasons {`2024-25`, `2025-26`} (criteria 4 and 11).

## The synthetic `xg` extension (documented)

Real OpenFootball data carries **no xG**. Per Phase 2 brief open
question 5 (recommended default accepted), fixture records may carry an
optional documented `xg` extension: `{"home": <number>, "away": <number>}`
with non-negative finite numbers. It is synthetic by construction,
clearly marked via the file-level `"synthetic": true` marker, and exists
to exercise both branches of the availability logic (AVAILABLE and
MISSING) ahead of a real shot-data source. When a real xG source
arrives, its provenance will be recorded here.

## Nothing downloads at runtime

There is no download, fetch, or network code path in the engine.
Ingestion reads local files with `pathlib`/`json` only; `app/domain`
and `app/validation` are pure (no filesystem access at all, enforced by
the criterion-12 AST test). The `data/` directory (git-ignored working
area, per HANDOFF Part III) does not exist yet — durable storage is
deferred (Phase 2 brief design decision 1; see
`docs/KNOWN-LIMITATIONS.md`).

## Not yet used: real OpenFootball data

Real OpenFootball match lists are **not** consumed as of Phase 2. If the
developer later accepts real data (Phase 2 brief open question 1, option
b), this file will record its exact source, version, and license before
any file is checked in, and the loader will need tolerance work for
real-world format quirks the synthetic fixtures cannot reproduce (see
`docs/KNOWN-LIMITATIONS.md`, Phase 2).
