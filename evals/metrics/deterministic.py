"""Deterministic (non-LLM) evaluation metrics for CampaignPilot."""
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class MetricResult:
    """Result of a single metric evaluation."""
    metric_name: str
    score: float  # 0.0 to 1.0 (normalized) or 1-5 scale — defined per metric
    passed: bool
    details: dict = field(default_factory=dict)
    error: Optional[str] = None


class BaseMetric(ABC):
    """Base class for all evaluation metrics."""
    name: str
    pass_threshold: float  # score must be >= this to pass

    @abstractmethod
    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Evaluate agent output against golden example.

        Args:
            agent_output: Output from the agent being evaluated
            golden_example: Ground truth example from golden dataset

        Returns:
            MetricResult with score, pass/fail, and details
        """
        pass


class CompletenessMetric(BaseMetric):
    """Checks that all required fields are present and non-empty."""

    name = "completeness"
    pass_threshold = 0.8

    def __init__(self, required_fields: Optional[list[str]] = None):
        """Initialize completeness metric.

        Args:
            required_fields: List of field names that must be present and non-empty.
                Defaults to core campaign fields.
        """
        self.required_fields = required_fields or [
            "recommended_channels",
            "budget_split",
            "primary_message_pillar",
            "kpis",
            "rationale",
        ]

    def _is_empty(self, value: Any) -> bool:
        """Check if a value is considered empty."""
        if value is None:
            return True
        if isinstance(value, str) and value.strip() == "":
            return True
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        return False

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Check each required field is present and non-empty."""
        missing_fields = []
        empty_fields = []
        present_fields = []

        for field_name in self.required_fields:
            if field_name not in agent_output:
                missing_fields.append(field_name)
            elif self._is_empty(agent_output[field_name]):
                empty_fields.append(field_name)
            else:
                present_fields.append(field_name)

        # Score = fraction of fields present and non-empty
        score = len(present_fields) / len(self.required_fields) if self.required_fields else 0.0
        passed = score >= self.pass_threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            details={
                "missing_fields": missing_fields,
                "empty_fields": empty_fields,
                "present_fields": present_fields,
                "required_count": len(self.required_fields),
                "present_count": len(present_fields),
            },
        )


class BudgetRealismMetric(BaseMetric):
    """Validates budget split for realism and reasonableness."""

    name = "budget_realism"
    pass_threshold = 0.7

    MIN_CHANNEL_ALLOCATION = 0.05  # 5%
    MAX_CHANNEL_ALLOCATION = 0.80  # 80%
    SUM_TOLERANCE = 0.05  # 5% tolerance for rounding

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Check budget_split is realistic and valid."""
        budget_split = agent_output.get("budget_split", {})
        violations = []

        # Check if budget_split exists and is a dict
        if not isinstance(budget_split, dict):
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={
                    "sum": 0.0,
                    "sum_valid": False,
                    "channels_valid": False,
                    "violations": ["budget_split is not a dictionary"],
                },
            )

        # Check if there's at least one channel
        if len(budget_split) < 1:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={
                    "sum": 0.0,
                    "sum_valid": False,
                    "channels_valid": False,
                    "violations": ["No channels allocated"],
                },
            )

        # Normalize dollar amounts to fractions if sum >> 1 (agent outputs USD values)
        total_raw = sum(budget_split.values())
        if total_raw > 2:
            budget_split = {k: v / total_raw for k, v in budget_split.items()}
        total = sum(budget_split.values())
        sum_valid = 0.95 <= total <= 1.05
        if not sum_valid:
            violations.append(f"Sum of allocations is {total:.2f}, not close to 1.0")

        # Check individual channel allocations
        channels_valid = True
        for channel, allocation in budget_split.items():
            if not isinstance(allocation, (int, float)):
                violations.append(f"Channel '{channel}' allocation is not numeric")
                channels_valid = False
                continue

            if allocation < self.MIN_CHANNEL_ALLOCATION:
                violations.append(
                    f"Channel '{channel}' allocation {allocation:.1%} is below minimum {self.MIN_CHANNEL_ALLOCATION:.0%}"
                )
                channels_valid = False

            if allocation > self.MAX_CHANNEL_ALLOCATION:
                violations.append(
                    f"Channel '{channel}' allocation {allocation:.1%} exceeds maximum {self.MAX_CHANNEL_ALLOCATION:.0%}"
                )
                channels_valid = False

        # Determine score
        if sum_valid and channels_valid:
            score = 1.0
        elif sum_valid and not channels_valid:
            score = 0.5
        else:
            score = 0.0

        passed = score >= self.pass_threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            details={
                "sum": round(total, 3),
                "sum_valid": sum_valid,
                "channels_valid": channels_valid,
                "violations": violations,
                "channels": list(budget_split.keys()),
            },
        )


class SqlAccuracyMetric(BaseMetric):
    """Validates SQL query structure and execution."""

    name = "sql_accuracy"
    pass_threshold = 0.6

    def __init__(self, db_query_tool=None):
        """Initialize SQL accuracy metric.

        Args:
            db_query_tool: Optional tool to execute SQL queries. If None, only syntax is checked.
        """
        self.db_query_tool = db_query_tool

    def _extract_sql(self, agent_output: dict) -> Optional[str]:
        """Extract SQL from agent output."""
        # Try common field names
        for field in ["sql", "expected_sql", "query", "sql_query"]:
            if field in agent_output:
                value = agent_output[field]
                if isinstance(value, str):
                    return value.strip()

        # If no SQL field found, return None
        return None

    def _validate_sql_structure(self, sql: str) -> tuple[bool, list[str]]:
        """Perform basic structural validation on SQL."""
        issues = []

        if not sql:
            issues.append("SQL is empty")
            return False, issues

        sql_upper = sql.upper().strip()

        # Check for SELECT statement
        if not sql_upper.startswith("SELECT"):
            issues.append("Query does not start with SELECT")
            return False, issues

        # Basic checks
        if ";" in sql and not sql.strip().endswith(";"):
            issues.append("Semicolon found in middle of query")
            return False, issues

        # Check for balanced parentheses
        if sql.count("(") != sql.count(")"):
            issues.append("Unbalanced parentheses")
            return False, issues

        return True, issues

    def _execute_sql(self, sql: str) -> tuple[bool, str]:
        """Attempt to execute SQL query."""
        if not self.db_query_tool:
            return True, "No DB tool provided; structure validation passed"

        try:
            result = self.db_query_tool(sql)
            # If execution succeeds and returns rows, it's valid
            if result and isinstance(result, list) and len(result) >= 0:
                return True, f"Query executed successfully, returned {len(result)} rows"
            elif result:
                return True, "Query executed successfully"
            else:
                return False, "Query executed but returned no data"
        except Exception as e:
            return False, f"Query execution failed: {str(e)}"

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Check SQL validity and executability."""
        sql = self._extract_sql(agent_output)

        if not sql:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={
                    "extracted": False,
                    "structure_valid": False,
                    "execution_valid": False,
                    "issues": ["No SQL found in agent output"],
                },
            )

        # Validate structure
        structure_valid, structure_issues = self._validate_sql_structure(sql)

        if not structure_valid:
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={
                    "extracted": True,
                    "structure_valid": False,
                    "execution_valid": False,
                    "issues": structure_issues,
                    "sql_preview": sql[:200],
                },
            )

        # Try to execute if structure is valid
        execution_valid, execution_message = self._execute_sql(sql)

        # Score based on validation results
        if structure_valid and execution_valid:
            score = 1.0
        elif structure_valid and not execution_valid:
            score = 0.5
        else:
            score = 0.0

        passed = score >= self.pass_threshold

        return MetricResult(
            metric_name=self.name,
            score=score,
            passed=passed,
            details={
                "extracted": True,
                "structure_valid": structure_valid,
                "execution_valid": execution_valid,
                "execution_message": execution_message,
                "issues": structure_issues,
                "sql_preview": sql[:300],
            },
        )


class SafetyMetric(BaseMetric):
    """Checks marketing copy for safety violations."""

    name = "safety"
    pass_threshold = 1.0  # Must be fully safe to pass

    def __init__(self, safety_checker):
        """Initialize safety metric.

        Args:
            safety_checker: SafetyChecker instance with check_safety() method
        """
        self.safety_checker = safety_checker

    def _extract_text(self, agent_output: dict) -> str:
        """Extract all relevant text from agent output."""
        text_parts = []

        # Try common field names for marketing copy
        for field in ["headline", "subject_line", "title", "name"]:
            if field in agent_output:
                value = agent_output[field]
                if isinstance(value, str) and value.strip():
                    text_parts.append(value)

        for field in ["body", "content", "copy", "message", "description"]:
            if field in agent_output:
                value = agent_output[field]
                if isinstance(value, str) and value.strip():
                    text_parts.append(value)

        for field in ["cta", "call_to_action", "button_text"]:
            if field in agent_output:
                value = agent_output[field]
                if isinstance(value, str) and value.strip():
                    text_parts.append(value)

        # If no recognized fields, concatenate all string values
        if not text_parts:
            for value in agent_output.values():
                if isinstance(value, str) and value.strip():
                    text_parts.append(value)

        return " ".join(text_parts)

    def evaluate(self, agent_output: dict, golden_example: dict) -> MetricResult:
        """Check marketing copy for safety violations."""
        text = self._extract_text(agent_output)

        if not text:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                passed=True,
                details={"violations": [], "text_length": 0},
            )

        try:
            # Run safety checker
            result = self.safety_checker.check_safety(text)

            # Check if result has violations
            violations = result.get("violations", [])
            passed = len(violations) == 0
            score = 1.0 if passed else 0.0

            return MetricResult(
                metric_name=self.name,
                score=score,
                passed=passed,
                details={
                    "violations": violations,
                    "text_length": len(text),
                    "safety_result": result,
                },
            )
        except Exception as e:
            logger.error(f"Safety check failed: {e}")
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                passed=False,
                details={"violations": [f"Safety checker error: {str(e)}"]},
                error=str(e),
            )
