"""
Medicine Reminder — Add, track, and log medications. View history.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date, timedelta

from utils.auth import require_auth
from utils.helpers import load_css, page_header
from database.db_manager import (
    add_medicine, get_medicines, deactivate_medicine,
    log_medicine_taken, get_medicine_logs
)

st.set_page_config(page_title="Medicine Reminder | HealthAI", page_icon="💊", layout="wide")
load_css()

user = require_auth()
uid  = user["id"]

with st.sidebar:
    st.markdown(f"**👤 {user.get('full_name') or user['username']}**")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated","user"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")

page_header("Medicine Reminder", "Track your medications, dosages, and schedules", "💊")

tab_current, tab_add, tab_history = st.tabs(["💊 Current Medicines", "➕ Add Medicine", "📊 History"])

# ── Current Medicines ─────────────────────────────────────────────────────────
with tab_current:
    medicines = get_medicines(uid, active_only=True)
    now       = datetime.now()

    if not medicines:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem">
            <div style="font-size:3rem">💊</div>
            <div style="color:#64748B;margin-top:0.5rem">No active medicines. Add one in the "Add Medicine" tab.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        today_str = date.today().isoformat()
        for med in medicines:
            # Check if expired
            is_expired = med.get("end_date") and med["end_date"] < today_str
            days_left  = None
            if med.get("end_date"):
                end = date.fromisoformat(med["end_date"])
                days_left = (end - date.today()).days

            status_color = "#EF4444" if is_expired else "#10B981"
            status_text  = "Expired" if is_expired else (f"{days_left}d left" if days_left is not None else "Ongoing")

            col1, col2, col3 = st.columns([4, 2, 1])
            with col1:
                time_slots_str = ", ".join(med.get("time_slots", [])) or "Not specified"
                st.markdown(f"""
                <div class="glass-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start">
                        <div>
                            <div style="font-size:1.1rem;font-weight:700;color:#E2E8F0">💊 {med['medicine_name']}</div>
                            <div style="color:#94A3B8;margin-top:0.3rem">
                                <span>📏 {med.get('dosage','N/A')}</span> &nbsp;|&nbsp;
                                <span>🔄 {med.get('frequency','N/A')}</span>
                            </div>
                            <div style="color:#64748B;font-size:0.85rem;margin-top:0.3rem">
                                ⏰ Times: {time_slots_str}
                            </div>
                            {f"<div style='color:#64748B;font-size:0.8rem'>📅 {med.get('start_date','')} → {med.get('end_date','')}</div>" if med.get('end_date') else ""}
                            {f"<div style='color:#64748B;font-size:0.8rem;margin-top:0.2rem'>📝 {med.get('notes','')}</div>" if med.get('notes') else ""}
                        </div>
                        <span style="background:rgba(30,41,59,0.8);color:{status_color};padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:600">{status_text}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                if not is_expired:
                    if st.button(f"✅ Mark Taken", key=f"taken_{med['id']}"):
                        log_medicine_taken(med["id"], uid)
                        st.success(f"✅ {med['medicine_name']} marked as taken!")
                        st.rerun()
            with col3:
                if st.button(f"🗑️ Stop", key=f"stop_{med['id']}"):
                    deactivate_medicine(med["id"], uid)
                    st.warning(f"Deactivated {med['medicine_name']}")
                    st.rerun()

    # Today's schedule
    if medicines:
        st.markdown("### 📅 Today's Schedule")
        all_slots = {}
        for med in medicines:
            for slot in med.get("time_slots", []):
                if slot not in all_slots:
                    all_slots[slot] = []
                all_slots[slot].append(med["medicine_name"])

        if all_slots:
            sorted_slots = sorted(all_slots.items())
            for time_str, meds in sorted_slots:
                try:
                    t = datetime.strptime(time_str, "%H:%M")
                    is_past = t.hour < now.hour or (t.hour == now.hour and t.minute < now.minute)
                    current = t.hour == now.hour
                except:
                    is_past, current = False, False

                bg = "rgba(16,185,129,0.1)" if current else "rgba(30,41,59,0.4)"
                time_color = "#10B981" if current else "#64748B" if is_past else "#0EA5E9"
                st.markdown(f"""
                <div style="display:flex;gap:1rem;align-items:center;padding:0.7rem;background:{bg};border-radius:8px;margin-bottom:6px">
                    <div style="font-weight:700;color:{time_color};min-width:60px">{time_str}</div>
                    <div style="color:#E2E8F0">{', '.join(meds)}</div>
                    {"<div style='color:#10B981;margin-left:auto'>← Now</div>" if current else ""}
                    {"<div style='color:#64748B;margin-left:auto;font-size:0.8rem'>Done</div>" if is_past and not current else ""}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No time slots configured. Edit your medicines to add specific times.")


# ── Add Medicine ──────────────────────────────────────────────────────────────
with tab_add:
    st.markdown("### ➕ Add New Medicine")
    with st.form("add_medicine_form"):
        c1, c2 = st.columns(2)
        with c1:
            med_name  = st.text_input("Medicine Name *", placeholder="e.g., Metformin, Aspirin")
            dosage    = st.text_input("Dosage", placeholder="e.g., 500mg, 1 tablet")
            frequency = st.selectbox("Frequency", [
                "Once daily", "Twice daily", "Three times daily",
                "Four times daily", "Every 6 hours", "Every 8 hours",
                "Every 12 hours", "As needed", "Weekly", "Monthly"
            ])
            notes = st.text_area("Notes / Instructions", placeholder="e.g., Take with food, Before bedtime", height=80)
        with c2:
            start_date = st.date_input("Start Date", value=date.today())
            end_date   = st.date_input("End Date (optional)", value=None)
            st.markdown("**Select Reminder Times:**")
            time_options = [f"{h:02d}:{m:02d}" for h in range(6, 24) for m in [0, 30]]
            time_slots   = st.multiselect("Time Slots", time_options,
                                          default=["08:00"],
                                          help="Select one or more times to take this medicine")

        submitted = st.form_submit_button("💊 Add Medicine", use_container_width=True)

    if submitted:
        if not med_name.strip():
            st.error("Medicine name is required.")
        else:
            add_medicine(
                user_id=uid,
                medicine_name=med_name.strip(),
                dosage=dosage.strip(),
                frequency=frequency,
                time_slots=time_slots,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat() if end_date else None,
                notes=notes.strip()
            )
            st.success(f"✅ {med_name} added to your medicine list!")
            st.rerun()


# ── History ───────────────────────────────────────────────────────────────────
with tab_history:
    st.markdown("### 📊 Medicine History (Last 30 Days)")
    logs = get_medicine_logs(uid, days=30)

    if not logs:
        st.info("No medicine logs yet. Start logging your medicines in the Current Medicines tab.")
    else:
        df = pd.DataFrame(logs)
        df["taken_at"] = pd.to_datetime(df["taken_at"])
        df["date"]     = df["taken_at"].dt.date
        df["hour"]     = df["taken_at"].dt.hour

        # Summary metrics
        total_taken = len(df)
        unique_meds = df["medicine_name"].nunique()
        days_logged = df["date"].nunique()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Doses Taken", total_taken)
        with col2:
            st.metric("Unique Medicines", unique_meds)
        with col3:
            st.metric("Days Logged", days_logged)

        # Daily adherence chart
        daily = df.groupby("date").size().reset_index(name="doses")
        fig = px.bar(daily, x="date", y="doses",
                     color="doses", color_continuous_scale=["#0EA5E9","#10B981"],
                     labels={"date":"Date","doses":"Doses Taken"},
                     title="Daily Medication Adherence")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#94A3B8", coloraxis_showscale=False,
                           margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(fig, use_container_width=True)

        # Per-medicine breakdown
        med_counts = df["medicine_name"].value_counts().reset_index()
        med_counts.columns = ["Medicine", "Times Taken"]
        fig2 = px.pie(med_counts, values="Times Taken", names="Medicine",
                      color_discrete_sequence=["#0EA5E9","#10B981","#FBBF24","#EF4444","#A855F7"],
                      title="Medication Distribution")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#94A3B8",
                            margin=dict(l=10,r=10,t=40,b=10), height=300)
        st.plotly_chart(fig2, use_container_width=True)

        # Log table
        st.markdown("#### 📋 Detailed Log")
        display_df = df[["medicine_name","taken_at","status"]].copy()
        display_df.columns = ["Medicine", "Taken At", "Status"]
        display_df["Taken At"] = display_df["Taken At"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
