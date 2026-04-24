import React, { useState, useRef, useEffect } from 'react';
import { API_BASE, WS_BASE } from '../lib/api.js';

const EVENT_COLORS = { reasoning: '#8B5CF6', tool_call: '#6366F1', tool_result: '#06B6D4', completed: '#10B981', error: '#EF4444' };

const EventRow = ({ event }) => {
  const color = EVENT_COLORS[event.type] || '#9CA3AF';
  const label = event.tool_name ? `${event.type} · ${event.tool_name}` : event.type;
  const detail = event.thinking || event.message || null;
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 0', borderBottom: '1px solid #F3F4F6' }}>
      <span style={{ fontSize: 10, fontWeight: 700, color, fontFamily: 'monospace', textTransform: 'uppercase', whiteSpace: 'nowrap', paddingTop: 1, minWidth: 80 }}>{label}</span>
      {detail && <span style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5 }}>{detail}</span>}
    </div>
  );
};

const StatCard = ({ label, value, sub, color = '#6366F1' }) => (
  <div style={{ background: '#fff', border: `1.5px solid ${color}20`, borderRadius: 14, padding: '18px 20px', textAlign: 'center' }}>
    <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 8 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 900, color, letterSpacing: '-0.03em', lineHeight: 1 }}>{value}</div>
    {sub && <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 6 }}>{sub}</div>}
  </div>
);

const BalanceRow = ({ variable, pValue, balanced }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid #F3F4F6' }}>
    <div style={{ flex: 1, fontSize: 13, fontWeight: 600, color: '#374151' }}>{variable}</div>
    {pValue != null && <div style={{ fontSize: 12, color: '#6B7280', fontFamily: 'monospace' }}>p = {typeof pValue === 'number' ? pValue.toFixed(4) : pValue}</div>}
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: balanced ? '#10B981' : '#EF4444' }} />
      <span style={{ fontSize: 12, fontWeight: 700, color: balanced ? '#10B981' : '#EF4444' }}>{balanced ? 'Balanced' : 'Imbalanced'}</span>
    </div>
  </div>
);

const GroupPill = ({ label, n, pct, color }) => (
  <div style={{ flex: 1, background: `${color}08`, border: `1.5px solid ${color}25`, borderRadius: 12, padding: '16px', textAlign: 'center' }}>
    <div style={{ fontSize: 11, fontWeight: 700, color, textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6 }}>{label}</div>
    <div style={{ fontSize: 28, fontWeight: 900, color, letterSpacing: '-0.03em' }}>{n?.toLocaleString() ?? '—'}</div>
    <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 4 }}>{pct != null ? `${(pct * 100).toFixed(0)}% of pool` : 'participants'}</div>
  </div>
);

const ABTestConsole = ({ onBack }) => {
  const [formData, setFormData] = useState({
    experiment_name: '',
    campaign_id: null,
    baseline_conversion_rate: 0.05,
    minimum_detectable_effect: 0.20,
    mde_type: 'relative',
    desired_power: 0.80,
    significance_level: 0.05,
    test_fraction: 0.50,
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const eventsEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => { eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);
  useEffect(() => () => wsRef.current?.close(), []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numFields = ['campaign_id', 'baseline_conversion_rate', 'minimum_detectable_effect', 'desired_power', 'significance_level', 'test_fraction'];
    setFormData(p => ({ ...p, [name]: numFields.includes(name) ? (value === '' ? null : Number(value)) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setEvents([]); setResult(null);
    wsRef.current?.close();
    try {
      const res = await fetch(`${API_BASE}/agents/ab-test/design`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || res.statusText); }
      const data = await res.json();
      setResult(data);
      const ws = new WebSocket(`${WS_BASE}/ws/agent-events/${data.run_id}`);
      wsRef.current = ws;
      ws.onmessage = (ev) => { try { const d = JSON.parse(ev.data); if (d.type !== 'ping') setEvents(p => [...p, d]); } catch {} };
      ws.onerror = () => setEvents(p => [...p, { type: 'error', message: 'WebSocket failed' }]);
    } catch (err) {
      setEvents([{ type: 'error', message: err.message }]);
    } finally {
      setLoading(false);
    }
  };

  const out = result?.output || {};
  const sampleSize = out.required_sample_size || out.sample_size_per_group || out.total_sample_size;
  const power = out.achieved_power || out.power || formData.desired_power;
  const controlN = out.control_size || out.n_control;
  const treatN = out.treatment_size || out.n_treatment;
  const totalPool = out.eligible_pool || out.total_pool;
  const balance = out.balance_report || out.covariate_balance || out.balance;
  const stratification = out.stratification_variables || out.strata;

  const inputStyle = { width: '100%', padding: '10px 12px', border: '1.5px solid #E5E7EB', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box' };
  const labelStyle = { display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' };

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <div style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(255,255,255,0.96)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #E5E7EB', padding: '0 32px', height: 56, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 13, color: '#374151', fontWeight: 500 }}>← Back</button>
        <div style={{ width: 1, height: 18, background: '#E5E7EB' }} />
        <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg,#10B981,#06B6D4)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>🧪</div>
        <div>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0A0A0A' }}>A/B Testing Agent</span>
          <span style={{ fontSize: 12, color: '#9CA3AF', marginLeft: 8 }}>Power analysis · stratified assignment · balance validation</span>
        </div>
        {loading && <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#10B981', fontWeight: 600 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10B981' }} /> Designing…
        </div>}
      </div>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px', display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24 }}>
        {/* Form */}
        <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '28px', height: 'fit-content', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0A0A0A', margin: '0 0 24px 0', letterSpacing: '-0.02em' }}>Experiment Design</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>Experiment Name</label>
              <input type="text" name="experiment_name" value={formData.experiment_name} onChange={handleChange} placeholder="e.g. Email subject line test" required style={inputStyle} />
            </div>

            <div style={{ background: '#F8F9FA', borderRadius: 10, padding: '14px', marginBottom: 16 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 12 }}>Statistical Parameters</div>
              {[
                { label: 'Baseline Conversion Rate', name: 'baseline_conversion_rate', min: 0.001, max: 1, step: 0.01 },
                { label: 'Minimum Detectable Effect', name: 'minimum_detectable_effect', min: 0.01, step: 0.01 },
                { label: 'Desired Power', name: 'desired_power', min: 0.5, max: 0.99, step: 0.05 },
                { label: 'Significance Level (α)', name: 'significance_level', min: 0.01, max: 0.2, step: 0.01 },
                { label: 'Test Fraction', name: 'test_fraction', min: 0.1, max: 0.9, step: 0.05 },
              ].map(f => (
                <div key={f.name} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <label style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>{f.label}</label>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#6366F1', fontFamily: 'monospace' }}>{formData[f.name]}</span>
                  </div>
                  <input type="range" name={f.name} value={formData[f.name]} onChange={handleChange} min={f.min} max={f.max} step={f.step} style={{ width: '100%', accentColor: '#10B981' }} />
                </div>
              ))}
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={labelStyle}>MDE Type</label>
              <select name="mde_type" value={formData.mde_type} onChange={handleChange} style={inputStyle}>
                <option value="relative">Relative (% lift)</option>
                <option value="absolute">Absolute (pp change)</option>
              </select>
            </div>

            <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: loading ? '#E5E7EB' : 'linear-gradient(135deg,#10B981,#06B6D4)', color: loading ? '#9CA3AF' : '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? 'Designing experiment…' : 'Design Experiment →'}
            </button>
          </form>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Timeline */}
          <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: loading ? '#10B981' : events.length ? '#10B981' : '#D1D5DB' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Execution Timeline</span>
            </div>
            {events.length === 0 && !loading
              ? <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>Submit to see live experiment design events.</p>
              : <div style={{ maxHeight: 180, overflowY: 'auto' }}>{events.map((ev, i) => <EventRow key={i} event={ev} />)}</div>
            }
            <div ref={eventsEndRef} />
          </div>

          {/* Key stats */}
          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
              <StatCard label="Required Sample" value={sampleSize != null ? Number(sampleSize).toLocaleString() : '—'} sub="per group" color="#10B981" />
              <StatCard label="Statistical Power" value={power != null ? `${(power * 100).toFixed(0)}%` : '—'} sub={`target: ${(formData.desired_power * 100).toFixed(0)}%`} color="#6366F1" />
              <StatCard label="Significance α" value={formData.significance_level} sub={`${((1 - formData.significance_level) * 100).toFixed(0)}% confidence`} color="#8B5CF6" />
              <StatCard label="Eligible Pool" value={totalPool != null ? Number(totalPool).toLocaleString() : '—'} sub="SMB advertisers" color="#06B6D4" />
            </div>
          )}

          {/* Group split */}
          {(controlN != null || treatN != null) && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: '0 0 16px 0' }}>Group Assignment</h3>
              <div style={{ display: 'flex', gap: 14 }}>
                <GroupPill label="Control" n={controlN} pct={controlN && totalPool ? controlN / totalPool : null} color="#6366F1" />
                <GroupPill label="Treatment" n={treatN} pct={treatN && totalPool ? treatN / totalPool : null} color="#10B981" />
              </div>
            </div>
          )}

          {/* Covariate balance */}
          {balance && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: '0 0 4px 0' }}>Covariate Balance</h3>
              <p style={{ fontSize: 12, color: '#9CA3AF', margin: '0 0 16px 0' }}>Chi-square + Welch's t-test validation per stratification variable</p>
              {Array.isArray(balance)
                ? balance.map((b, i) => <BalanceRow key={i} variable={b.variable || b.covariate || `Variable ${i + 1}`} pValue={b.p_value} balanced={b.balanced ?? b.p_value > 0.05} />)
                : typeof balance === 'object'
                  ? Object.entries(balance).map(([k, v]) => <BalanceRow key={k} variable={k} pValue={typeof v === 'object' ? v.p_value : null} balanced={typeof v === 'object' ? v.balanced : v} />)
                  : <p style={{ fontSize: 13, color: '#374151', margin: 0 }}>{String(balance)}</p>
              }
            </div>
          )}

          {/* Stratification */}
          {stratification && (
            <div style={{ background: '#F0FDF4', border: '1px solid #86EFAC', borderRadius: 16, padding: '20px 24px' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#166534', margin: '0 0 12px 0' }}>Stratification Variables</h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {(Array.isArray(stratification) ? stratification : Object.keys(stratification)).map(s => (
                  <span key={s} style={{ background: '#DCFCE7', border: '1px solid #86EFAC', borderRadius: 20, padding: '5px 14px', fontSize: 13, fontWeight: 600, color: '#166534' }}>{s}</span>
                ))}
              </div>
            </div>
          )}

          {/* Fallback */}
          {result && !sampleSize && !controlN && (
            <div style={{ background: '#0D1117', border: '1px solid #21262D', borderRadius: 16, padding: '20px 24px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>Experiment Output</div>
              <pre style={{ margin: 0, fontSize: 12, color: '#E6EDF3', fontFamily: '"SF Mono","Fira Code",monospace', overflowX: 'auto', lineHeight: 1.7 }}>{JSON.stringify(result.output, null, 2)}</pre>
            </div>
          )}

          {events.some(e => e.type === 'error') && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 12, padding: '16px 20px' }}>
              <div style={{ fontWeight: 700, color: '#DC2626', fontSize: 14, marginBottom: 4 }}>Error</div>
              <p style={{ fontSize: 13, color: '#7F1D1D', margin: 0 }}>{events.find(e => e.type === 'error')?.message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ABTestConsole;
