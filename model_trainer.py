"""
Local ML Model Trainer for Healthcare Disease Prediction.
Trains models offline using synthetic/generated datasets. No internet required.
Models: Diabetes, Heart Disease, Kidney Disease, Liver Disease, Breast Cancer
"""

import os
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

MODELS_DIR = os.path.join(os.path.dirname(__file__), "trained")
os.makedirs(MODELS_DIR, exist_ok=True)


# ─── Synthetic Dataset Generators ──────────────────────────────────────────

def generate_diabetes_data(n=1500, seed=42):
    np.random.seed(seed)
    n_pos = n // 2
    n_neg = n - n_pos

    # Positive cases
    preg_p = np.random.randint(0, 10, n_pos)
    gluc_p = np.random.normal(145, 25, n_pos).clip(90, 250)
    bp_p   = np.random.normal(78, 12, n_pos).clip(50, 120)
    skin_p = np.random.normal(30, 10, n_pos).clip(10, 60)
    ins_p  = np.random.normal(160, 80, n_pos).clip(0, 500)
    bmi_p  = np.random.normal(34, 6, n_pos).clip(18, 55)
    dpf_p  = np.random.normal(0.65, 0.3, n_pos).clip(0.05, 2.5)
    age_p  = np.random.normal(48, 12, n_pos).clip(21, 81)

    # Negative cases
    preg_n = np.random.randint(0, 7, n_neg)
    gluc_n = np.random.normal(108, 20, n_neg).clip(60, 165)
    bp_n   = np.random.normal(68, 10, n_neg).clip(40, 100)
    skin_n = np.random.normal(22, 8, n_neg).clip(5, 50)
    ins_n  = np.random.normal(80, 50, n_neg).clip(0, 300)
    bmi_n  = np.random.normal(28, 5, n_neg).clip(18, 48)
    dpf_n  = np.random.normal(0.35, 0.2, n_neg).clip(0.05, 1.5)
    age_n  = np.random.normal(33, 10, n_neg).clip(21, 70)

    X = np.vstack([
        np.column_stack([preg_p, gluc_p, bp_p, skin_p, ins_p, bmi_p, dpf_p, age_p]),
        np.column_stack([preg_n, gluc_n, bp_n, skin_n, ins_n, bmi_n, dpf_n, age_n])
    ])
    y = np.array([1]*n_pos + [0]*n_neg)
    idx = np.random.permutation(len(y))
    return X[idx], y[idx]


def generate_heart_disease_data(n=1500, seed=42):
    np.random.seed(seed)
    n_pos = n // 2
    n_neg = n - n_pos

    def make_row(pos):
        age  = np.random.normal(57 if pos else 47, 9)
        sex  = np.random.binomial(1, 0.7 if pos else 0.5)
        cp   = np.random.randint(0, 4)
        tbp  = np.random.normal(140 if pos else 130, 20)
        chol = np.random.normal(250 if pos else 225, 45)
        fbs  = np.random.binomial(1, 0.35 if pos else 0.15)
        rec  = np.random.randint(0, 3)
        mhr  = np.random.normal(140 if pos else 160, 25)
        ea   = np.random.binomial(1, 0.6 if pos else 0.2)
        old  = float(np.clip(np.random.normal(1.5 if pos else 0.5, 1.0), 0, 5))
        slope= np.random.randint(0, 3)
        ca   = np.random.randint(0, 4)
        thal = np.random.randint(0, 4)
        return [age, sex, cp, tbp, chol, fbs, rec, mhr, ea, old, slope, ca, thal]

    pos_rows = [make_row(True)  for _ in range(n_pos)]
    neg_rows = [make_row(False) for _ in range(n_neg)]
    X = np.array(pos_rows + neg_rows)
    y = np.array([1]*n_pos + [0]*n_neg)
    idx = np.random.permutation(len(y))
    return X[idx], y[idx]


def generate_kidney_disease_data(n=1500, seed=42):
    np.random.seed(seed)
    n_pos = n // 2
    n_neg = n - n_pos

    def make(pos):
        def nc(mu, sd, lo, hi): return float(np.clip(np.random.normal(mu, sd), lo, hi))
        age   = nc(55 if pos else 42, 15, 2, 90)
        bp    = nc(90 if pos else 75, 15, 50, 180)
        sg    = np.random.choice([1.005,1.010,1.015,1.020,1.025], p=[0.4,0.3,0.15,0.1,0.05] if pos else [0.05,0.1,0.2,0.35,0.3])
        al    = np.random.randint(0, 5) if pos else 0
        su    = np.random.randint(0, 5) if pos else 0
        rbc   = 1 if pos and np.random.random()<0.7 else 0
        pc    = 1 if pos and np.random.random()<0.65 else 0
        pcc   = 1 if pos and np.random.random()<0.5 else 0
        ba    = 1 if pos and np.random.random()<0.4 else 0
        bgr   = nc(140 if pos else 110, 30, 70, 300)
        bu    = nc(70 if pos else 30, 25, 10, 200)
        sc    = nc(4.5 if pos else 1.0, 2, 0.4, 15)
        sod   = nc(135 if pos else 140, 10, 110, 160)
        pot   = nc(4.5 if pos else 4.0, 1.0, 2.5, 7)
        hemo  = nc(9 if pos else 14, 2.5, 3, 18)
        pcv   = nc(30 if pos else 44, 7, 15, 55)
        wbc   = nc(10000 if pos else 7500, 3000, 3000, 20000)
        rbc2  = nc(4 if pos else 5, 0.8, 2, 7)
        htn   = 1 if pos and np.random.random()<0.7 else int(np.random.random()<0.2)
        dm    = 1 if pos and np.random.random()<0.55 else int(np.random.random()<0.15)
        cad   = 1 if pos and np.random.random()<0.3 else int(np.random.random()<0.05)
        appet = 0 if pos and np.random.random()<0.6 else 1
        pe    = 1 if pos and np.random.random()<0.5 else int(np.random.random()<0.1)
        ane   = 1 if pos and np.random.random()<0.55 else int(np.random.random()<0.08)
        return [age,bp,sg,al,su,rbc,pc,pcc,ba,bgr,bu,sc,sod,pot,hemo,pcv,wbc,rbc2,htn,dm,cad,appet,pe,ane]

    rows = [make(True) for _ in range(n_pos)] + [make(False) for _ in range(n_neg)]
    X = np.array(rows, dtype=float)
    y = np.array([1]*n_pos + [0]*n_neg)
    idx = np.random.permutation(len(y))
    return X[idx], y[idx]


def generate_liver_disease_data(n=1500, seed=42):
    np.random.seed(seed)
    n_pos = n // 2
    n_neg = n - n_pos

    def make(pos):
        def nc(mu, sd, lo, hi): return float(np.clip(np.random.normal(mu, sd), lo, hi))
        age   = nc(47 if pos else 40, 12, 4, 90)
        gender= int(np.random.random() < (0.75 if pos else 0.6))
        tb    = nc(3.0 if pos else 0.9, 1.5, 0.3, 15)
        db    = nc(1.8 if pos else 0.25, 1.0, 0.1, 10)
        alkphos= nc(340 if pos else 220, 100, 60, 800)
        sgpt  = nc(80 if pos else 35, 50, 7, 500)
        sgot  = nc(90 if pos else 30, 55, 10, 500)
        tp    = nc(6.5 if pos else 6.8, 0.8, 2.7, 9.6)
        alb   = nc(2.8 if pos else 3.6, 0.6, 0.9, 5.5)
        ratio = nc(0.9 if pos else 1.1, 0.3, 0.3, 2.8)
        return [age, gender, tb, db, alkphos, sgpt, sgot, tp, alb, ratio]

    rows = [make(True) for _ in range(n_pos)] + [make(False) for _ in range(n_neg)]
    X = np.array(rows, dtype=float)
    y = np.array([1]*n_pos + [0]*n_neg)
    idx = np.random.permutation(len(y))
    return X[idx], y[idx]


def generate_breast_cancer_data(n=1500, seed=42):
    np.random.seed(seed)
    n_mal = n // 2
    n_ben = n - n_mal

    def make(malignant):
        def nc(mu, sd, lo, hi): return float(np.clip(np.random.normal(mu, sd), lo, hi))
        if malignant:
            radius    = nc(17, 3, 10, 28)
            texture   = nc(22, 4, 11, 35)
            perimeter = nc(115, 18, 70, 185)
            area      = nc(900, 200, 400, 2000)
            smooth    = nc(0.105, 0.015, 0.07, 0.16)
            compact   = nc(0.16, 0.05, 0.05, 0.35)
            concave   = nc(0.17, 0.07, 0.0, 0.4)
            concav_p  = nc(0.09, 0.03, 0.01, 0.2)
            sym       = nc(0.21, 0.03, 0.13, 0.3)
            frac_dim  = nc(0.062, 0.007, 0.05, 0.09)
        else:
            radius    = nc(12, 2, 6, 19)
            texture   = nc(17, 3, 9, 28)
            perimeter = nc(78, 10, 45, 120)
            area      = nc(460, 80, 200, 800)
            smooth    = nc(0.092, 0.012, 0.05, 0.13)
            compact   = nc(0.08, 0.03, 0.02, 0.18)
            concave   = nc(0.04, 0.04, 0.0, 0.2)
            concav_p  = nc(0.025, 0.015, 0.0, 0.1)
            sym       = nc(0.18, 0.03, 0.1, 0.26)
            frac_dim  = nc(0.063, 0.007, 0.05, 0.09)
        return [radius, texture, perimeter, area, smooth, compact, concave, concav_p, sym, frac_dim]

    rows = [make(True) for _ in range(n_mal)] + [make(False) for _ in range(n_ben)]
    X = np.array(rows, dtype=float)
    y = np.array([1]*n_mal + [0]*n_ben)
    idx = np.random.permutation(len(y))
    return X[idx], y[idx]


# ─── Model Training ─────────────────────────────────────────────────────────

def train_and_save(name, X, y, model_cls=None):
    """Train a model, scale features, save to disk."""
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s  = scaler.transform(X_test)

    clf = model_cls or RandomForestClassifier(n_estimators=200, max_depth=8, random_state=42, class_weight="balanced")
    clf.fit(X_train_s, y_train)

    acc = accuracy_score(y_test, clf.predict(X_test_s))
    print(f"  {name}: accuracy={acc:.4f}")

    joblib.dump(clf,    os.path.join(MODELS_DIR, f"{name}_model.pkl"))
    joblib.dump(scaler, os.path.join(MODELS_DIR, f"{name}_scaler.pkl"))
    return acc


def train_all_models(progress_callback=None):
    """Train all 5 disease prediction models."""
    results = {}

    tasks = [
        ("diabetes",       generate_diabetes_data),
        ("heart_disease",  generate_heart_disease_data),
        ("kidney_disease", generate_kidney_disease_data),
        ("liver_disease",  generate_liver_disease_data),
        ("breast_cancer",  generate_breast_cancer_data),
    ]

    for i, (name, gen_fn) in enumerate(tasks):
        if progress_callback:
            progress_callback(i / len(tasks), f"Training {name.replace('_', ' ').title()} model...")
        X, y = gen_fn()
        acc = train_and_save(name, X, y)
        results[name] = acc

    if progress_callback:
        progress_callback(1.0, "All models trained!")
    return results


def models_exist():
    """Check if all trained models are already on disk."""
    names = ["diabetes", "heart_disease", "kidney_disease", "liver_disease", "breast_cancer"]
    return all(
        os.path.exists(os.path.join(MODELS_DIR, f"{n}_model.pkl")) and
        os.path.exists(os.path.join(MODELS_DIR, f"{n}_scaler.pkl"))
        for n in names
    )
