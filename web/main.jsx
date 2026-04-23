import React, { useState } from 'react';
import ReactDOM from 'react-dom/client';
import Nav from './components/Nav';
import Hero from './components/Hero';
import Ribbon from './components/Ribbon';
import Bento from './components/Bento';
import AgentShowcase from './components/AgentShowcase';
import Workflow from './components/Workflow';
import MetricBand from './components/MetricBand';
import Cta from './components/Cta';
import StrategistConsole from './pages/StrategistConsole';
import './styles.css';

const Footer = () => (
  <footer style={{ padding: '40px 20px', background: '#0A0A0A', color: '#fff', textAlign: 'center' }}>
    <p>© 2026 CampaignPilot. Powered by Claude AI.</p>
  </footer>
);

const App = () => {
  const [view, setView] = useState('landing'); // 'landing' or 'console'
  const [activeAgent, setActiveAgent] = useState('strategist');

  const handleLaunchConsole = () => {
    setView('console');
    setActiveAgent('strategist');
  };

  const handleBackToLanding = () => {
    setView('landing');
  };

  if (view === 'console') {
    return (
      <div style={{ minHeight: '100vh', background: '#F8F9FA' }}>
        <StrategistConsole onBack={handleBackToLanding} />
      </div>
    );
  }

  return (
    <>
      <Nav onLaunchClick={handleLaunchConsole} />
      <Hero onLaunchClick={handleLaunchConsole} />
      <Ribbon />
      <Bento />
      <AgentShowcase onLaunch={handleLaunchConsole} />
      <Workflow />
      <MetricBand />
      <Cta onLaunchClick={handleLaunchConsole} />
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
