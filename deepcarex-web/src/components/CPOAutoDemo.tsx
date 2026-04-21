import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Play, Pause, RotateCcw, CheckCircle2, XCircle, Activity, FileText, Pill, ArrowRight, AlertTriangle, Clock3 } from 'lucide-react';
import { CPOEnv, type PatientScenario, type CPOState, type CPOActionType, totalReward } from '../env/CPOEnv';
import { runCPOPathway, type CPOActionResponse } from '../services/gemini';
import { getAllScenarios } from '../data/scenarioGenerator';

const SIDEBAR_SCENARIOS = [
  { id: 'uti', icon: '🩺', title: 'UTI (Simple)', desc: '34F, dysuria, pelvic discomfort' },
  { id: 'chf_pneumonia', icon: '🫁', title: 'CHF + Pneumonia (Moderate)', desc: '73F, dyspnea, bilateral crackles' },
  { id: 'sepsis_mof', icon: '🆘', title: 'Sepsis (Complex)', desc: '58M, rigors, hypotension' }
];

const ACTION_ICON: Record<string, React.ReactNode> = {
  'Order Test': <FileText className="w-5 h-5" />,
  'Prescribe': <Pill className="w-5 h-5" />,
  'Refer': <ArrowRight className="w-5 h-5" />,
  'Escalate': <AlertTriangle className="w-5 h-5" />,
  'Wait': <Clock3 className="w-5 h-5" />,
};

const ACTION_COLOR: Record<string, string> = {
  'Order Test': 'bg-blue-500/20 text-blue-300 border-blue-500/50',
  'Prescribe': 'bg-green-500/20 text-green-300 border-green-500/50',
  'Refer': 'bg-purple-500/20 text-purple-300 border-purple-500/50',
  'Escalate': 'bg-red-500/20 text-red-300 border-red-500/50',
  'Wait': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
};

// Map Gemini response actions back to CPOActionType
const mapActionType = (label: string): CPOActionType => {
  if (label === 'Order Test') return 'OrderTest';
  return label as CPOActionType;
};

const OPTIMAL_REWARDS: Record<string, number> = {
  'uti': 1.15,
  'chf_pneumonia': 1.35,
  'sepsis_mof': 0.5
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const CPOAutoDemo = () => {
  const envRef = useRef(new CPOEnv());
  const [activeScenarioId, setActiveScenarioId] = useState('uti');
  const [scenario, setScenario] = useState<PatientScenario | null>(null);
  const [state, setState] = useState<CPOState | null>(null);
  
  const [history, setHistory] = useState<CPOActionResponse[]>([]);
  const [rewardData, setRewardData] = useState<{ step: number; reward: number }[]>([{ step: 0, reward: 0 }]);
  const [cumulativeReward, setCumulativeReward] = useState(0);
  
  const [isThinking, setIsThinking] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [episodeEnd, setEpisodeEnd] = useState<'success' | 'failed' | null>(null);

  const isPlayingRef = useRef(isPlaying);
  useEffect(() => { isPlayingRef.current = isPlaying; }, [isPlaying]);

  const activeScenarioData = SIDEBAR_SCENARIOS.find(s => s.id === activeScenarioId);

  const resetDemo = (scenarioId: string) => {
    const all = getAllScenarios();
    const sc = all.find(s => s.id === scenarioId) || all[0];
    const initialState = envRef.current.reset(sc);
    
    setScenario(sc);
    setState(initialState);
    setHistory([]);
    setRewardData([{ step: 0, reward: 0 }]);
    setCumulativeReward(0);
    setEpisodeEnd(null);
    setIsThinking(false);
    setIsPlaying(true);
    setActiveScenarioId(scenarioId);
  };

  useEffect(() => {
    resetDemo('uti'); // Auto-select Level 1 on load
  }, []);

  useEffect(() => {
    let active = true;

    const runLoop = async () => {
      while (active) {
        if (!isPlayingRef.current || episodeEnd || !state || !scenario) {
          await sleep(500);
          continue;
        }

        setIsThinking(true);
        await sleep(1000); // Fake thinking delay

        if (!active || !isPlayingRef.current) break;

        const response = await runCPOPathway("", state, cumulativeReward);
        
        setIsThinking(false);
        if (!active || !isPlayingRef.current) break;

        setHistory(prev => [...prev, response]);

        const actionType = mapActionType(response.action);
        const stepResult = envRef.current.step({
          type: actionType,
          detail: response.specific_detail,
          outcome: state.currentAssessment
        });

        setState(stepResult.nextState);
        setCumulativeReward(prev => {
          const nr = Number((prev + stepResult.reward).toFixed(3));
          setRewardData(rd => [...rd, { step: stepResult.nextState.stepCount, reward: nr }]);
          return nr;
        });

        if (stepResult.done) {
          setEpisodeEnd(stepResult.diagnosisReached ? 'success' : 'failed');
        }

        await sleep(2000); // 2s interval before next step
      }
    };

    runLoop();
    return () => { active = false; };
  }, [state, scenario, cumulativeReward, episodeEnd]);

  if (!state || !scenario) return null;

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Sidebar Switcher */}
      <div className="lg:w-1/4 space-y-4">
        <h3 className="text-slate-400 font-semibold tracking-wider text-sm uppercase mb-6">Select Scenario</h3>
        {SIDEBAR_SCENARIOS.map(s => (
          <button
            key={s.id}
            onClick={() => resetDemo(s.id)}
            className={`w-full text-left p-4 rounded-2xl transition-all border ${
              activeScenarioId === s.id 
                ? 'bg-cyan-500/10 border-cyan-500/50 shadow-[0_0_15px_rgba(6,182,212,0.2)]' 
                : 'bg-slate-900 border-slate-800 hover:bg-slate-800'
            }`}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">{s.icon}</span>
              <div>
                <p className={`font-bold ${activeScenarioId === s.id ? 'text-cyan-400' : 'text-slate-200'}`}>
                  {s.title}
                </p>
                <p className="text-xs text-slate-400 mt-1">{s.desc}</p>
              </div>
            </div>
          </button>
        ))}

        <div className="mt-8 p-4 bg-slate-900/50 border border-slate-800 rounded-2xl">
          <div className="flex gap-2 justify-center">
            <button 
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-3 bg-slate-800 hover:bg-slate-700 rounded-full text-white transition-colors"
              title={isPlaying ? "Pause" : "Play"}
            >
              {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </button>
            <button 
              onClick={() => resetDemo(activeScenarioId)}
              className="p-3 bg-slate-800 hover:bg-slate-700 rounded-full text-white transition-colors"
              title="Restart"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:w-3/4 space-y-6">
        
        {/* Top panels: Patient State & Reward Chart */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div 
            className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden"
            animate={{ 
              backgroundColor: state.stepCount > 0 ? ['#0f172a', '#1e293b', '#0f172a'] : '#0f172a'
            }}
            transition={{ duration: 1 }}
          >
            <h3 className="text-sm text-slate-400 font-semibold mb-4 uppercase tracking-wider">Current Patient State</h3>
            <div className="space-y-4">
              <div className="flex gap-4 border-b border-slate-800 pb-4">
                <div>
                  <p className="text-xs text-slate-500">Demographics</p>
                  <p className="font-semibold text-slate-200">{state.demographics.age}{state.demographics.sex}, {state.demographics.weight}kg</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Vitals</p>
                  <p className="font-mono text-cyan-300 text-sm">BP {state.vitals.bp} | HR {state.vitals.hr}</p>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-slate-500 mb-2">Symptoms & Signs</p>
                <div className="flex flex-wrap gap-2">
                  {state.symptoms.map(sym => (
                    <span key={sym} className="px-2 py-1 bg-red-500/10 text-red-300 text-xs rounded-full border border-red-500/20">
                      {sym}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <p className="text-xs text-slate-500 mb-2">Labs</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(state.labResults).length > 0 ? Object.entries(state.labResults).map(([k,v]) => (
                    <motion.span 
                      key={k} 
                      initial={{ scale: 0.8, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      className="px-2 py-1 bg-blue-500/10 text-blue-300 text-xs rounded-full border border-blue-500/20"
                    >
                      {k}: {v}
                    </motion.span>
                  )) : (
                    <span className="text-slate-500 text-xs italic">No labs reported</span>
                  )}
                </div>
              </div>
            </div>
          </motion.div>

          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col">
            <h3 className="text-sm text-slate-400 font-semibold mb-2 uppercase tracking-wider flex justify-between">
              <span>Cumulative Reward</span>
              <span className={cumulativeReward >= 0 ? "text-green-400" : "text-red-400"}>
                {cumulativeReward >= 0 ? '+' : ''}{cumulativeReward.toFixed(3)}
              </span>
            </h3>
            <div className="flex-1 min-h-[150px] -ml-4">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={rewardData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="step" stroke="#64748b" tick={{fill: '#64748b'}} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" tick={{fill: '#64748b'}} tickLine={false} axisLine={false} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#f8fafc' }}
                    itemStyle={{ color: '#22d3ee' }}
                  />
                  <ReferenceLine y={OPTIMAL_REWARDS[activeScenarioId]} stroke="#fbbf24" strokeDasharray="3 3" label={{ position: 'top', value: 'Optimal Path', fill: '#fbbf24', fontSize: 10 }} />
                  <Line type="monotone" dataKey="reward" stroke="#22d3ee" strokeWidth={3} dot={{ r: 4, fill: '#0f172a', stroke: '#22d3ee', strokeWidth: 2 }} activeDot={{ r: 6, fill: '#22d3ee' }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Reasoning Panel */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl min-h-[250px] relative">
          <h3 className="text-sm text-slate-400 font-semibold mb-6 uppercase tracking-wider">Agent Reasoning & Actions</h3>
          
          <AnimatePresence mode="popLayout">
            {history.map((act, idx) => (
              <motion.div 
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4 bg-slate-950 border border-slate-800 p-5 rounded-xl shadow-lg relative overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500"></div>
                <div className="flex flex-col md:flex-row gap-4 md:items-start justify-between">
                  <div className="flex-1 space-y-3">
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg border ${ACTION_COLOR[act.action] || 'bg-slate-800 text-white'}`}>
                        {ACTION_ICON[act.action] || <Activity className="w-5 h-5" />}
                      </div>
                      <div>
                        <span className="text-xs text-slate-500 uppercase tracking-wide">Step {idx + 1}</span>
                        <h4 className="text-lg font-bold text-slate-200">{act.action}</h4>
                      </div>
                    </div>
                    <div className="bg-slate-900/50 p-3 rounded-lg border border-slate-800">
                      <p className="text-sm text-slate-300 font-medium">{act.specific_detail}</p>
                    </div>
                    <p className="text-sm text-slate-400 italic">"{act.reasoning}"</p>
                  </div>
                  
                  <div className="md:w-48 shrink-0 bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-xs">
                    <p className="text-slate-500 font-semibold mb-2 uppercase border-b border-slate-800 pb-1">Reward Delta</p>
                    <div className="space-y-1">
                      <div className="flex justify-between"><span className="text-slate-400">Accuracy</span><span className="text-green-400 font-mono">{act.expected_reward_impact.accuracy}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Time</span><span className="text-red-400 font-mono">{act.expected_reward_impact.time}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Cost</span><span className="text-red-400 font-mono">{act.expected_reward_impact.cost}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Burden</span><span className="text-red-400 font-mono">{act.expected_reward_impact.patient_burden}</span></div>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
            
            {isThinking && (
              <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center gap-3 text-cyan-400 p-4"
              >
                <Activity className="w-5 h-5 animate-spin" />
                <span className="text-sm font-medium">Agent analyzing pathway...</span>
                <span className="flex gap-1">
                  <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0 }}>.</motion.span>
                  <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.2 }}>.</motion.span>
                  <motion.span animate={{ opacity: [0, 1, 0] }} transition={{ repeat: Infinity, duration: 1.5, delay: 0.4 }}>.</motion.span>
                </span>
              </motion.div>
            )}

            {episodeEnd && (
              <motion.div 
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className={`p-6 rounded-xl border mt-6 text-center ${
                  episodeEnd === 'success' ? 'bg-green-500/10 border-green-500/30' : 'bg-red-500/10 border-red-500/30'
                }`}
              >
                <div className="flex justify-center mb-3">
                  {episodeEnd === 'success' ? <CheckCircle2 className="w-12 h-12 text-green-400" /> : <XCircle className="w-12 h-12 text-red-400" />}
                </div>
                <h4 className={`text-xl font-bold mb-2 ${episodeEnd === 'success' ? 'text-green-400' : 'text-red-400'}`}>
                  {episodeEnd === 'success' ? 'Diagnosis Reached Successfully' : 'Pathway Failed'}
                </h4>
                <div className="flex justify-center gap-6 mt-4 text-sm">
                  <div>
                    <p className="text-slate-500 uppercase tracking-wide text-xs">Total Reward</p>
                    <p className="font-mono text-lg text-slate-200">{cumulativeReward.toFixed(3)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 uppercase tracking-wide text-xs">Steps Used</p>
                    <p className="font-mono text-lg text-slate-200">{state.stepCount} / {scenario.maxSteps}</p>
                  </div>
                  <div>
                    <p className="text-slate-500 uppercase tracking-wide text-xs">Budget Used</p>
                    <p className="font-mono text-lg text-slate-200">${state.costAccrued} / ${scenario.budgetCeiling}</p>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {history.length === 0 && !isThinking && !episodeEnd && (
            <div className="text-center p-8 text-slate-500 italic">
              Awaiting initialization...
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
