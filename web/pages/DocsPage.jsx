import React, { useState, useEffect, useRef } from 'react';

const SECTIONS = [
  { id: 'overview', label: 'Architecture Overview' },
  { id: 'agents', label: 'The Five AI Agents' },
  { id: 'api', label: 'API Reference' },
  { id: 'websocket', label: 'WebSocket Streaming' },
  { id: 'database', label: 'Database Schema' },
  { id: 'testing', label: 'Testing Guide' },
];

const AGENTS = [
  {
    id: 'strategist',
    name: 'Strategist Agent',
    icon: '🧠',
    color: '#6366F1',
    gradient: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
    endpoint: 'POST /agents/strategist/run',
    purpose: 'Generates full multi-channel campaign briefs. Queries brand guidelines + past performance to produce budgets, KPIs, channel mixes, and rationale.',
    inputs: [
      { name: 'campaign_goal', type: 'string', desc: 'What the campaign should achieve' },
      { name: 'budget_usd', type: 'number', desc: 'Total campaign budget' },
      { name: 'timeline_days', type: 'integer', desc: 'Campaign duration' },
      { name: 'target_segment', type: 'string', desc: 'Target audience description' },
    ],
    steps: [
      'Parse campaign request, extract objectives',
      'Search knowledge base for brand guidelines',
      'Query DB for past campaign performance',
      'Retrieve channel benchmarks from KB',
      'Generate multi-channel strategy',
      'Output structured JSON with budget, KPIs, rationale',
    ],
  },
  {
    id: 'creative',
    name: 'Creative Agent',
    icon: '✍️',
    color: '#EC4899',
    gradient: 'linear-gradient(135deg, #EC4899, #F59E0B)',
    endpoint: 'POST /agents/creative/run',
    purpose: 'Generates ad copy variants optimized per channel, persona, and tone angle. Validates output against brand guidelines before returning.',
    inputs: [
      { name: 'channel', type: 'string', desc: 'facebook, linkedin, email, reels…' },
      { name: 'product', type: 'string', desc: 'Product/service being advertised' },
      { name: 'persona', type: 'string', desc: 'Target persona description' },
      { name: 'tone', type: 'string', desc: 'friendly, professional, urgent' },
      { name: 'key_message', type: 'string', desc: 'Core value proposition' },
      { name: 'num_variants', type: 'integer', desc: 'Number of variants (1–5)' },
    ],
    steps: [
      'Load brand guidelines from ChromaDB',
      'Retrieve channel character limits and specs',
      'Generate N variant drafts per messaging angle',
      'Validate each variant against prohibited phrases',
      'Score variants by brand voice alignment',
      'Return ranked variants with safety flags',
    ],
  },
  {
    id: 'analyst',
    name: 'Analyst Agent',
    icon: '📊',
    color: '#06B6D4',
    gradient: 'linear-gradient(135deg, #06B6D4, #6366F1)',
    endpoint: 'POST /agents/analyst/run',
    purpose: 'Answers natural-language analytics questions by generating SQL, executing against live data, and producing business insights with anomaly detection.',
    inputs: [
      { name: 'question', type: 'string', desc: '"What is ROAS by channel for Q1 2026?"' },
    ],
    steps: [
      'Parse natural language question',
      'Generate SQL (SELECT only, validated)',
      'Execute against PostgreSQL',
      'Detect result anomalies (ROAS > 10x flagged)',
      'Assess data quality',
      'Return insights with data quality context',
    ],
  },
  {
    id: 'optimizer',
    name: 'Optimizer Agent',
    icon: '⚡',
    color: '#F59E0B',
    gradient: 'linear-gradient(135deg, #F59E0B, #EF4444)',
    endpoint: 'POST /agents/optimizer/run',
    purpose: 'Analyzes live campaign performance vs. benchmarks and generates quantified budget reallocation recommendations with expected ROI impact.',
    inputs: [
      { name: 'campaign_id', type: 'integer', desc: 'Campaign to optimize' },
      { name: 'campaign_name', type: 'string', desc: 'Human-readable name' },
      { name: 'remaining_budget_usd', type: 'float', desc: 'Unspent budget' },
      { name: 'days_remaining', type: 'integer', desc: 'Campaign flight time left' },
    ],
    steps: [
      'Retrieve performance metrics by channel',
      'Compare vs. industry benchmarks',
      'Identify underperforming channels (statistically)',
      'Validate against historical patterns',
      'Generate reallocation recommendations',
      'Output expected ROI delta per recommendation',
    ],
  },
  {
    id: 'ab-test',
    name: 'A/B Testing Agent',
    icon: '🧪',
    color: '#10B981',
    gradient: 'linear-gradient(135deg, #10B981, #06B6D4)',
    endpoint: 'POST /agents/ab-test/design',
    purpose: 'Designs statistically valid experiments using power analysis, stratified random sampling, and covariate balance validation (chi-square + Welch\'s t-test).',
    inputs: [
      { name: 'experiment_name', type: 'string', desc: 'Human-readable identifier' },
      { name: 'baseline_conversion_rate', type: 'float', desc: 'Expected baseline (0–1)' },
      { name: 'minimum_detectable_effect', type: 'float', desc: 'Min lift to detect' },
      { name: 'desired_power', type: 'float', desc: 'Statistical power goal (typ. 0.8)' },
      { name: 'significance_level', type: 'float', desc: 'Type I error rate (typ. 0.05)' },
      { name: 'test_fraction', type: 'float', desc: 'Proportion to treatment (0.1–0.9)' },
    ],
    steps: [
      'Run power analysis → required sample size',
      'Stratify population (industry, size, DMA, experience)',
      'Assign groups via proportional stratified sampling',
      'Validate covariate balance (chi-square, Welch\'s t)',
      'Calculate standardized effect sizes',
      'Return experiment design with diagnostics report',
    ],
  },
];

const ENDPOINTS = [
  { method: 'POST', path: '/agents/strategist/run', desc: 'Generate campaign brief', color: '#10B981' },
  { method: 'POST', path: '/agents/creative/run', desc: 'Generate ad copy variants', color: '#10B981' },
  { method: 'POST', path: '/agents/analyst/run', desc: 'Run analytics query', color: '#10B981' },
  { method: 'POST', path: '/agents/optimizer/run', desc: 'Generate optimization recs', color: '#10B981' },
  { method: 'POST', path: '/agents/ab-test/design', desc: 'Design A/B experiment', color: '#10B981' },
  { method: 'GET', path: '/agents/{agent}/run/{run_id}', desc: 'Retrieve stored run result', color: '#6366F1' },
  { method: 'GET', path: '/agents/{agent}/runs', desc: 'List run history', color: '#6366F1' },
  { method: 'WS', path: '/ws/agent-events/{run_id}', desc: 'Real-time event stream', color: '#F59E0B' },
  { method: 'GET', path: '/health', desc: 'Service health check', color: '#6366F1' },
];

const WS_EVENTS = [
  {
    type: 'reasoning',
    color: '#8B5CF6',
    delay: '0.0s',
    desc: 'Agent thinking / planning',
    example: `{ "type": "reasoning", "thinking": "The user wants LinkedIn for VP personas...", "timestamp": 1713811595 }`,
  },
  {
    type: 'tool_call',
    color: '#6366F1',
    delay: '0.3s',
    desc: 'Tool invocation (KB search, SQL, etc.)',
    example: `{ "type": "tool_call", "tool_name": "search_knowledge_base", "input": { "query": "brand voice", "n_results": 5 } }`,
  },
  {
    type: 'tool_result',
    color: '#06B6D4',
    delay: '0.8s',
    desc: 'Tool response received',
    example: `{ "type": "tool_result", "tool_name": "search_knowledge_base", "output": [{ "doc_id": "bg_001", "content": "..." }] }`,
  },
  {
    type: 'reasoning',
    color: '#8B5CF6',
    delay: '1.1s',
    desc: 'Agent re-evaluates with new data',
    example: `{ "type": "reasoning", "thinking": "Based on brand guidelines, I should recommend...", "timestamp": 1713811598 }`,
  },
  {
    type: 'tool_call',
    color: '#6366F1',
    delay: '1.8s',
    desc: 'Second tool call (DB query)',
    example: `{ "type": "tool_call", "tool_name": "query_database", "input": { "sql": "SELECT ..." } }`,
  },
  {
    type: 'completed',
    color: '#10B981',
    delay: '3.5s',
    desc: 'Execution done, result ready',
    example: `{ "type": "completed", "success": true, "total_turns": 5, "timestamp": 1713811620 }`,
  },
];

const DB_TABLES = [
  { name: 'agent_runs', desc: 'All agent execution history', cols: ['run_id (uuid)', 'agent_name', 'input_params (jsonb)', 'output (jsonb)', 'tokens', 'latency_ms', 'created_at'] },
  { name: 'campaigns', desc: 'Campaign metadata', cols: ['id', 'name', 'goal', 'budget_usd', 'channel_mix (jsonb)', 'created_at'] },
  { name: 'creatives', desc: 'Ad copy variants', cols: ['id', 'campaign_id', 'channel', 'tone', 'variants (jsonb)', 'brand_safety_score'] },
  { name: 'performance_events', desc: 'Daily metrics by channel', cols: ['id', 'campaign_id', 'channel', 'date', 'impressions', 'clicks', 'conversions', 'spend_usd'] },
  { name: 'ab_experiments', desc: 'Experiment designs', cols: ['id', 'name', 'sample_size', 'power', 'significance_level', 'design_json (jsonb)'] },
  { name: 'eval_runs', desc: 'Model evaluation results', cols: ['id', 'agent_name', 'score', 'eval_type', 'details (jsonb)'] },
];

// ─── Sub-components ───────────────────────────────────────────────────────────

const CodeBlock = ({ children, lang = '' }) => (
  <div style={{
    background: '#0D1117',
    borderRadius: 12,
    padding: '20px 24px',
    margin: '16px 0',
    overflowX: 'auto',
    border: '1px solid #21262D',
  }}>
    {lang && (
      <div style={{ color: '#6B7280', fontSize: 11, fontFamily: 'monospace', marginBottom: 8, textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        {lang}
      </div>
    )}
    <pre style={{
      margin: 0,
      fontFamily: '"SF Mono", "Fira Code", "Fira Mono", monospace',
      fontSize: 13,
      lineHeight: 1.7,
      color: '#E6EDF3',
      whiteSpace: 'pre',
    }}>
      {children}
    </pre>
  </div>
);

const Badge = ({ method }) => {
  const colors = {
    POST: { bg: '#0D2B1F', text: '#10B981', border: '#10B981' },
    GET: { bg: '#0D1B2E', text: '#6366F1', border: '#6366F1' },
    WS: { bg: '#2B1A00', text: '#F59E0B', border: '#F59E0B' },
  };
  const c = colors[method] || colors.GET;
  return (
    <span style={{
      background: c.bg,
      color: c.text,
      border: `1px solid ${c.border}`,
      borderRadius: 6,
      padding: '3px 10px',
      fontSize: 11,
      fontFamily: 'monospace',
      fontWeight: 700,
      letterSpacing: '0.05em',
    }}>
      {method}
    </span>
  );
};

const SectionTitle = ({ id, eyebrow, title, subtitle }) => (
  <div id={id} style={{ marginBottom: 48, scrollMarginTop: 88 }}>
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      background: 'rgba(99,102,241,0.08)',
      border: '1px solid rgba(99,102,241,0.2)',
      borderRadius: 100,
      padding: '6px 14px',
      marginBottom: 20,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#6366F1', display: 'inline-block' }} />
      <span style={{ fontSize: 12, fontWeight: 600, color: '#6366F1', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{eyebrow}</span>
    </div>
    <h2 style={{ fontSize: 32, fontWeight: 800, color: '#0A0A0A', marginBottom: 12, letterSpacing: '-0.03em' }}>{title}</h2>
    {subtitle && <p style={{ fontSize: 17, color: '#6B7280', lineHeight: 1.6, maxWidth: 600 }}>{subtitle}</p>}
  </div>
);

// ─── Architecture Diagram ─────────────────────────────────────────────────────

const ArchDiagram = () => {
  const layers = [
    {
      label: 'Frontend Layer',
      sublabel: 'React + Vite · localhost:5174',
      color: '#6366F1',
      items: ['Strategist Console', 'Creative Console', 'Analyst Console', 'Optimizer Console', 'A/B Testing Console'],
    },
    {
      label: 'API Layer',
      sublabel: 'FastAPI · localhost:8001',
      color: '#8B5CF6',
      items: ['/agents/*/run', '/ws/agent-events/{run_id}', '/health', 'CORS + Auth Middleware'],
    },
    {
      label: 'Agent & Data Layer',
      sublabel: 'Claude API + PostgreSQL + ChromaDB',
      color: '#EC4899',
      items: ['BaseAgent (event_callback)', 'Tool executors (SQL, KB search)', 'PostgreSQL (run history)', 'ChromaDB (knowledge base)'],
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0, position: 'relative' }}>
      {layers.map((layer, i) => (
        <React.Fragment key={layer.label}>
          <div style={{
            background: '#FFFFFF',
            border: `2px solid ${layer.color}22`,
            borderRadius: 16,
            padding: '24px 28px',
            boxShadow: `0 4px 24px ${layer.color}10`,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <div style={{
                width: 10, height: 10, borderRadius: '50%',
                background: layer.color, boxShadow: `0 0 8px ${layer.color}`,
              }} />
              <div>
                <div style={{ fontWeight: 700, fontSize: 14, color: '#0A0A0A' }}>{layer.label}</div>
                <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 1 }}>{layer.sublabel}</div>
              </div>
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {layer.items.map(item => (
                <span key={item} style={{
                  background: `${layer.color}10`,
                  border: `1px solid ${layer.color}30`,
                  color: layer.color,
                  borderRadius: 8,
                  padding: '5px 12px',
                  fontSize: 13,
                  fontWeight: 500,
                }}>
                  {item}
                </span>
              ))}
            </div>
          </div>
          {i < layers.length - 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 60, padding: '12px 0' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                <div style={{ width: 2, height: 24, background: 'linear-gradient(to bottom, #6366F1, #8B5CF6)' }} />
                <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600 }}>HTTP REST</div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                <div style={{ width: 2, height: 24, background: 'linear-gradient(to bottom, #F59E0B, #EF4444)' }} />
                <div style={{ fontSize: 11, color: '#9CA3AF', fontWeight: 600 }}>WebSocket</div>
              </div>
            </div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

// ─── Request Lifecycle ────────────────────────────────────────────────────────

const LifecycleDiagram = () => {
  const steps = [
    { n: 1, actor: 'Frontend', label: 'POST /agents/*/run', color: '#6366F1', side: 'right' },
    { n: 2, actor: 'API', label: 'Generate run_id, create event callback, instantiate agent', color: '#8B5CF6', side: 'center' },
    { n: 3, actor: 'Agent', label: 'Execute with event_callback → emits events to WS queue', color: '#EC4899', side: 'center' },
    { n: 4, actor: 'API', label: 'Return {run_id, timestamp} immediately', color: '#8B5CF6', side: 'left' },
    { n: 5, actor: 'Frontend', label: 'Subscribe WebSocket /ws/agent-events/{run_id}', color: '#6366F1', side: 'right' },
    { n: 6, actor: 'API', label: 'Stream events live (tool_call, reasoning, completed)', color: '#8B5CF6', side: 'left' },
    { n: 7, actor: 'Database', label: 'INSERT INTO agent_runs (persisted for history)', color: '#10B981', side: 'center' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {steps.map(step => (
        <div key={step.n} style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 16,
          padding: '14px 20px',
          background: '#FAFAFA',
          border: `1px solid ${step.color}22`,
          borderLeft: `4px solid ${step.color}`,
          borderRadius: '0 12px 12px 0',
        }}>
          <div style={{
            width: 28, height: 28, borderRadius: '50%',
            background: step.color,
            color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 700, fontSize: 13, flexShrink: 0,
          }}>
            {step.n}
          </div>
          <div>
            <span style={{
              fontSize: 11, fontWeight: 700, color: step.color,
              textTransform: 'uppercase', letterSpacing: '0.08em', marginRight: 8,
            }}>
              {step.actor}
            </span>
            <span style={{ fontSize: 14, color: '#374151' }}>{step.label}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

// ─── Agent Card ───────────────────────────────────────────────────────────────

const AgentCard = ({ agent }) => {
  const [open, setOpen] = useState(false);

  return (
    <div style={{
      border: `1.5px solid ${agent.color}22`,
      borderRadius: 16,
      overflow: 'hidden',
      transition: 'box-shadow 0.2s',
      boxShadow: open ? `0 8px 32px ${agent.color}20` : 'none',
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%',
          background: 'none',
          border: 'none',
          padding: '24px 28px',
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <div style={{
          width: 48, height: 48, borderRadius: 12,
          background: agent.gradient,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22, flexShrink: 0,
          boxShadow: `0 4px 12px ${agent.color}40`,
        }}>
          {agent.icon}
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 17, color: '#0A0A0A', marginBottom: 4 }}>{agent.name}</div>
          <code style={{ fontSize: 12, color: '#9CA3AF', fontFamily: '"SF Mono", monospace' }}>{agent.endpoint}</code>
        </div>
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          border: `2px solid ${agent.color}40`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: agent.color, fontWeight: 700, fontSize: 16,
          transform: open ? 'rotate(180deg)' : 'none',
          transition: 'transform 0.2s',
        }}>
          ↓
        </div>
      </button>

      {open && (
        <div style={{ padding: '0 28px 28px', borderTop: `1px solid ${agent.color}15` }}>
          <p style={{ fontSize: 14, color: '#374151', lineHeight: 1.7, marginTop: 20, marginBottom: 24 }}>
            {agent.purpose}
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#0A0A0A', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Input Parameters
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {agent.inputs.map(inp => (
                  <div key={inp.name} style={{
                    background: '#F8F9FA',
                    borderRadius: 8,
                    padding: '10px 14px',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 2,
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <code style={{ fontSize: 12, fontWeight: 700, color: agent.color, fontFamily: '"SF Mono", monospace' }}>{inp.name}</code>
                      <span style={{
                        fontSize: 10, color: '#9CA3AF', background: '#E5E7EB',
                        borderRadius: 4, padding: '1px 6px', fontFamily: 'monospace',
                      }}>{inp.type}</span>
                    </div>
                    <div style={{ fontSize: 12, color: '#6B7280' }}>{inp.desc}</div>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#0A0A0A', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Execution Steps
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {agent.steps.map((step, i) => (
                  <div key={i} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                    <div style={{
                      width: 20, height: 20, borderRadius: '50%', flexShrink: 0,
                      background: agent.gradient,
                      color: '#fff', fontSize: 11, fontWeight: 700,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {i + 1}
                    </div>
                    <div style={{ fontSize: 13, color: '#374151', lineHeight: 1.5, paddingTop: 2 }}>{step}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── WebSocket Timeline ───────────────────────────────────────────────────────

const WSTimeline = () => {
  const eventColors = {
    reasoning: '#8B5CF6',
    tool_call: '#6366F1',
    tool_result: '#06B6D4',
    completed: '#10B981',
    error: '#EF4444',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {WS_EVENTS.map((ev, i) => (
        <div key={i} style={{ display: 'flex', gap: 0 }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 40, flexShrink: 0 }}>
            <div style={{
              width: 14, height: 14, borderRadius: '50%',
              background: eventColors[ev.type] || '#6366F1',
              boxShadow: `0 0 8px ${eventColors[ev.type] || '#6366F1'}80`,
              marginTop: 18, zIndex: 1,
            }} />
            {i < WS_EVENTS.length - 1 && (
              <div style={{ width: 2, flex: 1, background: '#E5E7EB', minHeight: 20 }} />
            )}
          </div>
          <div style={{ paddingBottom: 20, paddingLeft: 16, flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12 }}>
              <span style={{
                background: `${eventColors[ev.type]}15`,
                color: eventColors[ev.type],
                border: `1px solid ${eventColors[ev.type]}30`,
                borderRadius: 6,
                padding: '3px 10px',
                fontSize: 12,
                fontFamily: 'monospace',
                fontWeight: 700,
              }}>
                {ev.type}
              </span>
              <span style={{ fontSize: 12, color: '#9CA3AF', fontFamily: 'monospace' }}>T+{ev.delay}</span>
              <span style={{ fontSize: 13, color: '#6B7280' }}>{ev.desc}</span>
            </div>
            <CodeBlock>{ev.example}</CodeBlock>
          </div>
        </div>
      ))}
    </div>
  );
};

// ─── Main Docs Page ───────────────────────────────────────────────────────────

const DocsPage = ({ onBack }) => {
  const [activeSection, setActiveSection] = useState('overview');
  const observer = useRef(null);

  useEffect(() => {
    observer.current = new IntersectionObserver(
      entries => {
        entries.forEach(e => {
          if (e.isIntersecting) setActiveSection(e.target.id);
        });
      },
      { rootMargin: '-20% 0px -70% 0px' }
    );
    SECTIONS.forEach(s => {
      const el = document.getElementById(s.id);
      if (el) observer.current.observe(el);
    });
    return () => observer.current?.disconnect();
  }, []);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div style={{ minHeight: '100vh', background: '#F8F9FA', fontFamily: "'Inter', -apple-system, sans-serif" }}>
      {/* Top bar */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 100,
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #E5E7EB',
        padding: '0 32px',
        height: 60,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <button
            onClick={onBack}
            style={{
              background: 'none', border: '1.5px solid #E5E7EB', borderRadius: 8,
              padding: '6px 14px', cursor: 'pointer', fontSize: 13,
              color: '#374151', fontWeight: 500, display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            ← Back
          </button>
          <div style={{ width: 1, height: 20, background: '#E5E7EB' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 22, height: 22, borderRadius: 6, background: 'linear-gradient(135deg,#6366F1,#EC4899)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 800 }}>◆</div>
            <span style={{ fontWeight: 700, fontSize: 15, color: '#0A0A0A' }}>CampaignPilot</span>
            <span style={{ fontSize: 13, color: '#9CA3AF' }}>/</span>
            <span style={{ fontSize: 13, color: '#6366F1', fontWeight: 600 }}>System Docs</span>
          </div>
        </div>
        <div style={{
          background: 'rgba(99,102,241,0.08)',
          border: '1px solid rgba(99,102,241,0.2)',
          borderRadius: 100,
          padding: '4px 12px',
          fontSize: 12, fontWeight: 600, color: '#6366F1',
        }}>
          v1.0 · April 2026
        </div>
      </div>

      <div style={{ display: 'flex', maxWidth: 1360, margin: '0 auto', padding: '0 32px' }}>
        {/* Sidebar */}
        <aside style={{
          width: 220, flexShrink: 0,
          position: 'sticky', top: 60, height: 'calc(100vh - 60px)',
          overflowY: 'auto',
          padding: '40px 0 40px',
          borderRight: '1px solid #E5E7EB',
        }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#9CA3AF', textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 12, paddingRight: 24 }}>
            On this page
          </div>
          <nav style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {SECTIONS.map(s => (
              <button
                key={s.id}
                onClick={() => scrollTo(s.id)}
                style={{
                  background: activeSection === s.id ? 'rgba(99,102,241,0.08)' : 'none',
                  border: 'none',
                  borderLeft: `2px solid ${activeSection === s.id ? '#6366F1' : 'transparent'}`,
                  borderRadius: '0 8px 8px 0',
                  padding: '8px 14px',
                  textAlign: 'left',
                  fontSize: 13,
                  fontWeight: activeSection === s.id ? 600 : 400,
                  color: activeSection === s.id ? '#6366F1' : '#6B7280',
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  marginRight: -1,
                }}
              >
                {s.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Main content */}
        <main style={{ flex: 1, padding: '56px 0 80px 56px', minWidth: 0 }}>

          {/* ── Hero ── */}
          <div style={{ marginBottom: 72 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'linear-gradient(135deg, rgba(99,102,241,0.1), rgba(236,72,153,0.1))',
              border: '1px solid rgba(99,102,241,0.2)',
              borderRadius: 100, padding: '6px 16px', marginBottom: 24,
            }}>
              <span style={{ fontSize: 12, fontWeight: 700, background: 'linear-gradient(135deg,#6366F1,#EC4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                SYSTEM DOCUMENTATION
              </span>
            </div>
            <h1 style={{ fontSize: 48, fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.05, marginBottom: 20, color: '#0A0A0A' }}>
              CampaignPilot<br />
              <span style={{ background: 'linear-gradient(135deg,#6366F1,#EC4899)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Architecture & API
              </span>
            </h1>
            <p style={{ fontSize: 18, color: '#6B7280', lineHeight: 1.7, maxWidth: 580 }}>
              A production-grade multi-agent marketing automation system powered by Claude AI. Five specialized agents, real-time event streaming, and full observability.
            </p>
            <div style={{ display: 'flex', gap: 12, marginTop: 28 }}>
              {[
                { label: '5 Agents', sub: 'Specialized AI', color: '#6366F1' },
                { label: 'FastAPI', sub: 'Python Backend', color: '#8B5CF6' },
                { label: 'WebSocket', sub: 'Live Streaming', color: '#F59E0B' },
                { label: 'Claude AI', sub: 'Sonnet 4.6', color: '#EC4899' },
              ].map(stat => (
                <div key={stat.label} style={{
                  background: '#fff',
                  border: '1px solid #E5E7EB',
                  borderRadius: 12,
                  padding: '14px 20px',
                  boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                }}>
                  <div style={{ fontWeight: 800, fontSize: 16, color: stat.color }}>{stat.label}</div>
                  <div style={{ fontSize: 12, color: '#9CA3AF', marginTop: 2 }}>{stat.sub}</div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Architecture ── */}
          <SectionTitle
            id="overview"
            eyebrow="Section 01"
            title="System Architecture"
            subtitle="Three-layer distributed system: React frontend communicates over HTTP REST and WebSocket to a FastAPI backend, which orchestrates Claude-powered agents accessing PostgreSQL and ChromaDB."
          />
          <ArchDiagram />

          <div style={{ marginTop: 40 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A0A0A', marginBottom: 20 }}>Request / Response Lifecycle</h3>
            <LifecycleDiagram />
          </div>

          <div style={{ height: 72 }} />

          {/* ── Agents ── */}
          <SectionTitle
            id="agents"
            eyebrow="Section 02"
            title="The Five AI Agents"
            subtitle="Each agent extends BaseAgent with an event_callback parameter, enabling real-time event emission to connected WebSocket clients during execution."
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {AGENTS.map(agent => <AgentCard key={agent.id} agent={agent} />)}
          </div>

          <div style={{ height: 72 }} />

          {/* ── API Reference ── */}
          <SectionTitle
            id="api"
            eyebrow="Section 03"
            title="API Reference"
            subtitle="All agents expose consistent REST endpoints. Every run returns a run_id immediately for WebSocket subscription and async polling."
          />

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 36 }}>
            {ENDPOINTS.map((ep, i) => (
              <div key={i} style={{
                background: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: 12,
                padding: '16px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}>
                <Badge method={ep.method} />
                <code style={{ fontSize: 14, fontFamily: '"SF Mono", monospace', color: '#0A0A0A', fontWeight: 600, flex: 1 }}>{ep.path}</code>
                <span style={{ fontSize: 13, color: '#9CA3AF' }}>{ep.desc}</span>
              </div>
            ))}
          </div>

          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A0A0A', marginBottom: 16 }}>Standard Response Schema</h3>
          <CodeBlock lang="JSON">{`{
  "run_id":              "550e8400-e29b-41d4-a716-446655440000",
  "agent_name":          "strategist",
  "success":             true,
  "output": {
    "campaign_goal":       "Generate 50 MQLs in Q4...",
    "recommended_channels": ["LinkedIn", "Email", "Content"],
    "budget_allocation":   { "LinkedIn": 25000, "Email": 15000 },
    "primary_kpis":        ["MQL Volume", "CAC", "ROAS"]
  },
  "tool_calls_made": [
    { "tool_name": "search_knowledge_base", "input": {...}, "output": {...} }
  ],
  "total_input_tokens":  2048,
  "total_output_tokens": 1024,
  "latency_ms":          3500,
  "trace_url":           "https://cloud.langfuse.com/traces/...",
  "error":               null,
  "timestamp":           "2026-04-23T10:30:00Z"
}`}</CodeBlock>

          <div style={{ height: 72 }} />

          {/* ── WebSocket ── */}
          <SectionTitle
            id="websocket"
            eyebrow="Section 04"
            title="WebSocket Event Streaming"
            subtitle="Agents emit structured events throughout execution via event_callback. These are broadcast to subscribers in real-time, powering the live timeline UI in each agent console."
          />

          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A0A0A', marginBottom: 16 }}>Connection Protocol</h3>
          <CodeBlock lang="JavaScript">{`// 1. POST to agent endpoint → receive run_id
const { run_id } = await fetch('/api/agents/strategist/run', {
  method: 'POST',
  body: JSON.stringify({ campaign_goal: '...', budget_usd: 50000 })
}).then(r => r.json());

// 2. Connect WebSocket using run_id
const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(\`\${protocol}://\${API_HOST}/ws/agent-events/\${run_id}\`);

// 3. Handle incoming events
ws.onmessage = ({ data }) => {
  const event = JSON.parse(data);
  // event.type: "reasoning" | "tool_call" | "tool_result" | "completed" | "error"
  renderTimelineEvent(event);
};`}</CodeBlock>

          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A0A0A', margin: '36px 0 20px' }}>Event Timeline</h3>
          <div style={{
            background: '#fff',
            border: '1px solid #E5E7EB',
            borderRadius: 16,
            padding: '32px 28px',
            boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
          }}>
            <WSTimeline />
          </div>

          <div style={{ height: 72 }} />

          {/* ── Database ── */}
          <SectionTitle
            id="database"
            eyebrow="Section 05"
            title="Database Schema"
            subtitle="PostgreSQL stores all agent run history, campaign data, and performance metrics. ChromaDB holds the vector knowledge base for RAG retrieval."
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 36 }}>
            {DB_TABLES.map(table => (
              <div key={table.name} style={{
                background: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: 12,
                padding: '20px',
                boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#6366F1' }} />
                  <code style={{ fontSize: 14, fontWeight: 700, color: '#0A0A0A', fontFamily: '"SF Mono", monospace' }}>{table.name}</code>
                </div>
                <p style={{ fontSize: 13, color: '#9CA3AF', marginBottom: 12 }}>{table.desc}</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {table.cols.map(col => (
                    <code key={col} style={{
                      fontSize: 11, fontFamily: '"SF Mono", monospace',
                      background: '#F3F4F6', color: '#374151',
                      borderRadius: 6, padding: '3px 8px',
                    }}>
                      {col}
                    </code>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A0A0A', marginBottom: 16 }}>ChromaDB Collections</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              { name: 'brand_guidelines', desc: 'Voice, tone, prohibited phrases, messaging pillars' },
              { name: 'campaign_history', desc: 'Past campaign briefs and performance summaries' },
              { name: 'benchmarks', desc: 'Industry CTR, CPC, ROAS benchmarks by channel' },
              { name: 'creative_examples', desc: 'Successful ad copy examples for few-shot retrieval' },
            ].map(col => (
              <div key={col.name} style={{
                background: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: 10,
                padding: '14px 18px',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
              }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#8B5CF6', flexShrink: 0 }} />
                <code style={{ fontSize: 13, fontWeight: 700, color: '#8B5CF6', fontFamily: '"SF Mono", monospace', minWidth: 180 }}>{col.name}</code>
                <span style={{ fontSize: 13, color: '#6B7280' }}>{col.desc}</span>
              </div>
            ))}
          </div>

          <div style={{ height: 72 }} />

          {/* ── Testing Guide ── */}
          <SectionTitle
            id="testing"
            eyebrow="Section 06"
            title="Testing Guide"
            subtitle="Step-by-step instructions for verifying each agent end-to-end — from service health checks through live WebSocket event streaming."
          />

          {[
            {
              step: 1,
              title: 'Verify Service Health',
              color: '#6366F1',
              content: (
                <>
                  <p style={{ fontSize: 14, color: '#374151', marginBottom: 12 }}>Confirm all three services are running before testing agents.</p>
                  <CodeBlock lang="Bash">{`# Backend health
curl http://localhost:8001/health | jq .
# Expected: { "status": "ok", "services": { "postgres": true, "chromadb": true } }

# ChromaDB heartbeat
curl http://localhost:8000/api/v1/heartbeat
# Expected: {"nanosecond heartbeat": 12345...}

# Frontend
open http://localhost:5174`}</CodeBlock>
                </>
              ),
            },
            {
              step: 2,
              title: 'Test Strategist Agent',
              color: '#8B5CF6',
              content: (
                <>
                  <p style={{ fontSize: 14, color: '#374151', marginBottom: 12 }}>Open the Strategist Console. Fill in campaign details and click "Generate Strategy".</p>
                  <CodeBlock lang="JSON - Expected Output">{`{
  "recommended_channels": ["LinkedIn", "Email", "Content Marketing"],
  "budget_allocation": { "LinkedIn": 25000, "Email": 15000 },
  "primary_kpis": ["MQL Volume", "CAC", "ROAS"],
  "rationale": "LinkedIn drives highest engagement for VP personas..."
}`}</CodeBlock>
                </>
              ),
            },
            {
              step: 3,
              title: 'Test Creative Agent',
              color: '#EC4899',
              content: (
                <>
                  <p style={{ fontSize: 14, color: '#374151', marginBottom: 12 }}>Switch to Creative Console. Select channel "LinkedIn", persona "VP of Engineering", tone "professional", request 3 variants.</p>
                  <p style={{ fontSize: 14, color: '#374151' }}>Expect 3 variants with brand safety scores. Watch the timeline show tool_call events for KB retrieval.</p>
                </>
              ),
            },
            {
              step: 4,
              title: 'Test Analyst Agent',
              color: '#06B6D4',
              content: (
                <>
                  <p style={{ fontSize: 14, color: '#374151', marginBottom: 12 }}>Enter a natural language question in the Analyst Console.</p>
                  <CodeBlock lang="Example Questions">{`"What is the average CTR by channel?"
"Show me top 5 campaigns by ROAS last quarter"
"Which channels have conversion rates above 2%?"`}</CodeBlock>
                </>
              ),
            },
            {
              step: 5,
              title: 'Test A/B Testing Agent',
              color: '#10B981',
              content: (
                <>
                  <p style={{ fontSize: 14, color: '#374151', marginBottom: 12 }}>In the A/B Testing Console, enter experiment parameters.</p>
                  <CodeBlock lang="Test Parameters">{`baseline_conversion_rate: 0.05   (5%)
minimum_detectable_effect: 0.20  (20% relative lift)
desired_power: 0.80
significance_level: 0.05
test_fraction: 0.50`}</CodeBlock>
                  <p style={{ fontSize: 14, color: '#374151', marginTop: 12 }}>Expect: required sample size, stratification details, balance validation report.</p>
                </>
              ),
            },
          ].map(item => (
            <div key={item.step} style={{
              border: `1.5px solid ${item.color}20`,
              borderRadius: 14,
              marginBottom: 16,
              overflow: 'hidden',
            }}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: 14,
                padding: '20px 24px',
                background: `${item.color}06`,
                borderBottom: `1px solid ${item.color}15`,
              }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                  background: `linear-gradient(135deg, ${item.color}, ${item.color}88)`,
                  color: '#fff', fontWeight: 800, fontSize: 14,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  {item.step}
                </div>
                <h4 style={{ fontSize: 15, fontWeight: 700, color: '#0A0A0A', margin: 0 }}>{item.title}</h4>
              </div>
              <div style={{ padding: '20px 24px' }}>
                {item.content}
              </div>
            </div>
          ))}

          {/* Footer */}
          <div style={{
            marginTop: 72,
            padding: '32px',
            background: 'linear-gradient(135deg, rgba(99,102,241,0.05), rgba(236,72,153,0.05))',
            border: '1px solid rgba(99,102,241,0.12)',
            borderRadius: 16,
            textAlign: 'center',
          }}>
            <div style={{ fontSize: 24, marginBottom: 8 }}>◆</div>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0A0A0A', marginBottom: 8 }}>CampaignPilot System Documentation</h3>
            <p style={{ fontSize: 14, color: '#9CA3AF' }}>Built with Claude AI · FastAPI · React · PostgreSQL · ChromaDB</p>
            <button
              onClick={onBack}
              style={{
                marginTop: 20,
                background: 'linear-gradient(135deg,#6366F1,#8B5CF6)',
                border: 'none', borderRadius: 10,
                padding: '10px 24px', color: '#fff',
                fontWeight: 700, fontSize: 14, cursor: 'pointer',
              }}
            >
              ← Back to CampaignPilot
            </button>
          </div>

        </main>
      </div>
    </div>
  );
};

export default DocsPage;
