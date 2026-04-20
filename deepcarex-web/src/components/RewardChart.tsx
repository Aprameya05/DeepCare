import type { CPORewardBreakdown } from '../env/CPOEnv';

interface RewardChartProps {
  metrics: CPORewardBreakdown;
}

function barWidthClass(value: number): string {
  const magnitude = Math.min(Math.abs(value), 1);
  if (magnitude === 0) return 'w-0';
  if (magnitude <= 0.12) return 'w-1/12';
  if (magnitude <= 0.2) return 'w-2/12';
  if (magnitude <= 0.28) return 'w-3/12';
  if (magnitude <= 0.36) return 'w-4/12';
  if (magnitude <= 0.44) return 'w-5/12';
  if (magnitude <= 0.52) return 'w-6/12';
  if (magnitude <= 0.6) return 'w-7/12';
  if (magnitude <= 0.68) return 'w-8/12';
  if (magnitude <= 0.76) return 'w-9/12';
  if (magnitude <= 0.84) return 'w-10/12';
  if (magnitude <= 0.92) return 'w-11/12';
  return 'w-full';
}

const METRIC_ROWS: Array<{ key: keyof CPORewardBreakdown; label: string }> = [
  { key: 'accuracy_gain', label: 'Accuracy Gain' },
  { key: 'time_cost', label: 'Time Cost' },
  { key: 'financial_cost', label: 'Financial Cost' },
  { key: 'burden', label: 'Burden' },
];

export const RewardChart = ({ metrics }: RewardChartProps) => {
  return (
    <div className="glass-panel rounded-2xl p-4">
      <h3 className="text-sm font-semibold tracking-wide text-gray-200 mb-4">Reward Dashboard</h3>
      <div className="space-y-3">
        {METRIC_ROWS.map((row) => {
          const value = metrics[row.key];
          const positive = value >= 0;
          return (
            <div key={row.key}>
              <div className="mb-1 flex items-center justify-between text-xs">
                <span className="text-gray-400">{row.label}</span>
                <span className={positive ? 'text-green-300 font-mono' : 'text-red-300 font-mono'}>
                  {positive ? '+' : ''}
                  {value.toFixed(2)}
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${barWidthClass(value)} ${
                    positive ? 'bg-green-400' : 'bg-red-400'
                  }`}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
