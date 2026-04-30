import client from './client';
import { BurdenResponse } from './types';

export const burdenApi = {
  calculate: async (visitId: string) => {
    const res = await client.post<any>(`/calculate/burden/${visitId}?country=US&insurance_coverage=0.8`);
    const total = res.data.ordering?.total_estimated_cost_usd || 0;
    const coverage = res.data.insurance_coverage || 0;
    const rawCost = coverage ? total / Math.max(1 - coverage, 0.01) : total;
    return {
      level: res.data.burden_result.category,
      score: res.data.burden_result.normalized_score,
      uncertainty_flags: res.data.ordering?.uncertainty_flags || [],
      cost_breakdown: {
        raw_cost: rawCost,
        insurance_reduction: rawCost - total,
        net_cost: total,
      },
    } satisfies BurdenResponse;
  }
};
