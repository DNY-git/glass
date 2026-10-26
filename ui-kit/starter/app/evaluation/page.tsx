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
