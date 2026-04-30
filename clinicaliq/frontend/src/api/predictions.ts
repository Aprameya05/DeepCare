import client from './client';
import { PredictResponse } from './types';

export const predictionsApi = {
  getPrediction: async (visitId: string) => {
    const res = await client.post<PredictResponse>(`/predict/disease-ranking`, { visit_id: visitId });
    return res.data;
  }
};
