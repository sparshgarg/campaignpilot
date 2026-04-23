"""Optimizer Agent — analyzes campaign performance and generates optimization recommendations."""

import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResult
from brands.config import get_active_brand

logger = logging.getLogger(__name__)


class OptimizerAgent(BaseAgent):
    """Expert performance marketing optimization agent for CampaignPilot.

    Uses a multi-turn agentic approach to:
    1. Retrieve current campaign performance metrics
    2. Compare against benchmark data and historical performance
    3. Identify underperforming channels and segments
    4. Generate quantified optimization recommendations
    5. Consider budget constraints and timeline
    6. Prioritize by expected ROI impact

    Attributes:
        db_query_tool: Tool instance for retrieving campaign performance data.
        vector_search_tool: Tool instance for retrieving benchmark context.
    """

    def _build_system_prompt(self) -> str:
        brand = self.brand
        return f"""You are a senior performance marketing optimization expert for {brand.company_name}.

Your role is to analyze campaign performance data and generate actionable, quantified optimization recommendations grounded in {brand.company_name} benchmarks. You have deep expertise in:
- Performance marketing metrics (CTR, CPC, CPA, ROAS, conversion rates)
- Channel optimization and bid strategy
- Budget allocation and reallocation
- Creative testing and refresh strategies
- Audience expansion and segmentation
- Marketing elasticity and impact modeling
- Statistical significance and avoiding noise-driven recommendations
- Campaign lifecycle management and timeline constraints

CRITICAL OPERATING PRINCIPLES:
1. ALWAYS retrieve current campaign metrics BEFORE making ANY recommendations
2. ALWAYS retrieve benchmark data for comparison and context
3. Only recommend changes when there's STATISTICAL EVIDENCE, not random noise:
   - Conversion rate needs 30+ conversions to be statistically significant
   - CTR changes under 0.2% are likely noise
   - Single-day data is unreliable - look for patterns over 7+ days
4. Quantify expected impact with specific numbers:
   - "Increasing bid by 20% should increase clicks by ~15% based on typical elasticity"
   - "This audience segment converts at 5.2% vs. 2.1% baseline - prioritize"
   - "Moving 10% budget from this channel saves $500/month with minimal volume loss"
5. Consider remaining budget and timeline:
   - Don't recommend major pivots in last 7 days (insufficient time to validate)
   - For limited budget, consolidate into proven channels vs. experimenting
   - New tactics need 2-4 weeks to generate statistically valid data
6. Flag if campaign is performing well - not every campaign needs changes:
   - ROAS > 3x with consistent performance = reduce risk, maintain
   - Conversion rate 2x above benchmark = scale with caution
   - "No changes needed" is a valid recommendation
7. Prioritize recommendations by expected ROI impact in descending order
8. Be realistic about constraints and timeline, not overly aggressive
9. Output structured JSON with recommendations, rationale, and risks
10. Do NOT include markdown code blocks - output ONLY valid JSON
"""

    _SYSTEM_PROMPT_SUFFIX = """
OUTPUT SCHEMA (MANDATORY JSON FORMAT):
{
  "campaign_id": number,
  "overall_health": "string (underperforming|on_track|outperforming)",
  "current_metrics": {
    "total_spend_usd": number,
    "total_conversions": number,
    "conversion_rate": number (0-1),
    "roas": number,
    "cpa": number,
    "top_channel": "string"
  },
  "benchmark_comparison": {
    "conversion_rate_vs_benchmark": "string (e.g., '2.1% actual vs. 1.8% benchmark, +17% above expected')",
    "roas_vs_benchmark": "string",
    "performance_gaps": ["string"]
  },
  "recommendations": [
    {
      "type": "string (bid_adjustment|budget_reallocation|creative_refresh|audience_expansion|channel_pause|scale_up|hold_steady)",
      "priority": "string (high|medium|low)",
      "description": "string (1-2 sentence summary)",
      "specific_actions": ["string (specific, executable action)"],
      "expected_impact": "string (quantified: e.g., '+20% clicks, ~3% volume decrease' or '$2k monthly savings')",
      "confidence": "string (high|medium|low)",
      "rationale": "string (2-3 sentences with data support)",
      "timeline": "string (e.g., 'immediate', '2 weeks', 'after 15 days', 'end of campaign')"
    }
  ],
  "summary": "string (2-3 paragraph executive summary of campaign health and top 3 priorities)",
  "risks": [
    {
      "risk": "string (e.g., 'Low statistical significance')",
      "mitigation": "string (how to mitigate or validate)"
    }
  ],
  "no_changes_note": "string or null (if campaign is performing well and no changes needed, explain here)"
}

INTERACTION PROTOCOL:
1. Parse the campaign optimization request (campaign_id, name, budget, timeline)
2. Use get_campaign_performance to retrieve current metrics and channel breakdown
3. Use get_benchmark_data for relevant channels to establish baselines
4. Use search_knowledge_base for strategy context and elasticity models
5. Analyze performance vs. benchmarks, identifying gaps and opportunities
6. Generate prioritized recommendations with quantified impact
7. Consider budget and timeline constraints in feasibility
8. Output complete JSON schema - nothing else
9. Do NOT include markdown, commentary, or code blocks outside the JSON"""

    def __init__(
        self,
        db_query_tool: Any,
        vector_search_tool: Any,
        model: str = "claude-sonnet-4-5",
        max_turns: int = 8,
        event_callback: Optional[Any] = None,
    ) -> None:
        """Initialize the OptimizerAgent.

        Args:
            db_query_tool: Instance with get_campaign_performance() method.
            vector_search_tool: Instance with search(query, collection, n_results) method.
            model: Claude model to use.
            max_turns: Maximum agentic loop turns.
            event_callback: Optional callable for streaming execution events.

        Raises:
            ValueError: If tools are not provided or missing required methods.
        """
        super().__init__(model=model, max_turns=max_turns, langfuse_enabled=True, event_callback=event_callback)

        if not db_query_tool:
            raise ValueError("db_query_tool is required")
        if not vector_search_tool:
            raise ValueError("vector_search_tool is required")

        # Verify tools have required methods
        if not hasattr(db_query_tool, "get_campaign_performance"):
            raise ValueError("db_query_tool must have get_campaign_performance() method")
        if not hasattr(vector_search_tool, "search"):
            raise ValueError("vector_search_tool must have search() method")

        self.db_query_tool = db_query_tool
        self.vector_search_tool = vector_search_tool
        self.brand = get_active_brand()

    def get_system_prompt(self) -> str:
        return self._build_system_prompt() + self._SYSTEM_PROMPT_SUFFIX

    def get_tools(self) -> list[dict]:
        """Return the tools available to this agent.

        Returns:
            List of 4 tools in Claude tool_use format with full JSON schemas.
        """
        return [
            {
                "name": "get_campaign_performance",
                "description": (
                    "Retrieve current and historical performance metrics for a campaign. "
                    "Returns aggregate metrics and channel breakdown including impressions, "
                    "clicks, conversions, spend, and revenue."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {
                            "type": "integer",
                            "description": "The ID of the campaign to analyze",
                        },
                        "date_from": {
                            "type": "string",
                            "description": (
                                "Optional: start date in YYYY-MM-DD format. "
                                "If not provided, defaults to campaign start date or last 30 days."
                            ),
                        },
                        "date_to": {
                            "type": "string",
                            "description": (
                                "Optional: end date in YYYY-MM-DD format. "
                                "If not provided, defaults to today."
                            ),
                        },
                    },
                    "required": ["campaign_id"],
                },
            },
            {
                "name": "get_benchmark_data",
                "description": (
                    f"Retrieve performance benchmarks for a specific channel from {self.brand.company_name}'s "
                    "knowledge base and industry standards for comparison and target setting."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "description": (
                                "Channel name (linkedin, email, search, display, content, webinar, partnership)"
                            ),
                        },
                    },
                    "required": ["channel"],
                },
            },
            {
                "name": "search_knowledge_base",
                "description": (
                    "Search the knowledge base for optimization strategies, elasticity models, "
                    "and best practices for campaign optimization."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Search query for strategy and context "
                                "(e.g., 'LinkedIn bid optimization', 'budget allocation strategy', "
                                "'creative refresh best practices', 'email audience expansion')"
                            ),
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-10, default 5)",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "save_recommendation",
                "description": (
                    "Save an optimization recommendation to the database for tracking and execution. "
                    "Use this after generating recommendations to persist them for the campaign team."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {
                            "type": "integer",
                            "description": "The campaign ID this recommendation applies to",
                        },
                        "recommendation_type": {
                            "type": "string",
                            "description": (
                                "Type of recommendation "
                                "(bid_adjustment, budget_reallocation, creative_refresh, "
                                "audience_expansion, channel_pause, scale_up, hold_steady)"
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": "Full description of the recommendation",
                        },
                        "expected_impact": {
                            "type": "string",
                            "description": "Quantified expected impact (e.g., '+15% conversions, -5% CPA')",
                        },
                    },
                    "required": ["campaign_id", "recommendation_type", "description", "expected_impact"],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Execute the specified tool and return results.

        Args:
            tool_name: Name of the tool to execute.
            tool_input: Input dict for the tool.

        Returns:
            Tool output (typically a dict or list).

        Raises:
            ValueError: If tool is unknown or execution fails.
        """
        try:
            if tool_name == "get_campaign_performance":
                campaign_id = tool_input.get("campaign_id")
                date_from = tool_input.get("date_from")
                date_to = tool_input.get("date_to")

                if not campaign_id:
                    raise ValueError("campaign_id is required for get_campaign_performance")

                logger.debug(
                    f"Fetching performance for campaign {campaign_id} "
                    f"from {date_from} to {date_to}"
                )

                performance = self.db_query_tool.get_campaign_performance(
                    campaign_id=campaign_id,
                    date_from=date_from,
                    date_to=date_to,
                )

                return {
                    "campaign_id": campaign_id,
                    "performance": performance or {},
                }

            elif tool_name == "get_benchmark_data":
                channel = tool_input.get("channel")

                if not channel:
                    raise ValueError("channel is required for get_benchmark_data")

                logger.debug(f"Fetching benchmark data for channel: {channel}")

                benchmarks = self.vector_search_tool.search(
                    query=f"{channel} performance benchmarks metrics",
                    collection=f"{self.brand.brand_id}_knowledge_base",
                    n_results=5,
                )

                # Format benchmark results
                formatted_benchmarks = []
                if isinstance(benchmarks, list):
                    for i, bench in enumerate(benchmarks):
                        if isinstance(bench, dict):
                            formatted_benchmarks.append({
                                "id": bench.get("id", f"benchmark_{i}"),
                                "content": bench.get("content", bench.get("text", str(bench))),
                                "metadata": bench.get("metadata", {}),
                            })
                        else:
                            formatted_benchmarks.append({"content": str(bench)})

                return {
                    "channel": channel,
                    "benchmarks": formatted_benchmarks,
                }

            elif tool_name == "search_knowledge_base":
                query = tool_input.get("query")
                n_results = tool_input.get("n_results", 5)

                if not query:
                    raise ValueError("query is required for search_knowledge_base")

                logger.debug(f"Searching knowledge base: {query} (limit: {n_results})")

                results = self.vector_search_tool.search(
                    query=query,
                    collection=f"{self.brand.brand_id}_knowledge_base",
                    n_results=min(n_results, 10),
                )

                # Format results
                formatted_results = []
                if isinstance(results, list):
                    for i, result in enumerate(results):
                        if isinstance(result, dict):
                            formatted_results.append({
                                "id": result.get("id", f"result_{i}"),
                                "content": result.get("content", result.get("text", str(result))),
                                "metadata": result.get("metadata", {}),
                            })
                        else:
                            formatted_results.append({"content": str(result)})

                return {
                    "query": query,
                    "count": len(formatted_results),
                    "results": formatted_results,
                }

            elif tool_name == "save_recommendation":
                campaign_id = tool_input.get("campaign_id")
                recommendation_type = tool_input.get("recommendation_type")
                description = tool_input.get("description")
                expected_impact = tool_input.get("expected_impact")

                if not all([campaign_id, recommendation_type, description, expected_impact]):
                    raise ValueError(
                        "campaign_id, recommendation_type, description, and expected_impact are required"
                    )

                logger.debug(
                    f"Saving recommendation for campaign {campaign_id}: {recommendation_type}"
                )

                # Call DB tool if it has save method
                if hasattr(self.db_query_tool, "save_recommendation"):
                    saved = self.db_query_tool.save_recommendation(
                        campaign_id=campaign_id,
                        recommendation_type=recommendation_type,
                        description=description,
                        expected_impact=expected_impact,
                    )
                    return {
                        "success": True,
                        "recommendation_id": saved.get("id") if isinstance(saved, dict) else None,
                        "message": "Recommendation saved successfully",
                    }
                else:
                    # If save method not available, just return success
                    logger.warning("db_query_tool does not have save_recommendation method; skipping")
                    return {
                        "success": True,
                        "recommendation_id": None,
                        "message": "Recommendation recorded (save not implemented)",
                    }

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {str(e)}")
            raise

    def optimize_campaign(
        self,
        campaign_id: int,
        campaign_name: str,
        remaining_budget_usd: float,
        days_remaining: int,
    ) -> AgentResult:
        """Generate optimization recommendations for a campaign.

        Args:
            campaign_id: The ID of the campaign to optimize.
            campaign_name: Display name of the campaign.
            remaining_budget_usd: Remaining budget available for the campaign.
            days_remaining: Days left in campaign timeline.

        Returns:
            AgentResult with validated optimization recommendations.

        Raises:
            ValueError: If output validation fails.
        """
        # Construct structured user message
        user_message = f"""Analyze and generate optimization recommendations for this campaign:

CAMPAIGN DETAILS:
- Campaign ID: {campaign_id}
- Campaign Name: {campaign_name}
- Remaining Budget: ${remaining_budget_usd:,.0f}
- Days Remaining: {days_remaining}

INSTRUCTIONS:
1. Use get_campaign_performance to retrieve current metrics and channel breakdown
2. For each active channel, use get_benchmark_data to establish performance baselines
3. Use search_knowledge_base to retrieve strategy context and elasticity models
4. Analyze performance vs. benchmarks and identify optimization opportunities
5. Generate prioritized recommendations considering budget and timeline constraints
6. Quantify expected impact for each recommendation (specific numbers, not vague)
7. For each major recommendation, consider using save_recommendation to persist it
8. Output ONLY valid JSON matching the required schema - nothing else

DECISION CRITERIA:
- Only recommend changes with statistical evidence (not noise/randomness)
- Flag anomalies or data quality concerns
- Prioritize by expected ROI impact
- If campaign is performing well, "no changes needed" is a valid output
- Don't recommend major pivots in the last 7 days
- Consider remaining budget and time constraints

REMEMBER:
- Be specific with numbers: "increasing bid 20% should increase clicks 15%" not "increase performance"
- Include timeline: "implement in next 2 days" or "execute after 10 days"
- Flag risks and mitigation strategies
- Compare to benchmarks explicitly
- Only recommend when there's statistical evidence"""

        logger.info(f"Starting campaign optimization for: {campaign_name} (ID: {campaign_id})")
        result = self.run(user_message)

        if result.success:
            # Validate output schema
            try:
                self._validate_output_schema(result.output)
                logger.info("Campaign optimization generated successfully and validated")
            except ValueError as e:
                logger.error(f"Output validation failed: {str(e)}")
                result.success = False
                result.error = f"Output validation failed: {str(e)}"
        else:
            logger.error(f"Campaign optimization failed: {result.error}")

        return result

    def _validate_output_schema(self, output: dict) -> None:
        """Validate that output matches the required schema.

        Args:
            output: The output dict to validate.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = [
            "campaign_id",
            "overall_health",
            "recommendations",
            "summary",
            "risks",
        ]

        missing_fields = [f for f in required_fields if f not in output]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate types
        if not isinstance(output["overall_health"], str):
            raise ValueError("overall_health must be a string")

        allowed_health = ["underperforming", "on_track", "outperforming"]
        if output["overall_health"] not in allowed_health:
            raise ValueError(f"overall_health must be one of {allowed_health}")

        if not isinstance(output["recommendations"], list):
            raise ValueError("recommendations must be a list")

        if not isinstance(output["summary"], str):
            raise ValueError("summary must be a string")

        if not isinstance(output["risks"], list):
            raise ValueError("risks must be a list")

        # Validate recommendation structure
        for i, rec in enumerate(output["recommendations"]):
            if not isinstance(rec, dict):
                raise ValueError(f"Recommendation {i} must be a dict")

            required_rec_fields = [
                "type",
                "priority",
                "description",
                "specific_actions",
                "expected_impact",
                "confidence",
                "rationale",
            ]

            missing_rec_fields = [f for f in required_rec_fields if f not in rec]
            if missing_rec_fields:
                raise ValueError(
                    f"Recommendation {i} missing fields: {missing_rec_fields}"
                )

            # Validate types
            if not isinstance(rec["specific_actions"], list):
                raise ValueError(f"Recommendation {i} specific_actions must be a list")

        # Validate risk structure
        for i, risk in enumerate(output["risks"]):
            if not isinstance(risk, dict):
                raise ValueError(f"Risk {i} must be a dict")

            if "risk" not in risk or "mitigation" not in risk:
                raise ValueError(f"Risk {i} must have 'risk' and 'mitigation' fields")

        logger.debug("Output schema validation passed")


if __name__ == "__main__":
    """Quick smoke test of the OptimizerAgent."""
    import sys

    # Mock tool classes for testing
    class MockDBQueryTool:
        """Mock database query tool."""

        def get_campaign_performance(
            self,
            campaign_id: int,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None,
        ) -> dict:
            """Return mock performance data."""
            return {
                "total_spend_usd": 12500,
                "total_impressions": 450000,
                "total_clicks": 5400,
                "total_conversions": 108,
                "total_revenue_usd": 54000,
                "channels": {
                    "linkedin": {
                        "spend": 5000,
                        "impressions": 150000,
                        "clicks": 2400,
                        "conversions": 60,
                        "revenue": 30000,
                    },
                    "email": {
                        "spend": 2500,
                        "impressions": 85000,
                        "clicks": 1700,
                        "conversions": 34,
                        "revenue": 17000,
                    },
                    "search": {
                        "spend": 5000,
                        "impressions": 215000,
                        "clicks": 1300,
                        "conversions": 14,
                        "revenue": 7000,
                    },
                },
            }

        def save_recommendation(
            self,
            campaign_id: int,
            recommendation_type: str,
            description: str,
            expected_impact: str,
        ) -> dict:
            """Return mock save result."""
            return {"id": "rec_001", "campaign_id": campaign_id}

    class MockVectorSearchTool:
        """Mock vector search tool."""

        def search(self, query: str, collection: str, n_results: int) -> list[dict]:
            """Return mock search results."""
            return [
                {
                    "id": "result_1",
                    "content": f"Benchmark data for: {query}",
                    "metadata": {"source": "industry_benchmarks"},
                },
            ]

    try:
        # Initialize mock tools
        db_query = MockDBQueryTool()
        vector_search = MockVectorSearchTool()

        # Create agent
        agent = OptimizerAgent(
            db_query_tool=db_query,
            vector_search_tool=vector_search,
        )

        # Optimize a campaign
        result = agent.optimize_campaign(
            campaign_id=1,
            campaign_name="Q2 Marketing Automation - VP Operations",
            remaining_budget_usd=7500,
            days_remaining=15,
        )

        # Display results
        try:
            from rich.console import Console
            from rich.panel import Panel

            console = Console()

            if result.success:
                console.print(
                    Panel(
                        json.dumps(result.output, indent=2),
                        title="Optimization Recommendations Output",
                        border_style="green",
                    )
                )
                console.print(
                    f"\n[blue]Tokens:[/blue] {result.total_input_tokens} in / {result.total_output_tokens} out"
                )
                console.print(f"[blue]Latency:[/blue] {result.latency_ms:.0f}ms")
                console.print(f"[blue]Tool calls:[/blue] {len(result.tool_calls_made)}")
                if result.trace_url:
                    console.print(f"[blue]Trace:[/blue] {result.trace_url}")
            else:
                console.print(f"[red]Error:[/red] {result.error}")
                sys.exit(1)

        except ImportError:
            # Fallback if rich not available
            if result.success:
                print("\n=== Optimization Recommendations Output ===")
                print(json.dumps(result.output, indent=2))
                print(f"\nTokens: {result.total_input_tokens} in / {result.total_output_tokens} out")
                print(f"Latency: {result.latency_ms:.0f}ms")
                print(f"Tool calls: {len(result.tool_calls_made)}")
            else:
                print(f"Error: {result.error}")
                sys.exit(1)

    except Exception as e:
        print(f"Fatal error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
