"""
Brand configuration loader for CampaignPilot.

Set ACTIVE_BRAND=meta (or amex, etc.) in your .env file.
Each brand lives in brands/{brand_name}/ with a config.json + knowledge base files.
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BrandConfig:
    brand_id: str                          # e.g. "meta"
    company_name: str                      # e.g. "Meta"
    company_tagline: str                   # e.g. "Build connections that matter"
    industry: str                          # e.g. "Social Media / Digital Advertising"
    business_model: str                    # e.g. "B2B2C — sell ad platform to SMBs who reach consumers"
    product_being_marketed: str            # e.g. "Meta Ads (Facebook, Instagram, Advantage+)"
    target_customer_description: str       # who the campaigns target
    campaign_context: str                  # what campaigns in this system are trying to achieve
    knowledge_base_path: Path             # path to this brand's knowledge base dir
    prohibited_phrases: list[str]          # brand safety — phrases to never use
    brand_voice_summary: str              # one-paragraph voice description
    products: list[dict]                  # key products (id, name, tagline, price_model)
    channels: list[str]                   # typical marketing channels for this brand
    currency: str = "USD"
    geography: str = "United States"


def load_brand(brand_id: str | None = None) -> BrandConfig:
    """
    Load brand configuration from brands/{brand_id}/config.json.

    Falls back to ACTIVE_BRAND env var, then 'meta' as default.

    Args:
        brand_id: Optional override. If None, reads from ACTIVE_BRAND env var.

    Returns:
        BrandConfig instance populated from the brand's config.json

    Raises:
        FileNotFoundError: If the brand config directory or config.json doesn't exist.
    """
    active_brand = brand_id or os.environ.get("ACTIVE_BRAND", "meta")
    config_path = Path(__file__).parent / active_brand / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Brand config not found: {config_path}\n"
            f"Available brands: {[d.name for d in Path(__file__).parent.iterdir() if d.is_dir() and not d.name.startswith('_')]}"
        )

    with open(config_path) as f:
        data = json.load(f)

    kb_path = Path(__file__).parent / active_brand / "knowledge_base"

    return BrandConfig(
        brand_id=active_brand,
        company_name=data["company_name"],
        company_tagline=data["company_tagline"],
        industry=data["industry"],
        business_model=data["business_model"],
        product_being_marketed=data["product_being_marketed"],
        target_customer_description=data["target_customer_description"],
        campaign_context=data["campaign_context"],
        knowledge_base_path=kb_path,
        prohibited_phrases=data["prohibited_phrases"],
        brand_voice_summary=data["brand_voice_summary"],
        products=data["products"],
        channels=data["channels"],
        currency=data.get("currency", "USD"),
        geography=data.get("geography", "United States"),
    )


def get_active_brand() -> BrandConfig:
    """Convenience function: load whichever brand is set in ACTIVE_BRAND env var."""
    return load_brand()
