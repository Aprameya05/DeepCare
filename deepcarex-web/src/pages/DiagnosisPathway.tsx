import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowRight, CheckSquare, Square } from 'lucide-react';

type PathwayModule = {
  id: string;
  name: string;
  type: 'Image' | 'Parameters';
};

const DEFAULT_MODULES: PathwayModule[] = [
  { id: 'alzheimers', name: "Alzheimer's Disease", type: 'Image' },
  { id: 'brain_tumor', name: 'Brain Tumor', type: 'Image' },
  { id: 'covid', name: 'COVID-19', type: 'Image' },
  { id: 'breast_cancer', name: 'Breast Cancer', type: 'Parameters' },
  { id: 'diabetes', name: 'Diabetes', type: 'Parameters' },
];

export const DiagnosisPathway = () => {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string[]>(DEFAULT_MODULES.map((m) => m.id));

  const selectedModules = useMemo(
    () => DEFAULT_MODULES.filter((mod) => selected.includes(mod.id)),
    [selected]
  );

  const toggleModule = (moduleId: string) => {
    setSelected((prev) =>
      prev.includes(moduleId) ? prev.filter((id) => id !== moduleId) : [...prev, moduleId]
    );
  };

  const startPathway = () => {
    if (selectedModules.length === 0) return;
    const ordered = DEFAULT_MODULES.filter((m) => selected.includes(m.id)).map((m) => m.id);
    const pathway = ordered.join(',');
    navigate(`/diagnosis/${ordered[0]}?pathway=${encodeURIComponent(pathway)}&step=1`, {
      state: { pathwayResults: [] },
    });
  };

  return (
    <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto pb-20">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-8 rounded-2xl border border-cyan-400/30"
      >
        <h2 className="text-3xl font-bold mb-3">Integrated Multi-Model Pathway</h2>
        <p className="text-gray-400 mb-8">
          Select modules to run in sequence. The gateway will normalize all model responses into one
          combined summary.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
          {DEFAULT_MODULES.map((module) => {
            const isSelected = selected.includes(module.id);
            return (
              <button
                key={module.id}
                type="button"
                onClick={() => toggleModule(module.id)}
                className="text-left p-4 rounded-xl border border-white/10 hover:border-cyan-400/60 transition-colors bg-deepnavy/50"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-white">{module.name}</div>
                    <div className="text-xs text-gray-400 uppercase tracking-wide">{module.type}</div>
                  </div>
                  {isSelected ? (
                    <CheckSquare className="w-5 h-5 text-biogreen" />
                  ) : (
                    <Square className="w-5 h-5 text-gray-500" />
                  )}
                </div>
              </button>
            );
          })}
        </div>

        <div className="flex items-center justify-between border-t border-white/10 pt-6">
          <span className="text-sm text-gray-300">
            {selectedModules.length} module{selectedModules.length === 1 ? '' : 's'} selected
          </span>
          <button
            type="button"
            disabled={selectedModules.length === 0}
            onClick={startPathway}
            className="px-6 py-3 rounded-lg bg-cyan-400 text-deepnavy font-bold disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-2"
          >
            Start Pathway <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    </div>
  );
};
