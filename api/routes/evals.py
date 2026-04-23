"""Eval results routes for CampaignPilot API."""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/evals", tags=["evals"])
logger = logging.getLogger(__name__)


@router.get("/runs")
async def list_eval_runs(
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """List recent evaluation runs from the database."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        return db.get_eval_runs(agent_name=agent_name, limit=limit)
    except Exception as e:
        logger.warning(f"Could not fetch eval runs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_eval_run(run_id: int) -> dict:
    """Get a single eval run with full scores and summary."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        rows = db.execute_query("SELECT * FROM eval_runs WHERE id = %s", (run_id,))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        raise HTTPException(status_code=404, detail=f"Eval run {run_id} not found")

    return dict(rows[0])


@router.get("/agents/{agent_name}/latest")
async def get_latest_agent_scores(agent_name: str) -> dict:
    """
    Get the latest eval scores for a specific agent.

    Returns aggregate scores (mean, min, max, pass_rate) per metric from the most recent run.
    """
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        rows = db.execute_query(
            "SELECT * FROM eval_runs WHERE agent_name = %s ORDER BY run_at DESC LIMIT 1",
            (agent_name,),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        raise HTTPException(status_code=404, detail=f"No eval runs found for agent '{agent_name}'")

    run = dict(rows[0])
    return {
        "agent_name": agent_name,
        "run_id": run["id"],
        "run_at": str(run.get("run_at", "")),
        "scores": run.get("scores", {}),
        "summary": run.get("summary", {}),
        "total_tokens": run.get("total_tokens"),
        "estimated_cost_usd": run.get("estimated_cost_usd"),
    }


@router.get("/agents/{agent_name}/trend")
async def get_agent_score_trend(
    agent_name: str,
    metric: Optional[str] = Query(None, description="Filter to a single metric"),
    limit: int = Query(10, ge=1, le=50),
) -> list[dict]:
    """
    Get score trend over time for a specific agent (for dashboard charts).

    Returns list of {run_at, metric_name, mean_score} records.
    """
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        rows = db.get_eval_runs(agent_name=agent_name, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    trend = []
    for run in rows:
        scores = run.get("scores", {})
        for metric_name, metric_scores in scores.items():
            if metric and metric_name != metric:
                continue
            trend.append({
                "run_id": run.get("id"),
                "run_at": str(run.get("run_at", "")),
                "metric": metric_name,
                "mean_score": metric_scores.get("mean") if isinstance(metric_scores, dict) else metric_scores,
            })

    return trend
