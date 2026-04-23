-- CampaignPilot Database Schema - PostgreSQL 15+

CREATE TABLE IF NOT EXISTS agent_runs (
    id SERIAL PRIMARY KEY,
    run_id UUID NOT NULL UNIQUE,
    agent_name VARCHAR(50) NOT NULL,
    model VARCHAR(100),
    max_turns INTEGER,
    input_params JSONB,
    success BOOLEAN DEFAULT false,
    output JSONB,
    error TEXT,
    tool_calls_made JSONB DEFAULT '[]'::jsonb,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    latency_ms FLOAT DEFAULT 0.0,
    trace_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_agent_runs_run_id ON agent_runs(run_id);
CREATE INDEX idx_agent_runs_agent_name ON agent_runs(agent_name);
CREATE INDEX idx_agent_runs_created_at ON agent_runs(created_at DESC);
CREATE INDEX idx_agent_runs_success ON agent_runs(success);

CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    goal TEXT,
    target_segment VARCHAR(255),
    budget_usd DECIMAL(12, 2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'planning',
    channels TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);

CREATE TABLE IF NOT EXISTS campaign_briefs (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    run_id UUID REFERENCES agent_runs(run_id),
    recommended_channels TEXT[],
    budget_split JSONB,
    primary_message_pillar TEXT,
    secondary_message_pillar TEXT,
    target_audience_description TEXT,
    kpis TEXT[],
    suggested_timeline TEXT,
    rationale TEXT,
    risks JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS creatives (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    run_id UUID REFERENCES agent_runs(run_id),
    variant_index INTEGER,
    headline VARCHAR(255),
    body TEXT,
    cta VARCHAR(100),
    tone VARCHAR(50),
    key_differentiator TEXT,
    channel VARCHAR(50),
    product VARCHAR(255),
    persona VARCHAR(255),
    safety_check_passed BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_events (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    event_date DATE NOT NULL,
    channel VARCHAR(50),
    impressions INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    conversions INTEGER DEFAULT 0,
    spend_usd DECIMAL(12, 2) DEFAULT 0,
    revenue_usd DECIMAL(12, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ab_experiments (
    id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(255) NOT NULL,
    campaign_id INTEGER REFERENCES campaigns(id),
    run_id UUID REFERENCES agent_runs(run_id),
    hypothesis TEXT,
    baseline_conversion_rate DECIMAL(5, 4),
    minimum_detectable_effect DECIMAL(5, 4),
    required_n_per_group INTEGER,
    achieved_power DECIMAL(5, 4),
    test_fraction DECIMAL(3, 2),
    status VARCHAR(50) DEFAULT 'designed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_agent_runs_updated_at BEFORE UPDATE ON agent_runs
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cp_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cp_user;
