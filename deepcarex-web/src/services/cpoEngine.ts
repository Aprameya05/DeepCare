import type { ClinicalCase, QuestionnaireAnswers, RecommendationResult } from "../types/cpoTypes";

/**
 * Match a single answer value against a match expression.
 *
 * Supported patterns:
 *   "includes:X"   — array contains X  (multi_select fields)
 *   ">=N" / "<=N"  — numeric comparison
 *   "N-M"          — inclusive numeric range
 *   "a|b|c"        — pipe-OR for string values
 *   "true"/"false" — boolean exact match
 *   "exact"        — plain string exact match
 */
export function matchFeature(
  value: string | number | boolean | string[],
  match: string
): boolean {
  // Array containment
  if (match.startsWith("includes:")) {
    const target = match.slice(9);
    return Array.isArray(value) ? value.includes(target) : false;
  }

  // Numeric operators (apply to number type or numeric strings; also handles scale_1_5)
  const numVal =
    typeof value === "number"
      ? value
      : typeof value === "string" && value !== "" && !isNaN(Number(value))
        ? Number(value)
        : NaN;

  if (!isNaN(numVal)) {
    const ge = /^>=(\d+(?:\.\d+)?)$/.exec(match);
    if (ge) return numVal >= parseFloat(ge[1]);
    const le = /^<=(\d+(?:\.\d+)?)$/.exec(match);
    if (le) return numVal <= parseFloat(le[1]);
    const range = /^(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$/.exec(match);
    if (range) return numVal >= parseFloat(range[1]) && numVal <= parseFloat(range[2]);
  }

  // Boolean exact match
  if (typeof value === "boolean") return value === (match === "true");

  // String pipe-OR (covers single_select and string "true"/"false" stored as strings)
  if (typeof value === "string") return match.split("|").includes(value);

  // Array × pipe-OR fallback (multi_select without includes: prefix)
  if (Array.isArray(value)) {
    const opts = match.split("|");
    return value.some((v) => opts.includes(v));
  }

  return false;
}

interface ScoredCase {
  clinicalCase: ClinicalCase;
  confidence: number;
  matchedFeatures: string[];
}

/**
 * Score one clinical case against the provided answers.
 * Returns confidence = 0 if any required feature is unmatched (disqualified).
 */
export function scoreCase(clinicalCase: ClinicalCase, answers: QuestionnaireAnswers): ScoredCase {
  const matchedFeatures: string[] = [];

  // Required features — all must match; first failure → disqualify
  for (const rf of clinicalCase.required_features) {
    const value = answers[rf.feature_key];
    if (value === undefined || !matchFeature(value, rf.match)) {
      return { clinicalCase, confidence: 0, matchedFeatures: [] };
    }
    matchedFeatures.push(rf.feature_key);
  }

  const requiredScore = clinicalCase.required_features.length > 0 ? 1 : 0;

  // Supporting features — weighted partial score; default 0.5 when none defined
  const sf = clinicalCase.supporting_features;
  let supportingScore = 0.5;
  if (sf.length > 0) {
    const totalWeight = sf.reduce((sum, f) => sum + f.weight, 0);
    let matchedWeight = 0;
    for (const f of sf) {
      const value = answers[f.feature_key];
      if (value !== undefined && matchFeature(value, f.match)) {
        matchedWeight += f.weight;
        matchedFeatures.push(f.feature_key);
      }
    }
    supportingScore = totalWeight > 0 ? matchedWeight / totalWeight : 0.5;
  }

  return {
    clinicalCase,
    confidence: 0.7 * requiredScore + 0.3 * supportingScore,
    matchedFeatures,
  };
}

/**
 * Recommend diagnostic tests based on questionnaire answers and a list of clinical cases.
 *
 * Returns a "recommend" result when the top-scoring case clears its confidence floor,
 * or an "escalate" result when there is no match, the score is too low, or
 * fewer than 3 answers were provided.
 */
export function recommendTests(
  answers: QuestionnaireAnswers,
  cases: ClinicalCase[]
): RecommendationResult {
  if (Object.keys(answers).length < 3) {
    return {
      status: "escalate",
      reason: "insufficient_data",
      topCandidates: [],
      message:
        "Not enough information was provided to make a recommendation. Please complete more questionnaire fields. Please consult a qualified clinician for evaluation.",
    };
  }

  const scored = cases
    .map((c) => scoreCase(c, answers))
    .sort((a, b) => b.confidence - a.confidence);

  const top = scored[0];

  if (top.confidence === 0) {
    return {
      status: "escalate",
      reason: "no_match",
      topCandidates: [],
      message:
        "Your symptom profile does not match any recognized pattern in our clinical database. Please consult a qualified clinician for evaluation.",
    };
  }

  if (top.confidence < top.clinicalCase.confidence_floor) {
    return {
      status: "escalate",
      reason: "below_threshold",
      topCandidates: scored.slice(0, 3).map((s) => ({
        condition_name: s.clinicalCase.condition_name,
        confidence: s.confidence,
      })),
      message: `The closest match (${top.clinicalCase.condition_name}) did not reach the minimum confidence threshold. The symptom pattern is ambiguous and requires further clinical assessment. Please consult a qualified clinician for evaluation.`,
    };
  }

  return {
    status: "recommend",
    condition: {
      id: top.clinicalCase.condition_id,
      name: top.clinicalCase.condition_name,
      rationale: top.clinicalCase.rationale,
    },
    tests: top.clinicalCase.recommended_tests.map((t) => ({
      name: t.test_name,
      priority: t.priority,
    })),
    confidence: top.confidence,
    matchedFeatures: top.matchedFeatures,
  };
}
