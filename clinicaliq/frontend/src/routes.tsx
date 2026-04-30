import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import DashboardPage from './pages/DashboardPage';
import PatientListPage from './pages/PatientListPage';
import NewPatientPage from './pages/NewPatientPage';
import PatientDetailPage from './pages/PatientDetailPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        path: '',
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'patients',
        element: <PatientListPage />,
      },
      {
        path: 'patients/new',
        element: <NewPatientPage />,
      },
      {
        path: 'patients/:id',
        element: <PatientDetailPage />,
      },
      {
        path: 'accuracy',
        element: <div className="p-8">Accuracy page - Coming in next stage</div>,
      }
    ],
  },
]);
