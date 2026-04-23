import React from 'react';
// Ribbon.jsx — logo/trust ribbon (placeholder brand set, no invented logos)
const Ribbon = () => {
  return (
    <div className="page">
      <div className="ribbon">
        <div className="ribbon-label">Benchmarks & knowledge bases plugged in</div>
        <div className="ribbon-row">
          <div className="ribbon-item accent-a"><span className="ribbon-dot" /> Meta Ads</div>
          <div className="ribbon-item accent-b"><span className="ribbon-dot" /> Advantage+</div>
          <div className="ribbon-item accent-c"><span className="ribbon-dot" /> WhatsApp Biz</div>
          <div className="ribbon-item"><span className="ribbon-dot" /> ChromaDB</div>
          <div className="ribbon-item accent-d"><span className="ribbon-dot" /> Langfuse</div>
          <div className="ribbon-item"><span className="ribbon-dot" /> n8n</div>
          <div className="ribbon-item"><span className="ribbon-dot" /> PostgreSQL</div>
        </div>
      </div>
    </div>
  );
};

export default Ribbon;
