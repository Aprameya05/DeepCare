// MIMIC-IV summary-stat priors; no external DB required.

export type CPOActionType = 'OrderTest' | 'Prescribe' | 'Refer' | 'Escalate' | 'Wait';

export interface PatientScenarioInitialState {
  demographics: { age: number; sex: string; weight: number };
  vitals: { bp: string; hr: number; temp: number; spo2: number };
  symptoms: string[];
  labResults: Record<string, number | string>;
}

export interface PatientScenario {
  id: string;
  name: string;
  level: 'simple' | 'moderate' | 'complex';
  initialState: PatientScenarioInitialState;
  groundTruthDiagnosis: string;
  optimalActionSequence: CPOActionType[];
  maxSteps: number;
  budgetCeiling: number;
  displayPriorResults: string;
}

const SCENARIOS: PatientScenario[] = [
  // ── Level 1: Simple — single-system ─────────────────────────────────────
  {
    id: 'uti',
    name: 'Simple: UTI',
    level: 'simple',
    initialState: {
      demographics: { age: 34, sex: 'F', weight: 65 },
      vitals: { bp: '118/76', hr: 88, temp: 37.8, spo2: 99 },
      symptoms: ['dysuria', 'urinary frequency', 'pelvic discomfort'],
      labResults: {},
    },
    groundTruthDiagnosis: 'Uncomplicated UTI',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Wait'],
    maxSteps: 5,
    budgetCeiling: 600,
    displayPriorResults: 'None',
  },
  {
    id: 'pneumonia',
    name: 'Simple: Pneumonia',
    level: 'simple',
    initialState: {
      demographics: { age: 52, sex: 'M', weight: 82 },
      vitals: { bp: '132/84', hr: 102, temp: 38.9, spo2: 94 },
      symptoms: ['productive cough', 'fever 38.9°C', 'pleuritic chest pain'],
      labResults: { rapid_flu: 'Negative' },
    },
    groundTruthDiagnosis: 'Community-Acquired Pneumonia',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Wait', 'Wait'],
    maxSteps: 6,
    budgetCeiling: 800,
    displayPriorResults: 'Rapid flu: Negative',
  },
  {
    id: 'htn_crisis',
    name: 'Simple: HTN Crisis',
    level: 'simple',
    initialState: {
      demographics: { age: 61, sex: 'M', weight: 90 },
      vitals: { bp: '195/118', hr: 94, temp: 36.8, spo2: 98 },
      symptoms: ['severe headache', 'blurred vision', 'nausea'],
      labResults: {},
    },
    groundTruthDiagnosis: 'Hypertensive Crisis',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Wait', 'Wait'],
    maxSteps: 6,
    budgetCeiling: 700,
    displayPriorResults: 'None',
  },
  // ── Level 2: Moderate — two comorbidities ───────────────────────────────
  {
    id: 't2dm_aki',
    name: 'Moderate: T2DM + AKI',
    level: 'moderate',
    initialState: {
      demographics: { age: 67, sex: 'M', weight: 88 },
      vitals: { bp: '148/92', hr: 96, temp: 37.2, spo2: 97 },
      symptoms: ['nausea', 'decreased urine output', 'bilateral leg edema', 'fatigue'],
      labResults: { glucose: 310, creatinine: 3.2, BUN: 48 },
    },
    groundTruthDiagnosis: 'AKI superimposed on T2DM nephropathy',
    optimalActionSequence: ['OrderTest', 'OrderTest', 'Prescribe', 'Refer', 'Wait'],
    maxSteps: 8,
    budgetCeiling: 1500,
    displayPriorResults: 'Glucose: 310 mg/dL, Creatinine: 3.2, BUN: 48',
  },
  {
    id: 'chf_pneumonia',
    name: 'Moderate: CHF + Pneumonia',
    level: 'moderate',
    initialState: {
      demographics: { age: 73, sex: 'F', weight: 71 },
      vitals: { bp: '158/96', hr: 110, temp: 38.5, spo2: 91 },
      symptoms: ['dyspnea at rest', 'bilateral crackles', 'productive cough', 'peripheral edema'],
      labResults: { BNP: 820, WBC: 14.2 },
    },
    groundTruthDiagnosis: 'Acute CHF exacerbation + CAP',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Prescribe', 'Refer', 'Wait'],
    maxSteps: 8,
    budgetCeiling: 2000,
    displayPriorResults: 'BNP: 820, WBC: 14.2',
  },
  // ── Level 3: Complex — multi-system ─────────────────────────────────────
  {
    id: 'sepsis_mof',
    name: 'Complex: Septic Shock + MODS',
    level: 'complex',
    initialState: {
      demographics: { age: 58, sex: 'M', weight: 78 },
      vitals: { bp: '85/52', hr: 128, temp: 39.4, spo2: 88 },
      symptoms: ['rigors', 'confusion', 'hypotension', 'oliguria', 'diffuse abdominal pain'],
      labResults: { lactate: 4.8, WBC: 22.1, creatinine: 2.8, bilirubin: 3.4, platelets: 68 },
    },
    groundTruthDiagnosis: 'Septic Shock — MODS, abdominal source',
    optimalActionSequence: ['Escalate'],
    maxSteps: 4,
    budgetCeiling: 5000,
    displayPriorResults: 'Lactate: 4.8, WBC: 22.1, Cr: 2.8, Bili: 3.4, Plt: 68',
  },
  {
    id: 'polytrauma',
    name: 'Complex: Polytrauma MVC',
    level: 'complex',
    initialState: {
      demographics: { age: 29, sex: 'M', weight: 80 },
      vitals: { bp: '90/60', hr: 138, temp: 36.1, spo2: 90 },
      symptoms: ['chest wall tenderness', 'abdominal guarding', 'GCS 13', 'right thigh deformity'],
      labResults: { Hgb: 7.2, pH: 7.28, base_excess: -8 },
    },
    groundTruthDiagnosis: 'Polytrauma — pneumothorax, splenic laceration, femur fracture',
    optimalActionSequence: ['Escalate'],
    maxSteps: 3,
    budgetCeiling: 5000,
    displayPriorResults: 'Hgb: 7.2, pH: 7.28, Base excess: -8',
  },
];

export function generateScenario(level: 'simple' | 'moderate' | 'complex'): PatientScenario {
  const pool = SCENARIOS.filter(s => s.level === level);
  return pool[Math.floor(Math.random() * pool.length)];
}

export function getCurriculumScenarios(level: 'simple' | 'moderate' | 'complex'): PatientScenario[] {
  return SCENARIOS.filter(s => s.level === level);
}

export function getAllScenarios(): PatientScenario[] {
  return SCENARIOS;
}
