import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import AccuracyDashboardPage from './pages/AccuracyDashboardPage';
import PatientListPage from './pages/PatientListPage';
import NewPatientPage from './pages/NewPatientPage';
import PatientDetailPage from './pages/PatientDetailPage';
import NewVisitPage from './pages/visits/NewVisitPage';
import VisitDetailPage from './pages/VisitDetailPage';
import ReportPage from './pages/ReportPage';

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
        element: <AccuracyDashboardPage />,
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
        path: 'visits/new',
        element: <NewVisitPage />,
      },
      {
        path: 'visits/:id',
        element: <VisitDetailPage />,
      },
      {
        path: 'visits/:id/report',
        element: <ReportPage />,
      },
      {
        path: 'accuracy',
        element: <AccuracyDashboardPage />,
      }
    ],
  },
]);
