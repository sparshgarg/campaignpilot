import React from 'react';
// Hero.jsx — hero with floating mini-UI cards
const Hero = ({ onLaunchClick }) => {
  return (
    <section className="hero page">
      <div className="hero-bg">
        <div className="hero-glow-a" />
        <div className="hero-glow-b" />
      </div>
      <div className="hero-grid">
        <div>
          <span className="eyebrow">◆ Multi-agent marketing OS</span>
          <h1 className="hero-title">
            Campaigns that<br />
            <span className="grad-text">think for themselves.</span>
          </h1>
          <p className="hero-sub">
            Five specialized AI agents plan, create, analyze, and optimize your SMB campaigns —
            grounded in your brand's benchmarks, with every tool call, token, and decision fully
            traceable.
          </p>
          <div className="hero-ctas">
            <button className="btn btn-primary btn-lg" onClick={onLaunchClick}>
              Start a campaign brief
              <span style={{ fontSize: 16 }}>→</span>
            </button>
            <button className="btn btn-outline btn-lg">
              <span style={{ color: '#6366F1' }}>▶</span> Watch 2-min demo
            </button>
          </div>
          <div className="hero-proof">
            <div className="hero-proof-stack">
              <div className="hero-proof-avatar" style={{ background: 'linear-gradient(135deg,#6366F1,#8B5CF6)' }}>MA</div>
              <div className="hero-proof-avatar" style={{ background: 'linear-gradient(135deg,#EC4899,#F43F5E)' }}>KJ</div>
              <div className="hero-proof-avatar" style={{ background: 'linear-gradient(135deg,#F59E0B,#EF4444)' }}>RP</div>
              <div className="hero-proof-avatar" style={{ background: 'linear-gradient(135deg,#06B6D4,#3B82F6)' }}>SB</div>
            </div>
            <div>Trusted by ops teams at 500+ SMB programs</div>
          </div>
        </div>

        <HeroVisual />
      </div>
    </section>
  );
};

const HeroVisual = () => {
  return (
    <div className="hero-visual">
      {/* Backing mock dashboard */}
      <div
        style={{
          position: 'absolute',
          top: 40,
          left: 20,
          right: 0,
          height: 440,
          background: 'white',
          border: '1px solid var(--line)',
          borderRadius: 28,
          boxShadow: '0 40px 80px -20px rgba(0,0,0,0.18)',
          padding: 22,
          overflow: 'hidden',
        }}
      >
        <div className="row" style={{ marginBottom: 18 }}>
          <div className="mock-dots">
            <span className="dot-r" /><span className="dot-y" /><span className="dot-g" />
          </div>
          <div style={{ marginLeft: 10, fontSize: 12, color: 'var(--muted)', fontWeight: 600 }}>
            app.campaignpilot.ai / strategist
          </div>
          <div className="sp" />
          <span className="chip chip-emerald"><span className="pulse-dot" style={{marginRight:6}}/>Live</span>
        </div>

        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>
          Campaign brief · Q4 restaurant acquisition
        </div>
        <div style={{ fontFamily: 'Plus Jakarta Sans', fontWeight: 800, fontSize: 22, letterSpacing: '-0.02em', marginBottom: 16 }}>
          Channel mix & budget allocation
        </div>

        {/* Mini bars for budget split */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', height: 120, padding: '0 4px', marginBottom: 18 }}>
          {[
            { label: 'IG Feed', pct: 32, color: '#6366F1' },
            { label: 'Reels', pct: 28, color: '#8B5CF6' },
            { label: 'FB Feed', pct: 22, color: '#EC4899' },
            { label: 'Stories', pct: 12, color: '#F59E0B' },
            { label: 'Audience', pct: 6, color: '#10B981' },
          ].map((b, i) => (
            <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
              <div style={{
                width: '100%',
                height: `${b.pct * 3}px`,
                background: `linear-gradient(180deg, ${b.color} 0%, ${b.color}aa 100%)`,
                borderRadius: 10,
                boxShadow: `0 6px 14px -4px ${b.color}66`,
              }} />
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--ink)' }}>{b.pct}%</div>
              <div style={{ fontSize: 9, color: 'var(--muted)', letterSpacing: '0.04em' }}>{b.label}</div>
            </div>
          ))}
        </div>

        <div className="tool-line" style={{ marginBottom: 6 }}>
          <div className="tl-icon tl-purple">S</div>
          <code>search_knowledge_base</code>
          <span style={{ color: 'var(--muted)' }}>("restaurant SMB benchmarks")</span>
          <span className="tl-meta">384ms</span>
        </div>
        <div className="tool-line">
          <div className="tl-icon tl-blue">D</div>
          <code>get_campaign_history</code>
          <span style={{ color: 'var(--muted)' }}>(vertical="restaurant", n=24)</span>
          <span className="tl-meta">112ms</span>
        </div>
      </div>

      {/* Floating card: ROAS */}
      <div className="float-card" style={{ top: 0, right: 40, width: 220, animationDelay: '0s' }}>
        <div className="label-xs">ROAS · Q4 to date</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginTop: 8 }}>
          <div className="big-num">3.42<span style={{fontSize: 18, color: 'var(--muted)', marginLeft:2}}>x</span></div>
          <span className="delta-up">↑ 18%</span>
        </div>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>vs. Meta benchmark 2.19x</div>
        <svg viewBox="0 0 180 40" style={{ width: '100%', height: 36, marginTop: 10 }} preserveAspectRatio="none">
          <defs>
            <linearGradient id="sparkA" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#6366F1" stopOpacity="0.35"/>
              <stop offset="100%" stopColor="#6366F1" stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d="M0,30 Q20,26 40,22 T80,18 Q100,20 120,14 T180,6 L180,40 L0,40 Z" fill="url(#sparkA)" />
          <path d="M0,30 Q20,26 40,22 T80,18 Q100,20 120,14 T180,6" stroke="#6366F1" strokeWidth="2" fill="none"/>
        </svg>
      </div>

      {/* Floating card: agent running */}
      <div className="float-card float-card--glass" style={{ bottom: 120, left: -20, width: 260, animationDelay: '1.8s' }}>
        <div className="row">
          <div className="icon-tile it-indigo" style={{ width: 36, height: 36, fontSize: 15, borderRadius: 10 }}>S</div>
          <div style={{ marginLeft: 2 }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)' }}>Strategist</div>
            <div style={{ fontSize: 11, color: 'var(--emerald)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span className="pulse-dot" /> Brief generated · 1.2s
            </div>
          </div>
        </div>
        <div style={{ marginTop: 12, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <span className="chip chip-indigo">5 turns</span>
          <span className="chip chip-slate">2.4k tokens</span>
          <span className="chip chip-emerald">✓ eval passed</span>
        </div>
      </div>

      {/* Floating card: brand safety */}
      <div className="float-card" style={{ bottom: 0, right: 20, width: 240, animationDelay: '3.4s' }}>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <div className="label-xs">Brand safety</div>
          <span className="chip chip-emerald" style={{ fontSize: 10, padding: '2px 8px' }}>Passed</span>
        </div>
        <div style={{ marginTop: 10, fontSize: 13, color: 'var(--ink)', fontWeight: 600, lineHeight: 1.45 }}>
          20 / 20 variants cleared<br/>prohibited-phrase audit
        </div>
        <div style={{ marginTop: 10, height: 4, background: 'var(--line-soft)', borderRadius: 4, overflow: 'hidden' }}>
          <div style={{ width: '100%', height: '100%', background: 'linear-gradient(90deg,#10B981,#14B8A6)' }} />
        </div>
      </div>
    </div>
  );
};

export default Hero;
