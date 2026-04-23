"""Generate synthetic historical campaigns for Meta's SMB advertiser acquisition program."""
import json
import random
from datetime import date, timedelta
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

random.seed(42)


@dataclass
class Campaign:
    """Represents a Meta SMB marketing campaign."""

    name: str
    goal: str
    target_segment: str
    budget_usd: int
    start_date: date
    end_date: date
    status: str
    channels: List[str]
    campaign_type: str
    vertical: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert campaign to dictionary with date strings."""
        return {
            "name": self.name,
            "goal": self.goal,
            "target_segment": self.target_segment,
            "budget_usd": self.budget_usd,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
            "channels": self.channels,
            "campaign_type": self.campaign_type,
            "vertical": self.vertical,
        }


CAMPAIGN_NAME_TEMPLATES = [
    "Q{q} {year} SMB Acquisition — {vertical} — {channel_label}",
    "{vertical} Advertiser Re-engagement — {channel_label} — Q{q}",
    "Advantage+ Upsell — {segment} Advertisers — {channel_label}",
    "WhatsApp Business API — {vertical} Outreach — {channel_label}",
    "Meta Business Suite Launch — {vertical} — {channel_label}",
    "New Advertiser Onboarding — {vertical} — Email Nurture",
    "Lapsed Advertiser Win-Back — 90-Day Inactive — {channel_label}",
    "Q{q} {vertical} SMB — Lookalike Audience Expansion",
    "Advantage+ Awareness — E-Commerce SMBs — {channel_label}",
    "Holiday Season Push — Local Retail Acquisition — {channel_label}",
    "Back-to-School — Education & Tutoring SMBs — {channel_label}",
    "Restaurant SMB — Local Awareness Campaign — {channel_label}",
    "{vertical} Case Study Amplification — {channel_label}",
    "Multi-Location SMB — Franchise Advertiser Program — {channel_label}",
    "SMB Budget Season — Q4 Decision Maker Outreach — {channel_label}",
    "Meta Ads Essentials — First-Time Advertiser — {channel_label}",
    "Service Business Lead Gen — WhatsApp Conversion — {channel_label}",
    "Creator Economy — SMB Brand Partnerships — {channel_label}",
    "Reels for Business — Video Advertiser Acquisition — {channel_label}",
    "SMB Success Stories — Social Proof Campaign — {channel_label}",
]

VERTICALS = [
    "Restaurant & Food Service",
    "E-Commerce",
    "Professional Services",
    "Health & Wellness",
    "Home Services",
    "Retail",
    "Education & Tutoring",
    "Real Estate",
    "Auto Services",
    "Beauty & Personal Care",
]

SEGMENTS = [
    "Local Retailers",
    "E-Commerce Founders",
    "Service Business Owners",
    "Multi-Location SMBs",
    "First-Time Advertisers",
    "Lapsed Advertisers ($500-2k/mo)",
    "Active Advertisers ($2k+/mo)",
]

CHANNEL_GROUPS = {
    "facebook_instagram": ["facebook", "instagram"],
    "email_nurture": ["email"],
    "paid_search": ["google_search"],
    "full_digital": ["facebook", "instagram", "email", "google_search"],
    "social_email": ["facebook", "instagram", "email"],
    "linkedin_email": ["linkedin", "email"],
    "webinar_email": ["webinar", "email"],
    "youtube_social": ["youtube", "facebook", "instagram"],
}

CAMPAIGN_TYPES = [
    "smb_acquisition",
    "lapsed_reengagement",
    "advantage_plus_upsell",
    "whatsapp_adoption",
    "brand_awareness",
]


def _generate_campaign_name(template: str, channel_group: str, vertical: str, segment: str) -> str:
    """Generate a campaign name by filling a template."""
    q = random.randint(1, 4)
    year = random.choice([2023, 2024])
    channel_labels = {
        "facebook_instagram": "Facebook & Instagram",
        "email_nurture": "Email",
        "paid_search": "Google Search",
        "full_digital": "Multi-Channel",
        "social_email": "Social + Email",
        "linkedin_email": "LinkedIn + Email",
        "webinar_email": "Webinar + Email",
        "youtube_social": "YouTube + Social",
    }
    channel_label = channel_labels.get(channel_group, "Digital")

    return template.format(
        q=q,
        year=year,
        vertical=vertical,
        channel_label=channel_label,
        segment=segment,
    )


def _generate_budget() -> int:
    """Generate a realistic campaign budget using weighted distribution."""
    rand = random.random()
    if rand < 0.20:
        # 20% small budget
        return random.randint(10000, 30000)
    elif rand < 0.60:
        # 40% mid-tier budget
        return random.randint(30000, 75000)
    elif rand < 0.90:
        # 30% substantial budget
        return random.randint(75000, 150000)
    else:
        # 10% large budget
        return random.randint(150000, 400000)


def _generate_goal(campaign_name: str, vertical: str, campaign_type: str) -> str:
    """Generate a realistic Meta SMB acquisition goal."""
    if campaign_type == "smb_acquisition":
        num_advertisers = random.randint(150, 500)
        cost_per = random.randint(100, 200)
        return f"Acquire {num_advertisers} new SMB advertisers in {vertical} at <${cost_per} cost-per-new-advertiser, Q{random.randint(1, 4)} 2024"

    elif campaign_type == "lapsed_reengagement":
        num_reactivated = random.randint(100, 300)
        return f"Re-engage and reactivate {num_reactivated} lapsed {vertical} advertisers (90+ days inactive)"

    elif campaign_type == "advantage_plus_upsell":
        num_upgrades = random.randint(50, 200)
        return f"Drive {num_upgrades} upgrades to Advantage+ for {vertical} SMB advertisers, increase ROAS by 25%+"

    elif campaign_type == "whatsapp_adoption":
        num_activations = random.randint(75, 250)
        return f"Activate WhatsApp Business API for {num_activations} {vertical} SMBs for customer messaging"

    else:  # brand_awareness
        impressions = random.randint(1000000, 5000000)
        return f"Generate {impressions:,} impressions and establish Meta advertising leadership among {vertical} SMBs"


def _generate_target_segment_desc(vertical: str, segment: str) -> str:
    """Generate a detailed target segment description."""
    size_options = [
        "1-50 employees",
        "5-100 employees",
        "10-500 employees",
        "50-1000 employees",
    ]
    size = random.choice(size_options)

    return f"{segment} in {vertical} with {size}, monthly ad spend $500-$10k, decision-maker (owner, marketing manager)"


def _random_date_in_range(start_date: date, end_date: date) -> date:
    """Generate a random date between start and end dates."""
    days_between = (end_date - start_date).days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)


def generate_campaigns(num_campaigns: int = 50) -> List[Dict[str, Any]]:
    """Generate 50 realistic Meta SMB marketing campaigns.

    Args:
        num_campaigns: Number of campaigns to generate (default: 50).

    Returns:
        List of campaign dictionaries with all required fields.
    """
    campaigns = []
    campaign_start_date = date(2023, 1, 1)
    campaign_end_date = date(2024, 9, 1)

    for i in range(num_campaigns):
        # Select random attributes
        vertical = random.choice(VERTICALS)
        segment = random.choice(SEGMENTS)
        campaign_type = random.choice(CAMPAIGN_TYPES)
        channel_group = random.choice(list(CHANNEL_GROUPS.keys()))
        channels = CHANNEL_GROUPS[channel_group]

        # Generate dates (Meta campaigns are faster: 30-90 days)
        start_date = _random_date_in_range(campaign_start_date, campaign_end_date)
        duration_days = random.randint(30, 90)
        end_date = start_date + timedelta(days=duration_days)

        # Generate core campaign data
        template = random.choice(CAMPAIGN_NAME_TEMPLATES)
        name = _generate_campaign_name(template, channel_group, vertical, segment)
        goal = _generate_goal(name, vertical, campaign_type)
        target_segment = _generate_target_segment_desc(vertical, segment)
        budget = _generate_budget()

        campaign = Campaign(
            name=name,
            goal=goal,
            target_segment=target_segment,
            budget_usd=budget,
            start_date=start_date,
            end_date=end_date,
            status="completed",
            channels=channels,
            campaign_type=campaign_type,
            vertical=vertical,
        )

        campaigns.append(campaign.to_dict())

    return campaigns


if __name__ == "__main__":
    campaigns = generate_campaigns()
    print(json.dumps(campaigns, indent=2))
