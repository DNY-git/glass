# Sports Looking Glass — UI Handoff Brief

**Version:** 1.1 · 2026-10-26
**Revision:** 1.1 corrects the draw-deficit definition, team count (6), stage map (8 of 10), API launch/port wording, static-export claim, and evaluation projection-field framing.
**For:** the agent building the Sports Looking Glass viewer UI
**Source repo:** https://github.com/DNY-git/glass (commit `b8cc13d`, 16 commits, master)
**This kit:** `HANDOFF-UI.md` (this file) · `data/` (static JSON exports) · `fixtures/golden-pins.json` (verification numbers) · `starter/` (runnable Next.js skeleton)

---

## 0. Read this first

You are building a **read-only viewer** for an already-built and test-verified
deterministic football analysis pipeline. You are **not** building product
features, prediction flows, or anything interactive beyond filtering and
navigation. The system behind this UI has a strict engineering constitution:
byte-deterministic outputs, write-once storage, pre-registered evaluation, and
vocabulary guards that scan its own source code for forbidden claim-words. Your
UI must respect the same discipline. The data you will render is synthetic
(fictional "Obsidian Coast League"), small (60 matches, 57 forecasts), and
already fully computed. Your job is presentation only — faithful, honest,
traceable presentation. If a design decision ever tempts you to make the numbers
look more impressive, decisive, or predictive than they are, you have made a
wrong decision.

## 1. Project context you must respect

Sports Looking Glass is a research and decision-analysis engine: it ingests
historical match results, validates them, extracts chronological features, fits
a Poisson maximum-likelihood model, produces forecast probability distributions,
explores bounded scenarios, and evaluates its own forecasts against realized
results — strictly in chronological order. It estimates; it never promises; it
never places or assists bets. The repo was reconstructed from documentation
after the original was lost, then driven through 13 phases with reviewer/tester
gates to a "research-ready" state. Eight of its ten pipeline stages exist; the
two that don't (`app/state/`, `app/improvement/`) are documented gaps, not
secrets. Everything the UI shows must sit inside these facts. Phrases like
"the model thinks", "predicted winner", or "expected to win" are
**constitutionally alien** to this system — its own API response carries a
disclaimer string and its own tests would fail if such wording entered the
codebase. The UI is an outside viewer, but it inherits the posture: the
disclaimer travels with the data everywhere.

Key facts you will render:

| Fact | Value |
|---|---|
| Competition / seasons | Obsidian Coast League · 2024-25, 2025-26 |
| Matches ingested | 60 (synthetic, checked-in fixtures) |
| Forecasts produced | 57 (write-once, content-hashed) |
| Evaluated populations | 30 primary (clean) / 57 secondary (clean + flagged) |
| Excluded from scoring | 3 refusals, counted and keyed |
| Run digest | `150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f` |
| Evaluation record hash | `ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47` |
| Versions | model `poisson-mle-v1` · forecast `forecast-poisson-mle-v1` · SCHEMA_VERSION 2 · EVALUATION_VERSION 1 |
| Stage map | 8 of 10 built; stage 3 (`app/state/`) and stage 10 (`app/improvement/`) unbuilt (G1–G5) |

## 2. Non-negotiable constraints

These three constraints are **acceptance criteria**, not style advice. A build
that violates any of them is a failed build.

### 2.1 Vocabulary guards

The UI must never render claim-language. Mirror of the repo's own
`tests/test_vocab_guards.py`. Banned sets (case-insensitive, strict-segment
matched — ASCII alphanumeric boundaries, so underscores are separators):

- **Outcome-comparative tokens:** `outperform`, `outperforms`, `outperformed`,
  `outperforming`, `beat`, `beats`, `beaten`, `beating`,
  `hit`, `hits`, `winner`, `champion`, `preferred`
- **Accuracy trio:** `validated`, `accurate`, `beating`
- **Field-name bans:** `performance`, `rank`, `ranking`, `correct`,
  `correctness`, `best`, `accuracy` — never use these as column names, labels,
  or variable names. Sanctioned alternatives: "results", "standing",
  "realized frequency", "descriptive". The starter's guard scans its own
  source for these tokens (labels/identifiers); they are not applied to prose.
- **Sanctioned metric identifiers** (legal ONLY as metric names on the
  evaluation surface, exactly as the evaluation package uses them):
  `log_loss`, `logloss`, `brier`, `rps`, `hit_rate`, `calibration`. Do not use
  them in prose sentences; do not decorate them with claim adjectives. The
  starter's guard strips these identifiers before the token scan, so
  `hit_rate` does not trip `hit`.

The starter ships `lib/vocab.ts` with these exact lists and a
`scripts/vocab-check.mjs` that scans built output and the starter's own source.
Keep both intact.

### 2.2 Disclaimer visibility

Every forecast view renders the built-in disclaimer string — verbatim, from the
data (field `disclaimer`), never paraphrased, never buried in a global footer
alone:

> "In-sample analytic estimate from the fitted model; pending chronological
> evaluation against realized results (Phases 9 and 11). Not evidence of
> accuracy."

The starter's `DisclaimerBanner` component does this; keep it on the forecast
list rows or cards **and** the forecast detail page.

### 2.3 Digest provenance

Every view that shows data must surface the hash that produced it: the
forecast's `content_hash` on detail views, the run digest `150b9796…` (short
form acceptable, full form on the provenance page) wherever evaluation numbers
appear, and the record hash on the evaluation page. Users must be able to
connect what is on screen to what is in the store. The starter's `DigestChip`
component exists for this.

### 2.4 Descriptive-only framing (implied by 2.1, spelled out)

Render model and baseline numbers side by side, unranked, with no ordering that
implies one "wins". No confidence intervals (they don't exist in the data), no
percent-improvement arithmetic, no star ratings, no "model vs baseline" verdict
line. Present; do not conclude.

## 3. Data contracts

Three static files ship in `data/`, byte-deterministic JSON. The forecast
object shape is **identical to the live API's response body** (see §4), so the
UI types work in both modes.

### 3.1 `data/forecasts.json` — array of 57 forecast objects

One object per stored forecast, key-sorted. Field table:

| Field | Type | Meaning |
|---|---|---|
| `competition`, `season`, `date`, `home`, `away` | string | the natural key (identity of the forecast) |
| `as_of` | string | data cutoff date used for the fit |
| `lambda_home`, `lambda_away` | float | fitted Poisson intensities (goals per team) |
| `max_goals` | int | scoreline matrix truncation (10) |
| `outcome_probs.home / .draw / .away` | float | analytic outcome probabilities (sum ≈ 1; `dropped_mass` discloses truncation) |
| `convergence_status` | string | optimizer outcome, e.g. `CONVERGED`, `SINGULAR_SYSTEM` — render it, never hide it |
| `insufficient_data` | bool | true when history was thin (e.g. opening day) — flagged forecasts "scream" |
| `insufficient_teams` | string[] | teams lacking history at `as_of` |
| `dropped_mass` | float | probability mass beyond `max_goals` (truncation disclosure, NOT an uncertainty band) |
| `kickoff` | `{availability, time}` | availability is `AVAILABLE` or `MISSING` — missing stays missing, never a default |
| `model_version`, `forecast_version` | string | provenance echo |
| `input_digest`, `content_hash` | string (sha256) | provenance echo — `content_hash` is what the store verified |
| `disclaimer` | string | fixed honest companion field (§2.2) |

### 3.2 `data/evaluation.json` — the digest-gated evaluation result, plus UI projection fields

Top level: `run_digest`, `accounting` (`n_targets` 60 = `n_predictions` 57
(`n_clean` 30 + `n_flagged` 27) + `n_refusals` 3, plus `refusal_keys`),
`primary`, `secondary`, `overdispersion`, and a `note` string that says
"descriptive only" — render that note on the evaluation page.

`note` and `n_draw_contributions` are **UI projection fields** added by the
export, not fields of the repo's `EvaluationResult` / `PopulationScores`:
`note` is a fixed descriptive caption; `n_draw_contributions` is the derived
count of realized draws in the population (7 primary / 14 secondary), computed
from the evaluation contributions. The metrics, calibration, and diagnostics
are the repo's values.

Each population carries `n_matches`, `model` and `baseline` (each
`{log_loss, brier, rps}`), `calibration` (`n_matches`, `n_pairs` = 3 ×
n_matches, and exactly **five bins** of `{n, mean_p, realized_frequency}` —
`mean_p` and `realized_frequency` are `null` exactly when `n` is 0; never merge
bins), `draw_deficit` (**realized draw rate minus mean forecast draw
probability**), and the projection-only `n_draw_contributions`.

`overdispersion` is `{n, mean, variance}` — a number only: no test, no
significance, no verdict. Label it exactly that way.

### 3.3 `data/provenance.json` — pins, versions, stage map, API contract

The digest/version/stage-map subset of the §1 table (counts live in
`forecasts.json` / `evaluation.json`), plus `fixture_file_sha256s`,
`replay_seed` (20261017), the `api_contract` block (route list, error codes,
localhost bind, launch note, byte-determinism), the `stage_map` (ten stages
with numbers, names, paths, and built/unbuilt status), and `honest_limits` —
render the honest-limits list verbatim on the provenance page.

### 3.4 `fixtures/golden-pins.json` — verification numbers

The pinned values a **correct** UI renders: `metrics` (four triples), `accounting`
[60, 57, 3, 27, 30], `dominant_bin_share`, `draw_deficit`,
`n_draw_contributions`, `calibration_total_pairs`, and the two full digests.
Your rendered numbers must match these exactly (the metrics and diagnostics
come from `data/evaluation.json`, which was exported from the same pipeline run;
`n_draw_contributions` is the projection count — if they ever disagree, the
data layer is broken, not the pins).

## 4. Data source modes — implement static, document live

**Mode A — static data (implement this):** the UI imports `data/*.json` at
build time (see `starter/lib/data.ts`). There is no data backend; the app is a
Next.js server app that renders from static JSON, and it deploys to Vercel as a
Next.js app. This mirrors the system's own store-then-serve design. This is the
default and the only mode the starter wires up.

**Mode B — live localhost API (document, don't build yet):** the repo can serve
the same bodies at runtime. Contract (from `provenance.json → api_contract`):

- `GET /health` → `{"status":"ok"}`
- `GET /forecasts/{competition}/{season}/{date}/{home}/{away}` → one forecast
  body, shape-identical to the array elements in `forecasts.json`
- Errors: malformed path → 400 `{"error":"bad_request"}`; unknown key → 404
  `{"error":"unknown_fixture"}`; POST/PUT/DELETE → 405
  `{"error":"method_not_allowed"}` (with `Allow: GET`); unknown route → 404
  `{"error":"not_found"}`; integrity failure → 500
  `{"error":"integrity_error"}`; other methods (e.g. PATCH) → the stdlib's
  default 501 response (not a JSON body)
- Binds `127.0.0.1` only, sends **no CORS headers** → a browser page cannot
  fetch it cross-origin. The repo's `create_server(db_path, host="127.0.0.1",
  port=0)` defaults to an ephemeral port; `8765` is a suggested local
  convention, not a built-in. No CLI/launcher is included — bind it in a small
  Python launcher. The documented upgrade path is a thin Next.js route handler
  (`app/api/forecasts/[...key]/route.ts`) that server-side fetches
  `http://127.0.0.1:8765/...` and relays the body. The starter does not set
  `output: 'export'`; if you add it for pure-static hosting, the proxy route is
  impossible. Document this in the README; implement only if explicitly asked
  later.

## 5. The UI surfaces

Shared shell: quiet, documentation-like design. No dashboards-glow, no
sportsbook aesthetics, no red/green win-loss color coding. Suggested palette:
near-white background, slate text, one restrained accent (e.g. indigo) for
interactive elements only. Numbers in tabular figures. The disclaimer banner is
visibly present, not decorative.

### 5.1 Forecast browser (`/`)

- List all 57 forecasts from `forecasts.json`, default order: date, then home
  team (matches the store's read-back order).
- Each row/card: date, home vs away, outcome probability bars
  (home/draw/away — horizontal stacked bar or three mini-bars; label the
  percentages, 1 decimal), season chip, and a flagged-state badge when
  `insufficient_data` is true ("insufficient data" — never a warning triangle
  implying danger).
- Filters: by season (2024-25 / 2025-26), by team (dropdown of the 6 teams),
  free-text search over team names. All client-side.
- Every row shows the full disclaimer (small, compact) — the detail page gives
  it full prominence.
- Row click → detail page at `/forecast/{competition}/{season}/{date}/{home}/{away}`
  (encodeURIComponent each segment).

### 5.2 Forecast detail (`/forecast/...`)

- Header: natural key fields + kickoff block (`time` + `availability`; if
  `MISSING`, render "kickoff: not recorded" — never a fabricated time).
- **Probability bars** large: home / draw / away with percentages.
- Model internals panel: `lambda_home`, `lambda_away`, `max_goals`,
  `dropped_mass` (label: "probability mass beyond 10 goals — truncation
  disclosure"), `convergence_status`.
- Integrity panel: `content_hash`, `input_digest`, `model_version`,
  `forecast_version`, `as_of` — via `DigestChip`.
- If `insufficient_data`: prominent banner listing `insufficient_teams` and a
  sentence: "This forecast was fitted with insufficient history for the listed
  teams; it is carried flagged in the store and scored only in the secondary
  population."
- Disclaimer banner (full string).
- Link: "Evaluation context" → `/evaluation`.

### 5.3 Evaluation page (`/evaluation`)

- Digest chip first: run digest + record hash + `EVALUATION_VERSION` 1.
- Accounting strip: 60 targets = 30 clean + 27 flagged + 3 refusals — render
  the equation visually (e.g. segmented bar), counts on every number (the
  project's own "n-on-every-number" rule).
- Populations table (primary n=30, secondary n=57): model row and baseline row
  side by side, columns log loss / Brier / RPS, 4 decimals, **unranked** —
  identical styling for both rows, no ordering, no delta column.
- Calibration chart per population: 5 fixed bins, grouped bars of mean p vs
  realized frequency, `null` bins rendered as visibly empty with "n = 0" —
  never merged, never dropped. Caption must include n_pairs (90 / 171).
- Diagnostics: `draw_deficit` (label: "realized draw rate minus mean forecast
  draw probability — descriptive"), `overdispersion` (label:
  "variance-versus-mean of realized team goals — a number only: no test, no
  significance, no verdict"), and the projection count
  `n_draw_contributions` (7 primary / 14 secondary — a count, not a metric).
- The refusal list: 3 natural keys, rendered as data (they exist in
  `evaluation.json → accounting.refusal_keys`) with a one-line explanation that
  refusals are excluded from scoring and counted.
- Render `evaluation.json → note` verbatim near the top (`note` is a UI
  projection caption, not a repo field).

### 5.4 Provenance page (`/provenance`)

- Full digests (monospace, wrap, copyable) for run digest and record hash;
  fixture file sha256s table.
- Stage map: 10-stage pipeline visualization, 8 built / 2 unbuilt — each row
  shows stage number, name, path, and status; unbuilt stages are styled as
  explicitly documented gaps (G1–G5), with their paths (`app/state/`,
  `app/improvement/`), never styled as "coming soon" marketing.
- Versions block: SCHEMA_VERSION 2, EVALUATION_VERSION 1, model/forecast
  versions, replay seed.
- API contract block (routes, error codes, localhost-only note, suggested-port
  launch note) — this page doubles as the system's public self-description.
- `honest_limits` list verbatim.

### 5.5 Methodology page (`/methodology`)

- What the model is: Poisson MLE with an internal history cutoff, fitted
  chronologically per `as_of`, scoreline matrix truncated at 10 goals. Plain
  language, no math rendering library needed.
- What the numbers are and are not: in-sample analytic estimates, pending
  chronological evaluation; not evidence of accuracy (quote the disclaimer);
  the system "estimates, never promises".
- Population definitions: primary = clean only; secondary = clean + flagged;
  refusals excluded and counted. Flag = insufficient team history at `as_of`.
- The discipline section: write-once storage, byte-deterministic bodies,
  digest-gated evaluation, vocabulary guards — one short paragraph each, framed
  as engineering facts.
- End with the honest-limits list (verbatim from `provenance.json`).

## 6. Stack & repository layout

Next.js (App Router, TypeScript, Tailwind). The `starter/` directory is a
runnable skeleton with all five page files stubbed to working minimums, typed
data access, and the guard components — extend it, don't restart.

```
starter/
├── package.json                 next 15 · react 19 · tailwind 4
├── next.config.ts
├── tsconfig.json
├── postcss.config.mjs
├── app/
│   ├── layout.tsx               shell: nav (4 surfaces) + disclaimer footer
│   ├── globals.css              tailwind import + tabular-nums base
│   ├── page.tsx                 5.1 forecast browser
│   ├── forecast/[competition]/[season]/[date]/[home]/[away]/page.tsx   5.2
│   ├── evaluation/page.tsx      5.3
│   ├── provenance/page.tsx      5.4
│   └── methodology/page.tsx     5.5
├── components/
│   ├── DisclaimerBanner.tsx     §2.2 — the verbatim string, prominent
│   ├── ProbabilityBars.tsx      home/draw/away bars, labeled percentages
│   └── DigestChip.tsx           §2.3 — hash display + copy button
├── lib/
│   ├── data.ts                  typed loaders over data/*.json
│   └── vocab.ts                 §2.1 banned sets + assertClean() helper
├── scripts/
│   └── vocab-check.mjs          scans built HTML + authored source (§8)
└── data/                        copies of ../data/*.json (build-time imports)
```

Conventions: server components by default; filters/search on the browser page
may be a client component. The starter builds as a Next.js server app; its
detail pages render on demand. Pure-static hosting is optional: add
`generateStaticParams` over `allForecasts()` and set `output: 'export'` in
`next.config.ts`; then the Mode-B proxy route is impossible (API routes need
the server). The starter does not enable it. If the agent later adds the
Mode-B proxy route, that route is the only piece that talks to the source
repo's server.

## 7. Acceptance criteria

The build is accepted when **all** of the following hold:

1. `npm install && npm run build` succeeds clean; `npm run dev` serves all five
   page files navigably (four nav surfaces plus the detail view).
2. Forecast browser lists exactly **57** forecasts; team filter covers exactly
   **6** teams; season filter yields counts that sum to 57.
3. Forecast detail for natural key
   `Obsidian Coast League / 2024-25 / 2024-08-17 / Emberfield Kestrels / Harbourlight Comets`
   renders `lambda_home` 1.1667 and `lambda_away` 1.1667, probability bars
   35.9% / 28.1% / 35.9%, `convergence_status` `SINGULAR_SYSTEM`,
   `insufficient_data` true with 6 listed teams, and the full disclaimer.
4. Evaluation page renders log loss 1.0893 (primary model) and 1.1003
   (secondary baseline) — matching `golden-pins.json` to 4 decimals — with
   model and baseline rows visually identical in rank terms.
5. Calibration charts show 5 bins each with correct n values (2/73/15/0/0 and
   6/137/27/1/0), empty bins visibly empty, captions carry n_pairs 90/171.
6. Provenance page shows both full digests, both unbuilt stages as documented
   gaps, and the honest-limits list verbatim.
7. `node scripts/vocab-check.mjs` (scans built output HTML and the starter's
   own source) reports **zero** banned-token hits.
8. Disclaimer string appears on the forecast list, every forecast detail, and
   is quoted on the methodology page.
9. No view renders a confidence interval, delta column, improvement percentage,
   star rating, or any ranked model-vs-baseline presentation.
10. All rendered numbers display with source traceability (digest chip or
    content_hash within one click of the number).

## 8. Verification recipes

```bash
cd starter
npm install
npm run build
npm run start        # or npm run dev

# vocabulary guard over built output + authored source:
node scripts/vocab-check.mjs        # scans .next/server/app + app/components/lib

# pin spot-check (one metric against the golden pins):
node -e "const d=require('./data/evaluation.json');const p=require('./fixtures/golden-pins.json');if(d.primary.model.log_loss!==p.metrics['primary.model'][1])throw new Error('pin mismatch');console.log('pins OK')"
```

(The pins file is already at `starter/fixtures/golden-pins.json`; the check
reads it directly.)

## 9. Out of scope / forbidden moves

- **Do not modify the source repo.** `app/`, `tests/`, `docs/`, `scripts/` in
  the glass repository are constitution-governed; the UI is a separate viewer.
  Never point your build at the repo's internals — only at the JSON in this kit
  or the documented API contract.
- **No committed database.** Never ship the sqlite file; the JSON export is the
  distributable form.
- **No scoring, verdicts, or new statistics.** If a chart idea requires
  computing a number not present in `data/`, drop the chart idea (arithmetic
  like percentage-labeling of existing probabilities is fine; derived metrics
  are not).
- **No betting vocabulary or affordances.** No odds, no stake sizing, no "value
  finder", no bookmaker comparisons. The system's own words: it never places or
  assists bets.
- **No fabricated data.** Missing kickoff stays missing; empty calibration bins
  stay empty; refusals stay excluded. Every gap in the data is rendered as a
  gap, never papered over.
- **No fake freshness.** The data has no timestamp field by design (S2 rule).
  Do not add "last updated" labels; the provenance page's digests are the
  freshness story.

## 10. Source-repo map (reference only)

| Path | What it is |
|---|---|
| `app/api/serialize.py` | the exact forecast body shape your types must mirror |
| `app/api/server.py` | the read-only HTTP surface (Mode B contract) |
| `app/evaluation/evaluate.py` | dataclasses behind `evaluation.json` (plus the UI projection fields documented in §3.2) |
| `tests/test_evaluation.py` | where the evaluation goldens (draw deficit, bins, metrics) are pinned |
| `tests/test_integration.py` | end-to-end pins (ADV-6/12.2) |
| `tests/test_vocab_guards.py` | the vocabulary-guard source of truth |
| `docs/KNOWN-LIMITATIONS.md` | the honest-limits canonical text |
| `docs/ROADMAP.md` | Block acceptance record, stages, postponed items |

Final note to the agent: the discipline described here is the product. The
fastest way to fail this handoff is to make the UI "more compelling" by
softening the honesty machinery. When in doubt, render the gap.
