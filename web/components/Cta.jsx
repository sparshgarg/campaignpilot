import React from 'react';
// Cta.jsx + Footer.jsx
const Cta = () => {
  return (
    <section className="section page">
      <div className="cta-card">
        <div className="cta-glow-1" />
        <div className="cta-glow-2" />
        <div style={{ position: 'relative', zIndex: 2 }}>
          <span className="eyebrow eyebrow-dark">Ready to orchestrate</span>
          <h2 style={{ marginTop: 20 }}>
            Your next campaign<br/>
            <span className="grad-text">thinks for itself.</span>
          </h2>
          <p>
            Spin up the console, point it at your brand knowledge base, and watch five agents
            plan, create, measure, and optimize — with every tool call traced.
          </p>
          <div className="cta-actions">
            <button className="btn btn-primary btn-lg">Launch console →</button>
            <button className="btn btn-outline btn-lg" style={{ background: 'rgba(255,255,255,0.05)', borderColor: 'rgba(255,255,255,0.18)', color: 'white' }}>
              Read the docs
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

const Footer = () => {
  return (
    <footer className="footer page">
      <div className="footer-top">
        <div>
          <a href="#" className="nav-logo">
            <div className="nav-logo-mark">◆</div>
            CampaignPilot
          </a>
          <p className="footer-blurb">
            Multi-agent marketing OS. Plan, create, analyze, and optimize SMB campaigns with full
            observability over every decision.
          </p>
        </div>
        <div className="footer-col">
          <h4>Platform</h4>
          <ul>
            <li><a href="#agents">Agents</a></li>
            <li><a href="#platform">Bento</a></li>
            <li><a href="#workflow">Workflow</a></li>
            <li><a href="#metrics">Eval framework</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Build</h4>
          <ul>
            <li><a href="#">API reference</a></li>
            <li><a href="#">Brand configs</a></li>
            <li><a href="#">n8n workflows</a></li>
            <li><a href="#">Changelog</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Resources</h4>
          <ul>
            <li><a href="#">Golden datasets</a></li>
            <li><a href="#">Eval rubrics</a></li>
            <li><a href="#">Benchmarks</a></li>
            <li><a href="#">Integrations</a></li>
          </ul>
        </div>
        <div className="footer-col">
          <h4>Company</h4>
          <ul>
            <li><a href="#">About</a></li>
            <li><a href="#">Careers</a></li>
            <li><a href="#">Security</a></li>
            <li><a href="#">Contact</a></li>
          </ul>
        </div>
      </div>
      <div className="footer-bottom">
        <div>© 2026 CampaignPilot · All systems live</div>
        <div style={{ display: 'flex', gap: 20 }}>
          <a href="#">Privacy</a>
          <a href="#">Terms</a>
          <a href="#">Status</a>
        </div>
      </div>
    </footer>
  );
};

export default Cta;
