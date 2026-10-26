# Looking Glass UI Kit — Single-File Bundle

This bundle contains EVERY file from `looking-glass-ui-kit.zip` concatenated,
each introduced by a path header like:

    ===== FILE: <relative/path> =====

Reconstruction rule for your agent:

1. For each `===== FILE:` block, create that exact path under a project
   directory and write the block's content verbatim (do not reformat JSON).
2. `starter/data/*.json` are IDENTICAL copies of the kit-level `data/*.json`;
   both are included so the starter runs standalone after extraction.
3. `starter/package-lock.json` is intentionally omitted — run `npm install`
   to regenerate it.
4. After reconstruction: `cd starter && npm install && npm run dev`,
   then `npm run build` and `node scripts/vocab-check.mjs`, and verify
   against `starter/fixtures/golden-pins.json`.
5. Read `HANDOFF-UI.md` (the first FILE block) top to bottom before coding;
   its Section 7 holds the 10 acceptance criteria.

---

===== FILE: HANDOFF-UI.md =====

````markdown
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
````

---

===== FILE: data/forecasts.json =====

```json
[
 {
  "as_of":"2024-08-17",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"833b144a4e4a06bf6817519fc7fd7cff100807ed15e7930dc7bb1cc418d2dbff",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-17",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.411434920281181e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"2dfa57b6560c8dacc533fd458680f3d1dca917cf1b5735eaf66ca2bf74112374",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.1666666666666667,
  "lambda_home":1.1666666666666667,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3593611725079439,
   "draw":0.2812776549841121,
   "home":0.3593611725079439
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-17",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"c5df9477c67195dc2441b95b0a8c4c102fdba053192404d6800930d10a96f58a",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-17",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.411434920281181e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"2dfa57b6560c8dacc533fd458680f3d1dca917cf1b5735eaf66ca2bf74112374",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.1666666666666667,
  "lambda_home":1.1666666666666667,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3593611725079439,
   "draw":0.2812776549841121,
   "home":0.3593611725079439
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-17",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"a09326c1d89d9a03eaf5028e734804921fb62e4d3fadffac4c8595b2b1094a48",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-17",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.411434920281181e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"2dfa57b6560c8dacc533fd458680f3d1dca917cf1b5735eaf66ca2bf74112374",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":1.1666666666666667,
  "lambda_home":1.1666666666666667,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3593611725079439,
   "draw":0.2812776549841121,
   "home":0.3593611725079439
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-24",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"a3f74e4348c8d8c6fdbcdaa4811b3150c3d9bf1a740f74fd949b8fd4338f6dae",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-24",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.513908966024104e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"44948c6b95282aafed453e9dda4cd8cb2461abbd1afdd07b352875ca5b812fc3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":1.3333333333333333,
  "lambda_home":1.3333333333333333,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3699751702908638,
   "draw":0.26004965941827246,
   "home":0.3699751702908638
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-24",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"c1de5af9722e24820821062d180830db8c4b70768c9de4c8b2d42c57056364b8",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-24",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.513908966024104e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"44948c6b95282aafed453e9dda4cd8cb2461abbd1afdd07b352875ca5b812fc3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.3333333333333333,
  "lambda_home":1.3333333333333333,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3699751702908638,
   "draw":0.26004965941827246,
   "home":0.3699751702908638
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-24",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"410818ed110ce3c00c5f35dfa57360537c6ce9d0a1f4c06a593d3ec704d421b4",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-24",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.513908966024104e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"44948c6b95282aafed453e9dda4cd8cb2461abbd1afdd07b352875ca5b812fc3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.3333333333333333,
  "lambda_home":1.3333333333333333,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3699751702908638,
   "draw":0.26004965941827246,
   "home":0.3699751702908638
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-31",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"f444e20c159fd9572dffe58d0deab5d50c2667ca59e1c3e67426897b4e77fa08",
  "convergence_status":"CONVERGED",
  "date":"2024-08-31",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.8217860664471175e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"0b0b4ebaa0765a1a43dafdaf6d088299deb0eba6a0adec41b1917b9005d69bfd",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.3703031150510972,
  "lambda_home":1.0609183238878162,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.12816022966803042,
   "draw":0.3425523444930482,
   "home":0.5292874258389213
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-31",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"ea4cbb117d198ed0cb165cfc8476b81a2e028f7144224419982ef76b3a61e436",
  "convergence_status":"CONVERGED",
  "date":"2024-08-31",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.693963318616376e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"0b0b4ebaa0765a1a43dafdaf6d088299deb0eba6a0adec41b1917b9005d69bfd",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":1.6867894428749755,
  "lambda_home":0.6142440932948282,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.6343664153403693,
   "draw":0.23410881317059234,
   "home":0.13152477148903832
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-31",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"4b6cf9e227a2ba00ea88730d935b378eb6fb1a4282fd1791ebc8de7cff3ae085",
  "convergence_status":"CONVERGED",
  "date":"2024-08-31",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.098917473134179e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"0b0b4ebaa0765a1a43dafdaf6d088299deb0eba6a0adec41b1917b9005d69bfd",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.603216190298661,
  "lambda_home":1.8508904943633888,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.337616525539674,
   "draw":0.2227786576043388,
   "home":0.4396048168559873
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-07",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"b167fb5845eaa48229d517e44dd9a4cc48fd4bb628d2cd6c988fd94a614ecbec",
  "convergence_status":"CONVERGED",
  "date":"2024-09-07",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.706323147920301e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"cb0842e33791426a8ffca3ef78e149bac860eeacc5c9a3fd28d45daf62c137fa",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.4118215390165645,
  "lambda_home":1.4367055218619005,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.369252624331739,
   "draw":0.2502947025520135,
   "home":0.3804526731162475
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-07",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"b3f2d6024736ddd0234e8bace5d887afa678b9d1d889474e85971022109b6a04",
  "convergence_status":"CONVERGED",
  "date":"2024-09-07",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.727204755885836e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"cb0842e33791426a8ffca3ef78e149bac860eeacc5c9a3fd28d45daf62c137fa",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":1.3262925964713923,
  "lambda_home":0.9487476314199124,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.4535857752572893,
   "draw":0.2789878513317099,
   "home":0.2674263734110008
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-07",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"c83d77c5e6e611406ab2f87df66bb4eec938c552b22e2073c7bbe68747a215e1",
  "convergence_status":"CONVERGED",
  "date":"2024-09-07",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.916418305800363e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"cb0842e33791426a8ffca3ef78e149bac860eeacc5c9a3fd28d45daf62c137fa",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":0.722170731725383,
  "lambda_home":1.4820593885623454,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.18193369375750684,
   "draw":0.26404613269370014,
   "home":0.5540201735487931
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-14",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"1734fcdffa72dfc6e69fe05eb62dd5d2f080a81aa096a580ae85bcb29e80c8b4",
  "convergence_status":"CONVERGED",
  "date":"2024-09-14",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.923490392161334e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"e5357d7fbada33e06b8b85d55e8843481dc4302df4caa9bebe0e5936075411e8",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.1195283945791696,
  "lambda_home":1.8886319722996139,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.22298819063605588,
   "draw":0.22382134518328742,
   "home":0.5531904641806569
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-14",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"ec81f8d93bf6af3dfd92b4cce9630400b9e79488f93ca05d47c63d0849d26113",
  "convergence_status":"CONVERGED",
  "date":"2024-09-14",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.7355903642909425e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"e5357d7fbada33e06b8b85d55e8843481dc4302df4caa9bebe0e5936075411e8",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":0.8667094881874103,
  "lambda_home":0.8678550261701807,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.33149834910368187,
   "draw":0.3363679041495406,
   "home":0.33213374674677765
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-14",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"c5986a91c64ed80a1ca1c2614d3a8953e59f7df8739c7158dabb8f3593d4873b",
  "convergence_status":"CONVERGED",
  "date":"2024-09-14",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.0878687639603868e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"e5357d7fbada33e06b8b85d55e8843481dc4302df4caa9bebe0e5936075411e8",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":1.60929516925125,
  "lambda_home":0.9274991487445767,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.5335976474978089,
   "draw":0.24931585758613573,
   "home":0.21708649491605558
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-21",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"fab4cb095bac99df6404dc567a8d537c7b778fafb98e0e620b5aadae9f8501b3",
  "convergence_status":"CONVERGED",
  "date":"2024-09-21",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.22568410555158e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"5276146a9a21b7206e1d5af951896ec19c64da75afd3eb8fe377dfa1e9e796ea",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":0.649610746878718,
  "lambda_home":0.990291567327154,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.23384550154913997,
   "draw":0.34036431195725614,
   "home":0.42579018649360384
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-21",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"f0fb7f5cf7f4b61ad4b53195fe629f3ba6d44339c98cb2bfedef2b0898bf556f",
  "convergence_status":"CONVERGED",
  "date":"2024-09-21",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.072076052216936e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"5276146a9a21b7206e1d5af951896ec19c64da75afd3eb8fe377dfa1e9e796ea",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.5631559038608636,
  "lambda_home":1.9392615955417358,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3137884718379548,
   "draw":0.21895695878938165,
   "home":0.4672545693726636
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-21",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"93ac70580bb5532eb9000fc5c85e497d00804611611f302cffc9b52be0d24b02",
  "convergence_status":"CONVERGED",
  "date":"2024-09-21",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.495979202736919e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"5276146a9a21b7206e1d5af951896ec19c64da75afd3eb8fe377dfa1e9e796ea",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.2108532452411054,
  "lambda_home":1.2332427217141644,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3577901482177298,
   "draw":0.2736435462973956,
   "home":0.36856630548487457
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-28",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"3b3249b08c4e0b27a0f815632c8c69c34465d8cb6e0bbe59589a714e03b7fb27",
  "convergence_status":"CONVERGED",
  "date":"2024-09-28",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.453487744195741e-10,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"28fc26033f8951dde8782c8ce15fbbc38ef866561d1ae15a30a47e8ad0062610",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.6025716658953583,
  "lambda_home":0.7574900720347882,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.25905208146424114,
   "draw":0.387853412234794,
   "home":0.3530945063009649
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-28",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"b7127428e60e312de090863f9fe82e110407f291f6f19ee57e0e8e6fd15f18b1",
  "convergence_status":"CONVERGED",
  "date":"2024-09-28",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.3900213747273256e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"28fc26033f8951dde8782c8ce15fbbc38ef866561d1ae15a30a47e8ad0062610",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":0.8959773125483517,
  "lambda_home":0.6319811315077909,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3974001275079228,
   "draw":0.3583663025653919,
   "home":0.24423356992668524
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-28",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"97ed73a804dc0822a87d0377f354b26802c9401cb55dd39d7acf216ae3fce558",
  "convergence_status":"CONVERGED",
  "date":"2024-09-28",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":0.00046216069552817984,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"28fc26033f8951dde8782c8ce15fbbc38ef866561d1ae15a30a47e8ad0062610",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":2.6324222909890094,
  "lambda_home":3.0822194234134215,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.342868335511294,
   "draw":0.1682607674838895,
   "home":0.4888708970048166
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-05",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"bd7e9bc720437bb787181687fd915addafe17963673728132a23b8c7659316cd",
  "convergence_status":"CONVERGED",
  "date":"2024-10-05",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.0967163782970033e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"33b2256a310052182fa6ba33355d9f20ae16ddd8b01b5cca58ff15e597f28c14",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.0167256891431709,
  "lambda_home":0.9901290768079278,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.35303876254104993,
   "draw":0.3078331176284175,
   "home":0.33912811983053254
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-05",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"052f2f9f58e5c4f1daa253cd71f30dfb35b9241937196dce56d8caa1ae80255c",
  "convergence_status":"CONVERGED",
  "date":"2024-10-05",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.986982422045983e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"33b2256a310052182fa6ba33355d9f20ae16ddd8b01b5cca58ff15e597f28c14",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.893159563952855,
  "lambda_home":1.5119275543047932,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2225756619269204,
   "draw":0.26001265602078566,
   "home":0.5174116820522938
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-05",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"cf57a1c4a73b565cabadc8381abe00df9299caaf687fc2334a2efa99955f21ae",
  "convergence_status":"CONVERGED",
  "date":"2024-10-05",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.6422332034249365e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"33b2256a310052182fa6ba33355d9f20ae16ddd8b01b5cca58ff15e597f28c14",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":1.579180026822077,
  "lambda_home":1.5460343521340896,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3884631783367584,
   "draw":0.23738627457714837,
   "home":0.37415054708609324
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-12",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"edabc3943d31dfa7713d58b87ea57ba158e092d9412c678bd67eb5b64f81e476",
  "convergence_status":"CONVERGED",
  "date":"2024-10-12",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.9246465582666303e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"46748c1ba265e5d642a4b3f4556904b6db487283999907a95c0cb66dfdc784b3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.3540536666771719,
  "lambda_home":1.243018099960839,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.39421185284012966,
   "draw":0.2636020978642507,
   "home":0.3421860492956196
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-12",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"2f25721c957a3ef4e2bde8df447a0e7befa098fc24ead91e8d64adf6923da8aa",
  "convergence_status":"CONVERGED",
  "date":"2024-10-12",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.3689008989681284e-05,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"46748c1ba265e5d642a4b3f4556904b6db487283999907a95c0cb66dfdc784b3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.569402165851035,
  "lambda_home":2.0973926263235274,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2898933407568657,
   "draw":0.21020049361132565,
   "home":0.49990616563180856
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-12",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"c8b637201faaa93c072d787b1fe46eb9a3b622347db134dcef8ffa30b9e29ca3",
  "convergence_status":"CONVERGED",
  "date":"2024-10-12",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.342279507658532e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"46748c1ba265e5d642a4b3f4556904b6db487283999907a95c0cb66dfdc784b3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.9389587793308788,
  "lambda_home":0.5678547410475994,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.4295604813280317,
   "draw":0.35649429100836244,
   "home":0.21394522766360588
  },
  "season":"2024-25"
 },
 {
  "as_of":"2025-08-09",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"16e1ae265354b90e4447da623dc65c2b38c91af6faf193ac2aa0262166090c97",
  "convergence_status":"CONVERGED",
  "date":"2025-08-09",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.2881075075753543e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"091cb31cfda5a8eb537b3ba64ffbaf8031ec68ac93675e116e430f0c09ea36d8",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.0978843164517536,
  "lambda_home":1.7392526835608624,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.23943803202657676,
   "draw":0.23668039328290005,
   "home":0.5238815746905231
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-09",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"6c370995e44f1cd594679fd067e1599316468a19fb6778f9b4e74d9171423f63",
  "convergence_status":"CONVERGED",
  "date":"2025-08-09",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.4964690314988047e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"091cb31cfda5a8eb537b3ba64ffbaf8031ec68ac93675e116e430f0c09ea36d8",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8525837027516033,
  "lambda_home":0.7465393140917015,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3540026481337185,
   "draw":0.35266320817343655,
   "home":0.2933341436928448
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-09",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"8cf1ff279e00589520c69885a86fc2f348236158f921ad53fd2c7c2fda125d63",
  "convergence_status":"CONVERGED",
  "date":"2025-08-09",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.554428139653567e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"091cb31cfda5a8eb537b3ba64ffbaf8031ec68ac93675e116e430f0c09ea36d8",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.7271284220673708,
  "lambda_home":1.8184211776565777,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.37089734403016367,
   "draw":0.22098834984804794,
   "home":0.40811430612178834
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-16",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"092393254adcadc9e273b434907b4db4a2d71a4f27d12ae7ac1b13e8d22f491a",
  "convergence_status":"CONVERGED",
  "date":"2025-08-16",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.7111062440041707e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"f02fb02abff97ffd6c12f11e9fe09ff76fc1572ea7e9abbf76b8786c2d9a4c6b",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.4217994640461886,
  "lambda_home":1.3050830154739286,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3986655395744571,
   "draw":0.2561968460052621,
   "home":0.34513761442028074
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-16",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"a0c52e81dcb1d201afe4ef21409ca4820d2b4e647aebff782b04b73e7695ef14",
  "convergence_status":"CONVERGED",
  "date":"2025-08-16",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.1974756259091066e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"f02fb02abff97ffd6c12f11e9fe09ff76fc1572ea7e9abbf76b8786c2d9a4c6b",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.2445962800660781,
  "lambda_home":1.2934761078896617,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3546460033290599,
   "draw":0.2675650853990432,
   "home":0.37778891127189684
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-16",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"428acc268ea291043dd7dc7360530020dc7532497350beb03586d1aa1c64c67e",
  "convergence_status":"CONVERGED",
  "date":"2025-08-16",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.035745682084979e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"f02fb02abff97ffd6c12f11e9fe09ff76fc1572ea7e9abbf76b8786c2d9a4c6b",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.0325580078716214,
  "lambda_home":1.1012879568271001,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.33425024591885494,
   "draw":0.2964621349791341,
   "home":0.36928761910201097
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-23",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"d3f7401a5bcabc66517423aec986dc42e33e05297be16ac16541d18d9fc20dbf",
  "convergence_status":"CONVERGED",
  "date":"2025-08-23",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.487536524131144e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"8024227166e065e35ec6126410746ba95abfe2ea3d17f85406866e8ad185e25f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.6182712174277901,
  "lambda_home":1.2225050974053684,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.18770273380375374,
   "draw":0.3033029659311485,
   "home":0.5089943002650977
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-23",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"ea5fa6f2422ac7d066e3af4b3052850e9961203b32da32cef57b64d85062f951",
  "convergence_status":"CONVERGED",
  "date":"2025-08-23",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.7603049512613396e-05,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"8024227166e065e35ec6126410746ba95abfe2ea3d17f85406866e8ad185e25f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.7518774455131965,
  "lambda_home":2.3460435988681416,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2895422358849736,
   "draw":0.19676837459427848,
   "home":0.5136893895207478
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-23",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"f7a27c5b8f9dd81d6b2c6b84e46a0ae7a5e1cf590b33da787d68ce6c970e0bf4",
  "convergence_status":"CONVERGED",
  "date":"2025-08-23",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.505427154047112e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"8024227166e065e35ec6126410746ba95abfe2ea3d17f85406866e8ad185e25f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.9396333183057631,
  "lambda_home":1.3076401854785205,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2681125392057641,
   "draw":0.2813192286892095,
   "home":0.4505682321050264
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-30",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"f800ab0994322cd41977e45aa1e7b097d7807a0d363211c068d2fc79620cc2a5",
  "convergence_status":"CONVERGED",
  "date":"2025-08-30",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.5343409542900588e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"87067a1dd9f0a0f5e23a1fd38e3ca9ee14fbf730f783dd1572bc874d61763e15",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.9341207202133033,
  "lambda_home":1.002479378358208,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3247035384208949,
   "draw":0.3143216231761184,
   "home":0.36097483840298666
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-30",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"80f2ee8167aa9433484003bc4bf4982253385bb16bcb04c7e05005921e16e5a1",
  "convergence_status":"CONVERGED",
  "date":"2025-08-30",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.2485341471801803e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"87067a1dd9f0a0f5e23a1fd38e3ca9ee14fbf730f783dd1572bc874d61763e15",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.195030591781164,
  "lambda_home":1.205508691429186,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.35916836910499805,
   "draw":0.2765808155611892,
   "home":0.36425081533381265
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-30",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"246b6755c67d7523884c0f814f13b6167ff69bb22dee270adeff98093d86a8c2",
  "convergence_status":"CONVERGED",
  "date":"2025-08-30",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.738799868093558e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"87067a1dd9f0a0f5e23a1fd38e3ca9ee14fbf730f783dd1572bc874d61763e15",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.3632216481755208,
  "lambda_home":1.9133790588797552,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2737873370210773,
   "draw":0.22244470578698633,
   "home":0.5037679571919363
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-06",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"de180a43937b41493065c6ea476a0a1c08641d7cb63c3012eb06c457dc87a47b",
  "convergence_status":"CONVERGED",
  "date":"2025-09-06",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.015323591597067e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.3090969884782837,
  "lambda_home":1.9591070907657138,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2549058650155542,
   "draw":0.21934902697360512,
   "home":0.5257451080108406
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-06",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"b75b9930121a1507f03241203a6ec7e807f5ac57aa4e8c69be6ea53f39bfc547",
  "convergence_status":"CONVERGED",
  "date":"2025-09-06",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.0741986239691812e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8504745778063009,
  "lambda_home":1.0642703511510065,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2860457665096216,
   "draw":0.3141774493864862,
   "home":0.3997767841038922
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-06",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"a82e8c6f69aa165936571f11f64355d3be487f9f278e88ff11cc6201c71680ec",
  "convergence_status":"CONVERGED",
  "date":"2025-09-06",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.457246631257462e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.4863537389284454,
  "lambda_home":1.1492776002125977,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.4493991447884946,
   "draw":0.25745593403095113,
   "home":0.29314492118055424
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-13",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"acce96d42ab8ab562c9bc24c39d14b4fedbeb6e3feb1cdd5534708a76b59ee39",
  "convergence_status":"CONVERGED",
  "date":"2025-09-13",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.7334560893119715e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"e7e2cbbf0a04270e3b0597b4037e5622b0449c61e759c39cdacf375ac454facf",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.315833615326821,
  "lambda_home":1.4174201571278444,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3487394138119666,
   "draw":0.2559735525178045,
   "home":0.39528703367022894
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-13",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"723407c5f76101f6d85d92b5a42d9da463a021a8c153d3a7b273986b753533d7",
  "convergence_status":"CONVERGED",
  "date":"2025-09-13",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.779073886102992e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"e7e2cbbf0a04270e3b0597b4037e5622b0449c61e759c39cdacf375ac454facf",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8197845272205212,
  "lambda_home":0.9226784953949482,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.30414248342670186,
   "draw":0.33477626146578515,
   "home":0.3610812551075128
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-13",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"d242f76cdfbaab645af0f8ad6d59a31fb8ffa0f955ce64b327291a66928ffdfb",
  "convergence_status":"CONVERGED",
  "date":"2025-09-13",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.969037808974733e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"e7e2cbbf0a04270e3b0597b4037e5622b0449c61e759c39cdacf375ac454facf",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.9866575851779977,
  "lambda_home":1.31807735956797,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.5297786916880045,
   "draw":0.21740444199232398,
   "home":0.2528168663196715
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-20",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"a789055b46f5ba1819bee11e1f9565c731209e922cd3323f607f51ed93a5fe0f",
  "convergence_status":"CONVERGED",
  "date":"2025-09-20",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.600992538599357e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"29621e2ad994915c6b4c67d2245e944a520b9c24433e0f9457bd9dffa4a4049e",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.9508230596315286,
  "lambda_home":1.432739927572198,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.25012592867026284,
   "draw":0.2676983834961114,
   "home":0.48217568783362597
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-20",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"6eaa5c4d19476c5557f0a233d4ef1b45e7d1193f95807f9529ce0f4db395e3ab",
  "convergence_status":"CONVERGED",
  "date":"2025-09-20",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.424328715555646e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"29621e2ad994915c6b4c67d2245e944a520b9c24433e0f9457bd9dffa4a4049e",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.2596697269262127,
  "lambda_home":1.304586053430135,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.35642542450055675,
   "draw":0.26597724361195796,
   "home":0.3775973318874853
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-20",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"3f147053ac9d0def0b1ba62dbba01060733f4c550e43395e65b9a6997a6745ed",
  "convergence_status":"CONVERGED",
  "date":"2025-09-20",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.593870254256728e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"29621e2ad994915c6b4c67d2245e944a520b9c24433e0f9457bd9dffa4a4049e",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.1520724927000396,
  "lambda_home":1.5177293078973033,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.28838581264792224,
   "draw":0.2548152679497044,
   "home":0.4567989194023733
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-27",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"db74e88531313e4c082ecdbc6be1120780efa98bb2a2a396dcdb3815d2bd9a48",
  "convergence_status":"CONVERGED",
  "date":"2025-09-27",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.407668007302192e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"cc47cacd8c79da9e39c5b98a7642cc52ba4bbc7a76e4989e031e57b3706996f6",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.1621346741375742,
  "lambda_home":1.0642824224421261,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3800995874386447,
   "draw":0.28879090331993224,
   "home":0.3311095092414231
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-27",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"e9019462227eaf632eede4502fb210385a5e499e9aac5d8074ddd29ee4a5e64b",
  "convergence_status":"CONVERGED",
  "date":"2025-09-27",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.5709273104569377e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"cc47cacd8c79da9e39c5b98a7642cc52ba4bbc7a76e4989e031e57b3706996f6",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8125435900391084,
  "lambda_home":1.0370451550795048,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2791974235534825,
   "draw":0.3205311785828085,
   "home":0.4002713978637089
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-27",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"1804773fc9e0bec208f1e2fdb42d89471090aff3a71c0ca1f10445135fd46ef6",
  "convergence_status":"CONVERGED",
  "date":"2025-09-27",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.698101328226016e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"cc47cacd8c79da9e39c5b98a7642cc52ba4bbc7a76e4989e031e57b3706996f6",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.7993262768555487,
  "lambda_home":1.9501861021025948,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.363084489292335,
   "draw":0.21391763144487125,
   "home":0.42299787926279375
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-04",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"39184a51e5d77ca0174286bf89ac2a83e89b21c85151e1ce038e2af39fa703c0",
  "convergence_status":"CONVERGED",
  "date":"2025-10-04",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.6532118298773213e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"2e77ce67e84e915ca48eeeb2de73a482dbc322cd93326c98074dc4086ee4d600",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.0739807889070745,
  "lambda_home":1.6802424900872117,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.24257973989034493,
   "draw":0.2420093993481586,
   "home":0.5154108607614964
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-04",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"b6c1ca05a04a78a181410fc1abaec59a5cc4c5ba6ecb68beed3b91db846c05e1",
  "convergence_status":"CONVERGED",
  "date":"2025-10-04",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.1055337267862342e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"2e77ce67e84e915ca48eeeb2de73a482dbc322cd93326c98074dc4086ee4d600",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.1921347727676188,
  "lambda_home":1.1790134364534202,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3638983815038343,
   "draw":0.2786015203074252,
   "home":0.3575000981887407
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-04",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"991867e2c0f19343e0ffdfb76d9a16247606bd4d801fb0efb3214f8cb461cca1",
  "convergence_status":"CONVERGED",
  "date":"2025-10-04",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.3056657560971416e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"2e77ce67e84e915ca48eeeb2de73a482dbc322cd93326c98074dc4086ee4d600",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.307114459425539,
  "lambda_home":1.239807492863459,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3824413193871901,
   "draw":0.26693375324637986,
   "home":0.3506249273664299
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-11",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"0dfc19bb1049c5fa86fa0e72664e149404f22be329bfcdf0802cfe2566ea612f",
  "convergence_status":"CONVERGED",
  "date":"2025-10-11",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.1528543953809312e-05,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"0b8db4d21edd03b5647e93307049e9b08082bf837b6498a8cba44eaaeb0b3b1f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":2.0656077985709618,
  "lambda_home":1.4354582360219812,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.521276991276099,
   "draw":0.2123228301071329,
   "home":0.2664001786167683
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-11",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"486b377bc560554d1de435aede94ce7c86647162db03d5e5aa6bff6df0b29933",
  "convergence_status":"CONVERGED",
  "date":"2025-10-11",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.816752902035091e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"0b8db4d21edd03b5647e93307049e9b08082bf837b6498a8cba44eaaeb0b3b1f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.3037344959775778,
  "lambda_home":1.3034457692381014,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.36832281172114884,
   "draw":0.26348950126196596,
   "home":0.3681876870168851
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-11",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"684141bc3ea843cd30ee52a50dd475e18f6cc50e9b6935d2803942f3ac8f0c66",
  "convergence_status":"CONVERGED",
  "date":"2025-10-11",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.2830406150359295e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"0b8db4d21edd03b5647e93307049e9b08082bf837b6498a8cba44eaaeb0b3b1f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8128225462981823,
  "lambda_home":0.951283906202788,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2960208366475033,
   "draw":0.33174402962485916,
   "home":0.3722351337276376
  },
  "season":"2025-26"
 }
]
```

---

===== FILE: data/evaluation.json =====

```json
{
 "accounting":{
  "n_clean":30,
  "n_flagged":27,
  "n_predictions":57,
  "n_refusals":3,
  "n_targets":60,
  "refusal_keys":[
   [
    "Obsidian Coast League",
    "2024-25",
    "2024-08-10",
    "Coralgate Athletic",
    "Thistledown Wanderers"
   ],
   [
    "Obsidian Coast League",
    "2024-25",
    "2024-08-10",
    "Quarryhill Zenith",
    "Harbourlight Comets"
   ],
   [
    "Obsidian Coast League",
    "2024-25",
    "2024-08-10",
    "Silverpine Rovers",
    "Emberfield Kestrels"
   ]
  ]
 },
 "note":"Descriptive statistics only: no confidence intervals, no deltas, no verdicts, no comparative claims.",
 "overdispersion":{
  "mean":1.3070175438596492,
  "n":114,
  "variance":0.9671437365343182
 },
 "primary":{
  "baseline":{
   "brier":0.6513262608006456,
   "log_loss":1.0756660244986818,
   "rps":0.2350484286002546
  },
  "calibration":{
   "bins":[
    {
     "mean_p":0.1922355541990161,
     "n":2,
     "realized_frequency":0.5
    },
    {
     "mean_p":0.3068857322030056,
     "n":73,
     "realized_frequency":0.3013698630136986
    },
    {
     "mean_p":0.48085802938550376,
     "n":15,
     "realized_frequency":0.4666666666666667
    },
    {
     "mean_p":null,
     "n":0,
     "realized_frequency":null
    },
    {
     "mean_p":null,
     "n":0,
     "realized_frequency":null
    }
   ],
   "n_matches":30,
   "n_pairs":90
  },
  "draw_deficit":-0.03437540133650058,
  "model":{
   "brier":0.657717020755589,
   "log_loss":1.0893088945036264,
   "rps":0.23748019128548054
  },
  "n_draw_contributions":7,
  "n_matches":30
 },
 "run_digest":"150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f",
 "secondary":{
  "baseline":{
   "brier":0.6659747894436246,
   "log_loss":1.10026212693129,
   "rps":0.2385794979516648
  },
  "calibration":{
   "bins":[
    {
     "mean_p":0.16572509513274955,
     "n":6,
     "realized_frequency":0.6666666666666666
    },
    {
     "mean_p":0.30851337436509413,
     "n":137,
     "realized_frequency":0.32116788321167883
    },
    {
     "mean_p":0.4853685454016753,
     "n":27,
     "realized_frequency":0.3333333333333333
    },
    {
     "mean_p":0.6343664153403693,
     "n":1,
     "realized_frequency":0.0
    },
    {
     "mean_p":null,
     "n":0,
     "realized_frequency":null
    }
   ],
   "n_matches":57,
   "n_pairs":171
  },
  "draw_deficit":-0.025271786352718206,
  "model":{
   "brier":0.7110877726071556,
   "log_loss":1.172910978563622,
   "rps":0.2599049808350038
  },
  "n_draw_contributions":14,
  "n_matches":57
 }
}
```

---

===== FILE: data/provenance.json =====

```json
{
 "api_contract":{
  "base":"http://127.0.0.1:8765",
  "bind":"127.0.0.1 (localhost-only, read-only; no CORS headers)",
  "body_encoding":"byte-deterministic JSON (sort_keys, compact separators, UTF-8)",
  "errors":{
   "integrity_error":500,
   "malformed_path":400,
   "unimplemented_method":501,
   "unknown_fixture":404,
   "unknown_route":404,
   "write_method":405
  },
  "launch":"No CLI is included. create_server(db_path, host=\"127.0.0.1\", port=0) defaults to an ephemeral port; 8765 is a suggested local convention \u2014 bind it in a small launcher.",
  "routes":[
   "GET /health",
   "GET /forecasts/{competition}/{season}/{date}/{home}/{away}"
  ]
 },
 "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
 "evaluation_version":1,
 "fixture_file_sha256s":[
  [
   "season-1.json",
   "f779fc0a952e00ecd904c8019b288c43326635cb5c5a698f2f74870b11d57e39"
  ],
  [
   "season-2.json",
   "5a9da621c678933b0a5f0320a79c8c245783b34bbaf59a73e0fd7d7609d916a9"
  ]
 ],
 "forecast_version":"forecast-poisson-mle-v1",
 "honest_limits":[
  "synthetic fixtures only (Obsidian Coast League, 2 seasons, 60 matches)",
  "evaluated n = 30 primary / 57 secondary",
  "runtime wall-times are load-labelled, not an SLA",
  "'research-ready' = documented, traceable, deterministic, pre-registered \u2014 not validated, accurate, or complete"
 ],
 "model_version":"poisson-mle-v1",
 "record_content_hash":"ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47",
 "replay_seed":20261017,
 "repo_commit":"b8cc13d",
 "run_digest":"150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f",
 "schema_version":2,
 "stage_map":{
  "built":[
   {
    "name":"DATA",
    "path":"app/ingestion/",
    "stage":1
   },
   {
    "name":"VALIDATION",
    "path":"app/validation/",
    "stage":2
   },
   {
    "name":"FEATURE EXTRACTION",
    "path":"app/features/",
    "stage":4
   },
   {
    "name":"STATISTICAL MODELS",
    "path":"app/models/",
    "stage":5
   },
   {
    "name":"FORECAST DISTRIBUTIONS",
    "path":"app/forecasts/",
    "stage":6
   },
   {
    "name":"SCENARIO EXPLORATION",
    "path":"app/scenarios/",
    "stage":7
   },
   {
    "name":"DECISION ANALYSIS",
    "path":"app/decisions/",
    "stage":8
   },
   {
    "name":"OUTCOME EVALUATION",
    "path":"app/backtesting/ + app/evaluation/",
    "stage":9
   }
  ],
  "unbuilt":[
   {
    "documented_as":"G1-G5 in docs/KNOWN-LIMITATIONS.md",
    "name":"PRE-MATCH STATE",
    "path":"app/state/",
    "stage":3
   },
   {
    "documented_as":"G1-G5 in docs/KNOWN-LIMITATIONS.md",
    "name":"MODEL IMPROVEMENT",
    "path":"app/improvement/",
    "stage":10
   }
  ]
 }
}
```

---

===== FILE: fixtures/golden-pins.json =====

```json
{
 "accounting":[
  60,
  57,
  3,
  27,
  30
 ],
 "calibration_total_pairs":{
  "primary":90,
  "secondary":171
 },
 "dominant_bin_share":{
  "primary":0.8111111111111111,
  "secondary":0.8011695906432749
 },
 "draw_deficit":{
  "primary":-0.03437540133650058,
  "secondary":-0.025271786352718206
 },
 "metrics":{
  "primary.baseline":[
   30,
   1.0756660244986818,
   0.6513262608006456,
   0.2350484286002546
  ],
  "primary.model":[
   30,
   1.0893088945036264,
   0.657717020755589,
   0.23748019128548054
  ],
  "secondary.baseline":[
   57,
   1.10026212693129,
   0.6659747894436246,
   0.2385794979516648
  ],
  "secondary.model":[
   57,
   1.172910978563622,
   0.7110877726071556,
   0.2599049808350038
  ]
 },
 "n_draw_contributions":{
  "primary":7,
  "secondary":14
 },
 "record_hash":"ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47",
 "run_digest":"150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f"
}
```

---

===== FILE: starter/README.md =====

````markdown
# Looking Glass UI — starter

A runnable Next.js skeleton for the Sports Looking Glass read-only viewer,
pre-wired with the real data. Your agent extends this; see `../HANDOFF-UI.md`
for the full brief (surfaces, constraints, acceptance criteria).

## Run it

```bash
npm install
npm run dev        # http://localhost:3000
```

## Build + verify

```bash
npm run build
npm run vocab-check   # built output + authored source (must print "clean")
npm run start         # production server, or use npm run dev
```

The starter is a Next.js server app: the four nav surfaces pre-render and the
detail pages render on demand. Pure-static hosting is optional — add
`generateStaticParams` over `allForecasts()` and set `output: "export"` in
`next.config.ts`; then the Mode-B proxy route is impossible (API routes need
the server). The starter does not enable it.

## What is wired

- `/` — forecast browser: 57 forecasts, season/team filters, search, probability
  bars, per-row disclaimer, flagged badges
- `/forecast/{competition}/{season}/{date}/{home}/{away}` — detail: internals,
  integrity hashes, missing-data rendering, full disclaimer
- `/evaluation` — descriptive metrics, grouped 5-bin calibration bars,
  diagnostics (including the derived draw count), accounting with refusal keys
- `/provenance` — full digests, 10-stage map (8/10 built), versions, API
  contract with launch note, honest limits
- `/methodology` — plain-language explainer, disclaimer quoted, honest limits

## Data

`data/forecasts.json` is a static export of the store and shape-identical to
the live API's forecast body. `evaluation.json` and `provenance.json` are UI
projections; the projection fields (`note`, `n_draw_contributions`, and the
stage-map/API additions) are documented in HANDOFF-UI.md §3.2–3.3.

Mode B (live localhost API; suggested port 8765 — the repo's `create_server`
defaults to an ephemeral port) is documented in HANDOFF-UI.md §4. The loader in
`lib/data.ts` is where the data source is swapped; the Mode-B proxy route is a
separate addition.

## Constraints recap (acceptance criteria — see HANDOFF-UI.md §2)

1. Vocabulary guards (`lib/vocab.ts` + `scripts/vocab-check.mjs`) — never render
   claim-language; the two allowlisted negation sites are the disclaimer and
   the honest-limits phrasing. Field-name bans are checked in authored source;
   sanctioned metric identifiers are exempt from the token scan.
2. Disclaimer visible on every forecast view, verbatim from data.
3. Digest provenance surfaced wherever data renders.
4. Descriptive-only presentation: unranked side-by-side numbers, no deltas,
   no confidence intervals, no verdicts.
````

---

===== FILE: starter/package.json =====

```json
{
  "name": "looking-glass-ui",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "vocab-check": "node scripts/vocab-check.mjs"
  },
  "dependencies": {
    "next": "15.5.28",
    "react": "19.1.0",
    "react-dom": "19.1.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "4.1.13",
    "@types/node": "24.5.2",
    "@types/react": "19.1.13",
    "@types/react-dom": "19.1.9",
    "tailwindcss": "4.1.13",
    "typescript": "5.9.3"
  }
}
```

---

===== FILE: starter/tsconfig.json =====

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

---

===== FILE: starter/next.config.ts =====

```typescript
import type { NextConfig } from "next";

// Mode A (static data): default build pre-renders the four nav surfaces;
// detail pages render on demand. Data is imported at build time from
// ./data/*.json (see lib/data.ts).
// Mode B (live localhost API): when/if you add the documented proxy route
// (app/api/forecasts/[...key]/route.ts), nothing here needs to change for
// `next build`; only for `output: "export"`-style pure-static hosting would
// the proxy route be impossible (API routes require the server).
const nextConfig: NextConfig = {};

export default nextConfig;
```

---

===== FILE: starter/postcss.config.mjs =====

```javascript
const config = {
  plugins: ["@tailwindcss/postcss"],
};

export default config;
```

---

===== FILE: starter/next-env.d.ts =====

```typescript
/// <reference types="next" />
/// <reference types="next/image-types/global" />
/// <reference path="./.next/types/routes.d.ts" />

// NOTE: This file should not be edited
// see https://nextjs.org/docs/app/api-reference/config/typescript for more information.
```

---

===== FILE: starter/app/layout.tsx =====

```typescript
import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Sports Looking Glass — viewer",
  description:
    "Read-only viewer over the Sports Looking Glass deterministic football analysis store. Estimates, never promises.",
};

const NAV = [
  { href: "/", label: "Forecasts" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/provenance", label: "Provenance" },
  { href: "/methodology", label: "Methodology" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-5xl px-4 py-3 flex items-center justify-between flex-wrap gap-2">
            <Link href="/" className="font-semibold text-slate-800">
              Sports Looking Glass <span className="text-slate-400 font-normal">· viewer</span>
            </Link>
            <nav className="flex gap-1 text-sm">
              {NAV.map((n) => (
                <Link
                  key={n.href}
                  href={n.href}
                  className="px-3 py-1.5 rounded text-slate-600 hover:bg-slate-100 hover:text-indigo-700"
                >
                  {n.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="border-t border-slate-200 mt-12">
          <div className="mx-auto max-w-5xl px-4 py-4 text-xs text-slate-400">
            Read-only viewer over a deterministic, write-once store. Estimates,
            never promises; this system never places or assists bets.
          </div>
        </footer>
      </body>
    </html>
  );
}
```

---

===== FILE: starter/app/globals.css =====

```css
@import "tailwindcss";

:root {
  --lg-accent: #4f46e5; /* indigo-600 — interactive elements only */
}

html {
  font-feature-settings: "tnum" 1; /* tabular figures everywhere numbers render */
}

body {
  @apply bg-slate-50 text-slate-800 antialiased;
}

/* Hashes and digests: monospace, wrappable */
.hash {
  @apply font-mono text-xs break-all text-slate-500;
}
```

---

===== FILE: starter/app/page.tsx =====

```typescript
"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import ProbabilityBars from "@/components/ProbabilityBars";
import {
  Forecast,
  orderedForecasts,
  pct,
  seasons,
  teams,
} from "@/lib/data";

/**
 * Surface 5.1 — Forecast browser: all 57 stored forecasts, client-side
 * filters only. Flagged forecasts carry a visible badge; the disclaimer
 * travels with every row (§2.2).
 */
export default function ForecastBrowser() {
  const forecasts = useMemo(() => orderedForecasts(), []);
  const allTeams = useMemo(() => teams(), []);
  const allSeasons = useMemo(() => seasons(), []);

  const [season, setSeason] = useState("all");
  const [team, setTeam] = useState("all");
  const [query, setQuery] = useState("");

  const filtered = forecasts.filter((f) => {
    if (season !== "all" && f.season !== season) return false;
    if (team !== "all" && f.home !== team && f.away !== team) return false;
    if (query && !`${f.home} ${f.away}`.toLowerCase().includes(query.toLowerCase()))
      return false;
    return true;
  });

  return (
    <section className="space-y-4">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <h1 className="text-xl font-semibold">Stored forecasts</h1>
        <p className="text-sm text-slate-500 tabular-nums">
          {filtered.length} of {forecasts.length} forecasts
        </p>
      </div>

      <div className="flex gap-3 flex-wrap text-sm">
        <label className="flex items-center gap-1.5">
          <span className="text-slate-500">Season</span>
          <select
            value={season}
            onChange={(e) => setSeason(e.target.value)}
            className="border border-slate-300 rounded px-2 py-1 bg-white"
          >
            <option value="all">all</option>
            {allSeasons.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5">
          <span className="text-slate-500">Team</span>
          <select
            value={team}
            onChange={(e) => setTeam(e.target.value)}
            className="border border-slate-300 rounded px-2 py-1 bg-white max-w-52"
          >
            <option value="all">all</option>
            {allTeams.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-1.5 flex-1 min-w-40">
          <span className="text-slate-500">Search</span>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="team name…"
            className="border border-slate-300 rounded px-2 py-1 bg-white flex-1 min-w-32"
          />
        </label>
      </div>

      <ul className="space-y-2">
        {filtered.map((f) => (
          <Row key={f.content_hash} f={f} />
        ))}
      </ul>
    </section>
  );
}

function Row({ f }: { f: Forecast }) {
  const detailPath = `/forecast/${[
    f.competition,
    f.season,
    f.date,
    f.home,
    f.away,
  ].map(encodeURIComponent).join("/")}`;
  return (
    <li className="bg-white border border-slate-200 rounded p-3">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="min-w-56">
          <Link href={detailPath} className="font-medium text-slate-800 hover:text-indigo-700">
            {f.home} <span className="text-slate-400 font-normal">vs</span> {f.away}
          </Link>
          <div className="text-xs text-slate-500 mt-0.5 tabular-nums">
            {f.date} · {f.season} · as of {f.as_of}
            {f.insufficient_data && (
              <span className="ml-2 inline-block bg-amber-50 text-amber-700 border border-amber-200 rounded px-1.5 text-[10px]">
                insufficient data
              </span>
            )}
          </div>
        </div>
        <div className="flex-1 min-w-64 max-w-md">
          <ProbabilityBars probs={f.outcome_probs} size="sm" />
        </div>
      </div>
      <div className="mt-2">
        <DisclaimerBanner compact text={f.disclaimer} />
      </div>
    </li>
  );
}
```

---

===== FILE: starter/app/evaluation/page.tsx =====

```typescript
import DigestChip from "@/components/DigestChip";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import { Evaluation, Population, evaluation, num, provenance } from "@/lib/data";

/**
 * Surface 5.3 — Evaluation. Descriptive only (§2.4): model and baseline
 * rows are visually identical and unranked; five calibration bins, never
 * merged; n on every number; the overdispersion diagnostic is "a number
 * only: no test, no verdict".
 */
export default function EvaluationPage() {
  const ev: Evaluation = evaluation();
  const prov = provenance();
  const acc = ev.accounting;

  return (
    <section className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-xl font-semibold">Forecast evaluation</h1>
        <p className="text-sm text-slate-600">{ev.note}</p>
        <div className="flex gap-2 flex-wrap">
          <DigestChip label="run digest" hash={ev.run_digest} href="/provenance" />
          <DigestChip label="record hash" hash={prov.record_content_hash} href="/provenance" />
          <span className="inline-flex items-center gap-1.5 bg-white border border-slate-200 rounded px-2 py-1 text-xs text-slate-500">
            EVALUATION_VERSION {prov.evaluation_version}
          </span>
        </div>
      </header>

      <section className="bg-white border border-slate-200 rounded p-4">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
          Accounting — n on every number
        </h2>
        <div className="flex h-4 rounded-sm overflow-hidden w-full max-w-xl">
          <div className="bg-slate-700" style={{ width: `${(acc.n_clean / acc.n_targets) * 100}%` }} />
          <div className="bg-slate-400" style={{ width: `${(acc.n_flagged / acc.n_targets) * 100}%` }} />
          <div className="bg-slate-200" style={{ width: `${(acc.n_refusals / acc.n_targets) * 100}%` }} />
        </div>
        <p className="text-sm text-slate-600 mt-2 tabular-nums">
          {acc.n_targets} targets = {acc.n_clean} clean + {acc.n_flagged} flagged +{" "}
          {acc.n_refusals} refusals · {acc.n_predictions} predictions scored
        </p>
        <details className="mt-2 text-xs text-slate-500">
          <summary className="cursor-pointer">the {acc.n_refusals} refusal keys (excluded from scoring, counted)</summary>
          <ul className="mt-1 space-y-0.5">
            {acc.refusal_keys.map((k, i) => (
              <li key={i} className="tabular-nums">{k.join(" / ")}</li>
            ))}
          </ul>
        </details>
      </section>

      <PopulationTable title="Primary population — clean only" pop={ev.primary} />
      <PopulationTable title="Secondary population — clean + flagged" pop={ev.secondary} />

      <section className="bg-white border border-slate-200 rounded p-4 text-sm space-y-1">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-1">
          Diagnostics
        </h2>
        <p className="text-slate-600">
          draw deficit — realized draw rate minus mean forecast draw probability —
          descriptive: <span className="tabular-nums">{num(ev.primary.draw_deficit)}</span>{" "}
          (primary, n = {ev.primary.n_matches}) ·{" "}
          <span className="tabular-nums">{num(ev.secondary.draw_deficit)}</span> (secondary,{" "}
          n = {ev.secondary.n_matches})
        </p>
        <p className="text-slate-600">
          realized draws counted —{" "}
          <span className="tabular-nums">{ev.primary.n_draw_contributions}</span> (primary) ·{" "}
          <span className="tabular-nums">{ev.secondary.n_draw_contributions}</span>{" "}
          (secondary) — a count, not a metric
        </p>
        <p className="text-slate-600">
          overdispersion — variance-versus-mean of realized team goals — a number
          only: no test, no significance, no verdict: n = {ev.overdispersion.n}, mean ={" "}
          <span className="tabular-nums">{num(ev.overdispersion.mean)}</span>, variance ={" "}
          <span className="tabular-nums">{num(ev.overdispersion.variance)}</span>
        </p>
      </section>

      <DisclaimerBanner />
    </section>
  );
}

function PopulationTable({ title, pop }: { title: string; pop: Population }) {
  const bins = pop.calibration.bins;
  return (
    <section className="bg-white border border-slate-200 rounded p-4 space-y-3">
      <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide">{title}</h2>

      <table className="w-full text-sm tabular-nums">
        <thead>
          <tr className="text-left text-slate-400 text-xs uppercase tracking-wide">
            <th className="py-1 font-normal">side</th>
            <th className="py-1 font-normal">n</th>
            <th className="py-1 font-normal">log loss</th>
            <th className="py-1 font-normal">brier</th>
            <th className="py-1 font-normal">rps</th>
          </tr>
        </thead>
        <tbody>
          <tr className="border-t border-slate-100">
            <td className="py-1.5">model</td>
            <td>{pop.n_matches}</td>
            <td>{num(pop.model.log_loss)}</td>
            <td>{num(pop.model.brier)}</td>
            <td>{num(pop.model.rps)}</td>
          </tr>
          <tr className="border-t border-slate-100">
            <td className="py-1.5">per-fixture baseline</td>
            <td>{pop.n_matches}</td>
            <td>{num(pop.baseline.log_loss)}</td>
            <td>{num(pop.baseline.brier)}</td>
            <td>{num(pop.baseline.rps)}</td>
          </tr>
        </tbody>
      </table>

      <div>
        <p className="text-xs text-slate-400 mb-1">
          pooled calibration — five fixed bins, never merged · {pop.calibration.n_pairs}{" "}
          forecast/outcome pairs · bars: mean forecast probability (dark) / realized
          frequency (light)
        </p>
        <div className="space-y-2">
          {bins.map((b, i) => (
            <div key={i} className="grid grid-cols-[3.5rem_1fr] gap-2 text-xs">
              <span className="text-slate-400 pt-0.5">bin {i}</span>
              {b.n === 0 ? (
                <div className="flex items-center gap-2">
                  <div className="h-6 flex-1 rounded-sm border border-dashed border-slate-200" />
                  <span className="w-40 text-slate-300">empty (n = 0)</span>
                </div>
              ) : (
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="w-14 shrink-0 text-right text-slate-400">mean p</span>
                    <div className="h-2.5 flex-1 bg-slate-100 rounded-sm overflow-hidden">
                      <div
                        className="h-2.5 bg-slate-600"
                        style={{ width: `${Math.min(100, b.mean_p! * 100)}%` }}
                      />
                    </div>
                    <span className="w-16 shrink-0 text-right tabular-nums text-slate-600">
                      {num(b.mean_p!)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-14 shrink-0 text-right text-slate-400">realized</span>
                    <div className="h-2.5 flex-1 bg-slate-100 rounded-sm overflow-hidden">
                      <div
                        className="h-2.5 bg-slate-400"
                        style={{ width: `${Math.min(100, b.realized_frequency! * 100)}%` }}
                      />
                    </div>
                    <span className="w-16 shrink-0 text-right tabular-nums text-slate-600">
                      {num(b.realized_frequency!)}
                    </span>
                  </div>
                  <div className="pl-16 text-slate-400 tabular-nums">n = {b.n}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

---

===== FILE: starter/app/methodology/page.tsx =====

```typescript
import DisclaimerBanner from "@/components/DisclaimerBanner";
import { provenance } from "@/lib/data";

/**
 * Surface 5.5 — Methodology: what the model is, what the numbers are and
 * are not, population definitions, the discipline, honest limits verbatim.
 */
export default function MethodologyPage() {
  const p = provenance();
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold">Methodology</h1>
        <p className="text-sm text-slate-500">
          What this system does, in plain language.
        </p>
      </header>

      <Block title="The model">
        <p>
          For each fixture, the system fits a Poisson model by maximum likelihood
          to the match history available strictly before that fixture&apos;s
          date, then reads off outcome probabilities from the resulting scoreline
          distribution (truncated at 10 goals in this store). The fit is
          chronological: no future information ever reaches a past forecast.
          Where team history is too thin at the cutoff date, the forecast is
          carried with an explicit insufficient-data flag instead of a silent
          guess.
        </p>
      </Block>

      <Block title="What the numbers are — and are not">
        <p>
          Every probability in this viewer is an in-sample analytic estimate from
          the fitted model, stored write-once at forecast time and served
          unchanged since. The stored forecasts were later scored against what
          actually happened, on two populations: <strong>primary</strong> (30
          clean forecasts) and <strong>secondary</strong> (the same plus 27
          flagged ones — 57 total). Three fixtures were refused outright,
          excluded from scoring, and counted. That evaluation is descriptive:
          the numbers say what happened on this small synthetic dataset, and
          nothing more.
        </p>
        <div className="mt-3">
          <DisclaimerBanner />
        </div>
      </Block>

      <Block title="The discipline">
        <ul className="list-disc list-inside space-y-1.5">
          <li>
            <strong>Write-once storage.</strong> Forecasts are content-hashed
            and immutable once stored; the database refuses edits at the schema
            level.
          </li>
          <li>
            <strong>Determinism.</strong> The same inputs re-run to
            byte-identical outputs, across processes and hash seeds; each run
            carries a digest that can be re-derived and compared.
          </li>
          <li>
            <strong>Digest-gated evaluation.</strong> Metrics only compute after
            the run digest matches its pin — numbers and provenance cannot
            drift apart.
          </li>
          <li>
            <strong>Vocabulary guards.</strong> The project scans its own source
            for claim-words; this viewer inherits that posture (see
            HANDOFF-UI.md §2.1 and `lib/vocab.ts`).
          </li>
        </ul>
      </Block>

      <Block title="Honest limits">
        <ul className="list-disc list-inside text-slate-600 space-y-1">
          {p.honest_limits.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </Block>
    </section>
  );
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded p-4">
      <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
        {title}
      </h2>
      <div className="text-sm leading-relaxed text-slate-700 space-y-2">{children}</div>
    </div>
  );
}
```

---

===== FILE: starter/app/provenance/page.tsx =====

```typescript
import DigestChip from "@/components/DigestChip";
import { provenance } from "@/lib/data";

/**
 * Surface 5.4 — Provenance: full digests, fixture hashes, the stage map
 * (unbuilt stages styled as documented gaps, never "coming soon"),
 * versions, API contract, honest-limits verbatim.
 */
export default function ProvenancePage() {
  const p = provenance();
  const stages = [
    ...p.stage_map.built.map((s) => ({ ...s, built: true, documented_as: undefined })),
    ...p.stage_map.unbuilt.map((u) => ({ ...u, built: false })),
  ].sort((a, b) => a.stage - b.stage);
  return (
    <section className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold">Provenance</h1>
        <p className="text-sm text-slate-500">
          Everything on screen traces to the write-once store through these pins.
        </p>
      </header>

      <section className="bg-white border border-slate-200 rounded p-4 space-y-2">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide">Digests</h2>
        <DigestChip label="run digest" hash={p.run_digest} full />
        <DigestChip label="record hash" hash={p.record_content_hash} full />
        <table className="text-xs mt-2">
          <thead>
            <tr className="text-left text-slate-400">
              <th className="pr-4 font-normal">fixture file</th>
              <th className="font-normal">sha256</th>
            </tr>
          </thead>
          <tbody>
            {p.fixture_file_sha256s.map(([name, hash]) => (
              <tr key={name}>
                <td className="pr-4 py-0.5 text-slate-600">{name}</td>
                <td className="hash">{hash}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="bg-white border border-slate-200 rounded p-4">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
          Pipeline stage map — {p.stage_map.built.length} of{" "}
          {p.stage_map.built.length + p.stage_map.unbuilt.length} built
        </h2>
        <ul className="text-sm space-y-1">
          {stages.map((s) => (
            <li
              key={s.stage}
              className={`flex items-start gap-2 ${s.built ? "" : "text-slate-400"}`}
            >
              <span
                className={`mt-1.5 w-2 h-2 rounded-full inline-block ${
                  s.built ? "bg-slate-600" : "border border-slate-400"
                }`}
              />
              <span className="w-5 text-right text-xs text-slate-400 tabular-nums mt-0.5">
                {s.stage}
              </span>{" "}
              <span>
                <span className={s.built ? "text-slate-700" : ""}>{s.name}</span>{" "}
                <code className="hash">{s.path}</code>
                {!s.built && <> — documented gap, {s.documented_as}</>}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-white border border-slate-200 rounded p-4 text-sm">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
          Versions
        </h2>
        <ul className="space-y-1 text-slate-600 tabular-nums">
          <li>repo commit {p.repo_commit}</li>
          <li>model {p.model_version} · forecast {p.forecast_version}</li>
          <li>SCHEMA_VERSION {p.schema_version} · EVALUATION_VERSION {p.evaluation_version}</li>
          <li>simulation replay seed {p.replay_seed}</li>
        </ul>
      </section>

      <section className="bg-white border border-slate-200 rounded p-4 text-sm">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
          Read-only API contract (Mode B)
        </h2>
        <ul className="space-y-1 text-slate-600">
          <li>
            base: <code className="hash">{p.api_contract.base}</code> — {p.api_contract.bind}
          </li>
          <li>{p.api_contract.launch}</li>
          {p.api_contract.routes.map((r) => (
            <li key={r}>
              <code className="hash">{r}</code>
            </li>
          ))}
          <li>
            errors:{" "}
            {[
              ["malformed path", "malformed_path"],
              ["unknown fixture", "unknown_fixture"],
              ["write method", "write_method"],
              ["unknown route", "unknown_route"],
              ["integrity failure", "integrity_error"],
              ["other methods (stdlib default)", "unimplemented_method"],
            ].map(([label, key], i) => (
              <span key={key}>
                {i > 0 ? " · " : ""}
                {label} → {p.api_contract.errors[key]}
              </span>
            ))}
          </li>
          <li>bodies: {p.api_contract.body_encoding}</li>
        </ul>
      </section>

      <section className="bg-slate-100 border border-slate-200 rounded p-4">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
          Honest limits
        </h2>
        <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
          {p.honest_limits.map((l) => (
            <li key={l}>{l}</li>
          ))}
        </ul>
      </section>
    </section>
  );
}
```

---

===== FILE: starter/app/forecast/[competition]/[season]/[date]/[home]/[away]/page.tsx =====

```typescript
import Link from "next/link";
import { notFound } from "next/navigation";
import DisclaimerBanner from "@/components/DisclaimerBanner";
import DigestChip from "@/components/DigestChip";
import ProbabilityBars from "@/components/ProbabilityBars";
import { findByKey, num, pct } from "@/lib/data";

/**
 * Surface 5.2 — Forecast detail: the full stored body, gaps rendered as
 * gaps (missing kickoff stays missing), hashes surfaced (§2.3),
 * disclaimer verbatim (§2.2). Next 15: params is a Promise.
 */
export function generateStaticParams() {
  // Starter note: the browser page pre-renders; details render on demand.
  // Add generateStaticParams over allForecasts() here if you want fully
  // static detail pages (optional; then set output: "export" and the Mode-B
  // proxy route is impossible).
  return [];
}

export default async function ForecastDetail({
  params,
}: {
  params: Promise<{
    competition: string;
    season: string;
    date: string;
    home: string;
    away: string;
  }>;
}) {
  const key = await params;
  const f = findByKey(key.competition, key.season, key.date, key.home, key.away);
  if (!f) notFound();

  return (
    <article className="space-y-6">
      <header className="space-y-1">
        <p className="text-xs text-slate-400 uppercase tracking-wide">Stored forecast</p>
        <h1 className="text-xl font-semibold">
          {f.home} <span className="text-slate-400 font-normal">vs</span> {f.away}
        </h1>
        <p className="text-sm text-slate-500 tabular-nums">
          {f.competition} · {f.season} · {f.date} · as of {f.as_of}
        </p>
      </header>

      {f.insufficient_data && (
        <div className="bg-amber-50 border border-amber-200 rounded p-4 text-sm text-amber-800">
          <p className="font-medium mb-1">Fitted with insufficient history</p>
          <p>
            This forecast was fitted with insufficient history for the listed
            teams; it is carried flagged in the store and scored only in the
            secondary population.
          </p>
          <p className="mt-1 text-xs">{f.insufficient_teams.join(", ")}</p>
        </div>
      )}

      <section className="bg-white border border-slate-200 rounded p-4 space-y-3">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide">
          Outcome probabilities
        </h2>
        <ProbabilityBars probs={f.outcome_probs} size="lg" />
        <p className="text-xs text-slate-400">
          Probabilities sum to {pct(1 - f.dropped_mass, 2)} of mass; the
          remaining {num(f.dropped_mass, 8)} lies beyond the {f.max_goals}-goal
          truncation — a truncation disclosure, not an uncertainty band.
        </p>
      </section>

      <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white border border-slate-200 rounded p-4">
          <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
            Model internals
          </h2>
          <dl className="text-sm space-y-1 tabular-nums">
            <Field label="lambda (home)" value={num(f.lambda_home, 4)} />
            <Field label="lambda (away)" value={num(f.lambda_away, 4)} />
            <Field label="max goals" value={String(f.max_goals)} />
            <Field
              label={`mass beyond ${f.max_goals} goals — truncation`}
              value={num(f.dropped_mass, 8)}
            />
            <Field label="convergence" value={f.convergence_status} />
          </dl>
        </div>
        <div className="bg-white border border-slate-200 rounded p-4">
          <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-2">
            Kickoff
          </h2>
          {f.kickoff.availability === "AVAILABLE" ? (
            <p className="text-sm tabular-nums">{f.kickoff.time}</p>
          ) : (
            <p className="text-sm text-slate-500">kickoff: not recorded</p>
          )}
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded p-4 space-y-2">
        <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wide mb-1">
          Integrity &amp; provenance
        </h2>
        <DigestChip label="content hash" hash={f.content_hash} href="/provenance" />
        <DigestChip label="input digest" hash={f.input_digest} href="/provenance" />
        <p className="text-xs text-slate-500">
          as of {f.as_of} · model {f.model_version} · forecast {f.forecast_version}
        </p>
      </section>

      <DisclaimerBanner text={f.disclaimer} />

      <p className="text-sm">
        <Link href="/evaluation" className="text-indigo-700 hover:underline">
          Evaluation context →
        </Link>
      </p>
    </article>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-slate-800">{value}</dd>
    </div>
  );
}
```

---

===== FILE: starter/components/DisclaimerBanner.tsx =====

```typescript
import { provenance } from "@/lib/data";

/**
 * HANDOFF-UI.md §2.2: the built-in disclaimer string — verbatim from the
 * data, never paraphrased, never buried. `compact` for list rows;
 * full prominence on detail views.
 */
export default function DisclaimerBanner({
  compact = false,
  text,
}: {
  compact?: boolean;
  text?: string;
}) {
  const disclaimer = text ?? provenance().disclaimer;
  return (
    <p
      role="note"
      className={
        compact
          ? "text-[11px] leading-snug text-slate-500 border-l-2 border-slate-300 pl-2"
          : "text-sm leading-relaxed text-slate-600 bg-slate-100 border-l-4 border-slate-400 px-4 py-3 rounded"
      }
    >
      {disclaimer}
    </p>
  );
}
```

---

===== FILE: starter/components/ProbabilityBars.tsx =====

```typescript
import { pct } from "@/lib/data";

/**
 * Outcome probability bars — home / draw / away, labeled percentages,
 * identical visual weight for all three outcomes (never a "favored" style).
 * Colors are neutral slate shades; the accent is never used here, so no
 * outcome reads as endorsed.
 */
export default function ProbabilityBars({
  probs,
  size = "md",
}: {
  probs: { home: number; draw: number; away: number };
  size?: "sm" | "md" | "lg";
}) {
  const heights = {
    sm: "h-1.5 text-[10px]",
    md: "h-2.5 text-xs",
    lg: "h-4 text-sm",
  } as const;
  const rows = [
    { label: "home", value: probs.home, shade: "bg-slate-700" },
    { label: "draw", value: probs.draw, shade: "bg-slate-400" },
    { label: "away", value: probs.away, shade: "bg-slate-300" },
  ];
  return (
    <div className={`space-y-1 ${size === "lg" ? "w-full max-w-md" : "w-full"}`}>
      {rows.map((r) => (
        <div key={r.label} className="flex items-center gap-2">
          <span className={`w-10 shrink-0 text-right text-slate-500 ${heights[size]} leading-none`}>
            {r.label}
          </span>
          <div className="flex-1 bg-slate-200 rounded-sm overflow-hidden">
            <div
              className={`${heights[size]} ${r.shade}`}
              style={{ width: `${Math.min(100, r.value * 100)}%` }}
            />
          </div>
          <span className={`w-14 shrink-0 tabular-nums text-slate-600 ${heights[size]} leading-none`}>
            {pct(r.value)}
          </span>
        </div>
      ))}
    </div>
  );
}
```

---

===== FILE: starter/components/DigestChip.tsx =====

```typescript
"use client";

import { useState } from "react";

/**
 * HANDOFF-UI.md §2.3 digest provenance: every data view surfaces the hash
 * that produced it. Short form in place, full form on the provenance page.
 */
export default function DigestChip({
  label,
  hash,
  href,
  full = false,
}: {
  label: string;
  hash: string;
  href?: string;
  /** Full hash on the provenance page; short form in place elsewhere. */
  full?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const short = hash.length > 14 ? `${hash.slice(0, 10)}…` : hash;
  const display = full ? hash : short;
  return (
    <span
      className={`inline-flex items-center gap-1.5 bg-white border border-slate-200 rounded px-2 py-1 ${
        full ? "max-w-full" : ""
      }`}
    >
      <span className="shrink-0 text-[10px] uppercase tracking-wide text-slate-400">{label}</span>
      {href ? (
        <a
          href={href}
          className={`hash hover:text-indigo-600 ${full ? "min-w-0" : ""}`}
          title={hash}
        >
          {display}
        </a>
      ) : (
        <span className={`hash ${full ? "min-w-0" : ""}`} title={hash}>
          {display}
        </span>
      )}
      <button
        type="button"
        className="shrink-0 text-[10px] text-slate-400 hover:text-indigo-600"
        onClick={() => {
          navigator.clipboard?.writeText(hash);
          setCopied(true);
          setTimeout(() => setCopied(false), 1200);
        }}
      >
        {copied ? "copied" : "copy"}
      </button>
    </span>
  );
}
```

---

===== FILE: starter/lib/data.ts =====

```typescript
/**
 * Typed data access over the kit's static JSON exports.
 *
 * The Forecast shape is IDENTICAL to the live API's forecast_payload()
 * (app/api/serialize.py in the source repo), so switching to Mode B
 * (live localhost API via a proxy route) changes the loader only.
 */
import forecastsJson from "@/data/forecasts.json";
import evaluationJson from "@/data/evaluation.json";
import provenanceJson from "@/data/provenance.json";

export interface Forecast {
  as_of: string;
  away: string;
  competition: string;
  content_hash: string;
  convergence_status: string;
  date: string;
  disclaimer: string;
  dropped_mass: number;
  forecast_version: string;
  home: string;
  input_digest: string;
  insufficient_data: boolean;
  insufficient_teams: string[];
  kickoff: { availability: string; time: string | null };
  lambda_away: number;
  lambda_home: number;
  max_goals: number;
  model_version: string;
  outcome_probs: { away: number; draw: number; home: number };
  season: string;
}

export interface MetricTriple {
  log_loss: number;
  brier: number;
  rps: number;
}

export interface CalibrationBin {
  n: number;
  mean_p: number | null;
  realized_frequency: number | null;
}

export interface Population {
  n_matches: number;
  model: MetricTriple;
  baseline: MetricTriple;
  calibration: { n_matches: number; n_pairs: number; bins: CalibrationBin[] };
  draw_deficit: number;
  n_draw_contributions: number;
}

export interface Evaluation {
  run_digest: string;
  accounting: {
    n_targets: number;
    n_predictions: number;
    n_refusals: number;
    n_flagged: number;
    n_clean: number;
    refusal_keys: string[][];
  };
  primary: Population;
  secondary: Population;
  overdispersion: { n: number; mean: number; variance: number };
  /**
   * UI projection fields, not part of the repo's EvaluationResult:
   * `note` is a fixed descriptive caption; `n_draw_contributions` (on each
   * Population) is the derived count of realized draws.
   */
  note: string;
}

export interface Provenance {
  repo_commit: string;
  run_digest: string;
  record_content_hash: string;
  evaluation_version: number;
  schema_version: number;
  model_version: string;
  forecast_version: string;
  fixture_file_sha256s: string[][];
  replay_seed: number;
  disclaimer: string;
  api_contract: {
    base: string;
    routes: string[];
    errors: Record<string, number>;
    bind: string;
    body_encoding: string;
    launch: string;
  };
  stage_map: {
    built: { stage: number; name: string; path: string }[];
    unbuilt: { stage: number; name: string; path: string; documented_as: string }[];
  };
  honest_limits: string[];
}

export const allForecasts = (): Forecast[] =>
  forecastsJson as unknown as Forecast[];

/** Store read-back order: competition, season, date, home, away. */
export const orderedForecasts = (): Forecast[] =>
  [...allForecasts()].sort((a, b) =>
    (a.competition + a.season + a.date + a.home + a.away).localeCompare(
      b.competition + b.season + b.date + b.home + b.away,
    ),
  );

export const teams = (): string[] =>
  [...new Set(allForecasts().flatMap((f) => [f.home, f.away]))].sort();

export const seasons = (): string[] =>
  [...new Set(allForecasts().map((f) => f.season))].sort();

export const evaluation = (): Evaluation =>
  evaluationJson as unknown as Evaluation;

export const provenance = (): Provenance =>
  provenanceJson as unknown as Provenance;

export const forecastKeyPath = (f: Forecast): string =>
  [f.competition, f.season, f.date, f.home, f.away]
    .map(encodeURIComponent)
    .join("/");

export const findByKey = (
  competition: string,
  season: string,
  date: string,
  home: string,
  away: string,
): Forecast | undefined =>
  allForecasts().find(
    (f) =>
      f.competition === decodeURIComponent(competition) &&
      f.season === decodeURIComponent(season) &&
      f.date === decodeURIComponent(date) &&
      f.home === decodeURIComponent(home) &&
      f.away === decodeURIComponent(away),
  );

export const pct = (p: number, digits = 1): string =>
  `${(p * 100).toFixed(digits)}%`;

export const num = (x: number, digits = 4): string => x.toFixed(digits);
```

---

===== FILE: starter/lib/vocab.ts =====

```typescript
/**
 * UI vocabulary guards — mirror of the source repo's tests/test_vocab_guards.py.
 *
 * These are acceptance criteria (HANDOFF-UI.md §2.1), not style advice:
 * the UI renders descriptive statistics and must never render claim-language.
 *
 * Two sanctioned negation sites are allowlisted (the repo's own pattern:
 * allowlist the negation, never delete the sentence):
 *   1. the built-in disclaimer: "...Not evidence of accuracy."
 *   2. the honest-limits phrasing: "...not validated, accurate, or complete"
 */

export const OUTCOME_COMPARATIVE_TOKENS = [
  "outperform", "outperforms", "outperformed", "outperforming",
  "beat", "beats", "beaten", "beating", "hit", "hits",
  "winner", "champion", "preferred",
] as const;

export const ACCURACY_TRIO = ["validated", "accurate", "beating"] as const;

/** Banned as labels/column names/variable names (field-name scope). */
export const FIELD_BAN_SEGMENTS = [
  "performance", "rank", "ranking", "correct", "correctness", "best", "accuracy",
] as const;

/**
 * Sanctioned metric identifiers — legal ONLY as metric names on the
 * evaluation surface (exactly as the evaluation package uses them).
 * Never in prose, never with claim adjectives.
 */
export const SANCTIONED_METRIC_TOKENS = [
  "log_loss", "logloss", "brier", "rps", "hit_rate", "calibration",
] as const;

export const BANNED_TOKENS: string[] = [
  ...new Set<string>([...OUTCOME_COMPARATIVE_TOKENS, ...ACCURACY_TRIO]),
];

export const ALLOWLISTED_PHRASES = [
  "Not evidence of accuracy",
  "not validated, accurate, or complete",
] as const;

function stripAllowlisted(text: string): string {
  let out = text;
  for (const phrase of ALLOWLISTED_PHRASES) {
    out = out.split(phrase).join(" ");
  }
  return out;
}

/**
 * Sanctioned metric identifiers are legal on the evaluation surface; strip
 * them before the token scan so `hit_rate` does not trip the `hit` ban.
 */
function stripSanctionedMetrics(text: string): string {
  let out = text;
  for (const token of SANCTIONED_METRIC_TOKENS) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "gi");
    out = out.replace(pattern, " ");
  }
  return out;
}

export function findBannedTokens(text: string): string[] {
  const cleaned = stripSanctionedMetrics(stripAllowlisted(text));
  const hits: string[] = [];
  for (const token of BANNED_TOKENS) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "i");
    if (pattern.test(cleaned)) hits.push(token);
  }
  return hits;
}

/**
 * Field-name scope: never use these as column names, labels, or variable
 * names. This is checked over the starter's authored source, not prose.
 */
export function findFieldNameViolations(text: string): string[] {
  const cleaned = stripSanctionedMetrics(stripAllowlisted(text));
  const hits: string[] = [];
  for (const token of FIELD_BAN_SEGMENTS) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "i");
    if (pattern.test(cleaned)) hits.push(token);
  }
  return hits;
}

/** Throws when UI copy violates a guard — use in tests/self-checks. */
export function assertClean(text: string, context = "ui text"): void {
  const hits = findBannedTokens(text);
  if (hits.length > 0) {
    throw new Error(
      `vocabulary guard tripped in ${context}: [${hits.join(", ")}] — ` +
        `see HANDOFF-UI.md §2.1. Render the gap, never the claim.`,
    );
  }
}
```

---

===== FILE: starter/scripts/vocab-check.mjs =====

```javascript
#!/usr/bin/env node
/**
 * Vocabulary guard (HANDOFF-UI.md acceptance criterion 7).
 *
 * Scans what THIS UI authors and renders — prerendered HTML (or a static
 * export in out/) plus our own app/components/lib source — mirroring the
 * source repo's guard, which scans its own app/ tree only. Framework runtime
 * strings (e.g. Next.js cache statuses like "HIT") are third-party code, out
 * of scope. Allowlisted negation sites mirror lib/vocab.ts.
 *
 * Field-name bans are checked over authored source (labels/identifiers), not
 * prose. Sanctioned metric identifiers are stripped before the token scan so
 * `hit_rate` does not trip `hit`.
 *
 * Exit 1 on any hit — wire this into CI.
 */
import { readdirSync, readFileSync, statSync, existsSync } from "node:fs";
import { join } from "node:path";

const BANNED = [
  "outperform", "outperforms", "outperformed", "outperforming",
  "beat", "beats", "beaten", "beating", "hit", "hits",
  "winner", "champion", "preferred", "validated", "accurate",
];
const FIELD_BANNED = [
  "performance", "rank", "ranking", "correct", "correctness", "best", "accuracy",
];
const SANCTIONED = ["log_loss", "logloss", "brier", "rps", "hit_rate", "calibration"];
const ALLOWLISTED = ["Not evidence of accuracy", "not validated, accurate, or complete"];

// Rendered output (prerendered HTML; out/ if a static export is added) + this
// UI's own source. Not node runtime. lib/vocab.ts and this file are the guard's
// single source of truth — the banned words are DEFINED there, so they are
// excluded from their own scan (same pattern as the source repo: defined ONCE
// in the test module).
const HTML_ROOTS = [".next/server/app", "out"];
const SOURCE_ROOTS = ["app", "components", "lib"];
const SOURCE_EXCLUDED = new Set([join("lib", "vocab.ts"), join("scripts", "vocab-check.mjs")]);

function* walk(dir, exts) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    const s = statSync(p);
    if (s.isDirectory()) yield* walk(p, exts);
    else if (exts.some((e) => entry.endsWith(e))) yield p;
  }
}

function clean(text) {
  let out = text;
  for (const phrase of ALLOWLISTED) out = out.split(phrase).join(" ");
  for (const token of SANCTIONED) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "gi");
    out = out.replace(pattern, " ");
  }
  return out;
}

function scan(text, tokens) {
  const hits = [];
  for (const token of tokens) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "i");
    if (pattern.test(text)) hits.push(token);
  }
  return hits;
}

const offenders = [];

for (const root of HTML_ROOTS) {
  for (const file of walk(root, [".html"])) {
    const text = clean(readFileSync(file, "utf8"));
    for (const token of scan(text, BANNED)) offenders.push(`${file}: ${token}`);
  }
}

for (const root of SOURCE_ROOTS) {
  for (const file of walk(root, [".ts", ".tsx", ".mjs", ".css"])) {
    const normalized = file.split("\\").join("/");
    if (SOURCE_EXCLUDED.has(normalized)) continue;
    const text = clean(readFileSync(file, "utf8"));
    for (const token of scan(text, BANNED)) offenders.push(`${file}: ${token}`);
    for (const token of scan(text, FIELD_BANNED)) offenders.push(`${file}: field-name ban: ${token}`);
  }
}

if (offenders.length > 0) {
  console.error("VOCABULARY GUARD TRIPPED:");
  for (const o of offenders) console.error("  " + o);
  console.error("See HANDOFF-UI.md section 2.1 — render the gap, never the claim.");
  process.exit(1);
}
console.log("vocab-check: clean");
```

---

===== FILE: starter/data/forecasts.json =====

```json
[
 {
  "as_of":"2024-08-17",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"833b144a4e4a06bf6817519fc7fd7cff100807ed15e7930dc7bb1cc418d2dbff",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-17",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.411434920281181e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"2dfa57b6560c8dacc533fd458680f3d1dca917cf1b5735eaf66ca2bf74112374",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.1666666666666667,
  "lambda_home":1.1666666666666667,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3593611725079439,
   "draw":0.2812776549841121,
   "home":0.3593611725079439
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-17",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"c5df9477c67195dc2441b95b0a8c4c102fdba053192404d6800930d10a96f58a",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-17",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.411434920281181e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"2dfa57b6560c8dacc533fd458680f3d1dca917cf1b5735eaf66ca2bf74112374",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.1666666666666667,
  "lambda_home":1.1666666666666667,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3593611725079439,
   "draw":0.2812776549841121,
   "home":0.3593611725079439
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-17",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"a09326c1d89d9a03eaf5028e734804921fb62e4d3fadffac4c8595b2b1094a48",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-17",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.411434920281181e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"2dfa57b6560c8dacc533fd458680f3d1dca917cf1b5735eaf66ca2bf74112374",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":1.1666666666666667,
  "lambda_home":1.1666666666666667,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3593611725079439,
   "draw":0.2812776549841121,
   "home":0.3593611725079439
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-24",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"a3f74e4348c8d8c6fdbcdaa4811b3150c3d9bf1a740f74fd949b8fd4338f6dae",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-24",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.513908966024104e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"44948c6b95282aafed453e9dda4cd8cb2461abbd1afdd07b352875ca5b812fc3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":1.3333333333333333,
  "lambda_home":1.3333333333333333,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3699751702908638,
   "draw":0.26004965941827246,
   "home":0.3699751702908638
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-24",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"c1de5af9722e24820821062d180830db8c4b70768c9de4c8b2d42c57056364b8",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-24",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.513908966024104e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"44948c6b95282aafed453e9dda4cd8cb2461abbd1afdd07b352875ca5b812fc3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.3333333333333333,
  "lambda_home":1.3333333333333333,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3699751702908638,
   "draw":0.26004965941827246,
   "home":0.3699751702908638
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-24",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"410818ed110ce3c00c5f35dfa57360537c6ce9d0a1f4c06a593d3ec704d421b4",
  "convergence_status":"SINGULAR_SYSTEM",
  "date":"2024-08-24",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.513908966024104e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"44948c6b95282aafed453e9dda4cd8cb2461abbd1afdd07b352875ca5b812fc3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.3333333333333333,
  "lambda_home":1.3333333333333333,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3699751702908638,
   "draw":0.26004965941827246,
   "home":0.3699751702908638
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-31",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"f444e20c159fd9572dffe58d0deab5d50c2667ca59e1c3e67426897b4e77fa08",
  "convergence_status":"CONVERGED",
  "date":"2024-08-31",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.8217860664471175e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"0b0b4ebaa0765a1a43dafdaf6d088299deb0eba6a0adec41b1917b9005d69bfd",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.3703031150510972,
  "lambda_home":1.0609183238878162,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.12816022966803042,
   "draw":0.3425523444930482,
   "home":0.5292874258389213
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-31",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"ea4cbb117d198ed0cb165cfc8476b81a2e028f7144224419982ef76b3a61e436",
  "convergence_status":"CONVERGED",
  "date":"2024-08-31",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.693963318616376e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"0b0b4ebaa0765a1a43dafdaf6d088299deb0eba6a0adec41b1917b9005d69bfd",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":1.6867894428749755,
  "lambda_home":0.6142440932948282,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.6343664153403693,
   "draw":0.23410881317059234,
   "home":0.13152477148903832
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-08-31",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"4b6cf9e227a2ba00ea88730d935b378eb6fb1a4282fd1791ebc8de7cff3ae085",
  "convergence_status":"CONVERGED",
  "date":"2024-08-31",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.098917473134179e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"0b0b4ebaa0765a1a43dafdaf6d088299deb0eba6a0adec41b1917b9005d69bfd",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.603216190298661,
  "lambda_home":1.8508904943633888,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.337616525539674,
   "draw":0.2227786576043388,
   "home":0.4396048168559873
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-07",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"b167fb5845eaa48229d517e44dd9a4cc48fd4bb628d2cd6c988fd94a614ecbec",
  "convergence_status":"CONVERGED",
  "date":"2024-09-07",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.706323147920301e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"cb0842e33791426a8ffca3ef78e149bac860eeacc5c9a3fd28d45daf62c137fa",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.4118215390165645,
  "lambda_home":1.4367055218619005,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.369252624331739,
   "draw":0.2502947025520135,
   "home":0.3804526731162475
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-07",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"b3f2d6024736ddd0234e8bace5d887afa678b9d1d889474e85971022109b6a04",
  "convergence_status":"CONVERGED",
  "date":"2024-09-07",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.727204755885836e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"cb0842e33791426a8ffca3ef78e149bac860eeacc5c9a3fd28d45daf62c137fa",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":1.3262925964713923,
  "lambda_home":0.9487476314199124,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.4535857752572893,
   "draw":0.2789878513317099,
   "home":0.2674263734110008
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-07",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"c83d77c5e6e611406ab2f87df66bb4eec938c552b22e2073c7bbe68747a215e1",
  "convergence_status":"CONVERGED",
  "date":"2024-09-07",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.916418305800363e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"cb0842e33791426a8ffca3ef78e149bac860eeacc5c9a3fd28d45daf62c137fa",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":0.722170731725383,
  "lambda_home":1.4820593885623454,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.18193369375750684,
   "draw":0.26404613269370014,
   "home":0.5540201735487931
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-14",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"1734fcdffa72dfc6e69fe05eb62dd5d2f080a81aa096a580ae85bcb29e80c8b4",
  "convergence_status":"CONVERGED",
  "date":"2024-09-14",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.923490392161334e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"e5357d7fbada33e06b8b85d55e8843481dc4302df4caa9bebe0e5936075411e8",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.1195283945791696,
  "lambda_home":1.8886319722996139,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.22298819063605588,
   "draw":0.22382134518328742,
   "home":0.5531904641806569
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-14",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"ec81f8d93bf6af3dfd92b4cce9630400b9e79488f93ca05d47c63d0849d26113",
  "convergence_status":"CONVERGED",
  "date":"2024-09-14",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.7355903642909425e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"e5357d7fbada33e06b8b85d55e8843481dc4302df4caa9bebe0e5936075411e8",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":0.8667094881874103,
  "lambda_home":0.8678550261701807,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.33149834910368187,
   "draw":0.3363679041495406,
   "home":0.33213374674677765
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-14",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"c5986a91c64ed80a1ca1c2614d3a8953e59f7df8739c7158dabb8f3593d4873b",
  "convergence_status":"CONVERGED",
  "date":"2024-09-14",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.0878687639603868e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"e5357d7fbada33e06b8b85d55e8843481dc4302df4caa9bebe0e5936075411e8",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":1.60929516925125,
  "lambda_home":0.9274991487445767,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.5335976474978089,
   "draw":0.24931585758613573,
   "home":0.21708649491605558
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-21",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"fab4cb095bac99df6404dc567a8d537c7b778fafb98e0e620b5aadae9f8501b3",
  "convergence_status":"CONVERGED",
  "date":"2024-09-21",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.22568410555158e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"5276146a9a21b7206e1d5af951896ec19c64da75afd3eb8fe377dfa1e9e796ea",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":0.649610746878718,
  "lambda_home":0.990291567327154,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.23384550154913997,
   "draw":0.34036431195725614,
   "home":0.42579018649360384
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-21",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"f0fb7f5cf7f4b61ad4b53195fe629f3ba6d44339c98cb2bfedef2b0898bf556f",
  "convergence_status":"CONVERGED",
  "date":"2024-09-21",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.072076052216936e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"5276146a9a21b7206e1d5af951896ec19c64da75afd3eb8fe377dfa1e9e796ea",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.5631559038608636,
  "lambda_home":1.9392615955417358,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3137884718379548,
   "draw":0.21895695878938165,
   "home":0.4672545693726636
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-21",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"93ac70580bb5532eb9000fc5c85e497d00804611611f302cffc9b52be0d24b02",
  "convergence_status":"CONVERGED",
  "date":"2024-09-21",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.495979202736919e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"5276146a9a21b7206e1d5af951896ec19c64da75afd3eb8fe377dfa1e9e796ea",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.2108532452411054,
  "lambda_home":1.2332427217141644,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3577901482177298,
   "draw":0.2736435462973956,
   "home":0.36856630548487457
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-28",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"3b3249b08c4e0b27a0f815632c8c69c34465d8cb6e0bbe59589a714e03b7fb27",
  "convergence_status":"CONVERGED",
  "date":"2024-09-28",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.453487744195741e-10,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"28fc26033f8951dde8782c8ce15fbbc38ef866561d1ae15a30a47e8ad0062610",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.6025716658953583,
  "lambda_home":0.7574900720347882,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.25905208146424114,
   "draw":0.387853412234794,
   "home":0.3530945063009649
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-28",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"b7127428e60e312de090863f9fe82e110407f291f6f19ee57e0e8e6fd15f18b1",
  "convergence_status":"CONVERGED",
  "date":"2024-09-28",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.3900213747273256e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"28fc26033f8951dde8782c8ce15fbbc38ef866561d1ae15a30a47e8ad0062610",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":0.8959773125483517,
  "lambda_home":0.6319811315077909,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3974001275079228,
   "draw":0.3583663025653919,
   "home":0.24423356992668524
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-09-28",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"97ed73a804dc0822a87d0377f354b26802c9401cb55dd39d7acf216ae3fce558",
  "convergence_status":"CONVERGED",
  "date":"2024-09-28",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":0.00046216069552817984,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"28fc26033f8951dde8782c8ce15fbbc38ef866561d1ae15a30a47e8ad0062610",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":2.6324222909890094,
  "lambda_home":3.0822194234134215,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.342868335511294,
   "draw":0.1682607674838895,
   "home":0.4888708970048166
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-05",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"bd7e9bc720437bb787181687fd915addafe17963673728132a23b8c7659316cd",
  "convergence_status":"CONVERGED",
  "date":"2024-10-05",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.0967163782970033e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"33b2256a310052182fa6ba33355d9f20ae16ddd8b01b5cca58ff15e597f28c14",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.0167256891431709,
  "lambda_home":0.9901290768079278,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.35303876254104993,
   "draw":0.3078331176284175,
   "home":0.33912811983053254
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-05",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"052f2f9f58e5c4f1daa253cd71f30dfb35b9241937196dce56d8caa1ae80255c",
  "convergence_status":"CONVERGED",
  "date":"2024-10-05",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.986982422045983e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"33b2256a310052182fa6ba33355d9f20ae16ddd8b01b5cca58ff15e597f28c14",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.893159563952855,
  "lambda_home":1.5119275543047932,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2225756619269204,
   "draw":0.26001265602078566,
   "home":0.5174116820522938
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-05",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"cf57a1c4a73b565cabadc8381abe00df9299caaf687fc2334a2efa99955f21ae",
  "convergence_status":"CONVERGED",
  "date":"2024-10-05",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.6422332034249365e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"33b2256a310052182fa6ba33355d9f20ae16ddd8b01b5cca58ff15e597f28c14",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"17:30"
  },
  "lambda_away":1.579180026822077,
  "lambda_home":1.5460343521340896,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3884631783367584,
   "draw":0.23738627457714837,
   "home":0.37415054708609324
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-12",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"edabc3943d31dfa7713d58b87ea57ba158e092d9412c678bd67eb5b64f81e476",
  "convergence_status":"CONVERGED",
  "date":"2024-10-12",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.9246465582666303e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"46748c1ba265e5d642a4b3f4556904b6db487283999907a95c0cb66dfdc784b3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"20:00"
  },
  "lambda_away":1.3540536666771719,
  "lambda_home":1.243018099960839,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.39421185284012966,
   "draw":0.2636020978642507,
   "home":0.3421860492956196
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-12",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"2f25721c957a3ef4e2bde8df447a0e7befa098fc24ead91e8d64adf6923da8aa",
  "convergence_status":"CONVERGED",
  "date":"2024-10-12",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.3689008989681284e-05,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"46748c1ba265e5d642a4b3f4556904b6db487283999907a95c0cb66dfdc784b3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"12:30"
  },
  "lambda_away":1.569402165851035,
  "lambda_home":2.0973926263235274,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2898933407568657,
   "draw":0.21020049361132565,
   "home":0.49990616563180856
  },
  "season":"2024-25"
 },
 {
  "as_of":"2024-10-12",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"c8b637201faaa93c072d787b1fe46eb9a3b622347db134dcef8ffa30b9e29ca3",
  "convergence_status":"CONVERGED",
  "date":"2024-10-12",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.342279507658532e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"46748c1ba265e5d642a4b3f4556904b6db487283999907a95c0cb66dfdc784b3",
  "insufficient_data":true,
  "insufficient_teams":[
   "Coralgate Athletic",
   "Emberfield Kestrels",
   "Harbourlight Comets",
   "Quarryhill Zenith",
   "Silverpine Rovers",
   "Thistledown Wanderers"
  ],
  "kickoff":{
   "availability":"AVAILABLE",
   "time":"15:00"
  },
  "lambda_away":0.9389587793308788,
  "lambda_home":0.5678547410475994,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.4295604813280317,
   "draw":0.35649429100836244,
   "home":0.21394522766360588
  },
  "season":"2024-25"
 },
 {
  "as_of":"2025-08-09",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"16e1ae265354b90e4447da623dc65c2b38c91af6faf193ac2aa0262166090c97",
  "convergence_status":"CONVERGED",
  "date":"2025-08-09",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.2881075075753543e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"091cb31cfda5a8eb537b3ba64ffbaf8031ec68ac93675e116e430f0c09ea36d8",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.0978843164517536,
  "lambda_home":1.7392526835608624,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.23943803202657676,
   "draw":0.23668039328290005,
   "home":0.5238815746905231
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-09",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"6c370995e44f1cd594679fd067e1599316468a19fb6778f9b4e74d9171423f63",
  "convergence_status":"CONVERGED",
  "date":"2025-08-09",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.4964690314988047e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"091cb31cfda5a8eb537b3ba64ffbaf8031ec68ac93675e116e430f0c09ea36d8",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8525837027516033,
  "lambda_home":0.7465393140917015,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3540026481337185,
   "draw":0.35266320817343655,
   "home":0.2933341436928448
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-09",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"8cf1ff279e00589520c69885a86fc2f348236158f921ad53fd2c7c2fda125d63",
  "convergence_status":"CONVERGED",
  "date":"2025-08-09",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.554428139653567e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"091cb31cfda5a8eb537b3ba64ffbaf8031ec68ac93675e116e430f0c09ea36d8",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.7271284220673708,
  "lambda_home":1.8184211776565777,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.37089734403016367,
   "draw":0.22098834984804794,
   "home":0.40811430612178834
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-16",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"092393254adcadc9e273b434907b4db4a2d71a4f27d12ae7ac1b13e8d22f491a",
  "convergence_status":"CONVERGED",
  "date":"2025-08-16",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.7111062440041707e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"f02fb02abff97ffd6c12f11e9fe09ff76fc1572ea7e9abbf76b8786c2d9a4c6b",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.4217994640461886,
  "lambda_home":1.3050830154739286,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3986655395744571,
   "draw":0.2561968460052621,
   "home":0.34513761442028074
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-16",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"a0c52e81dcb1d201afe4ef21409ca4820d2b4e647aebff782b04b73e7695ef14",
  "convergence_status":"CONVERGED",
  "date":"2025-08-16",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.1974756259091066e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"f02fb02abff97ffd6c12f11e9fe09ff76fc1572ea7e9abbf76b8786c2d9a4c6b",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.2445962800660781,
  "lambda_home":1.2934761078896617,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3546460033290599,
   "draw":0.2675650853990432,
   "home":0.37778891127189684
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-16",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"428acc268ea291043dd7dc7360530020dc7532497350beb03586d1aa1c64c67e",
  "convergence_status":"CONVERGED",
  "date":"2025-08-16",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.035745682084979e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"f02fb02abff97ffd6c12f11e9fe09ff76fc1572ea7e9abbf76b8786c2d9a4c6b",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.0325580078716214,
  "lambda_home":1.1012879568271001,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.33425024591885494,
   "draw":0.2964621349791341,
   "home":0.36928761910201097
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-23",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"d3f7401a5bcabc66517423aec986dc42e33e05297be16ac16541d18d9fc20dbf",
  "convergence_status":"CONVERGED",
  "date":"2025-08-23",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.487536524131144e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"8024227166e065e35ec6126410746ba95abfe2ea3d17f85406866e8ad185e25f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.6182712174277901,
  "lambda_home":1.2225050974053684,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.18770273380375374,
   "draw":0.3033029659311485,
   "home":0.5089943002650977
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-23",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"ea5fa6f2422ac7d066e3af4b3052850e9961203b32da32cef57b64d85062f951",
  "convergence_status":"CONVERGED",
  "date":"2025-08-23",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.7603049512613396e-05,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"8024227166e065e35ec6126410746ba95abfe2ea3d17f85406866e8ad185e25f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.7518774455131965,
  "lambda_home":2.3460435988681416,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2895422358849736,
   "draw":0.19676837459427848,
   "home":0.5136893895207478
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-23",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"f7a27c5b8f9dd81d6b2c6b84e46a0ae7a5e1cf590b33da787d68ce6c970e0bf4",
  "convergence_status":"CONVERGED",
  "date":"2025-08-23",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.505427154047112e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"8024227166e065e35ec6126410746ba95abfe2ea3d17f85406866e8ad185e25f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.9396333183057631,
  "lambda_home":1.3076401854785205,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2681125392057641,
   "draw":0.2813192286892095,
   "home":0.4505682321050264
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-30",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"f800ab0994322cd41977e45aa1e7b097d7807a0d363211c068d2fc79620cc2a5",
  "convergence_status":"CONVERGED",
  "date":"2025-08-30",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.5343409542900588e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"87067a1dd9f0a0f5e23a1fd38e3ca9ee14fbf730f783dd1572bc874d61763e15",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.9341207202133033,
  "lambda_home":1.002479378358208,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3247035384208949,
   "draw":0.3143216231761184,
   "home":0.36097483840298666
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-30",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"80f2ee8167aa9433484003bc4bf4982253385bb16bcb04c7e05005921e16e5a1",
  "convergence_status":"CONVERGED",
  "date":"2025-08-30",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.2485341471801803e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"87067a1dd9f0a0f5e23a1fd38e3ca9ee14fbf730f783dd1572bc874d61763e15",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.195030591781164,
  "lambda_home":1.205508691429186,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.35916836910499805,
   "draw":0.2765808155611892,
   "home":0.36425081533381265
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-08-30",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"246b6755c67d7523884c0f814f13b6167ff69bb22dee270adeff98093d86a8c2",
  "convergence_status":"CONVERGED",
  "date":"2025-08-30",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.738799868093558e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"87067a1dd9f0a0f5e23a1fd38e3ca9ee14fbf730f783dd1572bc874d61763e15",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.3632216481755208,
  "lambda_home":1.9133790588797552,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2737873370210773,
   "draw":0.22244470578698633,
   "home":0.5037679571919363
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-06",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"de180a43937b41493065c6ea476a0a1c08641d7cb63c3012eb06c457dc87a47b",
  "convergence_status":"CONVERGED",
  "date":"2025-09-06",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.015323591597067e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.3090969884782837,
  "lambda_home":1.9591070907657138,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2549058650155542,
   "draw":0.21934902697360512,
   "home":0.5257451080108406
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-06",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"b75b9930121a1507f03241203a6ec7e807f5ac57aa4e8c69be6ea53f39bfc547",
  "convergence_status":"CONVERGED",
  "date":"2025-09-06",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.0741986239691812e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8504745778063009,
  "lambda_home":1.0642703511510065,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2860457665096216,
   "draw":0.3141774493864862,
   "home":0.3997767841038922
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-06",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"a82e8c6f69aa165936571f11f64355d3be487f9f278e88ff11cc6201c71680ec",
  "convergence_status":"CONVERGED",
  "date":"2025-09-06",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.457246631257462e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"b5f63c333de1a50da25e8c578c80b559289895e753e79c2f2c608981e35fdc78",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.4863537389284454,
  "lambda_home":1.1492776002125977,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.4493991447884946,
   "draw":0.25745593403095113,
   "home":0.29314492118055424
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-13",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"acce96d42ab8ab562c9bc24c39d14b4fedbeb6e3feb1cdd5534708a76b59ee39",
  "convergence_status":"CONVERGED",
  "date":"2025-09-13",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":4.7334560893119715e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"e7e2cbbf0a04270e3b0597b4037e5622b0449c61e759c39cdacf375ac454facf",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.315833615326821,
  "lambda_home":1.4174201571278444,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3487394138119666,
   "draw":0.2559735525178045,
   "home":0.39528703367022894
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-13",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"723407c5f76101f6d85d92b5a42d9da463a021a8c153d3a7b273986b753533d7",
  "convergence_status":"CONVERGED",
  "date":"2025-09-13",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":5.779073886102992e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"e7e2cbbf0a04270e3b0597b4037e5622b0449c61e759c39cdacf375ac454facf",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8197845272205212,
  "lambda_home":0.9226784953949482,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.30414248342670186,
   "draw":0.33477626146578515,
   "home":0.3610812551075128
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-13",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"d242f76cdfbaab645af0f8ad6d59a31fb8ffa0f955ce64b327291a66928ffdfb",
  "convergence_status":"CONVERGED",
  "date":"2025-09-13",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.969037808974733e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"e7e2cbbf0a04270e3b0597b4037e5622b0449c61e759c39cdacf375ac454facf",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.9866575851779977,
  "lambda_home":1.31807735956797,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.5297786916880045,
   "draw":0.21740444199232398,
   "home":0.2528168663196715
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-20",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"a789055b46f5ba1819bee11e1f9565c731209e922cd3323f607f51ed93a5fe0f",
  "convergence_status":"CONVERGED",
  "date":"2025-09-20",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":3.600992538599357e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"29621e2ad994915c6b4c67d2245e944a520b9c24433e0f9457bd9dffa4a4049e",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.9508230596315286,
  "lambda_home":1.432739927572198,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.25012592867026284,
   "draw":0.2676983834961114,
   "home":0.48217568783362597
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-20",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"6eaa5c4d19476c5557f0a233d4ef1b45e7d1193f95807f9529ce0f4db395e3ab",
  "convergence_status":"CONVERGED",
  "date":"2025-09-20",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.424328715555646e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"29621e2ad994915c6b4c67d2245e944a520b9c24433e0f9457bd9dffa4a4049e",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.2596697269262127,
  "lambda_home":1.304586053430135,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.35642542450055675,
   "draw":0.26597724361195796,
   "home":0.3775973318874853
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-20",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"3f147053ac9d0def0b1ba62dbba01060733f4c550e43395e65b9a6997a6745ed",
  "convergence_status":"CONVERGED",
  "date":"2025-09-20",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.593870254256728e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"29621e2ad994915c6b4c67d2245e944a520b9c24433e0f9457bd9dffa4a4049e",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.1520724927000396,
  "lambda_home":1.5177293078973033,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.28838581264792224,
   "draw":0.2548152679497044,
   "home":0.4567989194023733
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-27",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"db74e88531313e4c082ecdbc6be1120780efa98bb2a2a396dcdb3815d2bd9a48",
  "convergence_status":"CONVERGED",
  "date":"2025-09-27",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":6.407668007302192e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"cc47cacd8c79da9e39c5b98a7642cc52ba4bbc7a76e4989e031e57b3706996f6",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.1621346741375742,
  "lambda_home":1.0642824224421261,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3800995874386447,
   "draw":0.28879090331993224,
   "home":0.3311095092414231
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-27",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"e9019462227eaf632eede4502fb210385a5e499e9aac5d8074ddd29ee4a5e64b",
  "convergence_status":"CONVERGED",
  "date":"2025-09-27",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.5709273104569377e-08,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Silverpine Rovers",
  "input_digest":"cc47cacd8c79da9e39c5b98a7642cc52ba4bbc7a76e4989e031e57b3706996f6",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8125435900391084,
  "lambda_home":1.0370451550795048,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2791974235534825,
   "draw":0.3205311785828085,
   "home":0.4002713978637089
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-09-27",
  "away":"Emberfield Kestrels",
  "competition":"Obsidian Coast League",
  "content_hash":"1804773fc9e0bec208f1e2fdb42d89471090aff3a71c0ca1f10445135fd46ef6",
  "convergence_status":"CONVERGED",
  "date":"2025-09-27",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":9.698101328226016e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"cc47cacd8c79da9e39c5b98a7642cc52ba4bbc7a76e4989e031e57b3706996f6",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.7993262768555487,
  "lambda_home":1.9501861021025948,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.363084489292335,
   "draw":0.21391763144487125,
   "home":0.42299787926279375
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-04",
  "away":"Harbourlight Comets",
  "competition":"Obsidian Coast League",
  "content_hash":"39184a51e5d77ca0174286bf89ac2a83e89b21c85151e1ce038e2af39fa703c0",
  "convergence_status":"CONVERGED",
  "date":"2025-10-04",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.6532118298773213e-06,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Coralgate Athletic",
  "input_digest":"2e77ce67e84e915ca48eeeb2de73a482dbc322cd93326c98074dc4086ee4d600",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.0739807889070745,
  "lambda_home":1.6802424900872117,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.24257973989034493,
   "draw":0.2420093993481586,
   "home":0.5154108607614964
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-04",
  "away":"Quarryhill Zenith",
  "competition":"Obsidian Coast League",
  "content_hash":"b6c1ca05a04a78a181410fc1abaec59a5cc4c5ba6ecb68beed3b91db846c05e1",
  "convergence_status":"CONVERGED",
  "date":"2025-10-04",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.1055337267862342e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"2e77ce67e84e915ca48eeeb2de73a482dbc322cd93326c98074dc4086ee4d600",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.1921347727676188,
  "lambda_home":1.1790134364534202,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3638983815038343,
   "draw":0.2786015203074252,
   "home":0.3575000981887407
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-04",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"991867e2c0f19343e0ffdfb76d9a16247606bd4d801fb0efb3214f8cb461cca1",
  "convergence_status":"CONVERGED",
  "date":"2025-10-04",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.3056657560971416e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Thistledown Wanderers",
  "input_digest":"2e77ce67e84e915ca48eeeb2de73a482dbc322cd93326c98074dc4086ee4d600",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.307114459425539,
  "lambda_home":1.239807492863459,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.3824413193871901,
   "draw":0.26693375324637986,
   "home":0.3506249273664299
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-11",
  "away":"Coralgate Athletic",
  "competition":"Obsidian Coast League",
  "content_hash":"0dfc19bb1049c5fa86fa0e72664e149404f22be329bfcdf0802cfe2566ea612f",
  "convergence_status":"CONVERGED",
  "date":"2025-10-11",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":1.1528543953809312e-05,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Emberfield Kestrels",
  "input_digest":"0b8db4d21edd03b5647e93307049e9b08082bf837b6498a8cba44eaaeb0b3b1f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":2.0656077985709618,
  "lambda_home":1.4354582360219812,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.521276991276099,
   "draw":0.2123228301071329,
   "home":0.2664001786167683
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-11",
  "away":"Thistledown Wanderers",
  "competition":"Obsidian Coast League",
  "content_hash":"486b377bc560554d1de435aede94ce7c86647162db03d5e5aa6bff6df0b29933",
  "convergence_status":"CONVERGED",
  "date":"2025-10-11",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":2.816752902035091e-07,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Harbourlight Comets",
  "input_digest":"0b8db4d21edd03b5647e93307049e9b08082bf837b6498a8cba44eaaeb0b3b1f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":1.3037344959775778,
  "lambda_home":1.3034457692381014,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.36832281172114884,
   "draw":0.26348950126196596,
   "home":0.3681876870168851
  },
  "season":"2025-26"
 },
 {
  "as_of":"2025-10-11",
  "away":"Silverpine Rovers",
  "competition":"Obsidian Coast League",
  "content_hash":"684141bc3ea843cd30ee52a50dd475e18f6cc50e9b6935d2803942f3ac8f0c66",
  "convergence_status":"CONVERGED",
  "date":"2025-10-11",
  "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
  "dropped_mass":7.2830406150359295e-09,
  "forecast_version":"forecast-poisson-mle-v1",
  "home":"Quarryhill Zenith",
  "input_digest":"0b8db4d21edd03b5647e93307049e9b08082bf837b6498a8cba44eaaeb0b3b1f",
  "insufficient_data":false,
  "insufficient_teams":[],
  "kickoff":{
   "availability":"MISSING",
   "time":null
  },
  "lambda_away":0.8128225462981823,
  "lambda_home":0.951283906202788,
  "max_goals":10,
  "model_version":"poisson-mle-v1",
  "outcome_probs":{
   "away":0.2960208366475033,
   "draw":0.33174402962485916,
   "home":0.3722351337276376
  },
  "season":"2025-26"
 }
]
```

---

===== FILE: starter/data/evaluation.json =====

```json
{
 "accounting":{
  "n_clean":30,
  "n_flagged":27,
  "n_predictions":57,
  "n_refusals":3,
  "n_targets":60,
  "refusal_keys":[
   [
    "Obsidian Coast League",
    "2024-25",
    "2024-08-10",
    "Coralgate Athletic",
    "Thistledown Wanderers"
   ],
   [
    "Obsidian Coast League",
    "2024-25",
    "2024-08-10",
    "Quarryhill Zenith",
    "Harbourlight Comets"
   ],
   [
    "Obsidian Coast League",
    "2024-25",
    "2024-08-10",
    "Silverpine Rovers",
    "Emberfield Kestrels"
   ]
  ]
 },
 "note":"Descriptive statistics only: no confidence intervals, no deltas, no verdicts, no comparative claims.",
 "overdispersion":{
  "mean":1.3070175438596492,
  "n":114,
  "variance":0.9671437365343182
 },
 "primary":{
  "baseline":{
   "brier":0.6513262608006456,
   "log_loss":1.0756660244986818,
   "rps":0.2350484286002546
  },
  "calibration":{
   "bins":[
    {
     "mean_p":0.1922355541990161,
     "n":2,
     "realized_frequency":0.5
    },
    {
     "mean_p":0.3068857322030056,
     "n":73,
     "realized_frequency":0.3013698630136986
    },
    {
     "mean_p":0.48085802938550376,
     "n":15,
     "realized_frequency":0.4666666666666667
    },
    {
     "mean_p":null,
     "n":0,
     "realized_frequency":null
    },
    {
     "mean_p":null,
     "n":0,
     "realized_frequency":null
    }
   ],
   "n_matches":30,
   "n_pairs":90
  },
  "draw_deficit":-0.03437540133650058,
  "model":{
   "brier":0.657717020755589,
   "log_loss":1.0893088945036264,
   "rps":0.23748019128548054
  },
  "n_draw_contributions":7,
  "n_matches":30
 },
 "run_digest":"150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f",
 "secondary":{
  "baseline":{
   "brier":0.6659747894436246,
   "log_loss":1.10026212693129,
   "rps":0.2385794979516648
  },
  "calibration":{
   "bins":[
    {
     "mean_p":0.16572509513274955,
     "n":6,
     "realized_frequency":0.6666666666666666
    },
    {
     "mean_p":0.30851337436509413,
     "n":137,
     "realized_frequency":0.32116788321167883
    },
    {
     "mean_p":0.4853685454016753,
     "n":27,
     "realized_frequency":0.3333333333333333
    },
    {
     "mean_p":0.6343664153403693,
     "n":1,
     "realized_frequency":0.0
    },
    {
     "mean_p":null,
     "n":0,
     "realized_frequency":null
    }
   ],
   "n_matches":57,
   "n_pairs":171
  },
  "draw_deficit":-0.025271786352718206,
  "model":{
   "brier":0.7110877726071556,
   "log_loss":1.172910978563622,
   "rps":0.2599049808350038
  },
  "n_draw_contributions":14,
  "n_matches":57
 }
}
```

---

===== FILE: starter/data/provenance.json =====

```json
{
 "api_contract":{
  "base":"http://127.0.0.1:8765",
  "bind":"127.0.0.1 (localhost-only, read-only; no CORS headers)",
  "body_encoding":"byte-deterministic JSON (sort_keys, compact separators, UTF-8)",
  "errors":{
   "integrity_error":500,
   "malformed_path":400,
   "unimplemented_method":501,
   "unknown_fixture":404,
   "unknown_route":404,
   "write_method":405
  },
  "launch":"No CLI is included. create_server(db_path, host=\"127.0.0.1\", port=0) defaults to an ephemeral port; 8765 is a suggested local convention \u2014 bind it in a small launcher.",
  "routes":[
   "GET /health",
   "GET /forecasts/{competition}/{season}/{date}/{home}/{away}"
  ]
 },
 "disclaimer":"In-sample analytic estimate from the fitted model; pending chronological evaluation against realized results (Phases 9 and 11). Not evidence of accuracy.",
 "evaluation_version":1,
 "fixture_file_sha256s":[
  [
   "season-1.json",
   "f779fc0a952e00ecd904c8019b288c43326635cb5c5a698f2f74870b11d57e39"
  ],
  [
   "season-2.json",
   "5a9da621c678933b0a5f0320a79c8c245783b34bbaf59a73e0fd7d7609d916a9"
  ]
 ],
 "forecast_version":"forecast-poisson-mle-v1",
 "honest_limits":[
  "synthetic fixtures only (Obsidian Coast League, 2 seasons, 60 matches)",
  "evaluated n = 30 primary / 57 secondary",
  "runtime wall-times are load-labelled, not an SLA",
  "'research-ready' = documented, traceable, deterministic, pre-registered \u2014 not validated, accurate, or complete"
 ],
 "model_version":"poisson-mle-v1",
 "record_content_hash":"ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47",
 "replay_seed":20261017,
 "repo_commit":"b8cc13d",
 "run_digest":"150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f",
 "schema_version":2,
 "stage_map":{
  "built":[
   {
    "name":"DATA",
    "path":"app/ingestion/",
    "stage":1
   },
   {
    "name":"VALIDATION",
    "path":"app/validation/",
    "stage":2
   },
   {
    "name":"FEATURE EXTRACTION",
    "path":"app/features/",
    "stage":4
   },
   {
    "name":"STATISTICAL MODELS",
    "path":"app/models/",
    "stage":5
   },
   {
    "name":"FORECAST DISTRIBUTIONS",
    "path":"app/forecasts/",
    "stage":6
   },
   {
    "name":"SCENARIO EXPLORATION",
    "path":"app/scenarios/",
    "stage":7
   },
   {
    "name":"DECISION ANALYSIS",
    "path":"app/decisions/",
    "stage":8
   },
   {
    "name":"OUTCOME EVALUATION",
    "path":"app/backtesting/ + app/evaluation/",
    "stage":9
   }
  ],
  "unbuilt":[
   {
    "documented_as":"G1-G5 in docs/KNOWN-LIMITATIONS.md",
    "name":"PRE-MATCH STATE",
    "path":"app/state/",
    "stage":3
   },
   {
    "documented_as":"G1-G5 in docs/KNOWN-LIMITATIONS.md",
    "name":"MODEL IMPROVEMENT",
    "path":"app/improvement/",
    "stage":10
   }
  ]
 }
}
```

---

===== FILE: starter/fixtures/golden-pins.json =====

```json
{
 "accounting":[
  60,
  57,
  3,
  27,
  30
 ],
 "calibration_total_pairs":{
  "primary":90,
  "secondary":171
 },
 "dominant_bin_share":{
  "primary":0.8111111111111111,
  "secondary":0.8011695906432749
 },
 "draw_deficit":{
  "primary":-0.03437540133650058,
  "secondary":-0.025271786352718206
 },
 "metrics":{
  "primary.baseline":[
   30,
   1.0756660244986818,
   0.6513262608006456,
   0.2350484286002546
  ],
  "primary.model":[
   30,
   1.0893088945036264,
   0.657717020755589,
   0.23748019128548054
  ],
  "secondary.baseline":[
   57,
   1.10026212693129,
   0.6659747894436246,
   0.2385794979516648
  ],
  "secondary.model":[
   57,
   1.172910978563622,
   0.7110877726071556,
   0.2599049808350038
  ]
 },
 "n_draw_contributions":{
  "primary":7,
  "secondary":14
 },
 "record_hash":"ef46a36622b1ceb7f2bd85e730770d05c0ae880525b76657ca1934c7d16dfa47",
 "run_digest":"150b9796dde5ae4dbf2e3a7665c7cf55062323c33acad41d5d90c44481bbef2f"
}
```

---
