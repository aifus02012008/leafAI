import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ToastContainer } from './components/Toast';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { DiagnosePage } from './pages/DiagnosePage';
import { DiseasesPage } from './pages/DiseasesPage';
import { HistoryPage } from './pages/HistoryPage';
import { TreatmentsPage } from './pages/TreatmentsPage';
import { ToolsPage } from './pages/ToolsPage';
import { AssistantPage } from './pages/AssistantPage';
import { RadarPage } from './pages/RadarPage';
import { FarmsPage } from './pages/FarmsPage';

export default function App() {
  return (
    <BrowserRouter basename={import.meta.env.BASE_URL}>
      <AuthProvider>
        <ToastContainer />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/diagnose" element={<DiagnosePage />} />
            <Route path="/diseases" element={<DiseasesPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/treatments" element={<TreatmentsPage />} />
            <Route path="/tools" element={<ToolsPage />} />
            <Route path="/assistant" element={<AssistantPage />} />
            <Route path="/radar" element={<RadarPage />} />
            <Route path="/farms" element={<FarmsPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
