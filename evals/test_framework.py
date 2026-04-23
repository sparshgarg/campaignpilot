"""
Test suite for the CampaignPilot evaluation framework.

Run with: python -m pytest evals/test_framework.py -v
"""

import json
import pytest
from unittest.mock import Mock, patch

from evals.metrics.deterministic import (
    CompletenessMetric,
    BudgetRealismMetric,
    SqlAccuracyMetric,
    SafetyMetric,
    MetricResult,
)
from evals.metrics.llm_judge import (
    StrategicCoherenceMetric,
    BrandVoiceMetric,
    InsightQualityMetric,
)
from evals.metrics.brand_safety import BrandSafetyMetric
from evals.runner import EvalRunner, ExampleResult


class TestCompletenessMetric:
    """Test suite for CompletenessMetric."""

    def test_all_fields_present(self):
        """Test when all required fields are present."""
        metric = CompletenessMetric(required_fields=["field1", "field2"])
        agent_output = {"field1": "value1", "field2": "value2"}
        result = metric.evaluate(agent_output, {})

        assert result.score == 1.0
        assert result.passed is True
        assert len(result.details["present_fields"]) == 2
        assert len(result.details["missing_fields"]) == 0

    def test_missing_fields(self):
        """Test when fields are missing."""
        metric = CompletenessMetric(required_fields=["field1", "field2", "field3"])
        agent_output = {"field1": "value1"}
        result = metric.evaluate(agent_output, {})

        assert result.score == pytest.approx(1/3, 0.01)
        assert result.passed is False
        assert "field2" in result.details["missing_fields"]
        assert "field3" in result.details["missing_fields"]

    def test_empty_field_values(self):
        """Test when fields are present but empty."""
        metric = CompletenessMetric(required_fields=["field1", "field2"])
        agent_output = {"field1": "value1", "field2": ""}
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.5
        assert result.passed is False
        assert "field2" in result.details["empty_fields"]

    def test_empty_list_and_dict(self):
        """Test that empty lists and dicts are considered empty."""
        metric = CompletenessMetric(required_fields=["list_field", "dict_field", "valid"])
        agent_output = {
            "list_field": [],
            "dict_field": {},
            "valid": "value",
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == pytest.approx(1/3, 0.01)
        assert "list_field" in result.details["empty_fields"]
        assert "dict_field" in result.details["empty_fields"]


class TestBudgetRealismMetric:
    """Test suite for BudgetRealismMetric."""

    def test_valid_budget_split(self):
        """Test valid budget allocation."""
        metric = BudgetRealismMetric()
        agent_output = {
            "budget_split": {
                "LinkedIn": 0.45,
                "Email": 0.35,
                "Events": 0.20,
            }
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 1.0
        assert result.passed is True
        assert result.details["sum_valid"] is True
        assert result.details["channels_valid"] is True

    def test_invalid_sum(self):
        """Test when budget doesn't sum to 1.0."""
        metric = BudgetRealismMetric()
        agent_output = {
            "budget_split": {
                "LinkedIn": 0.60,
                "Email": 0.25,
            }
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.0
        assert result.passed is False
        assert result.details["sum_valid"] is False

    def test_channel_below_minimum(self):
        """Test when channel allocation is below 5%."""
        metric = BudgetRealismMetric()
        agent_output = {
            "budget_split": {
                "LinkedIn": 0.90,
                "Email": 0.04,
                "Events": 0.06,
            }
        }
        result = metric.evaluate(agent_output, {})

        assert result.passed is False
        assert "Email" in str(result.details["violations"])

    def test_channel_above_maximum(self):
        """Test when channel allocation exceeds 80%."""
        metric = BudgetRealismMetric()
        agent_output = {
            "budget_split": {
                "LinkedIn": 0.85,
                "Email": 0.15,
            }
        }
        result = metric.evaluate(agent_output, {})

        assert result.passed is False
        assert "LinkedIn" in str(result.details["violations"])

    def test_rounding_tolerance(self):
        """Test that sums within 5% tolerance pass."""
        metric = BudgetRealismMetric()
        agent_output = {
            "budget_split": {
                "LinkedIn": 0.45,
                "Email": 0.35,
                "Events": 0.195,  # Sum = 0.995, within tolerance
            }
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 1.0


class TestSqlAccuracyMetric:
    """Test suite for SqlAccuracyMetric."""

    def test_valid_sql_structure(self):
        """Test valid SQL syntax."""
        metric = SqlAccuracyMetric()
        agent_output = {
            "sql": "SELECT * FROM users WHERE active = true"
        }
        result = metric.evaluate(agent_output, {})

        assert result.score >= 0.5  # At least structure is valid
        assert result.details["structure_valid"] is True

    def test_invalid_sql_no_select(self):
        """Test SQL without SELECT."""
        metric = SqlAccuracyMetric()
        agent_output = {
            "sql": "UPDATE users SET active = false"
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.0
        assert result.details["structure_valid"] is False

    def test_missing_sql(self):
        """Test when SQL is not provided."""
        metric = SqlAccuracyMetric()
        agent_output = {"result": "some output"}
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.0
        assert result.passed is False

    def test_sql_with_execution(self):
        """Test SQL execution with mock tool."""
        mock_tool = Mock(return_value=[{"id": 1}, {"id": 2}])
        metric = SqlAccuracyMetric(db_query_tool=mock_tool)
        agent_output = {
            "sql": "SELECT id FROM users"
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 1.0
        assert result.details["execution_valid"] is True
        mock_tool.assert_called_once()

    def test_sql_execution_failure(self):
        """Test SQL that fails to execute."""
        mock_tool = Mock(side_effect=Exception("Invalid table"))
        metric = SqlAccuracyMetric(db_query_tool=mock_tool)
        agent_output = {
            "sql": "SELECT * FROM invalid_table"
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.5  # Structure valid, execution fails
        assert result.details["execution_valid"] is False


class TestSafetyMetric:
    """Test suite for SafetyMetric."""

    def test_safe_content(self):
        """Test when content passes safety checks."""
        mock_checker = Mock()
        mock_checker.check_safety.return_value = {
            "violations": [],
            "passed": True
        }
        metric = SafetyMetric(safety_checker=mock_checker)
        agent_output = {
            "headline": "Safe headline",
            "body": "Safe content"
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 1.0
        assert result.passed is True

    def test_unsafe_content(self):
        """Test when content fails safety checks."""
        mock_checker = Mock()
        mock_checker.check_safety.return_value = {
            "violations": [
                {"type": "unsubstantiated_claim", "severity": "high"}
            ],
            "passed": False
        }
        metric = SafetyMetric(safety_checker=mock_checker)
        agent_output = {
            "headline": "Unsafe claim",
        }
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.0
        assert result.passed is False

    def test_empty_content(self):
        """Test when there's no content to check."""
        mock_checker = Mock()
        metric = SafetyMetric(safety_checker=mock_checker)
        agent_output = {}
        result = metric.evaluate(agent_output, {})

        # No content = safe by default
        assert result.passed is True
        mock_checker.check_safety.assert_not_called()


class TestBrandSafetyMetric:
    """Test suite for BrandSafetyMetric."""

    def test_brand_safe_content(self):
        """Test brand-safe content."""
        mock_checker = Mock()
        mock_checker.check_safety.return_value = {
            "violations": [],
            "passed": True
        }
        metric = BrandSafetyMetric(safety_checker=mock_checker)
        agent_output = {"headline": "Professional headline"}
        result = metric.evaluate(agent_output, {})

        assert result.score == 1.0

    def test_brand_unsafe_high_severity(self):
        """Test high severity violations."""
        mock_checker = Mock()
        mock_checker.check_safety.return_value = {
            "violations": [
                {"severity": "high", "message": "Critical issue"}
            ],
            "passed": False
        }
        metric = BrandSafetyMetric(safety_checker=mock_checker)
        agent_output = {"headline": "Bad content"}
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.0

    def test_brand_unsafe_low_severity(self):
        """Test low severity violations."""
        mock_checker = Mock()
        mock_checker.check_safety.return_value = {
            "violations": [
                {"severity": "low", "message": "Minor issue"}
            ],
            "passed": False
        }
        metric = BrandSafetyMetric(safety_checker=mock_checker)
        agent_output = {"headline": "Slightly bad content"}
        result = metric.evaluate(agent_output, {})

        assert result.score == 0.5


class TestEvalRunner:
    """Test suite for EvalRunner."""

    def test_runner_initialization(self):
        """Test EvalRunner initialization."""
        runner = EvalRunner()
        assert runner.db_query_tool is None
        assert runner.pass_threshold_override == {}

    def test_load_golden_dataset(self, tmp_path):
        """Test loading golden dataset from file."""
        dataset = [
            {"id": "ex1", "input": {"goal": "test"}, "expected_output": {}},
            {"id": "ex2", "input": {"goal": "test2"}, "expected_output": {}},
        ]
        file_path = tmp_path / "dataset.json"
        with open(file_path, "w") as f:
            json.dump(dataset, f)

        loaded = EvalRunner.load_golden_dataset(str(file_path))
        assert len(loaded) == 2
        assert loaded[0]["id"] == "ex1"

    def test_calculate_aggregates(self):
        """Test aggregate statistics calculation."""
        runner = EvalRunner()
        metric1 = Mock(name="metric1")
        metric2 = Mock(name="metric2")

        results = [
            ExampleResult(
                example_id="ex1",
                metric_scores={"metric1": 0.8, "metric2": 3.5},
                metric_passed={"metric1": True, "metric2": True},
                metric_details={},
                agent_output={},
                golden_expected={},
            ),
            ExampleResult(
                example_id="ex2",
                metric_scores={"metric1": 0.6, "metric2": 2.5},
                metric_passed={"metric1": False, "metric2": False},
                metric_details={},
                agent_output={},
                golden_expected={},
            ),
        ]

        aggregates = runner._calculate_aggregates(results, [metric1, metric2])

        assert aggregates["metric1"]["mean"] == pytest.approx(0.7, 0.01)
        assert aggregates["metric1"]["pass_rate"] == 0.5
        assert aggregates["metric2"]["mean"] == pytest.approx(3.0, 0.01)


class TestMetricResult:
    """Test MetricResult dataclass."""

    def test_metric_result_creation(self):
        """Test creating MetricResult."""
        result = MetricResult(
            metric_name="test_metric",
            score=0.85,
            passed=True,
            details={"key": "value"},
        )

        assert result.metric_name == "test_metric"
        assert result.score == 0.85
        assert result.passed is True
        assert result.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
