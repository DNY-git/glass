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
