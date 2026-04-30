import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Users, ActivitySquare } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Sidebar() {
  const location = useLocation();

  const links = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Patients', to: '/patients', icon: Users },
    { name: 'Accuracy Reports', to: '/accuracy', icon: ActivitySquare },
  ];

  return (
    <div className="w-64 border-r bg-white dark:bg-slate-950 flex flex-col">
      <div className="h-16 flex items-center px-6 border-b">
        <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
          <ActivitySquare className="text-blue-600 w-6 h-6" />
          NexioraDx
        </h1>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = location.pathname.startsWith(link.to);
          return (
            <Link
              key={link.to}
              to={link.to}
              className={cn(
                'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-50 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white'
              )}
            >
              <Icon className="w-5 h-5" />
              {link.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
