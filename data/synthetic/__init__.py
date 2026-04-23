"""Synthetic data generation module for CampaignPilot.

This package provides utilities for generating realistic synthetic marketing campaign
data for testing and development of the CampaignPilot platform.
"""

from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign

__all__ = [
    "generate_campaigns",
    "generate_creatives_for_campaign",
]
