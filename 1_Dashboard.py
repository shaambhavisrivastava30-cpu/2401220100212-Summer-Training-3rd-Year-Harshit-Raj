"""
Dashboard — Overview of health stats, predictions, and upcoming events.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, date

from utils.auth import require_auth
from utils.helpers import load_css, page_header, metric_card
from database.db_manager import (
    get_prediction_stats, get_appointments, get_medicines,
    get_vitals, update_user_profile, get_user_by_id
)

st.set_page_config(page_title="Dashboard | HealthAI", page_icon="📊", layout="wide")
load_css()

user = require_auth()
uid  = user["id"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding:1rem 0;">
        <div style="font-size:3rem">👤</div>
        <div style="font-weight:700; font-size:1.1rem; color:#E2E8F0">
            {user.get('full_name') or user['username']}
        </div>
        <div style="color:#64748B; font-size:0.85rem">{user.get('email') or 'No email set'}</div>
    </div>
    """, unsafe_allow_html=True)
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated", "user", "chat_messages"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")

page_header("Dashboard", f"Welcome back, {user.get('full_name') or user['username']}! Here's your health overview.", "📊")

# ── Top Metrics ───────────────────────────────────────────────────────────────
predictions = get_prediction_stats(uid)
appointments = get_appointments(uid, upcoming_only=True)
medicines    = get_medicines(uid)

high_risk = sum(1 for p in predictions if p.get("risk_level") == "High")
today     = date.today().isoformat()
today_appts = [a for a in appointments if a["appointment_date"] == today]

col1, col2, col3, col4 = st.columns(4)
with col1:
    metric_card("Total Predictions", str(len(predictions)), "🔬", "All time")
with col2:
    metric_card("High Risk Alerts", str(high_risk), "⚠️", "Needs attention" if high_risk else "All clear")
with col3:
    metric_card("Upcoming Appts", str(len(appointments)), "📅", "Scheduled")
with col4:
    metric_card("Active Medicines", str(len(medicines)), "💊", "Current medications")

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts Row ────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown('<div class="section-header">📈 Prediction History</div>', unsafe_allow_html=True)
    if predictions:
        df = pd.DataFrame(predictions)
        df["created_at"] = pd.to_datetime(df["created_at"])
        df["date"]       = df["created_at"].dt.date

        disease_counts = df["disease_type"].value_counts().reset_index()
        disease_counts.columns = ["disease", "count"]
        disease_counts["disease"] = disease_counts["disease"].str.replace("_", " ").str.title()

        fig = px.bar(
            disease_counts, x="disease", y="count",
            color="count",
            color_continuous_scale=["#0EA5E9", "#10B981"],
            labels={"disease": "Disease Type", "count": "Tests Run"},
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            showlegend=False,
            coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
        )
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem">🔬</div>
            <div style="color:#64748B; margin-top:0.5rem">No predictions yet. Visit Disease Prediction to get started.</div>
        </div>
        """, unsafe_allow_html=True)

with col_right:
    st.markdown('<div class="section-header">📊 Risk Distribution</div>', unsafe_allow_html=True)
    if predictions:
        risk_counts = {"Low": 0, "Medium": 0, "High": 0}
        for p in predictions:
            rl = p.get("risk_level", "Low")
            if rl in risk_counts:
                risk_counts[rl] += 1

        fig2 = go.Figure(go.Pie(
            labels=list(risk_counts.keys()),
            values=list(risk_counts.values()),
            hole=0.55,
            marker=dict(colors=["#10B981", "#FBBF24", "#EF4444"]),
            textfont=dict(color="#E2E8F0", size=13),
        ))
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="#94A3B8",
            showlegend=True,
            legend=dict(font=dict(color="#94A3B8")),
            margin=dict(l=10, r=10, t=10, b=10),
            height=280,
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:3rem;">
            <div style="font-size:2rem">📊</div>
            <div style="color:#64748B">No data yet</div>
        </div>
        """, unsafe_allow_html=True)

# ── Upcoming Appointments ─────────────────────────────────────────────────────
st.markdown('<div class="section-header">📅 Upcoming Appointments</div>', unsafe_allow_html=True)
if appointments:
    for a in appointments[:5]:
        days_until = (date.fromisoformat(a["appointment_date"]) - date.today()).days
        urgency_color = "#EF4444" if days_until == 0 else "#FBBF24" if days_until <= 3 else "#10B981"
        st.markdown(f"""
        <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; padding:1rem 1.5rem;">
            <div>
                <div style="font-weight:600; color:#E2E8F0;">Dr. {a['doctor_name']}</div>
                <div style="color:#64748B; font-size:0.85rem">{a.get('speciality','') or 'General'} • {a.get('location','') or 'TBD'}</div>
            </div>
            <div style="text-align:right">
                <div style="color:{urgency_color}; font-weight:700">{a['appointment_date']}</div>
                <div style="color:#64748B; font-size:0.85rem">{a['appointment_time']} • {"Today!" if days_until==0 else f"In {days_until} day(s)"}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No upcoming appointments. Book one in the Appointments section.")

# ── Recent Predictions ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🔬 Recent Predictions</div>', unsafe_allow_html=True)
if predictions:
    for p in predictions[:6]:
        risk_color = {"Low": "#10B981", "Medium": "#FBBF24", "High": "#EF4444"}.get(p["risk_level"], "#94A3B8")
        disease_name = p["disease_type"].replace("_", " ").title()
        st.markdown(f"""
        <div class="glass-card" style="display:flex; justify-content:space-between; align-items:center; padding:0.8rem 1.5rem;">
            <div>
                <div style="font-weight:600; color:#E2E8F0">{disease_name}</div>
                <div style="color:#64748B; font-size:0.8rem">{p['created_at'][:16]}</div>
            </div>
            <div style="text-align:right">
                <div style="color:{risk_color}; font-weight:700">{p['prediction']} — {p['risk_level']} Risk</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No predictions yet. Use Disease Prediction to analyze your health data.")

# ── Profile Update ────────────────────────────────────────────────────────────
with st.expander("✏️ Update Profile"):
    with st.form("profile_form"):
        fresh_user = get_user_by_id(uid)
        c1, c2 = st.columns(2)
        with c1:
            fn   = st.text_input("Full Name",  value=fresh_user.get("full_name") or "")
            em   = st.text_input("Email",       value=fresh_user.get("email") or "")
            age  = st.number_input("Age", min_value=0, max_value=120, value=int(fresh_user.get("age") or 0))
        with c2:
            gender = st.selectbox("Gender", ["", "Male", "Female", "Other"], index=["", "Male", "Female", "Other"].index(fresh_user.get("gender") or ""))
            blood  = st.selectbox("Blood Group", ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                                  index=["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(fresh_user.get("blood_group") or ""))
            phone  = st.text_input("Phone", value=fresh_user.get("phone") or "")
        if st.form_submit_button("Save Profile", use_container_width=True):
            update_user_profile(uid, full_name=fn, email=em, age=age, gender=gender, blood_group=blood, phone=phone)
            st.session_state["user"] = get_user_by_id(uid)
            st.success("✅ Profile updated successfully!")
