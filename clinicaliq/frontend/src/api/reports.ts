import client from './client';

export const reportsApi = {
  generate: async (visitId: string) => {
    const res = await client.post(`/reports/generate/${visitId}?country=US&insurance_coverage=0.8`);
    return res.data;
  },
  download: async (visitId: string) => {
    const res = await client.get(`/reports/${visitId}`, { responseType: 'blob' });
    return res.data;
  }
};
