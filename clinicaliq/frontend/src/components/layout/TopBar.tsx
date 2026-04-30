import { Bell, Search, UserCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';

export default function TopBar() {
  return (
    <header className="h-16 border-b bg-white dark:bg-slate-950 px-6 flex items-center justify-between shrink-0">
      <div className="flex-1 flex items-center gap-4 max-w-md">
        <div className="relative w-full">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
          <Input 
            placeholder="Search patients..." 
            className="w-full pl-9 bg-slate-50 dark:bg-slate-900 border-none shadow-none"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200">
          <Bell className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 pl-4 border-l">
          <UserCircle className="h-8 w-8 text-slate-400" />
          <div className="text-sm">
            <p className="font-medium">Dr. Smith</p>
            <p className="text-xs text-slate-500">Attending</p>
          </div>
        </div>
      </div>
    </header>
  );
}
