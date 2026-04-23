-- Create campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    goal TEXT,
    target_segment VARCHAR(255),
    budget_usd NUMERIC(12, 2),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'draft',
    channels TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create campaign_briefs table
CREATE TABLE IF NOT EXISTS campaign_briefs (
    id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    content JSONB NOT NULL DEFAULT '{}',
    quality_score NUMERIC(3, 2),
    created_by_agent VARCHAR(100),
    approved_at TIMESTAMPTZ,
    approved_by VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create creatives table
CREATE TABLE IF NOT EXISTS creatives (
    id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    channel VARCHAR(100) NOT NULL,
    variant_index INT NOT NULL DEFAULT 1,
    headline TEXT NOT NULL,
    body TEXT NOT NULL,
    cta VARCHAR(255),
    tone VARCHAR(100),
    quality_score NUMERIC(3, 2),
    safety_passed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create performance_events table
CREATE TABLE IF NOT EXISTS performance_events (
    id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    channel VARCHAR(100) NOT NULL,
    impressions INT NOT NULL DEFAULT 0,
    clicks INT NOT NULL DEFAULT 0,
    conversions INT NOT NULL DEFAULT 0,
    spend_usd NUMERIC(10, 2) NOT NULL DEFAULT 0,
    revenue_usd NUMERIC(10, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create optimization_recommendations table
CREATE TABLE IF NOT EXISTS optimization_recommendations (
    id SERIAL PRIMARY KEY,
    campaign_id INT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    recommendation_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    expected_impact TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create eval_runs table
CREATE TABLE IF NOT EXISTS eval_runs (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    golden_dataset_version VARCHAR(50),
    run_at TIMESTAMPTZ DEFAULT NOW(),
    scores JSONB NOT NULL DEFAULT '{}',
    summary JSONB NOT NULL DEFAULT '{}',
    total_tokens INT,
    estimated_cost_usd NUMERIC(8, 4)
);

-- Create indexes for campaigns table
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_campaigns_target_segment ON campaigns(target_segment);

-- Create indexes for campaign_briefs table
CREATE INDEX IF NOT EXISTS idx_campaign_briefs_campaign_id ON campaign_briefs(campaign_id);

-- Create indexes for creatives table
CREATE INDEX IF NOT EXISTS idx_creatives_campaign_id ON creatives(campaign_id);
CREATE INDEX IF NOT EXISTS idx_creatives_channel ON creatives(channel);

-- Create indexes for performance_events table
CREATE INDEX IF NOT EXISTS idx_performance_events_campaign_id ON performance_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_performance_events_event_date ON performance_events(event_date);
CREATE INDEX IF NOT EXISTS idx_performance_events_channel ON performance_events(channel);

-- Create indexes for optimization_recommendations table
CREATE INDEX IF NOT EXISTS idx_optimization_recommendations_campaign_id ON optimization_recommendations(campaign_id);

-- Create indexes for eval_runs table
CREATE INDEX IF NOT EXISTS idx_eval_runs_agent_name ON eval_runs(agent_name);
CREATE INDEX IF NOT EXISTS idx_eval_runs_run_at ON eval_runs(run_at);

-- ─────────────────────────────────────────────
-- SMB Advertiser Pool (dummy CRM-style dataset)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS smb_advertisers (
    id SERIAL PRIMARY KEY,
    business_name VARCHAR(255) NOT NULL,

    -- Industry classification
    industry VARCHAR(100) NOT NULL,            -- e.g. "Restaurant & Food Service"
    sub_industry VARCHAR(100),                  -- e.g. "Fast Casual"

    -- Geography
    country VARCHAR(50) NOT NULL DEFAULT 'US',
    state VARCHAR(50),                          -- e.g. "CA"
    city VARCHAR(100),                          -- e.g. "Los Angeles"
    dma_code INT,                               -- Nielsen DMA code
    dma_name VARCHAR(150),                      -- e.g. "Los Angeles"
    zip_code VARCHAR(10),

    -- Business size & maturity
    employee_count INT,                         -- 1–500
    annual_revenue_usd BIGINT,                  -- estimated annual revenue
    business_age_years INT,                     -- years in operation

    -- Advertising profile
    advertising_experience VARCHAR(20) NOT NULL DEFAULT 'none',
                                                -- none | beginner | intermediate | advanced
    monthly_ad_spend_usd NUMERIC(10,2),         -- current/estimated monthly ad spend
    has_run_meta_ads BOOLEAN DEFAULT FALSE,
    last_meta_ad_date DATE,                     -- NULL if never run Meta ads
    facebook_page_followers INT DEFAULT 0,
    instagram_followers INT DEFAULT 0,
    has_website BOOLEAN DEFAULT FALSE,

    -- Segment tags
    primary_product_category VARCHAR(100),      -- what they sell
    business_type VARCHAR(20) DEFAULT 'B2C',    -- B2C | B2B | both
    is_ecommerce BOOLEAN DEFAULT FALSE,
    has_physical_location BOOLEAN DEFAULT TRUE,

    -- Meta-level fields
    lead_source VARCHAR(100),                   -- e.g. "organic_search", "partner_referral"
    acquisition_likelihood_score NUMERIC(4,3),  -- 0.000–1.000 propensity score (for future ML use)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_smb_advertisers_industry ON smb_advertisers(industry);
CREATE INDEX IF NOT EXISTS idx_smb_advertisers_dma_code ON smb_advertisers(dma_code);
CREATE INDEX IF NOT EXISTS idx_smb_advertisers_country ON smb_advertisers(country);
CREATE INDEX IF NOT EXISTS idx_smb_advertisers_state ON smb_advertisers(state);
CREATE INDEX IF NOT EXISTS idx_smb_advertisers_adv_experience ON smb_advertisers(advertising_experience);
CREATE INDEX IF NOT EXISTS idx_smb_advertisers_has_run_meta ON smb_advertisers(has_run_meta_ads);

-- ─────────────────────────────────────────────
-- A/B Experiment Registry
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ab_experiments (
    id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis TEXT,

    -- Experiment scope
    campaign_id INT REFERENCES campaigns(id) ON DELETE SET NULL,
    target_industry VARCHAR(100),               -- NULL = all industries
    target_dma_code INT,                        -- NULL = all DMAs
    target_country VARCHAR(50) DEFAULT 'US',

    -- Stratification config (JSON: which columns to stratify on + bins)
    stratification_config JSONB NOT NULL DEFAULT '{}',

    -- Group sizes & stats
    total_pool_size INT,
    test_group_size INT,
    control_group_size INT,

    -- Statistical parameters
    desired_power NUMERIC(4,3) DEFAULT 0.80,    -- 1 - β (Type II error)
    significance_level NUMERIC(4,3) DEFAULT 0.05, -- α (Type I error)
    minimum_detectable_effect NUMERIC(6,4),     -- MDE as absolute or relative effect
    mde_type VARCHAR(20) DEFAULT 'relative',    -- 'relative' | 'absolute'

    -- Power analysis results
    required_sample_size_per_group INT,
    achieved_power NUMERIC(4,3),
    power_analysis_notes TEXT,

    -- Balance diagnostics (JSON: {variable: {test_mean, control_mean, p_value, standardized_diff}})
    balance_diagnostics JSONB DEFAULT '{}',

    -- Lifecycle
    status VARCHAR(30) DEFAULT 'draft',         -- draft | active | completed | cancelled
    created_by VARCHAR(100) DEFAULT 'ab_testing_agent',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    activated_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_ab_experiments_status ON ab_experiments(status);
CREATE INDEX IF NOT EXISTS idx_ab_experiments_campaign_id ON ab_experiments(campaign_id);

-- ─────────────────────────────────────────────
-- A/B Experiment Assignments
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ab_experiment_assignments (
    id SERIAL PRIMARY KEY,
    experiment_id INT NOT NULL REFERENCES ab_experiments(id) ON DELETE CASCADE,
    smb_advertiser_id INT NOT NULL REFERENCES smb_advertisers(id) ON DELETE CASCADE,
    group_label VARCHAR(20) NOT NULL,           -- 'test' | 'control'
    stratum_key VARCHAR(200),                   -- composite strata label (industry × size_bucket × dma_tier)
    propensity_score NUMERIC(6,5),             -- estimated P(treatment) from logistic model
    assigned_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE (experiment_id, smb_advertiser_id)
);

CREATE INDEX IF NOT EXISTS idx_ab_assignments_experiment_id ON ab_experiment_assignments(experiment_id);
CREATE INDEX IF NOT EXISTS idx_ab_assignments_smb_id ON ab_experiment_assignments(smb_advertiser_id);
CREATE INDEX IF NOT EXISTS idx_ab_assignments_group ON ab_experiment_assignments(group_label);

-- ─────────────────────────────────────────────

-- Create campaign_performance_summary view
CREATE OR REPLACE VIEW campaign_performance_summary AS
SELECT
    pe.campaign_id,
    SUM(pe.impressions) AS total_impressions,
    SUM(pe.clicks) AS total_clicks,
    SUM(pe.conversions) AS total_conversions,
    SUM(pe.spend_usd) AS total_spend_usd,
    SUM(pe.revenue_usd) AS total_revenue_usd,
    CASE
        WHEN SUM(pe.impressions) > 0
        THEN (SUM(pe.clicks)::NUMERIC / SUM(pe.impressions))
        ELSE 0
    END AS ctr,
    CASE
        WHEN SUM(pe.spend_usd) > 0
        THEN (SUM(pe.revenue_usd) / SUM(pe.spend_usd))
        ELSE 0
    END AS roas
FROM
    performance_events pe
GROUP BY
    pe.campaign_id;
