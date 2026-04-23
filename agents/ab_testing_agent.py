"""A/B Testing Stratification Agent.

Selects statistically valid test and control groups from the SMB advertiser pool.

The agent:
  1. Queries the smb_advertisers table for eligible SMBs
  2. Runs a power analysis to determine required sample sizes
  3. Stratifies the pool by industry, DMA tier, employee size bucket,
     and advertising experience
  4. Assigns test / control groups within each stratum (stratified random sampling)
  5. Validates balance across all covariates (chi-square for categorical,
     Welch's t-test for continuous)
  6. Persists the experiment to ab_experiments and ab_experiment_assignments
  7. Returns a structured ExperimentResult with all diagnostics
"""

from __future__ import annotations

import json
import logging
import math
import random
from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from scipy import stats
from agents.base_agent import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


# ─── Result dataclass ──────────────────────────────────────────────────────────

@dataclass
class ExperimentResult:
    """Output of a completed experiment design run."""
    experiment_id: Optional[int]
    experiment_name: str
    hypothesis: str

    pool_size: int
    test_size: int
    control_size: int

    # Power analysis
    required_n_per_group: int
    achieved_power: float
    significance_level: float
    minimum_detectable_effect: float
    mde_type: str

    # Balance diagnostics: {variable: {test_mean, control_mean, p_value, std_diff, balanced}}
    balance_diagnostics: dict[str, dict]
    overall_balance_passed: bool

    # Group assignments: list of {smb_id, group, stratum_key}
    assignments: list[dict]

    # Strata summary: {stratum_key: {total, test, control}}
    strata_summary: dict[str, dict]

    # Metadata
    stratification_variables: list[str]
    notes: str = ""
    success: bool = True
    error: Optional[str] = None


# ─── Statistical helpers ───────────────────────────────────────────────────────

def _power_analysis_two_proportions(
    p1: float,
    mde: float,
    alpha: float = 0.05,
    power: float = 0.80,
    mde_type: str = "relative",
) -> int:
    """Calculate required n per group for a two-proportion z-test.

    Args:
        p1: Baseline conversion proportion (e.g. 0.05 = 5%).
        mde: Minimum detectable effect. Relative: fraction change (0.20 = +20% lift).
             Absolute: absolute pp difference (0.02 = +2 pp).
        alpha: Type I error rate (default 0.05).
        power: Desired power 1-β (default 0.80).
        mde_type: 'relative' or 'absolute'.

    Returns:
        Required n per group (ceiling).
    """
    if mde_type == "relative":
        p2 = p1 * (1 + mde)
    else:
        p2 = p1 + mde

    p2 = min(0.99, max(0.01, p2))

    z_alpha = stats.norm.ppf(1 - alpha / 2)   # two-tailed
    z_beta = stats.norm.ppf(power)

    p_avg = (p1 + p2) / 2
    se_h0 = math.sqrt(2 * p_avg * (1 - p_avg))
    se_h1 = math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))

    n = ((z_alpha * se_h0 + z_beta * se_h1) / abs(p2 - p1)) ** 2
    return math.ceil(n)


def _achieved_power(
    n_per_group: int,
    p1: float,
    mde: float,
    alpha: float = 0.05,
    mde_type: str = "relative",
) -> float:
    """Calculate actual power given n per group."""
    if mde_type == "relative":
        p2 = p1 * (1 + mde)
    else:
        p2 = p1 + mde
    p2 = min(0.99, max(0.01, p2))

    z_alpha = stats.norm.ppf(1 - alpha / 2)
    p_avg = (p1 + p2) / 2
    se_h0 = math.sqrt(2 * p_avg * (1 - p_avg))
    se_h1 = math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))

    effect = abs(p2 - p1) * math.sqrt(n_per_group)
    ncp = effect / se_h1 if se_h1 > 0 else 0

    z_crit = z_alpha * se_h0 / se_h1 if se_h1 > 0 else z_alpha
    power = 1 - stats.norm.cdf(z_crit - ncp)
    return round(min(0.9999, max(0.0001, power)), 4)


def _size_bucket(employees: int) -> str:
    if employees <= 5:
        return "micro_1_5"
    elif employees <= 20:
        return "small_6_20"
    elif employees <= 50:
        return "medium_21_50"
    else:
        return "large_51_plus"


def _dma_tier(dma_code: int) -> str:
    top10 = {501, 803, 602, 504, 623, 539, 511, 618, 505, 524}
    mid = {561, 527, 548, 507, 613, 616, 534, 554, 532, 555,
           542, 528, 535, 659, 641, 581, 557, 560, 521, 619}
    if dma_code in top10:
        return "tier1_top10"
    elif dma_code in mid:
        return "tier2_mid"
    else:
        return "tier3_small"


def _balance_check_categorical(
    test_vals: list, control_vals: list, var_name: str
) -> dict:
    """Run chi-square test for balance on a categorical variable."""
    from collections import Counter
    cats = sorted(set(test_vals) | set(control_vals))
    test_counts = [Counter(test_vals).get(c, 0) for c in cats]
    ctrl_counts = [Counter(control_vals).get(c, 0) for c in cats]

    # Avoid zero-cell issues
    if sum(test_counts) == 0 or sum(ctrl_counts) == 0:
        return {"p_value": 1.0, "balanced": True, "test": {}, "control": {}}

    total_test = sum(test_counts)
    total_ctrl = sum(ctrl_counts)

    # Proportions
    test_props = {c: test_counts[i] / total_test for i, c in enumerate(cats)}
    ctrl_props = {c: ctrl_counts[i] / total_ctrl for i, c in enumerate(cats)}

    # Chi-square on raw counts
    contingency = np.array([test_counts, ctrl_counts])
    try:
        _, p_value, _, _ = stats.chi2_contingency(contingency)
    except ValueError:
        p_value = 1.0

    return {
        "p_value": round(float(p_value), 4),
        "balanced": p_value >= 0.05,
        "test_proportions": {k: round(v, 4) for k, v in test_props.items()},
        "control_proportions": {k: round(v, 4) for k, v in ctrl_props.items()},
    }


def _balance_check_continuous(
    test_vals: list, control_vals: list, var_name: str
) -> dict:
    """Run Welch's t-test for balance on a continuous variable."""
    if not test_vals or not control_vals:
        return {"p_value": 1.0, "balanced": True, "test_mean": 0.0, "control_mean": 0.0, "std_diff": 0.0}

    t_mean = float(np.mean(test_vals))
    c_mean = float(np.mean(control_vals))
    t_std = float(np.std(test_vals, ddof=1)) if len(test_vals) > 1 else 0.0
    c_std = float(np.std(control_vals, ddof=1)) if len(control_vals) > 1 else 0.0

    pooled_std = math.sqrt((t_std ** 2 + c_std ** 2) / 2) if (t_std > 0 or c_std > 0) else 1.0
    std_diff = abs(t_mean - c_mean) / pooled_std if pooled_std > 0 else 0.0

    try:
        _, p_value = stats.ttest_ind(test_vals, control_vals, equal_var=False)
    except Exception:
        p_value = 1.0

    return {
        "p_value": round(float(p_value), 4),
        "balanced": p_value >= 0.05 and std_diff < 0.20,  # ESSD < 0.2 = well balanced
        "test_mean": round(t_mean, 2),
        "control_mean": round(c_mean, 2),
        "standardized_diff": round(std_diff, 4),
    }


# ─── Core stratification logic ─────────────────────────────────────────────────

def _stratify_and_assign(
    pool: list[dict],
    test_fraction: float = 0.50,
    stratify_on: list[str] | None = None,
) -> tuple[list[dict], dict]:
    """Assign test/control within strata using proportional stratified sampling.

    Args:
        pool: List of SMB dicts with 'id', 'industry', 'dma_code',
              'employee_count', 'advertising_experience'.
        test_fraction: Fraction of each stratum to place in test (default 0.5).
        stratify_on: List of derived strata dimensions to use.

    Returns:
        (assignments, strata_summary)
        assignments: [{smb_id, group, stratum_key}]
        strata_summary: {stratum_key: {total, test, control}}
    """
    if stratify_on is None:
        stratify_on = ["industry", "size_bucket", "dma_tier", "advertising_experience"]

    # Build strata
    strata: dict[str, list[dict]] = {}
    for smb in pool:
        parts = []
        if "industry" in stratify_on:
            parts.append(smb["industry"].replace(" ", "_").replace("&", "and")[:20])
        if "size_bucket" in stratify_on:
            parts.append(_size_bucket(smb.get("employee_count", 5)))
        if "dma_tier" in stratify_on:
            parts.append(_dma_tier(smb.get("dma_code", 501)))
        if "advertising_experience" in stratify_on:
            parts.append(smb.get("advertising_experience", "none"))

        key = "__".join(parts)
        strata.setdefault(key, []).append(smb)

    assignments = []
    strata_summary = {}

    for key, members in strata.items():
        random.shuffle(members)
        n_test = max(1, round(len(members) * test_fraction))
        # Ensure at least 1 in control if stratum has ≥2 members
        if len(members) >= 2:
            n_test = min(n_test, len(members) - 1)

        for i, smb in enumerate(members):
            group = "test" if i < n_test else "control"
            assignments.append({
                "smb_id": smb["id"],
                "group": group,
                "stratum_key": key,
            })

        n_ctrl = len(members) - n_test
        strata_summary[key] = {
            "total": len(members),
            "test": n_test,
            "control": n_ctrl,
        }

    return assignments, strata_summary


# ─── Agent class ───────────────────────────────────────────────────────────────

class ABTestingAgent(BaseAgent):
    """Stratified A/B testing agent for Meta SMB advertiser pool.

    Workflow:
      1. Query SMB pool from Postgres (filtered by criteria)
      2. Run power analysis to validate sample sizes
      3. Stratified random assignment (industry × size × DMA tier × experience)
      4. Balance validation across all covariates
      5. Persist experiment to ab_experiments + ab_experiment_assignments
      6. Return ExperimentResult with full diagnostics

    This agent uses tools to query the DB; it does NOT call Claude for
    the statistical calculations — those are pure Python using scipy.stats.
    The LLM is used only to interpret the experiment design and generate
    a natural-language hypothesis and notes.
    """

    def __init__(
        self,
        db_query_tool: Any,
        model: str = "claude-sonnet-4-6",
        max_turns: int = 6,
        event_callback: Optional[Any] = None,
    ) -> None:
        super().__init__(model=model, max_turns=max_turns, langfuse_enabled=False, event_callback=event_callback)

        if not db_query_tool:
            raise ValueError("db_query_tool is required")
        if not hasattr(db_query_tool, "execute_query"):
            raise ValueError("db_query_tool must have execute_query() method")

        self.db = db_query_tool

    def get_system_prompt(self) -> str:
        return """You are an expert marketing data scientist specializing in experimental design for Meta SMB advertiser acquisition campaigns.

Your job is to design statistically rigorous A/B experiments on pools of small business advertisers. When given an experiment brief, you:
1. Confirm the experimental hypothesis is well-formed
2. Interpret the power analysis results and confirm sample adequacy
3. Validate the stratification strategy is appropriate for the business goal
4. Summarize the balance diagnostics — flag any imbalanced covariates
5. Produce a concise, plain-English experiment summary

Output ONLY valid JSON:
{
  "hypothesis": "string (well-formed If-Then-Because hypothesis)",
  "design_notes": "string (2-3 sentences on why this stratification + sample size is appropriate)",
  "balance_summary": "string (1-2 sentences: is the design balanced? which variables to watch?)",
  "risks": ["string (potential threats to validity)"],
  "recommendation": "string (proceed | revise | abort with reason)"
}"""

    def get_tools(self) -> list[dict]:
        return [
            {
                "name": "query_smb_pool",
                "description": "Query the SMB advertiser pool with optional filters. Returns count and sample.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "industry": {"type": "string", "description": "Filter by industry (optional)"},
                        "advertising_experience": {"type": "string", "description": "Filter by experience level (optional)"},
                        "has_run_meta_ads": {"type": "boolean", "description": "Filter by Meta ads history (optional)"},
                        "min_monthly_spend": {"type": "number", "description": "Minimum monthly ad spend filter (optional)"},
                        "limit": {"type": "integer", "description": "Max records to return for preview (default 5)", "default": 5},
                    },
                    "required": [],
                },
            },
        ]

    def _execute_tool(self, tool_name: str, tool_input: dict) -> Any:
        if tool_name == "query_smb_pool":
            conditions = ["1=1"]
            if tool_input.get("industry"):
                conditions.append(f"industry = '{tool_input['industry']}'")
            if tool_input.get("advertising_experience"):
                conditions.append(f"advertising_experience = '{tool_input['advertising_experience']}'")
            if tool_input.get("has_run_meta_ads") is not None:
                val = "TRUE" if tool_input["has_run_meta_ads"] else "FALSE"
                conditions.append(f"has_run_meta_ads = {val}")
            if tool_input.get("min_monthly_spend"):
                conditions.append(f"monthly_ad_spend_usd >= {tool_input['min_monthly_spend']}")

            where = " AND ".join(conditions)
            limit = tool_input.get("limit", 5)

            count_sql = f"SELECT COUNT(*) as cnt FROM smb_advertisers WHERE {where}"
            sample_sql = f"SELECT id, business_name, industry, state, dma_name, employee_count, advertising_experience FROM smb_advertisers WHERE {where} LIMIT {limit}"

            try:
                count_result = self.db.execute_query(count_sql)
                count = count_result[0]["cnt"] if count_result else 0
                sample = self.db.execute_query(sample_sql)
            except Exception as e:
                return {"error": str(e), "count": 0, "sample": []}

            return {"count": count, "sample": sample or []}
        raise ValueError(f"Unknown tool: {tool_name}")

    # ── Public API ──────────────────────────────────────────────────────────────

    def design_experiment(
        self,
        experiment_name: str,
        campaign_id: Optional[int] = None,
        filters: Optional[dict] = None,
        stratify_on: Optional[list[str]] = None,
        test_fraction: float = 0.50,
        baseline_conversion_rate: float = 0.05,
        minimum_detectable_effect: float = 0.20,
        mde_type: str = "relative",
        significance_level: float = 0.05,
        desired_power: float = 0.80,
        persist: bool = False,
    ) -> ExperimentResult:
        """Design a statistically valid A/B experiment on the SMB pool.

        Args:
            experiment_name: Human-readable name for the experiment.
            campaign_id: Optional campaign to link this experiment to.
            filters: Dict of filters for the SMB pool
                     (e.g. {"industry": "Restaurant & Food Service"}).
            stratify_on: Variables to stratify on. Default:
                         ["industry", "size_bucket", "dma_tier", "advertising_experience"].
            test_fraction: Fraction of pool assigned to test (default 0.50).
            baseline_conversion_rate: Estimated baseline conversion rate (default 5%).
            minimum_detectable_effect: MDE as relative (0.20 = 20% lift) or absolute pp.
            mde_type: 'relative' or 'absolute'.
            significance_level: α (default 0.05).
            desired_power: 1−β (default 0.80).
            persist: Whether to write the experiment to the DB.

        Returns:
            ExperimentResult with all diagnostics and assignments.
        """
        filters = filters or {}
        if stratify_on is None:
            stratify_on = ["industry", "size_bucket", "dma_tier", "advertising_experience"]

        # ── Step 1: Load the pool ──────────────────────────────────────────────
        pool = self._load_pool(filters)
        if not pool:
            return ExperimentResult(
                experiment_id=None,
                experiment_name=experiment_name,
                hypothesis="",
                pool_size=0, test_size=0, control_size=0,
                required_n_per_group=0, achieved_power=0.0,
                significance_level=significance_level,
                minimum_detectable_effect=minimum_detectable_effect,
                mde_type=mde_type,
                balance_diagnostics={}, overall_balance_passed=False,
                assignments=[], strata_summary={},
                stratification_variables=stratify_on,
                success=False,
                error="No SMBs found matching the given filters. Run seed_smbs.py first.",
            )

        # ── Step 2: Power analysis ─────────────────────────────────────────────
        required_n = _power_analysis_two_proportions(
            p1=baseline_conversion_rate,
            mde=minimum_detectable_effect,
            alpha=significance_level,
            power=desired_power,
            mde_type=mde_type,
        )
        n_per_group = len(pool) // 2
        achieved_pwr = _achieved_power(
            n_per_group=n_per_group,
            p1=baseline_conversion_rate,
            mde=minimum_detectable_effect,
            alpha=significance_level,
            mde_type=mde_type,
        )

        logger.info(
            f"Power analysis: required_n={required_n}/group, "
            f"available={n_per_group}/group, achieved_power={achieved_pwr:.3f}"
        )

        # ── Step 3: Stratified assignment ──────────────────────────────────────
        assignments, strata_summary = _stratify_and_assign(
            pool=pool,
            test_fraction=test_fraction,
            stratify_on=stratify_on,
        )

        test_ids = {a["smb_id"] for a in assignments if a["group"] == "test"}
        ctrl_ids = {a["smb_id"] for a in assignments if a["group"] == "control"}
        test_pool = [s for s in pool if s["id"] in test_ids]
        ctrl_pool = [s for s in pool if s["id"] in ctrl_ids]

        # ── Step 4: Balance diagnostics ────────────────────────────────────────
        balance = self._check_balance(test_pool, ctrl_pool)
        all_balanced = all(v.get("balanced", True) for v in balance.values())

        # ── Step 5: LLM interpretation ─────────────────────────────────────────
        llm_brief = self._build_llm_brief(
            experiment_name=experiment_name,
            pool_size=len(pool),
            test_size=len(test_pool),
            control_size=len(ctrl_pool),
            required_n=required_n,
            achieved_power=achieved_pwr,
            balance=balance,
            strata_summary=strata_summary,
        )
        agent_result: AgentResult = self.run(llm_brief)
        hypothesis = experiment_name
        notes = ""
        if agent_result.success and agent_result.output:
            hypothesis = agent_result.output.get("hypothesis", experiment_name)
            notes = agent_result.output.get("design_notes", "")

        # ── Step 6: Persist (optional) ─────────────────────────────────────────
        exp_id = None
        if persist:
            exp_id = self._persist_experiment(
                experiment_name=experiment_name,
                hypothesis=hypothesis,
                campaign_id=campaign_id,
                stratification_config={"stratify_on": stratify_on, "filters": filters},
                pool_size=len(pool),
                test_size=len(test_pool),
                control_size=len(ctrl_pool),
                significance_level=significance_level,
                desired_power=desired_power,
                mde=minimum_detectable_effect,
                mde_type=mde_type,
                required_n=required_n,
                achieved_power=achieved_pwr,
                balance=balance,
                assignments=assignments,
            )

        return ExperimentResult(
            experiment_id=exp_id,
            experiment_name=experiment_name,
            hypothesis=hypothesis,
            pool_size=len(pool),
            test_size=len(test_pool),
            control_size=len(ctrl_pool),
            required_n_per_group=required_n,
            achieved_power=achieved_pwr,
            significance_level=significance_level,
            minimum_detectable_effect=minimum_detectable_effect,
            mde_type=mde_type,
            balance_diagnostics=balance,
            overall_balance_passed=all_balanced,
            assignments=assignments,
            strata_summary=strata_summary,
            stratification_variables=stratify_on,
            notes=notes,
            success=True,
        )

    # ── Private helpers ─────────────────────────────────────────────────────────

    def _load_pool(self, filters: dict) -> list[dict]:
        """Load SMB pool from database with optional filters."""
        conditions = ["1=1"]
        if filters.get("industry"):
            conditions.append(f"industry = '{filters['industry']}'")
        if filters.get("advertising_experience"):
            conditions.append(f"advertising_experience = '{filters['advertising_experience']}'")
        if filters.get("has_run_meta_ads") is not None:
            val = "TRUE" if filters["has_run_meta_ads"] else "FALSE"
            conditions.append(f"has_run_meta_ads = {val}")
        if filters.get("exclude_existing_advertisers"):
            conditions.append("has_run_meta_ads = FALSE")

        where = " AND ".join(conditions)
        sql = f"""
            SELECT id, business_name, industry, sub_industry, state, dma_code, dma_name,
                   employee_count, annual_revenue_usd, business_age_years,
                   advertising_experience, monthly_ad_spend_usd,
                   has_run_meta_ads, facebook_page_followers, is_ecommerce, business_type
            FROM smb_advertisers
            WHERE {where}
            ORDER BY id
        """
        try:
            rows = self.db.execute_query(sql)
            return rows or []
        except Exception as e:
            logger.error(f"Failed to load SMB pool: {e}")
            return []

    def _check_balance(self, test: list[dict], ctrl: list[dict]) -> dict[str, dict]:
        """Run balance checks on all key covariates."""
        diagnostics = {}

        # Categorical covariates
        for var in ["industry", "advertising_experience", "business_type"]:
            t_vals = [r.get(var, "unknown") for r in test]
            c_vals = [r.get(var, "unknown") for r in ctrl]
            diagnostics[var] = _balance_check_categorical(t_vals, c_vals, var)

        # Size bucket (derived)
        t_buckets = [_size_bucket(r.get("employee_count", 5)) for r in test]
        c_buckets = [_size_bucket(r.get("employee_count", 5)) for r in ctrl]
        diagnostics["size_bucket"] = _balance_check_categorical(t_buckets, c_buckets, "size_bucket")

        # DMA tier (derived)
        t_tiers = [_dma_tier(r.get("dma_code", 501)) for r in test]
        c_tiers = [_dma_tier(r.get("dma_code", 501)) for r in ctrl]
        diagnostics["dma_tier"] = _balance_check_categorical(t_tiers, c_tiers, "dma_tier")

        # Continuous covariates
        for var in ["employee_count", "annual_revenue_usd", "monthly_ad_spend_usd"]:
            t_vals = [float(r.get(var, 0) or 0) for r in test]
            c_vals = [float(r.get(var, 0) or 0) for r in ctrl]
            diagnostics[var] = _balance_check_continuous(t_vals, c_vals, var)

        return diagnostics

    def _build_llm_brief(
        self,
        experiment_name: str,
        pool_size: int,
        test_size: int,
        control_size: int,
        required_n: int,
        achieved_power: float,
        balance: dict,
        strata_summary: dict,
    ) -> str:
        imbalanced = [k for k, v in balance.items() if not v.get("balanced", True)]
        top_strata = sorted(strata_summary.items(), key=lambda x: -x[1]["total"])[:5]
        strata_str = "; ".join(f"{k}={v['total']} (T:{v['test']}/C:{v['control']})" for k, v in top_strata)

        return f"""Review this A/B experiment design for: {experiment_name}

DESIGN SUMMARY:
- Total pool: {pool_size} SMBs
- Test group: {test_size} | Control group: {control_size}
- Required n per group (80% power, α=0.05, MDE=20% relative lift): {required_n}
- Achieved power with this sample: {achieved_power:.1%}
- Power adequate: {"YES" if achieved_power >= 0.80 else "WARNING: UNDERPOWERED"}

BALANCE DIAGNOSTICS:
- Imbalanced variables (p < 0.05): {imbalanced if imbalanced else "None — all balanced"}
- Balance checks run on: industry, advertising_experience, business_type, size_bucket, dma_tier, employee_count, annual_revenue_usd, monthly_ad_spend_usd

TOP STRATA:
{strata_str}

Based on this, generate the experiment output JSON with a well-formed hypothesis, design notes, balance summary, risks, and recommendation."""

    def _persist_experiment(
        self,
        experiment_name: str,
        hypothesis: str,
        campaign_id: Optional[int],
        stratification_config: dict,
        pool_size: int,
        test_size: int,
        control_size: int,
        significance_level: float,
        desired_power: float,
        mde: float,
        mde_type: str,
        required_n: int,
        achieved_power: float,
        balance: dict,
        assignments: list[dict],
    ) -> Optional[int]:
        """Insert experiment + assignments into the database."""
        try:
            # Insert experiment
            exp_sql = """
                INSERT INTO ab_experiments (
                    experiment_name, hypothesis, stratification_config,
                    total_pool_size, test_group_size, control_group_size,
                    significance_level, desired_power,
                    minimum_detectable_effect, mde_type,
                    required_sample_size_per_group, achieved_power,
                    balance_diagnostics, status
                ) VALUES (
                    %(name)s, %(hyp)s, %(sc)s,
                    %(pool)s, %(test)s, %(ctrl)s,
                    %(alpha)s, %(power)s,
                    %(mde)s, %(mde_type)s,
                    %(req_n)s, %(ach_pwr)s,
                    %(balance)s, 'active'
                ) RETURNING id
            """
            # We need a raw connection; db_query_tool.execute_query is SELECT-only in some impls
            # Use the underlying connection if available; otherwise skip persistence
            if not hasattr(self.db, "_conn") and not hasattr(self.db, "conn"):
                logger.warning("db_query_tool has no direct connection; skipping persistence")
                return None

            conn = getattr(self.db, "_conn", None) or getattr(self.db, "conn", None)
            if conn is None:
                return None

            import psycopg2.extras
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(exp_sql, {
                    "name": experiment_name,
                    "hyp": hypothesis,
                    "sc": json.dumps(stratification_config),
                    "pool": pool_size,
                    "test": test_size,
                    "ctrl": control_size,
                    "alpha": significance_level,
                    "power": desired_power,
                    "mde": mde,
                    "mde_type": mde_type,
                    "req_n": required_n,
                    "ach_pwr": achieved_power,
                    "balance": json.dumps(balance),
                })
                exp_id = cur.fetchone()["id"]

                # Insert assignments in batches
                assign_sql = """
                    INSERT INTO ab_experiment_assignments
                    (experiment_id, smb_advertiser_id, group_label, stratum_key)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """
                batch = [(exp_id, a["smb_id"], a["group"], a["stratum_key"]) for a in assignments]
                psycopg2.extras.execute_batch(cur, assign_sql, batch, page_size=200)
                conn.commit()
                logger.info(f"Persisted experiment id={exp_id} with {len(batch)} assignments")
                return exp_id
        except Exception as e:
            logger.error(f"Failed to persist experiment: {e}")
            return None


# ── CLI smoke test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import os
    import sys
    from dotenv import load_dotenv
    load_dotenv()

    class MockDB:
        """In-memory mock DB for smoke testing without a live Postgres."""

        def __init__(self):
            from data.synthetic.generate_smbs import generate_smbs
            self._data = generate_smbs(500)
            for i, row in enumerate(self._data):
                row["id"] = i + 1

        def execute_query(self, sql: str) -> list[dict]:
            sql_upper = sql.strip().upper()
            if "COUNT(*)" in sql_upper:
                return [{"cnt": len(self._data)}]
            return self._data[:500]

    try:
        from rich.console import Console
        from rich.table import Table
        console = Console()

        db = MockDB()
        agent = ABTestingAgent(db_query_tool=db)

        result = agent.design_experiment(
            experiment_name="Q3 SMB Acquisition — Restaurant & Food Service DMA Test",
            filters={"industry": "Restaurant & Food Service"},
            baseline_conversion_rate=0.05,
            minimum_detectable_effect=0.20,
            mde_type="relative",
            desired_power=0.80,
        )

        console.print("\n[bold cyan]═══ A/B Experiment Design Result ═══[/bold cyan]")
        console.print(f"[green]Experiment:[/green] {result.experiment_name}")
        console.print(f"[green]Hypothesis:[/green] {result.hypothesis}")
        console.print(f"[green]Pool size:[/green]  {result.pool_size}")
        console.print(f"[green]Test group:[/green] {result.test_size}  |  [green]Control:[/green] {result.control_size}")
        console.print(f"[green]Required n/group:[/green] {result.required_n_per_group}  |  [green]Achieved power:[/green] {result.achieved_power:.1%}")
        console.print(f"[green]Overall balance passed:[/green] {result.overall_balance_passed}")

        # Balance table
        tbl = Table(title="Balance Diagnostics", show_header=True, header_style="bold")
        tbl.add_column("Variable", style="cyan")
        tbl.add_column("p-value", justify="right")
        tbl.add_column("Balanced?", justify="center")
        for var, diag in result.balance_diagnostics.items():
            pval = diag.get("p_value", "-")
            balanced = "[green]YES[/green]" if diag.get("balanced", True) else "[red]NO[/red]"
            tbl.add_row(var, str(pval), balanced)
        console.print(tbl)

        if result.notes:
            console.print(f"\n[yellow]Design notes:[/yellow] {result.notes}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        sys.exit(1)
