import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ParticleBackground } from './components/ParticleBackground';
import { AppShell } from './components/layout/AppShell';
import { Dashboard } from './pages/Dashboard';
import { DiagnosisForm } from './pages/DiagnosisForm';
import { DiagnosisPathway } from './pages/DiagnosisPathway';
import { Result } from './pages/Result';
import { About } from './pages/About';
import { CPO } from './pages/CPO';
import { CPODemoPage } from './pages/CPODemoPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-deepnavy text-white relative">
        <ParticleBackground />
        <main className="relative z-10">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route element={<AppShell />}>
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/diagnosis-pathway" element={<DiagnosisPathway />} />
              <Route path="/diagnosis/:diseaseId" element={<DiagnosisForm />} />
              <Route path="/result" element={<Result />} />
              <Route path="/about" element={<About />} />
              <Route path="/optimizer" element={<CPO />} />
              <Route path="/cpo" element={<Navigate to="/optimizer" replace />} />
              <Route path="/cpo-demo" element={<CPODemoPage />} />
            </Route>
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
