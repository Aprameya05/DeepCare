import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  Clock3,
  FileText,
  Pill,
  Stethoscope,
  TrendingUp,
} from 'lucide-react';
import { generateScenario, getCurriculumScenarios } from '../data/scenarioGenerator';
import {
  buildRecommendation,
  CPOEnv,
  totalReward,
  type CPOActionType,
  type CPORecommendation,
  type CPORewardBreakdown,
  type CPOState,
  type CurriculumLevel,
  type PatientScenario,
} from '../env/CPOEnv';
import { RewardChart } from '../components/RewardChart';

interface CPOLayoutProps {
  title: string;
  subtitle: string;
  children: ReactNode;
}

const ZERO_REWARD: CPORewardBreakdown = {
  accuracy_gain: 0,
  time_cost: 0,
  financial_cost: 0,
  burden: 0,
};

const RECOMMENDATION_DETAIL: Record<CPOActionType, string> = {
  OrderTest: 'High-yield diagnostic test bundle',
  Prescribe: 'Targeted therapy based on current evidence',
  Refer: 'Specialist consult for advanced workup',
  Escalate: 'Critical care escalation for instability',
  Wait: 'Observe and reassess with serial monitoring',
};

const ACTION_ICON: Record<CPOActionType, ReactNode> = {
  OrderTest: <FileText className="w-5 h-5 text-cyan-300" />,
  Prescribe: <Pill className="w-5 h-5 text-green-300" />,
  Refer: <ArrowRight className="w-5 h-5 text-blue-300" />,
  Escalate: <AlertTriangle className="w-5 h-5 text-red-300" />,
  Wait: <Clock3 className="w-5 h-5 text-yellow-300" />,
};

const levelBadgeClass: Record<CurriculumLevel, string> = {
  simple: 'border-green-500/40 bg-green-500/10 text-green-300',
  moderate: 'border-yellow-500/40 bg-yellow-500/10 text-yellow-300',
  complex: 'border-red-500/40 bg-red-500/10 text-red-300',
};

const labBadgeClass = (value: number | string): string => {
  if (typeof value !== 'number') return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-200';
  if (value >= 200) return 'bg-red-500/10 border-red-500/30 text-red-300';
  if (value >= 80) return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300';
  return 'bg-green-500/10 border-green-500/30 text-green-300';
};

const vitalTone = (label: string, value: string | number): string => {
  if (label === 'SpO2' && typeof value === 'number') {
    if (value < 90) return 'bg-red-500/10 border-red-500/30 text-red-300';
    if (value < 95) return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300';
    return 'bg-green-500/10 border-green-500/30 text-green-300';
  }
  if (label === 'HR' && typeof value === 'number') {
    if (value > 120 || value < 50) return 'bg-red-500/10 border-red-500/30 text-red-300';
    if (value > 100) return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300';
    return 'bg-green-500/10 border-green-500/30 text-green-300';
  }
  if (label === 'Temp' && typeof value === 'number') {
    if (value > 39 || value < 35) return 'bg-red-500/10 border-red-500/30 text-red-300';
    if (value > 37.5) return 'bg-yellow-500/10 border-yellow-500/30 text-yellow-300';
    return 'bg-green-500/10 border-green-500/30 text-green-300';
  }
  return 'bg-cyan-500/10 border-cyan-500/30 text-cyan-200';
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function RewardDonut({ breakdown }: { breakdown: CPORewardBreakdown }) {
  const segments = [
    { key: 'accuracy_gain', color: '#4ade80', value: Math.abs(breakdown.accuracy_gain) },
    { key: 'time_cost', color: '#f87171', value: Math.abs(breakdown.time_cost) },
    { key: 'financial_cost', color: '#fb7185', value: Math.abs(breakdown.financial_cost) },
    { key: 'burden', color: '#f43f5e', value: Math.abs(breakdown.burden) },
  ];
  const total = segments.reduce((sum, item) => sum + item.value, 0);
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;

  return (
    <svg viewBox="0 0 72 72" className="h-36 w-36">
      <circle cx="36" cy="36" r={radius} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="10" />
      {segments.map((segment) => {
        const fraction = total === 0 ? 0 : segment.value / total;
        const dash = fraction * circumference;
        const currentOffset = offset;
        offset += dash;
        return (
          <circle
            key={segment.key}
            cx="36"
            cy="36"
            r={radius}
            fill="none"
            stroke={segment.color}
            strokeWidth="10"
            strokeLinecap="butt"
            strokeDasharray={`${dash} ${circumference - dash}`}
            strokeDashoffset={-currentOffset}
            transform="rotate(-90 36 36)"
          />
        );
      })}
      <text x="36" y="34" textAnchor="middle" className="fill-gray-300 text-[9px] tracking-wide">
        STEP
      </text>
      <text x="36" y="44" textAnchor="middle" className="fill-white text-[10px] font-semibold">
        {totalReward(breakdown).toFixed(2)}
      </text>
    </svg>
  );
}

export const CPOLayout = ({ title, subtitle, children }: CPOLayoutProps) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold text-white flex items-center gap-3">
          <Brain className="w-9 h-9 text-cyan-400" />
          {title}
        </h1>
        <p className="mt-3 text-gray-400 max-w-3xl">{subtitle}</p>
      </div>
      {children}
    </div>
  );
};

export const CPO = () => {
  const [selectedLevel, setSelectedLevel] = useState<CurriculumLevel>('simple');
  const scenarioOptions = useMemo(() => getCurriculumScenarios(selectedLevel), [selectedLevel]);
  const [scenario, setScenario] = useState<PatientScenario>(() => generateScenario('simple'));
  const envRef = useRef(new CPOEnv());
  const [state, setState] = useState<CPOState>(() => envRef.current.reset(scenario));
  const [recommendation, setRecommendation] = useState<CPORecommendation | null>(null);
  const [latestBreakdown, setLatestBreakdown] = useState<CPORewardBreakdown>(ZERO_REWARD);
  const [cumulativeReward, setCumulativeReward] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [episodeDone, setEpisodeDone] = useState(false);
  const [doneLabel, setDoneLabel] = useState('');

  const fetchRecommendation = async (currentState: CPOState, currentScenario: PatientScenario) => {
    setIsLoading(true);
    await sleep(700);
    const nextAction = currentScenario.optimalActionSequence[currentState.stepCount] ?? 'Wait';
    const rec = buildRecommendation(
      nextAction,
      RECOMMENDATION_DETAIL[nextAction],
      `State trend: ${currentState.currentAssessment} Prioritize ${nextAction} to improve expected reward while respecting budget and step limits.`
    );
    setRecommendation(rec);
    setIsLoading(false);
  };

  const resetEpisode = (nextScenario: PatientScenario) => {
    const resetState = envRef.current.reset(nextScenario);
    setState(resetState);
    setRecommendation(null);
    setLatestBreakdown(ZERO_REWARD);
    setCumulativeReward(0);
    setEpisodeDone(false);
    setDoneLabel('');
    void fetchRecommendation(resetState, nextScenario);
  };

  useEffect(() => {
    resetEpisode(scenario);
  }, [scenario]);

  const handleStep = async () => {
    if (!recommendation || episodeDone) return;
    setIsLoading(true);
    await sleep(400);
    const result = envRef.current.step({
      type: recommendation.action,
      detail: recommendation.specific_detail,
      outcome: state.currentAssessment,
    });
    setState(result.nextState);
    setLatestBreakdown(result.reward_breakdown);
    setCumulativeReward((prev) => Number((prev + result.reward).toFixed(3)));
    setEpisodeDone(result.done);
    if (result.done) {
      setDoneLabel(result.diagnosisReached ? 'Diagnosis Reached ✓' : 'Max Steps Exceeded ✗');
      setRecommendation(null);
      setIsLoading(false);
      return;
    }
    await fetchRecommendation(result.nextState, scenario);
  };

  const vitals = [
    { label: 'BP', value: state.vitals.bp },
    { label: 'HR', value: state.vitals.hr },
    { label: 'Temp', value: state.vitals.temp },
    { label: 'SpO2', value: state.vitals.spo2 },
  ];

  return (
    <CPOLayout
      title="Clinical Pathway Optimizer"
      subtitle="Split-panel CPO workspace: patient context, action timeline, and agent recommendations with reward intelligence."
    >
      <div className="mb-6 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-300">Curriculum</label>
          <select
            value={selectedLevel}
            onChange={(e) => {
              const nextLevel = e.target.value as CurriculumLevel;
              setSelectedLevel(nextLevel);
              setScenario(generateScenario(nextLevel));
            }}
            className="bg-deepnavy border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/50"
          >
            <option value="simple">Simple</option>
            <option value="moderate">Moderate</option>
            <option value="complex">Complex</option>
          </select>
        </div>
        <div className="flex flex-wrap gap-2">
          {scenarioOptions.map((item) => (
            <button
              key={item.id}
              onClick={() => setScenario(item)}
              className={`rounded-full border px-3 py-1 text-xs transition-colors ${
                scenario.id === item.id
                  ? 'border-cyan-400/60 bg-cyan-500/20 text-cyan-200'
                  : levelBadgeClass[item.level]
              }`}
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col xl:flex-row gap-6">
        <section className="glass-panel rounded-2xl p-5 xl:w-1/3 space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-cyan-400" />
            Patient State
          </h2>
          <div className="rounded-xl border border-white/10 bg-black/20 p-3 text-sm text-gray-300">
            {state.demographics.age}
            {state.demographics.sex}, {state.demographics.weight}kg
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Vitals</p>
            <div className="flex flex-wrap gap-2">
              {vitals.map((vital) => (
                <span
                  key={vital.label}
                  className={`rounded-full border px-2.5 py-1 text-xs ${vitalTone(vital.label, vital.value)}`}
                >
                  {vital.label}: {vital.value}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Symptoms</p>
            <div className="flex flex-wrap gap-2">
              {state.symptoms.map((symptom) => (
                <span
                  key={symptom}
                  className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2.5 py-1 text-xs text-purple-200"
                >
                  {symptom}
                </span>
              ))}
            </div>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-gray-500 mb-2">Labs</p>
            <div className="flex flex-wrap gap-2">
              {Object.entries(state.labResults).map(([name, value]) => (
                <span key={name} className={`rounded-full border px-2.5 py-1 text-xs ${labBadgeClass(value)}`}>
                  {name}: {value}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="glass-panel rounded-2xl p-5 xl:w-1/3">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Action Timeline
          </h2>
          <div className="space-y-5">
            {state.actionHistory.length === 0 && (
              <div className="rounded-xl border border-dashed border-white/15 px-4 py-6 text-center text-sm text-gray-500">
                No actions yet. Run the first recommendation.
              </div>
            )}
            {state.actionHistory.map((entry, index) => (
              <div key={`${entry.action.type}-${index}`} className="relative pl-8">
                {index < state.actionHistory.length - 1 && (
                  <span className="absolute left-[0.6rem] top-4 h-full w-px bg-white/15" />
                )}
                <span className="absolute left-0 top-1.5 h-3 w-3 rounded-full bg-cyan-400" />
                <p className="text-sm font-medium text-white">
                  Step {index + 1}: {entry.action.type}
                </p>
                <p className="text-xs text-gray-400">{entry.action.detail}</p>
                <p className={entry.reward >= 0 ? 'text-xs text-green-300 mt-1' : 'text-xs text-red-300 mt-1'}>
                  Reward: {entry.reward >= 0 ? '+' : ''}
                  {entry.reward.toFixed(3)}
                </p>
              </div>
            ))}
          </div>
        </section>

        <section className="glass-panel rounded-2xl p-5 xl:w-1/3 space-y-4">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Brain className="w-5 h-5 text-cyan-400" />
            Agent Recommendation
          </h2>
          {isLoading ? (
            <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/10 p-4 flex items-center gap-3 text-cyan-200">
              <Activity className="w-4 h-4 animate-spin" />
              <span className="text-sm">Agent is evaluating next step...</span>
            </div>
          ) : recommendation ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-white/10 bg-black/20 p-4">
                <div className="flex items-center gap-2 text-cyan-200 text-sm">
                  {ACTION_ICON[recommendation.action]}
                  {recommendation.actionLabel}
                </div>
                <p className="mt-2 text-sm text-gray-200">{recommendation.specific_detail}</p>
                <p className="mt-3 text-xs text-gray-400">{recommendation.reasoning}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-black/20 p-4 flex items-center justify-between">
                <RewardDonut breakdown={recommendation.reward_breakdown} />
                <div className="text-xs text-gray-400 space-y-1">
                  <p className="text-green-300">Accuracy {recommendation.reward_breakdown.accuracy_gain.toFixed(2)}</p>
                  <p className="text-red-300">Time {recommendation.reward_breakdown.time_cost.toFixed(2)}</p>
                  <p className="text-red-300">Cost {recommendation.reward_breakdown.financial_cost.toFixed(2)}</p>
                  <p className="text-red-300">Burden {recommendation.reward_breakdown.burden.toFixed(2)}</p>
                </div>
              </div>
              <button
                onClick={handleStep}
                className="w-full rounded-xl border border-cyan-500/50 bg-cyan-500/15 px-4 py-2 text-sm font-medium text-cyan-200 hover:bg-cyan-500/25 transition-colors"
              >
                Apply Recommended Action
              </button>
            </div>
          ) : (
            <div className="rounded-xl border border-white/10 bg-black/20 p-4 text-sm text-gray-400">
              Recommendation unavailable.
            </div>
          )}

          <RewardChart metrics={latestBreakdown} />

          <div className="rounded-xl border border-white/10 bg-black/20 p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-400">Cumulative Reward</span>
              <span className={cumulativeReward >= 0 ? 'text-green-300 font-mono' : 'text-red-300 font-mono'}>
                {cumulativeReward >= 0 ? '+' : ''}
                {cumulativeReward.toFixed(3)}
              </span>
            </div>
            <p className="mt-2 text-xs text-gray-500">{state.currentAssessment}</p>
            {episodeDone && (
              <div className="mt-3 inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200">
                <CheckCircle2 className="w-3.5 h-3.5" />
                {doneLabel}
              </div>
            )}
            <button
              onClick={() => resetEpisode(scenario)}
              className="mt-4 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-gray-200 hover:bg-white/10 transition-colors"
            >
              Reset Episode
            </button>
          </div>
        </section>
      </div>
    </CPOLayout>
  );
};
