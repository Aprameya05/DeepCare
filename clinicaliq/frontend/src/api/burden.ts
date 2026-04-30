import client from './client';
import { BurdenResponse } from './types';

export const burdenApi = {
  calculate: async (visitId: string) => {
    const res = await client.post<BurdenResponse>(`/calculate/burden`, { visit_id: visitId });
    return res.data;
  }
};
