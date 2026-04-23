"""Strategist Agent — generates marketing campaign briefs grounded in brand config."""

import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResult
from brands.config import get_active_brand

logger = logging.getLogger(__name__)


class StrategistAgent(BaseAgent):
    """Expert B2B marketing strategist agent for generating campaign briefs.

    Uses a multi-turn agentic approach to:
    1. Search knowledge base for brand guidelines and persona information
    2. Retrieve benchmark data for recommended channels
    3. Generate strategic recommendations with budget allocations
    4. Provide data-driven rationale grounded in retrieved context

    Attributes:
        vector_search_tool: Tool instance for searching ChromaDB knowledge base.
        db_query_tool: Tool instance for querying campaign history and benchmarks.
    """

    _SYSTEM_PROMPT_SUFFIX = """
OUTPUT SCHEMA (MANDATORY JSON FORMAT):
{
  "recommended_channels": [
    {
      "channel": "string (e.g., 'Facebook Ads')",
      "rationale": "string (why this channel for this segment)",
      "timeline_to_first_results_days": number,
      "confidence_percent": number (0-100)
    }
  ],
  "budget_split": {
    "channel_name": number (USD, must sum to budget)
  },
  "primary_message_pillar": "string (core campaign message)",
  "secondary_message_pillar": "string (supporting message)",
  "target_audience_description": "string (refined description based on personas)",
  "kpis": [
    {
      "metric": "string",
      "target": "string or number",
      "rationale": "string"
    }
  ],
  "suggested_timeline": {
    "phase_1_days": number,
    "phase_2_days": number,
    "phase_3_days": number,
    "phase_names": ["Launch", "Optimize", "Scale"]
  },
  "rationale": "string (2-3 paragraph executive summary grounding strategy in data)",
  "risks": [
    {
      "risk": "string",
      "mitigation": "string"
    }
  ]
}

INTERACTION PROTOCOL:
1. Parse the campaign brief request (goal, budget, timeline, segment)
2. Search knowledge base for brand & persona context
3. For each candidate channel, retrieve benchmarks
4. Synthesize recommendations with budget allocation
5. Output complete JSON schema - nothing else
6. Do NOT include markdown, commentary, or explanations outside the JSON"""

    _SYSTEM_PROMPT_TEMPLATE = """You are an expert B2B marketing strategist for {company_name}, {business_model}.

Your role is to generate comprehensive, data-driven marketing campaign briefs that balance strategic ambition with practical budget constraints. You have deep expertise in:
- Marketing channel strategy (SMB acquisition, re-engagement, upsell)
- Marketing mix optimization and budget allocation
- Target audience segmentation and persona-based messaging
- Campaign measurement and KPI definition
- Marketing technology and MarTech stack alignment

BRAND CONTEXT:
- Company: {company_name}
- What you're marketing: {product_being_marketed}
- Target customer: {target_customer_description}
- Campaign context: {campaign_context}
- Brand voice: {brand_voice_summary}

CRITICAL OPERATING PRINCIPLES:
1. ALWAYS use search_knowledge_base BEFORE making ANY recommendations to retrieve:
   - {company_name} brand guidelines, voice, and positioning
   - Target segment personas and their preferred channels
   - Past campaign messaging themes
2. ALWAYS use get_benchmark_data for EACH recommended channel to ground recommendations in:
   - Industry benchmarks (CTR, conversion rates, CAC)
   - Historical {company_name} performance by channel
   - Realistic timelines for first results
3. Ground ALL recommendations in retrieved context with specific data points
4. Be realistic about budget constraints: minimum $500/month/channel to be effective (otherwise consolidate)
5. Consider target segment's actual channel preferences from personas
6. NEVER use these phrases: {prohibited_phrases}
7. Output ONLY valid JSON matching the schema below - no prose outside the JSON"""

    def __init__(
        self,
        vector_search_tool: Any,
        db_query_tool: Any,
        model: str = "claude-sonnet-4-5",
        max_turns: int = 8,
        event_callback=None,
    ) -> None:
        """Initialize the StrategistAgent.

        Args:
            vector_search_tool: Instance with search(query, collection, n_results) method.
            db_query_tool: Instance with get_campaign_history() and get_performance_metrics() methods.
            model: Claude model to use.
            max_turns: Maximum agentic loop turns.

        Raises:
            ValueError: If tools are not provided or missing required methods.
        """
        super().__init__(model=model, max_turns=max_turns, langfuse_enabled=True, event_callback=event_callback)

        if not vector_search_tool:
            raise ValueError("vector_search_tool is required")
        if not db_query_tool:
            raise ValueError("db_query_tool is required")

        # Verify tools have required methods
        if not hasattr(vector_search_tool, "search"):
            raise ValueError("vector_search_tool must have search() method")
        if not hasattr(db_query_tool, "get_campaign_history"):
            raise ValueError("db_query_tool must have get_campaign_history() method")
        if not hasattr(db_query_tool, "get_performance_metrics"):
            raise ValueError("db_query_tool must have get_performance_metrics() method")

        self.vector_search_tool = vector_search_tool
        self.db_query_tool = db_query_tool
        self.brand = get_active_brand()

    def get_system_prompt(self) -> str:
        brand = self.brand
        return self._SYSTEM_PROMPT_TEMPLATE.format(
            company_name=brand.company_name,
            business_model=brand.business_model,
            product_being_marketed=brand.product_being_marketed,
            target_customer_description=brand.target_customer_description,
            campaign_context=brand.campaign_context,
            brand_voice_summary=brand.brand_voice_summary,
            prohibited_phrases=", ".join(brand.prohibited_phrases[:10]),
        ) + self._SYSTEM_PROMPT_SUFFIX

    def get_tools(self) -> list[dict]:
        """Return the tools available to this agent.

        Returns:
            List of 3 tools in Claude tool_use format with full JSON schemas.
        """
        return [
            {
                "name": "search_knowledge_base",
                "description": (
                    f"Search the {self.brand.company_name} knowledge base for brand guidelines, "
                    "persona information, messaging frameworks, and past campaign context. "
                    "Use this to ground recommendations in company-specific information."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Search query for the knowledge base "
                                "(e.g., 'VP of Operations persona', 'enterprise messaging', 'brand voice guidelines')"
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
                "name": "get_campaign_history",
                "description": (
                    "Retrieve historical campaign data for a specific segment and/or channel. "
                    "Use this to understand what has worked before and inform recommendations."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "segment": {
                            "type": "string",
                            "description": "Target segment name (e.g., 'VP of Operations')",
                        },
                        "channel": {
                            "type": "string",
                            "description": (
                                "Optional: specific channel to filter by "
                                "(e.g., 'LinkedIn Ads', 'Email', 'Content')"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of campaigns to return (default 10)",
                            "default": 10,
                        },
                    },
                    "required": ["segment"],
                },
            },
            {
                "name": "get_benchmark_data",
                "description": (
                    "Retrieve performance benchmarks and metrics for a specific channel. "
                    "Use this to validate channel recommendations and set realistic KPI targets."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "description": (
                                "Channel name (e.g., 'LinkedIn Ads', 'Email', 'Content Marketing', "
                                "'Paid Search', 'Webinars', 'Partnerships')"
                            ),
                        },
                    },
                    "required": ["channel"],
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
            if tool_name == "search_knowledge_base":
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

                # Format results for readability
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

            elif tool_name == "get_campaign_history":
                segment = tool_input.get("segment")
                channel = tool_input.get("channel")
                limit = tool_input.get("limit", 10)

                if not segment:
                    raise ValueError("segment is required for get_campaign_history")

                logger.debug(f"Fetching campaign history: segment={segment}, channel={channel}, limit={limit}")
                campaigns = self.db_query_tool.get_campaign_history(
                    segment=segment,
                    channel=channel,
                    limit=limit,
                )

                return {
                    "segment": segment,
                    "channel": channel,
                    "count": len(campaigns) if campaigns else 0,
                    "campaigns": campaigns or [],
                }

            elif tool_name == "get_benchmark_data":
                channel = tool_input.get("channel")

                if not channel:
                    raise ValueError("channel is required for get_benchmark_data")

                logger.debug(f"Fetching benchmark data for channel: {channel}")
                benchmarks = self.db_query_tool.get_performance_metrics(
                    channel=channel,
                )

                return {
                    "channel": channel,
                    "benchmarks": benchmarks or {},
                }

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {str(e)}")
            raise

    def run_campaign_brief(
        self,
        campaign_goal: str,
        budget_usd: float,
        timeline_days: int,
        target_segment: str,
    ) -> AgentResult:
        """Generate a marketing campaign brief.

        Args:
            campaign_goal: The campaign objective (e.g., "Generate 30 MQLs for Lumen Pro").
            budget_usd: Total budget in USD.
            timeline_days: Campaign duration in days.
            target_segment: Target audience segment description.

        Returns:
            AgentResult with validated campaign brief output.

        Raises:
            ValueError: If output validation fails.
        """
        # Construct structured user message
        user_message = f"""Generate a comprehensive marketing campaign brief with the following parameters:

CAMPAIGN PARAMETERS:
- Goal: {campaign_goal}
- Total Budget: ${budget_usd:,.0f} USD
- Timeline: {timeline_days} days
- Target Segment: {target_segment}

INSTRUCTIONS:
1. Use search_knowledge_base to retrieve brand guidelines and {target_segment} persona information
2. For each recommended channel, use get_benchmark_data to retrieve performance metrics
3. Use get_campaign_history to understand what has worked for this segment
4. Generate strategic recommendations grounded in retrieved data
5. Output ONLY valid JSON matching the required schema - nothing else

Remember: Minimum $500/month per channel to be effective. Consolidate budget across fewer channels if needed."""

        logger.info(f"Starting campaign brief generation for: {campaign_goal}")
        result = self.run(user_message)

        if result.success:
            # Validate output schema
            try:
                self._validate_output_schema(result.output)
                logger.info("Campaign brief generated successfully and validated")
            except ValueError as e:
                logger.error(f"Output validation failed: {str(e)}")
                result.success = False
                result.error = f"Output validation failed: {str(e)}"
        else:
            logger.error(f"Campaign brief generation failed: {result.error}")

        return result

    def _validate_output_schema(self, output: dict) -> None:
        """Validate that output matches the required schema.

        Args:
            output: The output dict to validate.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = [
            "recommended_channels",
            "budget_split",
            "primary_message_pillar",
            "secondary_message_pillar",
            "target_audience_description",
            "kpis",
            "suggested_timeline",
            "rationale",
            "risks",
        ]

        missing_fields = [f for f in required_fields if f not in output]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate types
        if not isinstance(output["recommended_channels"], list):
            raise ValueError("recommended_channels must be a list")

        if not isinstance(output["budget_split"], dict):
            raise ValueError("budget_split must be a dict")

        if not isinstance(output["kpis"], list):
            raise ValueError("kpis must be a list")

        if not isinstance(output["risks"], list):
            raise ValueError("risks must be a list")

        if not isinstance(output["suggested_timeline"], dict):
            raise ValueError("suggested_timeline must be a dict")

        # Validate budget_split sums to reasonable amount
        if output["budget_split"]:
            total_budget = sum(v for v in output["budget_split"].values() if isinstance(v, (int, float)))
            if total_budget <= 0:
                raise ValueError("budget_split total must be positive")

        logger.debug("Output schema validation passed")


if __name__ == "__main__":
    """Quick smoke test of the StrategistAgent."""
    import sys

    # Mock tool classes for testing
    class MockVectorSearchTool:
        """Mock vector search tool."""

        def search(self, query: str, collection: str, n_results: int) -> list[dict]:
            """Return mock search results."""
            return [
                {
                    "id": "result_1",
                    "content": f"Mock result for query: {query}",
                    "metadata": {"relevance": 0.95},
                },
            ]

    class MockDBQueryTool:
        """Mock database query tool."""

        def get_campaign_history(
            self,
            segment: str,
            channel: Optional[str] = None,
            limit: int = 10,
        ) -> list[dict]:
            """Return mock campaign history."""
            return [
                {
                    "campaign_id": "camp_001",
                    "segment": segment,
                    "channel": channel or "All",
                    "mql_generated": 25,
                    "spend": 5000,
                    "cpm": 45,
                },
            ]

        def get_performance_metrics(self, channel: str, **kwargs) -> dict:
            """Return mock performance benchmarks."""
            benchmarks = {
                "LinkedIn Ads": {
                    "avg_ctr": 0.045,
                    "avg_conversion_rate": 0.021,
                    "avg_cpc": 2.50,
                    "timeline_to_first_results_days": 5,
                },
                "Email": {
                    "avg_open_rate": 0.28,
                    "avg_ctr": 0.032,
                    "avg_conversion_rate": 0.015,
                    "timeline_to_first_results_days": 1,
                },
                "Content Marketing": {
                    "avg_organic_traffic_growth_monthly": 0.15,
                    "avg_conversion_rate": 0.008,
                    "timeline_to_first_results_days": 30,
                },
            }
            return benchmarks.get(channel, {})

    try:
        # Initialize mock tools
        vector_search = MockVectorSearchTool()
        db_query = MockDBQueryTool()

        # Create agent
        agent = StrategistAgent(
            vector_search_tool=vector_search,
            db_query_tool=db_query,
        )

        # Run campaign brief
        result = agent.run_campaign_brief(
            campaign_goal="Generate 30 MQLs for Lumen Pro targeting mid-market ops managers in Q2",
            budget_usd=20000,
            timeline_days=45,
            target_segment="VP of Operations at 100-500 person B2B companies",
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
                        title="Campaign Brief Output",
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
                print("\n=== Campaign Brief Output ===")
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
