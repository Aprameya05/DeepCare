import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { TestRecommendation } from '@/api/types';

interface TestRecommendationListProps {
  recommendations: TestRecommendation[];
}

export function TestRecommendationList({ recommendations }: TestRecommendationListProps) {
  // Group by priority
  const p1 = recommendations.filter(r => r.priority === 1);
  const p2 = recommendations.filter(r => r.priority === 2);
  const p3 = recommendations.filter(r => r.priority === 3);

  const renderGroup = (title: string, tests: TestRecommendation[], badgeColor: string) => {
    if (tests.length === 0) return null;
    return (
      <div className="mb-4 last:mb-0">
        <h4 className="font-semibold text-sm text-slate-500 mb-2">{title}</h4>
        <div className="space-y-2">
          {tests.map((test, idx) => (
            <div key={idx} className="p-3 border rounded-md flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Badge className={badgeColor}>P{test.priority}</Badge>
                <span className="font-medium">{test.test_name}</span>
              </div>
              <span className="text-sm text-slate-600 dark:text-slate-400">{test.reason}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Recommended Tests</CardTitle>
      </CardHeader>
      <CardContent>
        {renderGroup("Priority 1 (Critical)", p1, "bg-red-500")}
        {renderGroup("Priority 2 (Important)", p2, "bg-amber-500")}
        {renderGroup("Priority 3 (Optional/Routine)", p3, "bg-blue-500")}
        {recommendations.length === 0 && <p className="text-slate-500">No tests recommended.</p>}
      </CardContent>
    </Card>
  );
}
