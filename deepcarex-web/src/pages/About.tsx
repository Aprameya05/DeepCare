import { motion } from 'framer-motion';
import { Database, Cpu, Search, CheckCircle } from 'lucide-react';

export const About = () => {
    return (
        <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto pb-20">
            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-16">
                <h2 className="text-4xl font-bold mb-4 font-mono select-none">How It Works</h2>
                <div className="h-1 w-24 bg-cyan-400 mx-auto rounded-full neon-box"></div>
            </motion.div>

            <div className="space-y-16">
               {/* Timeline */}
               <div className="relative border-l border-cyan-400/30 pl-8 ml-4 md:ml-0 space-y-12">
                   {[
                       { icon: Database, title: "Data Ingestion", desc: "Patient data, either medical scans (MRI, CT, X-Ray) or tabular clinical values, are securely ingested into the inference engine." },
                       { icon: Cpu, title: "Preprocessing & Enhancement", desc: "Images undergo automated cropping, noise reduction, and normalization to match the training distributions of our models." },
                       { icon: Search, title: "Deep Learning Inference", desc: "Data is routed to the appropriate specialized model (e.g., VGG19, ResNet152V2, XGBoost) accelerated by Gemini 3.1 APIs." },
                       { icon: CheckCircle, title: "Diagnostic Output", desc: "The engine produces a highly accurate prediction alongside confidence margins, key findings, and action recommendations." }
                   ].map((step, idx) => (
                       <motion.div 
                          key={idx}
                          initial={{ opacity: 0, x: -20 }}
                          whileInView={{ opacity: 1, x: 0 }}
                          viewport={{ once: true }}
                          className="relative"
                       >
                           <div className="absolute -left-[51px] bg-deepnavy p-2 rounded-full border border-cyan-400 neon-box">
                               <step.icon className="w-5 h-5 text-cyan-400" />
                           </div>
                           <h3 className="text-xl font-bold mb-2 text-white">{step.title}</h3>
                           <p className="text-gray-400 leading-relaxed max-w-2xl">{step.desc}</p>
                       </motion.div>
                   ))}
               </div>
            </div>
        </div>
    );
};
