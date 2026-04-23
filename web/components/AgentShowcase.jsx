import React from 'react';
// AgentShowcase.jsx — interactive tabbed agent switcher
const AGENTS = [
  {
    id: 'strategist',
    name: 'Strategist',
    tile: 'it-indigo',
    dot: '#6366F1',
    short: 'Plans channel mix, budgets & KPIs',
    title: 'Design a winning campaign in under 2 seconds.',
    desc: 'Pulls from your benchmarks, historical campaigns, and brand guidelines to return a full brief: channel split, budget allocation, message pillar, KPIs, and risks.',
    bullets: [
      'RAG against 49-doc knowledge base · grounded citations',
      'Budget-realism checks before output ever ships',
      'Outputs a structured brief your ops team can action',
    ],
  },
  {
    id: 'creative',
    name: 'Creative',
    tile: 'it-pink',
    dot: '#EC4899',
    short: 'Ad copy across every channel',
    title: 'On-brand copy. Every channel. Every variant.',
    desc: 'Generates Facebook, Instagram, email, and search variants. Every line passes a prohibited-phrase allowlist and tone audit before it reaches review.',
    bullets: [
      'Multi-channel variants in one run',
      'Brand-safety gate: phrases, claims, tone',
      'Tone dial: professional, urgent, educational, friendly',
    ],
  },
  {
    id: 'analyst',
    name: 'Analyst',
    tile: 'it-cyan',
    dot: '#06B6D4',
    short: 'Natural language → SQL → insight',
    title: 'Ask a question. Get a decision.',
    desc: "Text-to-SQL with a SELECT-only allowlist, schema awareness, and narrated insight. You get the query, the results, and the 'so what' in one pass.",
    bullets: [
      'SELECT-only validator + known-table allowlist',
      'Insight quality graded 1–5 by LLM judge',
      'Visualizes results inline with recommended action',
    ],
  },
  {
    id: 'optimizer',
    name: 'Optimizer',
    tile: 'it-amber',
    dot: '#F59E0B',
    short: 'Performance vs benchmarks',
    title: 'Reallocate before waste compounds.',
    desc: 'Compares live campaign metrics against your brand benchmarks and surfaces prioritized recommendations — reallocate, pause, scale, or rebalance.',
    bullets: [
      'Benchmark comparison: ROAS, CTR, CPC, CAC',
      'Priority-ranked actions with expected impact',
      'Drag-to-adjust budget recommendations',
    ],
  },
  {
    id: 'abtest',
    name: 'A/B Testing',
    tile: 'it-emerald',
    dot: '#10B981',
    short: 'Statistically valid experiments',
    title: 'Experiments that actually measure something.',
    desc: 'Stratified random assignment across industry, size, DMA tier, and ad experience — with a proper two-proportion power analysis and balance diagnostics.',
    bullets: [
      'Stratified sampling on 4 covariates',
      'Chi-square + Welch\'s t-test balance checks',
      'Power analysis baked into every design',
    ],
  },
];

const AgentShowcase = ({ onLaunch }) => {
  const [active, setActive] = React.useState('strategist');
  const agent = AGENTS.find((a) => a.id === active);

  return (
    <section id="agents" className="section page">
      <div className="section-head">
        <div>
          <span className="eyebrow">Five agents. One mission.</span>
          <h2 style={{ marginTop: 16 }}>
            Specialists, not a<br/><span className="grad-text">monolith.</span>
          </h2>
        </div>
        <p>
          Each agent has a narrow role, its own eval rubric, and its own regression threshold.
          When something drifts, you know exactly where to fix it.
        </p>
      </div>

      <div className="agents">
        <div className="agent-tabs">
          {AGENTS.map((a) => (
            <button
              key={a.id}
              className={`agent-tab ${active === a.id ? 'active' : ''}`}
              onClick={() => setActive(a.id)}
            >
              <span className="tab-dot" style={{ background: a.dot }} />
              {a.name}
            </button>
          ))}
        </div>

        <div className="agent-panel">
          <div className="agent-copy">
            <div className={`icon-tile ${agent.tile}`} style={{ width: 52, height: 52, fontSize: 22, borderRadius: 14 }}>
              {agent.name[0]}
            </div>
            <h3>{agent.title}</h3>
            <p>{agent.desc}</p>
            <div className="agent-bullets">
              {agent.bullets.map((b, i) => (
                <div className="agent-bullet" key={i}>
                  <div className="bullet-check">✓</div>
                  <span>{b}</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 28, display: 'flex', gap: 10 }}>
              <button className="btn btn-dark" onClick={onLaunch}>Launch {agent.name.toLowerCase()} →</button>
              <button className="btn btn-outline">View eval rubric</button>
            </div>
          </div>

          <AgentMock agent={agent} />
        </div>
      </div>
    </section>
  );
};

const AgentMock = ({ agent }) => {
  switch (agent.id) {
    case 'strategist': return <StrategistMock />;
    case 'creative': return <CreativeMock />;
    case 'analyst': return <AnalystMock />;
    case 'optimizer': return <OptimizerMock />;
    case 'abtest': return <ABMock />;
    default: return null;
  }
};

const StrategistMock = () => (
  <div className="mock">
    <div className="mock-head">
      <div className="mock-title"><span className="pulse-dot" /> strategist.run</div>
      <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'SF Mono, monospace' }}>+1.24s</div>
    </div>
    <div className="tool-line"><div className="tl-icon tl-purple">S</div><code>search_knowledge_base</code><span style={{color:'var(--muted)'}}>("restaurant SMB")</span><span className="tl-meta">+0.38s</span></div>
    <div className="tool-line"><div className="tl-icon tl-blue">D</div><code>get_campaign_history</code><span style={{color:'var(--muted)'}}>(vertical="rest...")</span><span className="tl-meta">+0.11s</span></div>
    <div className="tool-line"><div className="tl-icon tl-green">B</div><code>get_benchmark_data</code><span style={{color:'var(--muted)'}}>(vertical="rest...")</span><span className="tl-meta">+0.09s</span></div>

    <div style={{ marginTop: 14, padding: 16, background: 'white', border: '1px solid var(--line)', borderRadius: 14 }}>
      <div className="label-xs">Channel mix</div>
      <div style={{ display: 'flex', height: 10, borderRadius: 5, overflow: 'hidden', marginTop: 10 }}>
        <div style={{ width: '32%', background: '#6366F1' }} />
        <div style={{ width: '28%', background: '#8B5CF6' }} />
        <div style={{ width: '22%', background: '#EC4899' }} />
        <div style={{ width: '12%', background: '#F59E0B' }} />
        <div style={{ width: '6%', background: '#10B981' }} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 10, fontSize: 11, color: 'var(--muted)', fontWeight: 600 }}>
        <span>IG 32%</span><span>Reels 28%</span><span>FB 22%</span><span>Stories 12%</span><span>Aud 6%</span>
      </div>
    </div>

    <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
      <span className="chip chip-indigo">$75,000 · 45 days</span>
      <span className="chip chip-emerald">ROAS target 2.8x</span>
      <span className="chip chip-amber">CAC &lt; $150</span>
    </div>
  </div>
);

const CreativeMock = () => (
  <div className="mock">
    <div className="mock-head">
      <div className="mock-title"><span className="pulse-dot" /> creative.run</div>
      <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'SF Mono, monospace' }}>3 variants · 0.9s</div>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      {[
        { ch: 'IG · Feed', head: 'Fill more tables, not more paperwork.', body: 'Set it up in 4 minutes. We handle the boost.', cta: 'Try free →', tone: 'friendly' },
        { ch: 'FB · Feed', head: 'Your Saturday rush, every Saturday.', body: 'Reach diners within 5 miles who love your cuisine.', cta: 'See how →', tone: 'outcome-first' },
        { ch: 'Email', head: 'The next 45 days could bring 500 new regulars.', body: 'Based on restaurants like yours in your DMA.', cta: 'Get my plan', tone: 'urgent' },
      ].map((v, i) => (
        <div key={i} style={{ background: 'white', border: '1px solid var(--line)', borderRadius: 14, padding: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <span className="chip chip-slate" style={{ fontSize: 10 }}>{v.ch}</span>
            <span className="chip chip-emerald" style={{ fontSize: 10 }}>✓ safe</span>
          </div>
          <div style={{ fontWeight: 700, fontSize: 14, letterSpacing: '-0.01em', marginBottom: 4 }}>{v.head}</div>
          <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.4, marginBottom: 10 }}>{v.body}</div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span className="chip chip-pink" style={{ fontSize: 10 }}>{v.tone}</span>
            <span style={{ fontSize: 11, color: 'var(--indigo)', fontWeight: 700 }}>{v.cta}</span>
          </div>
        </div>
      ))}
    </div>
  </div>
);

const AnalystMock = () => (
  <div className="mock">
    <div className="mock-head">
      <div className="mock-title"><span className="pulse-dot" /> analyst.run</div>
      <div style={{ fontSize: 11, color: 'var(--muted)', fontFamily: 'SF Mono, monospace' }}>+0.68s</div>
    </div>
    <div style={{ padding: 12, background: 'white', border: '1px solid var(--line)', borderRadius: 12, marginBottom: 10 }}>
      <div className="label-xs" style={{ marginBottom: 6 }}>Question</div>
      <div style={{ fontSize: 13, color: 'var(--ink)' }}>"What is ROAS by channel in the last 30 days for restaurant campaigns?"</div>
    </div>
    <div style={{ padding: 12, background: '#0A0A0A', borderRadius: 12, marginBottom: 10, fontFamily: 'SF Mono, monospace', fontSize: 11, color: '#E4E4E7' }}>
      <span style={{ color: '#A5B4FC' }}>SELECT</span> channel, <span style={{ color: '#FCA5A5' }}>SUM</span>(revenue)/<span style={{ color: '#FCA5A5' }}>SUM</span>(spend) <span style={{ color: '#A5B4FC' }}>AS</span> roas<br/>
      <span style={{ color: '#A5B4FC' }}>FROM</span> performance_events <span style={{ color: '#A5B4FC' }}>WHERE</span> vertical=<span style={{ color: '#86EFAC' }}>'restaurant'</span><br/>
      <span style={{ color: '#A5B4FC' }}>GROUP BY</span> channel <span style={{ color: '#A5B4FC' }}>ORDER BY</span> roas <span style={{ color: '#A5B4FC' }}>DESC</span>;
    </div>
    <div style={{ background: 'white', border: '1px solid var(--line)', borderRadius: 12, overflow: 'hidden' }}>
      {[
        { ch: 'Reels', val: 3.82, pct: 100 },
        { ch: 'IG Feed', val: 3.24, pct: 85 },
        { ch: 'FB Feed', val: 2.41, pct: 63 },
        { ch: 'Stories', val: 1.88, pct: 49 },
      ].map((r, i) => (
        <div key={i} style={{ padding: '10px 14px', borderBottom: i < 3 ? '1px solid var(--line)' : 'none', display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ width: 70, fontSize: 12, fontWeight: 600 }}>{r.ch}</div>
          <div style={{ flex: 1, height: 6, background: 'var(--line-soft)', borderRadius: 3, overflow: 'hidden' }}>
            <div style={{ width: `${r.pct}%`, height: '100%', background: 'linear-gradient(90deg,#06B6D4,#3B82F6)' }} />
          </div>
          <div style={{ width: 50, textAlign: 'right', fontWeight: 700, fontSize: 13, fontFamily: 'Plus Jakarta Sans' }}>{r.val}x</div>
        </div>
      ))}
    </div>
    <div style={{ marginTop: 10, padding: 10, background: 'rgba(6,182,212,0.08)', border: '1px solid rgba(6,182,212,0.2)', borderRadius: 10, fontSize: 12, color: 'var(--ink)', lineHeight: 1.5 }}>
      <strong>Insight:</strong> Reels outperforms benchmark by 74%. Shift +10% from Stories next cycle.
    </div>
  </div>
);

const OptimizerMock = () => (
  <div className="mock">
    <div className="mock-head">
      <div className="mock-title"><span className="pulse-dot" /> optimizer.run</div>
      <span className="chip chip-amber" style={{ fontSize: 10 }}>Health · Yellow</span>
    </div>
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {[
        { m: 'ROAS', cur: '2.18x', bench: '2.19x', d: -0.5, ok: false },
        { m: 'CTR', cur: '2.64%', bench: '2.19%', d: 20.5, ok: true },
        { m: 'CPC', cur: '$1.82', bench: '$1.60', d: 13.7, ok: false },
        { m: 'CAC', cur: '$142', bench: '$150', d: -5.3, ok: true },
      ].map((r, i) => (
        <div key={i} style={{ background: 'white', border: '1px solid var(--line)', borderRadius: 12, padding: '10px 14px', display: 'grid', gridTemplateColumns: '60px 1fr 1fr 70px', gap: 10, alignItems: 'center', fontSize: 12 }}>
          <div style={{ fontWeight: 700 }}>{r.m}</div>
          <div><span className="label-xs">CUR</span> <span style={{ fontWeight: 700, color: 'var(--ink)' }}>{r.cur}</span></div>
          <div><span className="label-xs">BENCH</span> <span style={{ color: 'var(--muted)' }}>{r.bench}</span></div>
          <div style={{ textAlign: 'right', fontWeight: 700, color: r.ok ? 'var(--emerald)' : 'var(--red)' }}>{r.d > 0 ? '↑' : '↓'} {Math.abs(r.d)}%</div>
        </div>
      ))}
    </div>
    <div style={{ marginTop: 14, padding: 14, background: 'linear-gradient(135deg, rgba(245,158,11,0.08), rgba(239,68,68,0.06))', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 14 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
        <span className="chip chip-amber" style={{ fontSize: 10 }}>HIGH PRIORITY</span>
        <span style={{ fontSize: 11, color: 'var(--muted)', fontWeight: 600 }}>Budget reallocation</span>
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: '-0.01em', color: 'var(--ink)' }}>
        Shift $4,200 from Stories → Reels. Projected ROAS lift +0.31x.
      </div>
    </div>
  </div>
);

const ABMock = () => (
  <div className="mock">
    <div className="mock-head">
      <div className="mock-title"><span className="pulse-dot" /> ab_testing.design</div>
      <span className="chip chip-emerald" style={{ fontSize: 10 }}>Balanced ✓</span>
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginBottom: 12 }}>
      <div style={{ background: 'white', border: '1px solid var(--line)', borderRadius: 12, padding: 14 }}>
        <div className="label-xs">CONTROL · n</div>
        <div className="big-num" style={{ fontSize: 24, marginTop: 4 }}>1,248</div>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>baseline CR 2.6%</div>
      </div>
      <div style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.06), rgba(20,184,166,0.04))', border: '1px solid rgba(16,185,129,0.25)', borderRadius: 12, padding: 14 }}>
        <div className="label-xs" style={{ color: '#047857' }}>TEST · n</div>
        <div className="big-num" style={{ fontSize: 24, marginTop: 4 }}>1,248</div>
        <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>MDE +15% relative</div>
      </div>
    </div>
    <div style={{ background: 'white', border: '1px solid var(--line)', borderRadius: 12, padding: 14, marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div className="label-xs">POWER ACHIEVED</div>
        <div style={{ fontWeight: 800, fontFamily: 'Plus Jakarta Sans', fontSize: 18 }}>0.82</div>
      </div>
      <div style={{ height: 8, background: 'var(--line-soft)', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: '82%', height: '100%', background: 'linear-gradient(90deg, #10B981, #14B8A6)' }} />
      </div>
    </div>
    <div style={{ background: 'white', border: '1px solid var(--line)', borderRadius: 12, padding: 14 }}>
      <div className="label-xs" style={{ marginBottom: 8 }}>Balance · covariate p-values</div>
      {[
        { k: 'industry (χ²)', v: 0.41 },
        { k: 'size (t-test)', v: 0.68 },
        { k: 'DMA tier (χ²)', v: 0.52 },
        { k: 'ad experience (χ²)', v: 0.73 },
      ].map((b, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '4px 0' }}>
          <span style={{ color: 'var(--text)' }}>{b.k}</span>
          <span style={{ fontWeight: 700, color: 'var(--emerald)' }}>p = {b.v}</span>
        </div>
      ))}
    </div>
  </div>
);

export default AgentShowcase;
