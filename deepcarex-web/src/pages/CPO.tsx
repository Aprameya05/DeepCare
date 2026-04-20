import { useState, useEffect, useRef } from 'react';
import { runCPOPathway, runMetaOptimizedCPOPathway } from '../services/gemini';
import type { CPOActionResponse } from '../services/gemini';
import { CPOEnv } from '../env/CPOEnv';
import type { CPOState, CPOActionType } from '../env/CPOEnv';
import { getAllScenarios } from '../data/scenarioGenerator';
import type { PatientScenario } from '../data/scenarioGenerator';
import {
  Activity, ArrowRight, Brain, AlertTriangle, Stethoscope,
  Pill, FileText, ArrowUpCircle, Clock, ShieldCheck, ChevronRight,
  TrendingUp, Cpu,
} from 'lucide-react';

interface LogEntry {
  type: 'user' | 'agent';
  content: string | CPOActionResponse;
  stepReward?: number;
}

const ACTION_TYPE_MAP: Record<string, CPOActionType> = {
  'Order Test': 'OrderTest',
  'Prescribe': 'Prescribe',
  'Refer': 'Refer',
  'Escalate': 'Escalate',
  'Wait': 'Wait',
};

function stateToDisplayFields(state: CPOState) {
  return {
    demographics: `${state.demographics.age}${state.demographics.sex}, ${state.demographics.weight}kg`,
    symptoms: state.symptoms.join(', '),
  };
}

function buildCustomScenario(
  demographics: string,
  symptoms: string,
  priorResults: string
): PatientScenario {
  const ageMatch = demographics.match(/\d+/);
  const sexMatch = demographics.match(/\b([MFmf])\b/);
  return {
    id: 'custom',
    name: 'Custom Case',
    level: 'moderate',
    initialState: {
      demographics: {
        age: ageMatch ? parseInt(ageMatch[0]) : 40,
        sex: sexMatch ? sexMatch[1].toUpperCase() : 'U',
        weight: 70,
      },
      vitals: { bp: 'Unknown', hr: 0, temp: 0, spo2: 0 },
      symptoms: symptoms.split(/[,;]/).map(s => s.trim()).filter(Boolean),
      labResults: priorResults && priorResults !== 'None'
        ? { notes: priorResults }
        : {},
    },
    groundTruthDiagnosis: 'Unknown',
    optimalActionSequence: ['OrderTest', 'Prescribe', 'Refer', 'Wait', 'Wait'],
    maxSteps: 10,
    budgetCeiling: 3000,
    displayPriorResults: priorResults || 'None',
  };
}

export const CPO = () => {
  const [apiKey] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [demographics, setDemographics] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [priorResults, setPriorResults] = useState('');

  const [interactionLog, setInteractionLog] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [outcomeInput, setOutcomeInput] = useState('');
  const [cumulativeReward, setCumulativeReward] = useState(0);
  const [episodeDone, setEpisodeDone] = useState(false);
  const [useMetaOptimizer, setUseMetaOptimizer] = useState(true);

  const envRef = useRef(new CPOEnv());
  const cpoStateRef = useRef<CPOState | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const allScenarios = getAllScenarios();

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [interactionLog]);

  const loadScenario = (scenario: PatientScenario) => {
    const state = envRef.current.reset(scenario);
    cpoStateRef.current = state;
    const display = stateToDisplayFields(state);
    setDemographics(display.demographics);
    setSymptoms(display.symptoms);
    setPriorResults(scenario.displayPriorResults);
    setInteractionLog([]);
    setOutcomeInput('');
    setCumulativeReward(0);
    setEpisodeDone(false);
  };

  const fetchNextAction = async (state: CPOState, cumReward: number) => {
    setIsLoading(true);
    try {
      const response = useMetaOptimizer
        ? await runMetaOptimizedCPOPathway(apiKey, state, cumReward)
        : await runCPOPathway(apiKey, state, cumReward);
      setInteractionLog(prev => [...prev, { type: 'agent', content: response }]);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const startPathway = async () => {
    if (!demographics || !symptoms) {
      alert('Please fill in demographics and symptoms.');
      return;
    }

    const scenario = buildCustomScenario(demographics, symptoms, priorResults);
    const state = envRef.current.reset(scenario);
    cpoStateRef.current = state;
    setCumulativeReward(0);
    setEpisodeDone(false);

    setInteractionLog([{
      type: 'user',
      content: `Started pathway.\nDemographics: ${demographics}\nSymptoms: ${symptoms}\nPrior Results: ${priorResults || 'None'}`,
    }]);

    await fetchNextAction(state, 0);
  };

  const handleProvideOutcome = async () => {
    if (!outcomeInput.trim() || !cpoStateRef.current) return;

    const lastEntry = interactionLog[interactionLog.length - 1];
    if (lastEntry?.type !== 'agent') return;

    const actionData = lastEntry.content as CPOActionResponse;
    const actionType = ACTION_TYPE_MAP[actionData.action] ?? 'Wait';

    let stepReward = 0;
    let nextState = cpoStateRef.current;
    let done = false;

    try {
      const result = envRef.current.step({
        type: actionType,
        detail: actionData.specific_detail,
        outcome: outcomeInput,
      });
      nextState = result.nextState;
      stepReward = result.reward;
      done = result.done;
      cpoStateRef.current = nextState;
    } catch (err) {
      console.error('env.step error:', err);
    }

    const newCumReward = cumulativeReward + stepReward;
    setCumulativeReward(newCumReward);
    setEpisodeDone(done);

    // Annotate the last agent entry with its step reward
    setInteractionLog(prev =>
      prev.map((e, i) =>
        i === prev.length - 1 && e.type === 'agent'
          ? { ...e, stepReward }
          : e
      )
    );

    setInteractionLog(prev => [...prev, {
      type: 'user',
      content: `Outcome for ${actionData.action}: ${outcomeInput}`,
    }]);
    setOutcomeInput('');

    if (!done) {
      await fetchNextAction(nextState, newCumReward);
    } else {
      setInteractionLog(prev => [...prev, {
        type: 'agent',
        content: {
          action: 'Wait',
          specific_detail: 'Episode complete',
          reasoning: `Pathway concluded. Cumulative reward: ${newCumReward.toFixed(3)}`,
          expected_reward_impact: { accuracy: '—', cost: '—', time: '—', patient_burden: '—' },
        },
      }]);
    }
  };

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'Order Test': return <FileText className="w-5 h-5 text-cyan-400" />;
      case 'Prescribe': return <Pill className="w-5 h-5 text-green-400" />;
      case 'Refer': return <ArrowRight className="w-5 h-5 text-blue-400" />;
      case 'Escalate': return <AlertTriangle className="w-5 h-5 text-red-400" />;
      case 'Wait': return <Clock className="w-5 h-5 text-yellow-400" />;
      default: return <Brain className="w-5 h-5 text-cyan-400" />;
    }
  };

  const levelColor = (level: PatientScenario['level']) => ({
    simple: 'border-green-500/30 bg-green-500/10 text-green-300 hover:bg-green-500/20',
    moderate: 'border-yellow-500/30 bg-yellow-500/10 text-yellow-300 hover:bg-yellow-500/20',
    complex: 'border-red-500/30 bg-red-500/10 text-red-300 hover:bg-red-500/20',
  })[level];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
      <div className="mb-12">
        <h1 className="text-4xl font-bold text-white mb-4 flex items-center gap-3">
          <Brain className="w-10 h-10 text-cyan-400" />
          Clinical Pathway Optimizer (CPO)
        </h1>
        <p className="text-xl text-gray-400">
          Agent-driven decision making maximizing diagnostic accuracy while minimizing time, cost, and patient burden.
        </p>
        <div className="mt-4 inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-500/10 px-4 py-1.5 text-xs text-cyan-300">
          <Cpu className="w-4 h-4" />
          {useMetaOptimizer ? 'Meta Agent Optimizer Environment: Active' : 'Baseline Single-Agent Mode'}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* State Configuration Panel */}
        <div className="lg:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden h-full">
            <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/10 rounded-full blur-3xl" />

            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <Stethoscope className="w-5 h-5 text-cyan-400" />
              Patient State
            </h2>

            <div className="space-y-4 relative z-10">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-gray-400">Curriculum Scenarios</label>
                <div className="flex flex-wrap gap-2">
                  {allScenarios.map(s => (
                    <button
                      key={s.id}
                      onClick={() => loadScenario(s)}
                      className={`px-3 py-1.5 text-xs rounded-full border transition-colors ${levelColor(s.level)}`}
                    >
                      {s.name}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Demographics</label>
                <input
                  type="text"
                  value={demographics}
                  onChange={(e) => setDemographics(e.target.value)}
                  placeholder="e.g. 45M, Hx smoking"
                  className="w-full bg-deepnavy border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-400/50 transition-colors"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Symptoms</label>
                <textarea
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  placeholder="e.g. Chest pain, diaphoresis"
                  className="w-full bg-deepnavy border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-400/50 transition-colors min-h-[80px]"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Prior Results / History</label>
                <textarea
                  value={priorResults}
                  onChange={(e) => setPriorResults(e.target.value)}
                  placeholder="e.g. EKG normal 1 hr ago"
                  className="w-full bg-deepnavy border border-white/10 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-cyan-400/50 transition-colors min-h-[80px]"
                />
              </div>

              {/* Reward tracker */}
              {interactionLog.length > 0 && (
                <div className="flex items-center justify-between bg-black/30 rounded-xl px-4 py-3 border border-white/5">
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    <TrendingUp className="w-4 h-4 text-cyan-400" />
                    Cumulative Reward
                  </div>
                  <span className={`font-mono text-sm font-semibold ${cumulativeReward >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {cumulativeReward.toFixed(3)}
                  </span>
                </div>
              )}

              {episodeDone && (
                <div className="text-center text-xs text-yellow-400 bg-yellow-500/10 border border-yellow-500/20 rounded-lg py-2">
                  Episode complete — reset to start a new pathway
                </div>
              )}

              <button
                onClick={startPathway}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-cyan-500/20 to-blue-500/20 hover:from-cyan-500/30 hover:to-blue-500/30 border border-cyan-500/50 rounded-lg text-cyan-300 font-medium transition-all group relative overflow-hidden disabled:opacity-50"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-cyan-400/10 to-blue-400/10 translate-y-full group-hover:translate-y-0 transition-transform" />
                <span className="relative flex items-center justify-center gap-2">
                  <Activity className="w-5 h-5" />
                  Initialize Pathway Agent
                </span>
              </button>

              <label className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                <div>
                  <p className="text-sm text-white">Meta Agent Optimizer</p>
                  <p className="text-xs text-gray-400">Planner -&gt; Critic -&gt; Selector optimization loop on Gemini</p>
                </div>
                <button
                  type="button"
                  onClick={() => setUseMetaOptimizer(prev => !prev)}
                  className={`relative h-6 w-11 rounded-full transition-colors ${useMetaOptimizer ? 'bg-cyan-500/70' : 'bg-gray-600'}`}
                  aria-label="Toggle Meta Agent Optimizer"
                >
                  <span
                    className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-transform ${useMetaOptimizer ? 'translate-x-5' : 'translate-x-0.5'}`}
                  />
                </button>
              </label>
            </div>
          </div>
        </div>

        {/* Pathway Terminal */}
        <div className="lg:col-span-8 flex flex-col h-[700px]">
          <div className="flex-1 glass-panel rounded-2xl rounded-b-none border-b-0 p-6 overflow-y-auto relative flex flex-col space-y-6">

            {interactionLog.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-500">
                <Brain className="w-16 h-16 opacity-20 mb-4 animate-[spin_10s_linear_infinite]" />
                <p>Waiting for State Initialization...</p>
              </div>
            ) : (
              interactionLog.map((log, index) => (
                <div key={index} className={`flex w-full ${log.type === 'user' ? 'justify-end' : 'justify-start'}`}>

                  {log.type === 'user' ? (
                    <div className="max-w-[80%] bg-blue-900/40 border border-blue-500/30 rounded-2xl rounded-tr-none px-5 py-3 text-sm text-gray-200">
                      <pre className="font-sans whitespace-pre-wrap">{log.content as string}</pre>
                    </div>
                  ) : (
                    <div className="max-w-[90%] w-full bg-cyan-900/20 border border-cyan-500/30 rounded-2xl rounded-tl-none p-5 relative overflow-hidden">
                      <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500" />

                      <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-cyan-500/10 rounded-lg">
                          {getActionIcon((log.content as CPOActionResponse).action)}
                        </div>
                        <div>
                          <p className="text-xs text-cyan-400 uppercase tracking-widest font-semibold flex items-center gap-1">
                            <ShieldCheck className="w-3 h-3" /> Recommended Action
                          </p>
                          <h3 className="text-lg font-bold text-white flex items-center gap-2">
                            {(log.content as CPOActionResponse).action}
                            <ChevronRight className="w-4 h-4 text-gray-500" />
                            <span className="text-gray-300 font-medium">{(log.content as CPOActionResponse).specific_detail}</span>
                          </h3>
                        </div>
                        {log.stepReward !== undefined && (
                          <span className={`ml-auto text-xs font-mono font-semibold ${log.stepReward >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            Δr {log.stepReward >= 0 ? '+' : ''}{log.stepReward.toFixed(3)}
                          </span>
                        )}
                      </div>

                      <div className="pl-12 border-l-2 border-white/5 space-y-4">
                        <div>
                          <p className="text-xs text-gray-400 mb-1">Reasoning Constraint Analysis:</p>
                          <p className="text-sm text-gray-300">{(log.content as CPOActionResponse).reasoning}</p>
                        </div>

                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                          <div className="bg-black/20 rounded border border-white/5 p-2 text-center">
                            <span className="block text-[10px] text-gray-400 uppercase">Accuracy</span>
                            <span className="text-xs font-mono text-green-400">{(log.content as CPOActionResponse).expected_reward_impact.accuracy}</span>
                          </div>
                          <div className="bg-black/20 rounded border border-white/5 p-2 text-center">
                            <span className="block text-[10px] text-gray-400 uppercase">Cost</span>
                            <span className="text-xs font-mono text-cyan-400">{(log.content as CPOActionResponse).expected_reward_impact.cost}</span>
                          </div>
                          <div className="bg-black/20 rounded border border-white/5 p-2 text-center">
                            <span className="block text-[10px] text-gray-400 uppercase">Time</span>
                            <span className="text-xs font-mono text-yellow-400">{(log.content as CPOActionResponse).expected_reward_impact.time}</span>
                          </div>
                          <div className="bg-black/20 rounded border border-white/5 p-2 text-center">
                            <span className="block text-[10px] text-gray-400 uppercase">Burden</span>
                            <span className="text-xs font-mono text-purple-400">{(log.content as CPOActionResponse).expected_reward_impact.patient_burden}</span>
                          </div>
                        </div>

                        {(log.content as CPOActionResponse).optimizer_trace && (
                          <div className="rounded-lg border border-cyan-500/20 bg-cyan-500/5 p-3">
                            <p className="text-[11px] uppercase tracking-wider text-cyan-300 mb-1">Optimizer Trace</p>
                            <p className="text-xs text-gray-300">
                              {(log.content as CPOActionResponse).optimizer_trace?.environment}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              Reward: {(log.content as CPOActionResponse).optimizer_trace?.reward_function}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              Candidates: {(log.content as CPOActionResponse).optimizer_trace?.candidate_count} | Selected: #
                              {(log.content as CPOActionResponse).optimizer_trace?.selected_candidate_index}
                            </p>
                            <p className="text-xs text-gray-400 mt-1">
                              {(log.content as CPOActionResponse).optimizer_trace?.selection_reason}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                </div>
              ))
            )}

            {isLoading && (
              <div className="flex w-full justify-start">
                <div className="max-w-[80%] bg-cyan-900/10 border border-cyan-500/20 rounded-2xl rounded-tl-none px-5 py-4 flex items-center gap-3">
                  <Activity className="w-5 h-5 text-cyan-400 animate-pulse" />
                  <span className="text-sm text-cyan-400/70 font-mono tracking-widest uppercase animate-pulse">Agent Computing Path...</span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div className="glass-panel rounded-2xl rounded-t-none p-4 bg-black/20">
            <div className="flex gap-2">
              <input
                type="text"
                value={outcomeInput}
                onChange={(e) => setOutcomeInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleProvideOutcome()}
                placeholder="Simulate action outcome (e.g. 'Troponin is elevated', 'Patient refused test')..."
                className="flex-1 bg-deepnavy border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-cyan-400/50 transition-colors disabled:opacity-50"
                disabled={isLoading || episodeDone || interactionLog.length === 0 || interactionLog[interactionLog.length - 1].type === 'user'}
              />
              <button
                onClick={handleProvideOutcome}
                disabled={isLoading || episodeDone || !outcomeInput.trim() || interactionLog.length === 0 || interactionLog[interactionLog.length - 1].type === 'user'}
                className="bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 p-3 rounded-xl border border-cyan-500/50 transition-colors disabled:opacity-50"
              >
                <ArrowUpCircle className="w-6 h-6" />
              </button>
            </div>
            <p className="text-[10px] text-gray-500 mt-2 text-center">
              Enter the outcome to progress the state. The agent will re-calculate the next optimal step based on Reward constraints.
            </p>
          </div>
        </div>

      </div>
    </div>
  );
};
