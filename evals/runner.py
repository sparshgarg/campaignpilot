"""Eval runner — the core harness for CampaignPilot agent evaluation."""
import argparse
import json
import logging
import statistics
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional, Callable

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from evals.metrics.deterministic import BaseMetric

load_dotenv()
logger = logging.getLogger(__name__)
console = Console()


@dataclass
class ExampleResult:
    """Result of evaluating a single example."""

    example_id: str
    metric_scores: dict[str, float]
    metric_passed: dict[str, bool]
    metric_details: dict[str, dict]
    agent_output: dict
    golden_expected: dict
    errors: list[str] = field(default_factory=list)


@dataclass
class EvalReport:
    """Comprehensive evaluation report."""

    agent_name: str
    dataset_version: str
    total_examples: int
    example_results: list[ExampleResult]
    aggregate_scores: dict[str, dict]  # metric -> {mean, min, max, p25, p75, pass_rate}
    regression_flags: list[dict]  # [{metric, baseline_score, current_score, drop_pct}]
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    run_duration_ms: float
    passed: bool  # overall pass/fail


class EvalRunner:
    """Main evaluation harness for CampaignPilot agents."""

    # Token pricing for Claude Haiku (as of 2024)
    HAIKU_INPUT_COST_PER_1M = 0.80  # dollars per 1M input tokens
    HAIKU_OUTPUT_COST_PER_1M = 4.00  # dollars per 1M output tokens

    def __init__(
        self,
        db_query_tool: Optional[Callable] = None,
        pass_threshold_override: Optional[dict] = None,
    ):
        """Initialize eval runner.

        Args:
            db_query_tool: Optional tool for SQL execution and DB operations
            pass_threshold_override: Optional dict of metric_name -> threshold overrides
        """
        self.db_query_tool = db_query_tool
        self.pass_threshold_override = pass_threshold_override or {}
        self.db_connection = None

    def _get_db_connection(self):
        """Get PostgreSQL connection from DATABASE_URL env var."""
        import os

        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            logger.warning("DATABASE_URL not set; evaluation results won't be saved")
            return None

        try:
            # Parse PostgreSQL URL
            conn = psycopg2.connect(db_url)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return None

    def _save_to_db(self, report: EvalReport) -> bool:
        """Save evaluation report to database.

        Args:
            report: EvalReport to save

        Returns:
            True if successful, False otherwise
        """
        conn = self._get_db_connection()
        if not conn:
            return False

        try:
            cur = conn.cursor()

            # Insert eval run
            cur.execute(
                """
                INSERT INTO eval_runs (agent_name, dataset_version, total_examples,
                    passed, aggregate_scores, input_tokens, output_tokens,
                    estimated_cost_usd, duration_ms)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    report.agent_name,
                    report.dataset_version,
                    report.total_examples,
                    report.passed,
                    json.dumps(report.aggregate_scores),
                    report.total_input_tokens,
                    report.total_output_tokens,
                    report.estimated_cost_usd,
                    report.run_duration_ms,
                ),
            )

            run_id = cur.fetchone()[0]

            # Insert example results
            for example_result in report.example_results:
                cur.execute(
                    """
                    INSERT INTO eval_examples (eval_run_id, example_id,
                        metric_scores, metric_passed, errors)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        run_id,
                        example_result.example_id,
                        json.dumps(example_result.metric_scores),
                        json.dumps(example_result.metric_passed),
                        json.dumps(example_result.errors),
                    ),
                )

            conn.commit()
            logger.info(f"Saved evaluation results to DB (run_id={run_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to save to DB: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def _check_regression(
        self, agent_name: str, current_scores: dict[str, dict]
    ) -> list[dict]:
        """Check for metric regressions vs baseline.

        Args:
            agent_name: Name of the agent
            current_scores: Current aggregate scores

        Returns:
            List of regression flags with {metric, baseline_score, current_score, drop_pct}
        """
        conn = self._get_db_connection()
        if not conn:
            return []

        regressions = []
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

            # Get last eval run for this agent
            cur.execute(
                """
                SELECT scores FROM eval_runs
                WHERE agent_name = %s
                ORDER BY run_at DESC
                LIMIT 1
                """,
                (agent_name,),
            )

            row = cur.fetchone()
            if not row:
                return []

            baseline_scores = json.loads(row["scores"]) if isinstance(row["scores"], str) else row["scores"]

            # Check for regressions (>5% drop)
            for metric_name, current_score_data in current_scores.items():
                if metric_name not in baseline_scores:
                    continue

                baseline_mean = baseline_scores[metric_name].get("mean", 0.0)
                current_mean = current_score_data.get("mean", 0.0)

                if baseline_mean > 0:
                    drop_pct = ((baseline_mean - current_mean) / baseline_mean) * 100
                    if drop_pct > 5.0:
                        regressions.append(
                            {
                                "metric": metric_name,
                                "baseline_score": round(baseline_mean, 3),
                                "current_score": round(current_mean, 3),
                                "drop_pct": round(drop_pct, 1),
                            }
                        )

            return regressions

        except Exception as e:
            logger.error(f"Regression check failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def _extract_tokens(self, agent_result: Any) -> tuple[int, int]:
        """Extract token counts from agent result if available."""
        input_tokens = 0
        output_tokens = 0

        if hasattr(agent_result, "usage"):
            input_tokens = getattr(agent_result.usage, "input_tokens", 0)
            output_tokens = getattr(agent_result.usage, "output_tokens", 0)
        elif isinstance(agent_result, dict):
            input_tokens = agent_result.get("input_tokens", 0)
            output_tokens = agent_result.get("output_tokens", 0)

        return input_tokens, output_tokens

    def _calculate_aggregates(
        self, example_results: list[ExampleResult], metrics: list[BaseMetric]
    ) -> dict[str, dict]:
        """Calculate aggregate statistics for each metric."""
        aggregates = {}

        for metric in metrics:
            metric_name = metric.name
            scores = [
                result.metric_scores[metric_name]
                for result in example_results
                if metric_name in result.metric_scores
            ]
            passes = [
                result.metric_passed[metric_name]
                for result in example_results
                if metric_name in result.metric_passed
            ]

            if not scores:
                aggregates[metric_name] = {
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "p25": 0.0,
                    "p75": 0.0,
                    "pass_rate": 0.0,
                }
                continue

            aggregates[metric_name] = {
                "mean": round(statistics.mean(scores), 3),
                "min": round(min(scores), 3),
                "max": round(max(scores), 3),
                "p25": round(statistics.quantiles(scores, n=4)[0], 3) if len(scores) > 1 else scores[0],
                "p75": round(statistics.quantiles(scores, n=4)[2], 3) if len(scores) > 1 else scores[0],
                "pass_rate": round(sum(passes) / len(passes), 3) if passes else 0.0,
            }

        return aggregates

    def run(
        self,
        agent: Any,
        golden_dataset: list[dict],
        metrics: list[BaseMetric],
        agent_name: str,
        dataset_version: str = "v1",
    ) -> EvalReport:
        """Run evaluation on agent against golden dataset.

        Args:
            agent: Agent instance with run() method
            golden_dataset: List of golden examples with 'input' and 'expected_output'
            metrics: List of BaseMetric instances to evaluate
            agent_name: Name of the agent
            dataset_version: Version of the dataset

        Returns:
            EvalReport with results
        """
        start_time = time.time()
        example_results = []
        total_input_tokens = 0
        total_output_tokens = 0

        console.print(
            f"\n[bold blue]Evaluating {agent_name} against {len(golden_dataset)} examples[/bold blue]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Running {agent_name} eval...", total=len(golden_dataset)
            )

            for idx, golden_example in enumerate(golden_dataset):
                try:
                    # Extract input from golden example
                    example_input = golden_example.get("input", {})
                    example_id = golden_example.get("id", f"example_{idx}")

                    # Run agent — use run_fn if provided, otherwise call .run()
                    run_fn = getattr(agent, "_eval_run_fn", None)
                    if run_fn:
                        agent_result = run_fn(example_input)
                    else:
                        agent_result = agent.run(str(example_input))

                    # Unwrap AgentResult dataclass or tuple
                    from agents.base_agent import AgentResult as _AgentResult
                    if isinstance(agent_result, _AgentResult):
                        agent_output = agent_result.output or {}
                        total_input_tokens += agent_result.total_input_tokens
                        total_output_tokens += agent_result.total_output_tokens
                    elif isinstance(agent_result, tuple):
                        agent_output, metadata = agent_result
                        input_tokens, output_tokens = self._extract_tokens(metadata)
                        total_input_tokens += input_tokens
                        total_output_tokens += output_tokens
                    else:
                        agent_output = agent_result if isinstance(agent_result, dict) else {"output": agent_result}

                    # Evaluate metrics
                    metric_scores = {}
                    metric_passed = {}
                    metric_details = {}
                    errors = []

                    for metric in metrics:
                        try:
                            result = metric.evaluate(agent_output, golden_example)
                            metric_scores[metric.name] = result.score
                            metric_passed[metric.name] = result.passed
                            metric_details[metric.name] = result.details
                            if result.error:
                                errors.append(f"{metric.name}: {result.error}")
                        except Exception as e:
                            logger.error(f"Metric {metric.name} evaluation failed: {e}")
                            metric_scores[metric.name] = 0.0
                            metric_passed[metric.name] = False
                            metric_details[metric.name] = {"error": str(e)}
                            errors.append(f"{metric.name}: {str(e)}")

                    example_results.append(
                        ExampleResult(
                            example_id=example_id,
                            metric_scores=metric_scores,
                            metric_passed=metric_passed,
                            metric_details=metric_details,
                            agent_output=agent_output,
                            golden_expected=golden_example.get("expected_output", {}),
                            errors=errors,
                        )
                    )

                except Exception as e:
                    logger.error(f"Failed to process example {idx}: {e}")
                    example_results.append(
                        ExampleResult(
                            example_id=f"example_{idx}",
                            metric_scores={m.name: 0.0 for m in metrics},
                            metric_passed={m.name: False for m in metrics},
                            metric_details={},
                            agent_output={},
                            golden_expected={},
                            errors=[str(e)],
                        )
                    )

                progress.update(task, advance=1)

        # Calculate aggregate scores
        aggregate_scores = self._calculate_aggregates(example_results, metrics)

        # Check for regressions
        regression_flags = self._check_regression(agent_name, aggregate_scores)

        # Calculate overall pass/fail
        all_metrics_pass = all(
            aggregate_scores[m.name]["pass_rate"] >= 0.5 for m in metrics
        )

        # Calculate cost
        estimated_cost_usd = (
            (total_input_tokens / 1_000_000) * self.HAIKU_INPUT_COST_PER_1M
            + (total_output_tokens / 1_000_000) * self.HAIKU_OUTPUT_COST_PER_1M
        )

        duration_ms = (time.time() - start_time) * 1000

        report = EvalReport(
            agent_name=agent_name,
            dataset_version=dataset_version,
            total_examples=len(golden_dataset),
            example_results=example_results,
            aggregate_scores=aggregate_scores,
            regression_flags=regression_flags,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
            estimated_cost_usd=round(estimated_cost_usd, 4),
            run_duration_ms=round(duration_ms, 0),
            passed=all_metrics_pass,
        )

        return report

    def print_report(self, report: EvalReport) -> None:
        """Print a beautifully formatted evaluation report."""
        # Overall status panel
        status_symbol = "✓" if report.passed else "✗"
        status_color = "green" if report.passed else "red"
        console.print(
            Panel(
                f"[bold {status_color}]{status_symbol} {report.agent_name} ({report.dataset_version})[/bold {status_color}]\n"
                f"Examples: {report.total_examples} | Status: {'PASSED' if report.passed else 'FAILED'}",
                expand=False,
            )
        )

        # Metrics table
        metrics_table = Table(title="Metric Results", show_header=True, header_style="bold magenta")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Mean", justify="right")
        metrics_table.add_column("Pass Rate", justify="right")
        metrics_table.add_column("Range", justify="right")
        metrics_table.add_column("Status", justify="center")
        metrics_table.add_column("Regression", style="yellow")

        for metric_name, scores in report.aggregate_scores.items():
            mean = scores.get("mean", 0.0)
            pass_rate = scores.get("pass_rate", 0.0)
            min_score = scores.get("min", 0.0)
            max_score = scores.get("max", 0.0)

            status = "✓" if pass_rate >= 0.5 else "✗"
            status_color = "green" if pass_rate >= 0.5 else "red"

            regression = ""
            for flag in report.regression_flags:
                if flag["metric"] == metric_name:
                    regression = f"↓ {flag['drop_pct']}%"
                    break

            metrics_table.add_row(
                metric_name,
                f"{mean:.3f}",
                f"{pass_rate:.0%}",
                f"{min_score:.3f}-{max_score:.3f}",
                f"[{status_color}]{status}[/{status_color}]",
                regression,
            )

        console.print(metrics_table)

        # Failed examples (up to 5)
        failed_examples = [
            result
            for result in report.example_results
            if any(not passed for passed in result.metric_passed.values())
        ]

        if failed_examples:
            console.print("\n[bold red]Failed Examples[/bold red]")
            for result in failed_examples[:5]:
                failed_metrics = [
                    m for m, p in result.metric_passed.items() if not p
                ]
                console.print(f"  [yellow]{result.example_id}[/yellow]: {', '.join(failed_metrics)}")
                for metric_name in failed_metrics:
                    details = result.metric_details.get(metric_name, {})
                    console.print(f"    {metric_name}: {details.get('reasoning', str(details))}")

        # Cost summary
        console.print(
            Panel(
                f"Input Tokens: {report.total_input_tokens:,}\n"
                f"Output Tokens: {report.total_output_tokens:,}\n"
                f"Estimated Cost: ${report.estimated_cost_usd:.4f}\n"
                f"Duration: {report.run_duration_ms:.0f}ms",
                title="Cost Summary",
            )
        )

        # Regression alert
        if report.regression_flags:
            regression_text = "\n".join(
                [
                    f"  {flag['metric']}: {flag['baseline_score']:.3f} → {flag['current_score']:.3f} (↓{flag['drop_pct']}%)"
                    for flag in report.regression_flags
                ]
            )
            console.print(
                Panel(
                    regression_text,
                    title="[bold red]⚠ Regression Detected[/bold red]",
                    style="red",
                )
            )

    @staticmethod
    def load_golden_dataset(path: str) -> list[dict]:
        """Load golden dataset from JSON file.

        Args:
            path: Path to JSON file

        Returns:
            List of golden examples
        """
        with open(path, "r") as f:
            return json.load(f)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run CampaignPilot agent evaluations"
    )
    parser.add_argument(
        "--agent",
        choices=["strategist", "creative", "analyst", "optimizer"],
        required=True,
        help="Agent to evaluate",
    )
    parser.add_argument(
        "--dataset", type=str, required=True, help="Path to golden dataset JSON"
    )
    parser.add_argument(
        "--dataset-version", type=str, default="v1", help="Version of the dataset"
    )
    parser.add_argument(
        "--no-llm-judge",
        action="store_true",
        help="Skip LLM-as-judge metrics (faster/cheaper)",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to DB",
    )

    args = parser.parse_args()

    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from tools.vector_search import VectorSearchTool
    from tools.db_query import DBQueryTool
    from evals.metrics.deterministic import CompletenessMetric, BudgetRealismMetric, SqlAccuracyMetric, SafetyMetric

    vs = VectorSearchTool()
    db = DBQueryTool()

    if args.agent == "strategist":
        from agents.strategist import StrategistAgent
        from evals.metrics.llm_judge import StrategicCoherenceMetric
        agent = StrategistAgent(vector_search_tool=vs, db_query_tool=db)
        agent._eval_run_fn = lambda inp: agent.run_campaign_brief(**inp)
        metrics = [CompletenessMetric(), BudgetRealismMetric()]
        if not args.no_llm_judge:
            metrics.append(StrategicCoherenceMetric())

    elif args.agent == "creative":
        from agents.creative import CreativeAgent
        from evals.metrics.llm_judge import BrandVoiceMetric
        from evals.metrics.brand_safety import BrandSafetyMetric
        agent = CreativeAgent(vector_search_tool=vs, db_query_tool=db)
        agent._eval_run_fn = lambda inp: agent.run_creative_brief(**inp)
        from tools.safety_checker import SafetyChecker
        metrics = [SafetyMetric(SafetyChecker()), CompletenessMetric(), BrandSafetyMetric()]
        if not args.no_llm_judge:
            metrics.append(BrandVoiceMetric())

    elif args.agent == "analyst":
        from agents.analyst import AnalystAgent
        from evals.metrics.llm_judge import InsightQualityMetric
        agent = AnalystAgent(vector_search_tool=vs, db_query_tool=db)
        agent._eval_run_fn = lambda inp: agent.answer_question(**inp)
        metrics = [SqlAccuracyMetric(), CompletenessMetric()]
        if not args.no_llm_judge:
            metrics.append(InsightQualityMetric())

    elif args.agent == "optimizer":
        from agents.optimizer import OptimizerAgent
        from evals.metrics.llm_judge import StrategicCoherenceMetric
        agent = OptimizerAgent(vector_search_tool=vs, db_query_tool=db)
        agent._eval_run_fn = lambda inp: agent.optimize_campaign(**inp)
        metrics = [CompletenessMetric(), BudgetRealismMetric()]
        if not args.no_llm_judge:
            metrics.append(StrategicCoherenceMetric())

    else:
        console.print(f"[bold red]Unknown agent: {args.agent}[/bold red]")
        sys.exit(1)

    golden_dataset = EvalRunner.load_golden_dataset(args.dataset)
    runner = EvalRunner(db_query_tool=db)

    report = runner.run(
        agent=agent,
        golden_dataset=golden_dataset,
        metrics=metrics,
        agent_name=args.agent,
        dataset_version=args.dataset_version,
    )

    runner.print_report(report)

    if not args.no_save:
        saved = runner._save_to_db(report)
        if saved:
            console.print("[green]Results saved to DB.[/green]")
        else:
            console.print("[yellow]Could not save to DB (DATABASE_URL not set or connection failed).[/yellow]")

    sys.exit(0 if report.passed else 1)
