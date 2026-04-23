"""
Example integration showing how to use the CampaignPilot evaluation framework.

This file demonstrates:
1. Loading golden datasets
2. Creating custom agents
3. Running evaluations with different metric combinations
4. Interpreting results
"""

import json
from pathlib import Path
from typing import Any

from evals.runner import EvalRunner
from evals.metrics import (
    CompletenessMetric,
    BudgetRealismMetric,
    SqlAccuracyMetric,
    SafetyMetric,
    StrategicCoherenceMetric,
    BrandVoiceMetric,
    InsightQualityMetric,
    BrandSafetyMetric,
)


# Mock agents for demonstration
class MockStrategistAgent:
    """Example strategist agent that generates campaign strategies."""

    def run(self, goal_input: dict) -> dict:
        """Generate strategy based on input."""
        return {
            "recommended_channels": ["LinkedIn", "Email", "Webinar"],
            "budget_split": {
                "LinkedIn": 0.45,
                "Email": 0.35,
                "Webinar": 0.20,
            },
            "primary_message_pillar": "ROI impact through data transparency",
            "kpis": [
                "Conversion rate",
                "Cost per lead",
                "Pipeline influence",
            ],
            "rationale": "Target IT decision makers where our solution shows strongest competitive advantage.",
            "risks": [
                "Market saturation in Q4",
                "Budget constraints",
            ],
        }


class MockCreativeAgent:
    """Example creative agent that generates marketing copy."""

    def run(self, input_brief: dict) -> dict:
        """Generate creative content."""
        return {
            "headline": "See the data your competitors are missing",
            "body": "Lumen Analytics reveals hidden patterns in your customer behavior. Our customers find insights 10x faster than legacy tools.",
            "cta": "Get your free trial",
            "primary_benefit": "Speed to insight",
        }


class MockAnalystAgent:
    """Example analyst agent that generates data insights."""

    def run(self, campaign_data: dict) -> dict:
        """Generate insights from campaign data."""
        return {
            "insight": "LinkedIn ads showed 3.2x higher conversion rate than email. LinkedIn's targeting precision allowed us to reach decision makers directly.",
            "sql": "SELECT channel, COUNT(*) as impressions, SUM(conversions) as conversions, SUM(conversions)/COUNT(*) as conversion_rate FROM campaign_metrics GROUP BY channel ORDER BY conversion_rate DESC",
            "data_source": "campaign_metrics table",
            "recommendation": "Increase LinkedIn budget by 25% for next quarter based on demonstrated ROI.",
        }


def example_strategist_evaluation():
    """Example: Evaluating the strategist agent."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Strategist Agent Evaluation")
    print("="*60)

    # Create golden dataset
    golden_dataset = [
        {
            "id": "strategist_001",
            "input": {
                "goal": "Drive database administrators to trial",
                "segment": "Fortune 500 IT Directors",
                "budget_usd": 50000,
                "campaign_duration_days": 30,
            },
            "expected_output": {
                "recommended_channels": ["LinkedIn", "Email"],
                "budget_split": {"LinkedIn": 0.6, "Email": 0.4},
            },
        },
        {
            "id": "strategist_002",
            "input": {
                "goal": "Build brand awareness among data engineers",
                "segment": "Mid-market tech companies",
                "budget_usd": 100000,
                "campaign_duration_days": 60,
            },
            "expected_output": {
                "recommended_channels": ["LinkedIn", "Reddit", "Conferences"],
                "budget_split": {"LinkedIn": 0.4, "Reddit": 0.3, "Conferences": 0.3},
            },
        },
    ]

    # Define metrics for strategist
    metrics = [
        CompletenessMetric(
            required_fields=[
                "recommended_channels",
                "budget_split",
                "primary_message_pillar",
                "kpis",
                "rationale",
            ]
        ),
        BudgetRealismMetric(),
        StrategicCoherenceMetric(),
    ]

    # Create agent and runner
    agent = MockStrategistAgent()
    runner = EvalRunner()

    # Run evaluation
    report = runner.run(
        agent=agent,
        golden_dataset=golden_dataset,
        metrics=metrics,
        agent_name="strategist",
        dataset_version="v1",
    )

    # Print results
    print(f"\nAgent: {report.agent_name}")
    print(f"Dataset Version: {report.dataset_version}")
    print(f"Examples Evaluated: {report.total_examples}")
    print(f"Overall Result: {'PASSED' if report.passed else 'FAILED'}")
    print(f"\nMetric Scores:")
    for metric_name, scores in report.aggregate_scores.items():
        print(
            f"  {metric_name}: {scores['mean']:.3f} (pass rate: {scores['pass_rate']:.0%})"
        )


def example_creative_evaluation():
    """Example: Evaluating the creative agent."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Creative Agent Evaluation")
    print("="*60)

    golden_dataset = [
        {
            "id": "creative_001",
            "input": {
                "target_audience": "CFOs",
                "value_prop": "Reduce reporting time by 80%",
                "tone": "professional",
            },
            "expected_output": {
                "headline": "Executives love simplicity",
                "body": "Your finance team spends 40+ hours monthly on reports. Lumen cuts that to 8.",
            },
        },
    ]

    # Mock safety checker
    class MockSafetyChecker:
        def check_safety(self, text: str) -> dict:
            violations = []
            if "guarantee" in text.lower():
                violations.append({
                    "type": "unsubstantiated_claim",
                    "severity": "high",
                })
            return {"violations": violations, "passed": len(violations) == 0}

    metrics = [
        CompletenessMetric(required_fields=["headline", "body", "cta"]),
        BrandVoiceMetric(),
        BrandSafetyMetric(safety_checker=MockSafetyChecker()),
    ]

    agent = MockCreativeAgent()
    runner = EvalRunner()

    report = runner.run(
        agent=agent,
        golden_dataset=golden_dataset,
        metrics=metrics,
        agent_name="creative",
        dataset_version="v1",
    )

    print(f"\nAgent: {report.agent_name}")
    print(f"Evaluated: {report.total_examples} examples")
    print(f"Result: {'PASSED' if report.passed else 'FAILED'}")
    print(f"\nMetric Scores:")
    for metric_name, scores in report.aggregate_scores.items():
        status = "✓" if scores["pass_rate"] >= 0.5 else "✗"
        print(
            f"  {status} {metric_name}: {scores['mean']:.3f} (pass rate: {scores['pass_rate']:.0%})"
        )


def example_analyst_evaluation():
    """Example: Evaluating the analyst agent with SQL checking."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Analyst Agent Evaluation")
    print("="*60)

    golden_dataset = [
        {
            "id": "analyst_001",
            "input": {
                "data": {
                    "channels": ["email", "linkedin", "facebook"],
                    "metrics": ["impressions", "clicks", "conversions"],
                }
            },
            "expected_output": {
                "insight": "LinkedIn shows highest conversion rate",
                "sql": "SELECT channel, SUM(conversions) / SUM(clicks) as conversion_rate FROM metrics GROUP BY channel",
            },
        },
    ]

    # Mock DB tool (in practice, this would be your actual database query runner)
    def mock_query_tool(sql: str):
        """Mock query execution."""
        if "SELECT" in sql and "GROUP BY" in sql:
            return [
                {"channel": "linkedin", "conversion_rate": 0.032},
                {"channel": "email", "conversion_rate": 0.024},
            ]
        raise Exception("Invalid query")

    metrics = [
        CompletenessMetric(required_fields=["insight", "sql", "recommendation"]),
        SqlAccuracyMetric(db_query_tool=mock_query_tool),
        InsightQualityMetric(),
    ]

    agent = MockAnalystAgent()
    runner = EvalRunner()

    report = runner.run(
        agent=agent,
        golden_dataset=golden_dataset,
        metrics=metrics,
        agent_name="analyst",
        dataset_version="v1",
    )

    print(f"\nAgent: {report.agent_name}")
    print(f"Evaluated: {report.total_examples} examples")
    print(f"Result: {'PASSED' if report.passed else 'FAILED'}")
    print(f"Estimated Cost: ${report.estimated_cost_usd:.4f}")
    print(f"Duration: {report.run_duration_ms:.0f}ms")
    print(f"\nMetric Scores:")
    for metric_name, scores in report.aggregate_scores.items():
        status = "✓" if scores["pass_rate"] >= 0.5 else "✗"
        print(
            f"  {status} {metric_name}: {scores['mean']:.3f} (min: {scores['min']:.3f}, max: {scores['max']:.3f})"
        )


def example_creating_golden_dataset():
    """Example: How to create and save a golden dataset."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Creating Golden Datasets")
    print("="*60)

    # Example golden dataset structure
    golden_dataset = [
        {
            "id": "example_001",
            "input": {
                "goal": "Drive qualified leads from target segment",
                "segment": "VP Product at B2B SaaS companies",
                "budget_usd": 75000,
                "campaign_duration_days": 45,
            },
            "expected_output": {
                "recommended_channels": [
                    "LinkedIn",
                    "Product Hunt",
                    "Industry Conferences",
                ],
                "budget_split": {
                    "LinkedIn": 0.5,
                    "Product Hunt": 0.2,
                    "Industry Conferences": 0.3,
                },
                "primary_message_pillar": "Product-led growth acceleration",
                "kpis": [
                    "Conversion rate",
                    "Customer acquisition cost",
                    "Trial-to-paid rate",
                ],
                "rationale": "VPs of Product prefer LinkedIn for professional content and industry conferences for networking. Budget allocation reflects channel effectiveness for this segment.",
                "risks": [
                    "Conference sponsorship costs higher than budgeted",
                    "Product Hunt saturation in SaaS category",
                    "LinkedIn organic reach declining",
                ],
            },
        },
        {
            "id": "example_002",
            "input": {
                "goal": "Re-engage lapsed customers",
                "segment": "Lapsed users (no activity >6 months)",
                "budget_usd": 25000,
                "campaign_duration_days": 30,
            },
            "expected_output": {
                "recommended_channels": ["Email", "Retargeting Ads"],
                "budget_split": {
                    "Email": 0.8,
                    "Retargeting": 0.2,
                },
                "primary_message_pillar": "New features and improvements",
                "kpis": [
                    "Reactivation rate",
                    "Cost per reactivated user",
                ],
                "rationale": "Email is most cost-effective for re-engagement. Retargeting ads capture high-intent users as they browse.",
                "risks": [
                    "High unsubscribe rate",
                    "Spam filter blocking",
                ],
            },
        },
    ]

    # Save to file
    output_path = "/tmp/golden_dataset.json"
    with open(output_path, "w") as f:
        json.dump(golden_dataset, f, indent=2)

    print(f"\nGolden dataset created with {len(golden_dataset)} examples")
    print(f"Saved to: {output_path}")
    print("\nDataset structure:")
    print("  - id: Unique identifier for the example")
    print("  - input: What you give to the agent")
    print("  - expected_output: What the agent should produce")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CampaignPilot Evaluation Framework - Integration Examples")
    print("="*60)

    try:
        example_strategist_evaluation()
    except Exception as e:
        print(f"Strategist example error: {e}")

    try:
        example_creative_evaluation()
    except Exception as e:
        print(f"Creative example error: {e}")

    try:
        example_analyst_evaluation()
    except Exception as e:
        print(f"Analyst example error: {e}")

    try:
        example_creating_golden_dataset()
    except Exception as e:
        print(f"Golden dataset example error: {e}")

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)
