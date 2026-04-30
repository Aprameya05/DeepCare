import client from './client';
import { AccuracyTrend } from './types';

export const accuracyApi = {
  getTrend: async () => {
    const res = await client.get<AccuracyTrend[]>(`/accuracy/trend`);
    return res.data;
  }
};
