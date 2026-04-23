"""Base agent class for CampaignPilot multi-agent system."""

import time
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

import anthropic
from dotenv import load_dotenv
import os

load_dotenv(override=True)

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Result from an agent run.

    Attributes:
        output: The final output from the agent (typically a dict).
        tool_calls_made: List of tool calls executed with metadata.
        total_input_tokens: Total input tokens consumed across all LLM calls.
        total_output_tokens: Total output tokens generated across all LLM calls.
        latency_ms: Total latency in milliseconds from start to finish.
        trace_url: Optional URL to the Langfuse trace.
        success: Whether the run completed successfully.
        error: Error message if success is False.
    """
    output: dict
    tool_calls_made: list[dict] = field(default_factory=list)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    latency_ms: float = 0.0
    trace_url: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class BaseAgent(ABC):
    """Abstract base class for all agents in CampaignPilot.

    Subclasses must implement:
    - get_system_prompt(): Return the system prompt string.
    - get_tools(): Return list of tool definitions in Claude tool_use format.
    - _execute_tool(tool_name, tool_input): Execute the specified tool and return result.
    """

    def __init__(
        self,
        model: str = "claude-haiku-4-5-20251001",
        max_turns: int = 5,
        langfuse_enabled: bool = True,
        event_callback=None,
    ) -> None:
        """Initialize the base agent.

        Args:
            model: The Claude model to use.
            max_turns: Maximum number of agentic loop turns.
            langfuse_enabled: Whether to enable Langfuse tracing.
            event_callback: Optional callable(event_dict) for streaming execution events.
        """
        self.model = model
        self.max_turns = max_turns
        self.langfuse_enabled = langfuse_enabled
        self.event_callback = event_callback

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

        # Initialize Langfuse client (gracefully disable if keys not set)
        self.langfuse = None
        if self.langfuse_enabled:
            try:
                langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
                langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY")
                langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

                if langfuse_secret and langfuse_public:
                    from langfuse import Langfuse
                    self.langfuse = Langfuse(
                        secret_key=langfuse_secret,
                        public_key=langfuse_public,
                        host=langfuse_host,
                    )
                    logger.info("Langfuse tracing enabled")
                else:
                    logger.warning("Langfuse keys not found; tracing disabled")
                    self.langfuse = None
            except ImportError:
                logger.warning("Langfuse not installed; tracing disabled")
                self.langfuse = None
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse: {e}; continuing without tracing")
                self.langfuse = None

    def _emit(self, event_type: str, **data) -> None:
        """Emit an execution event to the callback if set."""
        if self.event_callback:
            try:
                self.event_callback({"type": event_type, "timestamp": time.time(), **data})
            except Exception as e:
                logger.warning(f"Event callback failed: {e}")

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent.

        Returns:
            The system prompt string.
        """
        pass

    @abstractmethod
    def get_tools(self) -> list[dict]:
        """Return the list of tools available to this agent.

        Returns:
            List of tool definitions in Claude tool_use format.
        """
        pass

    @abstractmethod
    def _execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        """Execute the specified tool and return its output.

        Args:
            tool_name: The name of the tool to execute.
            tool_input: The input dict for the tool.

        Returns:
            The tool's output.
        """
        pass

    def run(self, user_message: str, context: Optional[dict] = None) -> AgentResult:
        """Run the agent loop with the given user message.

        Args:
            user_message: The user's message to process.
            context: Optional context dict to be prepended to the system prompt.

        Returns:
            AgentResult with output, tool calls, tokens, latency, and trace URL.
        """
        start_time = time.time()
        messages: list[dict] = [{"role": "user", "content": user_message}]
        tool_calls_made: list[dict] = []
        total_input_tokens = 0
        total_output_tokens = 0
        trace = None
        trace_url = None

        try:
            self._emit("agent_start", agent=self.__class__.__name__, message=user_message[:200])

            # Create Langfuse trace
            if self.langfuse:
                trace = self.langfuse.trace(
                    name=self.__class__.__name__,
                    input=user_message,
                )

            system_prompt = self.get_system_prompt()
            if context:
                system_prompt = f"{system_prompt}\n\nContext: {json.dumps(context, indent=2)}"

            if self.client is None:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            # Agentic loop
            for turn in range(self.max_turns):
                logger.debug(f"Turn {turn + 1}/{self.max_turns}")
                self._emit("turn_start", turn=turn + 1, max_turns=self.max_turns)

                # Call Claude with tool use
                self._emit("llm_call_start", turn=turn + 1, model=self.model)
                turn_start = time.time()
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=8192,
                    system=system_prompt,
                    tools=self.get_tools(),
                    messages=messages,
                )
                turn_latency_ms = (time.time() - turn_start) * 1000

                # Track tokens
                total_input_tokens += response.usage.input_tokens
                total_output_tokens += response.usage.output_tokens

                self._emit(
                    "llm_call_end",
                    turn=turn + 1,
                    latency_ms=turn_latency_ms,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    stop_reason=response.stop_reason,
                )

                # Log generation to Langfuse
                if trace:
                    self._log_generation(
                        trace,
                        f"turn_{turn + 1}",
                        messages,
                        response,
                        turn_latency_ms,
                    )

                # Check stop reason
                if response.stop_reason == "end_turn":
                    # Extract final output as JSON from text content
                    output_dict: dict = {}
                    for block in response.content:
                        if hasattr(block, "text"):
                            try:
                                text = block.text.strip()
                                # Extract JSON from markdown fences anywhere in the text
                                if "```" in text:
                                    import re
                                    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
                                    if match:
                                        text = match.group(1)
                                output_dict = json.loads(text)
                            except json.JSONDecodeError:
                                logger.warning(
                                    f"Could not parse final response as JSON: {block.text[:200]}"
                                )
                                output_dict = {"raw_text": block.text}

                    latency_ms = (time.time() - start_time) * 1000
                    result = AgentResult(
                        output=output_dict,
                        tool_calls_made=tool_calls_made,
                        total_input_tokens=total_input_tokens,
                        total_output_tokens=total_output_tokens,
                        latency_ms=latency_ms,
                        trace_url=trace_url,
                        success=True,
                    )

                    if trace:
                        trace.update(
                            output=output_dict,
                            metadata={"success": True, "turns": turn + 1},
                        )
                        trace_url = trace.get_trace_url()
                        result.trace_url = trace_url

                    logger.info(
                        f"Agent completed in {turn + 1} turns | "
                        f"Tokens: {total_input_tokens} in / {total_output_tokens} out | "
                        f"Latency: {latency_ms:.0f}ms"
                    )
                    self._emit("agent_complete", turns=turn + 1, latency_ms=latency_ms, total_tokens=total_input_tokens + total_output_tokens)
                    return result

                elif response.stop_reason == "tool_use":
                    # Process tool calls
                    assistant_message: dict = {"role": "assistant", "content": response.content}
                    messages.append(assistant_message)

                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            tool_name = block.name
                            tool_input = block.input
                            tool_use_id = block.id

                            logger.debug(f"Tool call: {tool_name} with input {tool_input}")
                            self._emit("tool_call_start", tool=tool_name, input=tool_input)

                            # Execute tool and time it
                            tool_start = time.time()
                            try:
                                tool_output = self._execute_tool(tool_name, tool_input)
                                tool_latency_ms = (time.time() - tool_start) * 1000
                                tool_success = True
                                tool_error = None
                            except Exception as e:
                                tool_latency_ms = (time.time() - tool_start) * 1000
                                tool_output = None
                                tool_success = False
                                tool_error = str(e)
                                logger.error(f"Tool execution error: {tool_error}")

                            # Compute output preview
                            output_preview = str(tool_output)[:200] if tool_success else tool_error
                            self._emit(
                                "tool_call_end",
                                tool=tool_name,
                                success=tool_success,
                                latency_ms=tool_latency_ms,
                                output_preview=output_preview,
                            )

                            # Record tool call
                            tool_calls_made.append({
                                "tool": tool_name,
                                "input": tool_input,
                                "output": tool_output,
                                "latency_ms": tool_latency_ms,
                                "success": tool_success,
                                "error": tool_error,
                            })

                            # Add tool result to messages
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": tool_use_id,
                                "content": json.dumps(tool_output, default=str) if tool_success else f"Error: {tool_error}",
                            })

                    # Append all tool results in one user message
                    messages.append({"role": "user", "content": tool_results})

                else:
                    logger.warning(f"Unexpected stop reason: {response.stop_reason}")
                    latency_ms = (time.time() - start_time) * 1000
                    error_msg = f"Unexpected stop reason: {response.stop_reason}"
                    result = AgentResult(
                        output={},
                        tool_calls_made=tool_calls_made,
                        total_input_tokens=total_input_tokens,
                        total_output_tokens=total_output_tokens,
                        latency_ms=latency_ms,
                        trace_url=trace_url,
                        success=False,
                        error=error_msg,
                    )
                    if trace:
                        trace.update(output={}, metadata={"success": False, "error": error_msg})
                    return result

            # Max turns exceeded
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Agent exceeded max turns ({self.max_turns})"
            result = AgentResult(
                output={},
                tool_calls_made=tool_calls_made,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                latency_ms=latency_ms,
                trace_url=trace_url,
                success=False,
                error=error_msg,
            )
            if trace:
                trace.update(output={}, metadata={"success": False, "error": error_msg})
            logger.error(error_msg)
            return result

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = f"Agent error: {str(e)}"
            result = AgentResult(
                output={},
                tool_calls_made=tool_calls_made,
                total_input_tokens=total_input_tokens,
                total_output_tokens=total_output_tokens,
                latency_ms=latency_ms,
                trace_url=trace_url,
                success=False,
                error=error_msg,
            )
            if trace:
                trace.update(output={}, metadata={"success": False, "error": error_msg})
            logger.exception("Unhandled exception in agent loop")
            return result

    def _log_generation(
        self,
        trace: Any,
        generation_name: str,
        input_messages: list,
        response: Any,
        latency_ms: float,
    ) -> None:
        """Log a generation to Langfuse.

        Args:
            trace: The Langfuse trace object.
            generation_name: Name for this generation.
            input_messages: The messages sent to the model.
            response: The response from the model.
            latency_ms: Latency in milliseconds.
        """
        if not self.langfuse:
            return

        try:
            # Extract text from response
            output_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    output_text += block.text
                elif hasattr(block, "name"):
                    output_text += f"[Tool: {block.name}]"

            # Calculate cost estimate (Claude Sonnet 4.5 pricing)
            input_cost = response.usage.input_tokens * 0.000003
            output_cost = response.usage.output_tokens * 0.000015
            total_cost = input_cost + output_cost

            trace.generation(
                name=generation_name,
                model=self.model,
                input=input_messages,
                output=output_text,
                usage={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
                metadata={
                    "latency_ms": latency_ms,
                    "stop_reason": response.stop_reason,
                },
                cost_data={
                    "input": input_cost,
                    "output": output_cost,
                    "total": total_cost,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to log generation to Langfuse: {e}")
