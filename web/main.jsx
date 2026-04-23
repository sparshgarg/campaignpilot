import React from 'react';
import ReactDOM from 'react-dom/client';
import Nav from './components/Nav';
import Hero from './components/Hero';
import Ribbon from './components/Ribbon';
import Bento from './components/Bento';
import AgentShowcase from './components/AgentShowcase';
import Workflow from './components/Workflow';
import MetricBand from './components/MetricBand';
import Cta from './components/Cta';
import './styles.css';

// Placeholder Footer component if not present
const Footer = () => (
  <footer style={{ padding: '40px 20px', background: '#0A0A0A', color: '#fff', textAlign: 'center' }}>
    <p>© 2026 CampaignPilot. Powered by Claude AI.</p>
  </footer>
);

const App = () => {
  return (
    <>
      <Nav />
      <Hero />
      <Ribbon />
      <Bento />
      <AgentShowcase />
      <Workflow />
      <MetricBand />
      <Cta />
      <Footer />
    </>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
