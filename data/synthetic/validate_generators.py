#!/usr/bin/env python3
"""Validation script for synthetic data generators.

This script tests all generators and reports on data quality and authenticity.
"""

import sys
from pathlib import Path
from datetime import date
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.synthetic.generate_campaigns import generate_campaigns
from data.synthetic.generate_creatives import generate_creatives_for_campaign


def validate_campaigns(campaigns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate campaign data structure and content.

    Args:
        campaigns: List of campaign dictionaries.

    Returns:
        Validation report dictionary.
    """
    report = {
        "total_campaigns": len(campaigns),
        "all_have_required_fields": True,
        "date_ranges_valid": True,
        "budgets_in_range": True,
        "channels_valid": True,
        "field_completeness": 0,
    }

    required_fields = {
        "name",
        "goal",
        "target_segment",
        "budget_usd",
        "start_date",
        "end_date",
        "status",
        "channels",
    }

    valid_channels = {
        "email",
        "linkedin",
        "google_search",
        "facebook",
        "content_syndication",
        "webinar",
    }

    complete_fields = 0

    for campaign in campaigns:
        # Check required fields
        if not all(field in campaign for field in required_fields):
            report["all_have_required_fields"] = False

        # Check all fields are present
        if all(field in campaign for field in required_fields):
            complete_fields += 1

        # Validate date range
        try:
            start = date.fromisoformat(campaign["start_date"])
            end = date.fromisoformat(campaign["end_date"])
            if not start < end or (end - start).days < 60:
                report["date_ranges_valid"] = False
        except (ValueError, KeyError):
            report["date_ranges_valid"] = False

        # Validate budget
        if not (5000 <= campaign.get("budget_usd", 0) <= 150000):
            report["budgets_in_range"] = False

        # Validate channels
        for channel in campaign.get("channels", []):
            if channel not in valid_channels:
                report["channels_valid"] = False

    report["field_completeness"] = (
        complete_fields / len(campaigns) * 100 if campaigns else 0
    )

    return report


def validate_creatives(
    campaigns: List[Dict[str, Any]], creatives_per_campaign: List[List[Dict]]
) -> Dict[str, Any]:
    """Validate creative data structure and content.

    Args:
        campaigns: List of campaign dictionaries.
        creatives_per_campaign: List of creative lists per campaign.

    Returns:
        Validation report dictionary.
    """
    report = {
        "total_creatives": 0,
        "avg_per_campaign": 0,
        "all_have_required_fields": True,
        "quality_scores_valid": True,
        "channels_match_campaigns": True,
        "field_completeness": 0,
    }

    required_fields = {
        "channel",
        "variant_index",
        "headline",
        "body",
        "cta",
        "tone",
        "quality_score",
        "safety_passed",
    }

    total_creatives = 0
    complete_fields = 0

    for campaign, creatives in zip(campaigns, creatives_per_campaign):
        total_creatives += len(creatives)
        campaign_channels = set(campaign.get("channels", []))

        for creative in creatives:
            # Check required fields
            if not all(field in creative for field in required_fields):
                report["all_have_required_fields"] = False
            else:
                complete_fields += 1

            # Validate quality score
            qs = creative.get("quality_score", 0)
            if not (3.0 <= qs <= 5.0):
                report["quality_scores_valid"] = False

            # Check channel matches campaign
            if creative.get("channel") not in campaign_channels:
                report["channels_match_campaigns"] = False

    report["total_creatives"] = total_creatives
    report["avg_per_campaign"] = (
        total_creatives / len(campaigns) if campaigns else 0
    )
    report["field_completeness"] = (
        complete_fields / total_creatives * 100 if total_creatives else 0
    )

    return report


def validate_quality_distribution(creatives_per_campaign: List[List[Dict]]) -> Dict:
    """Validate quality score distribution.

    Args:
        creatives_per_campaign: List of creative lists per campaign.

    Returns:
        Distribution statistics.
    """
    all_scores = []
    for creatives in creatives_per_campaign:
        for creative in creatives:
            all_scores.append(creative["quality_score"])

    if not all_scores:
        return {}

    sorted_scores = sorted(all_scores)
    mid = len(sorted_scores) // 2

    return {
        "count": len(all_scores),
        "min": min(all_scores),
        "max": max(all_scores),
        "mean": sum(all_scores) / len(all_scores),
        "median": sorted_scores[mid],
        "target_range_pct": (
            sum(1 for s in all_scores if 3.8 <= s <= 4.5)
            / len(all_scores)
            * 100
        ),
    }


def print_report(
    campaign_report: Dict,
    creative_report: Dict,
    quality_distribution: Dict,
) -> None:
    """Print validation report in a readable format.

    Args:
        campaign_report: Campaign validation report.
        creative_report: Creative validation report.
        quality_distribution: Quality score distribution stats.
    """
    print("\n" + "=" * 80)
    print("SYNTHETIC DATA GENERATOR VALIDATION REPORT")
    print("=" * 80)

    # Campaign validation
    print("\n[CAMPAIGNS]")
    print(f"  Total campaigns: {campaign_report['total_campaigns']}")
    print(
        f"  All have required fields: {campaign_report['all_have_required_fields']}"
    )
    print(f"  Date ranges valid: {campaign_report['date_ranges_valid']}")
    print(f"  Budgets in range (5k-150k): {campaign_report['budgets_in_range']}")
    print(f"  Channels valid: {campaign_report['channels_valid']}")
    print(f"  Field completeness: {campaign_report['field_completeness']:.1f}%")

    # Creative validation
    print("\n[CREATIVES]")
    print(f"  Total creatives: {creative_report['total_creatives']}")
    print(f"  Average per campaign: {creative_report['avg_per_campaign']:.1f}")
    print(
        f"  All have required fields: {creative_report['all_have_required_fields']}"
    )
    print(f"  Quality scores valid (3.0-5.0): {creative_report['quality_scores_valid']}")
    print(
        f"  Channels match campaigns: {creative_report['channels_match_campaigns']}"
    )
    print(f"  Field completeness: {creative_report['field_completeness']:.1f}%")

    # Quality distribution
    if quality_distribution:
        print("\n[QUALITY SCORE DISTRIBUTION]")
        print(f"  Count: {quality_distribution['count']}")
        print(f"  Min: {quality_distribution['min']:.2f}")
        print(f"  Max: {quality_distribution['max']:.2f}")
        print(f"  Mean: {quality_distribution['mean']:.2f}")
        print(f"  Median: {quality_distribution['median']:.2f}")
        print(
            f"  In target range (3.8-4.5): {quality_distribution['target_range_pct']:.1f}%"
        )

    # Overall status
    all_valid = (
        campaign_report["all_have_required_fields"]
        and campaign_report["date_ranges_valid"]
        and campaign_report["budgets_in_range"]
        and campaign_report["channels_valid"]
        and creative_report["all_have_required_fields"]
        and creative_report["quality_scores_valid"]
        and creative_report["channels_match_campaigns"]
    )

    print("\n[STATUS]")
    if all_valid:
        print("  ✓ ALL VALIDATIONS PASSED")
    else:
        print("  ✗ SOME VALIDATIONS FAILED")
        if not campaign_report["all_have_required_fields"]:
            print("    - Campaign missing required fields")
        if not campaign_report["date_ranges_valid"]:
            print("    - Campaign date ranges invalid")
        if not campaign_report["budgets_in_range"]:
            print("    - Campaign budgets out of range")
        if not campaign_report["channels_valid"]:
            print("    - Invalid channels in campaigns")
        if not creative_report["all_have_required_fields"]:
            print("    - Creative missing required fields")
        if not creative_report["quality_scores_valid"]:
            print("    - Creative quality scores out of range")
        if not creative_report["channels_match_campaigns"]:
            print("    - Creative channels don't match campaigns")

    print("=" * 80 + "\n")


def main():
    """Run validation on generated synthetic data."""
    print("Generating test data...")

    # Generate test data
    campaigns = generate_campaigns(num_campaigns=20)
    creatives_per_campaign = [
        generate_creatives_for_campaign(campaign) for campaign in campaigns
    ]

    # Validate
    campaign_report = validate_campaigns(campaigns)
    creative_report = validate_creatives(campaigns, creatives_per_campaign)
    quality_distribution = validate_quality_distribution(creatives_per_campaign)

    # Print report
    print_report(campaign_report, creative_report, quality_distribution)

    # Return exit code
    all_valid = (
        campaign_report["all_have_required_fields"]
        and campaign_report["date_ranges_valid"]
        and campaign_report["budgets_in_range"]
        and campaign_report["channels_valid"]
        and creative_report["all_have_required_fields"]
        and creative_report["quality_scores_valid"]
        and creative_report["channels_match_campaigns"]
    )

    return 0 if all_valid else 1


if __name__ == "__main__":
    sys.exit(main())
