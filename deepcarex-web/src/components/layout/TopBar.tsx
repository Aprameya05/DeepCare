import { Link } from 'react-router-dom';

export const TopBar = () => {
  return (
    <header className="h-16 border-b border-white/10 bg-deepnavy/85 backdrop-blur-md flex items-center justify-between px-6">
      <div>
        <h1 className="text-white font-semibold">Vector-DB Frontend Flow</h1>
        <p className="text-xs text-gray-400">Primary frontend baseline | Release v4.0</p>
      </div>
      <div className="text-sm">
        <Link
          to="/dashboard"
          className="px-3 py-1.5 rounded-md border border-cyan-500/40 text-cyan-300 hover:bg-cyan-500/10 transition-colors"
        >
          Open Diagnosis
        </Link>
      </div>
    </header>
  );
};
