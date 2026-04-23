import React from 'react';

const Nav = ({ onLaunchClick }) => {
  return (
    <div className="nav-wrap">
      <nav className="nav">
        <div className="row" style={{ gap: 36 }}>
          <a href="#" className="nav-logo">
            <div className="nav-logo-mark">◆</div>
            CampaignPilot
          </a>
          <div className="nav-links">
            <a href="#agents">Agents</a>
            <a href="#platform">Platform</a>
            <a href="#workflow">Workflow</a>
            <a href="#metrics">Results</a>
            <a href="#docs">Docs</a>
          </div>
        </div>
        <div className="nav-cta">
          <button className="btn btn-ghost">Sign in</button>
          <button className="btn btn-primary" onClick={onLaunchClick}>
            Launch console
            <span style={{ fontSize: 16 }}>→</span>
          </button>
        </div>
      </nav>
    </div>
  );
};

export default Nav;
