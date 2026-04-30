import client from './client';

export const overrideApi = {
  submit: async (visitId: string, overrideData: any) => {
    const res = await client.post(`/override/`, { visit_id: visitId, ...overrideData });
    return res.data;
  }
};
