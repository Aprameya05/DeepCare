import { ActivitySquare, Brain, LayoutDashboard, Route, Info } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

type NavItem = {
  label: string;
  to: string;
  icon: React.ComponentType<{ className?: string }>;
};

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
  { label: 'Diagnosis Pathway', to: '/diagnosis-pathway', icon: ActivitySquare },
  { label: 'Optimizer', to: '/optimizer', icon: Route },
  { label: 'About', to: '/about', icon: Info },
];

export const Sidebar = () => {
  const location = useLocation();

  return (
    <aside className="w-64 border-r border-white/10 bg-deepnavy/90 backdrop-blur-md hidden lg:flex flex-col">
      <div className="h-16 px-5 flex items-center border-b border-white/10">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyan-400" />
          <span className="font-semibold text-white tracking-wide">NexioraDx</span>
        </div>
      </div>

      <nav className="p-4 space-y-2">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const active = location.pathname.startsWith(item.to);
          return (
            <Link
              key={item.to}
              to={item.to}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                active
                  ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-500/30'
                  : 'text-gray-300 hover:bg-white/5 hover:text-white'
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
};
