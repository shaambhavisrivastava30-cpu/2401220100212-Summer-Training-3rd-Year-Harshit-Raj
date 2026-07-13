"""
Appointments — Book, view, and manage doctor appointments.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
from datetime import date, time, datetime, timedelta

from utils.auth import require_auth
from utils.helpers import load_css, page_header
from database.db_manager import (
    book_appointment, get_appointments, update_appointment_status, delete_appointment
)

st.set_page_config(page_title="Appointments | HealthAI", page_icon="📅", layout="wide")
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

page_header("Appointments", "Book and manage your doctor appointments", "📅")

SPECIALITIES = [
    "General Physician", "Cardiologist", "Neurologist", "Orthopedist",
    "Dermatologist", "Pediatrician", "Gynecologist", "Urologist",
    "Ophthalmologist", "ENT Specialist", "Psychiatrist", "Endocrinologist",
    "Gastroenterologist", "Pulmonologist", "Oncologist", "Rheumatologist",
    "Nephrologist", "Dietitian", "Physiotherapist", "Dentist", "Other"
]

SAMPLE_DOCTORS = {
    "General Physician":    ["Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Brown"],
    "Cardiologist":         ["Dr. Robert Martinez", "Dr. Lisa Anderson", "Dr. James Wilson"],
    "Neurologist":          ["Dr. Patricia Davis", "Dr. Christopher Lee", "Dr. Jennifer Taylor"],
    "Orthopedist":          ["Dr. David Harris", "Dr. Mary Thompson", "Dr. John Garcia"],
    "Dermatologist":        ["Dr. Susan White", "Dr. Kevin Martin", "Dr. Nancy Clark"],
    "Pediatrician":         ["Dr. Karen Lewis", "Dr. Steven Robinson", "Dr. Betty Walker"],
    "Gynecologist":         ["Dr. Dorothy Hall", "Dr. Michelle Young", "Dr. Sandra King"],
    "Urologist":            ["Dr. Charles Allen", "Dr. Barbara Wright", "Dr. Joseph Scott"],
    "Ophthalmologist":      ["Dr. Helen Green", "Dr. Frank Adams", "Dr. Virginia Baker"],
    "ENT Specialist":       ["Dr. Arthur Nelson", "Dr. Deborah Carter", "Dr. Ronald Mitchell"],
    "Psychiatrist":         ["Dr. Megan Perez", "Dr. Timothy Roberts", "Dr. Laura Turner"],
    "Endocrinologist":      ["Dr. Gregory Phillips", "Dr. Sharon Campbell", "Dr. Raymond Parker"],
    "Gastroenterologist":   ["Dr. Judith Evans", "Dr. Bruce Edwards", "Dr. Joyce Collins"],
    "Dietitian":            ["Dr. Ruth Stewart", "Dr. Harold Sanchez", "Dr. Kathryn Morris"],
}

tab_upcoming, tab_book, tab_all = st.tabs(["📅 Upcoming", "➕ Book Appointment", "📋 All Appointments"])

# ── Upcoming Appointments ─────────────────────────────────────────────────────
with tab_upcoming:
    upcoming = get_appointments(uid, upcoming_only=True)
    today    = date.today()

    if not upcoming:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem">
            <div style="font-size:3rem">📅</div>
            <div style="color:#64748B;margin-top:0.5rem">No upcoming appointments. Book one below!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"**{len(upcoming)} upcoming appointment(s)**")
        for appt in upcoming:
            appt_date = date.fromisoformat(appt["appointment_date"])
            days_left  = (appt_date - today).days
            urgency_bg = "rgba(239,68,68,0.1)" if days_left == 0 else "rgba(251,191,36,0.1)" if days_left <= 3 else "rgba(16,185,129,0.1)"
            date_color = "#EF4444" if days_left == 0 else "#FBBF24" if days_left <= 3 else "#10B981"
            countdown  = "TODAY! 🚨" if days_left == 0 else f"In {days_left} day(s)"

            col1, col2, col3 = st.columns([5, 2, 1])
            with col1:
                st.markdown(f"""
                <div class="glass-card" style="background:{urgency_bg}">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <div style="font-size:1.1rem;font-weight:700;color:#E2E8F0">
                                🏥 Dr. {appt['doctor_name']}
                            </div>
                            <div style="color:#94A3B8;margin-top:0.3rem">
                                🩺 {appt.get('speciality','General')} &nbsp;|&nbsp;
                                📍 {appt.get('location','Location TBD')}
                            </div>
                            {f"<div style='color:#64748B;font-size:0.85rem;margin-top:0.3rem'>📝 {appt.get('notes','')}</div>" if appt.get('notes') else ""}
                        </div>
                        <div style="text-align:right">
                            <div style="color:{date_color};font-weight:700;font-size:1.1rem">{appt['appointment_date']}</div>
                            <div style="color:{date_color};font-size:0.9rem">{appt['appointment_time']}</div>
                            <div style="color:{date_color};font-size:0.8rem;margin-top:0.2rem">{countdown}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if st.button("✅ Mark Done", key=f"done_{appt['id']}"):
                    update_appointment_status(appt["id"], uid, "completed")
                    st.success("Appointment marked as completed.")
                    st.rerun()
            with col3:
                if st.button("❌ Cancel", key=f"cancel_{appt['id']}"):
                    update_appointment_status(appt["id"], uid, "cancelled")
                    st.warning("Appointment cancelled.")
                    st.rerun()


# ── Book Appointment ──────────────────────────────────────────────────────────
with tab_book:
    st.markdown("### ➕ Book New Appointment")
    with st.form("book_appt_form"):
        c1, c2 = st.columns(2)
        with c1:
            speciality = st.selectbox("Speciality *", SPECIALITIES)
            doctors    = SAMPLE_DOCTORS.get(speciality, [])
            if doctors:
                doctor_name = st.selectbox("Doctor *", doctors + ["Other (enter manually)"])
                if doctor_name == "Other (enter manually)":
                    doctor_name = st.text_input("Doctor Name *", placeholder="Dr. First Last")
            else:
                doctor_name = st.text_input("Doctor Name *", placeholder="Dr. First Last")
            location = st.text_input("Hospital / Clinic", placeholder="City Medical Center, Room 201")

        with c2:
            appt_date = st.date_input("Appointment Date *", min_value=date.today(),
                                       value=date.today() + timedelta(days=1))
            appt_time = st.time_input("Appointment Time *", value=time(10, 0))
            notes     = st.text_area("Notes / Reason for Visit", height=90,
                                     placeholder="Annual check-up, follow-up for blood pressure...")

        submitted = st.form_submit_button("📅 Book Appointment", use_container_width=True)

    if submitted:
        name_to_save = doctor_name if isinstance(doctor_name, str) else ""
        if not name_to_save.strip():
            st.error("Doctor name is required.")
        else:
            book_appointment(
                user_id=uid,
                doctor_name=name_to_save.strip().removeprefix("Dr. ").strip(),
                speciality=speciality,
                date=appt_date.isoformat(),
                time=appt_time.strftime("%H:%M"),
                location=location.strip(),
                notes=notes.strip()
            )
            st.success(f"✅ Appointment booked with Dr. {name_to_save} on {appt_date} at {appt_time.strftime('%H:%M')}!")
            st.rerun()

    # Doctor list reference
    with st.expander("👨‍⚕️ Available Doctors Reference"):
        for spec, docs in SAMPLE_DOCTORS.items():
            st.markdown(f"**{spec}:**")
            for d in docs:
                st.markdown(f"  - {d}")


# ── All Appointments ──────────────────────────────────────────────────────────
with tab_all:
    st.markdown("### 📋 All Appointments")
    all_appts = get_appointments(uid, upcoming_only=False)

    if not all_appts:
        st.info("No appointments found.")
    else:
        status_filter = st.multiselect("Filter by Status",
                                        ["scheduled","completed","cancelled"],
                                        default=["scheduled","completed","cancelled"])
        filtered = [a for a in all_appts if a["status"] in status_filter]

        status_colors = {"scheduled":"#0EA5E9","completed":"#10B981","cancelled":"#EF4444"}

        for appt in filtered:
            sc = status_colors.get(appt["status"], "#64748B")
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            padding:0.8rem 1.2rem;background:rgba(30,41,59,0.4);
                            border-radius:10px;margin-bottom:6px;
                            border-left:3px solid {sc}">
                    <div>
                        <span style="font-weight:600;color:#E2E8F0">Dr. {appt['doctor_name']}</span>
                        <span style="color:#64748B;font-size:0.85rem;margin-left:0.8rem">{appt.get('speciality','')}</span>
                    </div>
                    <div style="text-align:right">
                        <span style="color:#94A3B8">{appt['appointment_date']} {appt['appointment_time']}</span>
                        &nbsp;
                        <span style="background:rgba(30,41,59,0.8);color:{sc};padding:2px 8px;border-radius:12px;font-size:0.75rem">{appt['status'].title()}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                if appt["status"] == "scheduled":
                    if st.button("🗑️", key=f"del_appt_{appt['id']}", help="Delete"):
                        delete_appointment(appt["id"], uid)
                        st.rerun()

        # Calendar view summary
        st.divider()
        st.markdown("#### 📊 Appointment Summary")
        df = pd.DataFrame(all_appts)
        if not df.empty:
            status_counts = df["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            import plotly.express as px
            fig = px.pie(status_counts, values="Count", names="Status",
                         color="Status",
                         color_discrete_map={"scheduled":"#0EA5E9","completed":"#10B981","cancelled":"#EF4444"},
                         title="Appointment Status Distribution")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#94A3B8",
                               margin=dict(l=10,r=10,t=40,b=10), height=280)
            st.plotly_chart(fig, use_container_width=True)
