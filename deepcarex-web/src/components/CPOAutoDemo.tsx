import { useState, useEffect, useRef, Component, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Play, Pause, RotateCcw, CheckCircle2, XCircle, Activity, FileText, Pill, ArrowRight, AlertTriangle, Clock3 } from 'lucide-react';
import { CPOEnv, type PatientScenario, type CPOState, type CPOActionType, totalReward } from '../env/CPOEnv';
import type { CPOActionResponse } from '../services/gemini';
import { getAllScenarios } from '../data/scenarioGenerator';

const SIDEBAR_SCENARIOS = [
  { id: 'uti', icon: '🩺', title: 'UTI (Simple)', desc: '34F, dysuria, pelvic discomfort' },
  { id: 'chf_pneumonia', icon: '🫁', title: 'CHF + Pneumonia (Moderate)', desc: '73F, dyspnea, bilateral crackles' },
  { id: 'sepsis_mof', icon: '🆘', title: 'Sepsis (Complex)', desc: '58M, rigors, hypotension' }
];

class CPOStepErrorBoundary extends Component<{ children: ReactNode }, { caught: boolean }> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { caught: false };
  }
  static getDerivedStateFromError() { return { caught: true }; }
  render() {
    if (this.state.caught) {
      return (
        <div className="p-4 rounded-xl border border-yellow-500/30 bg-yellow-500/10 text-yellow-300 text-sm text-center">
          Step failed — retrying...
        </div>
      );
    }
    return this.props.children;
  }
}

const ACTION_ICON: Record<string, ReactNode> = {
  'Order Test': <FileText className="w-5 h-5" />,
  'Prescribe': <Pill className="w-5 h-5" />,
  'Refer': <ArrowRight className="w-5 h-5" />,
  'Escalate': <AlertTriangle className="w-5 h-5" />,
  'Wait': <Clock3 className="w-5 h-5" />,
};

const ACTION_COLOR: Record<string, string> = {
  'Order Test': 'bg-blue-500/20 text-blue-300 border-blue-500/50',
  'Prescribe': 'bg-green-500/20 text-green-300 border-green-500/50',
  'Refer': 'bg-yellow-500/20 text-yellow-300 border-yellow-500/50',
  'Escalate': 'bg-red-500/20 text-red-300 border-red-500/50',
  'Wait': 'bg-gray-500/20 text-gray-300 border-gray-500/50',
};

// Map Gemini response actions back to CPOActionType
const mapActionType = (label: string): CPOActionType => {
  if (label === 'Order Test') return 'OrderTest';
  return label as CPOActionType;
};

const formatImpactAsPositive = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed || trimmed === '$0' || trimmed === '0') return trimmed;
  if (trimmed.startsWith('+')) return trimmed;
  if (trimmed.startsWith('-')) return `+${trimmed.slice(1)}`;
  if (/^[\d$]/.test(trimmed)) return `+${trimmed}`;
  return trimmed;
};

const OPTIMAL_REWARDS: Record<string, number> = {
  'uti': 1.15,
  'chf_pneumonia': 1.35,
  'sepsis_mof': 0.5,
  'pneumonia': 1.10,
  'htn_crisis': 1.05,
  't2dm_aki': 1.20,
  'polytrauma': 0.60,
};

const HARDCODED_STEPS: Record<string, CPOActionResponse[]> = {
  uti: [
    {
      action: 'Order Test',
      specific_detail: 'Urinalysis with microscopy + urine culture & sensitivity',
      reasoning: 'Urinalysis is first-line for suspected UTI — confirms pyuria/bacteriuria with high accuracy delta at minimal cost and low patient burden.',
      expected_reward_impact: { accuracy: '+0.45', cost: '-$150', time: '-60 min', patient_burden: '-0.3' },
    },
    {
      action: 'Prescribe',
      specific_detail: 'Trimethoprim-Sulfamethoxazole 160/800 mg PO BID × 7 days',
      reasoning: 'UA confirms uncomplicated UTI. TMP-SMX is IDSA first-line for uncomplicated cystitis — excellent efficacy, low resistance, low cost.',
      expected_reward_impact: { accuracy: '+0.35', cost: '-$50', time: '-15 min', patient_burden: '-0.1' },
    },
    {
      action: 'Prescribe',
      specific_detail: 'Phenazopyridine 200 mg PO TID × 2 days for symptomatic dysuria relief',
      reasoning: 'Adjunct urinary analgesic reduces dysuria while awaiting antibiotic effect. Minimal cost and burden; improves patient comfort during treatment window.',
      expected_reward_impact: { accuracy: '+0.05', cost: '-$20', time: '-5 min', patient_burden: '-0.1' },
    },
    {
      action: 'Wait',
      specific_detail: 'Await 48-hour urine culture & sensitivity result before further action',
      reasoning: 'Culture result confirms organism and susceptibility — enables de-escalation or targeted switch if TMP-SMX resistance detected. Holding further action maximizes diagnostic accuracy at near-zero cost.',
      expected_reward_impact: { accuracy: '+0.10', cost: '$0', time: '-120 min', patient_burden: '-0.05' },
    },
    {
      action: 'Refer',
      specific_detail: 'Urology follow-up if recurrent UTI (≥3 episodes/year) or abnormal culture result',
      reasoning: 'Episode near completion. Culture confirms TMP-SMX susceptibility — therapy adequate. Conditional urology referral only if recurrence pattern or resistance emerges.',
      expected_reward_impact: { accuracy: '+0.15', cost: '-$200', time: '-120 min', patient_burden: '-0.2' },
    },
  ],
  chf_pneumonia: [
    {
      action: 'Order Test',
      specific_detail: 'CXR PA/Lateral + BNP + CBC/CMP + ABG',
      reasoning: 'Dual pathology suspected. CXR distinguishes pulmonary edema from consolidation; BNP quantifies cardiac stress; ABG assesses hypoxic severity. High accuracy delta justifies upfront cost.',
      expected_reward_impact: { accuracy: '+0.45', cost: '-$150', time: '-60 min', patient_burden: '-0.3' },
    },
    {
      action: 'Order Test',
      specific_detail: 'Blood cultures ×2 + Procalcitonin + Sputum Gram stain & culture',
      reasoning: 'Microbiologic workup before antibiotic initiation. Procalcitonin differentiates bacterial CAP from CHF-only exacerbation, preventing unnecessary antibiotics and guiding therapy duration.',
      expected_reward_impact: { accuracy: '+0.35', cost: '-$150', time: '-60 min', patient_burden: '-0.3' },
    },
    {
      action: 'Prescribe',
      specific_detail: 'IV Furosemide 40 mg bolus + continuous SpO₂ & BMP monitoring',
      reasoning: 'BNP elevated; CXR shows bilateral infiltrates with Kerley B lines consistent with pulmonary edema. IV loop diuretic is highest-yield intervention for CHF component — rapid symptom relief.',
      expected_reward_impact: { accuracy: '+0.35', cost: '-$50', time: '-15 min', patient_burden: '-0.1' },
    },
    {
      action: 'Prescribe',
      specific_detail: 'Ceftriaxone 1 g IV q24h + Azithromycin 500 mg PO daily (CURB-65 CAP pathway)',
      reasoning: 'Dual-coverage for community-acquired pneumonia per ATS/IDSA guidelines. Beta-lactam + macrolide covers atypical organisms; initiated after blood cultures drawn to preserve microbiologic yield.',
      expected_reward_impact: { accuracy: '+0.35', cost: '-$50', time: '-15 min', patient_burden: '-0.1' },
    },
    {
      action: 'Refer',
      specific_detail: 'Cardiology consult for GDMT optimization + Pulmonology for antibiotic stewardship',
      reasoning: 'Complex dual-pathology warrants specialist co-management. Cardiology optimizes heart failure therapy; Pulmonology guides de-escalation once culture data returns.',
      expected_reward_impact: { accuracy: '+0.25', cost: '-$200', time: '-120 min', patient_burden: '-0.2' },
    },
    {
      action: 'Wait',
      specific_detail: '48 h reassessment: diuresis response, culture sensitivities, repeat BNP',
      reasoning: 'Therapeutic interventions initiated. Watchful waiting with close monitoring maximizes diagnostic accuracy as treatment response data accumulates before further action.',
      expected_reward_impact: { accuracy: '+0.10', cost: '$0', time: '-120 min', patient_burden: '-0.05' },
    },
    {
      action: 'Prescribe',
      specific_detail: 'ACE inhibitor + beta-blocker dose titration post-stabilization (GDMT optimization)',
      reasoning: 'Acute decompensation resolved. Optimizing guideline-directed medical therapy reduces 30-day readmission risk and improves long-term ventricular remodeling outcomes.',
      expected_reward_impact: { accuracy: '+0.20', cost: '-$50', time: '-15 min', patient_burden: '-0.1' },
    },
    {
      action: 'Refer',
      specific_detail: 'Discharge with cardiac rehab enrollment + outpatient pulmonary follow-up at 2 weeks',
      reasoning: 'Coordinated outpatient follow-up closes the care loop — ensures antibiotic course completion and CHF titration with clear escalation pathway if deterioration occurs.',
      expected_reward_impact: { accuracy: '+0.15', cost: '-$200', time: '-120 min', patient_burden: '-0.2' },
    },
  ],
  sepsis_mof: [
    {
      action: 'Order Test',
      specific_detail: 'STAT: Blood cultures ×2 + Lactate + CBC/CMP + Coagulation panel + Procalcitonin',
      reasoning: 'Sepsis-3 criteria met (SOFA ≥2, suspected infection). Blood cultures and lactate are time-critical — must precede antibiotics. Coagulation panel screens for DIC in evolving MODS.',
      expected_reward_impact: { accuracy: '+0.45', cost: '-$150', time: '-60 min', patient_burden: '-0.3' },
    },
    {
      action: 'Prescribe',
      specific_detail: '30 mL/kg IV Lactated Ringer\'s fluid resuscitation bolus over 3 hours',
      reasoning: 'Surviving Sepsis Campaign: fluid resuscitation within 1 hour of septic shock recognition. LR preferred over NS to avoid hyperchloremic acidosis. Titrate to MAP ≥65 mmHg.',
      expected_reward_impact: { accuracy: '+0.35', cost: '-$50', time: '-15 min', patient_burden: '-0.1' },
    },
    {
      action: 'Prescribe',
      specific_detail: 'Piperacillin-Tazobactam 3.375 g IV q6h + Vancomycin 25 mg/kg IV loading dose',
      reasoning: 'Broad-spectrum empiric coverage for septic shock with unknown source. Pip-tazo covers Gram-negative/anaerobes; Vancomycin covers MRSA. De-escalate once cultures return at 48–72 h.',
      expected_reward_impact: { accuracy: '+0.35', cost: '-$50', time: '-15 min', patient_burden: '-0.1' },
    },
    {
      action: 'Escalate',
      specific_detail: 'ICU admission — initiate Norepinephrine 0.1 mcg/kg/min + invasive arterial line & CVP monitoring',
      reasoning: 'MAP <65 mmHg despite 30 mL/kg fluid resuscitation. Septic shock requiring vasopressor therapy mandates ICU-level care. Norepinephrine is first-line vasopressor per SSC guidelines.',
      expected_reward_impact: { accuracy: '+0.40', cost: '-$1000', time: '-30 min', patient_burden: '-0.8' },
    },
  ],
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const CPOAutoDemo = () => {
  const envRef = useRef(new CPOEnv());
  const [activeScenarioId, setActiveScenarioId] = useState('uti');
  const [scenario, setScenario] = useState<PatientScenario | null>(null);
  const [state, setState] = useState<CPOState | null>(null);
  const prevStateRef = useRef<CPOState | null>(null);
  
  const [history, setHistory] = useState<CPOActionResponse[]>([]);
  const [rewardData, setRewardData] = useState<{ step: number; reward: number }[]>([{ step: 0, reward: 0 }]);
  const [cumulativeReward, setCumulativeReward] = useState(0);
  const [changedFields, setChangedFields] = useState<Set<string>>(new Set());
  
  const [isThinking, setIsThinking] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [episodeEnd, setEpisodeEnd] = useState<'success' | 'failed' | null>(null);

  const isPlayingRef = useRef(isPlaying);
  useEffect(() => { isPlayingRef.current = isPlaying; }, [isPlaying]);

  const getChangedFields = (prev: CPOState, next: CPOState) => {
    const changes = new Set<string>();

    if (prev.vitals.bp !== next.vitals.bp) changes.add('vitals.bp');
    if (prev.vitals.hr !== next.vitals.hr) changes.add('vitals.hr');
    if (prev.vitals.temp !== next.vitals.temp) changes.add('vitals.temp');
    if (prev.vitals.spo2 !== next.vitals.spo2) changes.add('vitals.spo2');

    const labKeys = new Set([...Object.keys(prev.labResults), ...Object.keys(next.labResults)]);
    labKeys.forEach((key) => {
      if (prev.labResults[key] !== next.labResults[key]) {
        changes.add(`labResults.${key}`);
      }
    });

    const prevSymptoms = new Set(prev.symptoms);
    const nextSymptoms = new Set(next.symptoms);
    const symptomsChanged =
      prev.symptoms.length !== next.symptoms.length ||
      [...prevSymptoms].some((symptom) => !nextSymptoms.has(symptom)) ||
      [...nextSymptoms].some((symptom) => !prevSymptoms.has(symptom));
    if (symptomsChanged) {
      changes.add('symptoms');
      next.symptoms.forEach((symptom) => changes.add(`symptoms.${symptom}`));
    }

    return changes;
  };

  useEffect(() => {
    if (changedFields.size === 0) return;
    const timeoutId = window.setTimeout(() => setChangedFields(new Set()), 2000);
    return () => window.clearTimeout(timeoutId);
  }, [changedFields]);

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
    setChangedFields(new Set());
    setIsThinking(false);
    setHasStarted(false);
    setIsPlaying(true);
    setActiveScenarioId(scenarioId);
    prevStateRef.current = initialState;
  };

  useEffect(() => {
    resetDemo('uti'); // Auto-select Level 1 on load
  }, []);

  useEffect(() => {
    let active = true;

    const runLoop = async () => {
      while (active) {
        if (!hasStarted || !isPlayingRef.current || episodeEnd || !state || !scenario) {
          await sleep(500);
          continue;
        }

        setIsThinking(true);
        await sleep(1000); // Fake thinking delay

        if (!active || !isPlayingRef.current) break;

        const scenarioSteps = HARDCODED_STEPS[activeScenarioId] ?? HARDCODED_STEPS['uti'];
        const nextIndex = history.length;

        if (nextIndex >= scenarioSteps.length) {
          setIsThinking(false);
          setEpisodeEnd('success');
          break;
        }

        const response = scenarioSteps[nextIndex];
        const isFinalStep = nextIndex === scenarioSteps.length - 1;

        setIsThinking(false);
        if (!active || !isPlayingRef.current) break;

        setHistory(prev => [...prev, response]);

        const actionType = mapActionType(response.action);
        const stepResult = envRef.current.step({
          type: actionType,
          detail: response.specific_detail,
          outcome: state.currentAssessment
        });

        const previousState = prevStateRef.current ?? state;
        const nextChangedFields = getChangedFields(previousState, stepResult.nextState);
        setChangedFields(nextChangedFields);
        prevStateRef.current = stepResult.nextState;

        setState(stepResult.nextState);
        setCumulativeReward(prev => {
          const nr = Number((prev + stepResult.reward).toFixed(3));
          setRewardData(rd => [...rd, { step: stepResult.nextState.stepCount, reward: nr }]);
          return nr;
        });

        if (isFinalStep) {
          setEpisodeEnd('success');
        }

        await sleep(2000); // 2s interval before next step
      }
    };

    runLoop();
    return () => { active = false; };
  }, [hasStarted, state, scenario, cumulativeReward, episodeEnd]);

  if (!state || !scenario) {
    return (
      <div className="flex flex-col lg:flex-row gap-6 animate-pulse">
        <div className="lg:w-1/4 space-y-4">
          {[0, 1, 2].map(i => (
            <div key={i} className="h-20 rounded-2xl bg-slate-800/60" />
          ))}
        </div>
        <div className="lg:w-3/4 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-56 rounded-2xl bg-slate-800/60" />
            <div className="h-56 rounded-2xl bg-slate-800/60" />
          </div>
          <div className="h-64 rounded-2xl bg-slate-800/60" />
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col lg:flex-row gap-6">
      {/* Demo Mode watermark */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-widest text-cyan-400 pointer-events-none">
        <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse inline-block" />
        Demo Mode
      </div>
      {/* Sidebar Switcher */}
      <div className="lg:w-1/4">
        <h3 className="text-slate-400 font-semibold tracking-wider text-sm uppercase mb-3 lg:mb-6">Select Scenario</h3>
        <div className="flex flex-row overflow-x-auto lg:flex-col gap-4 pb-2 lg:pb-0 snap-x hide-scrollbar scroll-smooth">
        {SIDEBAR_SCENARIOS.map(s => (
          <button
            key={s.id}
            onClick={() => resetDemo(s.id)}
            className={`shrink-0 w-[280px] lg:w-full snap-start text-left p-4 rounded-2xl transition-all border ${
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
        </div>

        <div className="mt-4 lg:mt-8 p-4 bg-slate-900/50 border border-slate-800 rounded-2xl">
          {!hasStarted ? (
            <button
              onClick={() => {
                setHasStarted(true);
                setIsPlaying(true);
              }}
              className="w-full rounded-xl border border-cyan-500/50 bg-cyan-500/15 px-4 py-3 text-sm font-semibold text-cyan-200 hover:bg-cyan-500/25 transition-colors"
            >
              Watch Agent Think
            </button>
          ) : (
            <div className="flex gap-2 justify-center">
              <button 
                onClick={() => setIsPlaying(!isPlaying)}
                className="p-3 bg-slate-800 hover:bg-slate-700 rounded-full text-white transition-colors"
                title={isPlaying ? "Pause" : "Resume"}
              >
                {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
              </button>
              <button 
                onClick={() => resetDemo(activeScenarioId)}
                className="p-3 bg-slate-800 hover:bg-slate-700 rounded-full text-white transition-colors"
                title="Reset"
              >
                <RotateCcw className="w-5 h-5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="lg:w-3/4 space-y-6">
        
        {/* Top panels: Patient State & Reward Chart */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div 
            key={`state-card-${state.stepCount}`}
            className="bg-slate-900 border border-slate-800 p-6 rounded-2xl relative overflow-hidden"
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
                  <p className="font-mono text-cyan-300 text-sm flex items-center gap-2">
                    <span className={`rounded px-1.5 py-0.5 transition-colors duration-2000 ${changedFields.has('vitals.bp') ? 'bg-yellow-400/20' : ''}`}>
                      BP {state.vitals.bp}
                    </span>
                    <span>|</span>
                    <span className={`rounded px-1.5 py-0.5 transition-colors duration-2000 ${changedFields.has('vitals.hr') ? 'bg-yellow-400/20' : ''}`}>
                      HR {state.vitals.hr}
                    </span>
                  </p>
                </div>
              </div>
              
              <div>
                <p className="text-xs text-slate-500 mb-2">Symptoms & Signs</p>
                <div className="flex flex-wrap gap-2">
                  {state.symptoms.map(sym => (
                    <span
                      key={sym}
                      className={`px-2 py-1 text-xs rounded-full border transition-colors duration-2000 ${
                        changedFields.has('symptoms') || changedFields.has(`symptoms.${sym}`)
                          ? 'bg-yellow-400/20 border-yellow-400/40 text-yellow-200'
                          : 'bg-red-500/10 border-red-500/20 text-red-300'
                      }`}
                    >
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
                      className={`px-2 py-1 text-xs rounded-full border transition-colors duration-2000 ${
                        changedFields.has(`labResults.${k}`)
                          ? 'bg-yellow-400/20 border-yellow-400/40 text-yellow-200'
                          : 'bg-blue-500/10 border-blue-500/20 text-blue-300'
                      }`}
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
            <div className="flex-1 min-h-[200px] h-[200px] lg:h-auto -ml-4">
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

          <CPOStepErrorBoundary>
          <div className="max-h-[500px] overflow-y-auto pr-1">
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
                      <div className="flex justify-between"><span className="text-slate-400">Accuracy</span><span className="text-green-400 font-mono">{formatImpactAsPositive(act.expected_reward_impact.accuracy)}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Time</span><span className="text-green-400 font-mono">{formatImpactAsPositive(act.expected_reward_impact.time)}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Cost</span><span className="text-green-400 font-mono">{formatImpactAsPositive(act.expected_reward_impact.cost)}</span></div>
                      <div className="flex justify-between"><span className="text-slate-400">Burden</span><span className="text-green-400 font-mono">{formatImpactAsPositive(act.expected_reward_impact.patient_burden)}</span></div>
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
          </CPOStepErrorBoundary>
        </div>
      </div>
    </div>
  );
};
