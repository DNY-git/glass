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
