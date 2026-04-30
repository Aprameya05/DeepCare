import client from './client';
import { VitalsCreate } from './types';

export const vitalsApi = {
  create: async (data: VitalsCreate) => {
    const res = await client.post('/vitals/', data);
    return res.data;
  }
};
