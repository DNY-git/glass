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
