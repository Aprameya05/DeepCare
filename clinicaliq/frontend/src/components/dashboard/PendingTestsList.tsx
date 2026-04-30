import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export function PendingTestsList() {
  const { data } = useQuery({
    queryKey: ['dashboard', 'pending-tests'],
    queryFn: dashboardApi.getPendingTests,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Pending High Priority Tests</CardTitle>
      </CardHeader>
      <CardContent>
        {data?.length === 0 ? (
          <p className="text-sm text-slate-500">No pending tests.</p>
        ) : (
          <div className="space-y-4">
            {data?.map((test: any, idx: number) => (
              <div key={idx} className="flex justify-between items-center border-b pb-3 last:border-0 last:pb-0">
                <div>
                  <p className="font-medium">{test.test_name}</p>
                  <p className="text-xs text-slate-500">Patient: {test.patient_name}</p>
                </div>
                <Badge variant="destructive">P{test.priority}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
