import client from './client';
import { Visit, VisitCreate } from './types';

export const visitsApi = {
  create: async (data: VisitCreate) => {
    const res = await client.post<Visit>('/visits/', data);
    return res.data;
  },
  get: async (id: string) => {
    const res = await client.get<Visit>(`/visits/${id}`);
    return res.data;
  }
};
