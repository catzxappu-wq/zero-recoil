"""
ZERO RECOIL - Authentication & Authorization
ARMUGA X CATZX
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request
from database import get_db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this feature.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Administrator authentication required.", "danger")
            return redirect(url_for("admin_login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def log_admin_activity(admin_name, action, target_type="", target_id=None, details=""):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO activity_logs (admin_name, action, target_type, target_id, details)
            VALUES (?, ?, ?, ?, ?)
        """, (admin_name, action, target_type, target_id, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging admin activity: {e}")

def get_current_user():
    if "user_id" in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, created_at FROM users WHERE id = ?", (session["user_id"],))
        user = cursor.fetchone()
        conn.close()
        return user
    return None

def get_current_admin():
    if "admin_id" in session:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, role FROM admins WHERE id = ?", (session["admin_id"],))
        admin = cursor.fetchone()
        conn.close()
        return admin
    return None
