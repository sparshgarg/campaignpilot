import React from 'react';
// Workflow.jsx — lifecycle / how it works
const Workflow = () => {
  return (
    <section id="workflow" className="section page">
      <div className="workflow">
        <div>
          <span className="eyebrow">Lifecycle</span>
          <h2 style={{ fontSize: 'clamp(38px, 4.2vw, 54px)', letterSpacing: '-0.04em', marginTop: 16 }}>
            From brief to<br/><span className="grad-text">optimized spend</span> in one loop.
          </h2>
          <p style={{ color: 'var(--muted)', marginTop: 16, fontSize: 16, lineHeight: 1.55, maxWidth: 440 }}>
            Trigger a webhook, hit an endpoint, or click a button in the console. The same
            agent graph runs every time — auditable, versioned, traced.
          </p>

          <div className="wf-steps" style={{ marginTop: 32 }}>
            {[
              { n: '01', t: 'Brief', d: 'Strategist drafts channel mix + budget from your KB + benchmarks.' },
              { n: '02', t: 'Create', d: 'Creative generates on-brand variants, passes safety gate.' },
              { n: '03', t: 'Ship', d: 'n8n pushes to Meta Ads, Advantage+, or your ad platform of choice.' },
              { n: '04', t: 'Measure', d: 'Analyst narrates live performance. Optimizer reallocates.' },
            ].map((s, i) => (
              <div className="wf-step" key={i}>
                <div style={{ minWidth: 40 }}>
                  <div className="wf-num">{s.n}</div>
                </div>
                <div>
                  <div className="wf-title">{s.t}</div>
                  <div className="wf-desc">{s.d}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <WorkflowVisual />
      </div>
    </section>
  );
};

const WorkflowVisual = () => {
  return (
    <div className="wf-visual">
      <div style={{ position: 'relative' }}>
        <div className="row" style={{ marginBottom: 16 }}>
          <div className="mock-dots">
            <span className="dot-r" /><span className="dot-y" /><span className="dot-g" />
          </div>
          <div style={{ marginLeft: 10, fontSize: 12, fontWeight: 600, color: 'var(--muted)' }}>
            lifecycle · trace
          </div>
          <div className="sp" />
          <span className="chip chip-emerald"><span className="pulse-dot" style={{marginRight:6}}/>Running</span>
        </div>

        {/* Node graph */}
        <div className="pipeline" style={{ marginBottom: 18 }}>
          {[
            { n: 'Webhook', r: 'trigger', c: 'chip-slate', letter: 'W', bg: '#6B7280' },
            { n: 'Strategist', r: 'plan', c: 'chip-indigo', letter: 'S', bg: '#6366F1' },
            { n: 'Creative', r: 'copy', c: 'chip-pink', letter: 'C', bg: '#EC4899' },
            { n: 'Eval', r: 'gate', c: 'chip-emerald', letter: 'E', bg: '#10B981' },
            { n: 'Ship', r: 'ads api', c: 'chip-amber', letter: 'A', bg: '#F59E0B' },
          ].map((p, i) => (
            <div key={i} className="pipe-node">
              <div className="row">
                <div style={{ width: 22, height: 22, borderRadius: 6, background: p.bg, color: 'white', display: 'grid', placeItems: 'center', fontSize: 11, fontWeight: 800 }}>{p.letter}</div>
                <div className="pn-title">{p.n}</div>
              </div>
              <div className="pn-role">{p.r}</div>
              <div style={{ height: 3, background: 'var(--line-soft)', borderRadius: 2, overflow: 'hidden' }}>
                <div style={{ width: i < 3 ? '100%' : i === 3 ? '62%' : '0%', height: '100%', background: p.bg, transition: 'width 0.6s ease' }} />
              </div>
            </div>
          ))}
        </div>

        {/* Telemetry */}
        <div style={{ background: 'var(--canvas)', border: '1px solid var(--line)', borderRadius: 16, padding: 16 }}>
          <div className="label-xs" style={{ marginBottom: 10 }}>Live telemetry · last 60 min</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 14 }}>
            <div>
              <div className="big-num" style={{ fontSize: 24 }}>142</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600, marginTop: 4 }}>agent runs</div>
            </div>
            <div>
              <div className="big-num" style={{ fontSize: 24 }}>1.6s</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600, marginTop: 4 }}>p50 latency</div>
            </div>
            <div>
              <div className="big-num" style={{ fontSize: 24, color: 'var(--emerald)' }}>0</div>
              <div style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600, marginTop: 4 }}>safety flags</div>
            </div>
          </div>

          <svg viewBox="0 0 400 60" style={{ width: '100%', height: 60, marginTop: 14 }} preserveAspectRatio="none">
            <defs>
              <linearGradient id="wfGrad" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#6366F1" stopOpacity="0.3"/>
                <stop offset="100%" stopColor="#6366F1" stopOpacity="0"/>
              </linearGradient>
            </defs>
            <path d="M0,42 Q30,36 60,40 T120,30 Q160,22 200,28 T280,18 Q320,14 360,10 T400,6 L400,60 L0,60 Z" fill="url(#wfGrad)"/>
            <path d="M0,42 Q30,36 60,40 T120,30 Q160,22 200,28 T280,18 Q320,14 360,10 T400,6" stroke="#6366F1" strokeWidth="2" fill="none"/>
          </svg>
        </div>
      </div>
    </div>
  );
};

export default Workflow;
