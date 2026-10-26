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
