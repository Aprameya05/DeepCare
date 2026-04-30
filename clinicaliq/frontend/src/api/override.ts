import client from './client';

export const overrideApi = {
  submit: async (visitId: string, overrideData: any) => {
    const res = await client.post(`/doctor/override/${visitId}`, {
      doctor_id: 'frontend-doctor',
      confirmed_disease: overrideData.alternative_diagnosis,
      confirmed_tests: overrideData.confirmed_tests || [],
      notes: overrideData.reason || '',
    });
    return res.data;
  }
};
