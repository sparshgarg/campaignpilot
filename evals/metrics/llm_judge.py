"""LLM-as-judge evaluation metrics using Claude Haiku for cost efficiency."""
import json
import logging
import time
from abc import ABC
from dataclasses import dataclass
from typing import Optional, Tuple

import anthropic
from dotenv import load_dotenv

from evals.metrics.deterministic import BaseMetric, MetricResult

load_dotenv()
logger = logging.getLogger(__name__)


class BaseLLMJudge(BaseMetric, ABC):
    """Base class for LLM-as-judge metrics."""

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        """Initialize LLM judge.

        Args:
            model: Claude model to use for judging. Defaults to Haiku for cost efficiency.
        """
        self.model = model
        self.client = anthropic.Anthropic()

    def _judge(self, prompt: str, max_retries: int = 1) -> Tuple[float, str]:
        """Call Claude to judge and parse response.

        Args:
            prompt: Full prompt for the judge
            max_retries: Number of retries on JSON parse failure

        Returns:
            Tuple of (score, reasoning). Returns (0.0, "judge_error") on fatal error.
        """
        retries = 0
        while retries <= max_retries:
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=500,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                )

                response_text = message.content[0].text.strip()

                # Try to extract JSON from response
                try:
                    # Try direct JSON parse first
                    result = json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to find JSON in the response
                    json_match = response_text.find("{")
                    if json_match >= 0:
                        response_text = response_text[json_match :]
                        result = json.loads(response_text)
                    else:
                        raise json.JSONDecodeError("No JSON found", response_text, 0)

                # Extract score and reasoning
                score = float(result.get("score", 0.0))
                reasoning = result.get("reasoning", "")

                return score, reasoning

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                retries += 1
                if retries > max_retries:
                    logger.error(f"Judge parse error after {max_retries + 1} attempts: {e}")
                    return 0.0, "judge_error"
                time.sleep(0.5)

            except anthropic.APIError as e:
                logger.error(f"API error during judging: {e}")
                return 0.0, "judge_error"

        return 0.0, "judge_error"


class StrategicCoherenceMetric(BaseLLMJudge):
    """Evaluates strategic coherence of B2B marketing campaigns."""

    name = "strategic_coherence"
    pass_threshold = 3.0  # 1-5 scale

    RUBRIC = """You are evaluating the strategic coherence of a B2B marketing campaign brief.

RUBRIC:
1 - The strategy is fundamentally misaligned: wrong channels for the segment, KPIs don't match the goal, budget split is irrational, or the rationale contradicts the recommendations.
2 - Weak strategy: channels are plausible but not optimal, KPIs are generic, rationale is thin, budget split lacks justification.
3 - Acceptable strategy: channels are reasonable for the segment, KPIs are relevant, rationale explains the logic. Some missed opportunities or questionable choices.
4 - Strong strategy: channels are well-matched to the segment's preferred media, KPIs are specific and measurable, budget split is justified with reasoning, rationale cites relevant factors.
5 - Excellent strategy: optimal channel selection grounded in segment behavior, KPIs are specific/measurable/achievable/relevant, budget split maximizes expected ROI given constraints, rationale demonstrates deep understanding of B2B marketing dynamics and the Lumen Analytics brand.

IMPORTANT: Score based only on internal logical consistency and appropriateness for the stated goal and segment. Do not penalize for missing information not required by the schema.

Return ONLY valid JSON: {"score": <1-5 integer>, "reasoning": "<1-2 sentences explaining the score>"}"""

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Evaluate strategic coherence of the campaign."""
        # Build evaluation prompt
        input_context = json.dumps(golden_example.get("input", {}), indent=2)
        output_context = json.dumps(agent_output, indent=2)

        prompt = f"""{self.RUBRIC}

GOAL AND SEGMENT:
{input_context}

AGENT'S STRATEGY:
{output_context}

Evaluate the strategy above and return JSON with score and reasoning."""

        score, reasoning = self._judge(prompt)

        # Validate score is in range
        score = max(1.0, min(5.0, score))

        passed = score >= self.pass_threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            details={
                "reasoning": reasoning,
                "judge_model": self.model,
                "scale": "1-5",
            },
        )


class BrandVoiceMetric(BaseLLMJudge):
    """Evaluates marketing copy for brand voice alignment."""

    name = "brand_voice"
    pass_threshold = 3.0  # 1-5 scale

    RUBRIC = """You are evaluating whether marketing copy matches the Lumen Analytics brand voice guidelines.

LUMEN ANALYTICS BRAND VOICE:
- Professional but approachable — authoritative without being stiff
- Data-forward — specific numbers over vague claims
- Anti-hype — no exaggeration or marketing fluff
- Outcomes-obsessed — leads with what the customer achieves, not product features
- Second person ("you/your team") not third person

PROHIBITED PHRASES (any presence = automatic score reduction):
game-changing, revolutionary, world-class, best-in-class, cutting-edge, synergize, paradigm shift, disruptive, unlock your potential, leverage (as verb)

RUBRIC:
1 - Copy violates brand voice severely: contains multiple prohibited phrases, leads with features not outcomes, uses passive voice throughout, or reads like generic marketing spam.
2 - Copy mostly violates brand voice: contains 1 prohibited phrase OR lacks specific numbers OR focuses on features over outcomes.
3 - Acceptable copy: correct tone, no prohibited phrases, but generic — could apply to any BI tool. Missing the specific Lumen Analytics voice.
4 - Strong brand alignment: correct tone, outcome-led, specific and credible, feels like it came from Lumen Analytics.
5 - Exceptional: perfect tone, compelling specific outcome in first sentence, uses data point, second person, no fluff, clearly Lumen Analytics.

Return ONLY valid JSON: {"score": <1-5 integer>, "reasoning": "<1-2 sentences>"}"""

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Evaluate brand voice alignment of the copy."""
        # Extract copy from agent output
        copy_text = ""
        for field in ["headline", "subject_line", "body", "copy", "content", "message"]:
            if field in agent_output and isinstance(agent_output[field], str):
                copy_text += agent_output[field] + "\n"

        if not copy_text.strip():
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={
                    "error": "No marketing copy found in agent output",
                    "judge_model": self.model,
                },
            )

        prompt = f"""{self.RUBRIC}

MARKETING COPY TO EVALUATE:
{copy_text}

Evaluate the copy above and return JSON with score and reasoning."""

        score, reasoning = self._judge(prompt)

        # Validate score is in range
        score = max(1.0, min(5.0, score))

        passed = score >= self.pass_threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            details={
                "reasoning": reasoning,
                "judge_model": self.model,
                "scale": "1-5",
                "copy_length": len(copy_text),
            },
        )


class InsightQualityMetric(BaseLLMJudge):
    """Evaluates quality of marketing analytics insights."""

    name = "insight_quality"
    pass_threshold = 3.0  # 1-5 scale

    RUBRIC = """You are evaluating the quality of a marketing analytics insight.

RUBRIC:
1 - No insight: restates numbers without interpretation. Example: "LinkedIn had 450 clicks and email had 320 clicks."
2 - Minimal insight: identifies the top/bottom performer but states the obvious without explaining why or what to do.
3 - Adequate insight: identifies the finding, gives basic context (vs. benchmark or vs. other channels), suggests a next step.
4 - Strong insight: identifies the finding, explains the likely cause, quantifies the implication, recommends a specific action with expected impact.
5 - Exceptional insight: finding + root cause analysis + quantified implication + specific action + risk/tradeoff consideration. Reads like a senior analyst's recommendation.

Return ONLY valid JSON: {"score": <1-5 integer>, "reasoning": "<1-2 sentences>"}"""

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Evaluate quality of the insight."""
        # Extract insight text
        insight_text = ""
        for field in ["insight", "analysis", "finding", "recommendation", "summary"]:
            if field in agent_output and isinstance(agent_output[field], str):
                insight_text += agent_output[field] + "\n"

        if not insight_text.strip():
            # Try to concatenate all string fields
            for value in agent_output.values():
                if isinstance(value, str) and len(value) > 10:
                    insight_text += value + "\n"

        if not insight_text.strip():
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={
                    "error": "No insight content found in agent output",
                    "judge_model": self.model,
                },
            )

        # Include golden example context if available
        context = ""
        if "input" in golden_example:
            context = f"\nCONTEXT:\n{json.dumps(golden_example['input'], indent=2)}\n"

        prompt = f"""{self.RUBRIC}

{context}
INSIGHT TO EVALUATE:
{insight_text}

Evaluate the insight above and return JSON with score and reasoning."""

        score, reasoning = self._judge(prompt)

        # Validate score is in range
        score = max(1.0, min(5.0, score))

        passed = score >= self.pass_threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            details={
                "reasoning": reasoning,
                "judge_model": self.model,
                "scale": "1-5",
                "insight_length": len(insight_text),
            },
        )
