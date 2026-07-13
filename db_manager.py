"""
SQLite Database Manager for Smart Healthcare AI Platform
Handles all database operations with parameterized queries (SQL injection safe)
"""

import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "healthcare.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initialize all database tables."""
    conn = get_connection()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            age INTEGER,
            gender TEXT,
            blood_group TEXT,
            phone TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Predictions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            disease_type TEXT NOT NULL,
            input_data TEXT NOT NULL,
            prediction TEXT NOT NULL,
            confidence REAL,
            risk_level TEXT,
            recommendations TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Medical reports table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT,
            extracted_text TEXT,
            summary TEXT,
            file_path TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Medicines table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            medicine_name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            time_slots TEXT,
            start_date TEXT,
            end_date TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Medicine logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medicine_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            medicine_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            taken_at TEXT NOT NULL,
            status TEXT DEFAULT 'taken',
            FOREIGN KEY (medicine_id) REFERENCES medicines(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Appointments table
    c.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doctor_name TEXT NOT NULL,
            speciality TEXT,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            location TEXT,
            notes TEXT,
            status TEXT DEFAULT 'scheduled',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Chat history table
    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Emergency contacts table
    c.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            relationship TEXT,
            phone TEXT NOT NULL,
            email TEXT,
            is_primary INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Health vitals table
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vital_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT,
            notes TEXT,
            recorded_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ─── User Operations ────────────────────────────────────────────────────────

def create_user(username, password_hash, full_name=None, email=None):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, full_name, email) VALUES (?, ?, ?, ?)",
            (username, password_hash, full_name, email)
        )
        conn.commit()
        return True, "User created successfully"
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()


def get_user_by_username(username):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_profile(user_id, **kwargs):
    allowed = {"full_name", "email", "age", "gender", "blood_group", "phone"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [user_id]
    conn = get_connection()
    conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return True


# ─── Prediction Operations ──────────────────────────────────────────────────

def save_prediction(user_id, disease_type, input_data, prediction, confidence, risk_level, recommendations):
    conn = get_connection()
    conn.execute(
        """INSERT INTO predictions 
           (user_id, disease_type, input_data, prediction, confidence, risk_level, recommendations)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, disease_type, json.dumps(input_data), prediction, confidence, risk_level,
         json.dumps(recommendations))
    )
    conn.commit()
    conn.close()


def get_predictions(user_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["input_data"] = json.loads(d["input_data"])
        d["recommendations"] = json.loads(d["recommendations"])
        result.append(d)
    return result


def get_prediction_stats(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT disease_type, prediction, risk_level, created_at FROM predictions WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Medical Report Operations ───────────────────────────────────────────────

def save_medical_report(user_id, filename, file_type, extracted_text, summary, file_path):
    conn = get_connection()
    conn.execute(
        """INSERT INTO medical_reports (user_id, filename, file_type, extracted_text, summary, file_path)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, filename, file_type, extracted_text, summary, file_path)
    )
    conn.commit()
    conn.close()


def get_medical_reports(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM medical_reports WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_medical_report(report_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM medical_reports WHERE id = ? AND user_id = ?", (report_id, user_id))
    conn.commit()
    conn.close()


# ─── Medicine Operations ──────────────────────────────────────────────────────

def add_medicine(user_id, medicine_name, dosage, frequency, time_slots, start_date, end_date, notes):
    conn = get_connection()
    conn.execute(
        """INSERT INTO medicines (user_id, medicine_name, dosage, frequency, time_slots, start_date, end_date, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, medicine_name, dosage, frequency, json.dumps(time_slots), start_date, end_date, notes)
    )
    conn.commit()
    conn.close()


def get_medicines(user_id, active_only=True):
    conn = get_connection()
    query = "SELECT * FROM medicines WHERE user_id = ?"
    params = [user_id]
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["time_slots"] = json.loads(d["time_slots"]) if d["time_slots"] else []
        result.append(d)
    return result


def deactivate_medicine(medicine_id, user_id):
    conn = get_connection()
    conn.execute(
        "UPDATE medicines SET is_active = 0 WHERE id = ? AND user_id = ?",
        (medicine_id, user_id)
    )
    conn.commit()
    conn.close()


def log_medicine_taken(medicine_id, user_id):
    conn = get_connection()
    conn.execute(
        "INSERT INTO medicine_logs (medicine_id, user_id, taken_at) VALUES (?, ?, ?)",
        (medicine_id, user_id, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_medicine_logs(user_id, days=30):
    conn = get_connection()
    rows = conn.execute(
        """SELECT ml.*, m.medicine_name FROM medicine_logs ml
           JOIN medicines m ON ml.medicine_id = m.id
           WHERE ml.user_id = ?
           AND ml.taken_at >= datetime('now', ?)
           ORDER BY ml.taken_at DESC""",
        (user_id, f"-{days} days")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Appointment Operations ───────────────────────────────────────────────────

def book_appointment(user_id, doctor_name, speciality, date, time, location, notes):
    conn = get_connection()
    conn.execute(
        """INSERT INTO appointments (user_id, doctor_name, speciality, appointment_date, appointment_time, location, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, doctor_name, speciality, date, time, location, notes)
    )
    conn.commit()
    conn.close()


def get_appointments(user_id, upcoming_only=False):
    conn = get_connection()
    if upcoming_only:
        rows = conn.execute(
            """SELECT * FROM appointments WHERE user_id = ? 
               AND appointment_date >= date('now') AND status = 'scheduled'
               ORDER BY appointment_date, appointment_time""",
            (user_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM appointments WHERE user_id = ? ORDER BY appointment_date DESC, appointment_time DESC",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_appointment_status(appt_id, user_id, status):
    conn = get_connection()
    conn.execute(
        "UPDATE appointments SET status = ? WHERE id = ? AND user_id = ?",
        (status, appt_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_appointment(appt_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM appointments WHERE id = ? AND user_id = ?", (appt_id, user_id))
    conn.commit()
    conn.close()


# ─── Chat History Operations ──────────────────────────────────────────────────

def save_chat_message(user_id, role, message):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (user_id, role, message) VALUES (?, ?, ?)",
        (user_id, role, message)
    )
    conn.commit()
    conn.close()


def get_chat_history(user_id, limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, message, created_at FROM chat_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in reversed(rows)]


def clear_chat_history(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ─── Emergency Contacts Operations ───────────────────────────────────────────

def add_emergency_contact(user_id, name, relationship, phone, email, is_primary=False):
    conn = get_connection()
    conn.execute(
        """INSERT INTO emergency_contacts (user_id, name, relationship, phone, email, is_primary)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, name, relationship, phone, email, 1 if is_primary else 0)
    )
    conn.commit()
    conn.close()


def get_emergency_contacts(user_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM emergency_contacts WHERE user_id = ? ORDER BY is_primary DESC, name",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_emergency_contact(contact_id, user_id):
    conn = get_connection()
    conn.execute("DELETE FROM emergency_contacts WHERE id = ? AND user_id = ?", (contact_id, user_id))
    conn.commit()
    conn.close()


# ─── Health Vitals Operations ──────────────────────────────────────────────────

def save_vital(user_id, vital_type, value, unit, notes=None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO health_vitals (user_id, vital_type, value, unit, notes) VALUES (?, ?, ?, ?, ?)",
        (user_id, vital_type, value, unit, notes)
    )
    conn.commit()
    conn.close()


def get_vitals(user_id, vital_type=None, days=30):
    conn = get_connection()
    if vital_type:
        rows = conn.execute(
            """SELECT * FROM health_vitals WHERE user_id = ? AND vital_type = ?
               AND recorded_at >= datetime('now', ?) ORDER BY recorded_at DESC""",
            (user_id, vital_type, f"-{days} days")
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM health_vitals WHERE user_id = ?
               AND recorded_at >= datetime('now', ?) ORDER BY recorded_at DESC""",
            (user_id, f"-{days} days")
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize DB on import
init_database()
