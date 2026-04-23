"""Analyst Agent — answers marketing analytics questions by generating and executing SQL."""

import json
import logging
import re
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResult
from brands.config import get_active_brand

logger = logging.getLogger(__name__)


class AnalystAgent(BaseAgent):
    """Expert marketing data analyst agent for CampaignPilot.

    Uses a multi-turn agentic approach to:
    1. Retrieve schema information for available tables
    2. Generate valid SQL queries for the user's question
    3. Execute SQL against the database
    4. Interpret results with business context from knowledge base
    5. Flag anomalies and provide recommendations

    Attributes:
        db_query_tool: Tool instance for executing SQL queries.
        vector_search_tool: Tool instance for searching knowledge base.
    """

    def _build_system_prompt(self) -> str:
        brand = self.brand
        return f"""You are a senior marketing data analyst for {brand.company_name}.

Your role is to answer marketing analytics questions by generating SQL queries, executing them against the CampaignPilot database, and providing business insights grounded in {brand.company_name} benchmarks. You have deep expertise in:
- Marketing analytics and attribution modeling
- SQL query writing and database design
- Campaign performance metrics and KPIs
- Trend analysis and anomaly detection
- Statistical reasoning and data quality assessment
- Marketing benchmarks and best practices

CRITICAL OPERATING PRINCIPLES:
1. ALWAYS generate and validate SQL BEFORE executing any queries
2. ONLY query these tables:
   - campaigns: Campaign master data (id, name, goal, target_segment, budget_usd, start_date, end_date, status, channels)
   - campaign_briefs: Strategic brief data linked to campaigns
   - creatives: Ad creative variants and performance metadata
   - performance_events: Daily performance metrics (impressions, clicks, conversions, spend, revenue by channel/date)
   - optimization_recommendations: AI-generated recommendations from optimizer agent
   - eval_runs: Model evaluation runs and quality scores
3. Never make up numbers — ONLY report what the data actually shows
4. For numerical answers, always show the SQL that produced the result
5. Add business interpretation beyond raw numbers:
   - What does this metric mean for campaign success?
   - How does it compare to benchmarks or historical performance?
   - What patterns or trends do you observe?
6. Flag anomalies that suggest data quality issues:
   - ROAS > 10x is suspicious (data entry error likely)
   - Conversion rates > 10% are unusual for B2B (validate)
   - Negative spend or revenue indicates data issues
   - Missing data for significant date ranges
7. Provide context from company benchmarks when relevant
8. Output structured JSON with SQL, results, and narrative insight
9. Do NOT include markdown code blocks - output ONLY valid JSON
"""

    _SYSTEM_PROMPT_SUFFIX = """
OUTPUT SCHEMA (MANDATORY JSON FORMAT):
{
  "question": "string (the original question asked)",
  "sql": "string (the SQL query that was executed)",
  "results": [... array of result rows, each a dict],
  "result_count": number,
  "narrative_insight": "string (2-3 paragraph business interpretation)",
  "key_finding": "string (1-2 sentence headline finding)",
  "recommended_action": "string (what to do based on this data, if applicable)",
  "data_quality_notes": "string (any data quality issues or limitations)",
  "query_notes": "string (notes on how the query was structured to answer the question)"
}

INTERACTION PROTOCOL:
1. Parse the user's analytics question
2. Use get_schema_info if needed to understand available fields
3. Use search_knowledge_base for benchmark context if relevant
4. Generate a SQL query that directly answers the question
5. Validate SQL uses only allowed tables and is syntactically correct
6. Execute the SQL via execute_sql tool
7. Interpret results with business context
8. Output complete JSON schema - nothing else
9. Do NOT include markdown, commentary, or code blocks outside the JSON"""

    # Hardcoded schema for the database
    SCHEMA = {
        "campaigns": {
            "columns": [
                "id",
                "name",
                "goal",
                "target_segment",
                "budget_usd",
                "start_date",
                "end_date",
                "status",
                "channels",
            ],
            "description": "Master table of marketing campaigns with metadata, budget allocation, and status.",
        },
        "campaign_briefs": {
            "columns": [
                "id",
                "campaign_id",
                "recommended_channels",
                "budget_split",
                "primary_message_pillar",
                "secondary_message_pillar",
                "target_audience_description",
                "kpis",
                "suggested_timeline",
                "rationale",
                "risks",
                "created_at",
            ],
            "description": "Strategic briefs generated by the Strategist agent, linked to campaigns.",
        },
        "creatives": {
            "columns": [
                "id",
                "campaign_id",
                "variant_index",
                "headline",
                "body",
                "cta",
                "tone",
                "key_differentiator",
                "channel",
                "product",
                "persona",
                "safety_check_passed",
                "created_at",
            ],
            "description": "Ad creative variants generated by the Creative agent with performance metadata.",
        },
        "performance_events": {
            "columns": [
                "id",
                "campaign_id",
                "event_date",
                "channel",
                "impressions",
                "clicks",
                "conversions",
                "spend_usd",
                "revenue_usd",
            ],
            "description": "Daily performance metrics by campaign and channel (impressions, clicks, conversions, spend, revenue).",
        },
        "optimization_recommendations": {
            "columns": [
                "id",
                "campaign_id",
                "recommendation_type",
                "description",
                "expected_impact",
                "priority",
                "created_at",
            ],
            "description": "Optimization recommendations generated by the Optimizer agent with expected impact estimates.",
        },
        "eval_runs": {
            "columns": [
                "id",
                "campaign_id",
                "eval_date",
                "quality_score",
                "recommendations_count",
                "data_completeness_percent",
            ],
            "description": "Model evaluation runs tracking data quality and recommendation accuracy.",
        },
    }

    def __init__(
        self,
        db_query_tool: Any,
        vector_search_tool: Any,
        model: str = "claude-sonnet-4-5",
        max_turns: int = 6,
        event_callback: Optional[Any] = None,
    ) -> None:
        """Initialize the AnalystAgent.

        Args:
            db_query_tool: Instance with execute_query(sql: str) method.
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
        if not hasattr(db_query_tool, "execute_query"):
            raise ValueError("db_query_tool must have execute_query() method")
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
            List of 3 tools in Claude tool_use format with full JSON schemas.
        """
        return [
            {
                "name": "execute_sql",
                "description": (
                    "Execute a SQL SELECT query against the CampaignPilot database. "
                    "Only SELECT statements are allowed. Returns rows as a list of dicts. "
                    "Always validate query uses only allowed tables: campaigns, campaign_briefs, "
                    "creatives, performance_events, optimization_recommendations, eval_runs."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": (
                                "SQL SELECT query to execute. Must use only allowed tables. "
                                "Example: SELECT campaign_id, SUM(spend_usd) as total_spend FROM performance_events GROUP BY campaign_id"
                            ),
                        },
                    },
                    "required": ["sql"],
                },
            },
            {
                "name": "get_schema_info",
                "description": (
                    "Get schema information for database tables. "
                    "Returns column names, types, and table descriptions. "
                    "Optionally filter by table name."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": (
                                "Optional: specific table name to get schema for "
                                "(campaigns, campaign_briefs, creatives, performance_events, "
                                "optimization_recommendations, eval_runs). "
                                "Omit to get all schemas."
                            ),
                        },
                    },
                    "required": [],
                },
            },
            {
                "name": "search_knowledge_base",
                "description": (
                    "Search the knowledge base for benchmark context, best practices, "
                    "and historical campaign context. Use this to interpret results "
                    "and provide business insights."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Search query for benchmarks and context "
                                "(e.g., 'email campaign benchmarks', 'LinkedIn CTR benchmarks', "
                                "'B2B conversion rate benchmarks')"
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
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Execute the specified tool and return results.

        Args:
            tool_name: Name of the tool to execute.
            tool_input: Input dict for the tool.

        Returns:
            Tool output (typically a dict or list).

        Raises:
            ValueError: If tool is unknown, validation fails, or execution fails.
        """
        try:
            if tool_name == "execute_sql":
                sql = tool_input.get("sql", "").strip()

                if not sql:
                    raise ValueError("sql is required for execute_sql")

                # Validate SQL: must be SELECT only
                if not sql.upper().startswith("SELECT"):
                    raise ValueError("Only SELECT queries are allowed")

                # Validate allowed tables
                allowed_tables = [
                    "campaigns",
                    "campaign_briefs",
                    "creatives",
                    "performance_events",
                    "optimization_recommendations",
                    "eval_runs",
                ]

                sql_upper = sql.upper()
                for table in allowed_tables:
                    if table.upper() in sql_upper:
                        break
                else:
                    raise ValueError(
                        f"Query must reference at least one allowed table: {', '.join(allowed_tables)}"
                    )

                # Additional validation: check for dangerous keywords
                dangerous_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE"]
                for keyword in dangerous_keywords:
                    if keyword in sql_upper:
                        raise ValueError(f"Keyword '{keyword}' is not allowed")

                logger.debug(f"Executing SQL: {sql[:100]}...")

                # Execute via tool
                try:
                    result = self.db_query_tool.execute_query(sql)
                    if isinstance(result, dict) and "rows" in result:
                        rows = result["rows"]
                        row_count = len(rows) if isinstance(rows, list) else 0
                        error = result.get("error")
                    else:
                        rows = result if isinstance(result, list) else []
                        row_count = len(rows)
                        error = None
                except Exception as e:
                    logger.error(f"Database query error: {str(e)}")
                    return {
                        "rows": [],
                        "row_count": 0,
                        "error": str(e),
                    }

                return {
                    "rows": rows,
                    "row_count": row_count,
                    "error": error,
                }

            elif tool_name == "get_schema_info":
                table_name = tool_input.get("table_name")

                if table_name:
                    # Return specific table schema
                    if table_name not in self.SCHEMA:
                        raise ValueError(f"Unknown table: {table_name}")

                    schema = self.SCHEMA[table_name]
                    return {
                        "table": table_name,
                        "columns": schema["columns"],
                        "description": schema["description"],
                    }
                else:
                    # Return all schemas
                    return {
                        "tables": {
                            name: {
                                "columns": schema["columns"],
                                "description": schema["description"],
                            }
                            for name, schema in self.SCHEMA.items()
                        },
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

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {str(e)}")
            raise

    def answer_question(self, question: str) -> AgentResult:
        """Answer a marketing analytics question by generating and executing SQL.

        Args:
            question: The analytics question to answer.

        Returns:
            AgentResult with validated analytics output containing SQL, results, and insights.

        Raises:
            ValueError: If output validation fails.
        """
        # Construct user message
        user_message = f"""Answer this marketing analytics question for CampaignPilot:

QUESTION: {question}

INSTRUCTIONS:
1. Use get_schema_info if needed to understand available tables and columns
2. Generate a SQL query that directly answers the question
3. Validate the SQL only uses SELECT and references allowed tables
4. Execute the SQL via execute_sql tool
5. Use search_knowledge_base if you need benchmark context for interpretation
6. Interpret the results with business insights beyond raw numbers
7. Flag any data quality issues or anomalies you notice
8. Output ONLY valid JSON matching the required schema - nothing else

REMEMBER:
- Never make up numbers - only report what the data shows
- Always show the SQL query used to generate results
- Add business context and interpretation
- Flag suspicious metrics (ROAS > 10x, conversion rates > 10%, etc.)
- Only query allowed tables: campaigns, campaign_briefs, creatives, performance_events, optimization_recommendations, eval_runs"""

        logger.info(f"Starting analytics question answering: {question[:80]}...")
        result = self.run(user_message)

        if result.success:
            # Validate output schema
            try:
                self._validate_output_schema(result.output)
                logger.info("Analytics answer generated successfully and validated")
            except ValueError as e:
                logger.error(f"Output validation failed: {str(e)}")
                result.success = False
                result.error = f"Output validation failed: {str(e)}"
        else:
            logger.error(f"Analytics question answering failed: {result.error}")

        return result

    def _validate_output_schema(self, output: dict) -> None:
        """Validate that output matches the required schema.

        Args:
            output: The output dict to validate.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = [
            "question",
            "sql",
            "results",
            "narrative_insight",
            "key_finding",
        ]

        missing_fields = [f for f in required_fields if f not in output]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate types
        if not isinstance(output["sql"], str):
            raise ValueError("sql must be a string")

        if not isinstance(output["results"], list):
            raise ValueError("results must be a list")

        if not isinstance(output["narrative_insight"], str):
            raise ValueError("narrative_insight must be a string")

        if not isinstance(output["key_finding"], str):
            raise ValueError("key_finding must be a string")

        # Validate SQL is a SELECT statement
        if not output["sql"].upper().startswith("SELECT"):
            raise ValueError("sql must be a SELECT statement")

        logger.debug("Output schema validation passed")


if __name__ == "__main__":
    """Quick smoke test of the AnalystAgent."""
    import sys

    # Mock tool classes for testing
    class MockDBQueryTool:
        """Mock database query tool."""

        def execute_query(self, sql: str) -> dict:
            """Return mock query results."""
            return {
                "rows": [
                    {"campaign_id": 1, "total_spend": 5000, "conversions": 150},
                    {"campaign_id": 2, "total_spend": 3500, "conversions": 95},
                ],
                "error": None,
            }

    class MockVectorSearchTool:
        """Mock vector search tool."""

        def search(self, query: str, collection: str, n_results: int) -> list[dict]:
            """Return mock search results."""
            return [
                {
                    "id": "benchmark_1",
                    "content": "B2B average conversion rate is 2-3% for email campaigns",
                    "metadata": {"source": "industry_benchmarks"},
                },
            ]

    try:
        # Initialize mock tools
        db_query = MockDBQueryTool()
        vector_search = MockVectorSearchTool()

        # Create agent
        agent = AnalystAgent(
            db_query_tool=db_query,
            vector_search_tool=vector_search,
        )

        # Ask a question
        result = agent.answer_question(
            "What is the total spend and conversion count for each campaign?"
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
                        title="Analytics Answer Output",
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
                print("\n=== Analytics Answer Output ===")
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
