import client from './client';

export const reportsApi = {
  generate: async (visitId: string) => {
    const res = await client.post(`/reports/generate`, { visit_id: visitId });
    return res.data;
  },
  download: async (visitId: string) => {
    const res = await client.get(`/reports/${visitId}/download`, { responseType: 'blob' });
    return res.data;
  }
};
