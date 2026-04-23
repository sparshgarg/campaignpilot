import React, { useState, useRef, useEffect } from 'react';
import { API_BASE, WS_BASE } from '../lib/api.js';

const EVENT_COLORS = { reasoning: '#8B5CF6', tool_call: '#6366F1', tool_result: '#06B6D4', completed: '#10B981', error: '#EF4444' };

const EventRow = ({ event }) => {
  const color = EVENT_COLORS[event.type] || '#9CA3AF';
  const label = event.tool_name ? `${event.type} · ${event.tool_name}` : event.type;
  const detail = event.thinking || event.message || (event.input ? JSON.stringify(event.input).slice(0, 100) + '…' : null);
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 0', borderBottom: '1px solid #F3F4F6' }}>
      <span style={{ fontSize: 10, fontWeight: 700, color, fontFamily: 'monospace', textTransform: 'uppercase', whiteSpace: 'nowrap', paddingTop: 1, minWidth: 90 }}>{label}</span>
      {detail && <span style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5 }}>{detail}</span>}
    </div>
  );
};

const ImpactBadge = ({ impact }) => {
  const str = String(impact || '').toLowerCase();
  const isHigh = str.includes('high') || str.includes('critical');
  const isMed = str.includes('med') || str.includes('moderate');
  const color = isHigh ? '#EF4444' : isMed ? '#F59E0B' : '#10B981';
  return (
    <span style={{ fontSize: 11, fontWeight: 700, color, background: `${color}15`, border: `1px solid ${color}30`, borderRadius: 20, padding: '2px 10px' }}>{impact || 'Normal'}</span>
  );
};

const BudgetBar = ({ label, current, recommended, max }) => {
  const currentPct = Math.min(100, (current / max) * 100);
  const recPct = Math.min(100, (recommended / max) * 100);
  const delta = recommended - current;
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: '#9CA3AF' }}>${current?.toLocaleString()}</span>
          <span style={{ fontSize: 12, color: '#9CA3AF' }}>→</span>
          <span style={{ fontSize: 12, fontWeight: 700, color: delta > 0 ? '#10B981' : delta < 0 ? '#EF4444' : '#9CA3AF' }}>${recommended?.toLocaleString()}</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: delta > 0 ? '#10B981' : '#EF4444' }}>{delta > 0 ? `+$${delta?.toLocaleString()}` : `-$${Math.abs(delta)?.toLocaleString()}`}</span>
        </div>
      </div>
      <div style={{ height: 8, background: '#F3F4F6', borderRadius: 4, overflow: 'hidden', position: 'relative' }}>
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${recPct}%`, background: delta > 0 ? '#10B981' : '#EF4444', borderRadius: 4, opacity: 0.3 }} />
        <div style={{ position: 'absolute', left: 0, top: 0, height: '100%', width: `${currentPct}%`, background: '#6366F1', borderRadius: 4 }} />
      </div>
    </div>
  );
};

const RecommendationCard = ({ rec, index }) => {
  const r = typeof rec === 'object' ? rec : { action: String(rec) };
  return (
    <div style={{ border: '1.5px solid #E5E7EB', borderRadius: 12, padding: '16px 20px', marginBottom: 12 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, marginBottom: r.rationale ? 10 : 0 }}>
        <div style={{ width: 26, height: 26, borderRadius: 8, background: 'linear-gradient(135deg,#F59E0B,#EF4444)', color: '#fff', fontWeight: 800, fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{index + 1}</div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 14, fontWeight: 700, color: '#0A0A0A' }}>{r.action || r.recommendation || r.title}</span>
            {(r.impact || r.priority) && <ImpactBadge impact={r.impact || r.priority} />}
          </div>
          {r.channel && <span style={{ fontSize: 12, color: '#6366F1', fontWeight: 600, marginTop: 2, display: 'block' }}>{r.channel}</span>}
        </div>
        {r.expected_roi_delta != null && (
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 18, fontWeight: 800, color: '#10B981' }}>{r.expected_roi_delta > 0 ? '+' : ''}{r.expected_roi_delta}%</div>
            <div style={{ fontSize: 10, color: '#9CA3AF' }}>ROI delta</div>
          </div>
        )}
      </div>
      {r.rationale && <p style={{ fontSize: 13, color: '#6B7280', margin: '0 0 0 38px', lineHeight: 1.6 }}>{r.rationale}</p>}
      {r.budget_adjustment != null && (
        <div style={{ marginTop: 10, marginLeft: 38, display: 'flex', gap: 10 }}>
          <span style={{ fontSize: 12, background: '#F3F4F6', borderRadius: 6, padding: '4px 10px', color: '#374151' }}>
            Budget adjustment: <strong>{r.budget_adjustment > 0 ? '+' : ''}${r.budget_adjustment?.toLocaleString()}</strong>
          </span>
        </div>
      )}
    </div>
  );
};

const OptimizerConsole = ({ onBack }) => {
  const [formData, setFormData] = useState({ campaign_id: 1, campaign_name: '', remaining_budget_usd: 5000, days_remaining: 14 });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const eventsEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => { eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);
  useEffect(() => () => wsRef.current?.close(), []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const nums = ['campaign_id', 'remaining_budget_usd', 'days_remaining'];
    setFormData(p => ({ ...p, [name]: nums.includes(name) ? Number(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setEvents([]); setResult(null);
    wsRef.current?.close();
    try {
      const res = await fetch(`${API_BASE}/agents/optimizer/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
      if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || res.statusText); }
      const data = await res.json();
      setResult(data);
      const ws = new WebSocket(`${WS_BASE}/ws/agent-events/${data.run_id}`);
      wsRef.current = ws;
      ws.onmessage = (ev) => { try { setEvents(p => [...p, JSON.parse(ev.data)]); } catch {} };
      ws.onerror = () => setEvents(p => [...p, { type: 'error', message: 'WebSocket failed' }]);
    } catch (err) {
      setEvents([{ type: 'error', message: err.message }]);
    } finally {
      setLoading(false);
    }
  };

  const out = result?.output || {};
  const recs = out.recommendations || out.actions || out.optimizations || [];
  const summary = out.summary || out.executive_summary;
  const budgetAlloc = out.budget_reallocation || out.channel_budgets;

  const inputStyle = { width: '100%', padding: '10px 12px', border: '1.5px solid #E5E7EB', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box' };

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      <div style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(255,255,255,0.96)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #E5E7EB', padding: '0 32px', height: 56, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 13, color: '#374151', fontWeight: 500 }}>← Back</button>
        <div style={{ width: 1, height: 18, background: '#E5E7EB' }} />
        <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg,#F59E0B,#EF4444)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>⚡</div>
        <div>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0A0A0A' }}>Optimizer Agent</span>
          <span style={{ fontSize: 12, color: '#9CA3AF', marginLeft: 8 }}>Budget reallocation · channel optimization</span>
        </div>
        {loading && <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#F59E0B', fontWeight: 600 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#F59E0B' }} /> Optimizing…
        </div>}
      </div>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px', display: 'grid', gridTemplateColumns: '340px 1fr', gap: 24 }}>
        {/* Form */}
        <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '28px', height: 'fit-content', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0A0A0A', margin: '0 0 24px 0', letterSpacing: '-0.02em' }}>Campaign Details</h2>
          <form onSubmit={handleSubmit}>
            {[
              { label: 'Campaign ID', name: 'campaign_id', type: 'number', min: 1 },
              { label: 'Campaign Name', name: 'campaign_name', type: 'text', placeholder: 'e.g. Q2 Restaurant Growth', required: true },
              { label: 'Remaining Budget (USD)', name: 'remaining_budget_usd', type: 'number', min: 100, max: 1000000, required: true },
              { label: 'Days Remaining', name: 'days_remaining', type: 'number', min: 1, max: 365, required: true },
            ].map(f => (
              <div key={f.name} style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' }}>{f.label}</label>
                <input type={f.type} name={f.name} value={formData[f.name]} onChange={handleChange} placeholder={f.placeholder} required={f.required} min={f.min} max={f.max} style={inputStyle} />
              </div>
            ))}
            <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: loading ? '#E5E7EB' : 'linear-gradient(135deg,#F59E0B,#EF4444)', color: loading ? '#9CA3AF' : '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', marginTop: 8 }}>
              {loading ? 'Optimizing…' : 'Get Optimization →'}
            </button>
          </form>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Timeline */}
          <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: loading ? '#F59E0B' : events.length ? '#10B981' : '#D1D5DB' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Execution Timeline</span>
            </div>
            {events.length === 0 && !loading
              ? <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>Submit to see live optimization events.</p>
              : <div style={{ maxHeight: 180, overflowY: 'auto' }}>{events.map((ev, i) => <EventRow key={i} event={ev} />)}</div>
            }
            <div ref={eventsEndRef} />
          </div>

          {/* Metrics */}
          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Latency', value: `${Math.round(result.latency_ms)}ms` },
                { label: 'Input tokens', value: result.total_input_tokens?.toLocaleString() },
                { label: 'Output tokens', value: result.total_output_tokens?.toLocaleString() },
                { label: 'Actions', value: recs.length || '—' },
              ].map(m => (
                <div key={m.label} style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 16px' }}>
                  <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>{m.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#0A0A0A' }}>{m.value}</div>
                </div>
              ))}
            </div>
          )}

          {/* Summary */}
          {summary && (
            <div style={{ background: '#FFFBEB', border: '1px solid #FDE68A', borderRadius: 16, padding: '20px 24px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#92400E', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>Executive Summary</div>
              <p style={{ fontSize: 14, color: '#78350F', lineHeight: 1.7, margin: 0 }}>{summary}</p>
            </div>
          )}

          {/* Budget reallocation */}
          {budgetAlloc && typeof budgetAlloc === 'object' && !Array.isArray(budgetAlloc) && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: '0 0 20px 0' }}>Budget Reallocation</h3>
              {Object.entries(budgetAlloc).map(([ch, val]) => {
                const cur = typeof val === 'object' ? val.current : val;
                const rec = typeof val === 'object' ? val.recommended : val;
                const maxVal = Math.max(...Object.values(budgetAlloc).map(v => typeof v === 'object' ? Math.max(v.current, v.recommended) : v)) * 1.2;
                return <BudgetBar key={ch} label={ch} current={cur} recommended={rec} max={maxVal} />;
              })}
            </div>
          )}

          {/* Recommendations */}
          {recs.length > 0 && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: '0 0 16px 0' }}>Optimization Actions</h3>
              {recs.map((r, i) => <RecommendationCard key={i} rec={r} index={i} />)}
            </div>
          )}

          {/* Fallback */}
          {result && !summary && !recs.length && !budgetAlloc && (
            <div style={{ background: '#0D1117', border: '1px solid #21262D', borderRadius: 16, padding: '20px 24px' }}>
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

export default OptimizerConsole;
