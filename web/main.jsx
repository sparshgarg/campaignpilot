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
import CreativeConsole from './pages/CreativeConsole';
import AnalystConsole from './pages/AnalystConsole';
import OptimizerConsole from './pages/OptimizerConsole';
import ABTestConsole from './pages/ABTestConsole';
import DocsPage from './pages/DocsPage';
import './styles.css';

const Footer = () => (
  <footer style={{ padding: '40px 20px', background: '#0A0A0A', color: '#fff', textAlign: 'center' }}>
    <p>© 2026 CampaignPilot. Powered by Claude AI.</p>
  </footer>
);

const App = () => {
  const [view, setView] = useState('landing'); // 'landing' | 'console' | 'docs'
  const [activeAgent, setActiveAgent] = useState('strategist');

  const handleLaunchConsole = (agentName = 'strategist') => {
    setView('console');
    setActiveAgent(agentName);
  };

  const handleBackToLanding = () => {
    setView('landing');
  };

  const handleShowDocs = () => {
    setView('docs');
    window.scrollTo(0, 0);
  };

  if (view === 'docs') {
    return <DocsPage onBack={handleBackToLanding} />;
  }

  if (view === 'console') {
    const consoleProps = { onBack: handleBackToLanding };
    const consoles = {
      strategist: <StrategistConsole {...consoleProps} />,
      creative: <CreativeConsole {...consoleProps} />,
      analyst: <AnalystConsole {...consoleProps} />,
      optimizer: <OptimizerConsole {...consoleProps} />,
      'ab-test': <ABTestConsole {...consoleProps} />,
    };

    return (
      <div style={{ minHeight: '100vh', background: '#F8F9FA' }}>
        {consoles[activeAgent] || consoles.strategist}
      </div>
    );
  }

  return (
    <>
      <Nav onLaunchClick={handleLaunchConsole} onDocsClick={handleShowDocs} />
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
