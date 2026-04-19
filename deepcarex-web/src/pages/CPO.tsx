import React, { useState, useEffect, useRef } from 'react';
import { runCPOPathway } from '../services/gemini';
import type { CPOActionResponse } from '../services/gemini';
import { 
  Activity, ArrowRight, Brain, AlertTriangle, Stethoscope, 
  Pill, FileText, ArrowUpCircle, Clock, ShieldCheck, ChevronRight
} from 'lucide-react';

const predefinedCases = [
  {
    id: 1,
    name: "Simple Case: Chest Pain",
    demographics: "45M, no previous medical history",
    symptoms: "Sudden onset chest pain radiating to left arm, sweating",
    priorResults: "None"
  },
  {
    id: 2,
    name: "Moderate Case: Fever & Cough",
    demographics: "35F, pregnant (2nd trimester)",
    symptoms: "Productive cough for 5 days, 101F fever",
    priorResults: "Rapid flu negative"
  },
  {
    id: 3,
    name: "Multi-Comorbidity: ESRD & Diabetes",
    demographics: "68M, Hx ESRD on dialysis, Type 2 DM, HTN",
    symptoms: "Shortness of breath, missed dialysis yesterday, bilateral leg swelling",
    priorResults: "Home glucose 210 mg/dL"
  }
];

export const CPO = () => {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('gemini_api_key') || '');
  const [demographics, setDemographics] = useState('');
  const [symptoms, setSymptoms] = useState('');
  const [priorResults, setPriorResults] = useState('');
  
  const [historyOfActions, setHistoryOfActions] = useState<string[]>([]);
  const [interactionLog, setInteractionLog] = useState<{ type: 'user' | 'agent', content: any }[]>([]);
  
  const [isLoading, setIsLoading] = useState(false);
  const [outcomeInput, setOutcomeInput] = useState('');
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [interactionLog]);

  const loadCase = (id: number) => {
    const c = predefinedCases.find(x => x.id === id);
    if (c) {
      setDemographics(c.demographics);
      setSymptoms(c.symptoms);
      setPriorResults(c.priorResults);
      setHistoryOfActions([]);
      setInteractionLog([]);
      setOutcomeInput('');
    }
  };

  const startPathway = async () => {
    if (!apiKey) {
      console.warn("No Gemini API Key found. CPO will run in simulation fallback mode.");
    }
    if (!demographics || !symptoms) {
      alert("Please fill in demographics and symptoms.");
      return;
    }

    setHistoryOfActions([]);
    setInteractionLog([
      { type: 'user', content: `Started pathway simulation.\nDemographics: ${demographics}\nSymptoms: ${symptoms}\nPrior Results: ${priorResults}` }
    ]);
    
    await fetchNextAction([]);
  };

  const fetchNextAction = async (currentHistory: string[]) => {
    setIsLoading(true);
    try {
      const response = await runCPOPathway(apiKey, { demographics, symptoms, priorResults }, currentHistory);
      
      setInteractionLog(prev => [...prev, { type: 'agent', content: response }]);
      
      // We don't push the agent action to historyOfActions until the user provides an outcome
      // Or actually, let's keep history as "Action -> Outcome" strings
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleProvideOutcome = async () => {
    if (!outcomeInput.trim()) return;
    
    const lastAgentAction = interactionLog[interactionLog.length - 1];
    if (lastAgentAction?.type !== 'agent') return;
    
    const actionData = lastAgentAction.content as CPOActionResponse;
    const historyEntry = `Agent Action: [${actionData.action}] ${actionData.specific_detail} -> User Outcome/Result: ${outcomeInput}`;
    
    const newHistory = [...historyOfActions, historyEntry];
    setHistoryOfActions(newHistory);
    
    setInteractionLog(prev => [...prev, { type: 'user', content: `Outcome for ${actionData.action}: ${outcomeInput}` }]);
    setOutcomeInput('');
    
    await fetchNextAction(newHistory);
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
                <label className="text-sm font-medium text-gray-400">Curriculum Cases</label>
                <div className="flex flex-wrap gap-2">
                  {predefinedCases.map(c => (
                    <button
                      key={c.id}
                      onClick={() => loadCase(c.id)}
                      className="px-3 py-1.5 text-xs rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 transition-colors"
                    >
                      {c.name}
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
                      <pre className="font-sans whitespace-pre-wrap">{log.content}</pre>
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
                disabled={isLoading || interactionLog.length === 0 || interactionLog[interactionLog.length - 1].type === 'user'}
              />
              <button
                onClick={handleProvideOutcome}
                disabled={isLoading || !outcomeInput.trim() || interactionLog.length === 0 || interactionLog[interactionLog.length - 1].type === 'user'}
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
