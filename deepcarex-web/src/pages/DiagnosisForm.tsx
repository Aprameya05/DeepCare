import { useState, useRef, useEffect, type FormEvent } from 'react';
import { useParams, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, Activity, Key, Loader2, ArrowLeft } from 'lucide-react';
import { isApiInferenceConfigured, runImageDiagnosis, runParameterDiagnosis } from '../services/gemini';
import type { DiagnosisResult } from '../services/gemini';

const DISEASE_CONFIGS: Record<string, any> = {
  'alzheimers': {
    name: "Alzheimer's Disease",
    type: 'image',
    description: 'Upload a Brain MRI scan for deep learning analysis.',
    classes: ['Mild Impairment', 'Moderate Impairment', 'No Impairment', 'Very Mild Impairment'],
  },
  'brain_tumor': {
    name: "Brain Tumor",
    type: 'image',
    description: 'Upload an MRI scan to detect tumor presence and type.',
    classes: ['Glioma', 'Meningioma', 'No Tumor', 'Pituitary Tumor'],
  },
  'covid': {
    name: "COVID-19",
    type: 'image',
    description: 'Upload a Chest X-Ray or CT Scan for COVID-19 detection.',
    classes: ['COVID Positive', 'COVID Negative', 'Normal'],
  },
  'breast_cancer': {
    name: "Breast Cancer",
    type: 'parameters',
    description: 'Enter clinical parameters derived from fine needle aspirate (FNA) digitized imaging.',
    classes: ['Malignant', 'Benign'],
    fields: [
      { id: 'radius', label: 'Mean Radius', type: 'range', min: 6, max: 30, step: 0.1, default: 14 },
      { id: 'texture', label: 'Mean Texture', type: 'range', min: 9, max: 40, step: 0.1, default: 19 },
      { id: 'perimeter', label: 'Mean Perimeter', type: 'range', min: 43, max: 190, step: 1, default: 90 },
      { id: 'area', label: 'Mean Area', type: 'range', min: 140, max: 2500, step: 10, default: 600 },
      { id: 'smoothness', label: 'Mean Smoothness', type: 'range', min: 0.05, max: 0.17, step: 0.001, default: 0.10 },
    ]
  },
  'diabetes': {
    name: "Diabetes",
    type: 'parameters',
    description: 'Enter patient clinical data parameters to assess diabetes risk.',
    classes: ['Diabetes Positive', 'No Diabetes'],
    fields: [
      { id: 'gender', label: 'Gender', type: 'select', options: ['Female', 'Male', 'Other'], default: 'Female' },
      { id: 'age', label: 'Age', type: 'range', min: 1, max: 120, step: 1, default: 45 },
      { id: 'hypertension', label: 'Hypertension', type: 'select', options: ['No', 'Yes'], default: 'No' },
      { id: 'heart_disease', label: 'Heart Disease', type: 'select', options: ['No', 'Yes'], default: 'No' },
      { id: 'smoking', label: 'Smoking History', type: 'select', options: ['Never', 'Former', 'Current', 'No Info'], default: 'Never' },
      { id: 'bmi', label: 'BMI', type: 'range', min: 10, max: 60, step: 0.1, default: 25 },
      { id: 'hba1c', label: 'HbA1c Level', type: 'range', min: 3.5, max: 9.0, step: 0.1, default: 5.5 },
      { id: 'glucose', label: 'Blood Glucose Level', type: 'range', min: 80, max: 300, step: 1, default: 100 },
    ]
  }
};

export const DiagnosisForm = () => {
  const { diseaseId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const config = diseaseId ? DISEASE_CONFIGS[diseaseId] : null;
  const useApiInference = isApiInferenceConfigured();
  const pathwayRaw = searchParams.get('pathway') || '';
  const pathwaySequence = pathwayRaw
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean);
  const pathwayStep = Number(searchParams.get('step') || '1');
  const inPathway = pathwaySequence.length > 0;

  const envKey = import.meta.env.VITE_GEMINI_API_KEY;
  const [apiKey, setApiKey] = useState(envKey || localStorage.getItem('gemini_api_key') || '');
  const [showApiKeyPrompt, setShowApiKeyPrompt] = useState(!useApiInference && !apiKey);
  
  // Image state
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Parameter state
  const [params, setParams] = useState<Record<string, any>>({});
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (config?.type === 'parameters') {
      const initParams: Record<string, any> = {};
      config.fields.forEach((f: any) => initParams[f.id] = f.default);
      setParams(initParams);
    }
  }, [diseaseId, config]);

  const saveApiKey = (key: string) => {
    localStorage.setItem('gemini_api_key', key);
    setApiKey(key);
    setShowApiKeyPrompt(false);
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => setImagePreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!useApiInference && !apiKey) {
      setShowApiKeyPrompt(true);
      return;
    }

    if (config.type === 'image' && !imageFile) {
      setError('Please upload an image first.');
      return;
    }

    setLoading(true);

    try {
      let result: DiagnosisResult;

      if (config.type === 'image' && imageFile) {
        const reader = new FileReader();
        const base64Promise = new Promise<string>((resolve) => {
          reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
          reader.readAsDataURL(imageFile);
        });
        const base64Data = await base64Promise;
        result = await runImageDiagnosis(apiKey, config.name, config.classes, base64Data, imageFile.type);
      } else {
        result = await runParameterDiagnosis(apiKey, config.name, config.classes, params);
      }
      
      const resultEntry = {
        diseaseId: diseaseId || '',
        diseaseName: config.name,
        result,
        inputPreview: imagePreview || null,
        originalParams: config.type === 'parameters' ? params : null,
      };
      const existingPathwayResults = Array.isArray((location.state as any)?.pathwayResults)
        ? (location.state as any).pathwayResults
        : [];
      const updatedPathwayResults = [...existingPathwayResults, resultEntry];

      if (inPathway && pathwayStep < pathwaySequence.length) {
        const nextDiseaseId = pathwaySequence[pathwayStep];
        navigate(
          `/diagnosis/${nextDiseaseId}?pathway=${encodeURIComponent(pathwayRaw)}&step=${pathwayStep + 1}`,
          { state: { pathwayResults: updatedPathwayResults } }
        );
      } else if (inPathway) {
        navigate('/result', {
          state: {
            ...resultEntry,
            pathwayResults: updatedPathwayResults,
          },
        });
      } else {
        navigate('/result', {
          state: {
            result,
            diseaseName: config.name,
            inputPreview: imagePreview || null,
            originalParams: config.type === 'parameters' ? params : null,
          },
        });
      }
      
    } catch (err: any) {
      setError(err.message || 'Diagnosis failed.');
      if (!useApiInference && err.message && err.message.includes('API key')) {
        setShowApiKeyPrompt(true);
      }
    } finally {
      setLoading(false);
    }
  };

  if (!config) return <div className="pt-32 text-center text-white">Disease module not found.</div>;

  return (
    <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto pb-20">
      
      <button onClick={() => navigate(-1)} className="flex items-center text-cyan-400 hover:text-biogreen mb-8 transition-colors">
        <ArrowLeft className="w-5 h-5 mr-2" /> Back
      </button>

      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-8 rounded-2xl border border-cyan-400/20 shadow-[0_0_30px_rgba(0,0,0,0.3)] relative"
      >
        <span className="absolute top-0 right-0 p-4 font-mono text-xs text-white/30 uppercase tracking-widest">{diseaseId} AI MODULE</span>
        
        <h2 className="text-3xl font-bold mb-2 text-white">{config.name} Diagnosis</h2>
        <p className="text-gray-400 mb-8">{config.description}</p>
        
        {error && (
            <div className="mb-6 p-4 rounded-lg bg-alertred/10 border border-alertred/50 text-alertred">
                {error}
            </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          
          {config.type === 'image' && (
            <div 
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className="relative w-full h-80 rounded-xl border-2 border-dashed border-cyan-400/50 bg-deepnavy flex items-center justify-center cursor-pointer overflow-hidden group hover:border-cyan-400 transition-colors"
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleImageUpload} 
                accept="image/*" 
                className="hidden" 
              />
              
              <AnimatePresence>
                {imagePreview ? (
                  <motion.div 
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="absolute inset-0 w-full h-full"
                  >
                    <img src={imagePreview} alt="Preview" className="w-full h-full object-contain p-4" />
                    {loading && <div className="scan-line"></div>}
                    <div className="absolute inset-0 bg-deepnavy/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                      <span className="bg-deepnavy px-4 py-2 rounded-full glass-panel neon-text">Replace Image</span>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div className="flex flex-col items-center text-gray-500 group-hover:text-cyan-400 transition-colors pointer-events-none">
                    <UploadCloud className="w-16 h-16 mb-4" />
                    <p className="text-lg font-semibold">Drop image here or click to browse</p>
                    <p className="text-sm mt-2 opacity-70">Supports JPG, PNG, DICOM (converted)</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          )}

          {config.type === 'parameters' && (
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {config.fields.map((field: any) => (
                    <div key={field.id} className="bg-white/5 p-4 rounded-lg border border-white/5 hover:border-cyan-400/30 transition-colors group">
                        <div className="flex justify-between items-center mb-2">
                           <label className="text-sm font-semibold text-gray-300 group-hover:text-cyan-400 transition-colors">{field.label}</label>
                           {(field.type === 'range' || field.type === 'number') && (
                              <span className="font-mono text-biogreen font-bold">{params[field.id]}</span>
                           )}
                        </div>
                        
                        {field.type === 'range' && (
                           <input 
                             type="range" 
                             min={field.min} max={field.max} step={field.step}
                             value={params[field.id]}
                             onChange={(e) => setParams({...params, [field.id]: parseFloat(e.target.value)})}
                             className="w-full accent-cyan-400 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
                           />
                        )}
                        {field.type === 'number' && (
                             <input 
                             type="number" 
                             min={field.min} max={field.max} step={field.step}
                             value={params[field.id]}
                             onChange={(e) => setParams({...params, [field.id]: parseFloat(e.target.value)})}
                             className="w-full bg-deepnavy border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-400"
                           />
                        )}
                        {field.type === 'select' && (
                           <select 
                             value={params[field.id]}
                             onChange={(e) => setParams({...params, [field.id]: e.target.value})}
                             className="w-full bg-deepnavy border border-gray-600 rounded px-3 py-2 text-white focus:outline-none focus:border-cyan-400 appearance-none"
                           >
                              {field.options.map((opt: string) => <option key={opt} value={opt}>{opt}</option>)}
                           </select>
                        )}
                    </div>
                ))}
             </div>
          )}

          <div className="flex justify-end pt-4">
            <button 
              type="submit" 
              disabled={loading}
              className="relative inline-flex items-center justify-center px-8 py-4 font-bold text-deepnavy bg-cyan-400 rounded-lg overflow-hidden glass-panel-hover neon-box transition-all duration-300 min-w-48 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                   <Loader2 className="w-5 h-5 mr-3 animate-spin text-deepnavy" />
                   Processing...
                </>
              ) : (
                <>
                   Initialize Diagnosis <Activity className="w-5 h-5 ml-2" />
                </>
              )}
            </button>
          </div>
        </form>
      </motion.div>

      {/* API Key Modal Overlay */}
      <AnimatePresence>
        {showApiKeyPrompt && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-deepnavy/90 backdrop-blur-md p-4"
          >
             <motion.div 
               initial={{ scale: 0.9, y: 20 }}
               animate={{ scale: 1, y: 0 }}
               className="glass-panel p-8 rounded-2xl max-w-md w-full border border-cyan-400/50 shadow-[0_0_50px_rgba(0,212,255,0.2)]"
             >
                <div className="flex items-center justify-center w-16 h-16 bg-cyan-400/20 rounded-full mb-6 mx-auto">
                    <Key className="w-8 h-8 text-cyan-400" />
                </div>
                <h3 className="text-2xl font-bold text-center mb-2">Gemini API Connection</h3>
                <p className="text-gray-400 text-center text-sm mb-6">NexioraDx requires a Gemini API key to run the deep learning inference engine.</p>
                
                <form onSubmit={(e) => {
                    e.preventDefault();
                    const form = e.target as HTMLFormElement;
                    const input = form.elements.namedItem('apikey') as HTMLInputElement;
                    if(input.value) saveApiKey(input.value);
                }}>
                  <input 
                    name="apikey"
                    type="password" 
                    placeholder="Enter Gemini API Key..." 
                    className="w-full bg-deepnavy border border-gray-600 rounded-lg px-4 py-3 mb-6 text-white focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400 transition-all font-mono"
                    autoFocus
                  />
                  <div className="flex gap-4">
                      {apiKey && (
                          <button type="button" onClick={() => setShowApiKeyPrompt(false)} className="px-4 py-2 bg-gray-800 text-white rounded-lg flex-1 hover:bg-gray-700 transition-colors">
                              Cancel
                          </button>
                      )}
                      <button type="submit" className="px-4 py-2 bg-cyan-400 text-deepnavy font-bold rounded-lg flex-1 hover:bg-biogreen transition-colors shadow-[0_0_15px_rgba(0,212,255,0.4)]">
                          Connect Engine
                      </button>
                  </div>
                </form>
             </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  );
};
