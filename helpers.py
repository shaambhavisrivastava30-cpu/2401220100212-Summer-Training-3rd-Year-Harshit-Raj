"""
Helper utilities for the Smart Healthcare AI Platform.
"""

import streamlit as st


def load_css():
    """Inject custom CSS for glassmorphism and healthcare UI."""
    st.markdown("""
<style>
    /* ── Global ─────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Hide default streamlit elements ───────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* ── Glassmorphism card ────────────────────────────── */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(148, 163, 184, 0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .glass-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
    }

    /* ── Metric cards ──────────────────────────────────── */
    .metric-card {
        background: linear-gradient(135deg, rgba(14, 165, 233, 0.15), rgba(16, 185, 129, 0.1));
        border: 1px solid rgba(14, 165, 233, 0.3);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-3px); }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #0EA5E9;
        line-height: 1;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 0.3rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ── Status badges ─────────────────────────────────── */
    .badge-low    { background:#166534; color:#86EFAC; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
    .badge-medium { background:#854D0E; color:#FDE68A; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }
    .badge-high   { background:#991B1B; color:#FCA5A5; padding:3px 10px; border-radius:20px; font-size:0.75rem; font-weight:600; }

    /* ── Sidebar ───────────────────────────────────────── */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(148,163,184,0.1) !important;
    }

    /* ── Buttons ───────────────────────────────────────── */
    .stButton > button {
        background: linear-gradient(135deg, #0EA5E9, #10B981);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: opacity 0.2s, transform 0.2s;
    }
    .stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-1px);
    }

    /* ── Input fields ──────────────────────────────────── */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div,
    .stTextArea textarea {
        background: rgba(30,41,59,0.8) !important;
        border: 1px solid rgba(148,163,184,0.2) !important;
        color: #F1F5F9 !important;
        border-radius: 8px !important;
    }

    /* ── Tabs ──────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(30,41,59,0.5);
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94A3B8;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0EA5E9, #10B981) !important;
        color: white !important;
    }

    /* ── Chat bubbles ──────────────────────────────────── */
    .chat-user {
        background: linear-gradient(135deg, #0EA5E9, #0284C7);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0 0.5rem 20%;
        max-width: 80%;
        word-wrap: break-word;
    }
    .chat-bot {
        background: rgba(30,41,59,0.9);
        border: 1px solid rgba(14,165,233,0.2);
        color: #E2E8F0;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 20% 0.5rem 0;
        max-width: 80%;
        word-wrap: break-word;
    }

    /* ── Risk level colors ─────────────────────────────── */
    .risk-low    { color: #4ADE80; font-weight: 700; }
    .risk-medium { color: #FBBF24; font-weight: 700; }
    .risk-high   { color: #F87171; font-weight: 700; }

    /* ── Section headers ───────────────────────────────── */
    .section-header {
        font-size: 1.4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #0EA5E9, #10B981);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
    }

    /* ── Alert boxes ───────────────────────────────────── */
    .alert-success { background: rgba(16,185,129,0.15); border-left: 4px solid #10B981; padding: 1rem; border-radius: 8px; }
    .alert-warning { background: rgba(251,191,36,0.15); border-left: 4px solid #FBBF24; padding: 1rem; border-radius: 8px; }
    .alert-danger  { background: rgba(239,68,68,0.15);  border-left: 4px solid #EF4444;  padding: 1rem; border-radius: 8px; }
    .alert-info    { background: rgba(14,165,233,0.15); border-left: 4px solid #0EA5E9;  padding: 1rem; border-radius: 8px; }

    /* ── Progress bars ─────────────────────────────────── */
    .stProgress > div > div > div > div {
        background: linear-gradient(135deg, #0EA5E9, #10B981);
    }
    
    /* ── Scrollbar ─────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: rgba(30,41,59,0.5); }
    ::-webkit-scrollbar-thumb { background: rgba(14,165,233,0.4); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(14,165,233,0.7); }
</style>
""", unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "", icon: str = "🏥"):
    """Render a styled page header."""
    st.markdown(f"""
    <div style="padding: 1.5rem 0 1rem 0; border-bottom: 1px solid rgba(148,163,184,0.1); margin-bottom: 1.5rem;">
        <h1 style="font-size:2rem; font-weight:800; margin:0;
                   background:linear-gradient(135deg,#0EA5E9,#10B981);
                   -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                   background-clip:text;">
            {icon} {title}
        </h1>
        {"<p style='color:#94A3B8; margin:0.3rem 0 0 0;'>" + subtitle + "</p>" if subtitle else ""}
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, icon: str = "", delta: str = ""):
    """Render a single metric card."""
    delta_html = f"<div style='font-size:0.75rem;color:#94A3B8;margin-top:2px'>{delta}</div>" if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div style="font-size:1.5rem; margin-bottom:0.3rem;">{icon}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def risk_badge(risk_level: str) -> str:
    """Return HTML badge for risk level."""
    colors = {
        "Low":    ("#166534", "#86EFAC"),
        "Medium": ("#854D0E", "#FDE68A"),
        "High":   ("#991B1B", "#FCA5A5"),
    }
    bg, fg = colors.get(risk_level, ("#1E293B", "#94A3B8"))
    return f"<span style='background:{bg};color:{fg};padding:3px 12px;border-radius:20px;font-size:0.8rem;font-weight:600'>{risk_level}</span>"


def success_alert(msg):
    st.markdown(f'<div class="alert-success">✅ {msg}</div>', unsafe_allow_html=True)


def warning_alert(msg):
    st.markdown(f'<div class="alert-warning">⚠️ {msg}</div>', unsafe_allow_html=True)


def danger_alert(msg):
    st.markdown(f'<div class="alert-danger">🚨 {msg}</div>', unsafe_allow_html=True)


def info_alert(msg):
    st.markdown(f'<div class="alert-info">ℹ️ {msg}</div>', unsafe_allow_html=True)
