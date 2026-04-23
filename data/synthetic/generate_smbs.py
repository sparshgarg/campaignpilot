"""Generate a synthetic SMB advertiser pool for CampaignPilot A/B testing.

Produces ~500 records representing Meta's prospective and current SMB advertisers
across US industries, DMAs, and business sizes. Distributions are calibrated to
reflect realistic SMB demographics in the US.
"""

import random
import math
from datetime import date, timedelta
from typing import Any

import numpy as np

random.seed(2024)
np.random.seed(2024)

# ── Industry taxonomy ────────────────────────────────────────────────────────

INDUSTRY_CONFIG = {
    "Restaurant & Food Service": {
        "sub_industries": ["Fast Casual", "Full Service", "Bakery/Café", "Food Truck", "Catering", "Pizza"],
        "weight": 0.18,
        "employee_range": (2, 40),
        "revenue_range": (80_000, 1_500_000),
        "ecommerce_rate": 0.05,
        "physical_location_rate": 0.98,
        "b2c_rate": 0.97,
    },
    "Retail": {
        "sub_industries": ["Apparel", "Home Goods", "Sporting Goods", "Electronics", "Gift Shop", "Boutique"],
        "weight": 0.14,
        "employee_range": (2, 60),
        "revenue_range": (100_000, 3_000_000),
        "ecommerce_rate": 0.45,
        "physical_location_rate": 0.75,
        "b2c_rate": 0.95,
    },
    "E-Commerce": {
        "sub_industries": ["Apparel & Fashion", "Beauty & Cosmetics", "Health & Wellness", "Home Décor", "Niche Products"],
        "weight": 0.12,
        "employee_range": (1, 25),
        "revenue_range": (50_000, 5_000_000),
        "ecommerce_rate": 1.0,
        "physical_location_rate": 0.10,
        "b2c_rate": 0.95,
    },
    "Professional Services": {
        "sub_industries": ["Accounting", "Legal", "Marketing Agency", "IT Consulting", "HR / Recruiting", "Insurance"],
        "weight": 0.11,
        "employee_range": (2, 50),
        "revenue_range": (150_000, 4_000_000),
        "ecommerce_rate": 0.08,
        "physical_location_rate": 0.60,
        "b2c_rate": 0.40,
    },
    "Home Services": {
        "sub_industries": ["Plumbing", "HVAC", "Landscaping", "Cleaning", "Roofing", "General Contractor", "Painting"],
        "weight": 0.10,
        "employee_range": (1, 30),
        "revenue_range": (80_000, 2_000_000),
        "ecommerce_rate": 0.02,
        "physical_location_rate": 0.30,
        "b2c_rate": 0.90,
    },
    "Health & Fitness": {
        "sub_industries": ["Gym / Fitness Studio", "Yoga / Pilates", "Personal Training", "Physical Therapy", "Chiropractic", "Nutrition Coaching"],
        "weight": 0.08,
        "employee_range": (2, 30),
        "revenue_range": (60_000, 1_200_000),
        "ecommerce_rate": 0.15,
        "physical_location_rate": 0.85,
        "b2c_rate": 0.98,
    },
    "Beauty & Personal Care": {
        "sub_industries": ["Hair Salon", "Nail Salon", "Spa / Day Spa", "Barbershop", "Tattoo Studio", "Skincare"],
        "weight": 0.08,
        "employee_range": (1, 20),
        "revenue_range": (50_000, 800_000),
        "ecommerce_rate": 0.10,
        "physical_location_rate": 0.95,
        "b2c_rate": 0.99,
    },
    "Real Estate": {
        "sub_industries": ["Residential Sales", "Property Management", "Commercial Leasing", "Mortgage Brokerage"],
        "weight": 0.06,
        "employee_range": (1, 20),
        "revenue_range": (100_000, 2_500_000),
        "ecommerce_rate": 0.05,
        "physical_location_rate": 0.70,
        "b2c_rate": 0.75,
    },
    "Automotive": {
        "sub_industries": ["Auto Repair", "Car Dealership", "Auto Detailing", "Tires & Wheels", "Auto Parts"],
        "weight": 0.06,
        "employee_range": (3, 50),
        "revenue_range": (120_000, 5_000_000),
        "ecommerce_rate": 0.08,
        "physical_location_rate": 0.97,
        "b2c_rate": 0.88,
    },
    "Travel & Hospitality": {
        "sub_industries": ["Boutique Hotel", "B&B / Inn", "Tour Operator", "Travel Agency", "Event Venue"],
        "weight": 0.07,
        "employee_range": (2, 40),
        "revenue_range": (80_000, 2_000_000),
        "ecommerce_rate": 0.30,
        "physical_location_rate": 0.80,
        "b2c_rate": 0.92,
    },
}

# ── US DMAs (top 30 by population + representative mid/small markets) ─────────

DMA_LIST = [
    # (dma_code, dma_name, state, tier)  tier: 1=top10, 2=11-50, 3=50+
    (501, "New York", "NY", 1),
    (803, "Los Angeles", "CA", 1),
    (602, "Chicago", "IL", 1),
    (504, "Philadelphia", "PA", 1),
    (623, "Dallas-Ft. Worth", "TX", 1),
    (539, "Tampa-St. Petersburg", "FL", 1),
    (511, "Washington DC", "DC", 1),
    (618, "Houston", "TX", 1),
    (505, "Boston", "MA", 1),
    (524, "Atlanta", "GA", 1),
    (561, "Jacksonville", "FL", 2),
    (527, "Indianapolis", "IN", 2),
    (548, "Cleveland-Akron", "OH", 2),
    (507, "Detroit", "MI", 2),
    (613, "Minneapolis-St. Paul", "MN", 2),
    (616, "Phoenix", "AZ", 2),
    (534, "Orlando-Daytona Beach", "FL", 2),
    (554, "St. Louis", "MO", 2),
    (532, "Charlotte", "NC", 2),
    (555, "Denver", "CO", 2),
    (542, "Sacramento", "CA", 2),
    (528, "Miami-Ft. Lauderdale", "FL", 2),
    (535, "Columbus, OH", "OH", 2),
    (659, "San Antonio", "TX", 2),
    (641, "San Francisco-Oakland", "CA", 2),
    (581, "Las Vegas", "NV", 2),
    (557, "Portland, OR", "OR", 2),
    (560, "Raleigh-Durham", "NC", 2),
    (521, "Nashville", "TN", 2),
    (619, "Seattle-Tacoma", "WA", 2),
    (671, "Tulsa", "OK", 3),
    (673, "El Paso", "TX", 3),
    (576, "Omaha", "NE", 3),
    (566, "Harrisburg-Lancaster", "PA", 3),
    (549, "Greenville-Spartanburg", "SC", 3),
    (569, "Huntsville-Decatur", "AL", 3),
    (574, "Baton Rouge", "LA", 3),
    (583, "Des Moines-Ames", "IA", 3),
    (600, "Tri-Cities TN-VA", "TN", 3),
    (512, "Baltimore", "MD", 3),
]

# Weighted DMA selection (tier 1 = 40%, tier 2 = 45%, tier 3 = 15%)
DMA_WEIGHTS = {1: 4.0, 2: 1.5, 3: 0.5}

# ── Business name parts ───────────────────────────────────────────────────────

NAME_PARTS = {
    "prefixes": ["Premier", "Urban", "Local", "Main Street", "Valley", "Summit", "Family", "City", "Pro", "Elite",
                 "Quick", "Fresh", "Bright", "Classic", "Modern", "Core", "Apex", "Peak", "Harbor", "Coastal"],
    "suffixes": {
        "Restaurant & Food Service": ["Kitchen", "Bistro", "Grill", "Café", "Eatery", "Diner"],
        "Retail": ["Shop", "Boutique", "Store", "Market", "Outlet", "Goods"],
        "E-Commerce": ["Store", "Shop", "Co.", "Market", "Deals"],
        "Professional Services": ["Consulting", "Advisors", "Group", "Solutions", "Services", "Associates"],
        "Home Services": ["Solutions", "Services", "Pros", "Experts", "Home Care"],
        "Health & Fitness": ["Fitness", "Wellness", "Health", "Studio", "Training"],
        "Beauty & Personal Care": ["Salon", "Studio", "Spa", "Beauty", "Lounge"],
        "Real Estate": ["Realty", "Properties", "Real Estate", "Homes"],
        "Automotive": ["Auto", "Motors", "Automotive", "Car Care"],
        "Travel & Hospitality": ["Travel", "Ventures", "Stays", "Escapes"],
    },
}

LEAD_SOURCES = [
    "organic_search", "paid_search", "partner_referral",
    "meta_sales_outreach", "event", "social_media", "word_of_mouth",
]

ADVERTISING_EXPERIENCES = ["none", "beginner", "intermediate", "advanced"]
ADV_EXP_WEIGHTS = [0.30, 0.35, 0.25, 0.10]


def _pick_dma() -> dict:
    all_dmas = DMA_LIST
    weights = [DMA_WEIGHTS[row[3]] for row in all_dmas]
    total = sum(weights)
    norm = [w / total for w in weights]
    idx = np.random.choice(len(all_dmas), p=norm)
    code, name, state, _ = all_dmas[idx]
    return {"dma_code": code, "dma_name": name, "state": state}


def _business_name(industry: str) -> str:
    prefix = random.choice(NAME_PARTS["prefixes"])
    suffix_pool = NAME_PARTS["suffixes"].get(industry, ["Co."])
    suffix = random.choice(suffix_pool)
    return f"{prefix} {suffix}"


def _city_from_dma(dma_name: str) -> str:
    return dma_name.split("-")[0].strip().split(",")[0].strip()


def _adv_experience_by_industry(industry: str) -> str:
    if industry in ("E-Commerce", "Professional Services"):
        weights = [0.10, 0.30, 0.40, 0.20]
    elif industry in ("Restaurant & Food Service", "Retail"):
        weights = [0.25, 0.40, 0.25, 0.10]
    else:
        weights = ADV_EXP_WEIGHTS
    return np.random.choice(ADVERTISING_EXPERIENCES, p=weights)


def _monthly_ad_spend(experience: str, revenue: int) -> float:
    base_pct = {"none": 0.0, "beginner": 0.005, "intermediate": 0.012, "advanced": 0.025}
    pct = base_pct[experience] * np.random.uniform(0.5, 1.8)
    spend = revenue * pct / 12
    return round(max(0, spend), 2)


def _acquisition_likelihood(experience: str, has_meta: bool, monthly_spend: float, revenue: int) -> float:
    score = 0.20
    score += {"none": 0.0, "beginner": 0.10, "intermediate": 0.20, "advanced": 0.15}[experience]
    if has_meta:
        score -= 0.10  # already a customer, different funnel
    if monthly_spend > 500:
        score += 0.15
    if monthly_spend > 2000:
        score += 0.10
    if revenue > 500_000:
        score += 0.05
    return round(min(0.95, max(0.02, score + np.random.normal(0, 0.05))), 3)


def generate_smbs(n: int = 500) -> list[dict[str, Any]]:
    """Generate n synthetic SMB advertiser records.

    Args:
        n: Number of SMB records to generate.

    Returns:
        List of dicts matching the smb_advertisers table schema.
    """
    industries = list(INDUSTRY_CONFIG.keys())
    ind_weights = [INDUSTRY_CONFIG[i]["weight"] for i in industries]
    ind_weights_norm = [w / sum(ind_weights) for w in ind_weights]

    records = []
    today = date.today()

    for _ in range(n):
        industry = np.random.choice(industries, p=ind_weights_norm)
        cfg = INDUSTRY_CONFIG[industry]
        sub_industry = random.choice(cfg["sub_industries"])

        dma = _pick_dma()

        emp_min, emp_max = cfg["employee_range"]
        employee_count = int(np.random.lognormal(
            math.log((emp_min + emp_max) / 2), 0.6
        ))
        employee_count = max(emp_min, min(emp_max, employee_count))

        rev_min, rev_max = cfg["revenue_range"]
        annual_revenue = int(np.random.lognormal(
            math.log((rev_min + rev_max) / 2), 0.7
        ))
        annual_revenue = max(rev_min, min(rev_max, annual_revenue))

        business_age = max(1, int(np.random.exponential(5)))
        business_age = min(business_age, 25)

        experience = _adv_experience_by_industry(industry)
        monthly_spend = _monthly_ad_spend(experience, annual_revenue)

        has_meta = experience in ("intermediate", "advanced") and random.random() < 0.65
        if has_meta and experience == "beginner":
            has_meta = random.random() < 0.20

        last_meta = None
        if has_meta:
            days_ago = random.randint(14, 365 * 2)
            last_meta = (today - timedelta(days=days_ago)).isoformat()

        fb_followers = 0
        ig_followers = 0
        if experience != "none":
            fb_followers = int(np.random.lognormal(6, 1.2))
            fb_followers = min(fb_followers, 50_000)
            ig_followers = int(fb_followers * np.random.uniform(0.3, 1.5))
            ig_followers = min(ig_followers, 60_000)

        likelihood = _acquisition_likelihood(experience, has_meta, monthly_spend, annual_revenue)

        is_ecommerce = random.random() < cfg["ecommerce_rate"]
        has_physical = random.random() < cfg["physical_location_rate"]
        biz_type_roll = random.random()
        if biz_type_roll < cfg["b2c_rate"]:
            biz_type = "B2C"
        elif biz_type_roll < cfg["b2c_rate"] + 0.05:
            biz_type = "both"
        else:
            biz_type = "B2B"

        records.append({
            "business_name": _business_name(industry),
            "industry": industry,
            "sub_industry": sub_industry,
            "country": "US",
            "state": dma["state"],
            "city": _city_from_dma(dma["dma_name"]),
            "dma_code": dma["dma_code"],
            "dma_name": dma["dma_name"],
            "zip_code": f"{random.randint(10000, 99999):05d}",
            "employee_count": employee_count,
            "annual_revenue_usd": annual_revenue,
            "business_age_years": business_age,
            "advertising_experience": experience,
            "monthly_ad_spend_usd": monthly_spend,
            "has_run_meta_ads": has_meta,
            "last_meta_ad_date": last_meta,
            "facebook_page_followers": fb_followers,
            "instagram_followers": ig_followers,
            "has_website": experience != "none" or random.random() < 0.45,
            "primary_product_category": sub_industry,
            "business_type": biz_type,
            "is_ecommerce": is_ecommerce,
            "has_physical_location": has_physical,
            "lead_source": random.choice(LEAD_SOURCES),
            "acquisition_likelihood_score": likelihood,
        })

    return records


if __name__ == "__main__":
    smbs = generate_smbs(500)
    print(f"Generated {len(smbs)} SMB records")

    # Quick distribution summary
    from collections import Counter
    industries = Counter(s["industry"] for s in smbs)
    experiences = Counter(s["advertising_experience"] for s in smbs)
    print("\nIndustry distribution:")
    for ind, count in industries.most_common():
        print(f"  {ind}: {count}")
    print("\nAdvertising experience distribution:")
    for exp, count in experiences.most_common():
        print(f"  {exp}: {count}")
    print(f"\nAvg annual revenue: ${sum(s['annual_revenue_usd'] for s in smbs)/len(smbs):,.0f}")
    print(f"% with Meta ads history: {sum(s['has_run_meta_ads'] for s in smbs)/len(smbs)*100:.1f}%")
