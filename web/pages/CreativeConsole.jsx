import React, { useState, useRef, useEffect } from 'react';
import { API_BASE, WS_BASE } from '../lib/api.js';

const CHANNELS = ['facebook', 'instagram', 'reels', 'linkedin', 'email', 'search', 'display', 'tiktok'];
const TONES = ['professional', 'friendly', 'urgent', 'educational', 'humorous', 'inspirational'];

const EVENT_COLORS = { reasoning: '#8B5CF6', tool_call: '#6366F1', tool_result: '#06B6D4', completed: '#10B981', error: '#EF4444' };

const EventRow = ({ event }) => {
  const color = EVENT_COLORS[event.type] || '#9CA3AF';
  const label = event.tool_name ? `${event.type} · ${event.tool_name}` : event.type;
  const detail = event.thinking || event.message || (event.input ? JSON.stringify(event.input).slice(0, 80) + '…' : null);
  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '8px 0', borderBottom: '1px solid #F3F4F6' }}>
      <span style={{ fontSize: 10, fontWeight: 700, color, fontFamily: 'monospace', textTransform: 'uppercase', whiteSpace: 'nowrap', paddingTop: 1, minWidth: 80 }}>{label}</span>
      {detail && <span style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.5 }}>{detail}</span>}
    </div>
  );
};

const SafetyBadge = ({ score }) => {
  const pct = typeof score === 'number' ? score : parseFloat(score) || 0;
  const color = pct >= 0.8 ? '#10B981' : pct >= 0.5 ? '#F59E0B' : '#EF4444';
  const label = pct >= 0.8 ? 'Brand Safe' : pct >= 0.5 ? 'Review' : 'Flagged';
  return (
    <span style={{ fontSize: 11, fontWeight: 700, color, background: `${color}15`, border: `1px solid ${color}40`, borderRadius: 20, padding: '2px 10px' }}>
      {label} {Math.round(pct * 100)}%
    </span>
  );
};

const VariantCard = ({ variant, index }) => {
  const [expanded, setExpanded] = useState(index === 0);
  const v = typeof variant === 'object' ? variant : {};
  return (
    <div style={{ border: '1.5px solid #E5E7EB', borderRadius: 12, overflow: 'hidden', marginBottom: 12 }}>
      <button onClick={() => setExpanded(e => !e)} style={{ width: '100%', background: expanded ? '#FAFAFA' : '#fff', border: 'none', padding: '14px 16px', display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer', textAlign: 'left' }}>
        <div style={{ width: 24, height: 24, borderRadius: 6, background: 'linear-gradient(135deg,#EC4899,#F59E0B)', color: '#fff', fontWeight: 800, fontSize: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{index + 1}</div>
        <span style={{ fontWeight: 600, fontSize: 14, color: '#0A0A0A', flex: 1 }}>{v.headline || v.subject_line || `Variant ${index + 1}`}</span>
        {v.brand_safety_score != null && <SafetyBadge score={v.brand_safety_score} />}
        <span style={{ color: '#9CA3AF', fontSize: 14 }}>{expanded ? '↑' : '↓'}</span>
      </button>
      {expanded && (
        <div style={{ padding: '0 16px 16px', borderTop: '1px solid #F3F4F6' }}>
          {v.body && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>Body</div>
              <p style={{ fontSize: 13, color: '#374151', lineHeight: 1.6, margin: 0 }}>{v.body}</p>
            </div>
          )}
          {v.cta && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>CTA</div>
              <span style={{ background: 'linear-gradient(135deg,#EC4899,#F59E0B)', color: '#fff', borderRadius: 6, padding: '4px 12px', fontSize: 12, fontWeight: 700 }}>{v.cta}</span>
            </div>
          )}
          {v.rationale && (
            <div style={{ marginTop: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>Why it works</div>
              <p style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.6, margin: 0 }}>{v.rationale}</p>
            </div>
          )}
          {v.prohibited_flags && v.prohibited_flags.length > 0 && (
            <div style={{ marginTop: 12, background: '#FFF7ED', border: '1px solid #FED7AA', borderRadius: 8, padding: '8px 12px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#92400E', marginBottom: 4 }}>Brand flags</div>
              <div style={{ fontSize: 12, color: '#92400E' }}>{v.prohibited_flags.join(', ')}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const CreativeConsole = ({ onBack }) => {
  const [formData, setFormData] = useState({ channel: 'linkedin', product: '', persona: '', tone: 'professional', key_message: '', num_variants: 3 });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const eventsEndRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => { eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [events]);
  useEffect(() => () => wsRef.current?.close(), []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(p => ({ ...p, [name]: name === 'num_variants' ? Number(value) : value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setEvents([]); setResult(null);
    wsRef.current?.close();

    try {
      const res = await fetch(`${API_BASE}/agents/creative/run`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData) });
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

  const variants = result?.output?.variants || (Array.isArray(result?.output) ? result.output : null);

  const inputStyle = { width: '100%', padding: '10px 12px', border: '1.5px solid #E5E7EB', borderRadius: 8, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box', outline: 'none', transition: 'border-color 0.15s' };

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Top bar */}
      <div style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(255,255,255,0.96)', backdropFilter: 'blur(12px)', borderBottom: '1px solid #E5E7EB', padding: '0 32px', height: 56, display: 'flex', alignItems: 'center', gap: 16 }}>
        <button onClick={onBack} style={{ background: 'none', border: '1.5px solid #E5E7EB', borderRadius: 8, padding: '5px 12px', cursor: 'pointer', fontSize: 13, color: '#374151', fontWeight: 500 }}>← Back</button>
        <div style={{ width: 1, height: 18, background: '#E5E7EB' }} />
        <div style={{ width: 28, height: 28, borderRadius: 8, background: 'linear-gradient(135deg,#EC4899,#F59E0B)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14 }}>✍️</div>
        <div>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#0A0A0A' }}>Creative Agent</span>
          <span style={{ fontSize: 12, color: '#9CA3AF', marginLeft: 8 }}>Ad copy generation · brand safety validation</span>
        </div>
        {loading && <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#EC4899', fontWeight: 600 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#EC4899', animation: 'pulse 1s infinite' }} /> Generating…
        </div>}
      </div>

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px', display: 'grid', gridTemplateColumns: '380px 1fr', gap: 24 }}>
        {/* Form */}
        <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '28px', height: 'fit-content', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
          <h2 style={{ fontSize: 18, fontWeight: 800, color: '#0A0A0A', margin: '0 0 24px 0', letterSpacing: '-0.02em' }}>Ad Copy Brief</h2>
          <form onSubmit={handleSubmit}>
            {[
              { label: 'Channel', name: 'channel', type: 'select', options: CHANNELS },
              { label: 'Product / Service', name: 'product', placeholder: 'e.g. Cloud cost analytics platform', required: true },
              { label: 'Target Persona', name: 'persona', placeholder: 'e.g. VP Engineering at SaaS companies', required: true },
              { label: 'Tone', name: 'tone', type: 'select', options: TONES },
            ].map(f => (
              <div key={f.name} style={{ marginBottom: 16 }}>
                <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' }}>{f.label}</label>
                {f.type === 'select'
                  ? <select name={f.name} value={formData[f.name]} onChange={handleChange} style={inputStyle}>{f.options.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}</select>
                  : <input type="text" name={f.name} value={formData[f.name]} onChange={handleChange} placeholder={f.placeholder} required={f.required} style={inputStyle} />
                }
              </div>
            ))}
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' }}>Key Message</label>
              <textarea name="key_message" value={formData.key_message} onChange={handleChange} placeholder="Core value proposition or main benefit" required rows={3} style={{ ...inputStyle, resize: 'vertical' }} />
            </div>
            <div style={{ marginBottom: 24 }}>
              <label style={{ display: 'block', marginBottom: 6, fontWeight: 600, fontSize: 13, color: '#374151' }}>Variants to generate: <strong>{formData.num_variants}</strong></label>
              <input type="range" name="num_variants" min="1" max="5" value={formData.num_variants} onChange={handleChange} style={{ width: '100%', accentColor: '#EC4899' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#9CA3AF', marginTop: 2 }}><span>1</span><span>5</span></div>
            </div>
            <button type="submit" disabled={loading} style={{ width: '100%', padding: '12px', background: loading ? '#E5E7EB' : 'linear-gradient(135deg,#EC4899,#F59E0B)', color: loading ? '#9CA3AF' : '#fff', border: 'none', borderRadius: 10, fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', transition: 'opacity 0.2s' }}>
              {loading ? 'Generating copy…' : 'Generate Ad Copy →'}
            </button>
          </form>
        </div>

        {/* Right panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Execution timeline */}
          <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: loading ? '#EC4899' : events.length ? '#10B981' : '#D1D5DB' }} />
              <span style={{ fontSize: 12, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.07em' }}>Execution Timeline</span>
              {events.length > 0 && <span style={{ fontSize: 11, color: '#9CA3AF', marginLeft: 'auto' }}>{events.length} events</span>}
            </div>
            {events.length === 0 && !loading
              ? <p style={{ fontSize: 13, color: '#D1D5DB', margin: 0 }}>Submit the form to see live agent execution events here.</p>
              : <div style={{ maxHeight: 220, overflowY: 'auto' }}>{events.map((ev, i) => <EventRow key={i} event={ev} />)}</div>
            }
            <div ref={eventsEndRef} />
          </div>

          {/* Metrics bar */}
          {result && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
              {[
                { label: 'Latency', value: `${Math.round(result.latency_ms)}ms` },
                { label: 'Input tokens', value: result.total_input_tokens?.toLocaleString() },
                { label: 'Output tokens', value: result.total_output_tokens?.toLocaleString() },
                { label: 'Variants', value: variants?.length ?? '—' },
              ].map(m => (
                <div key={m.label} style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 12, padding: '14px 16px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
                  <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 4 }}>{m.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: '#0A0A0A' }}>{m.value}</div>
                </div>
              ))}
            </div>
          )}

          {/* Variants */}
          {variants && variants.length > 0 && (
            <div style={{ background: '#fff', border: '1px solid #E5E7EB', borderRadius: 16, padding: '20px 24px', boxShadow: '0 1px 4px rgba(0,0,0,0.04)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: '0 0 16px 0' }}>Generated Variants</h3>
              {variants.map((v, i) => <VariantCard key={i} variant={v} index={i} />)}
            </div>
          )}

          {/* Fallback JSON */}
          {result && !variants && (
            <div style={{ background: '#0D1117', border: '1px solid #21262D', borderRadius: 16, padding: '20px 24px' }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#6B7280', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 12 }}>Output</div>
              <pre style={{ margin: 0, fontSize: 12, color: '#E6EDF3', fontFamily: '"SF Mono","Fira Code",monospace', overflowX: 'auto', lineHeight: 1.7 }}>{JSON.stringify(result.output, null, 2)}</pre>
            </div>
          )}

          {result?.error && (
            <div style={{ background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 12, padding: '16px 20px' }}>
              <div style={{ fontWeight: 700, color: '#DC2626', fontSize: 14, marginBottom: 4 }}>Error</div>
              <p style={{ fontSize: 13, color: '#7F1D1D', margin: 0 }}>{result.error}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CreativeConsole;
