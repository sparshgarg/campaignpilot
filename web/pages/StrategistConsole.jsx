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

const ChannelBar = ({ channel, amount, total }) => {
  const pct = total > 0 ? (amount / total) * 100 : 0;
  const colors = { LinkedIn: '#6366F1', Email: '#06B6D4', Content: '#10B981', Search: '#F59E0B', Display: '#EC4899', Social: '#8B5CF6', default: '#9CA3AF' };
  const color = colors[channel] || colors.default;
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: '#374151' }}>{channel}</span>
        <span style={{ fontSize: 13, fontWeight: 700, color }}>
          ${typeof amount === 'number' ? amount.toLocaleString() : amount} <span style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 400 }}>({pct.toFixed(0)}%)</span>
        </span>
      </div>
      <div style={{ height: 6, background: '#F3F4F6', borderRadius: 3, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: color, borderRadius: 3, transition: 'width 0.4s ease' }} />
      </div>
    </div>
  );
};

const KPIChip = ({ kpi }) => (
  <span style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.2)', color: '#6366F1', borderRadius: 20, padding: '4px 12px', fontSize: 12, fontWeight: 600 }}>{kpi}</span>
);

const RiskChip = ({ risk }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', background: '#FFF7ED', border: '1px solid #FDE68A', borderRadius: 8 }}>
    <span style={{ color: '#F59E0B', fontSize: 14 }}>⚠</span>
    <span style={{ fontSize: 13, color: '#92400E' }}>{risk}</span>
  </div>
);

const StrategistConsole = ({ onBack }) => {
  const [formData, setFormData] = useState({ campaign_goal: '', budget_usd: 50000, timeline_days: 90, target_segment: '' });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const eventsEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => { eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);
  useEffect(() => () => wsRef.current?.close(), []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(p => ({ ...p, [name]: name === 'budget_usd' || name === 'timeline_days' ? Number(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setEvents([]); setResult(null);
    wsRef.current?.close();
    try {
      const res = await fetch(`${API_BASE}/agents/strategist/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
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
  const budgetAlloc = out.budget_allocation || out.channel_mix;
  const totalBudget = budgetAlloc ? Object.values(budgetAlloc).reduce((s, v) => s + (typeof v === 'number' ? v : 0), 0) : 0;
  const channels = out.recommended_channels || (budgetAlloc ? Object.keys(budgetAlloc) : []);
  const kpis = out.primary_kpis || out.kpis || [];
  const risks = out.key_risks || out.risks || [];
  const rationale = out.rationale || out.strategy_rationale;
  const timeline = out.timeline_recommendation || out.timeline;

  const inputStyle = { width: '100%', padding: '10px 12px', border: '1.5px solid #E5E7EB', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box' };

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Top bar */}
      <div style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(255,255,255,0.96)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #E5E7EB', padding: '0 32px', height: 56, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 13, color: '#374151', fontWeight: 500 }}>← Back</button>
        <div style={{ width: 1, height: 18, background: '#E5E7EB' }} />
        <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg,#6366F1,#8B5CF6)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>🧠</div>
        <div>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0A0A0A' }}>Strategist Agent</span>
          <span style={{ fontSize: 12, color: '#9CA3AF', marginLeft: 8 }}>Multi-channel campaign brief · budget allocation · KPI planning</span>
        </div>
        {loading && <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#6366F1', fontWeight: 600 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#6366F1' }} /> Generating…
        </div>}
      </div>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px', display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24 }}>
        {/* Form */}
        <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '28px', height: 'fit-content', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0A0A0A', margin: '0 0 24px 0', letterSpacing: '-0.02em' }}>Campaign Brief</h2>
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' }}>Campaign Goal</label>
              <textarea name="campaign_goal" value={formData.campaign_goal} onChange={handleChange} placeholder="e.g. Generate 50 MQLs for enterprise SaaS in Q4" required rows={3} style={{ ...inputStyle, resize: 'vertical' }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <label style={{ fontWeight: 600, fontSize: 13, color: '#374151' }}>Total Budget</label>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#6366F1' }}>${formData.budget_usd.toLocaleString()}</span>
              </div>
              <input type="range" name="budget_usd" value={formData.budget_usd} onChange={handleChange} min={1000} max={500000} step={1000} style={{ width: '100%', accentColor: '#6366F1' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9CA3AF', marginTop: 2 }}><span>$1K</span><span>$500K</span></div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <label style={{ fontWeight: 600, fontSize: 13, color: '#374151' }}>Timeline</label>
                <span style={{ fontSize: 13, fontWeight: 700, color: '#6366F1' }}>{formData.timeline_days} days</span>
              </div>
              <input type="range" name="timeline_days" value={formData.timeline_days} onChange={handleChange} min={7} max={365} step={7} style={{ width: '100%', accentColor: '#6366F1' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9CA3AF', marginTop: 2 }}><span>1 week</span><span>1 year</span></div>
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' }}>Target Segment</label>
              <input type="text" name="target_segment" value={formData.target_segment} onChange={handleChange} placeholder="e.g. VP Engineering at Series B SaaS companies" required style={inputStyle} />
            </div>
            <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: loading ? '#E5E7EB' : 'linear-gradient(135deg,#6366F1,#8B5CF6)', color: loading ? '#9CA3AF' : '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? 'Generating brief…' : 'Generate Strategy →'}
            </button>
          </form>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Timeline */}
          <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: loading ? '#6366F1' : events.length ? '#10B981' : '#D1D5DB' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Execution Timeline</span>
              {events.length > 0 && <span style={{ fontSize: 11, color: '#9CA3AF', marginLeft: 'auto' }}>{events.length} events</span>}
            </div>
            {events.length === 0 && !loading
              ? <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>Submit to see live agent reasoning and tool calls.</p>
              : <div style={{ maxHeight: 200, overflowY: 'auto' }}>{events.map((ev, i) => <EventRow key={i} event={ev} />)}</div>
            }
            <div ref={eventsEndRef} />
          </div>

          {/* Metrics row */}
          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Latency', value: `${Math.round(result.latency_ms)}ms` },
                { label: 'Input tokens', value: result.total_input_tokens?.toLocaleString() },
                { label: 'Output tokens', value: result.total_output_tokens?.toLocaleString() },
                { label: 'Channels', value: channels.length || '—' },
              ].map(m => (
                <div key={m.label} style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 16px' }}>
                  <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>{m.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#0A0A0A' }}>{m.value}</div>
                </div>
              ))}
            </div>
          )}

          {/* Budget allocation */}
          {budgetAlloc && totalBudget > 0 && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: 0 }}>Budget Allocation</h3>
                <span style={{ fontSize: 14, fontWeight: 700, color: '#6366F1' }}>${totalBudget.toLocaleString()} total</span>
              </div>
              {Object.entries(budgetAlloc).map(([ch, amt]) => (
                <ChannelBar key={ch} channel={ch} amount={typeof amt === 'number' ? amt : parseInt(amt)} total={totalBudget} />
              ))}
            </div>
          )}

          {/* KPIs + Timeline side by side */}
          {(kpis.length > 0 || timeline) && (
            <div style={{ display: 'grid', gridTemplateColumns: kpis.length && timeline ? '1fr 1fr' : '1fr', gap: 16 }}>
              {kpis.length > 0 && (
                <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px' }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0A0A0A', margin: '0 0 14px 0' }}>Primary KPIs</h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {kpis.map(k => <KPIChip key={k} kpi={k} />)}
                  </div>
                </div>
              )}
              {timeline && (
                <div style={{ background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: 16, padding: '20px 24px' }}>
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0369A1', margin: '0 0 8px 0' }}>Recommended Timeline</h3>
                  <p style={{ fontSize: 14, color: '#0C4A6E', margin: 0, lineHeight: 1.6 }}>{timeline}</p>
                </div>
              )}
            </div>
          )}

          {/* Rationale */}
          {rationale && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0A0A0A', margin: '0 0 10px 0' }}>Strategic Rationale</h3>
              <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.7, margin: 0 }}>{rationale}</p>
            </div>
          )}

          {/* Risks */}
          {risks.length > 0 && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: '#0A0A0A', margin: '0 0 12px 0' }}>Key Risks</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {risks.map((r, i) => <RiskChip key={i} risk={r} />)}
              </div>
            </div>
          )}

          {/* Trace link */}
          {result?.trace_url && (
            <div style={{ textAlign: 'right' }}>
              <a href={result.trace_url} target="_blank" rel="noopener noreferrer" style={{ fontSize: 12, color: '#6366F1', fontWeight: 600, textDecoration: 'none' }}>View full trace in Langfuse →</a>
            </div>
          )}

          {/* Fallback JSON */}
          {result && !budgetAlloc && !rationale && (
            <div style={{ background: '#0D1117', border: '1px solid #21262D', borderRadius: 16, padding: '20px 24px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>Raw Output</div>
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

export default StrategistConsole;
