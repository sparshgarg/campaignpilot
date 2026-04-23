"""CampaignPilot — Premium multi-agent control center.

Design: Gong.io energy + Meta minimalism.
Bento box layout · Bold gradients · Glassmorphism · Smooth interactions.
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="CampaignPilot",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# DESIGN SYSTEM · Premium CSS
# ============================================================================
st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">

<style>
    /* ====================================================================
       RESET & BASE
       ==================================================================== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }

    /* Main app background */
    .stApp {
        background: #F8F9FA;
    }

    /* Hide Streamlit branding */
    #MainMenu, footer, header[data-testid="stHeader"] {
        visibility: hidden;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    /* Hide sidebar toggle initially */
    [data-testid="collapsedControl"] {
        display: none;
    }

    /* ====================================================================
       TYPOGRAPHY
       ==================================================================== */
    h1, h2, h3, h4 {
        font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
        font-weight: 800;
        letter-spacing: -0.03em;
        color: #0A0A0A;
        line-height: 1.1;
    }

    /* Hero text */
    .hero-title {
        font-size: 72px;
        font-weight: 900;
        letter-spacing: -0.04em;
        line-height: 0.95;
        color: #0A0A0A;
        margin: 0;
    }

    .hero-title-gradient {
        background: linear-gradient(135deg, #6366F1 0%, #EC4899 50%, #F59E0B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .hero-subtitle {
        font-size: 18px;
        color: #6B7280;
        font-weight: 400;
        line-height: 1.5;
        max-width: 600px;
        margin-top: 24px;
    }

    .eyebrow {
        display: inline-block;
        padding: 6px 14px;
        background: rgba(99, 102, 241, 0.08);
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        color: #6366F1;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* ====================================================================
       GLASSMORPHISM NAVBAR
       ==================================================================== */
    .glass-nav {
        position: sticky;
        top: 0;
        z-index: 100;
        background: rgba(255, 255, 255, 0.72);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(229, 231, 235, 0.5);
        border-radius: 16px;
        padding: 16px 24px;
        margin-bottom: 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .nav-logo {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 20px;
        font-weight: 800;
        color: #0A0A0A;
        letter-spacing: -0.02em;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .nav-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        background: #10B981;
        color: white;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
    }

    /* ====================================================================
       BENTO BOX GRID
       ==================================================================== */
    .bento-grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 16px;
        margin: 32px 0;
    }

    .bento-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 24px;
        padding: 28px;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
        position: relative;
        overflow: hidden;
    }

    .bento-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.1);
        border-color: #D1D5DB;
    }

    /* Gradient accent cards */
    .bento-card-gradient {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
        color: white;
        border: none;
    }

    .bento-card-gradient h3, .bento-card-gradient p {
        color: white !important;
    }

    .bento-card-dark {
        background: #0A0A0A;
        color: white;
        border: none;
    }

    .bento-card-dark h3 { color: white !important; }
    .bento-card-dark p { color: #A1A1AA !important; }

    /* ====================================================================
       FLOATING ELEMENTS (Gong style)
       ==================================================================== */
    .floating-card {
        position: absolute;
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 16px 20px;
        box-shadow: 0 20px 50px -15px rgba(0, 0, 0, 0.15);
        animation: float 6s ease-in-out infinite;
    }

    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }

    .pulse-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4);
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.6); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* ====================================================================
       AGENT SELECTOR CARDS
       ==================================================================== */
    .agent-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 24px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        height: 100%;
    }

    .agent-card:hover {
        transform: translateY(-4px);
        border-color: #6366F1;
        box-shadow: 0 16px 40px -12px rgba(99, 102, 241, 0.25);
    }

    .agent-card.active {
        border-color: #6366F1;
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%);
        box-shadow: 0 16px 40px -12px rgba(99, 102, 241, 0.2);
    }

    .agent-icon {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        margin-bottom: 16px;
    }

    .icon-indigo { background: linear-gradient(135deg, #6366F1, #8B5CF6); color: white; }
    .icon-pink { background: linear-gradient(135deg, #EC4899, #F43F5E); color: white; }
    .icon-cyan { background: linear-gradient(135deg, #06B6D4, #3B82F6); color: white; }
    .icon-amber { background: linear-gradient(135deg, #F59E0B, #EF4444); color: white; }
    .icon-emerald { background: linear-gradient(135deg, #10B981, #14B8A6); color: white; }

    .agent-card-title {
        font-size: 18px;
        font-weight: 700;
        color: #0A0A0A;
        margin: 0 0 8px 0;
        letter-spacing: -0.01em;
    }

    .agent-card-desc {
        font-size: 13px;
        color: #6B7280;
        line-height: 1.5;
        margin: 0;
    }

    /* ====================================================================
       METRIC CARDS
       ==================================================================== */
    .metric-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 24px;
        transition: all 0.2s ease-in-out;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 24px -10px rgba(0, 0, 0, 0.08);
    }

    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }

    .metric-value {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 36px;
        font-weight: 800;
        color: #0A0A0A;
        letter-spacing: -0.03em;
        line-height: 1;
    }

    .metric-delta {
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .delta-up { color: #10B981; }
    .delta-down { color: #EF4444; }

    /* ====================================================================
       BUTTONS
       ==================================================================== */
    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white !important;
        border: none;
        border-radius: 14px;
        font-weight: 700;
        font-size: 15px;
        padding: 14px 28px;
        letter-spacing: -0.01em;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 8px 20px -5px rgba(99, 102, 241, 0.4);
        width: 100%;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 30px -5px rgba(99, 102, 241, 0.5);
        background: linear-gradient(135deg, #5558E3 0%, #7C3AED 100%);
        color: white !important;
    }

    .stButton > button:active {
        transform: translateY(0px);
    }

    /* ====================================================================
       FORM INPUTS
       ==================================================================== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: white !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 12px !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        color: #0A0A0A !important;
        transition: all 0.2s ease-in-out !important;
    }

    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1) !important;
    }

    /* Slider */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #6366F1, #8B5CF6) !important;
    }

    /* Labels */
    .stTextInput label, .stNumberInput label,
    .stTextArea label, .stSlider label, .stSelectbox label {
        font-size: 13px !important;
        font-weight: 600 !important;
        color: #374151 !important;
        margin-bottom: 6px !important;
    }

    /* ====================================================================
       TOOL CALL DISPLAY
       ==================================================================== */
    .tool-call-card {
        background: #FAFAFA;
        border: 1px solid #E5E7EB;
        border-radius: 16px;
        padding: 16px 20px;
        margin-bottom: 12px;
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
        font-size: 13px;
        transition: all 0.2s ease-in-out;
    }

    .tool-call-card:hover {
        border-color: #6366F1;
        background: white;
    }

    /* ====================================================================
       STATUS BADGES
       ==================================================================== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.01em;
    }

    .badge-success {
        background: rgba(16, 185, 129, 0.1);
        color: #059669;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .badge-warning {
        background: rgba(245, 158, 11, 0.1);
        color: #D97706;
        border: 1px solid rgba(245, 158, 11, 0.2);
    }

    .badge-error {
        background: rgba(239, 68, 68, 0.1);
        color: #DC2626;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }

    .badge-info {
        background: rgba(99, 102, 241, 0.1);
        color: #4F46E5;
        border: 1px solid rgba(99, 102, 241, 0.2);
    }

    /* ====================================================================
       OUTPUT CARDS
       ==================================================================== */
    .output-card {
        background: white;
        border: 1px solid #E5E7EB;
        border-radius: 20px;
        padding: 28px;
        margin-bottom: 20px;
        transition: all 0.2s ease-in-out;
    }

    .output-card:hover {
        box-shadow: 0 16px 40px -15px rgba(0, 0, 0, 0.08);
    }

    .output-card-title {
        font-size: 12px;
        font-weight: 600;
        color: #6B7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* ====================================================================
       EXPANDERS
       ==================================================================== */
    .streamlit-expanderHeader {
        background: white !important;
        border: 1px solid #E5E7EB !important;
        border-radius: 14px !important;
        font-weight: 600 !important;
    }

    /* ====================================================================
       DIVIDERS
       ==================================================================== */
    hr {
        border: none !important;
        border-top: 1px solid #E5E7EB !important;
        margin: 32px 0 !important;
    }

    /* ====================================================================
       JSON CODE BLOCKS
       ==================================================================== */
    pre, code {
        font-family: 'SF Mono', 'Monaco', 'Consolas', monospace !important;
        font-size: 12px !important;
        border-radius: 12px !important;
    }

    /* ====================================================================
       HIDE SOME DEFAULT STREAMLIT ELEMENTS
       ==================================================================== */
    [data-testid="stToolbar"] {
        visibility: hidden;
    }

    .element-container {
        margin-bottom: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE
# ============================================================================
if "current_agent" not in st.session_state:
    st.session_state.current_agent = None
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ============================================================================
# TOOLS (cached)
# ============================================================================
@st.cache_resource
def get_tools():
    from tools.vector_search import VectorSearchTool
    from tools.db_query import DBQueryTool
    return VectorSearchTool(), DBQueryTool()


# ============================================================================
# GLASSMORPHISM NAVBAR
# ============================================================================
st.markdown(f"""
<div class="glass-nav">
    <div class="nav-logo">
        <span style="font-size: 26px;">◆</span>
        CampaignPilot
    </div>
    <div style="display: flex; align-items: center; gap: 16px;">
        <span class="status-badge badge-success">
            <span class="pulse-dot"></span> All Systems Live
        </span>
        <span style="font-size: 13px; color: #6B7280;">{datetime.now().strftime('%b %d, %Y')}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# HERO SECTION
# ============================================================================
if st.session_state.current_agent is None:
    col_hero, col_float = st.columns([1.4, 1])

    with col_hero:
        st.markdown(f"""
        <div style="padding-top: 40px;">
            <span class="eyebrow">◆ Multi-Agent Orchestration</span>
            <h1 class="hero-title">
                Campaigns that<br>
                <span class="hero-title-gradient">think for themselves.</span>
            </h1>
            <p class="hero-subtitle">
                Five specialized AI agents coordinate to plan, create, analyze, and optimize marketing campaigns—with full observability over every decision, tool call, and token.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_float:
        st.markdown("""
        <div style="position: relative; height: 400px; padding-top: 40px;">
            <div class="floating-card" style="top: 20px; right: 0px; width: 240px; animation-delay: 0s;">
                <div style="font-size: 11px; color: #6B7280; font-weight: 600; margin-bottom: 6px;">ROAS · Q4</div>
                <div style="font-size: 28px; font-weight: 800; color: #0A0A0A; letter-spacing: -0.02em;">3.42<span style="color: #10B981; font-size: 14px;">↑ 18%</span></div>
                <div style="font-size: 11px; color: #6B7280; margin-top: 4px;">vs. benchmark 2.19</div>
            </div>
            <div class="floating-card" style="top: 160px; right: 60px; width: 260px; animation-delay: 1.5s;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <div style="width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg, #6366F1, #EC4899); display: flex; align-items: center; justify-content: center; color: white; font-weight: 800;">S</div>
                    <div style="flex: 1;">
                        <div style="font-size: 12px; font-weight: 600; color: #0A0A0A;">Strategist Agent</div>
                        <div style="font-size: 11px; color: #10B981; font-weight: 600;">● Brief generated · 1.2s</div>
                    </div>
                </div>
            </div>
            <div class="floating-card" style="top: 280px; right: 10px; width: 220px; animation-delay: 3s;">
                <div style="font-size: 11px; color: #6B7280; font-weight: 600; margin-bottom: 8px;">Budget Split</div>
                <div style="display: flex; gap: 4px; height: 8px; border-radius: 4px; overflow: hidden;">
                    <div style="background: #6366F1; width: 45%;"></div>
                    <div style="background: #EC4899; width: 30%;"></div>
                    <div style="background: #F59E0B; width: 25%;"></div>
                </div>
                <div style="font-size: 11px; color: #6B7280; margin-top: 8px;">IG · FB · Reels</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================================
# BENTO BOX: AGENT SELECTION
# ============================================================================
st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)

if st.session_state.current_agent is None:
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <span class="eyebrow">Choose your agent</span>
        <h2 style="font-size: 40px; margin: 8px 0 8px 0;">Five agents. One mission.</h2>
        <p style="color: #6B7280; font-size: 16px;">Click an agent below to start orchestrating.</p>
    </div>
    """, unsafe_allow_html=True)

    agents_config = [
        ("Strategist", "📋", "icon-indigo", "Campaign strategy, channel mix, budget allocation, and KPIs grounded in Meta benchmarks."),
        ("Creative", "🎨", "icon-pink", "On-brand ad copy variants across Facebook, Instagram, email, and search."),
        ("Analyst", "📊", "icon-cyan", "Natural language analytics. Ask a question, get SQL + insights."),
        ("Optimizer", "⚡", "icon-amber", "Performance vs benchmarks. Budget reallocation recommendations."),
        ("A/B Testing", "🧪", "icon-emerald", "Statistically valid experiments with power analysis."),
    ]

    cols = st.columns(5)
    for i, (name, icon, icon_class, desc) in enumerate(agents_config):
        with cols[i]:
            st.markdown(f"""
            <div class="agent-card">
                <div class="agent-icon {icon_class}">{icon}</div>
                <h3 class="agent-card-title">{name}</h3>
                <p class="agent-card-desc">{desc}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Launch →", key=f"launch_{name}"):
                st.session_state.current_agent = name
                st.rerun()

    # ========================================================================
    # BENTO GRID: Live Metrics + System Status
    # ========================================================================
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <span class="eyebrow">System intelligence</span>
        <h2 style="font-size: 40px; margin: 8px 0;">Live telemetry.</h2>
    </div>
    """, unsafe_allow_html=True)

    # Bento grid
    bento_col1, bento_col2, bento_col3 = st.columns([2, 1, 1])

    with bento_col1:
        st.markdown("""
        <div class="bento-card bento-card-dark" style="height: 280px; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -100px; right: -100px; width: 300px; height: 300px; background: radial-gradient(circle, rgba(99,102,241,0.4) 0%, transparent 70%);"></div>
            <div style="position: relative; z-index: 1;">
                <span class="eyebrow" style="background: rgba(99,102,241,0.2); color: #A5B4FC; border-color: rgba(99,102,241,0.3);">Real-time</span>
                <h3 style="font-size: 32px; margin: 16px 0 8px 0; color: white;">
                    Agents orchestrated<br>with full observability.
                </h3>
                <p style="color: #A1A1AA; font-size: 14px; max-width: 400px;">
                    Every tool call, token, and decision is traced. Debug in seconds, not hours.
                </p>
                <div style="display: flex; gap: 24px; margin-top: 32px;">
                    <div>
                        <div style="font-size: 36px; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(135deg, #6366F1, #EC4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">5</div>
                        <div style="font-size: 12px; color: #A1A1AA; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Agents</div>
                    </div>
                    <div>
                        <div style="font-size: 36px; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(135deg, #F59E0B, #EF4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">500</div>
                        <div style="font-size: 12px; color: #A1A1AA; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">SMBs</div>
                    </div>
                    <div>
                        <div style="font-size: 36px; font-weight: 800; letter-spacing: -0.03em; background: linear-gradient(135deg, #10B981, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">9</div>
                        <div style="font-size: 12px; color: #A1A1AA; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Endpoints</div>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with bento_col2:
        st.markdown("""
        <div class="bento-card" style="height: 280px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div class="metric-label">Avg Latency</div>
                <div class="metric-value">1.8<span style="font-size: 20px; color: #6B7280;">s</span></div>
                <div class="metric-delta delta-up">↓ 23% faster</div>
            </div>
            <div style="height: 80px; background: linear-gradient(180deg, rgba(99,102,241,0.05) 0%, transparent 100%); border-radius: 12px; position: relative; overflow: hidden;">
                <svg viewBox="0 0 200 80" style="width: 100%; height: 100%;" preserveAspectRatio="none">
                    <path d="M0,50 Q25,30 50,40 T100,35 T150,25 T200,20" stroke="#6366F1" stroke-width="2" fill="none"/>
                    <path d="M0,50 Q25,30 50,40 T100,35 T150,25 T200,20 L200,80 L0,80 Z" fill="url(#grad)"/>
                    <defs>
                        <linearGradient id="grad" x1="0%" y1="0%" x2="0%" y2="100%">
                            <stop offset="0%" style="stop-color:#6366F1;stop-opacity:0.2"/>
                            <stop offset="100%" style="stop-color:#6366F1;stop-opacity:0"/>
                        </linearGradient>
                    </defs>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with bento_col3:
        st.markdown("""
        <div class="bento-card bento-card-gradient" style="height: 280px; display: flex; flex-direction: column; justify-content: space-between; position: relative; overflow: hidden;">
            <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);"></div>
            <div style="position: relative; z-index: 1;">
                <div style="font-size: 12px; color: rgba(255,255,255,0.8); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Cost / Run</div>
                <div style="font-family: 'Plus Jakarta Sans', sans-serif; font-size: 36px; font-weight: 800; letter-spacing: -0.03em; margin-top: 8px;">$0.15</div>
                <div style="font-size: 13px; color: rgba(255,255,255,0.9); font-weight: 600; margin-top: 8px;">Haiku · 4.5</div>
            </div>
            <div style="font-size: 11px; color: rgba(255,255,255,0.7); position: relative; z-index: 1;">
                80% cheaper than Sonnet<br>for eval workload
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Second row of bento
    bento2_col1, bento2_col2, bento2_col3 = st.columns(3)

    with bento2_col1:
        st.markdown("""
        <div class="bento-card" style="height: 200px;">
            <div class="metric-label">Knowledge Base</div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin: 12px 0;">
                <div class="metric-value">49</div>
                <span style="color: #6B7280; font-size: 14px;">documents</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px;">
                <span class="status-badge badge-info">ChromaDB</span>
                <span class="status-badge badge-info">Meta KB</span>
                <span class="status-badge badge-info">Creative</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with bento2_col2:
        st.markdown("""
        <div class="bento-card" style="height: 200px;">
            <div class="metric-label">Eval Framework</div>
            <div style="display: flex; align-items: baseline; gap: 8px; margin: 12px 0;">
                <div class="metric-value">57</div>
                <span style="color: #6B7280; font-size: 14px;">golden examples</span>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 16px;">
                <span class="status-badge badge-success">100% Pass</span>
                <span class="status-badge badge-info">4 Agents</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with bento2_col3:
        st.markdown("""
        <div class="bento-card" style="height: 200px; background: #0A0A0A; color: white; border: none;">
            <div style="font-size: 12px; font-weight: 600; color: #A1A1AA; text-transform: uppercase; letter-spacing: 0.05em;">Infrastructure</div>
            <div style="margin-top: 16px; display: flex; flex-direction: column; gap: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: white;">PostgreSQL</span>
                    <span class="pulse-dot"></span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: white;">ChromaDB</span>
                    <span class="pulse-dot"></span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: white;">FastAPI</span>
                    <span class="pulse-dot"></span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-size: 13px; color: white;">n8n</span>
                    <span class="pulse-dot"></span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# STRATEGIST AGENT VIEW
# ============================================================================
elif st.session_state.current_agent == "Strategist":
    vs, db = get_tools()

    # Back button + header
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("← Back", key="back_btn"):
            st.session_state.current_agent = None
            st.session_state.last_result = None
            st.rerun()

    st.markdown(f"""
    <div style="margin: 20px 0 40px 0;">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px;">
            <div class="agent-icon icon-indigo" style="margin: 0;">📋</div>
            <span class="eyebrow" style="margin-bottom: 0;">Strategist Agent</span>
        </div>
        <h1 class="hero-title" style="font-size: 56px;">
            Design a <span class="hero-title-gradient">winning campaign.</span>
        </h1>
        <p class="hero-subtitle" style="margin-top: 16px;">
            RAG-powered strategic planning. Agent pulls from Meta benchmarks, historical campaigns, and brand guidelines to generate channel mix, budget allocation, and KPIs.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Input card
    st.markdown('<div class="output-card">', unsafe_allow_html=True)
    st.markdown('<div class="output-card-title">◆ Campaign Parameters</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        campaign_goal = st.text_area(
            "Campaign Goal",
            value="Acquire 500 new SMB advertisers in the restaurant vertical at under $150 CAC",
            height=100,
        )
        budget_usd = st.number_input("Total Budget (USD)", value=75000, min_value=1000, step=1000)

    with col2:
        target_segment = st.text_input(
            "Target Segment",
            value="Restaurant owners with 1-10 locations who have never run a Meta ad",
        )
        timeline_days = st.slider("Campaign Duration (Days)", 7, 365, 45)

    st.markdown("</div>", unsafe_allow_html=True)

    # Run button
    run_btn = st.button("⚡ Generate Strategic Brief", key="run_strategist")

    if run_btn:
        import threading
        import time as time_mod
        from queue import Queue, Empty
        from agents.strategist import StrategistAgent

        # Setup live event streaming
        event_queue = Queue()
        result_holder = {"result": None, "error": None, "done": False}

        def run_agent_thread():
            try:
                def cb(event):
                    event_queue.put(event)
                agent = StrategistAgent(
                    vector_search_tool=vs,
                    db_query_tool=db,
                    event_callback=cb,
                )
                result = agent.run_campaign_brief(
                    campaign_goal=campaign_goal,
                    budget_usd=budget_usd,
                    timeline_days=timeline_days,
                    target_segment=target_segment,
                )
                result_holder["result"] = result
            except Exception as e:
                result_holder["error"] = str(e)
            finally:
                result_holder["done"] = True

        thread = threading.Thread(target=run_agent_thread, daemon=True)
        thread.start()

        # Live observability panel
        st.markdown("""
        <div style="margin-top: 24px;">
            <span class="eyebrow" style="background: rgba(16,185,129,0.1); color: #059669; border-color: rgba(16,185,129,0.3);">
                <span class="pulse-dot"></span> LIVE · OBSERVING
            </span>
            <h3 style="font-size: 28px; margin: 8px 0 16px 0;">Agent execution stream</h3>
        </div>
        """, unsafe_allow_html=True)

        live_panel = st.empty()
        events_log = []
        start_time = time_mod.time()

        # Icon mapping for event types
        event_meta = {
            "agent_start": ("🚀", "#6366F1", "Agent Initialized"),
            "turn_start": ("🔄", "#8B5CF6", "Turn Started"),
            "llm_call_start": ("🧠", "#3B82F6", "Calling Claude"),
            "llm_call_end": ("✓", "#10B981", "Claude Responded"),
            "tool_call_start": ("🔧", "#F59E0B", "Invoking Tool"),
            "tool_call_end": ("⚡", "#10B981", "Tool Completed"),
            "agent_complete": ("🎯", "#10B981", "Agent Complete"),
        }

        def render_events(events):
            html_parts = ['<div class="output-card" style="max-height: 500px; overflow-y: auto;">']
            for ev in events:
                icon, color, default_label = event_meta.get(ev["type"], ("●", "#6B7280", ev["type"]))
                elapsed = ev.get("timestamp", 0) - start_time

                # Build event content based on type
                content = ""
                if ev["type"] == "agent_start":
                    content = f"<div style='color: #6B7280; font-size: 13px;'>Starting {ev.get('agent', 'agent')}...</div>"
                elif ev["type"] == "turn_start":
                    content = f"<div style='color: #6B7280; font-size: 13px;'>Turn {ev.get('turn')} of {ev.get('max_turns')}</div>"
                elif ev["type"] == "llm_call_start":
                    content = f"<div style='color: #6B7280; font-size: 13px;'>Sending to {ev.get('model', 'Claude')}...</div>"
                elif ev["type"] == "llm_call_end":
                    tokens_in = ev.get('input_tokens', 0)
                    tokens_out = ev.get('output_tokens', 0)
                    stop = ev.get('stop_reason', '')
                    lat = ev.get('latency_ms', 0)
                    content = f"""<div style='color: #6B7280; font-size: 13px; display: flex; gap: 12px; flex-wrap: wrap;'>
                        <span>⏱ {lat:.0f}ms</span>
                        <span>📥 {tokens_in} in</span>
                        <span>📤 {tokens_out} out</span>
                        <span>🏁 {stop}</span>
                    </div>"""
                elif ev["type"] == "tool_call_start":
                    tool = ev.get('tool', 'unknown')
                    inp = ev.get('input', {})
                    inp_str = str(inp)[:150]
                    content = f"""<div style='font-family: SF Mono, monospace; font-size: 12px; color: #0A0A0A; background: #F9FAFB; padding: 8px 12px; border-radius: 8px; margin-top: 6px;'>
                        <span style='color: #8B5CF6; font-weight: 700;'>{tool}</span>({inp_str})
                    </div>"""
                elif ev["type"] == "tool_call_end":
                    tool = ev.get('tool', 'unknown')
                    success = ev.get('success', True)
                    lat = ev.get('latency_ms', 0)
                    preview = ev.get('output_preview', '')[:120]
                    status_color = "#10B981" if success else "#EF4444"
                    content = f"""<div style='color: #6B7280; font-size: 12px; display: flex; gap: 12px;'>
                        <span>{tool}</span>
                        <span style='color: {status_color};'>{"✓ success" if success else "✗ failed"}</span>
                        <span>⏱ {lat:.0f}ms</span>
                    </div>
                    <div style='font-family: SF Mono, monospace; font-size: 11px; color: #374151; background: #F9FAFB; padding: 6px 10px; border-radius: 6px; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;'>
                        → {preview}
                    </div>"""
                elif ev["type"] == "agent_complete":
                    lat = ev.get('latency_ms', 0)
                    turns = ev.get('turns', 0)
                    tokens = ev.get('total_tokens', 0)
                    content = f"""<div style='color: #059669; font-size: 13px; font-weight: 600;'>
                        Completed in {lat:.0f}ms · {turns} turns · {tokens:,} tokens
                    </div>"""

                html_parts.append(f"""
                <div style="display: flex; align-items: flex-start; gap: 12px; padding: 12px 0; border-bottom: 1px solid #F3F4F6;">
                    <div style="width: 28px; height: 28px; border-radius: 8px; background: {color}15; color: {color}; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0;">{icon}</div>
                    <div style="flex: 1; min-width: 0;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                            <div style="font-weight: 600; color: #0A0A0A; font-size: 14px;">{default_label}</div>
                            <div style="font-family: SF Mono, monospace; font-size: 11px; color: #9CA3AF;">+{elapsed:.2f}s</div>
                        </div>
                        {content}
                    </div>
                </div>
                """)
            html_parts.append('</div>')
            return "".join(html_parts)

        # Poll queue and update UI
        max_wait = 120  # 2 min timeout
        poll_start = time_mod.time()
        while not result_holder["done"] and (time_mod.time() - poll_start) < max_wait:
            try:
                event = event_queue.get(timeout=0.3)
                events_log.append(event)
                with live_panel.container():
                    st.markdown(render_events(events_log), unsafe_allow_html=True)
            except Empty:
                pass

        # Drain any remaining events
        while True:
            try:
                event = event_queue.get_nowait()
                events_log.append(event)
            except Empty:
                break

        # Final render
        with live_panel.container():
            st.markdown(render_events(events_log), unsafe_allow_html=True)

        thread.join(timeout=1)

        if result_holder["error"]:
            st.error(f"Agent execution failed: {result_holder['error']}")
            st.stop()

        st.session_state.last_result = result_holder["result"]

    # Display result
    result = st.session_state.last_result
    if result and result.success:
        # Metrics row
        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        metrics = [
            (m1, "Latency", f"{result.latency_ms:.0f}", "ms"),
            (m2, "Total Tokens", f"{result.total_input_tokens + result.total_output_tokens:,}", ""),
            (m3, "Tool Calls", f"{len(result.tool_calls_made)}", ""),
            (m4, "Cost", f"${(result.total_input_tokens * 0.0000008 + result.total_output_tokens * 0.000004):.4f}", ""),
        ]
        for col, label, value, unit in metrics:
            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}<span style="font-size: 16px; color: #6B7280; font-weight: 600;">{unit}</span></div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 32px;'></div>", unsafe_allow_html=True)

        output = result.output

        # Bento grid for brief
        b1, b2 = st.columns([1, 1])

        with b1:
            # Channels + Message
            if "recommended_channels" in output:
                channels_html = ""
                for ch in output["recommended_channels"]:
                    channels_html += f'<span class="status-badge badge-info" style="margin-right: 8px; margin-bottom: 8px; font-size: 13px; padding: 8px 14px;">📢 {ch}</span>'
                st.markdown(f"""
                <div class="output-card">
                    <div class="output-card-title">◆ Recommended Channels</div>
                    <div style="margin-top: 12px;">{channels_html}</div>
                </div>
                """, unsafe_allow_html=True)

            if "primary_message_pillar" in output:
                st.markdown(f"""
                <div class="output-card bento-card-gradient" style="position: relative; overflow: hidden;">
                    <div style="position: absolute; top: -50px; right: -50px; width: 200px; height: 200px; background: radial-gradient(circle, rgba(255,255,255,0.15) 0%, transparent 70%);"></div>
                    <div class="output-card-title" style="color: rgba(255,255,255,0.8);">◆ Primary Message Pillar</div>
                    <p style="font-size: 18px; font-weight: 600; color: white; line-height: 1.4; margin: 12px 0 0 0; position: relative;">
                        "{output['primary_message_pillar']}"
                    </p>
                </div>
                """, unsafe_allow_html=True)

        with b2:
            # Budget split
            if "budget_split" in output:
                bs = output["budget_split"]
                total = sum(bs.values())
                rows_html = ""
                for ch, amt in bs.items():
                    pct = (amt / total * 100) if total else 0
                    rows_html += f"""
                    <div style="margin-bottom: 16px;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                            <span style="font-weight: 600; color: #0A0A0A; font-size: 14px;">{ch}</span>
                            <span style="font-weight: 700; color: #0A0A0A; font-size: 14px;">${amt:,.0f} · {pct:.0f}%</span>
                        </div>
                        <div style="height: 8px; background: #F3F4F6; border-radius: 4px; overflow: hidden;">
                            <div style="height: 100%; width: {pct}%; background: linear-gradient(90deg, #6366F1, #EC4899); border-radius: 4px;"></div>
                        </div>
                    </div>
                    """
                st.markdown(f"""
                <div class="output-card" style="height: 100%;">
                    <div class="output-card-title">◆ Budget Allocation</div>
                    <div style="margin-top: 16px;">{rows_html}</div>
                </div>
                """, unsafe_allow_html=True)

        # KPIs
        if "kpis" in output:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            st.markdown('<div class="output-card-title">◆ Target KPIs</div>', unsafe_allow_html=True)

            kpis = output["kpis"]
            kpi_cols = st.columns(min(len(kpis), 4))
            for i, (k, v) in enumerate(kpis.items()):
                with kpi_cols[i % 4]:
                    st.markdown(f"""
                    <div class="metric-card" style="text-align: left;">
                        <div class="metric-label">{k.replace('_', ' ')}</div>
                        <div class="metric-value" style="font-size: 28px;">{v}</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Risks
        if "risks" in output and output["risks"]:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            st.markdown(f"""
            <div class="output-card">
                <div class="output-card-title">◆ Identified Risks</div>
            """, unsafe_allow_html=True)
            for risk in output["risks"]:
                st.markdown(f"""
                <div style="padding: 12px 16px; background: rgba(245, 158, 11, 0.05); border-left: 3px solid #F59E0B; border-radius: 12px; margin-top: 10px; font-size: 14px; color: #0A0A0A;">
                    ⚠️ {risk}
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Rationale
        if "rationale" in output:
            with st.expander("💭 View full agent reasoning"):
                st.markdown(output["rationale"])

        # Tool calls
        if result.tool_calls_made:
            st.markdown("<div style='margin-top: 24px;'></div>", unsafe_allow_html=True)
            with st.expander(f"🔧 Tool calls executed ({len(result.tool_calls_made)})"):
                for i, call in enumerate(result.tool_calls_made, 1):
                    status = "✅" if call.get("success") else "❌"
                    st.markdown(f"""
                    <div class="tool-call-card">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                            <strong>{status} {call.get('tool', 'unknown')}</strong>
                            <span style="color: #6B7280;">{call.get('latency_ms', 0):.0f}ms</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("Input / Output"):
                        st.json({"input": call.get("input"), "output": call.get("output")})

        # Raw JSON
        with st.expander("📄 Raw JSON output"):
            st.json(output)

        # Trace
        if result.trace_url:
            st.markdown(f"""
            <div style="margin-top: 24px; padding: 16px 20px; background: white; border: 1px solid #E5E7EB; border-radius: 16px; display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #6B7280; font-size: 14px;">View full execution trace in Langfuse</span>
                <a href="{result.trace_url}" target="_blank" style="color: #6366F1; font-weight: 600; text-decoration: none; font-size: 14px;">Open Trace →</a>
            </div>
            """, unsafe_allow_html=True)

    elif result and not result.success:
        st.error(f"Agent failed: {result.error}")


# ============================================================================
# PLACEHOLDER VIEWS FOR OTHER AGENTS
# ============================================================================
else:
    agent_name = st.session_state.current_agent
    col_back, _ = st.columns([1, 10])
    with col_back:
        if st.button("← Back", key="back_other"):
            st.session_state.current_agent = None
            st.rerun()

    icon_map = {
        "Creative": ("🎨", "icon-pink"),
        "Analyst": ("📊", "icon-cyan"),
        "Optimizer": ("⚡", "icon-amber"),
        "A/B Testing": ("🧪", "icon-emerald"),
    }
    icon, icon_class = icon_map.get(agent_name, ("◆", "icon-indigo"))

    st.markdown(f"""
    <div style="margin: 20px 0 40px 0;">
        <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 12px;">
            <div class="agent-icon {icon_class}" style="margin: 0;">{icon}</div>
            <span class="eyebrow" style="margin-bottom: 0;">{agent_name} Agent</span>
        </div>
        <h1 class="hero-title" style="font-size: 56px;">
            Coming <span class="hero-title-gradient">next.</span>
        </h1>
        <p class="hero-subtitle" style="margin-top: 16px;">
            This agent's UI is being built next. The {agent_name} agent is fully functional via the FastAPI endpoint at <code style="background: #F3F4F6; padding: 4px 8px; border-radius: 6px;">POST /agents/{agent_name.lower().replace(" ", "-").replace("a/b-testing", "ab-test")}/run</code>.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="bento-card bento-card-gradient" style="margin-top: 24px;">
        <h3 style="font-size: 24px; color: white; margin: 0 0 8px 0;">🚀 In Development</h3>
        <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin: 0;">
            Full interactive tab with inputs, real-time execution, and rich visualizations coming soon.
        </p>
    </div>
    """, unsafe_allow_html=True)
