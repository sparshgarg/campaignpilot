"""Agent execution routes for CampaignPilot API."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import uuid
import json
import logging
from datetime import datetime, timezone
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/agents", tags=["agents"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class StrategistRunRequest(BaseModel):
    campaign_goal: str = Field(..., description="The campaign objective (e.g. 'Generate 50 MQLs for Lumen Pro from mid-market CFOs in Q4')")
    budget_usd: float = Field(..., gt=0, description="Total campaign budget in USD")
    timeline_days: int = Field(..., gt=0, le=365, description="Campaign duration in days")
    target_segment: str = Field(..., description="Target audience description")


class AgentRunResponse(BaseModel):
    run_id: str
    agent_name: str
    success: bool
    output: dict
    tool_calls_made: list[dict]
    total_input_tokens: int
    total_output_tokens: int
    latency_ms: float
    trace_url: str | None
    error: str | None
    timestamp: str


class CreativeRunRequest(BaseModel):
    channel: str = Field(..., description="Ad channel (e.g. 'facebook', 'instagram', 'reels')")
    product: str = Field(..., description="Product or service being advertised")
    persona: str = Field(..., description="Target persona name or description")
    tone: str = Field(..., description="Desired tone (e.g. 'friendly', 'professional', 'urgent')")
    key_message: str = Field(..., description="Core message or value proposition")
    num_variants: int = Field(3, ge=1, le=5, description="Number of creative variants to generate")


class AnalystRunRequest(BaseModel):
    question: str = Field(..., description="Natural-language analytics question (e.g. 'What is the ROAS by channel last 30 days?')")


class OptimizerRunRequest(BaseModel):
    campaign_id: int = Field(..., description="Campaign ID to optimize")
    campaign_name: str = Field(..., description="Campaign name for context")
    remaining_budget_usd: float = Field(..., gt=0, description="Remaining budget in USD")
    days_remaining: int = Field(..., gt=0, le=365, description="Days left in campaign flight")


class ABTestDesignRequest(BaseModel):
    experiment_name: str = Field(..., description="Human-readable experiment name")
    campaign_id: Optional[int] = Field(None, description="Optional linked campaign ID")
    filters: Optional[dict] = Field(None, description="SMB pool filters (e.g. {'industry': 'Restaurant & Food Service'})")
    stratify_on: Optional[list[str]] = Field(None, description="Stratification variables (defaults to industry, size_bucket, dma_tier, advertising_experience)")
    test_fraction: float = Field(0.50, ge=0.1, le=0.9, description="Fraction of eligible SMBs assigned to test group")
    baseline_conversion_rate: float = Field(0.05, gt=0, lt=1, description="Expected baseline conversion rate (proportion)")
    minimum_detectable_effect: float = Field(0.20, gt=0, description="Minimum detectable effect (relative or absolute)")
    mde_type: str = Field("relative", pattern="^(relative|absolute)$")
    desired_power: float = Field(0.80, ge=0.5, le=0.99)
    significance_level: float = Field(0.05, ge=0.01, le=0.20)
    persist: bool = Field(False, description="Persist experiment to database")


class EvalRunRequest(BaseModel):
    agent_name: str = Field(..., pattern="^(strategist|creative|analyst|optimizer)$")
    dataset_path: str = Field(..., description="Path to golden dataset JSON file")
    dataset_version: str = "v1"
    use_llm_judge: bool = True


class EvalRunResponse(BaseModel):
    eval_run_id: str
    status: str
    agent_name: str
    dataset_path: str
    message: str


# ---------------------------------------------------------------------------
# Background eval runner
# ---------------------------------------------------------------------------

_eval_results: dict[str, dict] = {}  # in-memory store for background eval results


def _run_eval_background(eval_run_id: str, request: EvalRunRequest) -> None:
    """Execute an eval run in the background and store results."""
    try:
        from evals.runner import EvalRunner
        from evals.metrics.deterministic import CompletenessMetric, BudgetRealismMetric
        from evals.metrics.llm_judge import StrategicCoherenceMetric
        from tools.vector_search import VectorSearchTool
        from tools.db_query import DBQueryTool

        vs = VectorSearchTool()
        db = DBQueryTool()

        if request.agent_name == "strategist":
            from agents.strategist import StrategistAgent
            agent = StrategistAgent(vector_search_tool=vs, db_query_tool=db)
            agent._eval_run_fn = lambda inp: agent.run_campaign_brief(**inp)
            metrics = [CompletenessMetric(), BudgetRealismMetric()]
            if request.use_llm_judge:
                metrics.append(StrategicCoherenceMetric())
        elif request.agent_name == "creative":
            from agents.creative import CreativeAgent
            from evals.metrics.deterministic import SafetyMetric
            from evals.metrics.llm_judge import BrandVoiceMetric
            from evals.metrics.brand_safety import BrandSafetyMetric
            agent = CreativeAgent(vector_search_tool=vs, db_query_tool=db)
            agent._eval_run_fn = lambda inp: agent.run_creative_brief(**inp)
            from tools.safety_checker import SafetyChecker
            metrics = [SafetyMetric(SafetyChecker()), CompletenessMetric(), BrandSafetyMetric()]
            if request.use_llm_judge:
                metrics.append(BrandVoiceMetric())
        elif request.agent_name == "analyst":
            from agents.analyst import AnalystAgent
            from evals.metrics.deterministic import SqlAccuracyMetric
            from evals.metrics.llm_judge import InsightQualityMetric
            agent = AnalystAgent(vector_search_tool=vs, db_query_tool=db)
            agent._eval_run_fn = lambda inp: agent.answer_question(**inp)
            metrics = [SqlAccuracyMetric(), CompletenessMetric()]
            if request.use_llm_judge:
                metrics.append(InsightQualityMetric())
        elif request.agent_name == "optimizer":
            from agents.optimizer import OptimizerAgent
            agent = OptimizerAgent(vector_search_tool=vs, db_query_tool=db)
            agent._eval_run_fn = lambda inp: agent.optimize_campaign(**inp)
            metrics = [CompletenessMetric(), BudgetRealismMetric()]
            if request.use_llm_judge:
                metrics.append(StrategicCoherenceMetric())
        else:
            _eval_results[eval_run_id] = {"status": "error", "error": f"Unknown agent: '{request.agent_name}'"}
            return

        golden_dataset = EvalRunner.load_golden_dataset(request.dataset_path)
        runner = EvalRunner(db_query_tool=db)
        report = runner.run(
            agent=agent,
            golden_dataset=golden_dataset,
            metrics=metrics,
            agent_name=request.agent_name,
            dataset_version=request.dataset_version,
        )

        _eval_results[eval_run_id] = {
            "status": "completed",
            "agent_name": report.agent_name,
            "total_examples": report.total_examples,
            "aggregate_scores": report.aggregate_scores,
            "passed": report.passed,
            "estimated_cost_usd": report.estimated_cost_usd,
            "run_duration_ms": report.run_duration_ms,
        }

    except Exception as e:
        logger.exception(f"Background eval run {eval_run_id} failed")
        _eval_results[eval_run_id] = {"status": "error", "error": str(e)}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/strategist/run", response_model=AgentRunResponse)
async def run_strategist(request: StrategistRunRequest) -> AgentRunResponse:
    """
    Run the Strategist agent to generate a campaign brief.

    The agent performs RAG over the knowledge base and past campaign history
    before producing a structured JSON brief with channel mix, budget split, KPIs, and rationale.
    """
    try:
        from tools.vector_search import VectorSearchTool
        from tools.db_query import DBQueryTool
        from agents.strategist import StrategistAgent

        vs = VectorSearchTool()
        db = DBQueryTool()
        agent = StrategistAgent(vector_search_tool=vs, db_query_tool=db)

        result = agent.run_campaign_brief(
            campaign_goal=request.campaign_goal,
            budget_usd=request.budget_usd,
            timeline_days=request.timeline_days,
            target_segment=request.target_segment,
        )

        run_id = str(uuid.uuid4())

        return AgentRunResponse(
            run_id=run_id,
            agent_name="strategist",
            success=result.success,
            output=result.output,
            tool_calls_made=result.tool_calls_made,
            total_input_tokens=result.total_input_tokens,
            total_output_tokens=result.total_output_tokens,
            latency_ms=result.latency_ms,
            trace_url=result.trace_url,
            error=result.error,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Strategist run failed")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.get("/strategist/run/{run_id}", response_model=AgentRunResponse)
async def get_strategist_run(run_id: str) -> AgentRunResponse:
    """
    Retrieve a stored Strategist run result by ID.

    Note: in this implementation, results are not persisted between API restarts.
    Integrate with Postgres for durable storage.
    """
    raise HTTPException(status_code=404, detail=f"Run {run_id} not found. Persistent storage not yet implemented.")


@router.post("/creative/run", response_model=AgentRunResponse)
async def run_creative(request: CreativeRunRequest) -> AgentRunResponse:
    """
    Run the Creative agent to generate ad copy variants.

    Produces structured JSON with headline, body, CTA, and brand-safety flags
    for the requested channel, product, and persona combination.
    """
    try:
        from tools.vector_search import VectorSearchTool
        from tools.db_query import DBQueryTool
        from agents.creative import CreativeAgent

        vs = VectorSearchTool()
        db = DBQueryTool()
        agent = CreativeAgent(vector_search_tool=vs, db_query_tool=db)

        result = agent.run_creative_brief(
            channel=request.channel,
            product=request.product,
            persona=request.persona,
            tone=request.tone,
            key_message=request.key_message,
            num_variants=request.num_variants,
        )

        return AgentRunResponse(
            run_id=str(uuid.uuid4()),
            agent_name="creative",
            success=result.success,
            output=result.output,
            tool_calls_made=result.tool_calls_made,
            total_input_tokens=result.total_input_tokens,
            total_output_tokens=result.total_output_tokens,
            latency_ms=result.latency_ms,
            trace_url=result.trace_url,
            error=result.error,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Creative run failed")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/analyst/run", response_model=AgentRunResponse)
async def run_analyst(request: AnalystRunRequest) -> AgentRunResponse:
    """
    Run the Analyst agent to answer a natural-language analytics question.

    The agent translates the question to SQL, executes it against the campaigns DB,
    and returns a structured narrative with supporting data.
    """
    try:
        from tools.vector_search import VectorSearchTool
        from tools.db_query import DBQueryTool
        from agents.analyst import AnalystAgent

        vs = VectorSearchTool()
        db = DBQueryTool()
        agent = AnalystAgent(vector_search_tool=vs, db_query_tool=db)

        result = agent.answer_question(question=request.question)

        return AgentRunResponse(
            run_id=str(uuid.uuid4()),
            agent_name="analyst",
            success=result.success,
            output=result.output,
            tool_calls_made=result.tool_calls_made,
            total_input_tokens=result.total_input_tokens,
            total_output_tokens=result.total_output_tokens,
            latency_ms=result.latency_ms,
            trace_url=result.trace_url,
            error=result.error,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Analyst run failed")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/optimizer/run", response_model=AgentRunResponse)
async def run_optimizer(request: OptimizerRunRequest) -> AgentRunResponse:
    """
    Run the Optimizer agent to generate budget reallocation recommendations.

    Compares current campaign performance against Meta benchmarks and produces
    a structured JSON action plan with channel-level budget adjustments.
    """
    try:
        from tools.vector_search import VectorSearchTool
        from tools.db_query import DBQueryTool
        from agents.optimizer import OptimizerAgent

        vs = VectorSearchTool()
        db = DBQueryTool()
        agent = OptimizerAgent(vector_search_tool=vs, db_query_tool=db)

        result = agent.optimize_campaign(
            campaign_id=request.campaign_id,
            campaign_name=request.campaign_name,
            remaining_budget_usd=request.remaining_budget_usd,
            days_remaining=request.days_remaining,
        )

        return AgentRunResponse(
            run_id=str(uuid.uuid4()),
            agent_name="optimizer",
            success=result.success,
            output=result.output,
            tool_calls_made=result.tool_calls_made,
            total_input_tokens=result.total_input_tokens,
            total_output_tokens=result.total_output_tokens,
            latency_ms=result.latency_ms,
            trace_url=result.trace_url,
            error=result.error,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:
        logger.exception("Optimizer run failed")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")


@router.post("/ab-test/design")
async def design_ab_experiment(request: ABTestDesignRequest) -> dict:
    """
    Design a statistically valid A/B experiment using the SMB advertiser pool.

    Performs power analysis, stratified group assignment, and covariate balance
    validation. Returns an ExperimentResult with full diagnostics.
    """
    try:
        from tools.db_query import DBQueryTool
        from agents.ab_testing_agent import ABTestingAgent

        db = DBQueryTool()
        agent = ABTestingAgent(db_query_tool=db)

        result = agent.design_experiment(
            experiment_name=request.experiment_name,
            campaign_id=request.campaign_id,
            filters=request.filters,
            stratify_on=request.stratify_on,
            test_fraction=request.test_fraction,
            baseline_conversion_rate=request.baseline_conversion_rate,
            minimum_detectable_effect=request.minimum_detectable_effect,
            mde_type=request.mde_type,
            desired_power=request.desired_power,
            significance_level=request.significance_level,
            persist=request.persist,
        )

        from dataclasses import asdict
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **asdict(result),
        }

    except Exception as e:
        logger.exception("AB test design failed")
        raise HTTPException(status_code=500, detail=f"Experiment design failed: {str(e)}")


@router.post("/eval/run", response_model=EvalRunResponse)
async def trigger_eval_run(request: EvalRunRequest, background_tasks: BackgroundTasks) -> EvalRunResponse:
    """
    Trigger an evaluation run for a specified agent against a golden dataset.

    Runs asynchronously in the background. Poll GET /agents/eval/status/{eval_run_id}
    to check completion status.
    """
    import os
    if not os.path.exists(request.dataset_path):
        raise HTTPException(status_code=400, detail=f"Dataset not found: {request.dataset_path}")

    eval_run_id = str(uuid.uuid4())
    _eval_results[eval_run_id] = {"status": "running"}

    background_tasks.add_task(_run_eval_background, eval_run_id, request)

    return EvalRunResponse(
        eval_run_id=eval_run_id,
        status="started",
        agent_name=request.agent_name,
        dataset_path=request.dataset_path,
        message=f"Eval run started. Poll GET /agents/eval/status/{eval_run_id} for results.",
    )


@router.get("/eval/status/{eval_run_id}")
async def get_eval_status(eval_run_id: str) -> dict:
    """Get the status and results of a background eval run."""
    if eval_run_id not in _eval_results:
        raise HTTPException(status_code=404, detail=f"Eval run {eval_run_id} not found")
    return {"eval_run_id": eval_run_id, **_eval_results[eval_run_id]}


@router.get("/eval/runs")
async def list_eval_runs(limit: int = 20) -> list[dict]:
    """List recent eval runs from the database."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        return db.get_eval_runs(limit=limit)
    except Exception as e:
        logger.warning(f"Could not fetch eval runs from DB: {e}")
        return []
