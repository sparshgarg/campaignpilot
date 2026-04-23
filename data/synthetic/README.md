# CampaignPilot Synthetic Data Generation

This module generates production-quality synthetic marketing campaign data for CampaignPilot, a B2B SaaS marketing automation platform for Lumen Analytics.

## Overview

The synthetic data system consists of three main components:

1. **Campaign Generator** - Creates 50 realistic historical marketing campaigns
2. **Creative Generator** - Produces authentic ad copy variants across multiple channels
3. **Database Seeder** - Populates the database with campaigns, creatives, performance metrics, and recommendations

## File Structure

```
data/synthetic/
├── __init__.py                 # Module exports
├── generate_campaigns.py        # Campaign data generation
├── generate_creatives.py        # Ad creative generation
├── seed_db.py                   # Database seeding orchestration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## Installation

```bash
pip install -r data/synthetic/requirements.txt
```

## Usage

### Option 1: Direct Python Import

Generate campaigns programmatically:

```python
from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign

# Generate 50 realistic campaigns
campaigns = generate_campaigns(num_campaigns=50)

# Generate creatives for a campaign
campaign = campaigns[0]
creatives = generate_creatives_for_campaign(campaign)
```

### Option 2: Database Seeding

Populate your database with synthetic data:

```bash
# Set DATABASE_URL environment variable
export DATABASE_URL="postgresql://user:password@localhost/campaignpilot"

# Run the seeder
python data/synthetic/seed_db.py
```

## Data Structure

### Campaigns

Each campaign contains:

- **name**: Realistic campaign name from templates (e.g., "Q3 CFO Outreach — LinkedIn + Email")
- **goal**: Specific, quantified objective (e.g., "Generate 45 MQLs for Lumen Pro from mid-market CFOs in Q3")
- **target_segment**: Detailed audience description (e.g., "CFO at B2B SaaS companies with 100-500 employees")
- **budget_usd**: Weighted distribution:
  - 30% chance: $5k-20k
  - 40% chance: $20k-60k
  - 20% chance: $60k-100k
  - 10% chance: $100k-150k
- **start_date**: Random date between 2023-01-01 and 2024-06-01
- **end_date**: start_date + 60-180 days
- **status**: Always "completed" for historical data
- **channels**: Selected from 6 predefined channel groups

### Creatives

Each creative variant includes:

- **campaign_id**: Reference to parent campaign
- **channel**: Distribution channel (linkedin, email, google_search, facebook, content_syndication, webinar)
- **variant_index**: Position in the variant set (1-5)
- **headline**: Channel-appropriate headline
- **body**: Copy body text
- **cta**: Call-to-action text
- **tone**: Tonal descriptor (professional_formal, conversational, data_led, etc.)
- **quality_score**: Float 3.0-5.0 (weighted toward 4-4.5)
- **safety_passed**: Boolean (always True for synthetic data)

### Performance Events

Daily metrics for each campaign × channel pair:

- **impressions**: Starts at budget × 5, decays ~2% per day
- **clicks**: Calculated from impressions × CTR
- **ctr**: Channel-specific beta distribution (linkedin ~0.39%, email ~0.8%, google ~2.1%)
- **conversions**: clicks × conversion_rate
- **conversion_rate**: Beta distribution (1.5-1.0, 80-120)
- **spend_usd**: Proportional to impressions with channel-specific CPM
- **revenue_usd**: Conversions × product-specific deal value:
  - Lumen Core: ~$8,964 (±$2,000)
  - Lumen Pro: ~$28,764 (±$5,000)
  - Lumen Enterprise: ~$89,964 (±$15,000)

### Campaign Briefs

Strategic metadata for each campaign:

- **content**: JSON with recommended_channels, primary_message, kpis, rationale
- **quality_score**: 3.5-5.0
- **created_by_agent**: "strategist"
- **approved_at**: Random date after campaign start

### Optimization Recommendations

2-4 suggestions per campaign:

- **recommendation_type**: bid_adjustment, budget_reallocation, creative_refresh, audience_expansion, channel_pause
- **description**: Realistic, context-specific recommendation
- **priority**: low, medium, high
- **expected_impact**: 0.05-0.35 (5%-35% improvement)

## Data Authenticity

All synthetic data reflects real B2B SaaS marketing patterns:

### Campaign Templates (20 variations)
- Quarterly persona outreach
- Product trial acceleration
- Pain-point series
- Competitive displacement
- Account-based marketing
- Industry vertical focus
- And more...

### Ad Copy Pools
- **LinkedIn**: 12 realistic headlines, 5+ body variants
- **Email**: 10 subject lines, 5 body templates
- **Google Search**: 10 headlines, 6 descriptions
- **Facebook**: 6 headlines, 3 conversational bodies
- **Content Syndication**: 5 educational headlines, 3 body variants
- **Webinar**: 5 event titles, 2 descriptions

### Realistic Metrics
- CTR varies by channel with proper beta distributions
- Conversion rates account for product complexity and target persona
- Revenue calculations use product-tier appropriate deal values
- Daily fatigue modeled through exponential decay
- Budget allocation proportional to campaign duration

## Seeding Output

The seeder produces a summary like:

```
================================================================================
CampaignPilot Database Seeding Summary
================================================================================
Campaigns inserted:             50
Campaign briefs inserted:       50
Creatives inserted:             347
Performance events inserted:    23,650
Recommendations inserted:       198

Date range covered:             2023-01-01 to 2024-08-15
================================================================================
```

## Key Features

### 1. Type Safety
All modules use Python type hints for clarity and IDE support.

### 2. Reproducibility
Random seed is fixed at 42 across all generators for consistent results.

### 3. Scalability
Performance event batching (500 rows) prevents memory overflow with large datasets.

### 4. Realistic Distributions
- Budgets use weighted random selection
- CTR and conversion rates use beta distributions
- Deal values use gaussian distributions with product-specific parameters
- Campaign decay models real-world ad fatigue

### 5. Complete Documentation
Every module includes comprehensive docstrings following NumPy style.

## Database Schema Requirements

The seeder expects these tables to exist:

```sql
CREATE TABLE campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    goal TEXT NOT NULL,
    target_segment TEXT,
    budget_usd INTEGER,
    start_date DATE,
    end_date DATE,
    status VARCHAR(50),
    channels JSONB
);

CREATE TABLE campaign_briefs (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    content JSONB,
    quality_score FLOAT,
    created_by_agent VARCHAR(100),
    approved_at TIMESTAMP
);

CREATE TABLE creatives (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    channel VARCHAR(50),
    variant_index INTEGER,
    headline TEXT,
    body TEXT,
    cta VARCHAR(100),
    tone VARCHAR(50),
    quality_score FLOAT,
    safety_passed BOOLEAN
);

CREATE TABLE performance_events (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    channel VARCHAR(50),
    event_date DATE,
    impressions INTEGER,
    clicks INTEGER,
    ctr FLOAT,
    conversions INTEGER,
    conversion_rate FLOAT,
    spend_usd FLOAT,
    revenue_usd FLOAT
);

CREATE TABLE optimization_recommendations (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    recommendation_type VARCHAR(50),
    description TEXT,
    priority VARCHAR(20),
    expected_impact FLOAT
);
```

## Performance Characteristics

- **Campaign generation**: ~100ms for 50 campaigns
- **Creative generation**: ~150ms for 50 campaigns (3-5 variants each)
- **Performance event generation**: ~2-3 seconds (25k+ rows)
- **Database insert time**: ~10-15 seconds (network dependent)
- **Total seeding time**: ~20-30 seconds for full 50-campaign dataset

## Customization

### Generate Fewer Campaigns

```python
campaigns = generate_campaigns(num_campaigns=10)
```

### Custom Creative Variants

```python
creatives = generate_creatives_for_campaign(campaign, num_variants_per_channel=2)
```

### Modify Templates

Edit the pool constants in `generate_campaigns.py`:

```python
CAMPAIGN_TEMPLATES = [
    "Your custom template — {channel_label}",
    # ...
]
```

## Testing

Test individual generators:

```bash
# Test campaign generation
python data/synthetic/generate_campaigns.py | head -50

# Test creative generation
python data/synthetic/generate_creatives.py
```

## Notes

- All dates are in ISO 8601 format (YYYY-MM-DD)
- All monetary values are in USD
- CTR (click-through rate) is stored as a decimal (0.0039 = 0.39%)
- Conversion rates use the same decimal format
- JSONB fields support full PostgreSQL JSON querying

## License

This synthetic data generation module is part of CampaignPilot and follows the same license as the main project.
