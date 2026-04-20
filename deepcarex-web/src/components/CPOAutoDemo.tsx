import { useEffect, useRef, useState } from 'react';
import { Activity, CheckCircle2, Pause, Play, RotateCcw, XCircle } from 'lucide-react';
import { generateScenario } from '../data/scenarioGenerator';
import {
  buildRecommendation,
  CPOEnv,
  type CPORecommendation,
  type CPORewardBreakdown,
  type CPOState,
  type CurriculumLevel,
  type PatientScenario,
} from '../env/CPOEnv';
import { RewardChart } from './RewardChart';

const ZERO_REWARD: CPORewardBreakdown = {
  accuracy_gain: 0,
  time_cost: 0,
  financial_cost: 0,
  burden: 0,
};

const DETAIL_COPY: Record<CPORecommendation['action'], string> = {
  OrderTest: 'Collect discriminative diagnostics to narrow differential.',
  Prescribe: 'Initiate therapy aligned with current findings.',
  Refer: 'Escalate to specialist pathway for precision management.',
  Escalate: 'Immediate critical escalation due to instability.',
  Wait: 'Observe trajectory and reassess with latest signals.',
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

export const CPOAutoDemo = () => {
  const envRef = useRef(new CPOEnv());
  const [level, setLevel] = useState<CurriculumLevel>('simple');
  const [scenario, setScenario] = useState<PatientScenario | null>(null);
  const [state, setState] = useState<CPOState | null>(null);
  const [recommendation, setRecommendation] = useState<CPORecommendation | null>(null);
  const [stepReward, setStepReward] = useState<CPORewardBreakdown>(ZERO_REWARD);
  const [cumulativeReward, setCumulativeReward] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isUpdatingState, setIsUpdatingState] = useState(false);
  const [episodeEnd, setEpisodeEnd] = useState<'success' | 'failed' | null>(null);

  const pauseRef = useRef(false);
  const runningRef = useRef(false);

  useEffect(() => {
    pauseRef.current = isPaused;
  }, [isPaused]);

  useEffect(() => {
    runningRef.current = isRunning;
  }, [isRunning]);

  const resetDemo = () => {
    setIsRunning(false);
    setIsPaused(false);
    setIsThinking(false);
    setIsUpdatingState(false);
    setScenario(null);
    setState(null);
    setRecommendation(null);
    setStepReward(ZERO_REWARD);
    setCumulativeReward(0);
    setEpisodeEnd(null);
  };

  const createRecommendation = (currentState: CPOState, currentScenario: PatientScenario): CPORecommendation => {
    const action = currentScenario.optimalActionSequence[currentState.stepCount] ?? 'Wait';
    return buildRecommendation(
      action,
      DETAIL_COPY[action],
      `Step ${currentState.stepCount + 1}: maximize reward while controlling time and financial penalties.`
    );
  };

  const runDemo = async () => {
    const seededScenario = generateScenario(level);
    const initialState = envRef.current.reset(seededScenario);
    setScenario(seededScenario);
    setState(initialState);
    setRecommendation(null);
    setStepReward(ZERO_REWARD);
    setCumulativeReward(0);
    setEpisodeEnd(null);
    setIsRunning(true);
    setIsPaused(false);

    let localState = initialState;
    while (runningRef.current) {
      if (pauseRef.current) {
        await sleep(300);
        continue;
      }
      if (localState.stepCount >= localState.maxSteps) {
        setEpisodeEnd('failed');
        setIsRunning(false);
        break;
      }

      setIsUpdatingState(true);
      await sleep(450);
      setIsUpdatingState(false);

      if (pauseRef.current || !runningRef.current) continue;
      setIsThinking(true);
      await sleep(1500);
      setIsThinking(false);
      if (pauseRef.current || !runningRef.current) continue;

      const nextRecommendation = createRecommendation(localState, seededScenario);
      setRecommendation(nextRecommendation);

      const result = envRef.current.step({
        type: nextRecommendation.action,
        detail: nextRecommendation.specific_detail,
        outcome: localState.currentAssessment,
      });

      localState = result.nextState;
      setState(result.nextState);
      setStepReward(result.reward_breakdown);
      setCumulativeReward((prev) => Number((prev + result.reward).toFixed(3)));

      if (result.done) {
        setEpisodeEnd(result.diagnosisReached ? 'success' : 'failed');
        setIsRunning(false);
        break;
      }

      await sleep(1500);
    }
  };

  const rewardProgress = Math.max(0, Math.min(100, Math.round((cumulativeReward + 2) * 20)));

  return (
    <div className="space-y-6">
      <div className="glass-panel rounded-2xl p-5">
        <div className="flex flex-col md:flex-row md:items-center gap-3">
          <select
            value={level}
            onChange={(event) => setLevel(event.target.value as CurriculumLevel)}
            className="bg-deepnavy border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-400/40"
            disabled={isRunning}
          >
            <option value="simple">Simple</option>
            <option value="moderate">Moderate</option>
            <option value="complex">Complex</option>
          </select>
          <button
            onClick={runDemo}
            disabled={isRunning}
            className="rounded-lg border border-cyan-500/50 bg-cyan-500/15 px-4 py-2 text-sm text-cyan-200 hover:bg-cyan-500/25 disabled:opacity-60"
          >
            Run Demo
          </button>
          <div className="ml-0 md:ml-auto flex gap-2">
            <button
              onClick={() => setIsPaused(true)}
              disabled={!isRunning || isPaused}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-gray-200 disabled:opacity-50"
            >
              <Pause className="w-3.5 h-3.5" />
              Pause
            </button>
            <button
              onClick={() => setIsPaused(false)}
              disabled={!isRunning || !isPaused}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-gray-200 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5" />
              Resume
            </button>
            <button
              onClick={resetDemo}
              className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs text-gray-200"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`glass-panel rounded-2xl p-5 transition-all ${isUpdatingState ? 'ring-2 ring-cyan-400/40' : ''}`}>
          <h3 className="text-sm text-gray-400 mb-3">Patient State</h3>
          {state ? (
            <div className="space-y-2 text-sm">
              <p className="text-white">{state.demographics.age}{state.demographics.sex}, {state.demographics.weight}kg</p>
              <p className="text-gray-300">BP {state.vitals.bp} | HR {state.vitals.hr} | Temp {state.vitals.temp} | SpO2 {state.vitals.spo2}</p>
              <div className="flex flex-wrap gap-2">
                {state.symptoms.map((symptom) => (
                  <span key={symptom} className="rounded-full border border-purple-500/30 bg-purple-500/10 px-2 py-1 text-xs text-purple-200">
                    {symptom}
                  </span>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Run demo to initialize scenario.</p>
          )}
        </div>

        <div className="glass-panel rounded-2xl p-5">
          <h3 className="text-sm text-gray-400 mb-3">Playback</h3>
          {isThinking ? (
            <div className="rounded-xl border border-cyan-500/25 bg-cyan-500/10 p-4 flex items-center gap-2 text-cyan-200 text-sm">
              <Activity className="w-4 h-4 animate-spin" />
              Agent thinking...
            </div>
          ) : recommendation ? (
            <div className="rounded-xl border border-white/10 bg-black/20 p-4 space-y-2">
              <p className="text-cyan-200 text-sm">{recommendation.actionLabel}</p>
              <p className="text-white text-sm">{recommendation.specific_detail}</p>
              <p className="text-gray-400 text-xs">{recommendation.reasoning}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">Awaiting first recommendation.</p>
          )}
        </div>

        <div className="glass-panel rounded-2xl p-5 space-y-4">
          <h3 className="text-sm text-gray-400">Cumulative Reward</h3>
          <div className="h-2 rounded-full bg-white/10 overflow-hidden">
            <div
              className={`h-2 rounded-full transition-all duration-500 ${cumulativeReward >= 0 ? 'bg-green-400' : 'bg-red-400'} ${
                rewardProgress >= 90
                  ? 'w-11/12'
                  : rewardProgress >= 75
                    ? 'w-9/12'
                    : rewardProgress >= 60
                      ? 'w-7/12'
                      : rewardProgress >= 40
                        ? 'w-5/12'
                        : rewardProgress >= 20
                          ? 'w-3/12'
                          : rewardProgress > 0
                            ? 'w-1/12'
                            : 'w-0'
              }`}
            />
          </div>
          <p className={cumulativeReward >= 0 ? 'text-sm text-green-300 font-mono' : 'text-sm text-red-300 font-mono'}>
            {cumulativeReward >= 0 ? '+' : ''}
            {cumulativeReward.toFixed(3)}
          </p>

          <RewardChart metrics={stepReward} />

          {episodeEnd && (
            <div
              className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${
                episodeEnd === 'success'
                  ? 'border-green-500/40 bg-green-500/10 text-green-200'
                  : 'border-red-500/40 bg-red-500/10 text-red-200'
              }`}
            >
              {episodeEnd === 'success' ? <CheckCircle2 className="w-3.5 h-3.5" /> : <XCircle className="w-3.5 h-3.5" />}
              {episodeEnd === 'success' ? 'Diagnosis Reached ✓' : 'Max Steps Exceeded ✗'}
            </div>
          )}
        </div>
      </div>

      {scenario && (
        <div className="glass-panel rounded-2xl p-4 text-xs text-gray-400">
          Scenario: <span className="text-white">{scenario.name}</span> | Ground truth:{' '}
          <span className="text-cyan-200">{scenario.groundTruthDiagnosis}</span> | Steps used:{' '}
          <span className="text-white">{state?.stepCount ?? 0}</span> / {scenario.maxSteps}
        </div>
      )}
    </div>
  );
};
