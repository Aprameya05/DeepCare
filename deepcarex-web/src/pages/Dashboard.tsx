import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { 
  Brain, 
  Activity, 
  Dna, 
  ShieldAlert, 
  Microscope,
  Network
} from 'lucide-react';

export const Dashboard = () => {
  const navigate = useNavigate();

  const diseases = [
    { id: 'alzheimers', name: "Alzheimer's Disease", icon: Brain, model: 'Custom CNN', accuracy: '98%', type: 'Image' },
    { id: 'breast_cancer', name: "Breast Cancer", icon: Activity, model: 'Random Forest', accuracy: '94%', type: 'Parameters' },
    { id: 'brain_tumor', name: "Brain Tumor", icon: Microscope, model: 'VGG19', accuracy: '97%', type: 'Image' },
    { id: 'covid', name: "COVID-19", icon: ShieldAlert, model: 'ResNet152V2', accuracy: '95%', type: 'Image' },
    { id: 'diabetes', name: "Diabetes", icon: Dna, model: 'XGBoost', accuracy: '97%', type: 'Parameters' },
    { id: 'multi_pathway', name: "Integrated Pathway", icon: Network, model: 'Gateway Adapters', accuracy: 'Unified', type: 'Hybrid' },
  ];

  return (
    <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-12 text-center"
      >
        <p className="text-xs uppercase tracking-widest text-cyan-300 mb-3">
          Vector-DB Merged Frontend Release v4.0
        </p>
        <h2 className="text-4xl font-bold mb-4 font-mono select-none">Select Diagnostic Module</h2>
        <div className="h-1 w-24 bg-cyan-400 mx-auto rounded-full neon-box"></div>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 pb-20">
        {diseases.map((disease, idx) => {
          const Icon = disease.icon;
          return (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: idx * 0.1 }}
              key={disease.id}
              className="glass-panel p-6 rounded-2xl cursor-pointer group hover:-translate-y-2 relative overflow-hidden transition-all duration-300 neon-box border border-white/5 hover:border-cyan-400/50"
              onClick={() =>
                disease.id === 'multi_pathway'
                  ? navigate('/diagnosis-pathway')
                  : navigate(`/diagnosis/${disease.id}`)
              }
              whileHover={{ scale: 1.02, rotateX: 5, rotateY: 5 }}
              style={{ perspective: 1000 }}
            >
              {/* Scan effect on hover */}
              <div className="absolute inset-0 bg-cyan-400/10 opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="absolute top-0 left-0 w-full h-1 bg-cyan-400 shadow-[0_0_10px_#00d4ff] animate-[scan_2s_linear_infinite]" />
              </div>

              <div className="relative z-10 flex flex-col h-full items-center text-center">
                <div className="w-16 h-16 rounded-full bg-deepnavy/50 flex items-center justify-center mb-4 border border-cyan-400/30 group-hover:border-cyan-400 transition-colors shadow-[0_0_10px_rgba(0,212,255,0.2)] group-hover:shadow-[0_0_20px_rgba(0,212,255,0.6)]">
                  <Icon className="w-8 h-8 text-cyan-400" />
                </div>
                
                <h3 className="text-xl font-bold mb-2 group-hover:text-cyan-400 transition-colors">{disease.name}</h3>
                
                <div className="mt-auto pt-4 w-full flex flex-col gap-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Model</span>
                    <span className="text-gray-200 font-mono">{disease.model}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Accuracy</span>
                    <span className="text-biogreen font-bold">{disease.accuracy}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-1">
                    <span className="text-gray-400">Input</span>
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      disease.type === 'Image'
                        ? 'bg-purpleaccent/30 text-purple-200'
                        : disease.type === 'Hybrid'
                          ? 'bg-biogreen/30 text-biogreen'
                          : 'bg-cyan-400/30 text-cyan-200'
                    }`}>
                      {disease.type}
                    </span>
                  </div>
                  
                  <div className="w-full mt-4 py-2 border border-cyan-400/50 rounded-lg text-cyan-400 font-semibold group-hover:bg-cyan-400 group-hover:text-deepnavy transition-colors opacity-0 group-hover:opacity-100 flex justify-center items-center gap-2">
                    Diagnose Now <Activity className="w-4 h-4" />
                  </div>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
