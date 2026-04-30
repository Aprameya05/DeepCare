import client from './client';
import { PredictResponse } from './types';

export const predictionsApi = {
  getPrediction: async (visitId: string) => {
    const res = await client.post<any>(`/predict/disease-ranking/${visitId}`);
    return {
      predictions: (res.data.predictions || []).map((prediction: any) => ({
        disease: prediction.disease || prediction.disease_name,
        confidence: prediction.confidence_percent ?? Math.round((prediction.confidence || 0) * 100),
        pubmed_evidence: (prediction.pubmed_evidence || []).map((ref: any) =>
          typeof ref === 'string' ? ref : (ref.title || ref.pmid || 'Clinical reference')
        ),
      })),
      uncertainty_flags: res.data.uncertainty_flags || [],
    } satisfies PredictResponse;
  }
};
