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
