import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

export function RecentOverrides() {
  const { data } = useQuery({
    queryKey: ['dashboard', 'recent-overrides'],
    queryFn: dashboardApi.getRecentOverrides,
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Recent Doctor Overrides</CardTitle>
      </CardHeader>
      <CardContent>
        {data?.length === 0 ? (
          <p className="text-sm text-slate-500">No recent overrides.</p>
        ) : (
          <div className="space-y-4">
            {data?.map((item: any, idx: number) => (
              <div key={idx} className="border-b pb-3 last:border-0 last:pb-0">
                <div className="flex justify-between items-start mb-1">
                  <p className="font-medium text-sm">Corrected: {item.alternative_diagnosis}</p>
                  <span className="text-xs text-slate-400 whitespace-nowrap ml-2">
                    {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                  </span>
                </div>
                <div className="flex gap-2 items-center mt-1">
                  <Badge variant="outline" className="text-xs line-through text-slate-400">
                    {item.original_prediction}
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 mt-2 italic">"{item.reason}"</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
