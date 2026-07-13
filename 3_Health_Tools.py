"""
Health Tools — BMI, Calorie, Water Intake, Blood Pressure, Heart Rate, Daily Health Score.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

from utils.auth import require_auth
from utils.helpers import load_css, page_header
from database.db_manager import save_vital, get_vitals

st.set_page_config(page_title="Health Tools | HealthAI", page_icon="🩺", layout="wide")
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

page_header("Health Tools", "Monitor and calculate your key health metrics", "🩺")

tabs = st.tabs(["⚖️ BMI", "🔥 Calories", "💧 Water Intake", "❤️ Blood Pressure", "💓 Heart Rate", "⭐ Health Score"])

# ── Tab 1: BMI Calculator ─────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("### ⚖️ BMI Calculator")
    col1, col2 = st.columns(2)
    with col1:
        weight = st.number_input("Weight (kg)", 20.0, 300.0, 70.0, 0.5)
        height = st.number_input("Height (cm)", 100.0, 250.0, 170.0, 0.5)
        age    = st.number_input("Age", 10, 100, 30, 1)
        gender = st.selectbox("Gender", ["Male", "Female"])

    with col2:
        if st.button("Calculate BMI", use_container_width=True):
            h_m = height / 100
            bmi = weight / (h_m ** 2)

            if bmi < 18.5:   category, color, advice = "Underweight", "#3B82F6", "Increase caloric intake with nutritious foods. Consult a dietitian."
            elif bmi < 25.0: category, color, advice = "Normal Weight", "#10B981", "Excellent! Maintain your healthy lifestyle."
            elif bmi < 30.0: category, color, advice = "Overweight",   "#FBBF24", "Consider increasing physical activity and reducing calorie intake."
            else:             category, color, advice = "Obese",         "#EF4444", "Consult a doctor or dietitian for a weight management plan."

            save_vital(uid, "BMI", bmi, "kg/m²")

            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=bmi,
                number={"suffix":" kg/m²", "font":{"color":"#E2E8F0","size":28}},
                gauge={
                    "axis":  {"range": [10, 45], "tickcolor":"#64748B"},
                    "bar":   {"color": color},
                    "steps": [
                        {"range":[10,18.5], "color":"rgba(59,130,246,0.2)"},
                        {"range":[18.5,25], "color":"rgba(16,185,129,0.2)"},
                        {"range":[25,30],   "color":"rgba(251,191,36,0.2)"},
                        {"range":[30,45],   "color":"rgba(239,68,68,0.2)"},
                    ],
                    "bgcolor": "rgba(30,41,59,0.5)",
                    "bordercolor":"rgba(148,163,184,0.2)",
                },
                title={"text":"BMI","font":{"color":"#94A3B8"}},
            ))
            fig.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#94A3B8", margin=dict(l=20,r=20,t=40,b=10))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:1.5rem; font-weight:700; color:{color}">{category}</div>
                <div style="color:#94A3B8; margin-top:0.5rem">{advice}</div>
                <div style="margin-top:0.8rem; color:#64748B; font-size:0.85rem">
                    Ideal weight range: <strong style="color:#0EA5E9">{18.5*h_m**2:.1f} – {24.9*h_m**2:.1f} kg</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # BMI history chart
    vitals = get_vitals(uid, "BMI")
    if vitals:
        df = pd.DataFrame(vitals)
        df["recorded_at"] = pd.to_datetime(df["recorded_at"])
        fig2 = px.line(df, x="recorded_at", y="value", markers=True,
                       color_discrete_sequence=["#0EA5E9"],
                       labels={"recorded_at":"Date","value":"BMI"})
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#94A3B8", height=200,
                           margin=dict(l=10,r=10,t=30,b=10))
        fig2.add_hrect(y0=18.5, y1=24.9, fillcolor="rgba(16,185,129,0.1)",
                       line_width=0, annotation_text="Normal", annotation_font_color="#10B981")
        st.plotly_chart(fig2, use_container_width=True)


# ── Tab 2: Calorie Calculator ─────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### 🔥 Daily Calorie Calculator")
    col1, col2 = st.columns(2)
    with col1:
        c_weight = st.number_input("Weight (kg)", 20.0, 300.0, 70.0, 0.5, key="cal_w")
        c_height = st.number_input("Height (cm)", 100.0, 250.0, 170.0, 0.5, key="cal_h")
        c_age    = st.number_input("Age", 10, 100, 30, 1, key="cal_age")
        c_gender = st.selectbox("Gender", ["Male", "Female"], key="cal_g")
        c_activity = st.selectbox("Activity Level", [
            "Sedentary (little/no exercise)",
            "Lightly active (1-3 days/week)",
            "Moderately active (3-5 days/week)",
            "Very active (6-7 days/week)",
            "Super active (physical job + exercise)",
        ])
        c_goal = st.selectbox("Goal", ["Maintain weight", "Lose weight", "Gain muscle"])

    with col2:
        if st.button("Calculate Calories", use_container_width=True):
            # Mifflin-St Jeor Equation
            if c_gender == "Male":
                bmr = 10*c_weight + 6.25*c_height - 5*c_age + 5
            else:
                bmr = 10*c_weight + 6.25*c_height - 5*c_age - 161

            activity_multipliers = [1.2, 1.375, 1.55, 1.725, 1.9]
            amf = activity_multipliers[["Sedentary","Lightly","Moderately","Very","Super"].index(
                next(a for a in ["Sedentary","Lightly","Moderately","Very","Super"] if a in c_activity)
            )]
            tdee = bmr * amf

            goal_adj = {"Maintain weight": 0, "Lose weight": -500, "Gain muscle": +300}[c_goal]
            target   = tdee + goal_adj

            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:0.9rem;color:#64748B">Basal Metabolic Rate (BMR)</div>
                <div style="font-size:1.8rem;font-weight:700;color:#0EA5E9">{bmr:.0f} <span style="font-size:1rem">kcal/day</span></div>
            </div>
            <div class="glass-card">
                <div style="font-size:0.9rem;color:#64748B">Total Daily Energy Expenditure (TDEE)</div>
                <div style="font-size:1.8rem;font-weight:700;color:#10B981">{tdee:.0f} <span style="font-size:1rem">kcal/day</span></div>
            </div>
            <div class="glass-card">
                <div style="font-size:0.9rem;color:#64748B">Target Calories ({c_goal})</div>
                <div style="font-size:2rem;font-weight:800;color:#FBBF24">{target:.0f} <span style="font-size:1rem">kcal/day</span></div>
            </div>
            """, unsafe_allow_html=True)

            # Macro breakdown (50/30/20 carbs/protein/fat)
            protein_g = target * 0.30 / 4
            carbs_g   = target * 0.50 / 4
            fat_g     = target * 0.20 / 9

            fig = go.Figure(go.Pie(
                labels=["Carbohydrates", "Protein", "Fat"],
                values=[carbs_g, protein_g, fat_g],
                hole=0.5,
                marker=dict(colors=["#0EA5E9","#10B981","#FBBF24"]),
                texttemplate="%{label}<br>%{value:.0f}g",
                textfont=dict(color="#E2E8F0"),
            ))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#94A3B8",
                              height=250, showlegend=False, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)
            st.caption("Recommended macro breakdown: 50% carbs / 30% protein / 20% fat")


# ── Tab 3: Water Intake ───────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### 💧 Daily Water Intake Calculator")
    col1, col2 = st.columns(2)
    with col1:
        w_weight   = st.number_input("Weight (kg)", 20.0, 300.0, 70.0, 0.5, key="w_wt")
        w_activity = st.selectbox("Activity Level", ["Low", "Moderate", "High"], key="w_act")
        w_climate  = st.selectbox("Climate", ["Temperate", "Hot/Humid"], key="w_cl")
        w_pregnant = st.checkbox("Pregnant/Breastfeeding", key="w_pg")

    with col2:
        if st.button("Calculate Water Intake", use_container_width=True):
            base = w_weight * 35  # ml
            if w_activity == "Moderate": base += 400
            elif w_activity == "High":   base += 800
            if w_climate == "Hot/Humid": base += 500
            if w_pregnant:               base += 400
            liters   = base / 1000
            glasses  = base / 250

            st.markdown(f"""
            <div class="glass-card" style="text-align:center">
                <div style="font-size:4rem">💧</div>
                <div style="font-size:2.5rem;font-weight:800;color:#0EA5E9">{liters:.1f} L</div>
                <div style="color:#94A3B8">per day</div>
                <div style="margin-top:0.5rem;color:#64748B">{glasses:.0f} glasses of 250mL</div>
            </div>
            """, unsafe_allow_html=True)

            # Hourly reminder
            waking_hours = 16
            per_hour = base / waking_hours
            st.info(f"💡 Drink approximately **{per_hour:.0f} mL ({per_hour/250:.1f} glasses) every hour** while awake to stay hydrated.")

            tips = [
                "Start your day with a glass of water before breakfast",
                "Carry a reusable water bottle with you at all times",
                "Set hourly reminders on your phone",
                "Drink a glass before each meal",
                "Choose water over sugary beverages",
                "Eat water-rich foods like cucumbers, watermelon, and oranges",
            ]
            for tip in tips:
                st.markdown(f"- {tip}")

        # Track daily intake
        st.divider()
        st.markdown("#### 📊 Track Today's Intake")
        intake_ml = st.slider("Glasses consumed today (250mL each)", 0, 20, 0, 1)
        if st.button("Log Water Intake"):
            save_vital(uid, "Water", intake_ml * 250, "mL")
            st.success(f"✅ Logged {intake_ml * 250} mL water intake!")


# ── Tab 4: Blood Pressure ─────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("### ❤️ Blood Pressure Checker")
    col1, col2 = st.columns(2)
    with col1:
        systolic  = st.number_input("Systolic (mmHg)", 70, 250, 120, 1)
        diastolic = st.number_input("Diastolic (mmHg)", 40, 150, 80, 1)
        pulse     = st.number_input("Pulse Rate (bpm)", 30, 200, 72, 1)

        if st.button("Analyze Blood Pressure", use_container_width=True):
            save_vital(uid, "Systolic BP",  systolic,  "mmHg")
            save_vital(uid, "Diastolic BP", diastolic, "mmHg")
            save_vital(uid, "Pulse",        pulse,     "bpm")

            # Classification
            if systolic < 90 or diastolic < 60:
                cat, color, advice = "Low Blood Pressure (Hypotension)", "#3B82F6", "Increase fluid and salt intake. Consult a doctor if symptomatic."
            elif systolic < 120 and diastolic < 80:
                cat, color, advice = "Normal", "#10B981", "Your blood pressure is healthy! Keep it up."
            elif systolic < 130 and diastolic < 80:
                cat, color, advice = "Elevated", "#A3E635", "Adopt a heart-healthy lifestyle to prevent hypertension."
            elif systolic < 140 or diastolic < 90:
                cat, color, advice = "Hypertension Stage 1", "#FBBF24", "Consult a doctor. Reduce sodium, exercise regularly."
            elif systolic >= 140 or diastolic >= 90:
                cat, color, advice = "Hypertension Stage 2", "#F97316", "See a doctor promptly. Medication may be required."
            if systolic > 180 or diastolic > 120:
                cat, color, advice = "Hypertensive Crisis ⚠️", "#EF4444", "SEEK EMERGENCY MEDICAL CARE IMMEDIATELY!"

            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:1.5rem;font-weight:800;color:{color}">{cat}</div>
                <div style="font-size:2rem;color:#E2E8F0;margin:0.5rem 0">
                    {systolic}/{diastolic} <span style="font-size:1rem;color:#64748B">mmHg</span>
                </div>
                <div style="color:#94A3B8">{advice}</div>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # BP history
        sys_vitals  = get_vitals(uid, "Systolic BP")
        dias_vitals = get_vitals(uid, "Diastolic BP")
        if sys_vitals:
            df_sys  = pd.DataFrame(sys_vitals)
            df_dias = pd.DataFrame(dias_vitals) if dias_vitals else pd.DataFrame()
            df_sys["recorded_at"] = pd.to_datetime(df_sys["recorded_at"])

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df_sys["recorded_at"], y=df_sys["value"],
                                     mode="lines+markers", name="Systolic",
                                     line=dict(color="#EF4444", width=2)))
            if not df_dias.empty:
                df_dias["recorded_at"] = pd.to_datetime(df_dias["recorded_at"])
                fig.add_trace(go.Scatter(x=df_dias["recorded_at"], y=df_dias["value"],
                                         mode="lines+markers", name="Diastolic",
                                         line=dict(color="#3B82F6", width=2)))
            fig.add_hrect(y0=90, y1=120, fillcolor="rgba(16,185,129,0.1)", line_width=0)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#94A3B8", height=300, margin=dict(l=10,r=10,t=30,b=10),
                               title="BP History")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Log your blood pressure readings to see history here.")


# ── Tab 5: Heart Rate ─────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("### 💓 Heart Rate Checker")
    col1, col2 = st.columns(2)
    with col1:
        hr_age    = st.number_input("Age", 10, 100, 30, 1, key="hr_age")
        hr_bpm    = st.number_input("Resting Heart Rate (bpm)", 30, 220, 72, 1, key="hr_bpm")
        hr_fitness= st.selectbox("Fitness Level", ["Poor", "Below Average", "Average", "Above Average", "Excellent"])

        if st.button("Analyze Heart Rate", use_container_width=True):
            save_vital(uid, "Heart Rate", hr_bpm, "bpm")
            max_hr = 220 - hr_age

            # Resting HR categories
            if hr_bpm < 40:   hr_cat, hr_col = "Very Low (consult doctor)", "#3B82F6"
            elif hr_bpm < 60: hr_cat, hr_col = "Athletic / Excellent", "#10B981"
            elif hr_bpm < 70: hr_cat, hr_col = "Normal (fit)", "#A3E635"
            elif hr_bpm < 80: hr_cat, hr_col = "Normal", "#FBBF24"
            elif hr_bpm < 90: hr_cat, hr_col = "Above Normal", "#F97316"
            elif hr_bpm < 100:hr_cat, hr_col = "Elevated (Tachycardia)", "#EF4444"
            else:             hr_cat, hr_col = "High — See a Doctor", "#991B1B"

            hr_zones = {
                "Rest / Recovery":    (0.50, 0.60),
                "Fat Burning":        (0.60, 0.70),
                "Aerobic Fitness":    (0.70, 0.80),
                "Anaerobic Endurance":(0.80, 0.90),
                "Maximum Effort":     (0.90, 1.00),
            }

            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:1.5rem;font-weight:800;color:{hr_col}">{hr_cat}</div>
                <div style="font-size:2rem;color:#E2E8F0;margin:0.5rem 0">{hr_bpm} <span style="font-size:1rem;color:#64748B">bpm</span></div>
                <div style="color:#64748B">Max Heart Rate: <strong style="color:#0EA5E9">{max_hr} bpm</strong></div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("#### 🏃 Heart Rate Training Zones")
            for zone_name, (lo, hi) in hr_zones.items():
                lo_bpm = int(max_hr * lo)
                hi_bpm = int(max_hr * hi)
                in_zone = lo_bpm <= hr_bpm <= hi_bpm
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:0.5rem;
                            background:{'rgba(14,165,233,0.15)' if in_zone else 'rgba(30,41,59,0.4)'};
                            border-radius:8px;margin-bottom:4px;">
                    <span style="color:#E2E8F0">{'▶ ' if in_zone else '  '}{zone_name}</span>
                    <span style="color:#0EA5E9;font-weight:600">{lo_bpm}–{hi_bpm} bpm</span>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        hr_vitals = get_vitals(uid, "Heart Rate")
        if hr_vitals:
            df_hr = pd.DataFrame(hr_vitals)
            df_hr["recorded_at"] = pd.to_datetime(df_hr["recorded_at"])
            fig = px.line(df_hr, x="recorded_at", y="value", markers=True,
                          color_discrete_sequence=["#EF4444"],
                          labels={"recorded_at":"Date","value":"BPM"},
                          title="Heart Rate History")
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#94A3B8", height=300, margin=dict(l=10,r=10,t=40,b=10))
            fig.add_hrect(y0=60, y1=100, fillcolor="rgba(16,185,129,0.1)", line_width=0)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Log your heart rate to see history here.")


# ── Tab 6: Daily Health Score ─────────────────────────────────────────────────
with tabs[5]:
    st.markdown("### ⭐ Daily Health Score")
    st.markdown("Answer a few quick questions to calculate today's overall health score.")

    with st.form("health_score_form"):
        q1  = st.slider("Hours of sleep last night",      0, 12, 7)
        q2  = st.slider("Glasses of water consumed",      0, 20, 8)
        q3  = st.slider("Minutes of physical activity",   0, 180, 30)
        q4  = st.selectbox("How would you rate your diet today?", ["Poor","Fair","Good","Excellent"])
        q5  = st.selectbox("Stress level today",           ["Very High","High","Moderate","Low","None"])
        q6  = st.checkbox("Did you take all medications on time?")
        q7  = st.checkbox("Did you avoid alcohol and smoking today?")
        q8  = st.selectbox("Overall energy level",        ["Very Low","Low","Moderate","High","Very High"])
        calc= st.form_submit_button("Calculate Health Score", use_container_width=True)

    if calc:
        # Weighted scoring
        sleep_score  = min(q1/8, 1.0) * 20
        water_score  = min(q2/8, 1.0) * 15
        activity_score=min(q3/60,1.0) * 20
        diet_score   = {"Poor":0,"Fair":5,"Good":10,"Excellent":15}[q4]
        stress_score = {"Very High":0,"High":3,"Moderate":6,"Low":10,"None":12}[q5]
        med_score    = 8 if q6 else 0
        lifestyle_sc = 6 if q7 else 0
        energy_score = {"Very Low":0,"Low":1,"Moderate":2,"High":3,"Very High":4}[q8]

        total = sleep_score + water_score + activity_score + diet_score + stress_score + med_score + lifestyle_sc + energy_score
        total = min(total, 100)

        if total >= 80:   grade, color, msg = "Excellent", "#10B981", "You're doing great! Keep up the healthy habits."
        elif total >= 60: grade, color, msg = "Good",      "#A3E635", "Good job! A few small improvements can take you to excellent."
        elif total >= 40: grade, color, msg = "Fair",      "#FBBF24", "There's room for improvement. Focus on sleep, hydration, and activity."
        else:             grade, color, msg = "Needs Work", "#EF4444", "Let's work on building healthier daily habits."

        save_vital(uid, "Health Score", total, "points")

        col_g, col_r = st.columns([1, 2])
        with col_g:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=total,
                number={"suffix":"/100","font":{"color":"#E2E8F0","size":32}},
                gauge={
                    "axis":{"range":[0,100],"tickcolor":"#64748B"},
                    "bar": {"color": color},
                    "steps":[
                        {"range":[0,40],  "color":"rgba(239,68,68,0.15)"},
                        {"range":[40,60], "color":"rgba(251,191,36,0.15)"},
                        {"range":[60,80], "color":"rgba(163,230,53,0.15)"},
                        {"range":[80,100],"color":"rgba(16,185,129,0.15)"},
                    ],
                    "bgcolor":"rgba(30,41,59,0.5)","bordercolor":"rgba(148,163,184,0.2)",
                },
                title={"text":"Health Score","font":{"color":"#94A3B8"}},
            ))
            fig.update_layout(height=250, paper_bgcolor="rgba(0,0,0,0)",
                              font_color="#94A3B8", margin=dict(l=20,r=20,t=40,b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_r:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:1.8rem;font-weight:800;color:{color}">{grade}</div>
                <div style="color:#94A3B8;margin-top:0.5rem">{msg}</div>
            </div>
            """, unsafe_allow_html=True)

            breakdown = [
                ("Sleep",    sleep_score,   20,  "😴"),
                ("Hydration",water_score,   15,  "💧"),
                ("Activity", activity_score,20,  "🏃"),
                ("Diet",     diet_score,    15,  "🥗"),
                ("Stress",   stress_score,  12,  "🧘"),
                ("Meds",     med_score,      8,  "💊"),
                ("Lifestyle",lifestyle_sc,   6,  "🚭"),
                ("Energy",   energy_score,   4,  "⚡"),
            ]
            for label, score, max_s, icon in breakdown:
                pct = score / max_s if max_s > 0 else 0
                bar_col = "#10B981" if pct > 0.7 else "#FBBF24" if pct > 0.4 else "#EF4444"
                st.markdown(f"""
                <div style="margin-bottom:0.4rem">
                    <div style="display:flex;justify-content:space-between;color:#94A3B8;font-size:0.85rem">
                        <span>{icon} {label}</span><span>{score:.0f}/{max_s}</span>
                    </div>
                    <div style="background:rgba(30,41,59,0.8);border-radius:4px;height:6px;margin-top:3px">
                        <div style="background:{bar_col};width:{pct*100:.0f}%;height:6px;border-radius:4px"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
