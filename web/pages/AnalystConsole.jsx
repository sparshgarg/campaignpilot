import React, { useState, useRef, useEffect } from 'react';
import { API_BASE, WS_BASE } from '../lib/api.js';

const EVENT_COLORS = { reasoning: '#8B5CF6', tool_call: '#6366F1', tool_result: '#06B6D4', completed: '#10B981', error: '#EF4444' };

const EXAMPLE_QUESTIONS = [
  'What is the ROAS by channel for the last 30 days?',
  'Which campaigns have the highest click-through rate?',
  'Show me total spend vs conversions by channel',
  'What is the average CAC across all campaigns?',
];

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

const SqlBlock = ({ sql }) => (
  <div style={{ background: '#0D1117', border: '1px solid #21262D', borderRadius: 12, padding: '16px 20px', marginBottom: 20 }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Generated SQL</span>
      <span style={{ fontSize: 10, background: '#21262D', color: '#6B7280', borderRadius: 4, padding: '2px 6px', fontFamily: 'monospace' }}>SELECT only · validated</span>
    </div>
    <pre style={{ margin: 0, fontSize: 12, color: '#E6EDF3', fontFamily: '"SF Mono","Fira Code",monospace', lineHeight: 1.7, overflowX: 'auto', whiteSpace: 'pre-wrap' }}>{sql}</pre>
  </div>
);

const DataTable = ({ rows }) => {
  if (!rows || rows.length === 0) return null;
  const cols = Object.keys(rows[0]);
  return (
    <div style={{ overflowX: 'auto', borderRadius: 12, border: '1px solid #E5E7EB', marginBottom: 20 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr>{cols.map(c => <th key={c} style={{ padding: '10px 14px', background: '#F8F9FA', fontWeight: 700, color: '#374151', textAlign: 'left', borderBottom: '1px solid #E5E7EB', whiteSpace: 'nowrap' }}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.slice(0, 20).map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? '#fff' : '#FAFAFA' }}>
              {cols.map(c => <td key={c} style={{ padding: '9px 14px', borderBottom: '1px solid #F3F4F6', color: '#374151' }}>{row[c] ?? '—'}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > 20 && <div style={{ padding: '8px 14px', fontSize: 12, color: '#9CA3AF', background: '#F8F9FA' }}>{rows.length - 20} more rows…</div>}
    </div>
  );
};

const AnalystConsole = ({ onBack }) => {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const eventsEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => { eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);
  useEffect(() => () => wsRef.current?.close(), []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true); setEvents([]); setResult(null);
    wsRef.current?.close();

    try {
      const res = await fetch(`${API_BASE}/agents/analyst/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question }) });
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
  const sql = out.sql || out.query;
  const rows = out.results || out.data || out.rows;
  const insight = out.insight || out.narrative || out.answer || out.summary;
  const dataQuality = out.data_quality || out.quality;

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Top bar */}
      <div style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(255,255,255,0.96)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #E5E7EB', padding: '0 32px', height: 56, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 13, color: '#374151', fontWeight: 500 }}>← Back</button>
        <div style={{ width: 1, height: 18, background: '#E5E7EB' }} />
        <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg,#06B6D4,#6366F1)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>📊</div>
        <div>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0A0A0A' }}>Analyst Agent</span>
          <span style={{ fontSize: 12, color: '#9CA3AF', marginLeft: 8 }}>Natural language → SQL → business insights</span>
        </div>
        {loading && <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#06B6D4', fontWeight: 600 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#06B6D4' }} /> Analyzing…
        </div>}
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px' }}>
        {/* Query box */}
        <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '24px 28px', marginBottom: 24, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0A0A0A', margin: '0 0 6px 0', letterSpacing: '-0.02em' }}>Ask a question</h2>
          <p style={{ fontSize: 13, color: '#9CA3AF', margin: '0 0 18px 0' }}>The agent writes SQL, executes it, and explains the results in plain English.</p>

          <form onSubmit={handleSubmit}>
            <div style={{ display: 'flex', gap: 12 }}>
              <input
                value={question}
                onChange={e => setQuestion(e.target.value)}
                placeholder="e.g. What is the ROAS by channel for the last 30 days?"
                required
                style={{ flex: 1, padding: '12px 16px', border: '1.5px solid #E5E7EB', borderRadius: 10, fontSize: 14, fontFamily: 'inherit', outline: 'none' }}
              />
              <button type="submit" disabled={loading} style={{ padding: '12px 24px', background: loading ? '#E5E7EB' : 'linear-gradient(135deg,#06B6D4,#6366F1)', color: loading ? '#9CA3AF' : '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', whiteSpace: 'nowrap' }}>
                {loading ? 'Analyzing…' : 'Analyze →'}
              </button>
            </div>
          </form>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 14 }}>
            <span style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600 }}>Try:</span>
            {EXAMPLE_QUESTIONS.map(q => (
              <button key={q} onClick={() => setQuestion(q)} style={{ background: 'none', border: '1px solid #E5E7EB', borderRadius: 20, padding: '4px 12px', fontSize: 12, color: '#6B7280', cursor: 'pointer' }}>{q}</button>
            ))}
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
          {/* Execution timeline */}
          <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: loading ? '#06B6D4' : events.length ? '#10B981' : '#D1D5DB' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Execution Timeline</span>
            </div>
            {events.length === 0 && !loading
              ? <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>Ask a question to see live execution events.</p>
              : <div style={{ maxHeight: 300, overflowY: 'auto' }}>{events.map((ev, i) => <EventRow key={i} event={ev} />)}</div>
            }
            <div ref={eventsEndRef} />
          </div>

          {/* Metrics */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {result && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {[
                  { label: 'Latency', value: `${Math.round(result.latency_ms)}ms` },
                  { label: 'Input tokens', value: result.total_input_tokens?.toLocaleString() },
                  { label: 'Output tokens', value: result.total_output_tokens?.toLocaleString() },
                  { label: 'Rows returned', value: Array.isArray(rows) ? rows.length : '—' },
                ].map(m => (
                  <div key={m.label} style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 16px' }}>
                    <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>{m.label}</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: '#0A0A0A' }}>{m.value}</div>
                  </div>
                ))}
              </div>
            )}
            {dataQuality && (
              <div style={{ background: '#F0F9FF', border: '1px solid #BAE6FD', borderRadius: 12, padding: '14px 16px' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#0369A1', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>Data Quality</div>
                <p style={{ fontSize: 13, color: '#0C4A6E', margin: 0, lineHeight: 1.6 }}>{typeof dataQuality === 'string' ? dataQuality : JSON.stringify(dataQuality)}</p>
              </div>
            )}
          </div>
        </div>

        {/* Results */}
        {result && (
          <div style={{ marginTop: 24 }}>
            {insight && (
              <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '24px 28px', marginBottom: 20, boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 10 }}>Business Insight</div>
                <p style={{ fontSize: 15, color: '#0A0A0A', lineHeight: 1.7, margin: 0 }}>{insight}</p>
              </div>
            )}
            {sql && <SqlBlock sql={sql} />}
            {Array.isArray(rows) && rows.length > 0 && (
              <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 14 }}>Query Results</div>
                <DataTable rows={rows} />
              </div>
            )}
            {!insight && !sql && !rows && (
              <div style={{ background: '#0D1117', border: '1px solid #21262D', borderRadius: 16, padding: '20px 24px' }}>
                <pre style={{ margin: 0, fontSize: 12, color: '#E6EDF3', fontFamily: '"SF Mono","Fira Code",monospace', overflowX: 'auto', lineHeight: 1.7 }}>{JSON.stringify(result.output, null, 2)}</pre>
              </div>
            )}
          </div>
        )}

        {events.some(e => e.type === 'error') && (
          <div style={{ marginTop: 16, background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 12, padding: '16px 20px' }}>
            <div style={{ fontWeight: 700, color: '#DC2626', fontSize: 14, marginBottom: 4 }}>Error</div>
            <p style={{ fontSize: 13, color: '#7F1D1D', margin: 0 }}>{events.find(e => e.type === 'error')?.message}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalystConsole;
