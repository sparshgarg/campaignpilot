# Integration Examples

This document shows practical examples for using the synthetic data generators in your CampaignPilot system.

## Quick Start: Seed Your Database

```bash
# Install dependencies
pip install -r data/synthetic/requirements.txt

# Set your database connection
export DATABASE_URL="postgresql://username:password@localhost:5432/campaignpilot"

# Run the seeder
python data/synthetic/seed_db.py
```

Expected output:
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

## Example 1: Generate and Export Campaigns as JSON

```python
from data.synthetic.generate_campaigns import generate_campaigns
import json

# Generate 50 campaigns
campaigns = generate_campaigns(num_campaigns=50)

# Export to JSON file
with open("campaigns.json", "w") as f:
    json.dump(campaigns, f, indent=2)

print(f"Exported {len(campaigns)} campaigns to campaigns.json")
```

## Example 2: Analyze Campaign Performance Simulation

```python
from data.synthetic.generate_campaigns import generate_campaigns
from datetime import date, timedelta
import numpy as np

campaigns = generate_campaigns(num_campaigns=5)

print("Campaign Performance Analysis")
print("=" * 60)

for campaign in campaigns:
    print(f"\n{campaign['name']}")
    print(f"  Budget: ${campaign['budget_usd']:,}")
    
    # Calculate expected metrics based on budget
    duration_days = (
        date.fromisoformat(campaign['end_date']) - 
        date.fromisoformat(campaign['start_date'])
    ).days
    
    print(f"  Duration: {duration_days} days")
    print(f"  Daily budget: ${campaign['budget_usd'] / duration_days:,.2f}")
    print(f"  Channels: {', '.join(campaign['channels'])}")
```

## Example 3: Create a Creative Performance Report

```python
from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign

campaigns = generate_campaigns(num_campaigns=3)

print("Creative Variant Quality Report")
print("=" * 80)

for campaign in campaigns:
    print(f"\nCampaign: {campaign['name']}")
    creatives = generate_creatives_for_campaign(campaign)
    
    by_channel = {}
    for creative in creatives:
        channel = creative['channel']
        if channel not in by_channel:
            by_channel[channel] = []
        by_channel[channel].append(creative)
    
    for channel, variants in by_channel.items():
        print(f"\n  {channel.upper()} Variants:")
        for variant in variants:
            print(f"    [{variant['quality_score']}] {variant['headline'][:50]}...")
            print(f"      CTA: {variant['cta']}")
```

Output:
```
Creative Variant Quality Report
================================================================================

Campaign: Q3 CFO Outreach — LinkedIn + Email

  LINKEDIN Variants:
    [4.32] Stop Rebuilding the Same Report Every Week...
      CTA: See a Live Demo
    [3.91] Your CFO Wants Real-Time Numbers. Can You Deliver?...
      CTA: Download the Guide
    [4.67] We Analyzed 500 Operations Teams. Here's What Separ...
      CTA: Book a 20-Min Call

  EMAIL Variants:
    [4.15] Real-time dashboards in 2 weeks (no engineers needed)...
      CTA: Book a Demo
    [4.52] Lumen + your data = automated reports...
      CTA: Start Your Free Trial
```

## Example 4: Manual Database Insert (without seeder)

```python
import psycopg2
import json
from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign

conn = psycopg2.connect("dbname=campaignpilot user=postgres")
cur = conn.cursor()

campaigns = generate_campaigns(num_campaigns=10)

for campaign in campaigns:
    # Insert campaign
    cur.execute("""
        INSERT INTO campaigns 
        (name, goal, target_segment, budget_usd, start_date, end_date, status, channels)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        campaign['name'],
        campaign['goal'],
        campaign['target_segment'],
        campaign['budget_usd'],
        campaign['start_date'],
        campaign['end_date'],
        campaign['status'],
        json.dumps(campaign['channels'])
    ))
    
    campaign_id = cur.fetchone()[0]
    
    # Insert creatives
    creatives = generate_creatives_for_campaign(campaign)
    for creative in creatives:
        cur.execute("""
            INSERT INTO creatives
            (campaign_id, channel, variant_index, headline, body, cta, tone, quality_score, safety_passed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            campaign_id,
            creative['channel'],
            creative['variant_index'],
            creative['headline'],
            creative['body'],
            creative['cta'],
            creative['tone'],
            creative['quality_score'],
            creative['safety_passed']
        ))

conn.commit()
cur.close()
conn.close()
print("Successfully inserted campaigns and creatives")
```

## Example 5: Batch Operations for Large Datasets

```python
from data.synthetic.generate_campaigns import generate_campaigns
import psycopg2.extras
import json

conn = psycopg2.connect("dbname=campaignpilot user=postgres")

campaigns = generate_campaigns(num_campaigns=50)

# Prepare batch data
campaign_rows = []
for campaign in campaigns:
    campaign_rows.append((
        campaign['name'],
        campaign['goal'],
        campaign['target_segment'],
        campaign['budget_usd'],
        campaign['start_date'],
        campaign['end_date'],
        campaign['status'],
        json.dumps(campaign['channels'])
    ))

# Batch insert
with conn.cursor() as cur:
    psycopg2.extras.execute_batch(cur, """
        INSERT INTO campaigns 
        (name, goal, target_segment, budget_usd, start_date, end_date, status, channels)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, campaign_rows, page_size=100)

conn.commit()
conn.close()
print(f"Batch inserted {len(campaigns)} campaigns")
```

## Example 6: Generate Data for Testing

```python
from data.synthetic.generate_campaigns import generate_campaigns
from unittest import TestCase

class TestCampaignMetrics(TestCase):
    def setUp(self):
        """Generate fresh test data for each test."""
        self.campaigns = generate_campaigns(num_campaigns=3)
    
    def test_campaign_budget_within_range(self):
        """Verify campaign budgets are in expected ranges."""
        for campaign in self.campaigns:
            self.assertGreaterEqual(campaign['budget_usd'], 5000)
            self.assertLessEqual(campaign['budget_usd'], 150000)
    
    def test_campaign_dates_valid(self):
        """Verify campaign dates are logical."""
        from datetime import date
        for campaign in self.campaigns:
            start = date.fromisoformat(campaign['start_date'])
            end = date.fromisoformat(campaign['end_date'])
            self.assertLess(start, end)
            self.assertGreaterEqual((end - start).days, 60)
    
    def test_campaign_channels_defined(self):
        """Verify campaigns have valid channels."""
        valid_channels = {
            'email', 'linkedin', 'google_search', 'facebook', 
            'content_syndication', 'webinar'
        }
        for campaign in self.campaigns:
            for channel in campaign['channels']:
                self.assertIn(channel, valid_channels)
```

Run tests:
```bash
python -m pytest test_campaigns.py -v
```

## Example 7: Generate Partial Data for Specific Needs

```python
from data.synthetic.generate_campaigns import generate_campaigns, PERSONAS, PRODUCTS

# Generate only LinkedIn email campaigns
campaigns = generate_campaigns(num_campaigns=20)
linkedin_campaigns = [
    c for c in campaigns if 'linkedin' in c['channels']
]

print(f"Found {len(linkedin_campaigns)} LinkedIn campaigns")

# Generate only Pro-tier campaigns
pro_campaigns = [
    c for c in campaigns if 'Pro' in c['goal']
]

print(f"Found {len(pro_campaigns)} Lumen Pro campaigns")

# Calculate aggregate stats
total_budget = sum(c['budget_usd'] for c in campaigns)
avg_budget = total_budget / len(campaigns)

print(f"\nTotal budget across {len(campaigns)} campaigns: ${total_budget:,}")
print(f"Average campaign budget: ${avg_budget:,.0f}")
```

## Example 8: Performance Comparison

```python
from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign

campaigns = generate_campaigns(num_campaigns=5)

print("Channel Performance Comparison")
print("=" * 60)

channel_stats = {}

for campaign in campaigns:
    creatives = generate_creatives_for_campaign(campaign)
    for creative in creatives:
        channel = creative['channel']
        if channel not in channel_stats:
            channel_stats[channel] = {'count': 0, 'quality_sum': 0}
        
        channel_stats[channel]['count'] += 1
        channel_stats[channel]['quality_sum'] += creative['quality_score']

for channel, stats in sorted(channel_stats.items()):
    avg_quality = stats['quality_sum'] / stats['count']
    print(f"{channel:20} | Variants: {stats['count']:3} | Avg Quality: {avg_quality:.2f}")
```

Output:
```
Channel Performance Comparison
============================================================
content_syndication | Variants:   5 | Avg Quality: 4.18
email               | Variants:  14 | Avg Quality: 4.24
facebook            | Variants:   6 | Avg Quality: 4.32
google_search       | Variants:   6 | Avg Quality: 4.15
linkedin            | Variants:   8 | Avg Quality: 4.19
webinar             | Variants:   4 | Avg Quality: 4.27
```

## Environment Variables

For database seeding, configure:

```bash
# PostgreSQL connection
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"

# Optional: Logging level
export LOG_LEVEL="INFO"

# Optional: Random seed for reproducibility (default: 42)
export RANDOM_SEED="42"
```

## Performance Tips

1. **Batch inserts** for large datasets (500+ rows at a time)
2. **Disable foreign key checks** during initial load if needed:
   ```sql
   ALTER TABLE IF EXISTS creatives DISABLE TRIGGER ALL;
   -- ... inserts ...
   ALTER TABLE IF EXISTS creatives ENABLE TRIGGER ALL;
   ```

3. **Index creation** after seeding:
   ```sql
   CREATE INDEX idx_campaigns_status ON campaigns(status);
   CREATE INDEX idx_creatives_campaign ON creatives(campaign_id);
   CREATE INDEX idx_perf_events_date ON performance_events(event_date);
   ```

4. **Connection pooling** for Python apps:
   ```python
   from psycopg2 import pool
   
   connection_pool = pool.SimpleConnectionPool(1, 20, os.getenv('DATABASE_URL'))
   ```

## Troubleshooting

**ImportError: No module named 'faker'**
```bash
pip install faker psycopg2-binary numpy python-dotenv
```

**psycopg2.OperationalError: FATAL: database "campaignpilot" does not exist**
```bash
createdb campaignpilot
```

**Connection refused on localhost:5432**
```bash
# Ensure PostgreSQL is running
sudo systemctl start postgresql
# Or verify your DATABASE_URL
echo $DATABASE_URL
```

## Next Steps

1. Review generated data: `SELECT COUNT(*) FROM campaigns;`
2. Analyze campaign performance: See dashboard queries below
3. Test your analytics pipeline with realistic data
4. Benchmark your system's performance

### Sample Analytics Queries

```sql
-- Campaign count by status
SELECT status, COUNT(*) FROM campaigns GROUP BY status;

-- Average budget by channel composition
SELECT 
  channels::text,
  COUNT(*) as campaign_count,
  AVG(budget_usd) as avg_budget
FROM campaigns
GROUP BY channels
ORDER BY avg_budget DESC;

-- Performance by campaign
SELECT 
  c.name,
  COUNT(pe.id) as event_count,
  SUM(pe.impressions) as total_impressions,
  SUM(pe.clicks) as total_clicks,
  SUM(pe.conversions) as total_conversions,
  SUM(pe.spend_usd) as total_spend,
  SUM(pe.revenue_usd) as total_revenue
FROM campaigns c
LEFT JOIN performance_events pe ON c.id = pe.campaign_id
GROUP BY c.id, c.name
ORDER BY total_spend DESC;
```

## Support

For issues or questions about the synthetic data generation system, refer to the main README.md in this directory.
