import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ParticleBackground } from './components/ParticleBackground';
import { Navbar } from './components/Navbar';
import { Home } from './pages/Home';
import { Dashboard } from './pages/Dashboard';
import { DiagnosisForm } from './pages/DiagnosisForm';
import { Result } from './pages/Result';
import { About } from './pages/About';
import { Contact } from './pages/Contact';
import { AuthModal } from './components/AuthModal';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-deepnavy text-white relative">
        <ParticleBackground />
        <Navbar />
        
        <main className="relative z-10 pt-20">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/diagnosis/:diseaseId" element={<DiagnosisForm />} />
            <Route path="/result" element={<Result />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
          </Routes>
        </main>
        
        <AuthModal />
      </div>
    </Router>
  );
}

export default App;
