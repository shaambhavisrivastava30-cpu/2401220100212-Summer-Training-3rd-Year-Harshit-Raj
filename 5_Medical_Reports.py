"""
Medical Reports — Upload PDF/Image reports, extract text, generate offline summaries.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import re
from datetime import datetime
from pathlib import Path

from utils.auth import require_auth
from utils.helpers import load_css, page_header, success_alert, danger_alert
from database.db_manager import save_medical_report, get_medical_reports, delete_medical_report

st.set_page_config(page_title="Medical Reports | HealthAI", page_icon="📋", layout="wide")
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

page_header("Medical Reports", "Upload, analyze, and manage your medical documents offline", "📋")

# Storage directory
REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports" / str(uid)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return "\n\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_image_text(file_bytes: bytes) -> str:
    """Extract text from image using PIL (basic — no OCR in offline mode)."""
    try:
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(file_bytes))
        return f"[Image uploaded: {img.size[0]}x{img.size[1]} px, mode={img.mode}]\nNote: Offline OCR requires Tesseract. Install pytesseract + tesseract for full text extraction."
    except Exception as e:
        return f"[Image processing error: {e}]"


def generate_offline_summary(text: str, filename: str) -> str:
    """Generate an intelligent offline summary using keyword analysis."""
    if not text or len(text) < 20:
        return "No text content could be extracted for summarization."

    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Keyword detection
    HEALTH_KEYWORDS = {
        "blood glucose":    "🩸 Blood glucose values detected",
        "hemoglobin":       "🔴 Hemoglobin (Hb) levels found",
        "creatinine":       "🫘 Kidney marker (creatinine) detected",
        "cholesterol":      "❤️ Cholesterol values present",
        "blood pressure":   "💉 Blood pressure readings found",
        "white blood":      "🔬 WBC (White Blood Cell) count present",
        "platelet":         "🔬 Platelet count detected",
        "thyroid":          "🦋 Thyroid markers found",
        "liver":            "🫀 Liver function markers detected",
        "urine":            "💛 Urinalysis results present",
        "ecg":              "❤️ ECG / Electrocardiogram data detected",
        "x-ray":            "🩻 X-ray report detected",
        "mri":              "🧲 MRI scan report detected",
        "ct scan":          "🔍 CT scan report detected",
        "ultrasound":       "📡 Ultrasound report detected",
        "biopsy":           "🔬 Biopsy results present",
        "prescription":     "💊 Prescription / medication information found",
        "diagnosis":        "📋 Diagnosis section detected",
        "normal":           "✅ 'Normal' results mentioned",
        "abnormal":         "⚠️ Abnormal values flagged in report",
    }

    detected = []
    text_lower = text.lower()
    for kw, msg in HEALTH_KEYWORDS.items():
        if kw in text_lower:
            detected.append(msg)

    # Extract numbers that look like test values
    values = re.findall(r"\b\d+\.?\d*\s*(?:mg/dL|g/dL|mmol|mEq|IU|bpm|mmHg|%|ng|mcg)\b", text, re.IGNORECASE)

    summary_parts = [f"**📄 Report Summary: {filename}**\n"]
    summary_parts.append(f"- **Document length:** {len(text)} characters, {len(lines)} lines\n")

    if detected:
        summary_parts.append("\n**🔍 Detected Health Markers:**")
        for d in detected:
            summary_parts.append(f"  - {d}")

    if values[:10]:
        summary_parts.append("\n**📊 Extracted Numeric Values:**")
        for v in values[:10]:
            summary_parts.append(f"  - {v.strip()}")

    # Key lines
    important_lines = [l for l in lines[:30] if any(kw in l.lower() for kw in list(HEALTH_KEYWORDS.keys()))]
    if important_lines:
        summary_parts.append("\n**📝 Key Lines from Report:**")
        for l in important_lines[:8]:
            summary_parts.append(f"  > {l}")

    summary_parts.append("\n\n---\n⚠️ *This automated summary is for reference only. Always have reports reviewed by a qualified healthcare professional.*")
    return "\n".join(summary_parts)


# ── Upload Section ─────────────────────────────────────────────────────────────
tab_upload, tab_reports = st.tabs(["📤 Upload Report", "📁 My Reports"])

with tab_upload:
    st.markdown("### 📤 Upload Medical Report")
    st.markdown("""
    <div class="alert-info">
        ℹ️ Supported formats: PDF, PNG, JPG, JPEG.
        All files are stored locally on your device. No data is sent to any server.
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "Choose a medical report file",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload a PDF or image file of your medical report"
    )

    if uploaded_file:
        file_type = uploaded_file.type
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size:1.2rem;font-weight:600;color:#E2E8F0">📄 {filename}</div>
                <div style="color:#64748B;margin-top:0.3rem">
                    Size: {len(file_bytes)/1024:.1f} KB &nbsp;|&nbsp; Type: {file_type}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.button("🔍 Analyze & Save Report", use_container_width=True):
                with st.spinner("Extracting text and generating summary..."):
                    # Extract text
                    if "pdf" in file_type:
                        extracted = extract_pdf_text(file_bytes)
                    elif any(t in file_type for t in ["png","jpeg","jpg","image"]):
                        extracted = extract_image_text(file_bytes)
                    else:
                        extracted = "[Unsupported file type]"

                    # Generate summary
                    summary = generate_offline_summary(extracted, filename)

                    # Save file
                    safe_name = re.sub(r"[^\w\-_\.]", "_", filename)
                    file_path = REPORTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
                    with open(file_path, "wb") as f:
                        f.write(file_bytes)

                    # Save to DB
                    save_medical_report(uid, filename, file_type, extracted, summary, str(file_path))

                st.success("✅ Report analyzed and saved successfully!")

                # Show results
                st.markdown("#### 📊 Extracted Text")
                st.text_area("Raw Text Content", extracted[:3000] + ("..." if len(extracted) > 3000 else ""),
                             height=200, disabled=True)

                st.markdown("#### 📋 AI-Generated Summary")
                st.markdown(summary)

                if "png" in file_type or "jpeg" in file_type or "jpg" in file_type:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(file_bytes))
                    st.image(img, caption=filename, use_column_width=True)

# ── Reports List ───────────────────────────────────────────────────────────────
with tab_reports:
    st.markdown("### 📁 My Medical Reports")
    reports = get_medical_reports(uid)

    if not reports:
        st.markdown("""
        <div class="glass-card" style="text-align:center;padding:3rem">
            <div style="font-size:3rem">📁</div>
            <div style="color:#64748B;margin-top:0.5rem">No reports uploaded yet.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for report in reports:
            with st.expander(f"📄 {report['filename']} — {report['created_at'][:16]}"):
                col_info, col_actions = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**Type:** {report.get('file_type','Unknown')} &nbsp;|&nbsp; **Uploaded:** {report['created_at'][:16]}")
                with col_actions:
                    if st.button("🗑️ Delete", key=f"del_{report['id']}"):
                        delete_medical_report(report['id'], uid)
                        st.success("Report deleted.")
                        st.rerun()

                tab_s, tab_t = st.tabs(["📋 Summary", "📝 Raw Text"])
                with tab_s:
                    if report.get("summary"):
                        st.markdown(report["summary"])
                    else:
                        st.info("No summary available.")
                with tab_t:
                    if report.get("extracted_text"):
                        st.text_area("Extracted Text", report["extracted_text"][:2000], height=200, disabled=True)
                    else:
                        st.info("No text extracted.")
