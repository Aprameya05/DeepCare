import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/dashboard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, ActivitySquare, TrendingUp, TestTube } from 'lucide-react';

export function StatsCards() {
  const { data: stats } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
  });

  if (!stats) return null;

  const items = [
    { title: 'Total Patients', value: stats.total_patients, icon: Users, color: 'text-blue-500' },
    { title: 'Active Visits', value: stats.active_visits, icon: ActivitySquare, color: 'text-green-500' },
    { title: 'Model Accuracy', value: `${stats.average_accuracy}%`, icon: TrendingUp, color: 'text-amber-500' },
    { title: 'Pending Tests', value: stats.pending_tests, icon: TestTube, color: 'text-purple-500' },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {items.map((item, idx) => {
        const Icon = item.icon;
        return (
          <Card key={idx}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-500">{item.title}</CardTitle>
              <Icon className={`w-4 h-4 ${item.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{item.value}</div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
