import { StatsCards } from '@/components/dashboard/StatsCards';
import { DiseaseDistributionChart } from '@/components/dashboard/DiseaseDistributionChart';
import { AccuracyTrendChart } from '@/components/dashboard/AccuracyTrendChart';
import { PendingTestsList } from '@/components/dashboard/PendingTestsList';
import { HighBurdenCases } from '@/components/dashboard/HighBurdenCases';
import { RecentOverrides } from '@/components/dashboard/RecentOverrides';

export default function AccuracyDashboardPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold tracking-tight">System Accuracy & Dashboard</h1>
      </div>

      <StatsCards />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <AccuracyTrendChart />
        <DiseaseDistributionChart />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <RecentOverrides />
        <PendingTestsList />
        <HighBurdenCases />
      </div>
    </div>
  );
}
