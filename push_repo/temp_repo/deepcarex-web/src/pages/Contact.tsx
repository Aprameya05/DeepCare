import { motion } from 'framer-motion';
import { Send, MapPin, Mail, Phone } from 'lucide-react';

export const Contact = () => {
    return (
        <div className="min-h-screen pt-24 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto pb-20">
            <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-16">
                <h2 className="text-4xl font-bold mb-4 font-mono select-none">Contact Operations</h2>
                <div className="h-1 w-24 bg-cyan-400 mx-auto rounded-full neon-box"></div>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-panel p-8 rounded-2xl"
                >
                    <h3 className="text-2xl font-bold mb-6 text-white">Send a Message</h3>
                    <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
                        <div>
                            <input type="text" placeholder="Full Name" className="w-full bg-deepnavy/50 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 transition-colors" />
                        </div>
                        <div>
                            <input type="email" placeholder="Email Address" className="w-full bg-deepnavy/50 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 transition-colors" />
                        </div>
                        <div>
                            <textarea rows={4} placeholder="Your Message" className="w-full bg-deepnavy/50 border border-white/10 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-cyan-400 transition-colors resize-none"></textarea>
                        </div>
                        <button type="submit" className="flex items-center gap-2 justify-center w-full px-6 py-3 font-bold text-deepnavy bg-cyan-400 rounded-lg overflow-hidden glass-panel-hover neon-box transition-all duration-300">
                            Initialize Transmission <Send className="w-4 h-4" />
                        </button>
                    </form>
                </motion.div>

                <motion.div 
                     initial={{ opacity: 0, x: 20 }}
                     animate={{ opacity: 1, x: 0 }}
                     className="space-y-8"
                >
                     <div className="glass-panel p-6 rounded-2xl flex items-start gap-4 neon-box border border-white/5 hover:border-cyan-400/30 transition-colors">
                         <div className="p-3 bg-cyan-400/10 rounded-lg"><MapPin className="w-6 h-6 text-cyan-400" /></div>
                         <div>
                             <h4 className="font-bold text-white mb-1">Global Headquarters</h4>
                             <p className="text-gray-400 text-sm leading-relaxed">Level 42, Neural Tech Park<br/>Silicon Valley, CA 94025</p>
                         </div>
                     </div>
                     <div className="glass-panel p-6 rounded-2xl flex items-start gap-4 neon-box border border-white/5 hover:border-cyan-400/30 transition-colors">
                         <div className="p-3 bg-cyan-400/10 rounded-lg"><Mail className="w-6 h-6 text-cyan-400" /></div>
                         <div>
                             <h4 className="font-bold text-white mb-1">Electronic Mail</h4>
                             <p className="text-gray-400 text-sm leading-relaxed">systems@deepcarex.ai</p>
                         </div>
                     </div>
                     <div className="glass-panel p-6 rounded-2xl flex items-start gap-4 neon-box border border-white/5 hover:border-cyan-400/30 transition-colors">
                         <div className="p-3 bg-cyan-400/10 rounded-lg"><Phone className="w-6 h-6 text-cyan-400" /></div>
                         <div>
                             <h4 className="font-bold text-white mb-1">Secure Line</h4>
                             <p className="text-gray-400 text-sm leading-relaxed">+1 (800) DEEP-AI-9</p>
                         </div>
                     </div>
                </motion.div>
            </div>
        </div>
    );
};
