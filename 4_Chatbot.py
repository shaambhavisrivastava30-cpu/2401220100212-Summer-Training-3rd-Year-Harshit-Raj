"""
Offline Healthcare Chatbot — Rule-based, no internet required.
Uses keyword matching and intent classification for natural healthcare Q&A.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import re
from datetime import datetime

from utils.auth import require_auth
from utils.helpers import load_css, page_header
from database.db_manager import save_chat_message, get_chat_history, clear_chat_history

st.set_page_config(page_title="Health Chatbot | HealthAI", page_icon="💬", layout="wide")
load_css()

user = require_auth()
uid  = user["id"]

with st.sidebar:
    st.markdown(f"**👤 {user.get('full_name') or user['username']}**")
    st.divider()
    if st.button("🗑️ Clear History", use_container_width=True):
        clear_chat_history(uid)
        st.session_state.pop("chat_messages", None)
        st.rerun()
    if st.button("🚪 Logout", use_container_width=True):
        for k in ["authenticated","user","chat_messages"]:
            st.session_state.pop(k, None)
        st.switch_page("app.py")

page_header("Healthcare Chatbot", "Your offline AI health assistant — no internet required", "💬")

# ─────────────────────────────────────────────────────────────────────────────
# Chatbot Knowledge Base
# ─────────────────────────────────────────────────────────────────────────────

INTENTS = [
    {
        "name": "greeting",
        "patterns": ["hello","hi","hey","good morning","good afternoon","good evening","howdy"],
        "responses": [
            "Hello! I'm your HealthAI assistant. How can I help you today? 😊",
            "Hi there! I'm here to answer your health questions. What's on your mind?",
        ]
    },
    {
        "name": "goodbye",
        "patterns": ["bye","goodbye","see you","take care","farewell","exit","quit"],
        "responses": [
            "Take care of yourself! Remember to stay hydrated and get enough sleep. Goodbye! 👋",
            "Goodbye! Stay healthy and don't hesitate to return if you have more questions. 😊",
        ]
    },
    {
        "name": "thanks",
        "patterns": ["thank","thanks","thank you","thx","ty","appreciate"],
        "responses": [
            "You're welcome! I'm here whenever you need health guidance.",
            "Happy to help! Your health is important. 😊",
        ]
    },
    {
        "name": "diabetes",
        "patterns": ["diabetes","diabetic","blood sugar","glucose","insulin","type 1","type 2","hyperglycemia"],
        "responses": [
            """**Diabetes Overview** 🩸

Diabetes is a chronic condition where the body cannot properly regulate blood sugar (glucose).

**Types:**
- **Type 1:** Autoimmune — body doesn't produce insulin. Requires daily insulin therapy.
- **Type 2:** Most common — body doesn't use insulin effectively. Often preventable.
- **Gestational:** Occurs during pregnancy.

**Common Symptoms:**
- Frequent urination, excessive thirst
- Unexplained weight loss
- Blurred vision, fatigue
- Slow-healing wounds

**Management:**
- Monitor blood glucose regularly
- Follow a low-sugar, high-fiber diet
- Exercise at least 150 min/week
- Take medications/insulin as prescribed
- Attend regular check-ups

⚠️ *Please consult a doctor for diagnosis and treatment.*"""
        ]
    },
    {
        "name": "heart_disease",
        "patterns": ["heart","cardiac","cardiovascular","chest pain","heart attack","angina","coronary","artery","cholesterol"],
        "responses": [
            """**Heart Disease Information** ❤️

Heart disease refers to conditions affecting the heart's structure and function.

**Risk Factors:**
- High blood pressure & cholesterol
- Smoking, obesity, diabetes
- Family history, sedentary lifestyle
- Stress

**Warning Signs (seek emergency care immediately):**
- Chest pain or pressure
- Shortness of breath
- Pain radiating to arm, jaw, or back
- Dizziness, nausea, cold sweat

**Prevention:**
- Eat a heart-healthy diet (Mediterranean or DASH)
- Exercise regularly (150+ min/week)
- Quit smoking
- Manage stress
- Control blood pressure and cholesterol

🚨 *If you experience chest pain, call emergency services immediately.*"""
        ]
    },
    {
        "name": "hypertension",
        "patterns": ["hypertension","high blood pressure","blood pressure","bp","systolic","diastolic"],
        "responses": [
            """**Hypertension (High Blood Pressure)** 💉

Blood pressure is measured as systolic/diastolic (e.g., 120/80 mmHg).

**Categories:**
- Normal: < 120/80
- Elevated: 120–129/< 80
- Stage 1 Hypertension: 130–139/80–89
- Stage 2 Hypertension: ≥ 140/90
- Crisis (seek immediate care): > 180/120

**Lifestyle Changes:**
- Reduce sodium intake (< 2.3g/day)
- Follow DASH diet
- Exercise regularly
- Limit alcohol
- Quit smoking
- Manage stress with meditation/yoga

⚠️ *Hypertension is often silent. Regular monitoring is essential.*"""
        ]
    },
    {
        "name": "sleep",
        "patterns": ["sleep","insomnia","sleepless","tired","fatigue","rest","nap","bedtime","waking up"],
        "responses": [
            """**Sleep Health Tips** 😴

Adults need 7–9 hours of quality sleep per night.

**Tips for Better Sleep:**
- Keep a consistent sleep schedule (even on weekends)
- Create a dark, cool, quiet sleeping environment
- Avoid caffeine after 2 PM
- Limit screen time 1 hour before bed
- Avoid large meals close to bedtime
- Try relaxation techniques (deep breathing, meditation)
- Exercise regularly (but not within 2–3 hours of bedtime)

**Signs of Poor Sleep:**
- Daytime drowsiness, irritability
- Difficulty concentrating
- Mood changes

*If insomnia persists, consult a sleep specialist.*"""
        ]
    },
    {
        "name": "diet_nutrition",
        "patterns": ["diet","nutrition","food","eat","healthy eating","vegetables","fruits","protein","carbs","vitamins","minerals"],
        "responses": [
            """**Healthy Diet & Nutrition** 🥗

A balanced diet is the foundation of good health.

**Key Principles:**
- Fill half your plate with fruits and vegetables
- Choose whole grains over refined carbs
- Include lean proteins (fish, legumes, poultry)
- Limit saturated fats, sugar, and sodium
- Stay well hydrated (6–8 glasses of water daily)

**Superfoods to Include:**
- Leafy greens (spinach, kale)
- Berries, avocados, nuts
- Fatty fish (salmon, sardines)
- Legumes (lentils, chickpeas)
- Whole grains (oats, quinoa)

**Foods to Limit:**
- Processed/ultra-processed foods
- Sugary drinks and snacks
- Trans fats and fried foods"""
        ]
    },
    {
        "name": "exercise",
        "patterns": ["exercise","workout","fitness","gym","running","jogging","weight","strength","yoga","pilates","physical activity"],
        "responses": [
            """**Exercise & Physical Activity** 🏃

Regular exercise is one of the most powerful things you can do for your health.

**WHO Recommendations:**
- 150–300 min of moderate aerobic activity/week
- OR 75–150 min of vigorous activity/week
- Muscle-strengthening exercises 2+ days/week

**Types of Exercise:**
- **Cardio:** Walking, running, cycling, swimming
- **Strength:** Weight training, resistance bands
- **Flexibility:** Yoga, stretching
- **Balance:** Tai chi, pilates

**Benefits:**
- Reduces risk of heart disease, diabetes, cancer
- Improves mood and mental health
- Strengthens bones and muscles
- Aids weight management
- Boosts energy and sleep quality

*Start slowly and gradually increase intensity.*"""
        ]
    },
    {
        "name": "stress_mental",
        "patterns": ["stress","anxiety","depression","mental health","worried","nervous","panic","mood","sadness","mental"],
        "responses": [
            """**Mental Health & Stress Management** 🧘

Mental health is just as important as physical health.

**Signs of Stress/Anxiety:**
- Restlessness, irritability
- Racing thoughts, worry
- Physical symptoms (headache, muscle tension)
- Difficulty sleeping or concentrating

**Coping Strategies:**
- Deep breathing (4-7-8 technique)
- Mindfulness and meditation
- Regular physical exercise
- Social connection with loved ones
- Journaling your thoughts
- Limiting news and social media
- Adequate sleep and nutrition

**When to Seek Help:**
- Symptoms persist for 2+ weeks
- Interfering with daily life
- Thoughts of self-harm

*Please consult a mental health professional if symptoms are severe.*"""
        ]
    },
    {
        "name": "fever",
        "patterns": ["fever","temperature","febrile","hot","chills","sweating","38","39","40"],
        "responses": [
            """**Fever Information** 🌡️

A fever is a body temperature above 38°C (100.4°F).

**Levels:**
- Low-grade: 37.5–38.5°C
- Moderate: 38.5–39.5°C
- High: > 39.5°C (seek medical care)
- Dangerous: > 40°C (emergency)

**Home Remedies:**
- Rest and stay hydrated
- Cool compress on forehead
- Light, breathable clothing
- Paracetamol/ibuprofen as per dosage instructions

**See a Doctor If:**
- Fever > 39°C lasting > 48 hours
- Severe headache, rash, neck stiffness
- Difficulty breathing
- Confusion or extreme lethargy
- Infants under 3 months with any fever

🚨 *High fever with neck stiffness could indicate meningitis — seek emergency care.*"""
        ]
    },
    {
        "name": "headache",
        "patterns": ["headache","migraine","head pain","head ache","head hurts","throbbing"],
        "responses": [
            """**Headache Guide** 🤕

Headaches are one of the most common health complaints.

**Types:**
- **Tension headache:** Tight band around head, most common type
- **Migraine:** Severe, throbbing, often with nausea and light sensitivity
- **Cluster headache:** Severe pain around one eye
- **Secondary headache:** Caused by another condition (sinus, hypertension)

**Tension Headache Relief:**
- Rest in a quiet, dark room
- Apply a cold or warm compress
- Stay hydrated
- OTC pain relievers (follow dosage instructions)
- Stress management techniques

**See a Doctor If:**
- Sudden, extremely severe headache ("thunderclap")
- Headache with fever, stiff neck, or rash
- Following a head injury
- Worsening pattern or new headache type"""
        ]
    },
    {
        "name": "bmi",
        "patterns": ["bmi","body mass index","overweight","obese","underweight","weight"],
        "responses": [
            """**BMI (Body Mass Index) Guide** ⚖️

BMI = Weight (kg) ÷ Height² (m²)

**Categories:**
- Underweight: < 18.5
- Normal: 18.5 – 24.9
- Overweight: 25 – 29.9
- Obese Class I: 30 – 34.9
- Obese Class II: 35 – 39.9
- Obese Class III: ≥ 40

**Limitations of BMI:**
- Doesn't account for muscle mass
- May underestimate risk in older adults
- Doesn't reflect fat distribution

**To Reach a Healthy BMI:**
- Eat a balanced, calorie-appropriate diet
- Exercise 150+ min/week
- Get adequate sleep
- Consult a dietitian for personalized advice

*Use our Health Tools section to calculate your BMI!*"""
        ]
    },
    {
        "name": "cold_flu",
        "patterns": ["cold","flu","influenza","runny nose","cough","sore throat","sneeze","congestion"],
        "responses": [
            """**Cold vs. Flu** 🤧

**Common Cold:**
- Gradual onset, mainly upper respiratory
- Runny nose, sore throat, mild cough
- Rarely causes fever in adults
- Lasts 7–10 days

**Flu (Influenza):**
- Sudden onset, body-wide symptoms
- High fever, severe muscle aches
- Extreme fatigue, dry cough
- Can cause serious complications

**Treatment (Both):**
- Rest and stay home
- Stay hydrated (water, herbal tea, broth)
- Honey and lemon for sore throat
- Steam inhalation for congestion
- OTC symptom relief as appropriate

**Prevention:**
- Annual flu vaccine
- Frequent handwashing
- Avoid touching face
- Adequate sleep and nutrition

**See a Doctor If:**
- Difficulty breathing
- High persistent fever
- Worsening symptoms after initial improvement"""
        ]
    },
    {
        "name": "emergency",
        "patterns": ["emergency","urgent","911","help","ambulance","critical","severe","dying","heart attack","stroke","choking"],
        "responses": [
            """🚨 **MEDICAL EMERGENCY GUIDANCE**

**Call Emergency Services (911/112/999) Immediately for:**
- Chest pain or pressure
- Difficulty breathing
- Stroke symptoms (FAST: Face drooping, Arm weakness, Speech difficulty, Time to call)
- Severe allergic reaction (anaphylaxis)
- Uncontrolled bleeding
- Loss of consciousness
- Choking
- Severe burns

**While Waiting for Help:**
- Stay calm and stay with the person
- Do NOT give food or water
- If trained, perform CPR if needed
- Keep them warm and comfortable
- Have someone meet the ambulance

⚠️ *This chatbot cannot replace emergency services. Please call 911 immediately for life-threatening situations.*"""
        ]
    },
    {
        "name": "doctor_advice",
        "patterns": ["doctor","physician","specialist","hospital","clinic","see a doctor","consult","medical advice","appointment"],
        "responses": [
            """**When to See a Doctor** 🏥

**See a Doctor Promptly For:**
- Symptoms lasting more than 2 weeks
- Sudden onset of severe symptoms
- Unexplained weight loss or gain
- Persistent fever
- Blood in urine, stool, or vomit
- Chest pain or breathing difficulties
- New or worsening symptoms

**Regular Check-ups:**
- Annual physical exam
- Blood pressure check (yearly)
- Cholesterol test (every 4–5 years)
- Blood glucose screening
- Cancer screenings as age-appropriate

**Remember:**
- Bring a list of symptoms and medications
- Don't downplay symptoms to your doctor
- Ask questions you don't understand

*This chatbot provides general health information only and is NOT a substitute for professional medical diagnosis or treatment.*"""
        ]
    },
    {
        "name": "water_hydration",
        "patterns": ["water","hydration","hydrated","dehydration","drink water","thirsty"],
        "responses": [
            """**Hydration Guide** 💧

**Daily Water Intake:**
- Men: ~3.7 liters (125 oz) total fluids
- Women: ~2.7 liters (91 oz) total fluids
- More needed during exercise, heat, illness

**Signs of Dehydration:**
- Dark yellow urine
- Dizziness, fatigue
- Dry mouth and lips
- Reduced urination
- Headache, difficulty concentrating

**Hydration Tips:**
- Start your day with a glass of water
- Carry a reusable water bottle
- Eat water-rich foods (cucumber, watermelon)
- Drink before you feel thirsty
- Limit caffeine and alcohol

*Use our Water Calculator in Health Tools for your personalized recommendation!*"""
        ]
    },
    {
        "name": "disclaimer",
        "patterns": ["disclaimer","safe","reliable","accurate","trust","replace doctor","medical advice"],
        "responses": [
            """**Important Disclaimer** ⚠️

I am an offline AI health assistant designed to provide **general health information and education**.

**I am NOT:**
- A licensed medical professional
- A substitute for professional medical advice
- Able to diagnose or treat medical conditions

**Always:**
- Consult a qualified doctor for medical diagnosis
- Seek emergency services for urgent/life-threatening conditions
- Follow your healthcare provider's prescribed treatment

The information I provide is based on general medical knowledge and should not replace personalized advice from your doctor."""
        ]
    },
]

import random

def get_bot_response(user_input: str) -> str:
    text = user_input.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = set(text.split())

    best_intent = None
    best_score  = 0

    for intent in INTENTS:
        score = sum(1 for p in intent["patterns"] if p in text or p in words)
        if score > best_score:
            best_score = score
            best_intent = intent

    if best_intent and best_score > 0:
        return random.choice(best_intent["responses"])

    # Fallback response
    return """I'm not sure I understand your question. Could you rephrase it?

I can help with topics like:
- 🩸 Diabetes, ❤️ Heart Disease, 💉 Hypertension
- 😴 Sleep, 🥗 Diet & Nutrition, 🏃 Exercise
- 🌡️ Fever, 🤕 Headache, 🤧 Cold & Flu
- 🧘 Mental Health & Stress
- 💧 Hydration, ⚖️ BMI
- 🚨 Emergency guidance

⚠️ *I provide general health education only — not medical advice.*"""


# ─────────────────────────────────────────────────────────────────────────────
# Chat UI
# ─────────────────────────────────────────────────────────────────────────────

# Load history from DB on first load
if "chat_messages" not in st.session_state:
    history = get_chat_history(uid, limit=60)
    st.session_state["chat_messages"] = history

# Disclaimer
st.markdown("""
<div class="alert-warning" style="margin-bottom:1rem">
    ⚠️ <strong>Disclaimer:</strong> This chatbot provides general health <em>education</em> only.
    It is NOT a substitute for professional medical advice, diagnosis, or treatment.
    Always consult a qualified healthcare professional.
</div>
""", unsafe_allow_html=True)

# Display messages
chat_container = st.container()
with chat_container:
    if not st.session_state["chat_messages"]:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:2rem;">
            <div style="font-size:3rem">💬</div>
            <h3 style="color:#E2E8F0">Start a conversation!</h3>
            <p style="color:#64748B">Ask me about symptoms, diseases, nutrition, exercise, or any health topic.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for msg in st.session_state["chat_messages"]:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">🧑 {msg["message"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bot">🤖 {msg["message"]}</div>', unsafe_allow_html=True)

# Suggested questions
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("**💡 Suggested Questions:**")
suggestions = [
    "What are the symptoms of diabetes?",
    "How can I improve my sleep?",
    "What foods are good for heart health?",
    "How much water should I drink daily?",
    "When should I see a doctor?",
]
cols = st.columns(len(suggestions))
for col, suggestion in zip(cols, suggestions):
    if col.button(suggestion, key=f"suggest_{suggestion[:20]}"):
        response = get_bot_response(suggestion)
        st.session_state["chat_messages"].append({"role": "user", "message": suggestion})
        st.session_state["chat_messages"].append({"role": "bot",  "message": response})
        save_chat_message(uid, "user", suggestion)
        save_chat_message(uid, "bot",  response)
        st.rerun()

# Input
with st.form("chat_form", clear_on_submit=True):
    col_input, col_btn = st.columns([5, 1])
    with col_input:
        user_input = st.text_input("Type your health question...", label_visibility="collapsed",
                                   placeholder="Ask me anything about health...")
    with col_btn:
        send = st.form_submit_button("Send 📤", use_container_width=True)

if send and user_input.strip():
    response = get_bot_response(user_input.strip())
    st.session_state["chat_messages"].append({"role": "user", "message": user_input.strip()})
    st.session_state["chat_messages"].append({"role": "bot",  "message": response})
    save_chat_message(uid, "user", user_input.strip())
    save_chat_message(uid, "bot",  response)
    st.rerun()
