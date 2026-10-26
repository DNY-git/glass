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
