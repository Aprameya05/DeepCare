import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BurdenResponse } from '@/api/types';

export function BurdenSummary({ burden }: { burden: BurdenResponse }) {
  const getLevelColor = (level: string) => {
    switch (level) {
      case 'Low': return 'text-green-600';
      case 'Medium': return 'text-amber-500';
      case 'High': return 'text-red-600';
      default: return 'text-slate-600';
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Financial Burden Analysis</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
          <div>
            <p className="text-sm text-slate-500">Burden Level</p>
            <p className={`text-2xl font-bold ${getLevelColor(burden.level)}`}>{burden.level}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-slate-500">Score</p>
            <p className="text-xl font-semibold">{burden.score.toFixed(1)} / 100</p>
          </div>
        </div>

        <div className="space-y-2 border-t pt-4">
          <h4 className="font-medium text-sm">Estimated Cost Breakdown</h4>
          <div className="flex justify-between text-sm">
            <span className="text-slate-500">Raw Estimated Cost:</span>
            <span>${burden.cost_breakdown.raw_cost.toFixed(2)}</span>
          </div>
          <div className="flex justify-between text-sm text-green-600">
            <span>Estimated Insurance Coverage:</span>
            <span>-${burden.cost_breakdown.insurance_reduction.toFixed(2)}</span>
          </div>
          <div className="flex justify-between font-bold text-base border-t pt-2 mt-2">
            <span>Estimated Out-of-Pocket Net Cost:</span>
            <span>${burden.cost_breakdown.net_cost.toFixed(2)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
