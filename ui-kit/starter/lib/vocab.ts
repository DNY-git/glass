/**
 * UI vocabulary guards — mirror of the source repo's tests/test_vocab_guards.py.
 *
 * These are acceptance criteria (HANDOFF-UI.md §2.1), not style advice:
 * the UI renders descriptive statistics and must never render claim-language.
 *
 * Two sanctioned negation sites are allowlisted (the repo's own pattern:
 * allowlist the negation, never delete the sentence):
 *   1. the built-in disclaimer: "...Not evidence of accuracy."
 *   2. the honest-limits phrasing: "...not validated, accurate, or complete"
 */

export const OUTCOME_COMPARATIVE_TOKENS = [
  "outperform", "outperforms", "outperformed", "outperforming",
  "beat", "beats", "beaten", "beating", "hit", "hits",
  "winner", "champion", "preferred",
] as const;

export const ACCURACY_TRIO = ["validated", "accurate", "beating"] as const;

/** Banned as labels/column names/variable names (field-name scope). */
export const FIELD_BAN_SEGMENTS = [
  "performance", "rank", "ranking", "correct", "correctness", "best", "accuracy",
] as const;

/**
 * Sanctioned metric identifiers — legal ONLY as metric names on the
 * evaluation surface (exactly as the evaluation package uses them).
 * Never in prose, never with claim adjectives.
 */
export const SANCTIONED_METRIC_TOKENS = [
  "log_loss", "logloss", "brier", "rps", "hit_rate", "calibration",
] as const;

export const BANNED_TOKENS: string[] = [
  ...new Set<string>([...OUTCOME_COMPARATIVE_TOKENS, ...ACCURACY_TRIO]),
];

export const ALLOWLISTED_PHRASES = [
  "Not evidence of accuracy",
  "not validated, accurate, or complete",
] as const;

function stripAllowlisted(text: string): string {
  let out = text;
  for (const phrase of ALLOWLISTED_PHRASES) {
    out = out.split(phrase).join(" ");
  }
  return out;
}

/**
 * Sanctioned metric identifiers are legal on the evaluation surface; strip
 * them before the token scan so `hit_rate` does not trip the `hit` ban.
 */
function stripSanctionedMetrics(text: string): string {
  let out = text;
  for (const token of SANCTIONED_METRIC_TOKENS) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "gi");
    out = out.replace(pattern, " ");
  }
  return out;
}

export function findBannedTokens(text: string): string[] {
  const cleaned = stripSanctionedMetrics(stripAllowlisted(text));
  const hits: string[] = [];
  for (const token of BANNED_TOKENS) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "i");
    if (pattern.test(cleaned)) hits.push(token);
  }
  return hits;
}

/**
 * Field-name scope: never use these as column names, labels, or variable
 * names. This is checked over the starter's authored source, not prose.
 */
export function findFieldNameViolations(text: string): string[] {
  const cleaned = stripSanctionedMetrics(stripAllowlisted(text));
  const hits: string[] = [];
  for (const token of FIELD_BAN_SEGMENTS) {
    const pattern = new RegExp(`(?<![A-Za-z0-9])${token}(?![A-Za-z0-9])`, "i");
    if (pattern.test(cleaned)) hits.push(token);
  }
  return hits;
}

/** Throws when UI copy violates a guard — use in tests/self-checks. */
export function assertClean(text: string, context = "ui text"): void {
  const hits = findBannedTokens(text);
  if (hits.length > 0) {
    throw new Error(
      `vocabulary guard tripped in ${context}: [${hits.join(", ")}] — ` +
        `see HANDOFF-UI.md §2.1. Render the gap, never the claim.`,
    );
  }
}
