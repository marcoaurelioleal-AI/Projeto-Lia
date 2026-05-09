import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminPage } from './pages/AdminPage';
import { AssistantPage } from './pages/AssistantPage';
import { ChecklistsPage } from './pages/ChecklistsPage';
import { DashboardPage } from './pages/DashboardPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { LoginPage } from './pages/LoginPage';
import { ManualsPage } from './pages/ManualsPage';
import { ReportsPage } from './pages/ReportsPage';

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppShell />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'checklists', element: <ChecklistsPage /> },
      { path: 'incidents', element: <IncidentsPage /> },
      { path: 'reports', element: <ReportsPage /> },
      { path: 'manuals', element: <ManualsPage /> },
      { path: 'assistant', element: <AssistantPage /> },
      { path: 'admin', element: <AdminPage /> }
    ]
  },
  { path: '*', element: <Navigate to="/" replace /> }
]);
