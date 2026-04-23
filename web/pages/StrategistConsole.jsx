import React, { useState, useRef, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const StrategistConsole = ({ onBack }) => {
  const [formData, setFormData] = useState({
    campaign_goal: '',
    budget_usd: 5000,
    timeline_days: 30,
    target_segment: '',
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const eventsEndRef = useRef(null);

  const scrollToBottom = () => {
    eventsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [events]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: name === 'budget_usd' || name === 'timeline_days' ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setEvents([]);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/agents/strategist/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      setEvents([
        {
          type: 'agent_complete',
          timestamp: new Date().toISOString(),
          message: 'Agent execution complete',
        },
      ]);
    } catch (error) {
      setEvents([
        {
          type: 'error',
          timestamp: new Date().toISOString(),
          message: error.message,
        },
      ]);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', padding: '20px' }}>
      {/* Header */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', marginBottom: '40px' }}>
        <button
          onClick={onBack}
          style={{
            background: 'none',
            border: 'none',
            color: '#6366F1',
            cursor: 'pointer',
            fontSize: '14px',
            fontWeight: '600',
            marginBottom: '20px',
          }}
        >
          ← Back to home
        </button>
        <h1 style={{ fontSize: '36px', fontWeight: '900', color: '#0A0A0A', margin: '0 0 8px 0' }}>
          Strategist Agent
        </h1>
        <p style={{ color: '#6B7280', fontSize: '16px', margin: 0 }}>
          Design a winning campaign strategy. Pulls from your benchmarks and brand guidelines to return a full brief.
        </p>
      </div>

      <div
        style={{
          maxWidth: '1400px',
          margin: '0 auto',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '24px',
        }}
      >
        {/* Form */}
        <div
          style={{
            background: 'white',
            border: '1px solid #E5E7EB',
            borderRadius: '16px',
            padding: '32px',
          }}
        >
          <h2 style={{ fontSize: '20px', fontWeight: '700', marginTop: 0 }}>Campaign Details</h2>

          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#0A0A0A' }}>
                Campaign Goal
              </label>
              <input
                type="text"
                name="campaign_goal"
                value={formData.campaign_goal}
                onChange={handleInputChange}
                placeholder="e.g., Increase SaaS signups by 40% in Q2"
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#0A0A0A' }}>
                Budget (USD)
              </label>
              <input
                type="number"
                name="budget_usd"
                value={formData.budget_usd}
                onChange={handleInputChange}
                min="100"
                max="1000000"
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#0A0A0A' }}>
                Timeline (days)
              </label>
              <input
                type="number"
                name="timeline_days"
                value={formData.timeline_days}
                onChange={handleInputChange}
                min="1"
                max="365"
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
              />
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', color: '#0A0A0A' }}>
                Target Segment
              </label>
              <input
                type="text"
                name="target_segment"
                value={formData.target_segment}
                onChange={handleInputChange}
                placeholder="e.g., B2B marketing teams, 50-500 employees"
                required
                style={{
                  width: '100%',
                  padding: '12px',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  fontFamily: 'inherit',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%',
                padding: '12px',
                background: loading ? '#D1D5DB' : 'linear-gradient(135deg, #6366F1 0%, #EC4899 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s',
              }}
            >
              {loading ? 'Generating Brief...' : 'Generate Strategic Brief'}
            </button>
          </form>
        </div>

        {/* Results / Events */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Events Timeline */}
          <div
            style={{
              background: 'white',
              border: '1px solid #E5E7EB',
              borderRadius: '16px',
              padding: '24px',
              flex: 1,
              overflow: 'auto',
              maxHeight: '500px',
            }}
          >
            <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '14px', fontWeight: '700' }}>
              Execution Timeline
            </h3>
            {events.length === 0 && !loading && (
              <p style={{ color: '#9CA3AF', fontSize: '14px' }}>
                Fill in the form and click "Generate Brief" to see real-time execution.
              </p>
            )}
            {events.map((event, idx) => (
              <div
                key={idx}
                style={{
                  padding: '12px',
                  background: event.type === 'error' ? '#FEE2E2' : '#F3F4F6',
                  border: event.type === 'error' ? '1px solid #FCA5A5' : '1px solid #E5E7EB',
                  borderRadius: '8px',
                  marginBottom: '12px',
                  fontSize: '12px',
                }}
              >
                <div
                  style={{
                    fontWeight: '600',
                    color: event.type === 'error' ? '#DC2626' : '#0A0A0A',
                    marginBottom: '4px',
                  }}
                >
                  {event.type === 'error' ? '❌' : '✓'} {event.message}
                </div>
                {event.timestamp && (
                  <div style={{ color: '#6B7280', fontSize: '11px' }}>
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div style={{ textAlign: 'center', color: '#6366F1', padding: '20px' }}>
                <div style={{ fontSize: '24px', marginBottom: '8px' }}>⚙️</div>
                Running agent...
              </div>
            )}
            <div ref={eventsEndRef} />
          </div>

          {/* Results */}
          {result && result.success && (
            <div
              style={{
                background: 'white',
                border: '1px solid #E5E7EB',
                borderRadius: '16px',
                padding: '24px',
                flex: 1,
                overflow: 'auto',
                maxHeight: '500px',
              }}
            >
              <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '14px', fontWeight: '700' }}>
                Results
              </h3>

              {/* Metrics */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: '12px',
                  marginBottom: '16px',
                }}
              >
                <MetricCard label="Latency" value={`${result.latency_ms.toFixed(0)}ms`} />
                <MetricCard
                  label="Tokens"
                  value={`${result.total_input_tokens + result.total_output_tokens}`}
                />
              </div>

              {/* Output */}
              <div
                style={{
                  background: '#F8F9FA',
                  border: '1px solid #E5E7EB',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '16px',
                }}
              >
                <div style={{ fontSize: '12px', fontWeight: '600', marginBottom: '8px', color: '#0A0A0A' }}>
                  Campaign Brief
                </div>
                <pre
                  style={{
                    margin: 0,
                    fontSize: '11px',
                    color: '#6B7280',
                    overflow: 'auto',
                    maxHeight: '200px',
                  }}
                >
                  {JSON.stringify(result.output, null, 2)}
                </pre>
              </div>

              {result.trace_url && (
                <a
                  href={result.trace_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: '#6366F1',
                    fontSize: '12px',
                    textDecoration: 'none',
                    fontWeight: '600',
                  }}
                >
                  View full trace in Langfuse →
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const MetricCard = ({ label, value }) => (
  <div
    style={{
      background: '#F8F9FA',
      border: '1px solid #E5E7EB',
      borderRadius: '8px',
      padding: '12px',
      textAlign: 'center',
    }}
  >
    <div style={{ fontSize: '11px', color: '#6B7280', fontWeight: '600', marginBottom: '4px' }}>
      {label}
    </div>
    <div style={{ fontSize: '16px', fontWeight: '700', color: '#0A0A0A' }}>{value}</div>
  </div>
);

export default StrategistConsole;
