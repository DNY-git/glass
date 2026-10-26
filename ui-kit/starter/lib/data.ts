/**
 * Typed data access over the kit's static JSON exports.
 *
 * The Forecast shape is IDENTICAL to the live API's forecast_payload()
 * (app/api/serialize.py in the source repo), so switching to Mode B
 * (live localhost API via a proxy route) changes the loader only.
 */
import forecastsJson from "@/data/forecasts.json";
import evaluationJson from "@/data/evaluation.json";
import provenanceJson from "@/data/provenance.json";

export interface Forecast {
  as_of: string;
  away: string;
  competition: string;
  content_hash: string;
  convergence_status: string;
  date: string;
  disclaimer: string;
  dropped_mass: number;
  forecast_version: string;
  home: string;
  input_digest: string;
  insufficient_data: boolean;
  insufficient_teams: string[];
  kickoff: { availability: string; time: string | null };
  lambda_away: number;
  lambda_home: number;
  max_goals: number;
  model_version: string;
  outcome_probs: { away: number; draw: number; home: number };
  season: string;
}

export interface MetricTriple {
  log_loss: number;
  brier: number;
  rps: number;
}

export interface CalibrationBin {
  n: number;
  mean_p: number | null;
  realized_frequency: number | null;
}

export interface Population {
  n_matches: number;
  model: MetricTriple;
  baseline: MetricTriple;
  calibration: { n_matches: number; n_pairs: number; bins: CalibrationBin[] };
  draw_deficit: number;
  n_draw_contributions: number;
}

export interface Evaluation {
  run_digest: string;
  accounting: {
    n_targets: number;
    n_predictions: number;
    n_refusals: number;
    n_flagged: number;
    n_clean: number;
    refusal_keys: string[][];
  };
  primary: Population;
  secondary: Population;
  overdispersion: { n: number; mean: number; variance: number };
  /**
   * UI projection fields, not part of the repo's EvaluationResult:
   * `note` is a fixed descriptive caption; `n_draw_contributions` (on each
   * Population) is the derived count of realized draws.
   */
  note: string;
}

export interface Provenance {
  repo_commit: string;
  run_digest: string;
  record_content_hash: string;
  evaluation_version: number;
  schema_version: number;
  model_version: string;
  forecast_version: string;
  fixture_file_sha256s: string[][];
  replay_seed: number;
  disclaimer: string;
  api_contract: {
    base: string;
    routes: string[];
    errors: Record<string, number>;
    bind: string;
    body_encoding: string;
    launch: string;
  };
  stage_map: {
    built: { stage: number; name: string; path: string }[];
    unbuilt: { stage: number; name: string; path: string; documented_as: string }[];
  };
  honest_limits: string[];
}

export const allForecasts = (): Forecast[] =>
  forecastsJson as unknown as Forecast[];

/** Store read-back order: competition, season, date, home, away. */
export const orderedForecasts = (): Forecast[] =>
  [...allForecasts()].sort((a, b) =>
    (a.competition + a.season + a.date + a.home + a.away).localeCompare(
      b.competition + b.season + b.date + b.home + b.away,
    ),
  );

export const teams = (): string[] =>
  [...new Set(allForecasts().flatMap((f) => [f.home, f.away]))].sort();

export const seasons = (): string[] =>
  [...new Set(allForecasts().map((f) => f.season))].sort();

export const evaluation = (): Evaluation =>
  evaluationJson as unknown as Evaluation;

export const provenance = (): Provenance =>
  provenanceJson as unknown as Provenance;

export const forecastKeyPath = (f: Forecast): string =>
  [f.competition, f.season, f.date, f.home, f.away]
    .map(encodeURIComponent)
    .join("/");

export const findByKey = (
  competition: string,
  season: string,
  date: string,
  home: string,
  away: string,
): Forecast | undefined =>
  allForecasts().find(
    (f) =>
      f.competition === decodeURIComponent(competition) &&
      f.season === decodeURIComponent(season) &&
      f.date === decodeURIComponent(date) &&
      f.home === decodeURIComponent(home) &&
      f.away === decodeURIComponent(away),
  );

export const pct = (p: number, digits = 1): string =>
  `${(p * 100).toFixed(digits)}%`;

export const num = (x: number, digits = 4): string => x.toFixed(digits);
