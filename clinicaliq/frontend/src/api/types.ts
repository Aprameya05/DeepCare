export interface Patient {
  id: string;
  name: string;
  age: number;
  gender: string;
  phone?: string;
  medical_history?: string;
  created_at?: string;
  updated_at?: string;
}

export interface PatientCreate {
  name: string;
  age: number;
  gender: string;
  phone?: string;
  medical_history?: string;
}

export interface Visit {
  id: string;
  patient_id: string;
  chief_complaint: string;
  notes?: string;
  status: string;
  created_at: string;
}

export interface VisitCreate {
  patient_id: string;
  chief_complaint: string;
}

export interface VitalsCreate {
  visit_id: string;
  heart_rate?: number;
  respiratory_rate?: number;
  temperature?: number;
  oxygen_saturation?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
}

export interface SymptomQuestion {
  id: string;
  text: string;
  type: 'boolean' | 'scale' | 'text';
  options?: string[];
  depends_on?: string;
}

export interface PredictResponse {
  predictions: Array<{
    disease: string;
    confidence: number;
    pubmed_evidence: string[];
  }>;
  uncertainty_flags: string[];
}

export interface TestRecommendation {
  test_name: string;
  priority: 1 | 2 | 3;
  reason: string;
}

export interface BurdenResponse {
  level: 'Low' | 'Medium' | 'High';
  score: number;
  uncertainty_flags?: string[];
  cost_breakdown: {
    raw_cost: number;
    insurance_reduction: number;
    net_cost: number;
  };
}

export interface DashboardStats {
  total_patients: number;
  active_visits: number;
  average_accuracy: number;
  pending_tests: number;
}

export interface AccuracyTrend {
  date: string;
  accuracy: number;
}
