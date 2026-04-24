"""PostgreSQL database query tools for CampaignPilot."""
from __future__ import annotations

import os
import logging
from typing import Any
from contextlib import contextmanager
import psycopg2
import psycopg2.extras
from psycopg2 import Error, ProgrammingError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class DBQueryTool:
    """PostgreSQL query tool for CampaignPilot database operations.

    Provides safe, parameterized query execution with connection pooling via
    context managers. Never uses string interpolation for user input.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize database query tool.

        Args:
            database_url: PostgreSQL connection string. Defaults to DATABASE_URL env var.
                          If neither is provided, the tool operates in no-op mode and
                          all queries return empty results without raising.
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            logger.warning("DATABASE_URL not set — DBQueryTool running in no-op mode")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections.

        Yields:
            psycopg2 connection with RealDictCursor.

        Raises:
            psycopg2.Error: On connection or execution failure.
        """
        conn = None
        try:
            conn = psycopg2.connect(self.database_url)
            conn.cursor_factory = psycopg2.extras.RealDictCursor
            yield conn
            conn.commit()
        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a safe SELECT query. Returns [] if no database is configured."""
        if not self.database_url:
            return []
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    results = cur.fetchall()
                    return [dict(row) for row in results] if results else []
        except ProgrammingError as e:
            logger.error(f"Query error (sanitized SQL): {sql[:100]}...: {e}")
            raise
        except Error as e:
            logger.error(f"Database error during query: {e}")
            raise

    def execute_write(
        self,
        sql: str,
        params: tuple[Any, ...] | None = None
    ) -> int:
        """Execute an INSERT, UPDATE, or DELETE query. Returns 0 if no database is configured."""
        if not self.database_url:
            return 0
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    rowcount = cur.rowcount
                    logger.debug(f"Write query affected {rowcount} rows")
                    return rowcount
        except ProgrammingError as e:
            logger.error(f"Write error (sanitized SQL): {sql[:100]}...: {e}")
            raise
        except Error as e:
            logger.error(f"Database error during write: {e}")
            raise

    def get_campaign_history(
        self,
        segment: str | None = None,
        channel: str | None = None,
        limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get campaign history with optional filtering.

        Args:
            segment: Optional segment name to filter by (ILIKE).
            channel: Optional channel name to filter by.
            limit: Maximum results to return.

        Returns:
            List of campaign records.
        """
        sql = "SELECT * FROM campaigns WHERE 1=1"
        params: list[Any] = []

        if segment:
            sql += " AND target_segment ILIKE %s"
            params.append(f"%{segment}%")

        if channel:
            sql += " AND %s = ANY(channels)"
            params.append(channel)

        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        return self.execute_query(sql, tuple(params))

    def get_performance_metrics(
        self,
        campaign_id: int | None = None,
        channel: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        group_by_channel: bool = False
    ) -> list[dict[str, Any]]:
        """Get performance metrics with optional filtering and aggregation.

        Args:
            campaign_id: Optional campaign ID to filter by.
            channel: Optional channel to filter by.
            date_from: Optional start date (ISO format).
            date_to: Optional end date (ISO format).
            group_by_channel: If True, group results by channel with aggregates.

        Returns:
            List of performance metric records with calculated CTR and ROAS.
        """
        if group_by_channel:
            sql = """
                SELECT
                    channel,
                    SUM(impressions) as total_impressions,
                    SUM(clicks) as total_clicks,
                    SUM(conversions) as total_conversions,
                    SUM(spend_usd) as total_spend,
                    SUM(revenue_usd) as total_revenue,
                    CASE WHEN SUM(clicks) > 0 THEN
                        ROUND(100.0 * SUM(conversions) / SUM(clicks), 2)
                    ELSE 0 END as ctr,
                    CASE WHEN SUM(spend_usd) > 0 THEN
                        ROUND(SUM(revenue_usd) / SUM(spend_usd), 2)
                    ELSE 0 END as roas
                FROM performance_events
                WHERE 1=1
            """
        else:
            sql = """
                SELECT
                    campaign_id,
                    channel,
                    impressions,
                    clicks,
                    conversions,
                    spend_usd,
                    revenue_usd,
                    CASE WHEN clicks > 0 THEN
                        ROUND(100.0 * conversions / clicks, 2)
                    ELSE 0 END as ctr,
                    CASE WHEN spend_usd > 0 THEN
                        ROUND(revenue_usd / spend_usd, 2)
                    ELSE 0 END as roas
                FROM performance_events
                WHERE 1=1
            """

        params: list[Any] = []

        if campaign_id is not None:
            sql += " AND campaign_id = %s"
            params.append(campaign_id)

        if channel:
            sql += " AND channel = %s"
            params.append(channel)

        if date_from:
            sql += " AND event_date >= %s"
            params.append(date_from)

        if date_to:
            sql += " AND event_date <= %s"
            params.append(date_to)

        if group_by_channel:
            sql += " GROUP BY channel ORDER BY total_spend DESC"
        else:
            sql += " ORDER BY event_date DESC"

        return self.execute_query(sql, tuple(params) if params else None)

    def save_eval_run(
        self,
        agent_name: str,
        golden_dataset_version: str,
        scores: dict[str, Any],
        summary: dict[str, Any],
        total_tokens: int,
        estimated_cost_usd: float
    ) -> int:
        """Save evaluation run results.

        Args:
            agent_name: Name of the agent being evaluated.
            golden_dataset_version: Version of the golden dataset used.
            scores: Dictionary of evaluation scores.
            summary: Summary of evaluation results.
            total_tokens: Total tokens used in evaluation.
            estimated_cost_usd: Estimated cost in USD.

        Returns:
            ID of the inserted evaluation run.
        """
        import json
        sql = """
            INSERT INTO eval_runs
            (agent_name, golden_dataset_version, scores, summary, total_tokens, estimated_cost_usd)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            agent_name,
            golden_dataset_version,
            json.dumps(scores),
            json.dumps(summary),
            total_tokens,
            estimated_cost_usd
        )

        results = self.execute_query(sql, params)
        return results[0]["id"] if results else -1

    def get_eval_runs(
        self,
        agent_name: str | None = None,
        limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent evaluation runs.

        Args:
            agent_name: Optional agent name to filter by.
            limit: Maximum results to return.

        Returns:
            List of evaluation run records.
        """
        sql = "SELECT * FROM eval_runs WHERE 1=1"
        params: list[Any] = []

        if agent_name:
            sql += " AND agent_name = %s"
            params.append(agent_name)

        sql += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        return self.execute_query(sql, tuple(params))

    def save_optimization_recommendation(
        self,
        campaign_id: int,
        recommendation_type: str,
        description: str,
        expected_impact: str
    ) -> int:
        """Save an optimization recommendation.

        Args:
            campaign_id: ID of the campaign being recommended.
            recommendation_type: Type of recommendation (e.g., "budget", "creative").
            description: Detailed description of the recommendation.
            expected_impact: Expected impact or benefit.

        Returns:
            ID of the inserted recommendation.
        """
        sql = """
            INSERT INTO optimization_recommendations
            (campaign_id, recommendation_type, description, expected_impact)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """
        params = (campaign_id, recommendation_type, description, expected_impact)

        results = self.execute_query(sql, params)
        return results[0]["id"] if results else -1
