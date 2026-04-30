import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function HighBurdenCases() {
  const { data } = useQuery({
    queryKey: ['dashboard', 'high-burden'],
    queryFn: dashboardApi.getHighBurdenCases,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">High Burden Cases</CardTitle>
      </CardHeader>
      <CardContent>
        {data?.length === 0 ? (
          <p className="text-sm text-slate-500">No high burden cases.</p>
        ) : (
          <div className="space-y-4">
            {data?.map((caseItem: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center border-b pb-3 last:border-0 last:pb-0">
                <div>
                  <p className="font-medium">{caseItem.patient_name}</p>
                  <p className="text-xs text-slate-500">Est. Cost: ${caseItem.net_cost.toFixed(2)}</p>
                </div>
                <Badge className="bg-red-500 text-white">Score: {caseItem.score.toFixed(1)}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
