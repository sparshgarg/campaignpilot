"""Seed the CampaignPilot database with Meta SMB marketing synthetic data.

This script populates the database with 50 realistic campaigns, their creatives,
performance metrics, and optimization recommendations. All data is synthetic but
structured to reflect real Meta SMB advertiser acquisition patterns.
"""

import sys
import os
import json
import random
import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign

load_dotenv()
console = Console()

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Channel-specific baseline metrics (derived from Meta benchmarks)
CHANNEL_BASELINES = {
    "facebook": {"ctr_alpha": 2.0, "ctr_beta": 90, "ctr_scale": 0.0219, "cpc": 1.72, "conversion_rate": 0.038},
    "instagram": {"ctr_alpha": 1.8, "ctr_beta": 95, "ctr_scale": 0.018, "cpc": 1.95, "conversion_rate": 0.032},
    "email": {"open_rate": 0.22, "ctr_of_opens": 0.18, "conversion_rate": 0.045},
    "google_search": {"ctr_alpha": 2.5, "ctr_beta": 115, "ctr_scale": 0.021, "cpc": 4.22, "conversion_rate": 0.042},
    "linkedin": {"ctr_alpha": 1.2, "ctr_beta": 300, "ctr_scale": 0.0039, "cpc": 8.50, "conversion_rate": 0.028},
    "youtube": {"ctr_alpha": 1.5, "ctr_beta": 200, "ctr_scale": 0.005, "cpc": 3.20, "conversion_rate": 0.015},
    "webinar": {"registration_rate": 0.035, "attendance_rate": 0.42, "conversion_rate": 0.12},
}

# Campaign type-specific advertiser values
CAMPAIGN_TYPE_VALUES = {
    "smb_acquisition": 1250,
    "lapsed_reengagement": 850,
    "advantage_plus_upsell": 2100,
    "whatsapp_adoption": 450,
    "brand_awareness": 600,
}


class CampaignSeeder:
    """Seeds CampaignPilot database with synthetic Meta SMB marketing data."""

    def __init__(self, database_url: str):
        """Initialize the seeder with database connection.

        Args:
            database_url: PostgreSQL connection string.

        Raises:
            ValueError: If database_url is not provided.
        """
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        self.database_url = database_url
        self.conn = None
        self.campaign_id_map = {}  # Maps campaign index to database ID
        self.stats = {
            "campaigns_inserted": 0,
            "briefs_inserted": 0,
            "creatives_inserted": 0,
            "performance_events_inserted": 0,
            "recommendations_inserted": 0,
        }

    def connect(self) -> None:
        """Connect to PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.info("Connected to database")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from database")

    def _execute_query(self, query: str, params: Tuple = None) -> Any:
        """Execute a single query safely.

        Args:
            query: SQL query string.
            params: Query parameters.

        Returns:
            Query result or None.
        """
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params or ())
                return cur.fetchall()
        except psycopg2.Error as e:
            logger.error(f"Query failed: {e}")
            self.conn.rollback()
            raise

    def insert_campaigns(self, campaigns: List[Dict[str, Any]]) -> None:
        """Insert campaigns into the database.

        Args:
            campaigns: List of campaign dictionaries.
        """
        logger.info(f"Inserting {len(campaigns)} campaigns...")

        with self.conn.cursor() as cur:
            for idx, campaign in enumerate(campaigns):
                try:
                    query = """
                        INSERT INTO campaigns
                        (name, goal, target_segment, budget_usd, start_date, end_date, status, channels)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """
                    params = (
                        campaign["name"],
                        campaign["goal"],
                        campaign["target_segment"],
                        campaign["budget_usd"],
                        campaign["start_date"],
                        campaign["end_date"],
                        campaign["status"],
                        campaign["channels"],
                    )

                    cur.execute(query, params)
                    campaign_id = cur.fetchone()[0]
                    self.campaign_id_map[idx] = campaign_id
                    self.stats["campaigns_inserted"] += 1

                except psycopg2.Error as e:
                    logger.error(f"Failed to insert campaign {idx}: {e}")
                    self.conn.rollback()
                    raise

            self.conn.commit()
        logger.info(f"Successfully inserted {len(campaigns)} campaigns")

    def insert_campaign_briefs(self, campaigns: List[Dict[str, Any]]) -> None:
        """Insert campaign briefs with Meta SMB-specific structure.

        Args:
            campaigns: List of campaign dictionaries.
        """
        logger.info("Inserting campaign briefs...")

        message_templates = {
            "smb_acquisition": [
                "Outcome-first: more customers for your business",
                "Attract high-intent SMBs ready to launch their first campaign",
                "Build awareness among SMB decision-makers searching for ad solutions",
                "Lower barriers to entry: show how easy Meta Ads is to start",
            ],
            "lapsed_reengagement": [
                "Win-back: remind advertisers of their success previously",
                "Reactivation: timely offers for dormant accounts",
                "Prove ROI: show benchmarks and recent SMB success stories",
            ],
            "advantage_plus_upsell": [
                "Automation benefits: let AI handle audience and creative testing",
                "Cost savings: 32% lower CPA with Advantage+",
                "Upgrade path for successful manual advertisers",
            ],
            "whatsapp_adoption": [
                "Customer communication on their favorite messaging app",
                "Order confirmations, shipping updates, appointment reminders",
                "Build recurring relationships through WhatsApp Business API",
            ],
            "brand_awareness": [
                "Establish Meta advertising as essential for SMBs",
                "Position Meta as the most accessible platform for SMB growth",
                "Long-term brand lift for future consideration",
            ],
        }

        rationale_templates = [
            "Target segment shows high purchase intent based on recent advertiser activity",
            "Channel mix selected to maximize reach while controlling customer acquisition cost",
            "Creative messaging tailored to SMB decision-maker pain points and goals",
            "Timeline aligns with SMB budget cycles and business planning seasons",
            "Budget allocation optimized based on historical channel performance and benchmarks",
        ]

        with self.conn.cursor() as cur:
            for idx, campaign in enumerate(campaigns):
                campaign_id = self.campaign_id_map.get(idx)
                if not campaign_id:
                    continue

                try:
                    campaign_type = campaign.get("campaign_type", "smb_acquisition")
                    message_pool = message_templates.get(campaign_type, message_templates["smb_acquisition"])

                    brief_content = {
                        "campaign_type": campaign_type,
                        "recommended_channels": campaign["channels"],
                        "primary_message_pillar": random.choice(message_pool),
                        "target_audience_description": campaign["target_segment"],
                        "kpis": [
                            "cost_per_new_advertiser" if campaign_type == "smb_acquisition" else "reactivation_rate",
                            "new_advertiser_volume" if campaign_type == "smb_acquisition" else "advertiser_retention",
                            "30_day_retention",
                        ],
                        "rationale": random.choice(rationale_templates),
                    }

                    quality_score = round(random.uniform(4.0, 5.0), 2)
                    created_by_agent = "strategist"
                    campaign_start = campaign["start_date"]
                    approved_date = (
                        date.fromisoformat(campaign_start) if isinstance(campaign_start, str) else campaign_start
                    ) + timedelta(days=random.randint(1, 7))

                    query = """
                        INSERT INTO campaign_briefs
                        (campaign_id, content, quality_score, created_by_agent, approved_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    params = (
                        campaign_id,
                        json.dumps(brief_content),
                        quality_score,
                        created_by_agent,
                        approved_date.isoformat(),
                    )

                    cur.execute(query, params)
                    self.stats["briefs_inserted"] += 1

                except psycopg2.Error as e:
                    logger.error(f"Failed to insert brief for campaign {idx}: {e}")
                    self.conn.rollback()
                    raise

            self.conn.commit()
        logger.info(f"Successfully inserted {self.stats['briefs_inserted']} briefs")

    def insert_creatives(self, campaigns: List[Dict[str, Any]]) -> None:
        """Insert creative variants for all campaigns.

        Args:
            campaigns: List of campaign dictionaries.
        """
        logger.info("Generating and inserting creatives...")

        with self.conn.cursor() as cur:
            for idx, campaign in enumerate(campaigns):
                campaign_id = self.campaign_id_map.get(idx)
                if not campaign_id:
                    continue

                try:
                    creatives = generate_creatives_for_campaign(campaign)

                    for creative in creatives:
                        query = """
                            INSERT INTO creatives
                            (campaign_id, channel, variant_index, headline, body, cta, tone, quality_score, safety_passed)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        params = (
                            campaign_id,
                            creative["channel"],
                            creative["variant_index"],
                            creative["headline"],
                            creative["body"],
                            creative["cta"],
                            creative["tone"],
                            creative["quality_score"],
                            creative["safety_passed"],
                        )

                        cur.execute(query, params)
                        self.stats["creatives_inserted"] += 1

                except psycopg2.Error as e:
                    logger.error(f"Failed to insert creatives for campaign {idx}: {e}")
                    self.conn.rollback()
                    raise

            self.conn.commit()
        logger.info(f"Successfully inserted {self.stats['creatives_inserted']} creatives")

    def _generate_performance_metrics(
        self, campaign: Dict[str, Any], channel: str, day: date
    ) -> Dict[str, Any]:
        """Generate realistic daily performance metrics for a channel.

        Uses Meta benchmarks: Median ROAS 2.19x, CTR 2.19%, CPC $1.72, CPM $13.48

        Args:
            campaign: Campaign dictionary.
            channel: Channel name (e.g., 'facebook', 'email').
            day: Date for the metrics.

        Returns:
            Dictionary of performance metrics.
        """
        # Calculate days elapsed (with fatigue decay)
        start_date = campaign["start_date"]
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date)
        days_elapsed = (day - start_date).days

        # Base impressions with fatigue decay (1.5% for social, 0.8% for others)
        end_date = campaign["end_date"]
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date)

        total_duration = (end_date - start_date).days
        num_channels = len(campaign["channels"])
        daily_budget = campaign["budget_usd"] / total_duration / num_channels

        base_impressions = int(campaign["budget_usd"] * 5 / total_duration / num_channels)
        decay_rate = 0.985 if channel in ["facebook", "instagram"] else 0.992
        decay_factor = decay_rate ** days_elapsed
        impressions = int(base_impressions * decay_factor * random.uniform(0.8, 1.2))
        impressions = max(100, impressions)

        # CTR by channel using beta distribution
        baseline = CHANNEL_BASELINES.get(channel, CHANNEL_BASELINES["facebook"])

        if channel == "email":
            # Email: open_rate * ctr_of_opens
            open_rate = random.uniform(0.18, 0.26)
            ctr_of_opens = random.uniform(0.15, 0.22)
            ctr = open_rate * ctr_of_opens
            clicks = int(impressions * ctr)
        elif channel == "webinar":
            # Webinar: registration_rate
            ctr = baseline.get("registration_rate", 0.035)
            clicks = int(impressions * ctr)
        else:
            # Social/search: beta distribution scaled to baseline
            alpha = baseline.get("ctr_alpha", 2.0)
            beta_param = baseline.get("ctr_beta", 100)
            ctr_scale = baseline.get("ctr_scale", 0.015)
            ctr = np.random.beta(alpha, beta_param) * (ctr_scale * 3)
            ctr = min(0.15, max(0.0005, ctr))
            clicks = int(impressions * ctr)

        clicks = max(1, clicks)

        # Conversion rate (varies by channel)
        conv_baseline = baseline.get("conversion_rate", 0.03)
        conversion_rate = np.random.normal(conv_baseline, conv_baseline * 0.25)
        conversion_rate = min(0.12, max(0.002, conversion_rate))

        conversions = int(clicks * conversion_rate)

        # Spend proportional to impressions
        if channel == "email":
            cpm = 0.5
        elif channel == "webinar":
            cpm = 2.0
        else:
            cpm = baseline.get("cpc", 1.72)
            if channel != "google_search" and channel != "linkedin":
                cpm = np.random.normal(13.48, 2.5)  # Meta benchmark CPM
                cpm = max(5, min(25, cpm))

        spend_usd = round(impressions * cpm / 1000, 2) if cpm < 10 else round(clicks * cpm, 2)

        # Revenue based on campaign type and conversions
        campaign_type = campaign.get("campaign_type", "smb_acquisition")
        base_value = CAMPAIGN_TYPE_VALUES.get(campaign_type, 1250)
        mean_deal = base_value
        std_deal = base_value * 0.3

        advertiser_value = max(300, np.random.normal(mean_deal, std_deal))
        revenue_usd = round(conversions * advertiser_value, 2)

        return {
            "impressions": impressions,
            "clicks": clicks,
            "ctr": round(ctr, 6),
            "conversions": conversions,
            "conversion_rate": round(conversion_rate, 6),
            "spend_usd": spend_usd,
            "revenue_usd": revenue_usd,
        }

    def insert_performance_events(self, campaigns: List[Dict[str, Any]]) -> None:
        """Insert daily performance metrics for all campaign × channel pairs.

        Args:
            campaigns: List of campaign dictionaries.
        """
        logger.info("Generating and inserting performance events...")

        batch_size = 500
        batch = []

        with self.conn.cursor() as cur:
            for idx, campaign in enumerate(campaigns):
                campaign_id = self.campaign_id_map.get(idx)
                if not campaign_id:
                    continue

                try:
                    start_date = campaign["start_date"]
                    if isinstance(start_date, str):
                        start_date = date.fromisoformat(start_date)

                    end_date = campaign["end_date"]
                    if isinstance(end_date, str):
                        end_date = date.fromisoformat(end_date)

                    # For each day and channel pair, generate metrics
                    current_day = start_date
                    while current_day <= end_date:
                        for channel in campaign.get("channels", []):
                            metrics = self._generate_performance_metrics(campaign, channel, current_day)

                            query = """
                                INSERT INTO performance_events
                                (campaign_id, channel, event_date, impressions, clicks, conversions, spend_usd, revenue_usd)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            params = (
                                campaign_id,
                                channel,
                                current_day.isoformat(),
                                metrics["impressions"],
                                metrics["clicks"],
                                metrics["conversions"],
                                metrics["spend_usd"],
                                metrics["revenue_usd"],
                            )

                            batch.append((query, params))
                            self.stats["performance_events_inserted"] += 1

                            # Commit batch when it reaches size
                            if len(batch) >= batch_size:
                                for q, p in batch:
                                    cur.execute(q, p)
                                self.conn.commit()
                                batch = []

                        current_day += timedelta(days=1)

                except psycopg2.Error as e:
                    logger.error(f"Failed to insert performance events for campaign {idx}: {e}")
                    self.conn.rollback()
                    raise

            # Commit remaining batch
            if batch:
                for q, p in batch:
                    cur.execute(q, p)
                self.conn.commit()

        logger.info(f"Successfully inserted {self.stats['performance_events_inserted']} performance events")

    def insert_optimization_recommendations(self, campaigns: List[Dict[str, Any]]) -> None:
        """Insert optimization recommendations tailored to campaign types.

        Args:
            campaigns: List of campaign dictionaries.
        """
        logger.info("Inserting optimization recommendations...")

        recommendation_templates = {
            "smb_acquisition": [
                "creative_refresh",
                "audience_expansion",
                "bid_adjustment",
            ],
            "lapsed_reengagement": [
                "offer_change",
                "creative_refresh",
                "channel_pause",
            ],
            "advantage_plus_upsell": [
                "budget_increase",
                "creative_refresh",
                "audience_expansion",
            ],
            "whatsapp_adoption": [
                "audience_narrowing",
                "offer_change",
                "channel_optimization",
            ],
            "brand_awareness": [
                "budget_reallocation",
                "creative_refresh",
                "frequency_cap_increase",
            ],
        }

        description_templates = {
            "creative_refresh": [
                "Test {num} new creative variants on {channel} — engagement declining",
                "Refresh headlines on {channel} — performance below benchmarks",
                "Pause underperforming creatives — launch new messaging variants",
            ],
            "audience_expansion": [
                "Expand audience to include {persona} segments in {vertical}",
                "Build lookalike audiences based on top {pct}% converting advertisers",
                "Test new geographic expansion — strong intent signals from {location}",
            ],
            "bid_adjustment": [
                "Increase bids on {channel} by {pct}% — showing strong ROAS above benchmarks",
                "Optimize {channel} bids based on time-of-day performance patterns",
                "Reduce bids on {channel} by {pct}% — performance below 2.19x ROAS target",
            ],
            "offer_change": [
                "Update offer messaging to emphasize Advantage+ benefits — higher conversion potential",
                "Test time-limited offer on {channel} to reactivate lapsed advertisers",
                "Introduce WhatsApp Business API as upsell for existing customers",
            ],
            "channel_pause": [
                "Pause {channel} — unable to achieve target cost-per-advertiser",
                "Pause {channel} pending creative refresh — reallocate budget to stronger channels",
            ],
            "budget_increase": [
                "Increase budget for {channel} by ${amount} — underutilized high-performer reaching {persona}",
                "Allocate {pct}% more budget to Advantage+ upsell campaigns in {vertical}",
            ],
            "audience_narrowing": [
                "Narrow audience targeting to {persona} in {vertical} — higher conversion rates",
                "Focus WhatsApp adoption on e-commerce segment — best response rates",
            ],
            "channel_optimization": [
                "Shift ${amount} from {channel_1} to {channel_2} — better conversion rates for {vertical}",
                "Reallocate {pct}% of budget from underperforming channels to email nurture",
            ],
            "frequency_cap_increase": [
                "Increase frequency cap on {channel} — audience still responsive to message",
                "Expand impression share on {vertical} awareness campaign",
            ],
        }

        with self.conn.cursor() as cur:
            for idx, campaign in enumerate(campaigns):
                campaign_id = self.campaign_id_map.get(idx)
                if not campaign_id:
                    continue

                try:
                    campaign_type = campaign.get("campaign_type", "smb_acquisition")
                    rec_types = recommendation_templates.get(campaign_type, recommendation_templates["smb_acquisition"])
                    num_recommendations = random.randint(2, 3)
                    selected_types = random.sample(rec_types, min(num_recommendations, len(rec_types)))

                    for rec_type in selected_types:
                        # Generate description based on type
                        templates = description_templates.get(rec_type, [rec_type])
                        description = random.choice(templates)

                        # Fill in template variables
                        channels = campaign.get("channels", ["facebook"])
                        if channels:
                            channel = random.choice(channels)
                            channel_1 = random.choice(channels)
                            channel_2 = random.choice(channels)
                        else:
                            channel = channel_1 = channel_2 = "facebook"

                        vertical = campaign.get("vertical", "Restaurant & Food Service")
                        location = random.choice(["North", "South", "East", "West", "Central"])

                        description = description.replace("{channel}", channel)
                        description = description.replace("{channel_1}", channel_1)
                        description = description.replace("{channel_2}", channel_2)
                        description = description.replace("{amount}", str(random.randint(5000, 25000)))
                        description = description.replace("{pct}", str(random.randint(10, 40)))
                        description = description.replace("{persona}", random.choice(["owner", "marketing manager", "decision-maker"]))
                        description = description.replace("{vertical}", vertical)
                        description = description.replace("{num}", str(random.randint(3, 5)))
                        description = description.replace("{location}", location)

                        priority = random.choice(["low", "medium", "high"])
                        expected_impact = round(random.uniform(0.08, 0.40), 2)

                        query = """
                            INSERT INTO optimization_recommendations
                            (campaign_id, recommendation_type, description, expected_impact)
                            VALUES (%s, %s, %s, %s)
                        """
                        params = (
                            campaign_id,
                            rec_type,
                            description,
                            expected_impact,
                        )

                        cur.execute(query, params)
                        self.stats["recommendations_inserted"] += 1

                except psycopg2.Error as e:
                    logger.error(f"Failed to insert recommendations for campaign {idx}: {e}")
                    self.conn.rollback()
                    raise

            self.conn.commit()
        logger.info(f"Successfully inserted {self.stats['recommendations_inserted']} recommendations")

    def print_summary(self, campaigns: List[Dict[str, Any]]) -> None:
        """Print a rich summary table of inserted data.

        Args:
            campaigns: List of campaigns that were inserted.
        """
        if not campaigns:
            return

        start_dates = [c["start_date"] for c in campaigns]
        end_dates = [c["end_date"] for c in campaigns]

        start_dates = [d if isinstance(d, date) else date.fromisoformat(d) for d in start_dates]
        end_dates = [d if isinstance(d, date) else date.fromisoformat(d) for d in end_dates]

        min_date = min(start_dates)
        max_date = max(end_dates)

        # Create rich table
        table = Table(title="CampaignPilot Database Seeding Summary", show_header=True, header_style="bold cyan")
        table.add_column("Data Type", style="cyan")
        table.add_column("Count", justify="right", style="green")

        table.add_row("Campaigns", str(self.stats["campaigns_inserted"]))
        table.add_row("Campaign Briefs", str(self.stats["briefs_inserted"]))
        table.add_row("Creatives", str(self.stats["creatives_inserted"]))
        table.add_row("Performance Events", str(self.stats["performance_events_inserted"]))
        table.add_row("Recommendations", str(self.stats["recommendations_inserted"]))

        console.print(table)
        console.print(f"\nDate range covered: {min_date.isoformat()} to {max_date.isoformat()}", style="yellow")

    def seed(self) -> None:
        """Execute the full seeding process."""
        try:
            self.connect()

            # Generate all campaign data
            campaigns = generate_campaigns(num_campaigns=50)
            logger.info(f"Generated {len(campaigns)} campaigns")

            # Insert data in order
            self.insert_campaigns(campaigns)
            self.insert_campaign_briefs(campaigns)
            self.insert_creatives(campaigns)
            self.insert_performance_events(campaigns)
            self.insert_optimization_recommendations(campaigns)

            # Print summary
            self.print_summary(campaigns)

        except Exception as e:
            logger.error(f"Seeding failed: {e}")
            raise
        finally:
            self.disconnect()


def main():
    """Main entry point for the seeding script."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    seeder = CampaignSeeder(database_url)
    seeder.seed()


if __name__ == "__main__":
    main()
