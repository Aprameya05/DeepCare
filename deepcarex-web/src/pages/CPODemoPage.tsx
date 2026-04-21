import { useState, useEffect } from 'react';
import { Activity, Heart, Droplets, Brain } from 'lucide-react';
import { CPOAutoDemo } from '../components/CPOAutoDemo';

const VitalsStrip = () => {
  const [vitals, setVitals] = useState({ hr: 82, bpSys: 118, bpDia: 76, spo2: 98 });

  useEffect(() => {
    const interval = setInterval(() => {
      setVitals(prev => ({
        hr: prev.hr + Math.floor(Math.random() * 5) - 2,
        bpSys: prev.bpSys + Math.floor(Math.random() * 5) - 2,
        bpDia: prev.bpDia + Math.floor(Math.random() * 3) - 1,
        spo2: Math.min(100, Math.max(90, prev.spo2 + Math.floor(Math.random() * 3) - 1))
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex justify-center gap-6 text-sm md:text-base font-mono mb-8 opacity-80 bg-slate-900/50 p-3 rounded-full border border-slate-700/50 backdrop-blur">
      <div className="flex items-center gap-2 text-red-400"><Heart className="w-4 h-4 animate-pulse" /> {vitals.hr} BPM</div>
      <div className="flex items-center gap-2 text-cyan-400"><Activity className="w-4 h-4" /> {vitals.bpSys}/{vitals.bpDia} mmHg</div>
      <div className="flex items-center gap-2 text-blue-400"><Droplets className="w-4 h-4" /> {vitals.spo2}% SpO2</div>
    </div>
  );
};

export const CPODemoPage = () => {
  const [startDemo, setStartDemo] = useState(false);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans flex flex-col selection:bg-cyan-500/30">
      {!startDemo ? (
        <div className="flex-1 flex flex-col items-center justify-center p-6 relative overflow-hidden">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-cyan-900/20 via-slate-950 to-slate-950 z-0"></div>
          
          <div className="relative z-10 max-w-4xl w-full text-center space-y-8">
            <VitalsStrip />
            
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white drop-shadow-sm">
              Clinical Pathway <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500 drop-shadow-lg">Optimizer</span>
            </h1>
            <p className="text-xl md:text-2xl text-slate-400 max-w-2xl mx-auto font-light">
              RL Agent for Adaptive Medical Decision Making
            </p>
            
            <div className="pt-8">
              <button 
                onClick={() => setStartDemo(true)}
                className="group relative inline-flex items-center justify-center gap-3 px-8 py-4 bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold rounded-full transition-all hover:scale-105 active:scale-95 overflow-hidden shadow-[0_0_40px_rgba(6,182,212,0.3)] hover:shadow-[0_0_60px_rgba(6,182,212,0.5)]"
              >
                <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300"></div>
                <Activity className="w-5 h-5 relative z-10" />
                <span className="relative z-10 text-lg">Watch Agent Think</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex flex-col animate-in fade-in duration-700 bg-slate-950">
          <header className="py-4 px-6 md:px-10 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md flex flex-wrap items-center justify-between sticky top-0 z-50 gap-4">
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                <Brain className="w-6 h-6 text-cyan-400" /> CPO Live Demo
              </h2>
            </div>
            <VitalsStrip />
          </header>
          
          <main className="flex-1 w-full mx-auto p-4 md:p-6 lg:p-8">
            <CPOAutoDemo />
          </main>
        </div>
      )}

      <footer className="py-6 border-t border-slate-800/50 bg-slate-950 text-center text-sm text-slate-500 z-20 relative font-medium">
        Grounded in MIMIC-IV statistical priors | PPO reward structure | Part of DeepCareX Research Platform
      </footer>
    </div>
  );
};
