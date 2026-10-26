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
