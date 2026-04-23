import React from 'react';
// MetricBand.jsx — dark metrics band with gradient numbers
const MetricBand = () => {
  return (
    <section id="metrics" className="section page">
      <div className="metric-band">
        <div className="mb-glow-1" />
        <div className="mb-glow-2" />

        <div style={{ position: 'relative', zIndex: 1, marginBottom: 44 }}>
          <span className="eyebrow eyebrow-dark">In production</span>
          <h2 style={{ color: 'white', fontSize: 'clamp(36px, 4.4vw, 56px)', letterSpacing: '-0.04em', marginTop: 18, maxWidth: 680 }}>
            The difference production-grade<br/> eval infrastructure makes.
          </h2>
        </div>

        <div className="mb-grid">
          <div className="mb-stat">
            <div className="mb-num">500</div>
            <div className="mb-label">SMB advertisers seeded across<br/>10 industries &amp; 40 US DMAs</div>
          </div>
          <div className="mb-stat">
            <div className="mb-num">57</div>
            <div className="mb-label">Golden examples in the<br/>eval dataset — 100% pass</div>
          </div>
          <div className="mb-stat">
            <div className="mb-num">1.8s</div>
            <div className="mb-label">Median agent latency,<br/>end-to-end with tool calls</div>
          </div>
          <div className="mb-stat">
            <div className="mb-num">$0.05</div>
            <div className="mb-label">Full LLM-judge eval run<br/>on claude-haiku-4-5</div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default MetricBand;
