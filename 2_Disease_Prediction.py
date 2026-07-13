"""
Disease Prediction — ML-based predictions for 5 diseases using local models.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import plotly.graph_objects as go

from utils.auth import require_auth
from utils.helpers import load_css, page_header, risk_badge, success_alert, warning_alert, danger_alert
from database.db_manager import save_prediction
from models.model_trainer import train_all_models, models_exist
from models.predictor import predict, DISEASE_FEATURES

st.set_page_config(page_title="Disease Prediction | HealthAI", page_icon="🔬", layout="wide")
load_css()

user = require_auth()
uid  = user["id"]

with st.sidebar:
    st.markdown(f"**👤 {user.get('full_name') or user['username']}**")
    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated", "user"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")

page_header("Disease Prediction", "AI-powered disease risk assessment using local ML models", "🔬")

# ── Model Training ─────────────────────────────────────────────────────────────
if not models_exist():
    st.markdown("""
    <div class="glass-card" style="text-align:center; padding:2rem;">
        <div style="font-size:2.5rem">🤖</div>
        <h3 style="color:#E2E8F0">ML Models Not Yet Trained</h3>
        <p style="color:#94A3B8">Click the button below to train all 5 disease prediction models locally.
        This is a one-time setup (~30 seconds) and requires no internet.</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚀 Train All Models Now", use_container_width=True):
        progress_bar = st.progress(0.0)
        status_text  = st.empty()
        def cb(val, msg):
            progress_bar.progress(val)
            status_text.markdown(f"**{msg}**")
        results = train_all_models(progress_callback=cb)
        progress_bar.empty()
        status_text.empty()
        st.success("✅ All models trained successfully!")
        for name, acc in results.items():
            st.markdown(f"- **{name.replace('_',' ').title()}**: {acc:.1%} accuracy")
        st.rerun()
    st.stop()

# ── Disease Selector ──────────────────────────────────────────────────────────
disease_options = {k: f"{v['icon']} {v['title']}" for k, v in DISEASE_FEATURES.items()}
selected_key = st.selectbox("Select Disease to Predict", options=list(disease_options.keys()),
                             format_func=lambda k: disease_options[k])

info = DISEASE_FEATURES[selected_key]
st.markdown(f"""
<div class="glass-card">
    <div style="font-size:1.5rem; font-weight:700; color:#0EA5E9">{info['icon']} {info['title']}</div>
    <div style="color:#94A3B8; margin-top:0.3rem">{info['description']}</div>
</div>
""", unsafe_allow_html=True)

# ── Input Form ────────────────────────────────────────────────────────────────
with st.form(f"predict_form_{selected_key}"):
    st.markdown("#### 📝 Enter Clinical Values")
    features_def = info["features"]
    n = len(features_def)
    cols_per_row = 3
    rows = [features_def[i:i+cols_per_row] for i in range(0, n, cols_per_row)]

    values = {}
    for row in rows:
        cols = st.columns(len(row))
        for col, feat in zip(cols, row):
            with col:
                if feat["type"] == "int":
                    values[feat["key"]] = col.number_input(
                        feat["label"],
                        min_value=int(feat["min"]),
                        max_value=int(feat["max"]),
                        value=int(feat["default"]),
                        step=int(feat["step"]),
                        key=f"{selected_key}_{feat['key']}"
                    )
                else:
                    values[feat["key"]] = col.number_input(
                        feat["label"],
                        min_value=float(feat["min"]),
                        max_value=float(feat["max"]),
                        value=float(feat["default"]),
                        step=float(feat["step"]),
                        format="%.3f",
                        key=f"{selected_key}_{feat['key']}"
                    )

    submitted = st.form_submit_button("🔍 Run Prediction", use_container_width=True)

# ── Prediction Result ─────────────────────────────────────────────────────────
if submitted:
    try:
        feature_list = [values[f["key"]] for f in features_def]
        result = predict(selected_key, feature_list)

        save_prediction(
            user_id=uid,
            disease_type=selected_key,
            input_data=values,
            prediction=result["label"],
            confidence=result["confidence"],
            risk_level=result["risk_level"],
            recommendations=result["recommendations"],
        )

        # Result display
        risk_colors = {"Low": "#10B981", "Medium": "#FBBF24", "High": "#EF4444"}
        risk_col    = risk_colors.get(result["risk_level"], "#94A3B8")

        col_gauge, col_info = st.columns([1, 2])

        with col_gauge:
            # Confidence gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=result["confidence"],
                number={"suffix": "%", "font": {"color": "#E2E8F0", "size": 36}},
                gauge={
                    "axis": {"range": [0, 100], "tickcolor": "#64748B"},
                    "bar": {"color": risk_col},
                    "bgcolor": "rgba(30,41,59,0.5)",
                    "bordercolor": "rgba(148,163,184,0.2)",
                    "steps": [
                        {"range": [0, 40],  "color": "rgba(16,185,129,0.15)"},
                        {"range": [40, 70], "color": "rgba(251,191,36,0.15)"},
                        {"range": [70, 100],"color": "rgba(239,68,68,0.15)"},
                    ],
                    "threshold": {"line": {"color": risk_col, "width": 3}, "value": result["confidence"]},
                },
                title={"text": "Confidence", "font": {"color": "#94A3B8"}},
            ))
            fig.update_layout(
                height=250,
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#94A3B8",
                margin=dict(l=20, r=20, t=40, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            pred_icon = "⚠️" if result["prediction"] == "Positive" else "✅"
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:1.1rem; color:#94A3B8; margin-bottom:0.5rem">Prediction Result</div>
                <div style="font-size:2rem; font-weight:800; color:{'#EF4444' if result['prediction']=='Positive' else '#10B981'}">
                    {pred_icon} {result['prediction']}
                </div>
                <div style="margin-top:0.8rem">
                    <span style="color:#64748B">Risk Level: </span>
                    {risk_badge(result['risk_level'])}
                </div>
                <div style="color:#64748B; margin-top:0.5rem; font-size:0.85rem">
                    Model Confidence: <strong style="color:#0EA5E9">{result['confidence']}%</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Recommendations
        st.markdown("#### 💡 Health Recommendations")
        for i, rec in enumerate(result["recommendations"]):
            icon = "⚠️" if i == 0 and result["prediction"] == "Positive" else "✅"
            st.markdown(f"""
            <div style="display:flex; gap:0.8rem; padding:0.6rem 0; border-bottom:1px solid rgba(148,163,184,0.1);">
                <span>{icon}</span>
                <span style="color:#E2E8F0">{rec}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div class="alert-warning" style="margin-top:1rem">
            ⚠️ <strong>Disclaimer:</strong> This prediction is for informational purposes only
            and is NOT a substitute for professional medical diagnosis. Always consult a qualified
            healthcare professional for medical advice.
        </div>
        """, unsafe_allow_html=True)

    except FileNotFoundError:
        st.error("Model not found. Please train models first.")
    except Exception as e:
        st.error(f"Prediction error: {e}")
