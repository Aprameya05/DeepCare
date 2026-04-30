import client from './client';
import { TestRecommendation } from './types';

export const recommendationsApi = {
  getTests: async (visitId: string) => {
    const res = await client.post<any>(`/recommend/tests/${visitId}`);
    return (res.data.recommendations || []).map((item: any) => ({
      test_name: item.test_name,
      priority: item.priority,
      reason: item.recommendation_reason || item.clinical_reason || '',
    })) as TestRecommendation[];
  }
};
