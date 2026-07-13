"""
Authentication utilities using bcrypt for password hashing.
"""

import bcrypt
import streamlit as st
from database.db_manager import create_user, get_user_by_username


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password meets minimum requirements."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    return True, "Password is strong"


def register_user(username: str, password: str, full_name: str = None, email: str = None) -> tuple[bool, str]:
    """Register a new user."""
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters"
    if not username.isalnum() and "_" not in username:
        return False, "Username can only contain letters, numbers, and underscores"
    valid, msg = validate_password_strength(password)
    if not valid:
        return False, msg
    password_hash = hash_password(password)
    return create_user(username, password_hash, full_name, email)


def login_user(username: str, password: str) -> tuple[bool, str, dict | None]:
    """Authenticate a user."""
    if not username or not password:
        return False, "Please provide both username and password", None
    user = get_user_by_username(username)
    if not user:
        return False, "Invalid username or password", None
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid username or password", None
    return True, "Login successful", user


def is_authenticated() -> bool:
    """Check if a user is currently logged in."""
    return st.session_state.get("authenticated", False)


def get_current_user() -> dict | None:
    """Get the currently logged-in user."""
    return st.session_state.get("user", None)


def logout():
    """Log out the current user."""
    for key in ["authenticated", "user", "chat_messages"]:
        if key in st.session_state:
            del st.session_state[key]


def require_auth():
    """Redirect to login if not authenticated. Call at top of each page."""
    if not is_authenticated():
        st.warning("⚠️ Please log in to access this page.")
        st.markdown("[← Go to Login](/) ")
        st.stop()
    return get_current_user()
