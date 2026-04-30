import client from './client';
import { SymptomQuestion } from './types';

export const symptomsApi = {
  getQuestions: async (gender?: string, symptoms?: string[]) => {
    const params = new URLSearchParams();
    if (gender) params.append('gender', gender);
    if (symptoms && symptoms.length > 0) {
      symptoms.forEach(s => params.append('symptoms', s));
    }
    const res = await client.get<SymptomQuestion[]>(`/symptoms/questions?${params.toString()}`);
    return res.data;
  },
  submit: async (visitId: string, responses: any) => {
    const res = await client.post(`/visits/${visitId}/symptoms`, responses);
    return res.data;
  }
};
