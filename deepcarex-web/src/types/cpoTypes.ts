export type QuestionnaireAnswers = Record<string, string | number | boolean | string[]>;

export interface Test {
  name: string;
  priority: "primary" | "secondary";
}

interface ConditionInfo {
  id: string;
  name: string;
  rationale: string;
}

interface TopCandidate {
  condition_name: string;
  confidence: number;
}

export type RecommendationResult =
  | {
      status: "recommend";
      condition: ConditionInfo;
      tests: Test[];
      confidence: number;
      matchedFeatures: string[];
    }
  | {
      status: "escalate";
      reason: "no_match" | "below_threshold" | "insufficient_data";
      topCandidates: TopCandidate[];
      message: string;
    };

// Shape of each entry in cpoClinicalCases.json
export interface RequiredFeature {
  feature_key: string;
  match: string;
}

export interface SupportingFeature {
  feature_key: string;
  match: string;
  weight: number;
}

export interface ClinicalCase {
  condition_id: string;
  condition_name: string;
  rationale: string;
  required_features: RequiredFeature[];
  supporting_features: SupportingFeature[];
  recommended_tests: Array<{ test_name: string; priority: "primary" | "secondary" }>;
  confidence_floor: number;
}
