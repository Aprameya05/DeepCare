import type { CurriculumLevel, PatientScenario } from '../env/CPOEnv';

// Optimizer scenarios restricted to merged model branches only.
const SCENARIOS: PatientScenario[] = [
  {
    id: 'diabetes_followup',
    name: 'Simple: Diabetes Risk Review',
    level: 'simple',
    initialState: {
      demographics: { age: 47, sex: 'F', weight: 76 },
      vitals: { bp: '138/86', hr: 92, temp: 36.9, spo2: 98 },
      symptoms: ['polyuria', 'fatigue', 'increased thirst'],
      labResults: { glucose: 178, hba1c: 7.6 },
    },
    groundTruthDiagnosis: 'Diabetes Positive',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Wait'],
    maxSteps: 6,
    budgetCeiling: 800,
    displayPriorResults: 'Glucose: 178, HbA1c: 7.6',
  },
  {
    id: 'breast_cancer_screen',
    name: 'Simple: Breast Cancer Triage',
    level: 'simple',
    initialState: {
      demographics: { age: 53, sex: 'F', weight: 64 },
      vitals: { bp: '128/80', hr: 86, temp: 36.7, spo2: 99 },
      symptoms: ['palpable breast lump', 'localized tenderness'],
      labResults: { radius: 16.2, texture: 20.4, perimeter: 109.2, area: 815 },
    },
    groundTruthDiagnosis: 'Malignant',
    optimalActionSequence: ['OrderTest', 'Refer', 'Wait'],
    maxSteps: 6,
    budgetCeiling: 900,
    displayPriorResults: 'FNA morphology metrics available',
  },
  {
    id: 'covid_respiratory',
    name: 'Moderate: COVID Respiratory Assessment',
    level: 'moderate',
    initialState: {
      demographics: { age: 61, sex: 'M', weight: 83 },
      vitals: { bp: '144/88', hr: 108, temp: 38.3, spo2: 92 },
      symptoms: ['dry cough', 'fever', 'shortness of breath'],
      labResults: { crp: 62, rr: 26 },
    },
    groundTruthDiagnosis: 'COVID Positive',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Refer', 'Wait'],
    maxSteps: 8,
    budgetCeiling: 1800,
    displayPriorResults: 'Inflammatory markers elevated',
  },
  {
    id: 'brain_tumor_workup',
    name: 'Moderate: Brain Tumor Imaging Workup',
    level: 'moderate',
    initialState: {
      demographics: { age: 45, sex: 'M', weight: 79 },
      vitals: { bp: '136/84', hr: 88, temp: 36.8, spo2: 98 },
      symptoms: ['persistent headache', 'blurred vision', 'intermittent nausea'],
      labResults: { mri_flag: 'suspicious lesion present' },
    },
    groundTruthDiagnosis: 'Meningioma',
    optimalActionSequence: ['OrderTest', 'Refer', 'Wait', 'Wait'],
    maxSteps: 8,
    budgetCeiling: 2000,
    displayPriorResults: 'MRI lesion suspicion',
  },
  {
    id: 'alzheimers_progression',
    name: 'Complex: Alzheimer Progression Planning',
    level: 'complex',
    initialState: {
      demographics: { age: 72, sex: 'F', weight: 59 },
      vitals: { bp: '130/78', hr: 84, temp: 36.5, spo2: 97 },
      symptoms: ['memory decline', 'disorientation', 'executive dysfunction'],
      labResults: { cognitive_score: 18, caregiver_concern: 'high' },
    },
    groundTruthDiagnosis: "Alzheimer's Disease (AD)",
    optimalActionSequence: ['OrderTest', 'Refer', 'Prescribe', 'Wait'],
    maxSteps: 7,
    budgetCeiling: 2500,
    displayPriorResults: 'Progressive cognitive decline trend',
  },
];

export function generateScenario(level: CurriculumLevel): PatientScenario {
  const pool = SCENARIOS.filter(s => s.level === level);
  return pool[Math.floor(Math.random() * pool.length)];
}

export function getCurriculumScenarios(level: CurriculumLevel): PatientScenario[] {
  return SCENARIOS.filter(s => s.level === level);
}

export function getAllScenarios(): PatientScenario[] {
  return SCENARIOS;
}
