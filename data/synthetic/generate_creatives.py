"""Generate synthetic Meta SMB marketing ad creatives."""
import json
import random
from typing import List, Dict, Any, Optional

random.seed(42)

# Facebook/Instagram headline and body copy pools
FACEBOOK_HEADLINES = [
    "More customers found your restaurant last month. Here's how.",
    "Your neighbors are searching for what you sell. Are you showing up?",
    "The salon down the street grew bookings 40% with Meta Ads. You can too.",
    "Start your first Meta ad for $5 a day. No marketing degree required.",
    "3 billion people use Meta apps. How many know about your business?",
    "Your competition is already advertising on Facebook. Here's how to catch up.",
    "Turn your satisfied customers into your best ads — automatically.",
    "Local businesses like yours see a median 2.19x return on Meta Ads.",
    "Set up your first campaign in 20 minutes. Really.",
    "Stop guessing which customers to reach. Advantage+ figures it out for you.",
    "Your best customers have look-alikes. Meta Ads can find them.",
    "The holiday shopping season starts now. Is your business ready?",
    "More orders. Same budget. That's what Meta Ads delivers.",
    "Your Instagram feed is a storefront. Let's fill it with customers.",
]

FACEBOOK_BODIES = [
    "You built something worth finding. Meta Ads helps the right people find it — customers in your area who are already interested in what you offer. Start with $5/day and see results within your first week. No long-term contracts, no setup fees.",
    "Restaurants using Meta Ads see an average 2.19x return on their ad spend. That means for every $100 you put in, you're typically seeing $219 back in orders and foot traffic. It takes 20 minutes to set up your first campaign.",
    "Meta's Advantage+ technology automatically tests different versions of your ads and shows the best-performing ones to the people most likely to buy from you. SMBs using Advantage+ see 32% lower cost-per-customer than manual campaigns.",
    "Local retailers are using Meta Ads to reach customers searching for exactly what they sell. You can too. No experience needed. No technical setup. Just your product photos and a budget.",
    "E-commerce sellers are seeing median CTR of 2.19% on their Meta Ads. That's people clicking through from Facebook and Instagram directly to their shop. Start your first campaign today.",
    "Your business deserves customers. Meta has 3 billion of them. Show your ads to the ones ready to buy right now.",
    "Advantage+ is like having a team of marketing experts working for you 24/7. It learns your best customers and finds more like them. Average CPC $1.72. Average CPM $13.48.",
    "WhatsApp Business API connects you directly to your customers on their favorite messaging app. Send order updates, appointment reminders, support. It works on Instagram, Facebook, WhatsApp.",
]

EMAIL_SUBJECTS = [
    "Your free Meta Ads guide is inside",
    "How [Business Name] got 47 new customers last month with $300",
    "3 Meta Ads mistakes costing you customers right now",
    "You haven't run a Meta ad yet. Here's why that's costing you.",
    "Your Q4 advertising playbook (free, from Meta)",
    "Quick question about your marketing budget",
    "See how businesses like yours are winning on Meta",
    "Start advertising on Meta this week — here's everything you need",
    "[First Name], local retailers are seeing 2x returns on Meta Ads",
    "Your competitor just started advertising. Don't get left behind.",
    "Free: The SMB Advertiser's Playbook from Meta",
    "Ready to see real customers? Meta Ads starts at $5/day.",
]

EMAIL_BODIES = [
    "Running a small business means your marketing budget has to work hard. That's exactly why Meta Ads starts at $5 a day with no setup fees — and why 200+ million businesses use our tools to reach their customers. We put together a free guide to help you get your first campaign live this week.",
    "You're losing customers to Meta every day. They're searching for what you sell, scrolling through Instagram, messaging friends about your competitors. Meta Ads puts you right in front of them at that moment. Median ROAS: 2.19x. That's $219 back for every $100 spent.",
    "Advantage+ is different. It's AI-powered. You give it your product photos and budget, and it automatically finds your best customers across Facebook, Instagram, Messenger, and Audience Network. 32% lower cost per customer. Set it and forget it.",
    "WhatsApp Business is where your customers already are. Send order confirmations, shipping updates, appointment reminders, customer support — all from a single dashboard. No monthly fees. Just pay when you advertise.",
    "E-commerce sellers on Meta average 2.19% CTR. That's customers clicking from Instagram straight to your store. Local service businesses see median CPM of $13.48 to reach nearby customers actively searching. Your business is worth it.",
    "Meta Ads is not complicated. Pick your audience (local area, interests, behaviors). Pick your budget ($5/day minimum). Pick your creative. We handle the rest. Most new advertisers see results in their first week.",
]

GOOGLE_HEADLINES = [
    "Facebook Ads for Small Business",
    "Grow Your Business With Meta Ads",
    "Advertise on Instagram & Facebook",
    "Meta Ads — Start From $5/Day",
    "Reach Local Customers — Meta Ads",
    "Instagram Ads for Your Business",
    "Run Your First Facebook Ad Today",
    "Meta Advantage+ — 32% Lower CPA",
    "E-Commerce Ads on Meta & Instagram",
    "Local Business Ads That Work",
    "WhatsApp for Small Business Owners",
    "Reels Ads for SMB Growth",
]

GOOGLE_DESCRIPTIONS = [
    "Set up your first Meta ad in 20 minutes. Reach customers in your area. No setup fee. Start free today.",
    "200M+ businesses use Meta to reach customers. Join them. Flexible budgets. Measurable results. Median ROAS: 2.19x.",
    "Meta Advantage+ uses AI to find your best customers automatically. 32% lower cost per customer vs manual.",
    "Local businesses see median CTR 2.19% on Meta Ads. Reach customers actively searching for what you sell.",
    "Start advertising on Facebook and Instagram for $5/day. No long-term contracts. Pause anytime.",
    "E-commerce sellers see average CPC $1.72 on Meta. Reach ready-to-buy customers across Instagram and Facebook.",
    "WhatsApp Business API: send order updates, shipping info, appointment reminders. No setup fees.",
    "Reels ads reach billions of users. Average CPM $13.48. Get your video in front of customers.",
]

LINKEDIN_HEADLINES = [
    "Scaling SMB customer acquisition with Meta's Advantage+ technology",
    "How franchises are reaching customers across Meta's entire ecosystem",
    "Multi-location SMB success: coordinating Meta campaigns across markets",
    "Building recurring revenue: upselling Advantage+ to existing advertisers",
    "WhatsApp Business API adoption: the next growth vector for SMBs",
    "From zero to 50 new customers: SMB success on Meta in 90 days",
]

LINKEDIN_BODIES = [
    "Meta's Advantage+ isn't just for large brands. SMB advertisers using automated bidding see median ROAS of 2.19x — meaning $219 back for every $100 spent. The AI handles audience finding, creative testing, bid optimization. Your job: pick a budget and a goal.",
    "Local retailers, e-commerce founders, service businesses — they're all finding customers on Meta. And they're spending smart. Average CPC: $1.72. Median CPM: $13.48. Median CTR: 2.19%. Real benchmarks from real SMBs.",
    "WhatsApp Business API is becoming essential infrastructure for SMBs. Send order confirmations, appointment reminders, shipping updates, customer support. On the messaging app your customers already use.",
    "Advantage+ upsells: SMBs who start with manual Facebook ads and see success are ready to graduate. Upsell them on Advantage+, get 32% lower cost per customer, and they stay with you longer.",
]

YOUTUBE_HEADLINES = [
    "Meta Ads for Small Business Owners",
    "How Your Competitors Are Using Meta Ads",
    "Build Your Business With Facebook Ads",
    "Reach More Customers on Instagram",
]

YOUTUBE_BODIES = [
    "Your customers are watching videos on YouTube, scrolling Instagram, messaging friends. Meta Ads puts your business right in front of them. Start with $5/day.",
    "3 billion people use Meta's apps every month. Some of them are looking for exactly what you sell. Advantage+ finds them automatically.",
]

WEBINAR_HEADLINES = [
    "SMB Advertiser Masterclass: Building Your First Campaign on Meta",
    "Advantage+ Deep Dive: Automating Your Ad Operations",
    "WhatsApp Business for E-Commerce: Converting Messages to Orders",
    "Multi-Location SMB Strategy: Coordinating Ads Across Markets",
    "Real Data Workshop: Benchmarks and Best Practices for SMBs",
]

WEBINAR_BODIES = [
    "Join us for a live workshop where we walk through setting up your first Meta campaign step-by-step. Real examples. Real numbers. Real questions answered.",
    "Learn how Advantage+ works, when to use it, how it compares to manual bidding. See live campaign setup and performance analysis.",
    "WhatsApp Business API is changing how SMBs communicate with customers. Learn setup, best practices, and real ROI examples from e-commerce sellers.",
]

CTAS = {
    "facebook": [
        "Start Advertising Free",
        "Create Your First Ad",
        "See How It Works",
        "Get Started",
        "Claim Your Free Guide",
    ],
    "instagram": [
        "Start Advertising Free",
        "Create Your First Ad",
        "See How It Works",
        "Shop Now",
        "Learn More",
    ],
    "email": [
        "Get the Free Guide",
        "Start Your First Campaign",
        "See Pricing",
        "Book a Free Consultation",
        "Claim Your Offer",
    ],
    "google_search": [
        "Start Free Today",
        "Create Your First Ad",
        "See Plans & Pricing",
        "Get Started Now",
    ],
    "linkedin": [
        "Download the SMB Guide",
        "See Case Studies",
        "Start Advertising",
        "Book a Demo",
    ],
    "youtube": [
        "Learn More",
        "Start Advertising",
        "See How It Works",
    ],
    "webinar": [
        "Register Free",
        "Save Your Seat",
        "Join the Webinar",
    ],
}

TONES = {
    "facebook": ["warm_conversational", "outcome_focused", "social_proof_led", "educational"],
    "instagram": ["visual_outcome", "aspirational_grounded", "social_proof"],
    "email": ["helpful_advisor", "data_led", "personal", "educational"],
    "google_search": ["direct_benefit", "competitive", "action_oriented"],
    "linkedin": ["professional_data_led", "peer_credibility"],
    "youtube": ["educational", "inspirational"],
    "webinar": ["educational", "authority"],
}


def _generate_quality_score() -> float:
    """Generate a realistic quality score (3.0-5.0, weighted toward 4.0-4.8)."""
    rand = random.random()
    if rand < 0.70:
        # 70% are "good" (4.0-4.8)
        return round(random.uniform(4.0, 4.8), 2)
    elif rand < 0.90:
        # 20% are "excellent" (4.8-5.0)
        return round(random.uniform(4.8, 5.0), 2)
    else:
        # 10% are "acceptable" (3.0-4.0)
        return round(random.uniform(3.0, 4.0), 2)


def generate_creatives_for_campaign(
    campaign: Dict[str, Any], num_variants_per_channel: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Generate creative variants for a campaign across its channels.

    Args:
        campaign: Campaign dictionary with name, channels, goal, etc.
        num_variants_per_channel: Number of variants per channel (3-5 if None).

    Returns:
        List of creative dictionaries with channel, variants, and metadata.
    """
    if num_variants_per_channel is None:
        num_variants_per_channel = random.randint(3, 5)

    creatives = []

    for channel in campaign.get("channels", []):
        # Select appropriate copy pools and CTAs for channel
        if channel == "facebook":
            headlines = FACEBOOK_HEADLINES
            bodies = FACEBOOK_BODIES
            cta_pool = CTAS["facebook"]
            tone_pool = TONES["facebook"]
            num_variants = random.randint(4, 5)

        elif channel == "instagram":
            headlines = FACEBOOK_HEADLINES  # Reuse Facebook copy
            bodies = FACEBOOK_BODIES
            cta_pool = CTAS["instagram"]
            tone_pool = TONES["instagram"]
            num_variants = random.randint(3, 5)

        elif channel == "email":
            headlines = EMAIL_SUBJECTS
            bodies = EMAIL_BODIES
            cta_pool = CTAS["email"]
            tone_pool = TONES["email"]
            num_variants = random.randint(3, 5)

        elif channel == "google_search":
            headlines = GOOGLE_HEADLINES
            bodies = GOOGLE_DESCRIPTIONS
            cta_pool = CTAS["google_search"]
            tone_pool = TONES["google_search"]
            num_variants = random.randint(3, 4)

        elif channel == "linkedin":
            headlines = LINKEDIN_HEADLINES
            bodies = LINKEDIN_BODIES
            cta_pool = CTAS["linkedin"]
            tone_pool = TONES["linkedin"]
            num_variants = random.randint(3, 4)

        elif channel == "youtube":
            headlines = YOUTUBE_HEADLINES
            bodies = YOUTUBE_BODIES
            cta_pool = CTAS["youtube"]
            tone_pool = TONES["youtube"]
            num_variants = random.randint(2, 3)

        elif channel == "webinar":
            headlines = WEBINAR_HEADLINES
            bodies = WEBINAR_BODIES
            cta_pool = CTAS["webinar"]
            tone_pool = TONES["webinar"]
            num_variants = random.randint(2, 3)

        else:
            continue

        # Generate variants for this channel
        for variant_idx in range(num_variants):
            headline = random.choice(headlines)
            body = random.choice(bodies)
            cta = random.choice(cta_pool)
            tone = random.choice(tone_pool)
            quality_score = _generate_quality_score()

            creative = {
                "campaign_id": None,  # Will be filled during insert
                "channel": channel,
                "variant_index": variant_idx + 1,
                "headline": headline,
                "body": body,
                "cta": cta,
                "tone": tone,
                "quality_score": quality_score,
                "safety_passed": True,
            }

            creatives.append(creative)

    return creatives


if __name__ == "__main__":
    # Example usage
    sample_campaign = {
        "name": "Q3 2024 SMB Acquisition — Restaurant & Food Service — Facebook & Instagram",
        "channels": ["facebook", "instagram", "email"],
        "goal": "Acquire 250 new restaurant advertiser accounts at <$150 cost-per-new-advertiser",
        "target_segment": "Local Retailers in Restaurant & Food Service with 5-100 employees",
    }

    creatives = generate_creatives_for_campaign(sample_campaign)
    print(json.dumps(creatives, indent=2))
