import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertTriangle, CheckCircle, Download, RotateCcw, Share2, Activity, Microscope } from 'lucide-react';
import type { DiagnosisResult } from '../services/gemini';
import { useEffect } from 'react';

// Custom SVG Gauge component
const ConfidenceGauge = ({ value, color }: { value: number, color: string }) => {
    const radius = 60;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (value / 100) * circumference;

    return (
        <div className="relative flex items-center justify-center w-40 h-40">
            <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 160 160">
                {/* Background circle */}
                <circle cx="80" cy="80" r={radius} stroke="currentColor" strokeWidth="12" fill="none" className="text-gray-800" />
                {/* Progress circle */}
                <motion.circle 
                    cx="80" cy="80" r={radius} 
                    stroke={color} 
                    strokeWidth="12" 
                    fill="none" 
                    strokeLinecap="round"
                    strokeDasharray={circumference}
                    initial={{ strokeDashoffset: circumference }}
                    animate={{ strokeDashoffset }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="drop-shadow-[0_0_8px_currentColor]"
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-3xl font-bold font-mono" style={{ color }}>{value}%</span>
                <span className="text-[10px] uppercase tracking-wider text-gray-400">Confidence</span>
            </div>
        </div>
    );
};

export const Result = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Redirect if accessed directly without state
  useEffect(() => {
    if (!location.state || !location.state.result) {
        navigate('/dashboard');
    }
  }, [location, navigate]);

  if (!location.state || !location.state.result) return null;

  const { result, diseaseName, inputPreview, originalParams } = location.state as { 
      result: DiagnosisResult, 
      diseaseName: string, 
      inputPreview: string | null,
      originalParams: Record<string, any> | null,
      pathwayResults?: Array<{ diseaseName: string; result: DiagnosisResult }>
  };
  const pathwayResults = Array.isArray((location.state as any)?.pathwayResults)
    ? (location.state as any).pathwayResults
    : [];

  const isLowRisk = result.risk_level.toLowerCase() === 'low';
  const isHighRisk = result.risk_level.toLowerCase() === 'high';
  
  const statusColor = isLowRisk ? '#00ff88' : isHighRisk ? '#ff4d6d' : '#ffc107'; // green, red, yellow
  const statusClass = isLowRisk ? 'text-biogreen' : isHighRisk ? 'text-alertred' : 'text-yellow-400';
  const Icon = isLowRisk ? CheckCircle : AlertTriangle;

  return (
    <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto pb-20">
       <button onClick={() => navigate('/dashboard')} className="flex items-center text-cyan-400 hover:text-biogreen mb-8 transition-colors">
        <RotateCcw className="w-5 h-5 mr-2" /> New Test
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
        {/* Left Column: Summary & Input */}
        <div className="lg:col-span-1 space-y-6">
            <motion.div 
               initial={{ opacity: 0, x: -20 }}
               animate={{ opacity: 1, x: 0 }}
               className="glass-panel p-6 rounded-2xl flex flex-col items-center text-center relative overflow-hidden"
            >
                {/* Glowing background blob based on risk */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-32 blur-[60px] rounded-full opacity-30" style={{ backgroundColor: statusColor }}></div>
                
                <h3 className="text-gray-400 uppercase tracking-widest text-sm mb-4">Diagnosis Result</h3>
                
                <Icon className={`w-16 h-16 mb-4 ${statusClass} drop-shadow-[0_0_15px_currentColor]`} />
                
                <h2 className="text-2xl font-bold mb-2 text-white">{result.diagnosis}</h2>
                <div className={`px-4 py-1 rounded-full text-sm font-bold border mb-8 uppercase`} style={{ borderColor: statusColor, color: statusColor, backgroundColor: `${statusColor}15` }}>
                    {result.risk_level} Risk
                </div>

                <ConfidenceGauge value={result.confidence} color={statusColor} />
            </motion.div>

            {inputPreview && (
                <motion.div 
                   initial={{ opacity: 0, scale: 0.95 }}
                   animate={{ opacity: 1, scale: 1 }}
                   transition={{ delay: 0.2 }}
                   className="glass-panel p-4 rounded-2xl"
                >
                    <h3 className="text-sm font-semibold text-gray-400 mb-3 border-b border-white/10 pb-2">Scanned Image</h3>
                    <div className="rounded-lg overflow-hidden bg-black/50 border border-white/5 relative">
                        <img src={inputPreview} alt="Medical Scan" className="w-full h-auto opacity-80" />
                        <div className="absolute inset-0 bg-gradient-to-t from-deepnavy/80 to-transparent"></div>
                        <div className="absolute bottom-2 left-2 flex items-center gap-2">
                             <Activity className="w-4 h-4 text-cyan-400 animate-pulse" />
                             <span className="text-[10px] font-mono text-cyan-400">ANALYZED BY {diseaseName.toUpperCase()} MODULE</span>
                        </div>
                    </div>
                </motion.div>
            )}

            {originalParams && (
                 <motion.div 
                 initial={{ opacity: 0, scale: 0.95 }}
                 animate={{ opacity: 1, scale: 1 }}
                 transition={{ delay: 0.2 }}
                 className="glass-panel p-6 rounded-2xl"
              >
                  <h3 className="text-sm font-semibold text-gray-400 mb-4 border-b border-white/10 pb-2">Clinical Parameters</h3>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                      {Object.entries(originalParams).map(([key, val]) => (
                          <div key={key} className="flex justify-between text-xs">
                              <span className="text-gray-500 capitalize">{key.replace('_', ' ')}</span>
                              <span className="font-mono text-white">{val}</span>
                          </div>
                      ))}
                  </div>
              </motion.div>
            )}
        </div>

        {/* Right Column: Details & Recommendations */}
        <div className="lg:col-span-2 space-y-6">
            {pathwayResults.length > 1 && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.15 }}
                className="glass-panel p-6 rounded-2xl border border-cyan-400/20"
              >
                <h3 className="text-xl font-bold mb-4">Integrated Pathway Summary</h3>
                <div className="space-y-2">
                  {pathwayResults.map((entry: { diseaseName: string; result: DiagnosisResult }, idx: number) => (
                    <div key={`${entry.diseaseName}-${idx}`} className="flex items-center justify-between text-sm border-b border-white/10 pb-2">
                      <span className="text-gray-300">{idx + 1}. {entry.diseaseName}</span>
                      <span className="font-semibold text-cyan-300">
                        {entry.result.diagnosis} ({entry.result.confidence}%)
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="glass-panel p-8 rounded-2xl border-t-2"
                style={{ borderTopColor: statusColor }}
            >
                <div className="flex justify-between items-start mb-6">
                    <div>
                        <h2 className="text-3xl font-bold mb-1">Analysis Report</h2>
                        <p className="text-gray-400">Generated by NexioraDx Inference Engine</p>
                    </div>
                    <div className="flex gap-2">
                        <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/10" title="Download Report">
                            <Download className="w-5 h-5 text-cyan-400" />
                        </button>
                        <button className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors border border-white/10" title="Share Result">
                            <Share2 className="w-5 h-5 text-cyan-400" />
                        </button>
                    </div>
                </div>

                <div className="space-y-8">
                    {/* Findings / Risk Factors */}
                    <div>
                        <h3 className="text-lg font-semibold text-cyan-400 mb-4 flex items-center gap-2">
                            <Microscope className="w-5 h-5" /> 
                            {result.findings ? 'Key Visual Findings' : 'Contributing Risk Factors'}
                        </h3>
                        <ul className="space-y-3">
                            {(Array.isArray(result.findings) ? result.findings : Array.isArray(result.risk_factors) ? result.risk_factors : [(result.findings || result.risk_factors)]).map((item, idx) => (
                                <li key={idx} className="flex gap-3 text-gray-300 items-start">
                                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-400 mt-2 shrink-0"></div>
                                    <span className="leading-relaxed">{item}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div className="h-px w-full bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>

                    {/* Recommendations */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2" style={{ color: statusColor }}>
                            <Activity className="w-5 h-5" /> 
                            Recommended Next Steps
                        </h3>
                        <ul className="space-y-3">
                             {(Array.isArray(result.recommendations) ? result.recommendations : [result.recommendations]).map((item, idx) => (
                                <li key={idx} className="flex gap-3 text-gray-300 items-start">
                                    <div className="w-1.5 h-1.5 rounded-full mt-2 shrink-0 shadow-[0_0_8px_currentColor]" style={{ backgroundColor: statusColor, color: statusColor }}></div>
                                    <span className="leading-relaxed">{item}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                </div>

                <div className="mt-12 p-4 bg-deepnavy/50 rounded-xl border border-white/5">
                    <p className="text-xs text-gray-500 font-mono flex items-start gap-2">
                        <AlertTriangle className="w-4 h-4 text-yellow-500 shrink-0" />
                        DISCLAIMER: This diagnostic prediction is simulated using AI for informational purposes only. NexioraDx is not a certified medical device. Always consult with a qualified healthcare professional before making any medical decisions.
                    </p>
                </div>
            </motion.div>
        </div>

      </div>
    </div>
  );
};
