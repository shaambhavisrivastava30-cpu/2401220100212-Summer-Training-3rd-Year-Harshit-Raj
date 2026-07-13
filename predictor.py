"""
Disease prediction engine using trained local ML models.
"""

import os
import numpy as np
import joblib

MODELS_DIR = os.path.join(os.path.dirname(__file__), "trained")


def load_model(name):
    model_path  = os.path.join(MODELS_DIR, f"{name}_model.pkl")
    scaler_path = os.path.join(MODELS_DIR, f"{name}_scaler.pkl")
    if not os.path.exists(model_path) or not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Model '{name}' not found. Train models first.")
    model  = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    return model, scaler


def predict(name, features: list) -> dict:
    """
    Run a prediction and return structured result.
    Returns: {prediction, confidence, risk_level, recommendations}
    """
    model, scaler = load_model(name)
    X = np.array(features).reshape(1, -1)
    X_scaled = scaler.transform(X)

    pred = model.predict(X_scaled)[0]
    proba = model.predict_proba(X_scaled)[0]
    confidence = float(proba[pred])

    risk_level = _risk_level(pred, confidence)
    recommendations = _get_recommendations(name, pred, confidence, features)

    return {
        "prediction":      int(pred),
        "label":           "Positive" if pred == 1 else "Negative",
        "confidence":      round(confidence * 100, 1),
        "risk_level":      risk_level,
        "recommendations": recommendations,
    }


def _risk_level(pred, confidence):
    if pred == 0:
        if confidence >= 0.85:
            return "Low"
        return "Medium"
    else:
        if confidence >= 0.85:
            return "High"
        return "Medium"


def _get_recommendations(name, pred, confidence, features):
    general = [
        "Maintain a balanced diet rich in fruits and vegetables",
        "Exercise regularly — aim for at least 150 minutes of moderate activity per week",
        "Stay hydrated — drink 8-10 glasses of water daily",
        "Get 7-8 hours of quality sleep each night",
        "Manage stress through mindfulness, yoga, or meditation",
        "Avoid smoking and limit alcohol consumption",
        "Schedule regular health check-ups with your doctor",
    ]

    specific = {
        "diabetes": {
            1: [
                "Monitor blood glucose levels regularly",
                "Reduce sugar and refined carbohydrate intake",
                "Work with your doctor on a diabetes management plan",
                "Consider consulting a dietitian for a diabetic-friendly meal plan",
                "Check your feet daily for cuts or sores",
                "Take medications as prescribed",
            ],
            0: [
                "Continue maintaining healthy blood sugar levels",
                "Limit sugary beverages and processed foods",
                "Include fiber-rich foods to stabilize blood sugar",
            ]
        },
        "heart_disease": {
            1: [
                "Consult a cardiologist immediately for a thorough evaluation",
                "Monitor blood pressure and cholesterol regularly",
                "Follow a heart-healthy diet (DASH or Mediterranean diet)",
                "Avoid high-sodium foods",
                "Do not start intense exercise without medical clearance",
                "Take prescribed heart medications consistently",
            ],
            0: [
                "Maintain healthy cholesterol and blood pressure levels",
                "Eat a heart-healthy diet low in saturated fats",
                "Stay physically active with regular cardio exercise",
            ]
        },
        "kidney_disease": {
            1: [
                "Consult a nephrologist as soon as possible",
                "Monitor blood pressure and blood sugar levels closely",
                "Limit protein, potassium, phosphorus, and sodium intake",
                "Stay adequately hydrated but don't over-drink",
                "Avoid NSAIDs and other nephrotoxic medications",
                "Get regular kidney function tests (creatinine, eGFR)",
            ],
            0: [
                "Stay well-hydrated to support kidney health",
                "Limit excessive salt and protein intake",
                "Avoid prolonged use of OTC pain medications",
            ]
        },
        "liver_disease": {
            1: [
                "Consult a hepatologist or gastroenterologist",
                "Completely avoid alcohol",
                "Follow a liver-friendly diet — low in fat and processed foods",
                "Get vaccinated for Hepatitis A and B if not already done",
                "Monitor liver enzymes regularly with blood tests",
                "Avoid medications that can harm the liver without medical advice",
            ],
            0: [
                "Limit alcohol consumption to protect your liver",
                "Maintain a healthy weight to prevent fatty liver disease",
                "Avoid exposure to toxins and harsh chemicals",
            ]
        },
        "breast_cancer": {
            1: [
                "Consult an oncologist or breast specialist immediately",
                "Schedule a mammogram and/or breast ultrasound",
                "Consider genetic counseling if there is family history",
                "Follow your doctor's recommended treatment or monitoring plan",
                "Perform monthly self-breast exams",
                "Maintain a healthy BMI — obesity is a risk factor",
            ],
            0: [
                "Continue performing monthly breast self-exams",
                "Schedule regular mammograms as recommended by your doctor",
                "Maintain a healthy lifestyle to reduce cancer risk",
            ]
        },
    }

    recs = specific.get(name, {}).get(pred, []) + general[:3]
    if pred == 1:
        recs.insert(0, "⚠️ Please consult a qualified healthcare professional as soon as possible. This tool is for informational purposes only.")
    return recs[:8]


# ─── Feature definitions (labels + ranges for UI) ─────────────────────────

DISEASE_FEATURES = {
    "diabetes": {
        "title": "Diabetes Prediction",
        "icon": "🩸",
        "description": "Predicts the likelihood of Type 2 Diabetes based on clinical markers.",
        "features": [
            {"key": "pregnancies",       "label": "Number of Pregnancies",   "min": 0, "max": 20,   "step": 1,   "default": 0,     "type": "int"},
            {"key": "glucose",           "label": "Glucose (mg/dL)",         "min": 60, "max": 250, "step": 1,   "default": 110,   "type": "int"},
            {"key": "blood_pressure",    "label": "Blood Pressure (mmHg)",   "min": 40, "max": 130, "step": 1,   "default": 72,    "type": "int"},
            {"key": "skin_thickness",    "label": "Skin Thickness (mm)",     "min": 5,  "max": 80,  "step": 1,   "default": 23,    "type": "int"},
            {"key": "insulin",           "label": "Insulin (μU/mL)",         "min": 0,  "max": 500, "step": 1,   "default": 80,    "type": "int"},
            {"key": "bmi",               "label": "BMI",                     "min": 10, "max": 70,  "step": 0.1, "default": 25.0,  "type": "float"},
            {"key": "diabetes_pedigree", "label": "Diabetes Pedigree Function","min":0.05,"max":2.5,"step": 0.01,"default": 0.35,  "type": "float"},
            {"key": "age",               "label": "Age",                     "min": 18, "max": 90,  "step": 1,   "default": 30,    "type": "int"},
        ]
    },
    "heart_disease": {
        "title": "Heart Disease Prediction",
        "icon": "❤️",
        "description": "Predicts the likelihood of cardiovascular heart disease.",
        "features": [
            {"key": "age",         "label": "Age",                       "min": 18, "max": 90,  "step": 1,   "default": 45,    "type": "int"},
            {"key": "sex",         "label": "Sex (1=Male, 0=Female)",    "min": 0,  "max": 1,   "step": 1,   "default": 1,     "type": "int"},
            {"key": "cp",          "label": "Chest Pain Type (0-3)",     "min": 0,  "max": 3,   "step": 1,   "default": 0,     "type": "int"},
            {"key": "trestbps",    "label": "Resting Blood Pressure",    "min": 80, "max": 200, "step": 1,   "default": 120,   "type": "int"},
            {"key": "chol",        "label": "Cholesterol (mg/dL)",       "min": 100,"max": 600, "step": 1,   "default": 200,   "type": "int"},
            {"key": "fbs",         "label": "Fasting Blood Sugar >120 (1=Yes)", "min":0,"max":1,"step":1,"default":0,"type":"int"},
            {"key": "restecg",     "label": "Resting ECG Result (0-2)",  "min": 0,  "max": 2,   "step": 1,   "default": 0,     "type": "int"},
            {"key": "thalach",     "label": "Max Heart Rate Achieved",   "min": 60, "max": 220, "step": 1,   "default": 150,   "type": "int"},
            {"key": "exang",       "label": "Exercise Induced Angina (1=Yes)","min":0,"max":1,"step":1,"default":0,"type":"int"},
            {"key": "oldpeak",     "label": "ST Depression (Oldpeak)",   "min": 0.0,"max": 6.0, "step": 0.1, "default": 0.0,   "type": "float"},
            {"key": "slope",       "label": "Slope of ST Segment (0-2)", "min": 0,  "max": 2,   "step": 1,   "default": 1,     "type": "int"},
            {"key": "ca",          "label": "Major Vessels (0-3)",       "min": 0,  "max": 3,   "step": 1,   "default": 0,     "type": "int"},
            {"key": "thal",        "label": "Thalassemia Type (0-3)",    "min": 0,  "max": 3,   "step": 1,   "default": 1,     "type": "int"},
        ]
    },
    "kidney_disease": {
        "title": "Kidney Disease Prediction",
        "icon": "🫘",
        "description": "Predicts the likelihood of Chronic Kidney Disease.",
        "features": [
            {"key": "age",         "label": "Age",                          "min": 2,   "max": 90,   "step": 1,    "default": 40,    "type": "int"},
            {"key": "bp",          "label": "Blood Pressure (mmHg)",        "min": 50,  "max": 180,  "step": 1,    "default": 80,    "type": "int"},
            {"key": "sg",          "label": "Specific Gravity (1.005-1.025)","min":1.005,"max":1.025,"step":0.005,"default":1.015,   "type": "float"},
            {"key": "al",          "label": "Albumin Level (0-4)",          "min": 0,   "max": 4,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "su",          "label": "Sugar Level (0-4)",            "min": 0,   "max": 4,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "rbc",         "label": "Red Blood Cells (1=Abnormal)", "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "pc",          "label": "Pus Cell (1=Abnormal)",        "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "pcc",         "label": "Pus Cell Clumps (1=Present)",  "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "ba",          "label": "Bacteria (1=Present)",         "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "bgr",         "label": "Blood Glucose Random (mg/dL)", "min": 70,  "max": 300,  "step": 1,    "default": 100,   "type": "int"},
            {"key": "bu",          "label": "Blood Urea (mg/dL)",           "min": 10,  "max": 200,  "step": 1,    "default": 30,    "type": "int"},
            {"key": "sc",          "label": "Serum Creatinine (mg/dL)",     "min": 0.4, "max": 15.0, "step": 0.1,  "default": 1.0,   "type": "float"},
            {"key": "sod",         "label": "Sodium (mEq/L)",               "min": 110, "max": 160,  "step": 1,    "default": 140,   "type": "int"},
            {"key": "pot",         "label": "Potassium (mEq/L)",            "min": 2.5, "max": 7.0,  "step": 0.1,  "default": 4.0,   "type": "float"},
            {"key": "hemo",        "label": "Hemoglobin (g/dL)",            "min": 3.0, "max": 18.0, "step": 0.1,  "default": 13.5,  "type": "float"},
            {"key": "pcv",         "label": "Packed Cell Volume (%)",       "min": 15,  "max": 55,   "step": 1,    "default": 42,    "type": "int"},
            {"key": "wc",          "label": "WBC Count (cells/cumm)",       "min": 3000,"max":20000, "step": 100,  "default": 7500,  "type": "int"},
            {"key": "rc",          "label": "RBC Count (millions/cmm)",     "min": 2.0, "max": 7.0,  "step": 0.1,  "default": 5.0,   "type": "float"},
            {"key": "htn",         "label": "Hypertension (1=Yes)",         "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "dm",          "label": "Diabetes Mellitus (1=Yes)",    "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "cad",         "label": "Coronary Artery Disease (1=Yes)","min":0,  "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "appet",       "label": "Appetite (1=Good, 0=Poor)",    "min": 0,   "max": 1,    "step": 1,    "default": 1,     "type": "int"},
            {"key": "pe",          "label": "Pedal Edema (1=Yes)",          "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
            {"key": "ane",         "label": "Anemia (1=Yes)",               "min": 0,   "max": 1,    "step": 1,    "default": 0,     "type": "int"},
        ]
    },
    "liver_disease": {
        "title": "Liver Disease Prediction",
        "icon": "🫀",
        "description": "Predicts the likelihood of liver disease based on blood markers.",
        "features": [
            {"key": "age",             "label": "Age",                         "min": 4,   "max": 90,   "step": 1,   "default": 40,   "type": "int"},
            {"key": "gender",          "label": "Gender (1=Male, 0=Female)",   "min": 0,   "max": 1,    "step": 1,   "default": 1,    "type": "int"},
            {"key": "total_bilirubin", "label": "Total Bilirubin (mg/dL)",     "min": 0.1, "max": 15.0, "step": 0.1, "default": 0.9,  "type": "float"},
            {"key": "direct_bilirubin","label": "Direct Bilirubin (mg/dL)",    "min": 0.1, "max": 10.0, "step": 0.1, "default": 0.2,  "type": "float"},
            {"key": "alkaline_phos",   "label": "Alkaline Phosphotase (IU/L)", "min": 60,  "max": 800,  "step": 1,   "default": 220,  "type": "int"},
            {"key": "alamine_amino",   "label": "Alamine Aminotransferase",    "min": 7,   "max": 500,  "step": 1,   "default": 35,   "type": "int"},
            {"key": "aspartate_amino", "label": "Aspartate Aminotransferase",  "min": 10,  "max": 500,  "step": 1,   "default": 30,   "type": "int"},
            {"key": "total_proteins",  "label": "Total Proteins (g/dL)",       "min": 2.7, "max": 9.6,  "step": 0.1, "default": 6.8,  "type": "float"},
            {"key": "albumin",         "label": "Albumin (g/dL)",              "min": 0.9, "max": 5.5,  "step": 0.1, "default": 3.6,  "type": "float"},
            {"key": "ag_ratio",        "label": "Albumin/Globulin Ratio",      "min": 0.3, "max": 2.8,  "step": 0.1, "default": 1.1,  "type": "float"},
        ]
    },
    "breast_cancer": {
        "title": "Breast Cancer Prediction",
        "icon": "🎗️",
        "description": "Predicts malignancy likelihood based on tumor cell characteristics.",
        "features": [
            {"key": "radius_mean",    "label": "Mean Radius",           "min": 5.0, "max": 30.0, "step": 0.1, "default": 14.0, "type": "float"},
            {"key": "texture_mean",   "label": "Mean Texture",          "min": 8.0, "max": 40.0, "step": 0.1, "default": 18.0, "type": "float"},
            {"key": "perimeter_mean", "label": "Mean Perimeter",        "min": 40.0,"max": 200.0,"step": 0.5, "default": 90.0, "type": "float"},
            {"key": "area_mean",      "label": "Mean Area",             "min": 150, "max": 2500, "step": 1,   "default": 600,  "type": "float"},
            {"key": "smoothness",     "label": "Mean Smoothness",       "min": 0.05,"max": 0.17, "step":0.001,"default": 0.095,"type": "float"},
            {"key": "compactness",    "label": "Mean Compactness",      "min": 0.01,"max": 0.40, "step":0.001,"default": 0.09, "type": "float"},
            {"key": "concavity",      "label": "Mean Concavity",        "min": 0.0, "max": 0.45, "step":0.001,"default": 0.05, "type": "float"},
            {"key": "concave_points", "label": "Mean Concave Points",   "min": 0.0, "max": 0.22, "step":0.001,"default": 0.03, "type": "float"},
            {"key": "symmetry",       "label": "Mean Symmetry",         "min": 0.10,"max": 0.35, "step":0.001,"default": 0.18, "type": "float"},
            {"key": "fractal_dim",    "label": "Fractal Dimension",     "min": 0.05,"max": 0.10, "step":0.001,"default": 0.063,"type": "float"},
        ]
    }
}
