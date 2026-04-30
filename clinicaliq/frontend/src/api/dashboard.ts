import client from './client';
import { DashboardStats } from './types';

export const dashboardApi = {
  getStats: async () => {
    const res = await client.get<DashboardStats>(`/dashboard/stats`);
    return res.data;
  },
  getDiseaseDistribution: async () => {
    const res = await client.get(`/dashboard/disease-distribution`);
    return res.data;
  },
  getPendingTests: async () => {
    const res = await client.get(`/dashboard/pending-tests`);
    return res.data;
  },
  getHighBurdenCases: async () => {
    const res = await client.get(`/dashboard/high-burden`);
    return res.data;
  },
  getRecentOverrides: async () => {
    const res = await client.get(`/dashboard/recent-overrides`);
    return res.data;
  }
};
