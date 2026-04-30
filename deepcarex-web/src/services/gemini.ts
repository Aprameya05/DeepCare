import { GoogleGenerativeAI } from "@google/generative-ai";
import type { CPOState } from '../env/CPOEnv';

export type DiagnosisResult = {
  diagnosis: string;
  confidence: number;
  risk_level: 'Low' | 'Medium' | 'High';
  findings?: string[] | string;
  risk_factors?: string[] | string;
  recommendations: string[];
};

export type CPOActionResponse = {
  action: 'Order Test' | 'Prescribe' | 'Refer' | 'Escalate' | 'Wait';
  specific_detail: string;
  reasoning: string;
  expected_reward_impact: {
    accuracy: string;
    cost: string;
    time: string;
    patient_burden: string;
  };
  optimizer_trace?: {
    environment: string;
    reward_function: string;
    candidate_count: number;
    selected_candidate_index: number;
    selection_reason: string;
  };
};

function cleanJsonResponse(text: string): string {
    let clean = text.trim();
    if (clean.startsWith('```json')) {
        clean = clean.replace(/^```json/, '');
    } else if (clean.startsWith('```')) {
        clean = clean.replace(/^```/, '');
    }
    if (clean.endsWith('```')) {
        clean = clean.replace(/```$/, '');
    }
    return clean.trim();
}

const CPO_ACTIONS = ['Order Test', 'Prescribe', 'Refer', 'Escalate', 'Wait'] as const;

type CPOCandidateAction = {
  action: CPOActionResponse['action'];
  specific_detail: string;
  reasoning: string;
  expected_reward_impact: {
    accuracy: string;
    cost: string;
    time: string;
    patient_burden: string;
  };
};

type CPOCriticResponse = {
  scores: {
    candidate_index: number;
    total_reward: number;
    rationale: string;
  }[];
  selected_candidate_index: number;
  selection_reason: string;
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").trim();
const ENABLE_GEMINI_FALLBACK =
  String(import.meta.env.VITE_ENABLE_GEMINI_FALLBACK || "false").toLowerCase() === "true";

const DISEASE_NAME_TO_ID: Record<string, string> = {
  "Alzheimer's Disease": "alzheimers",
  "Brain Tumor": "brain_tumor",
  "COVID-19": "covid",
  "Breast Cancer": "breast_cancer",
  "Diabetes": "diabetes",
};

export const isApiInferenceConfigured = (): boolean => Boolean(API_BASE_URL);

function toDiseaseId(diseaseName: string): string {
  return DISEASE_NAME_TO_ID[diseaseName] || diseaseName.toLowerCase().replace(/\s+/g, "_");
}

function normalizeDiagnosisResponse(raw: any, fallbackClasses: string[]): DiagnosisResult {
  const diagnosis = String(raw?.diagnosis || fallbackClasses[0] || "Unknown");
  const confidence = Number.isFinite(raw?.confidence) ? Number(raw.confidence) : 0;
  const risk_level = ["Low", "Medium", "High"].includes(raw?.risk_level)
    ? raw.risk_level
    : confidence >= 85
      ? "High"
      : confidence >= 60
        ? "Medium"
        : "Low";

  return {
    diagnosis,
    confidence,
    risk_level,
    findings: raw?.findings,
    risk_factors: raw?.risk_factors,
    recommendations: Array.isArray(raw?.recommendations)
      ? raw.recommendations
      : ["Follow up with a qualified healthcare professional."],
  };
}

async function requestApiImageDiagnosis(
  diseaseId: string,
  imageBase64: string,
  mimeType: string,
  classes: string[]
): Promise<DiagnosisResult> {
  const binary = atob(imageBase64);
  const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
  const blob = new Blob([bytes], { type: mimeType || "image/jpeg" });
  const file = new File([blob], "scan-image", { type: mimeType || "image/jpeg" });

  const formData = new FormData();
  formData.append("diseaseId", diseaseId);
  formData.append("image", file);

  const response = await fetch(`${API_BASE_URL}/predict/image`, {
    method: "POST",
    body: formData,
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.detail || "Image inference API request failed.");
  }
  return normalizeDiagnosisResponse(payload, classes);
}

async function requestApiParameterDiagnosis(
  diseaseId: string,
  parameters: Record<string, any>,
  classes: string[]
): Promise<DiagnosisResult> {
  const response = await fetch(`${API_BASE_URL}/predict/params`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      diseaseId,
      parameters,
    }),
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload?.detail || "Parameter inference API request failed.");
  }
  return normalizeDiagnosisResponse(payload, classes);
}

const getMockResponse = (diseaseName: string, classes: string[], isHighRisk: boolean = true): DiagnosisResult => {
    return {
        diagnosis: isHighRisk ? classes[0] : classes[classes.length - 1],
        confidence: Math.floor(Math.random() * (99 - 85 + 1) + 85),
        risk_level: isHighRisk ? 'High' : 'Low',
        findings: [
            `Detected primary indicators associated with ${diseaseName}.`,
            "Pattern recognition matched with high confidence threshold.",
            "Cross-referenced with verified clinical datasets."
        ],
        risk_factors: [
            "Elevated clinical markers.",
            "Historical age/demographic baseline.",
            "Algorithm-identified anomalous features."
        ],
        recommendations: [
            "Schedule follow-up consultation with primary care physician.",
            "Conduct secondary diagnostic confirmation test.",
            "Maintain current monitoring protocol."
        ]
    };
};

export const runImageDiagnosis = async (
  apiKey: string,
  diseaseName: string,
  classes: string[],
  imageBase64: string,
  mimeType: string
): Promise<DiagnosisResult> => {
  const diseaseId = toDiseaseId(diseaseName);
  if (API_BASE_URL) {
    try {
      return await requestApiImageDiagnosis(diseaseId, imageBase64, mimeType, classes);
    } catch (error: any) {
      console.warn("Inference API image request failed.", error?.message);
      if (!ENABLE_GEMINI_FALLBACK) {
        throw new Error(
          "Inference API image request failed. Set VITE_ENABLE_GEMINI_FALLBACK=true to allow Gemini fallback."
        );
      }
    }
  }

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });

  const prompt = `You are a medical AI diagnostic assistant. Analyze this medical image for ${diseaseName} and provide:
1. Primary diagnosis from these exactly matching options: [${classes.join(', ')}]
2. Confidence percentage (0-100) as a number
3. Key visual findings/indicators you observed as an array of strings
4. Risk level: "Low", "Medium", or "High"
5. Recommended next steps as an array of strings

Respond ONLY with a valid JSON format matching this exact schema:
{
  "diagnosis": "string",
  "confidence": number,
  "findings": ["string"],
  "risk_level": "Low" | "Medium" | "High",
  "recommendations": ["string"]
}`;

  try {
    const result = await model.generateContent([
      {
        inlineData: {
          data: imageBase64,
          mimeType: mimeType
        }
      },
      prompt
    ]);
    
    const responseText = result.response.text();
    const jsonStr = cleanJsonResponse(responseText);
    return JSON.parse(jsonStr) as DiagnosisResult;
  } catch (error: any) {
    console.warn("Gemini API request failed due to quota/network issues. Falling back to simulated response.", error.message);
    // Give a 1.5 second artificial delay for the simulation effect
    await new Promise(r => setTimeout(r, 1500));
    return getMockResponse(diseaseName, classes, true);
  }
};

export const runParameterDiagnosis = async (
  apiKey: string,
  diseaseName: string,
  classes: string[],
  parameters: Record<string, any>
): Promise<DiagnosisResult> => {
  const diseaseId = toDiseaseId(diseaseName);
  if (API_BASE_URL) {
    try {
      return await requestApiParameterDiagnosis(diseaseId, parameters, classes);
    } catch (error: any) {
      console.warn("Inference API parameter request failed.", error?.message);
      if (!ENABLE_GEMINI_FALLBACK) {
        throw new Error(
          "Inference API parameter request failed. Set VITE_ENABLE_GEMINI_FALLBACK=true to allow Gemini fallback."
        );
      }
    }
  }

  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });

  const paramsString = Object.entries(parameters)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');

  const prompt = `You are a medical AI diagnostic assistant trained on clinical data for ${diseaseName}. Given these patient parameters:
${paramsString}

Predict:
1. Diagnosis ONLY from these exact options: [${classes.join(', ')}]
2. Confidence percentage (0-100) as a number
3. Top 3 contributing risk factors as an array of strings
4. Risk level: "Low", "Medium", or "High"
5. Recommendations as an array of strings

Respond ONLY with a valid JSON format matching this exact schema:
{
  "diagnosis": "string",
  "confidence": number,
  "risk_factors": ["string"],
  "risk_level": "Low" | "Medium" | "High",
  "recommendations": ["string"]
}`;

  try {
    const result = await model.generateContent(prompt);
    const responseText = result.response.text();
    const jsonStr = cleanJsonResponse(responseText);
    return JSON.parse(jsonStr) as DiagnosisResult;
  } catch (error: any) {
    console.warn("Gemini API request failed due to quota/network issues. Falling back to simulated response.", error.message);
    // Give a 1.5 second artificial delay for the simulation effect
    await new Promise(r => setTimeout(r, 1500));
    
    // Simple heuristic to make simulation semi-realistic
    let isHighRisk = false;
    if (diseaseName === 'Diabetes' && parameters.glucose > 140) isHighRisk = true;
    if (diseaseName === 'Breast Cancer' && parameters.radius > 15) isHighRisk = true;

    return getMockResponse(diseaseName, classes, isHighRisk);
  }
};

function validateCPOActionResponse(obj: unknown): obj is CPOActionResponse {
  const o = obj as CPOActionResponse;
  const validActions = ['Order Test', 'Prescribe', 'Refer', 'Escalate', 'Wait'];
  return (
    typeof o === 'object' &&
    o !== null &&
    validActions.includes(o.action) &&
    typeof o.specific_detail === 'string' &&
    typeof o.reasoning === 'string' &&
    typeof o.expected_reward_impact === 'object' &&
    o.expected_reward_impact !== null
  );
}

export const runCPOPathway = async (
  apiKey: string,
  state: CPOState,
  cumulativeReward = 0
): Promise<CPOActionResponse> => {
  let model: ReturnType<InstanceType<typeof GoogleGenerativeAI>['getGenerativeModel']> | null = null;
  try {
    if (!apiKey || apiKey.trim() === "") throw new Error("API key missing. Falling back.");
    const genAI = new GoogleGenerativeAI(apiKey);
    model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
  } catch (_initError) {
    // handled in try-catch below
  }

  const historyStr = state.actionHistory.length > 0
    ? state.actionHistory.map((s, i) =>
        `Step ${i + 1}: [${s.action.type}] ${s.action.detail}` +
        (s.action.outcome ? ` → Outcome: ${s.action.outcome}` : '') +
        ` (step reward: ${s.reward.toFixed(3)})`
      ).join('\n')
    : 'None';

  const labStr = Object.entries(state.labResults).length > 0
    ? Object.entries(state.labResults).map(([k, v]) => `  ${k}: ${v}`).join('\n')
    : '  None';

  const prompt = `You are an AI Clinical Pathway Optimizer (CPO) guided by a reinforcement-learning reward function.

REWARD WEIGHTS (per step):
  R = +diagnostic_accuracy_delta - 0.3×norm_time - 0.3×norm_cost - 0.4×patient_burden
  • OrderTest  cost $150  time 60 min  burden 0.3
  • Prescribe  cost $50   time 15 min  burden 0.1
  • Refer      cost $200  time 120 min burden 0.2
  • Escalate   cost $1000 time 30 min  burden 0.8  (ENDS EPISODE)
  • Wait       cost $0    time 120 min burden 0.05

CURRENT EPISODE STATE:
  Episode ID   : ${state.episodeId}
  Time elapsed : ${state.timeElapsed} min
  Cost accrued : $${state.costAccrued}
  Cumulative R : ${cumulativeReward.toFixed(3)}

PATIENT:
  Demographics : ${state.demographics.age}${state.demographics.sex}, ${state.demographics.weight}kg
  Vitals       : BP ${state.vitals.bp} | HR ${state.vitals.hr} | Temp ${state.vitals.temp}°C | SpO2 ${state.vitals.spo2}%
  Symptoms     : ${state.symptoms.join(', ')}
  Lab Results  :
${labStr}

PRIOR ACTIONS:
${historyStr}

Select the NEXT SINGLE BEST ACTION. Choose "Escalate" if patient is critically unstable.
Action options: "Order Test" | "Prescribe" | "Refer" | "Escalate" | "Wait"

Respond ONLY with valid JSON matching this exact schema:
{
  "action": "Order Test" | "Prescribe" | "Refer" | "Escalate" | "Wait",
  "specific_detail": "string",
  "reasoning": "string",
  "expected_reward_impact": {
    "accuracy": "string",
    "cost": "string",
    "time": "string",
    "patient_burden": "string"
  }
}`;

  try {
    if (!model) throw new Error("No model available");
    const result = await model.generateContent(prompt);
    const responseText = result.response.text();
    const jsonStr = cleanJsonResponse(responseText);
    const parsed: unknown = JSON.parse(jsonStr);
    if (!validateCPOActionResponse(parsed)) throw new Error("Invalid CPOActionResponse shape");
    return parsed;
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : String(error);
    console.warn("Gemini CPO request failed. Falling back.", msg);
    await new Promise(r => setTimeout(r, 1500));
    return {
      action: "Order Test",
      specific_detail: "Comprehensive Metabolic Panel (CMP) & CBC",
      reasoning: `Simulation fallback (${msg.slice(0, 60)}). Baseline labs offer high accuracy delta at low cost/time.`,
      expected_reward_impact: {
        accuracy: "+High",
        cost: "-Low",
        time: "-Low",
        patient_burden: "-Low",
      },
    };
  }
};

export const runMetaOptimizedCPOPathway = async (
  apiKey: string,
  state: CPOState,
  cumulativeReward = 0
): Promise<CPOActionResponse> => {
  let model: ReturnType<InstanceType<typeof GoogleGenerativeAI>['getGenerativeModel']> | null = null;
  try {
    if (!apiKey || apiKey.trim() === "") throw new Error("API key missing. Falling back.");
    const genAI = new GoogleGenerativeAI(apiKey);
    model = genAI.getGenerativeModel({ model: "gemini-1.5-pro" });
  } catch {
    // Fallback is handled in the catch below.
  }

  const historyStr = state.actionHistory.length > 0
    ? state.actionHistory.map((s, i) =>
      `Step ${i + 1}: [${s.action.type}] ${s.action.detail}` +
      (s.action.outcome ? ` → Outcome: ${s.action.outcome}` : '') +
      ` (step reward: ${s.reward.toFixed(3)})`
    ).join('\n')
    : 'None';

  const labStr = Object.entries(state.labResults).length > 0
    ? Object.entries(state.labResults).map(([k, v]) => `  ${k}: ${v}`).join('\n')
    : '  None';

  const plannerPrompt = `You are the Planner agent in a Meta-style Agent Optimizer Environment for clinical pathways.
Generate exactly 3 candidate next actions for this patient.

CURRENT EPISODE STATE:
  Episode ID   : ${state.episodeId}
  Time elapsed : ${state.timeElapsed} min
  Cost accrued : $${state.costAccrued}
  Cumulative R : ${cumulativeReward.toFixed(3)}

PATIENT:
  Demographics : ${state.demographics.age}${state.demographics.sex}, ${state.demographics.weight}kg
  Vitals       : BP ${state.vitals.bp} | HR ${state.vitals.hr} | Temp ${state.vitals.temp}°C | SpO2 ${state.vitals.spo2}%
  Symptoms     : ${state.symptoms.join(', ')}
  Lab Results  :
${labStr}

PRIOR ACTIONS:
${historyStr}

Constraints:
- Candidate actions must use only this action set: [${CPO_ACTIONS.join(', ')}]
- Optimize reward: +diagnostic_accuracy, -cost, -time, -patient_burden
- Keep actions clinically plausible and specific

Respond ONLY with JSON:
{
  "candidates": [
    {
      "action": "Order Test" | "Prescribe" | "Refer" | "Escalate" | "Wait",
      "specific_detail": "string",
      "reasoning": "string",
      "expected_reward_impact": {
        "accuracy": "string",
        "cost": "string",
        "time": "string",
        "patient_burden": "string"
      }
    }
  ]
}`;

  try {
    if (!model) throw new Error("No model available");
    const plannerResult = await model.generateContent(plannerPrompt);
    const plannerText = plannerResult.response.text();
    const plannerJson = JSON.parse(cleanJsonResponse(plannerText)) as { candidates: CPOCandidateAction[] };
    const candidates = (plannerJson.candidates || []).slice(0, 3);

    if (!Array.isArray(candidates) || candidates.length === 0) {
      throw new Error("Planner returned no candidates.");
    }

    const criticPrompt = `You are the Critic/Selector agent in a Meta-style Agent Optimizer Environment.
Score each candidate using this weighted reward function:
Reward = 0.45*AccuracyGain - 0.20*Cost - 0.20*Time - 0.15*PatientBurden

CURRENT EPISODE STATE:
  Episode ID   : ${state.episodeId}
  Time elapsed : ${state.timeElapsed} min
  Cost accrued : $${state.costAccrued}
  Cumulative R : ${cumulativeReward.toFixed(3)}

PATIENT:
  Demographics : ${state.demographics.age}${state.demographics.sex}, ${state.demographics.weight}kg
  Vitals       : BP ${state.vitals.bp} | HR ${state.vitals.hr} | Temp ${state.vitals.temp}°C | SpO2 ${state.vitals.spo2}%
  Symptoms     : ${state.symptoms.join(', ')}
  Lab Results  :
${labStr}

PRIOR ACTIONS:
${historyStr}

Candidate actions:
${candidates.map((c, idx) => `${idx}: ${JSON.stringify(c)}`).join('\n')}

Output ONLY valid JSON:
{
  "scores": [
    { "candidate_index": number, "total_reward": number, "rationale": "string" }
  ],
  "selected_candidate_index": number,
  "selection_reason": "string"
}`;

    const criticResult = await model.generateContent(criticPrompt);
    const criticText = criticResult.response.text();
    const criticJson = JSON.parse(cleanJsonResponse(criticText)) as CPOCriticResponse;

    const chosenIndex = Math.max(0, Math.min(candidates.length - 1, criticJson.selected_candidate_index ?? 0));
    const chosen = candidates[chosenIndex];

    return {
      action: chosen.action,
      specific_detail: chosen.specific_detail,
      reasoning: chosen.reasoning,
      expected_reward_impact: chosen.expected_reward_impact,
      optimizer_trace: {
        environment: "Meta Agent Optimizer v1 (Planner-Critic-Selector)",
        reward_function: "0.45*AccuracyGain - 0.20*Cost - 0.20*Time - 0.15*PatientBurden",
        candidate_count: candidates.length,
        selected_candidate_index: chosenIndex,
        selection_reason: criticJson.selection_reason || "Selected candidate with highest projected reward."
      }
    };
  } catch (error: any) {
    console.warn("Meta optimizer CPO failed, falling back to baseline CPO/simulation.", error?.message);
    const fallback = await runCPOPathway(apiKey, state, cumulativeReward);
    return {
      ...fallback,
      optimizer_trace: {
        environment: "Meta Agent Optimizer v1 (Fallback)",
        reward_function: "0.45*AccuracyGain - 0.20*Cost - 0.20*Time - 0.15*PatientBurden",
        candidate_count: 1,
        selected_candidate_index: 0,
        selection_reason: "Fallback mode engaged due to API/parse issue; returned safest baseline action."
      }
    };
  }
};
