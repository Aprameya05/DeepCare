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
