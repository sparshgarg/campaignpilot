"""Creative Agent — generates brand-safe ad copy grounded in brand config."""

import json
import logging
from typing import Any, Optional

from agents.base_agent import BaseAgent, AgentResult
from brands.config import get_active_brand

logger = logging.getLogger(__name__)


class CreativeAgent(BaseAgent):
    """Expert copywriter agent for generating Lumen Analytics ad creative.

    Uses a multi-turn agentic approach to:
    1. Search knowledge base for brand guidelines and best practices
    2. Retrieve past creative examples to understand successful patterns
    3. Generate multiple creative variants adapted to channel and tone
    4. Validate output against brand safety guidelines

    Attributes:
        vector_search_tool: Tool instance for searching ChromaDB knowledge base.
        safety_checker_tool: Tool instance for brand safety validation.
    """

    def _build_system_prompt(self) -> str:
        brand = self.brand
        prohibited = ", ".join(brand.prohibited_phrases[:12])
        products_str = ", ".join(p.get("name", "") for p in brand.products[:4])
        return f"""You are a senior copywriter for {brand.company_name}.

Your role is to generate compelling, brand-safe ad copy that drives SMB advertisers to adopt {brand.product_being_marketed}. You have deep expertise in:
- SMB-focused copywriting across Facebook, Instagram, email, and search
- Channel-specific tone and format requirements
- Outcome-focused messaging that resonates with small business owners
- Brand voice consistency: {brand.brand_voice_summary}

CRITICAL OPERATING PRINCIPLES:
1. ALWAYS use search_knowledge_base BEFORE writing ANY copy to retrieve:
   - {brand.company_name} brand guidelines, voice, and positioning
   - Target persona information and pain points
   - Approved messaging frameworks and proof points
2. ALWAYS use search_creative_examples to find successful copy patterns for your channel and tone
3. Products to feature when relevant: {products_str}
4. Lead with OUTCOMES, not features:
   - "More customers walking through your door" not "Advanced ad targeting"
   - "Grow sales with your budget" not "Advertising platform"
5. Adapt tone to channel:
   - Facebook/Instagram: Warm, direct, benefit-forward for SMB owners
   - Email: Conversational, outcome-focused
   - Search: Punchy, action-oriented
6. NEVER use these prohibited phrases: {prohibited}
7. Prioritize credibility signals: specific numbers, real business outcomes, practical benefits
8. Output ONLY valid JSON matching the schema below - no prose outside the JSON

OUTPUT SCHEMA (MANDATORY JSON FORMAT):
{{
  "variants": [
    {{
      "variant_index": number,
      "headline": "string (40-80 characters, benefit-focused)",
      "body": "string (2-4 sentences for social/email, 1 sentence for search)",
      "cta": "string (action-oriented call-to-action)",
      "tone": "string (professional, conversational, punchy, etc.)",
      "key_differentiator": "string (what makes this unique/compelling)",
      "channel_optimized_for": "string (facebook|instagram|email|search)",
      "safety_check": {{
        "passed": boolean,
        "violations": [] or ["violation description"]
      }}
    }}
  ],
  "channel": "string (facebook|instagram|email|search)",
  "product": "string (product name)",
  "persona": "string (target persona)",
  "tone": "string (overall tone)",
  "creative_strategy": "string (approach and rationale for these variants)",
  "rationale": "string (why these variants work based on successful patterns and persona insights)"
}}

INTERACTION PROTOCOL:
1. Parse creative brief (channel, product, persona, tone, key_message, num_variants)
2. Search knowledge base for brand guidelines and persona information
3. Search creative examples for successful patterns in this channel/tone
4. Generate N creative variants, each with a different angle/positioning
5. Check each variant for brand safety
6. Output complete JSON schema - nothing else"""

    def __init__(
        self,
        vector_search_tool: Any,
        safety_checker_tool: Any,
        model: str = "claude-sonnet-4-5",
        max_turns: int = 6,
        event_callback: Optional[Any] = None,
    ) -> None:
        """Initialize the CreativeAgent.

        Args:
            vector_search_tool: Instance with search(query, collection, n_results) method.
            safety_checker_tool: Instance with check_brand_safety(text) method.
            model: Claude model to use.
            max_turns: Maximum agentic loop turns.
            event_callback: Optional callable for streaming execution events.

        Raises:
            ValueError: If tools are not provided or missing required methods.
        """
        super().__init__(model=model, max_turns=max_turns, langfuse_enabled=True, event_callback=event_callback)

        if not vector_search_tool:
            raise ValueError("vector_search_tool is required")
        if not safety_checker_tool:
            raise ValueError("safety_checker_tool is required")

        # Verify tools have required methods
        if not hasattr(vector_search_tool, "search"):
            raise ValueError("vector_search_tool must have search() method")
        if not hasattr(safety_checker_tool, "check_brand_safety"):
            raise ValueError("safety_checker_tool must have check_brand_safety() method")

        self.vector_search_tool = vector_search_tool
        self.safety_checker_tool = safety_checker_tool
        self.brand = get_active_brand()

    def get_system_prompt(self) -> str:
        return self._build_system_prompt()

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
                    "messaging frameworks, persona information, and proof points. "
                    "Use this to understand brand voice, approved messaging, and target audience."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Search query for the knowledge base "
                                "(e.g., 'brand voice and tone', 'VP of Marketing persona', "
                                "'Lumen proof points', 'email messaging examples')"
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
                "name": "search_creative_examples",
                "description": (
                    "Search past creative examples for a specific channel and tone. "
                    "Use this to understand successful copy patterns and messaging approaches."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "channel": {
                            "type": "string",
                            "description": (
                                "Channel for examples (linkedin, email, search, display)"
                            ),
                        },
                        "tone": {
                            "type": "string",
                            "description": (
                                "Tone or style (professional, conversational, punchy, educational, etc.)"
                            ),
                        },
                        "n_results": {
                            "type": "integer",
                            "description": "Number of results to return (1-10, default 5)",
                            "default": 5,
                        },
                    },
                    "required": ["channel", "tone"],
                },
            },
            {
                "name": "check_brand_safety",
                "description": (
                    f"Validate copy against {self.brand.company_name} brand guidelines. "
                    "Checks for prohibited phrases, brand voice violations, and messaging consistency."
                ),
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The ad copy text to validate (headline, body, or CTA)",
                        },
                    },
                    "required": ["text"],
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

            elif tool_name == "search_creative_examples":
                channel = tool_input.get("channel")
                tone = tool_input.get("tone")
                n_results = tool_input.get("n_results", 5)

                if not channel or not tone:
                    raise ValueError("channel and tone are required for search_creative_examples")

                logger.debug(f"Searching creative examples: channel={channel}, tone={tone}, limit={n_results}")
                results = self.vector_search_tool.search(
                    query=f"{channel} {tone} creative examples",
                    collection="creative_examples",
                    n_results=min(n_results, 10),
                )

                # Format results for readability
                formatted_results = []
                if isinstance(results, list):
                    for i, result in enumerate(results):
                        if isinstance(result, dict):
                            formatted_results.append({
                                "id": result.get("id", f"example_{i}"),
                                "headline": result.get("headline", ""),
                                "body": result.get("body", ""),
                                "cta": result.get("cta", ""),
                                "metadata": result.get("metadata", {}),
                            })
                        else:
                            formatted_results.append({"content": str(result)})

                return {
                    "channel": channel,
                    "tone": tone,
                    "count": len(formatted_results),
                    "examples": formatted_results,
                }

            elif tool_name == "check_brand_safety":
                text = tool_input.get("text")

                if not text:
                    raise ValueError("text is required for check_brand_safety")

                logger.debug(f"Checking brand safety for text: {text[:100]}...")
                safety_result = self.safety_checker_tool.check_brand_safety(text)

                # Ensure result is a dict with 'passed' and 'violations' keys
                if isinstance(safety_result, dict):
                    return {
                        "passed": safety_result.get("passed", True),
                        "violations": safety_result.get("violations", []),
                    }
                else:
                    # If tool returns boolean, convert to dict
                    return {
                        "passed": bool(safety_result),
                        "violations": [],
                    }

            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {str(e)}")
            raise

    def run_creative_brief(
        self,
        channel: str,
        product: str,
        persona: str,
        tone: str,
        key_message: str,
        num_variants: int = 3,
    ) -> AgentResult:
        """Generate creative variants for a marketing campaign.

        Args:
            channel: Channel (linkedin, email, search, display).
            product: Product name (e.g., "Lumen Pro").
            persona: Target persona description.
            tone: Desired tone (professional, conversational, punchy, etc.).
            key_message: Primary message or value prop to highlight.
            num_variants: Number of creative variants to generate (default 3).

        Returns:
            AgentResult with validated creative output.

        Raises:
            ValueError: If output validation fails.
        """
        # Construct structured user message
        user_message = f"""Generate {num_variants} creative variants for a Lumen Analytics campaign with these specifications:

CREATIVE BRIEF:
- Channel: {channel}
- Product: {product}
- Target Persona: {persona}
- Tone: {tone}
- Key Message: {key_message}
- Number of Variants: {num_variants}

INSTRUCTIONS:
1. Use search_knowledge_base to retrieve brand guidelines, {product} positioning, and {persona} persona information
2. Use search_creative_examples to find successful {channel} creative examples with {tone} tone
3. Generate {num_variants} distinct creative variants, each with a different angle/positioning
4. Use check_brand_safety on each variant's headline and body before finalizing
5. Output ONLY valid JSON matching the required schema - nothing else

REQUIREMENTS:
- Each variant must have a unique angle or value prop emphasis
- Headlines should be 40-80 characters and benefit-focused
- Avoid all prohibited phrases (game-changing, revolutionary, world-class, etc.)
- Include specific Lumen proof points when relevant (60% faster reporting, 3400+ customers, etc.)
- Lead with OUTCOMES, not features
- Ensure all variants pass brand safety checks"""

        logger.info(f"Starting creative generation for: {channel} - {product}")
        result = self.run(user_message)

        if result.success:
            # Validate output schema
            try:
                self._validate_output_schema(result.output)
                logger.info("Creative variants generated successfully and validated")
            except ValueError as e:
                logger.error(f"Output validation failed: {str(e)}")
                result.success = False
                result.error = f"Output validation failed: {str(e)}"
        else:
            logger.error(f"Creative generation failed: {result.error}")

        return result

    def _validate_output_schema(self, output: dict) -> None:
        """Validate that output matches the required schema.

        Args:
            output: The output dict to validate.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required_fields = [
            "variants",
            "channel",
            "product",
            "persona",
            "tone",
            "creative_strategy",
            "rationale",
        ]

        missing_fields = [f for f in required_fields if f not in output]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        # Validate variants structure
        if not isinstance(output["variants"], list):
            raise ValueError("variants must be a list")

        if len(output["variants"]) == 0:
            raise ValueError("variants list cannot be empty")

        for i, variant in enumerate(output["variants"]):
            if not isinstance(variant, dict):
                raise ValueError(f"Variant {i} must be a dict")

            required_variant_fields = [
                "variant_index",
                "headline",
                "body",
                "cta",
                "tone",
                "key_differentiator",
                "safety_check",
            ]

            missing_variant_fields = [f for f in required_variant_fields if f not in variant]
            if missing_variant_fields:
                raise ValueError(
                    f"Variant {i} missing fields: {missing_variant_fields}"
                )

            # Validate safety check structure
            if not isinstance(variant["safety_check"], dict):
                raise ValueError(f"Variant {i} safety_check must be a dict")

            if "passed" not in variant["safety_check"]:
                raise ValueError(f"Variant {i} safety_check missing 'passed' field")

            if "violations" not in variant["safety_check"]:
                raise ValueError(f"Variant {i} safety_check missing 'violations' field")

        # Validate channel is one of allowed values
        allowed_channels = ["linkedin", "email", "search", "display"]
        if output["channel"] not in allowed_channels:
            raise ValueError(f"channel must be one of {allowed_channels}")

        logger.debug("Output schema validation passed")


if __name__ == "__main__":
    """Quick smoke test of the CreativeAgent."""
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

    class MockSafetyCheckerTool:
        """Mock brand safety checker tool."""

        def check_brand_safety(self, text: str) -> dict:
            """Return mock safety check result."""
            prohibited_phrases = [
                "game-changing",
                "revolutionary",
                "world-class",
                "best-in-class",
                "cutting-edge",
                "synergize",
                "paradigm shift",
                "disruptive",
                "unlock your potential",
            ]

            violations = [phrase for phrase in prohibited_phrases if phrase in text.lower()]

            return {
                "passed": len(violations) == 0,
                "violations": violations,
            }

    try:
        # Initialize mock tools
        vector_search = MockVectorSearchTool()
        safety_checker = MockSafetyCheckerTool()

        # Create agent
        agent = CreativeAgent(
            vector_search_tool=vector_search,
            safety_checker_tool=safety_checker,
        )

        # Run creative brief
        result = agent.run_creative_brief(
            channel="linkedin",
            product="Lumen Pro",
            persona="VP of Marketing at mid-market B2B SaaS",
            tone="professional",
            key_message="Reduce marketing attribution blind spots",
            num_variants=3,
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
                        title="Creative Variants Output",
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
                print("\n=== Creative Variants Output ===")
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
