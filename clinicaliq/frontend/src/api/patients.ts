import client from './client';
import { Patient, PatientCreate, Visit } from './types';

export const patientsApi = {
  list: async () => {
    const res = await client.get<Patient[]>('/patients/');
    return res.data;
  },
  search: async (q: string) => {
    const res = await client.get<Patient[]>(`/patients/search?q=${encodeURIComponent(q)}`);
    return res.data;
  },
  get: async (id: string) => {
    const res = await client.get<Patient>(`/patients/${id}`);
    return res.data;
  },
  create: async (data: PatientCreate) => {
    const res = await client.post<Patient>('/patients/', data);
    return res.data;
  },
  getVisits: async (id: string) => {
    const res = await client.get<Visit[]>(`/patients/${id}/visits`);
    return res.data;
  }
};
