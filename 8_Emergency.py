"""
Emergency Module — Emergency contacts, hospital database, first-aid instructions, SOS screen.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from datetime import datetime

from utils.auth import require_auth
from utils.helpers import load_css, page_header
from database.db_manager import (
    add_emergency_contact, get_emergency_contacts, delete_emergency_contact
)

st.set_page_config(page_title="Emergency | HealthAI", page_icon="🚨", layout="wide")
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

page_header("Emergency Module", "Emergency contacts, hospitals, first-aid, and SOS", "🚨")

# ── SOS Banner ────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,rgba(239,68,68,0.2),rgba(220,38,38,0.1));
            border:2px solid #EF4444; border-radius:16px; padding:1.5rem;
            text-align:center; margin-bottom:1.5rem; animation:pulse 2s infinite;">
    <div style="font-size:2.5rem">🚨</div>
    <h2 style="color:#EF4444;margin:0.5rem 0">MEDICAL EMERGENCY?</h2>
    <p style="color:#FCA5A5;font-size:1.1rem;margin:0">
        Call <strong>911</strong> (US) | <strong>112</strong> (EU/India) | <strong>999</strong> (UK) | <strong>000</strong> (AU)
    </p>
    <p style="color:#94A3B8;font-size:0.85rem;margin-top:0.5rem">
        Do not delay emergency services for life-threatening situations
    </p>
</div>
""", unsafe_allow_html=True)

tab_contacts, tab_hospitals, tab_firstaid, tab_sos = st.tabs(
    ["📞 Emergency Contacts", "🏥 Nearby Hospitals", "🩹 First Aid", "🆘 SOS Screen"]
)

# ── Emergency Contacts ────────────────────────────────────────────────────────
with tab_contacts:
    contacts = get_emergency_contacts(uid)

    col_list, col_add = st.columns([3, 2])

    with col_list:
        st.markdown("### 📞 Your Emergency Contacts")
        if not contacts:
            st.markdown("""
            <div class="glass-card" style="text-align:center;padding:2rem">
                <div style="font-size:2.5rem">📞</div>
                <div style="color:#64748B;margin-top:0.5rem">No emergency contacts added yet.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for c in contacts:
                primary_badge = '<span style="background:#0EA5E9;color:white;padding:2px 8px;border-radius:10px;font-size:0.7rem;margin-left:0.5rem">PRIMARY</span>' if c["is_primary"] else ""
                st.markdown(f"""
                <div class="glass-card" style="border-left:3px solid {'#0EA5E9' if c['is_primary'] else '#64748B'}">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start">
                        <div>
                            <div style="font-weight:700;color:#E2E8F0">
                                {c['name']}{primary_badge}
                            </div>
                            <div style="color:#94A3B8;font-size:0.9rem;margin-top:0.3rem">
                                👥 {c.get('relationship','') or 'Contact'} &nbsp;|&nbsp;
                                📱 {c['phone']}
                            </div>
                            {f"<div style='color:#64748B;font-size:0.85rem'>📧 {c.get('email','')}</div>" if c.get('email') else ""}
                        </div>
                        <div>
                            <a href="tel:{c['phone']}" style="background:linear-gradient(135deg,#0EA5E9,#10B981);color:white;padding:6px 14px;border-radius:8px;text-decoration:none;font-size:0.85rem;font-weight:600">
                                📞 Call
                            </a>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"🗑️ Remove {c['name']}", key=f"del_ec_{c['id']}"):
                    delete_emergency_contact(c["id"], uid)
                    st.rerun()

    with col_add:
        st.markdown("### ➕ Add Contact")
        with st.form("add_contact_form"):
            name         = st.text_input("Full Name *", placeholder="John Doe")
            relationship = st.selectbox("Relationship",
                ["Spouse/Partner", "Parent", "Child", "Sibling", "Friend", "Doctor", "Neighbor", "Other"])
            phone        = st.text_input("Phone Number *", placeholder="+1 (555) 000-0000")
            email        = st.text_input("Email (optional)", placeholder="contact@email.com")
            is_primary   = st.checkbox("Set as Primary Contact")
            add_btn      = st.form_submit_button("Add Contact", use_container_width=True)

        if add_btn:
            if not name.strip() or not phone.strip():
                st.error("Name and phone are required.")
            else:
                add_emergency_contact(uid, name.strip(), relationship, phone.strip(),
                                      email.strip() or None, is_primary)
                st.success(f"✅ {name} added as emergency contact!")
                st.rerun()


# ── Nearby Hospitals Database ─────────────────────────────────────────────────
with tab_hospitals:
    st.markdown("### 🏥 Hospital Directory")
    st.markdown("""
    <div class="alert-info">
        ℹ️ This is a reference database. In a real emergency, always call your local emergency number.
        Search for hospitals near you using Google Maps or your local directory.
    </div>
    """, unsafe_allow_html=True)

    HOSPITALS_DB = [
        {"name": "City General Hospital",      "type": "Multi-specialty", "emergency": "24/7",  "phone": "555-0100", "services": "ER, ICU, Surgery, Cardiology, Neurology"},
        {"name": "St. Mary's Medical Center",  "type": "Multi-specialty", "emergency": "24/7",  "phone": "555-0200", "services": "ER, Maternity, Pediatrics, Oncology"},
        {"name": "Children's Hospital",        "type": "Pediatric",       "emergency": "24/7",  "phone": "555-0300", "services": "Pediatric ER, NICU, Pediatric Surgery"},
        {"name": "Heart Care Institute",       "type": "Cardiac",         "emergency": "24/7",  "phone": "555-0400", "services": "Cath Lab, Cardiac Surgery, ICU, Echocardiography"},
        {"name": "NeuroHealth Center",         "type": "Neurological",    "emergency": "24/7",  "phone": "555-0500", "services": "Stroke Unit, Neurosurgery, MRI, EEG"},
        {"name": "Metro Urgent Care",          "type": "Urgent Care",     "emergency": "8am-10pm","phone": "555-0600","services": "Minor injuries, X-rays, Lab tests"},
        {"name": "Women's Health Clinic",      "type": "Gynecology",      "emergency": "Mon-Sat","phone": "555-0700","services": "Obstetrics, Gynecology, Mammography"},
        {"name": "Regional Cancer Center",     "type": "Oncology",        "emergency": "9am-5pm","phone": "555-0800","services": "Chemotherapy, Radiation, Oncology consultations"},
        {"name": "Community Health Clinic",    "type": "Primary Care",    "emergency": "Mon-Fri","phone": "555-0900","services": "General medicine, Vaccinations, Lab work"},
        {"name": "Ortho & Spine Center",       "type": "Orthopedic",      "emergency": "24/7",  "phone": "555-1000","services": "Fractures, Joint replacement, Spine surgery"},
    ]

    type_filter = st.selectbox("Filter by Type", ["All"] + sorted(set(h["type"] for h in HOSPITALS_DB)))
    search      = st.text_input("Search hospitals...", placeholder="Search by name or services")

    filtered_hospitals = HOSPITALS_DB
    if type_filter != "All":
        filtered_hospitals = [h for h in filtered_hospitals if h["type"] == type_filter]
    if search:
        s = search.lower()
        filtered_hospitals = [h for h in filtered_hospitals
                               if s in h["name"].lower() or s in h["services"].lower()]

    for hosp in filtered_hospitals:
        em_color = "#10B981" if hosp["emergency"] == "24/7" else "#FBBF24"
        st.markdown(f"""
        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                    <div style="font-size:1rem;font-weight:700;color:#E2E8F0">🏥 {hosp['name']}</div>
                    <div style="color:#94A3B8;margin-top:0.3rem">
                        <span style="background:rgba(14,165,233,0.15);color:#0EA5E9;padding:2px 8px;border-radius:10px;font-size:0.75rem">{hosp['type']}</span>
                        &nbsp;
                        <span style="background:rgba(0,0,0,0.2);color:{em_color};padding:2px 8px;border-radius:10px;font-size:0.75rem">⏰ {hosp['emergency']}</span>
                    </div>
                    <div style="color:#64748B;font-size:0.82rem;margin-top:0.5rem">🩺 {hosp['services']}</div>
                </div>
                <div style="text-align:right;color:#0EA5E9;font-weight:600">📞 {hosp['phone']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── First Aid Instructions ────────────────────────────────────────────────────
with tab_firstaid:
    st.markdown("### 🩹 First Aid Quick Reference")
    st.markdown("""
    <div class="alert-warning">
        ⚠️ These are basic first aid guidelines. Always seek professional medical help.
        Call emergency services for serious injuries or illnesses.
    </div>
    """, unsafe_allow_html=True)

    FIRST_AID = {
        "🫀 CPR (Cardiopulmonary Resuscitation)": """
**When to use:** Person is unresponsive and not breathing normally.

**Steps:**
1. Call emergency services (911/112) immediately
2. Place person on their back on a firm surface
3. Tilt head back, lift chin to open airway
4. Give 2 rescue breaths (1 second each) if trained
5. Begin chest compressions:
   - Place heel of hand on center of chest (lower half of sternum)
   - Interlock fingers, keep arms straight
   - Press down 2–2.4 inches (5–6 cm), 100–120 times/minute
6. Continue: 30 compressions → 2 breaths
7. Use AED as soon as available
8. Continue until help arrives or person recovers

⚡ **Hands-only CPR:** If untrained, skip rescue breaths and do continuous chest compressions (100–120/min)
""",
        "🩸 Severe Bleeding": """
**Steps:**
1. Call emergency services for severe bleeding
2. Put on gloves if available
3. Apply firm, direct pressure with clean cloth/bandage
4. Do NOT remove the cloth — add more on top if soaked through
5. Elevate the injured limb above heart level (if possible)
6. Maintain pressure for at least 10–15 minutes
7. Tourniquet: Apply 2–3 inches above wound only for life-threatening limb bleeding

⚠️ Do NOT remove embedded objects — stabilize them in place
""",
        "🌡️ Burns": """
**For Minor Burns (1st degree — redness, no blisters):**
1. Cool with cool (not ice-cold) running water for 10–20 minutes
2. Do not use ice, butter, or toothpaste
3. Cover with sterile non-stick dressing
4. Take OTC pain relief if needed

**For Severe Burns (2nd/3rd degree — blisters, charring):**
1. Call emergency services immediately
2. Cool the burn with water (not ice)
3. Do NOT burst blisters
4. Cover loosely with clean cling film or non-fluffy material
5. Remove jewelry near the burned area (before swelling)
6. Do NOT remove burnt clothing stuck to skin
""",
        "😮‍💨 Choking": """
**Conscious Adult/Child (over 1 year):**
1. Ask: "Are you choking?" — if can't speak/cough/breathe:
2. Give 5 sharp back blows between shoulder blades (heel of hand)
3. Give 5 abdominal thrusts (Heimlich maneuver):
   - Stand behind person, hands around waist
   - Fist above navel, grasp with other hand
   - Pull sharply inward and upward
4. Alternate 5 back blows + 5 abdominal thrusts
5. Call emergency if object not dislodged
6. If person becomes unconscious → begin CPR

**Infant (under 1 year):**
1. 5 back blows face-down on your forearm
2. 5 chest thrusts (not abdominal)
""",
        "⚡ Seizures": """
**Steps:**
1. Stay calm — do NOT restrain the person
2. Time the seizure
3. Clear area of dangerous objects
4. Cushion their head with something soft
5. Gently turn them onto their side if possible (recovery position)
6. Do NOT put anything in their mouth
7. Do NOT give water or food until fully conscious

**Call emergency services if:**
- Seizure lasts more than 5 minutes
- Person doesn't regain consciousness
- Another seizure follows immediately
- Person is injured, pregnant, or diabetic
- First-ever seizure
""",
        "🤕 Head Injury": """
**Steps:**
1. Call emergency for loss of consciousness, confusion, seizures
2. Stop any bleeding with gentle pressure
3. Do NOT remove objects penetrating the skull
4. Keep person still — suspect possible neck/spine injury
5. Monitor breathing and consciousness

**Warning Signs — Seek Emergency Care:**
- Confusion or memory loss
- Repeated vomiting
- Severe headache
- Loss of consciousness (even briefly)
- Clear fluid from nose/ears
- Unequal pupils
- Weakness in limbs
""",
        "🐝 Allergic Reaction / Anaphylaxis": """
**Mild Allergic Reaction:**
- Take antihistamine (e.g., diphenhydramine)
- Monitor for worsening symptoms

**Anaphylaxis (Severe) — CALL 911 IMMEDIATELY:**
Signs: throat swelling, difficulty breathing, collapse, rapid heartbeat, pale/bluish skin

1. Use epinephrine auto-injector (EpiPen) if available
   - Inject into outer thigh (through clothing is OK)
2. Call emergency services
3. Lay person flat — do NOT let them stand up
4. Give a second EpiPen after 5–15 min if no improvement
5. Begin CPR if they lose consciousness and stop breathing
""",
        "🌡️ Heat Stroke": """
**Signs:** High body temp (>40°C/104°F), hot/dry skin, confusion, no sweating, rapid pulse

**Steps:**
1. Call emergency services immediately
2. Move person to cool shaded area
3. Remove excess clothing
4. Cool rapidly: cold wet towels, fan, ice packs to neck/armpits/groin
5. Do NOT give fluids if unconscious
6. Give cool water if conscious and able to swallow
7. Continue cooling until help arrives
""",
        "🥶 Hypothermia": """
**Signs:** Shivering, slurred speech, slow pulse, pale/blue skin, confusion

**Steps:**
1. Call emergency services
2. Move person to warm, dry area
3. Remove wet clothing
4. Wrap in blankets, cover head
5. Place warm water bottles (wrapped) in armpits/groin — NOT direct on skin
6. Give warm (not hot) drinks if conscious
7. Do NOT rub the skin vigorously
""",
    }

    for topic, instructions in FIRST_AID.items():
        with st.expander(topic):
            st.markdown(instructions)


# ── SOS Screen ────────────────────────────────────────────────────────────────
with tab_sos:
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(239,68,68,0.25),rgba(220,38,38,0.1));
                border:2px solid #EF4444; border-radius:20px; padding:2.5rem;
                text-align:center; margin-bottom:2rem">
        <div style="font-size:4rem; animation:pulse 1s infinite">🆘</div>
        <h1 style="color:#EF4444; font-size:2.5rem; margin:0.5rem 0">EMERGENCY SOS</h1>
        <p style="color:#FCA5A5; font-size:1.2rem; margin:0">Medical Emergency Dashboard</p>
    </div>
    """, unsafe_allow_html=True)

    # Emergency numbers
    st.markdown("### 📞 Global Emergency Numbers")
    numbers = [
        ("🇺🇸 USA",       "911"),
        ("🇬🇧 UK",        "999 / 112"),
        ("🇪🇺 EU",        "112"),
        ("🇮🇳 India",     "112 / 108"),
        ("🇦🇺 Australia", "000"),
        ("🇨🇦 Canada",    "911"),
        ("🇳🇿 New Zealand","111"),
        ("🇯🇵 Japan",     "119 (medical) / 110 (police)"),
    ]
    cols = st.columns(4)
    for i, (country, number) in enumerate(numbers):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                        border-radius:12px;padding:1rem;text-align:center;margin-bottom:0.5rem">
                <div style="font-size:1.2rem">{country}</div>
                <div style="font-size:1.8rem;font-weight:800;color:#EF4444">{number}</div>
            </div>
            """, unsafe_allow_html=True)

    # Emergency contacts for current user
    st.markdown("### 📱 Your Emergency Contacts")
    ec = get_emergency_contacts(uid)
    if ec:
        for c in ec:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;
                        background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
                        border-radius:12px;padding:1.2rem;margin-bottom:0.5rem">
                <div>
                    <span style="font-size:1.1rem;font-weight:700;color:#E2E8F0">{c['name']}</span>
                    <span style="color:#94A3B8;margin-left:1rem">{c.get('relationship','')}</span>
                </div>
                <a href="tel:{c['phone']}" style="background:#EF4444;color:white;padding:10px 20px;
                   border-radius:10px;text-decoration:none;font-size:1rem;font-weight:700">
                    📞 {c['phone']}
                </a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ No emergency contacts added. Please add contacts in the Emergency Contacts tab.")

    # What to tell emergency services
    st.markdown("### 📋 What to Tell Emergency Services")
    st.markdown("""
    <div class="glass-card">
        <ol style="color:#E2E8F0; line-height:2">
            <li><strong>Your exact location</strong> — street address, landmarks, floor/room number</li>
            <li><strong>Your phone number</strong> — in case you get disconnected</li>
            <li><strong>What happened</strong> — describe the emergency clearly</li>
            <li><strong>Number of people involved</strong> and any injuries</li>
            <li><strong>Current condition</strong> of the patient (conscious, breathing, etc.)</li>
            <li><strong>Any relevant medical history</strong> — allergies, medications, conditions</li>
        </ol>
        <div style="background:rgba(239,68,68,0.1);padding:0.8rem;border-radius:8px;margin-top:1rem">
            <strong style="color:#EF4444">⚡ Stay on the line</strong>
            <span style="color:#94A3B8"> — Do not hang up until the dispatcher tells you to.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Patient info card
    fresh_user = user
    st.markdown("### 🪪 Patient Information Card")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(14,165,233,0.15),rgba(16,185,129,0.1));
                border:1px solid rgba(14,165,233,0.3);border-radius:16px;padding:1.5rem">
        <div style="font-size:1.3rem;font-weight:700;color:#0EA5E9;margin-bottom:1rem">
            🪪 {fresh_user.get('full_name') or fresh_user['username']}
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;color:#E2E8F0">
            <div>👤 Age: <strong>{fresh_user.get('age','Unknown')}</strong></div>
            <div>⚥ Gender: <strong>{fresh_user.get('gender','Unknown')}</strong></div>
            <div>🩸 Blood Group: <strong style="color:#EF4444">{fresh_user.get('blood_group','Unknown')}</strong></div>
            <div>📱 Phone: <strong>{fresh_user.get('phone','Unknown')}</strong></div>
        </div>
        <div style="margin-top:0.8rem;color:#64748B;font-size:0.85rem">
            Update your profile from the Dashboard to keep this card current.
        </div>
    </div>
    """, unsafe_allow_html=True)
