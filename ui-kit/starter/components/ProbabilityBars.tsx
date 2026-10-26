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
