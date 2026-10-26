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
