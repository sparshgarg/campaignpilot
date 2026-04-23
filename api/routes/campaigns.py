"""Campaign CRUD routes for CampaignPilot API."""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

router = APIRouter(prefix="/campaigns", tags=["campaigns"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    goal: str = Field(..., description="Campaign objective")
    target_segment: str = Field(..., description="Target audience description")
    budget_usd: float = Field(..., gt=0)
    start_date: date
    end_date: date
    channels: list[str] = Field(..., min_length=1)


class CampaignResponse(BaseModel):
    id: int
    name: str
    goal: str
    target_segment: str
    budget_usd: float
    start_date: str
    end_date: str
    status: str
    channels: list[str]
    created_at: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=list[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = Query(None, description="Filter by status (draft, active, completed)"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CampaignResponse]:
    """List campaigns with optional status filter and pagination."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()

        if status:
            rows = db.execute_query(
                "SELECT * FROM campaigns WHERE status = %s ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (status, limit, offset),
            )
        else:
            rows = db.execute_query(
                "SELECT * FROM campaigns ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset),
            )

        return [
            CampaignResponse(
                id=r["id"],
                name=r["name"],
                goal=r.get("goal", ""),
                target_segment=r.get("target_segment", ""),
                budget_usd=float(r.get("budget_usd", 0)),
                start_date=str(r.get("start_date", "")),
                end_date=str(r.get("end_date", "")),
                status=r.get("status", "draft"),
                channels=list(r.get("channels", [])),
                created_at=str(r.get("created_at", "")),
            )
            for r in rows
        ]

    except Exception as e:
        logger.exception("Failed to list campaigns")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(payload: CampaignCreate) -> CampaignResponse:
    """Create a new campaign record."""
    if payload.end_date <= payload.start_date:
        raise HTTPException(status_code=400, detail="end_date must be after start_date")

    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()

        rows = db.execute_query(
            """
            INSERT INTO campaigns (name, goal, target_segment, budget_usd, start_date, end_date, channels)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                payload.name,
                payload.goal,
                payload.target_segment,
                payload.budget_usd,
                payload.start_date,
                payload.end_date,
                payload.channels,
            ),
        )

        r = rows[0]
        return CampaignResponse(
            id=r["id"],
            name=r["name"],
            goal=r.get("goal", ""),
            target_segment=r.get("target_segment", ""),
            budget_usd=float(r.get("budget_usd", 0)),
            start_date=str(r.get("start_date", "")),
            end_date=str(r.get("end_date", "")),
            status=r.get("status", "draft"),
            channels=list(r.get("channels", [])),
            created_at=str(r.get("created_at", "")),
        )

    except Exception as e:
        logger.exception("Failed to create campaign")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: int) -> CampaignResponse:
    """Get a single campaign by ID."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        rows = db.execute_query("SELECT * FROM campaigns WHERE id = %s", (campaign_id,))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not rows:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")

    r = rows[0]
    return CampaignResponse(
        id=r["id"],
        name=r["name"],
        goal=r.get("goal", ""),
        target_segment=r.get("target_segment", ""),
        budget_usd=float(r.get("budget_usd", 0)),
        start_date=str(r.get("start_date", "")),
        end_date=str(r.get("end_date", "")),
        status=r.get("status", "draft"),
        channels=list(r.get("channels", [])),
        created_at=str(r.get("created_at", "")),
    )


@router.get("/{campaign_id}/performance")
async def get_campaign_performance(
    campaign_id: int,
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
) -> dict:
    """Get aggregated performance metrics for a campaign."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        metrics = db.get_performance_metrics(
            campaign_id=campaign_id,
            date_from=date_from,
            date_to=date_to,
            group_by_channel=True,
        )
        return {"campaign_id": campaign_id, "performance": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}/creatives")
async def get_campaign_creatives(campaign_id: int) -> dict:
    """Get all creative variants for a campaign."""
    try:
        from tools.db_query import DBQueryTool
        db = DBQueryTool()
        rows = db.execute_query(
            "SELECT * FROM creatives WHERE campaign_id = %s ORDER BY channel, variant_index",
            (campaign_id,),
        )
        return {"campaign_id": campaign_id, "creatives": [dict(r) for r in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
