import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';

export const AppShell = () => {
  return (
    <div className="min-h-screen bg-deepnavy text-white flex">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <TopBar />
        <main className="relative">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
