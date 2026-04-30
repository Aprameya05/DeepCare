import client from './client';
import { TestRecommendation } from './types';

export const recommendationsApi = {
  getTests: async (visitId: string) => {
    const res = await client.post<TestRecommendation[]>(`/recommend/tests`, { visit_id: visitId });
    return res.data;
  }
};
