import { Activity, Beaker, Hexagon, User } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Navbar = () => {
  return (
    <nav className="fixed top-0 w-full z-50 glass-panel border-b border-white/5 border-t-0 border-l-0 border-r-0">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="relative flex items-center justify-center">
                <Hexagon className="w-8 h-8 text-cyan-400 animate-pulse-glow" />
                <Activity className="w-4 h-4 text-white absolute animate-heartbeat" />
              </div>
              <span className="font-mono text-2xl font-bold tracking-wider text-white group-hover:neon-text transition-all duration-300">
                DeepCare<span className="text-cyan-400">X</span>
              </span>
            </Link>
          </div>
          
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-8">
              <Link to="/" className="text-gray-300 hover:text-cyan-400 hover:drop-shadow-[0_0_8px_rgba(0,212,255,0.8)] px-3 py-2 rounded-md text-sm font-medium transition-all">Home</Link>
              <Link to="/dashboard" className="text-gray-300 hover:text-cyan-400 hover:drop-shadow-[0_0_8px_rgba(0,212,255,0.8)] px-3 py-2 rounded-md text-sm font-medium transition-all">Diagnose</Link>
              <Link to="/about" className="text-gray-300 hover:text-cyan-400 hover:drop-shadow-[0_0_8px_rgba(0,212,255,0.8)] px-3 py-2 rounded-md text-sm font-medium transition-all">How it Works</Link>
              <Link to="/contact" className="text-gray-300 hover:text-cyan-400 hover:drop-shadow-[0_0_8px_rgba(0,212,255,0.8)] px-3 py-2 rounded-md text-sm font-medium transition-all">Contact Ops</Link>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
             <div className="flex items-center justify-between w-24 h-10 border border-white/10 rounded-full px-2">
                 {/* Simulated ECG animation visually placed near auth */}
                 <svg viewBox="0 0 100 20" className="w-full h-4 stroke-cyan-400 fill-none" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="0,10 20,10 30,0 40,20 50,10 100,10" className="opacity-70 animate-[scan_2s_linear_infinite]" />
                 </svg>
             </div>
            <button className="flex items-center gap-2 glass-panel-hover bg-white/5 px-4 py-2 rounded-lg text-sm font-medium transition-all neon-border">
              <User className="w-4 h-4 text-cyan-400" />
              <span>Login</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};
