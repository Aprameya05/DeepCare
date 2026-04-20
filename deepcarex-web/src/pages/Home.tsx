import { motion } from 'framer-motion';
import { ArrowRight, Brain, Activity, Dna, Microscope, HeartPulse } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const Home = () => {
  const navigate = useNavigate();

  const accuracyData = [
    { name: 'Diabetes', acc: '97%' },
    { name: 'Brain Tumor', acc: '97%' },
    { name: 'COVID-19', acc: '95%' },
    { name: "Alzheimer's", acc: '98%' },
    { name: 'Kidney', acc: '97%' },
    { name: 'Pneumonia', acc: '83%' },
    { name: 'Breast Cancer', acc: '94%' },
    { name: 'Hepatitis C', acc: '95%' },
  ];

  return (
    <div className="min-h-screen pt-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto flex flex-col justify-center">
      <div className="absolute inset-0 bg-grid-pattern opacity-20 pointer-events-none"></div>
      
      {/* Hero Section */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center z-10 relative mt-10"
      >
        <div className="inline-block mb-4 px-4 py-1.5 rounded-full glass-panel neon-border mb-8">
          <span className="text-cyan-400 text-sm font-semibold tracking-wider uppercase">NexioraDx v3.1 Inference Engine Active</span>
        </div>
        
        <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
          Intelligent Diagnosis.<br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-biogreen">
            Powered by Deep Learning.
          </span>
        </h1>
        
        <p className="max-w-2xl mx-auto text-lg text-gray-300 mb-10">
          AI-Powered Early Disease Detection — 90%+ Accuracy Across 8 Conditions. 
          Upload scans or enter clinical parameters for instant Gemini-powered analysis.
        </p>

        <button 
          onClick={() => navigate('/dashboard')}
          className="group relative inline-flex items-center justify-center px-8 py-4 font-bold text-deepnavy bg-cyan-400 rounded-lg overflow-hidden glass-panel-hover neon-box transition-all duration-300"
        >
          <span className="absolute inset-0 w-full h-full bg-gradient-to-br from-cyan-400 via-biogreen to-cyan-400 opacity-80 group-hover:opacity-100 transition-opacity"></span>
          <span className="relative flex items-center gap-2">
            Start Diagnosis <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </span>
        </button>
      </motion.div>

      {/* Accuracy Ticker */}
      <div className="mt-24 mb-16 relative w-full overflow-hidden glass-panel p-4 rounded-2xl flex items-center">
        <div className="flex whitespace-nowrap animate-[scan_20s_linear_infinite]" style={{ animationDirection: 'normal', animationName: 'marquee' }}>
            <style>{`
              @keyframes marquee { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
            `}</style>
          {/* Double the list to make it seamless */}
          {[...accuracyData, ...accuracyData].map((item, i) => (
            <div key={i} className="flex items-center gap-2 mx-8 text-lg font-mono">
              <span className="text-gray-300">{item.name}</span>
              <span className="text-biogreen font-bold">{item.acc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Stats Section */}
      <motion.div 
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="grid grid-cols-1 md:grid-cols-4 gap-6 pb-20"
      >
        <div className="glass-panel p-6 rounded-xl flex flex-col items-center text-center neon-box">
          <Brain className="w-10 h-10 text-cyan-400 mb-4" />
          <h3 className="text-3xl font-bold mb-2">8</h3>
          <p className="text-gray-400">Diseases Covered</p>
        </div>
        <div className="glass-panel p-6 rounded-xl flex flex-col items-center text-center neon-box">
          <Activity className="w-10 h-10 text-biogreen mb-4" />
          <h3 className="text-3xl font-bold mb-2">90%+</h3>
          <p className="text-gray-400">Average Accuracy</p>
        </div>
        <div className="glass-panel p-6 rounded-xl flex flex-col items-center text-center neon-box">
          <Microscope className="w-10 h-10 text-purpleaccent mb-4" />
          <h3 className="text-xl font-bold mb-2 mt-2">CNN + XGBoost</h3>
          <p className="text-gray-400">Architecture</p>
        </div>
        <div className="glass-panel p-6 rounded-xl flex flex-col items-center text-center neon-box">
          <HeartPulse className="w-10 h-10 text-alertred mb-4" />
          <h3 className="text-xl font-bold mb-2 mt-2">Instant</h3>
          <p className="text-gray-400">Inference Speed</p>
        </div>
      </motion.div>
    </div>
  );
};
