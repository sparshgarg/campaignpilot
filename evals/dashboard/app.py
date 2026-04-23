"""CampaignPilot Eval Dashboard — Streamlit app for monitoring agent performance."""
import json
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
import psycopg2.extras
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="CampaignPilot Eval Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .status-pass { color: #28a745; font-weight: bold; }
    .status-fail { color: #dc3545; font-weight: bold; }
    .regression-alert { background-color: #fff3cd; padding: 15px; border-radius: 5px; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_db_connection():
    """Get PostgreSQL connection with caching."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        st.warning("DATABASE_URL not configured. Using mock data for demo.")
        return None

    try:
        return psycopg2.connect(db_url)
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None


def get_mock_eval_runs():
    """Return mock data for demo when DB is unavailable."""
    return pd.DataFrame(
        {
            "id": [1, 2, 3, 4, 5],
            "agent_name": ["strategist", "creative", "analyst", "strategist", "creative"],
            "dataset_version": ["v1", "v1", "v1", "v1", "v1"],
            "total_examples": [10, 10, 10, 10, 10],
            "passed": [True, True, False, True, True],
            "input_tokens": [15000, 12000, 18000, 16000, 13000],
            "output_tokens": [3500, 4200, 5100, 3800, 4000],
            "estimated_cost_usd": [0.0165, 0.0159, 0.0215, 0.0175, 0.0162],
            "duration_ms": [45000, 38000, 52000, 43000, 39000],
            "created_at": [
                datetime.now() - timedelta(days=3),
                datetime.now() - timedelta(days=2),
                datetime.now() - timedelta(days=1),
                datetime.now() - timedelta(hours=12),
                datetime.now(),
            ],
            "aggregate_scores": [
                json.dumps(
                    {
                        "strategic_coherence": {"mean": 3.8, "pass_rate": 0.9},
                        "completeness": {"mean": 0.85, "pass_rate": 0.8},
                        "budget_realism": {"mean": 0.75, "pass_rate": 0.7},
                    }
                ),
                json.dumps(
                    {
                        "brand_voice": {"mean": 3.6, "pass_rate": 0.85},
                        "brand_safety": {"mean": 0.95, "pass_rate": 0.95},
                        "completeness": {"mean": 0.9, "pass_rate": 0.9},
                    }
                ),
                json.dumps(
                    {
                        "insight_quality": {"mean": 2.8, "pass_rate": 0.6},
                        "sql_accuracy": {"mean": 0.65, "pass_rate": 0.5},
                        "completeness": {"mean": 0.75, "pass_rate": 0.7},
                    }
                ),
                json.dumps(
                    {
                        "strategic_coherence": {"mean": 3.9, "pass_rate": 0.95},
                        "completeness": {"mean": 0.88, "pass_rate": 0.85},
                        "budget_realism": {"mean": 0.78, "pass_rate": 0.75},
                    }
                ),
                json.dumps(
                    {
                        "brand_voice": {"mean": 3.7, "pass_rate": 0.9},
                        "brand_safety": {"mean": 0.98, "pass_rate": 1.0},
                        "completeness": {"mean": 0.92, "pass_rate": 0.95},
                    }
                ),
            ],
        }
    )


def fetch_eval_runs(conn=None, agent_filter=None, limit=20):
    """Fetch evaluation runs from database."""
    if conn is None:
        return get_mock_eval_runs()

    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        query = "SELECT * FROM eval_runs ORDER BY created_at DESC LIMIT %s"
        params = [limit]

        if agent_filter and agent_filter != "All Agents":
            query = "SELECT * FROM eval_runs WHERE agent_name = %s ORDER BY created_at DESC LIMIT %s"
            params = [agent_filter, limit]

        cur.execute(query, params)
        rows = cur.fetchall()

        data = []
        for row in rows:
            data.append(dict(row))

        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"Failed to fetch eval runs: {e}")
        return get_mock_eval_runs()


def detect_regressions(df):
    """Detect performance regressions across runs."""
    regressions = []

    agents = df["agent_name"].unique()

    for agent in agents:
        agent_df = df[df["agent_name"] == agent].sort_values("created_at")

        if len(agent_df) < 2:
            continue

        for idx in range(1, len(agent_df)):
            prev_row = agent_df.iloc[idx - 1]
            curr_row = agent_df.iloc[idx]

            prev_scores = json.loads(prev_row["aggregate_scores"])
            curr_scores = json.loads(curr_row["aggregate_scores"])

            for metric_name in prev_scores:
                if metric_name not in curr_scores:
                    continue

                prev_mean = prev_scores[metric_name].get("mean", 0.0)
                curr_mean = curr_scores[metric_name].get("mean", 0.0)

                if prev_mean > 0:
                    drop_pct = ((prev_mean - curr_mean) / prev_mean) * 100
                    if drop_pct > 5.0:
                        regressions.append(
                            {
                                "agent": agent,
                                "metric": metric_name,
                                "baseline": round(prev_mean, 3),
                                "current": round(curr_mean, 3),
                                "drop_pct": round(drop_pct, 1),
                                "timestamp": curr_row["created_at"],
                            }
                        )

    return regressions


def fetch_ab_experiments(conn=None):
    """Fetch A/B experiments from database."""
    if conn is None:
        return _mock_ab_experiments()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT id, experiment_name, status, total_pool_size,
                   test_group_size, control_group_size,
                   significance_level, desired_power, achieved_power,
                   minimum_detectable_effect, mde_type,
                   required_sample_size_per_group,
                   balance_diagnostics, created_at
            FROM ab_experiments
            ORDER BY created_at DESC
            LIMIT 20
        """)
        rows = [dict(r) for r in cur.fetchall()]
        return pd.DataFrame(rows) if rows else _mock_ab_experiments()
    except Exception:
        return _mock_ab_experiments()


def _mock_ab_experiments():
    """Return mock A/B experiments for demo mode."""
    return pd.DataFrame([
        {
            "id": 1,
            "experiment_name": "Q3 Restaurant SMB — Facebook Ads Onboarding",
            "status": "active",
            "total_pool_size": 90,
            "test_group_size": 45,
            "control_group_size": 45,
            "significance_level": 0.05,
            "desired_power": 0.80,
            "achieved_power": 0.83,
            "minimum_detectable_effect": 0.20,
            "mde_type": "relative",
            "required_sample_size_per_group": 197,
            "balance_diagnostics": json.dumps({
                "industry":                 {"p_value": 0.82, "balanced": True},
                "advertising_experience":   {"p_value": 0.71, "balanced": True},
                "business_type":            {"p_value": 0.94, "balanced": True},
                "size_bucket":              {"p_value": 0.65, "balanced": True},
                "dma_tier":                 {"p_value": 0.58, "balanced": True},
                "employee_count":           {"p_value": 0.43, "balanced": True, "test_mean": 9.2, "control_mean": 9.8},
                "annual_revenue_usd":       {"p_value": 0.38, "balanced": True, "test_mean": 450000, "control_mean": 465000},
                "monthly_ad_spend_usd":     {"p_value": 0.61, "balanced": True, "test_mean": 285, "control_mean": 292},
            }),
            "created_at": datetime.now() - timedelta(days=2),
        },
        {
            "id": 2,
            "experiment_name": "E-Commerce Advantage+ Upsell — Beginner Advertisers",
            "status": "active",
            "total_pool_size": 60,
            "test_group_size": 30,
            "control_group_size": 30,
            "significance_level": 0.05,
            "desired_power": 0.80,
            "achieved_power": 0.76,
            "minimum_detectable_effect": 0.25,
            "mde_type": "relative",
            "required_sample_size_per_group": 129,
            "balance_diagnostics": json.dumps({
                "industry":                 {"p_value": 0.91, "balanced": True},
                "advertising_experience":   {"p_value": 0.88, "balanced": True},
                "business_type":            {"p_value": 0.77, "balanced": True},
                "size_bucket":              {"p_value": 0.53, "balanced": True},
                "dma_tier":                 {"p_value": 0.49, "balanced": True},
                "employee_count":           {"p_value": 0.72, "balanced": True, "test_mean": 6.1, "control_mean": 6.4},
                "annual_revenue_usd":       {"p_value": 0.044, "balanced": False, "test_mean": 320000, "control_mean": 410000},
                "monthly_ad_spend_usd":     {"p_value": 0.82, "balanced": True, "test_mean": 190, "control_mean": 195},
            }),
            "created_at": datetime.now() - timedelta(days=5),
        },
    ])


def fetch_smb_distribution(conn=None):
    """Fetch SMB pool distribution stats."""
    if conn is None:
        return _mock_smb_distribution()
    try:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""
            SELECT industry, COUNT(*) as count,
                   AVG(annual_revenue_usd) as avg_revenue,
                   AVG(monthly_ad_spend_usd) as avg_monthly_spend
            FROM smb_advertisers
            GROUP BY industry ORDER BY count DESC
        """)
        rows = [dict(r) for r in cur.fetchall()]
        return pd.DataFrame(rows) if rows else _mock_smb_distribution()
    except Exception:
        return _mock_smb_distribution()


def _mock_smb_distribution():
    return pd.DataFrame([
        {"industry": "Restaurant & Food Service", "count": 90, "avg_revenue": 425000, "avg_monthly_spend": 310},
        {"industry": "Retail",                   "count": 70, "avg_revenue": 680000, "avg_monthly_spend": 520},
        {"industry": "E-Commerce",               "count": 60, "avg_revenue": 890000, "avg_monthly_spend": 790},
        {"industry": "Professional Services",    "count": 55, "avg_revenue": 750000, "avg_monthly_spend": 430},
        {"industry": "Home Services",            "count": 50, "avg_revenue": 380000, "avg_monthly_spend": 210},
        {"industry": "Health & Fitness",         "count": 40, "avg_revenue": 290000, "avg_monthly_spend": 185},
        {"industry": "Beauty & Personal Care",   "count": 40, "avg_revenue": 210000, "avg_monthly_spend": 130},
        {"industry": "Real Estate",              "count": 30, "avg_revenue": 620000, "avg_monthly_spend": 480},
        {"industry": "Automotive",               "count": 30, "avg_revenue": 990000, "avg_monthly_spend": 610},
        {"industry": "Travel & Hospitality",     "count": 35, "avg_revenue": 540000, "avg_monthly_spend": 350},
    ])


def render_ab_testing_tab(conn):
    """Render the A/B Testing & Measurement tab."""
    st.header("A/B Testing — Experiment Design & Results")
    st.markdown(
        "Stratified test/control group selection for Meta SMB advertiser acquisition experiments. "
        "Groups are assigned within strata (industry × size × DMA tier × ad experience) "
        "and validated for covariate balance using chi-square and Welch's t-tests."
    )

    # ── SMB Pool Overview ──────────────────────────────────────────────────────
    st.subheader("SMB Advertiser Pool")
    smb_df = fetch_smb_distribution(conn)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total SMBs in Pool", f"{smb_df['count'].sum():,}")
    with col2:
        st.metric("Industries Represented", len(smb_df))
    with col3:
        avg_rev = smb_df["avg_revenue"].mean()
        st.metric("Avg Annual Revenue", f"${avg_rev:,.0f}")
    with col4:
        avg_spend = smb_df["avg_monthly_spend"].mean()
        st.metric("Avg Monthly Ad Spend", f"${avg_spend:,.0f}")

    fig_pool = px.bar(
        smb_df,
        x="industry",
        y="count",
        color="avg_monthly_spend",
        color_continuous_scale="Blues",
        title="SMB Pool by Industry (color = avg monthly ad spend $)",
        labels={"count": "SMB Count", "industry": "Industry", "avg_monthly_spend": "Avg Monthly Spend ($)"},
        height=380,
    )
    fig_pool.update_xaxes(tickangle=30)
    st.plotly_chart(fig_pool, use_container_width=True)

    st.divider()

    # ── Experiment List ────────────────────────────────────────────────────────
    st.subheader("Experiments")
    exp_df = fetch_ab_experiments(conn)

    if exp_df.empty:
        st.info("No experiments found. Run `agents/ab_testing_agent.py` to design one.")
        return

    # Experiment selector
    exp_names = exp_df["experiment_name"].tolist()
    selected_name = st.selectbox("Select experiment", exp_names)
    exp = exp_df[exp_df["experiment_name"] == selected_name].iloc[0]

    # Experiment summary metrics
    st.subheader(f"Experiment: {selected_name}")
    st.caption(f"Status: **{exp['status']}** | Created: {pd.to_datetime(exp['created_at']).strftime('%Y-%m-%d')}")

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Pool Size", f"{int(exp['total_pool_size']):,}")
    with c2:
        st.metric("Test Group", f"{int(exp['test_group_size']):,}")
    with c3:
        st.metric("Control Group", f"{int(exp['control_group_size']):,}")
    with c4:
        ach = float(exp["achieved_power"]) if exp["achieved_power"] else 0.0
        req_n = int(exp["required_sample_size_per_group"]) if exp["required_sample_size_per_group"] else 0
        color = "normal" if ach >= 0.80 else "inverse"
        st.metric("Achieved Power", f"{ach:.1%}", delta=f"req. n={req_n}/grp", delta_color=color)
    with c5:
        mde = float(exp["minimum_detectable_effect"]) if exp["minimum_detectable_effect"] else 0.0
        mde_type = exp["mde_type"] or "relative"
        label = f"{mde:.0%} {mde_type}" if mde_type == "relative" else f"+{mde:.2f} pp"
        st.metric("Min Detectable Effect", label)

    # Power adequacy banner
    if ach < 0.80:
        st.warning(
            f"⚠️ **Underpowered**: achieved power {ach:.1%} < 80% target. "
            f"Need {req_n} per group but only have {int(exp['test_group_size'])}. "
            "Consider expanding pool filters or reducing MDE."
        )
    else:
        st.success(f"✅ **Adequately powered**: {ach:.1%} ≥ 80% threshold with {int(exp['test_group_size'])} per group.")

    st.divider()

    # ── Balance Diagnostics ────────────────────────────────────────────────────
    st.subheader("Covariate Balance Diagnostics")
    st.caption(
        "p-value < 0.05 indicates a statistically significant imbalance between test and control groups. "
        "All variables should be balanced (p ≥ 0.05) for a valid experiment."
    )

    raw_balance = exp["balance_diagnostics"]
    balance = json.loads(raw_balance) if isinstance(raw_balance, str) else (raw_balance or {})

    if balance:
        balance_rows = []
        for var, diag in balance.items():
            pval = diag.get("p_value", "-")
            balanced = diag.get("balanced", True)
            test_val = diag.get("test_mean", diag.get("test_proportions", "-"))
            ctrl_val = diag.get("control_mean", diag.get("control_proportions", "-"))
            balance_rows.append({
                "Variable": var.replace("_", " ").title(),
                "p-value": f"{pval:.4f}" if isinstance(pval, float) else str(pval),
                "Balanced": "✅ Yes" if balanced else "❌ No",
                "Test Value": f"{test_val:,.0f}" if isinstance(test_val, (int, float)) else str(test_val)[:40],
                "Control Value": f"{ctrl_val:,.0f}" if isinstance(ctrl_val, (int, float)) else str(ctrl_val)[:40],
            })

        balance_display = pd.DataFrame(balance_rows)
        st.dataframe(balance_display, use_container_width=True, hide_index=True)

        # p-value bar chart
        pvals = {
            r["Variable"]: float(r["p-value"]) if r["p-value"] not in ("-", "None") else 1.0
            for r in balance_rows
        }
        fig_bal = go.Figure()
        colors = ["green" if v >= 0.05 else "red" for v in pvals.values()]
        fig_bal.add_trace(go.Bar(
            x=list(pvals.keys()),
            y=list(pvals.values()),
            marker_color=colors,
            name="p-value",
        ))
        fig_bal.add_hline(y=0.05, line_dash="dash", line_color="orange",
                          annotation_text="α = 0.05 threshold")
        fig_bal.update_layout(
            title="Covariate Balance — p-values (green = balanced, red = imbalanced)",
            xaxis_title="Covariate",
            yaxis_title="p-value",
            height=380,
            showlegend=False,
        )
        st.plotly_chart(fig_bal, use_container_width=True)

    st.divider()

    # ── Group Size Visualization ───────────────────────────────────────────────
    st.subheader("Group Size Summary")
    col_left, col_right = st.columns(2)

    with col_left:
        fig_pie = go.Figure(data=[go.Pie(
            labels=["Test", "Control"],
            values=[int(exp["test_group_size"]), int(exp["control_group_size"])],
            hole=0.4,
            marker_colors=["#1877F2", "#E7E7E7"],
        )])
        fig_pie.update_layout(title="Test vs Control Split", height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_right:
        power_data = {
            "Metric": ["Pool Size", "Test Group", "Control Group", "Required n/group", "Power"],
            "Value": [
                f"{int(exp['total_pool_size']):,}",
                f"{int(exp['test_group_size']):,}",
                f"{int(exp['control_group_size']):,}",
                f"{int(exp['required_sample_size_per_group']):,}",
                f"{float(exp['achieved_power']):.1%}",
            ],
        }
        st.dataframe(pd.DataFrame(power_data), use_container_width=True, hide_index=True)

    # ── All Experiments Table ──────────────────────────────────────────────────
    st.divider()
    st.subheader("All Experiments")
    display_cols = ["experiment_name", "status", "total_pool_size",
                    "test_group_size", "control_group_size",
                    "achieved_power", "created_at"]
    exp_display = exp_df[display_cols].copy()
    exp_display["achieved_power"] = exp_display["achieved_power"].apply(
        lambda x: f"{float(x):.1%}" if x is not None else "—"
    )
    exp_display["created_at"] = pd.to_datetime(exp_display["created_at"]).dt.strftime("%Y-%m-%d")
    exp_display.columns = ["Experiment", "Status", "Pool", "Test", "Control", "Power", "Created"]
    st.dataframe(exp_display, use_container_width=True, hide_index=True)


def main():
    """Main dashboard app."""
    st.title("CampaignPilot — Measurement Dashboard")

    # Header with last updated time
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Agent eval scores, performance regressions, and A/B experiment results.")
    with col2:
        if st.button("Refresh"):
            st.rerun()
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Tabs
    tab_evals, tab_ab = st.tabs(["Agent Evals", "A/B Testing"])

    # Sidebar filters (shared)
    with st.sidebar:
        st.header("Filters")
        agent_filter = st.selectbox("Select Agent", ["All Agents", "strategist", "creative", "analyst", "optimizer"])
        days_back = st.slider("Days back", 1, 30, 7)

    # Connect to DB
    conn = get_db_connection()

    # ── A/B Testing tab ────────────────────────────────────────────────────────
    with tab_ab:
        render_ab_testing_tab(conn)

    # ── Eval Scores tab ────────────────────────────────────────────────────────
    with tab_evals:
        # Fetch evaluation runs
        df_runs = fetch_eval_runs(conn, agent_filter if agent_filter != "All Agents" else None, limit=50)

        # Filter by date
        if len(df_runs) > 0:
            df_runs["created_at"] = pd.to_datetime(df_runs["created_at"])
            cutoff_date = datetime.now() - timedelta(days=days_back)
            df_runs = df_runs[df_runs["created_at"] >= cutoff_date]

        # Regression alert
        if len(df_runs) > 0:
            regressions = detect_regressions(df_runs)
            if regressions:
                st.markdown('<div class="regression-alert">', unsafe_allow_html=True)
                st.warning("⚠️ Performance Regression Detected")
                regression_df = pd.DataFrame(regressions)
                st.dataframe(
                    regression_df[["agent", "metric", "baseline", "current", "drop_pct"]],
                    use_container_width=True,
                )
                st.markdown("</div>", unsafe_allow_html=True)

        # Latest scores
        st.header("Latest Scores by Agent")

        if len(df_runs) > 0:
            # Extract latest run per agent
            latest_per_agent = df_runs.sort_values("created_at").drop_duplicates("agent_name", keep="last")

            # Build scores dataframe
            score_data = []
            for _, row in latest_per_agent.iterrows():
                scores = json.loads(row["aggregate_scores"])
                for metric_name, metric_scores in scores.items():
                    score_data.append({
                        "agent": row["agent_name"],
                        "metric": metric_name,
                        "score": metric_scores.get("mean", 0.0),
                        "pass_rate": metric_scores.get("pass_rate", 0.0),
                    })

            df_scores = pd.DataFrame(score_data)
            fig = px.bar(
                df_scores, x="metric", y="score", color="agent", barmode="group",
                title="Latest Metric Scores by Agent",
                labels={"score": "Mean Score", "metric": "Metric"}, height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Score trends
            st.header("Score Trends Over Time")
            trend_data = []
            for _, row in df_runs.iterrows():
                scores = json.loads(row["aggregate_scores"])
                for metric_name, metric_scores in scores.items():
                    trend_data.append({
                        "timestamp": row["created_at"],
                        "agent": row["agent_name"],
                        "metric": metric_name,
                        "score": metric_scores.get("mean", 0.0),
                    })

            if trend_data:
                df_trends = pd.DataFrame(trend_data)
                selected_metric = st.selectbox("Select metric to track", df_trends["metric"].unique())
                df_metric_trends = df_trends[df_trends["metric"] == selected_metric]
                fig_trend = px.line(
                    df_metric_trends, x="timestamp", y="score", color="agent",
                    title=f"Trend: {selected_metric}",
                    labels={"score": "Mean Score", "timestamp": "Date"},
                    height=400, markers=True,
                )
                st.plotly_chart(fig_trend, use_container_width=True)

            # Cost tracking
            st.header("Cost Tracking")
            fig_cost = px.bar(
                df_runs, x="created_at", y="estimated_cost_usd", color="agent_name",
                title="Estimated Eval Cost Over Time",
                labels={"estimated_cost_usd": "Cost (USD)", "created_at": "Date", "agent_name": "Agent"},
                height=400,
            )
            st.plotly_chart(fig_cost, use_container_width=True)

            # Run history table
            st.header("Run History")
            display_columns = [
                "created_at", "agent_name", "dataset_version", "total_examples",
                "passed", "input_tokens", "output_tokens", "estimated_cost_usd", "duration_ms",
            ]
            display_df = df_runs[display_columns].copy()
            display_df["created_at"] = display_df["created_at"].dt.strftime("%Y-%m-%d %H:%M")
            display_df = display_df.rename(columns={
                "created_at": "Date", "agent_name": "Agent", "dataset_version": "Dataset",
                "total_examples": "Examples", "passed": "Passed",
                "input_tokens": "Input Tokens", "output_tokens": "Output Tokens",
                "estimated_cost_usd": "Cost ($)", "duration_ms": "Duration (ms)",
            })
            st.dataframe(display_df, use_container_width=True)

            # Summary metrics
            st.header("Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Runs", len(df_runs))
            with col2:
                st.metric("Passed Runs", df_runs["passed"].sum())
            with col3:
                st.metric("Total Cost", f"${df_runs['estimated_cost_usd'].sum():.4f}")
            with col4:
                st.metric("Avg Duration", f"{df_runs['duration_ms'].mean():.0f}ms")

        else:
            st.info("No evaluation runs found. Run evaluations to populate the dashboard.")

    # Footer
    st.divider()
    st.caption("CampaignPilot Measurement Dashboard | Powered by Streamlit & PostgreSQL")


if __name__ == "__main__":
    main()
