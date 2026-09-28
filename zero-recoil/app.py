"""
ZERO RECOIL - Free Fire Sensitivity Platform
ARMUGA X CATZX
Production Full-Stack Application
"""
import os
import csv
import io
import re
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, make_response, Response
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db, init_db, seed_db
from auth import (
    login_required, admin_required,
    get_current_user, get_current_admin,
    log_admin_activity
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "zero-recoil-armuga-catzx-super-secret-key-2026")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text.lower().strip())
    return re.sub(r'[-\s]+', '-', text)

# Global Template Context Injector
@app.context_processor
def inject_globals():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT is_live, stream_url, title FROM live_stream WHERE id = 1")
    live_row = cursor.fetchone()
    conn.close()

    return {
        "current_user": get_current_user(),
        "current_admin": get_current_admin(),
        "live_info": live_row
    }

# ==============================================================================
# PUBLIC ROUTES
# ==============================================================================

@app.route("/")
def index():
    conn = get_db()
    cursor = conn.cursor()

    # Metric counts
    cursor.execute("SELECT COUNT(*) FROM guns WHERE status = 'active'")
    guns_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM brands WHERE status = 'active'")
    brands_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
    devices_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sensitivities WHERE status = 'active'")
    sens_count = cursor.fetchone()[0]

    # Popular Guns (MP40, M1887, UMP, SCAR, AWM, AK47)
    cursor.execute("""
        SELECT g.*, c.name as category_name
        FROM guns g
        JOIN categories c ON g.category_id = c.id
        WHERE g.status = 'active'
        ORDER BY g.sort_order ASC
        LIMIT 6
    """)
    popular_guns = cursor.fetchall()

    # Featured Devices
    cursor.execute("""
        SELECT d.*, b.name as brand_name,
               (SELECT GROUP_CONCAT(ram, ', ') FROM ram_options WHERE device_id = d.id) as ram_list
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
        WHERE d.status = 'active'
        LIMIT 6
    """)
    featured_devices = cursor.fetchall()

    # Latest Updates
    cursor.execute("""
        SELECT * FROM updates
        WHERE published = 1
        ORDER BY created_at DESC
        LIMIT 3
    """)
    latest_updates = cursor.fetchall()

    conn.close()

    stats = {
        "guns": guns_count,
        "brands": brands_count,
        "devices": devices_count,
        "sensitivities": sens_count
    }

    return render_template(
        "index.html",
        stats=stats,
        popular_guns=popular_guns,
        featured_devices=featured_devices,
        latest_updates=latest_updates
    )

@app.route("/guns")
def guns_list():
    category_slug = request.args.get("category", "").strip()
    conn = get_db()
    cursor = conn.cursor()

    # Categories with count
    cursor.execute("""
        SELECT c.*, (SELECT COUNT(*) FROM guns WHERE category_id = c.id AND status = 'active') as gun_count
        FROM categories c
        ORDER BY c.sort_order ASC
    """)
    categories = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM guns WHERE status = 'active'")
    total_guns = cursor.fetchone()[0]

    query = """
        SELECT g.*, c.name as category_name, c.slug as category_slug,
               (SELECT COUNT(*) FROM sensitivities WHERE gun_id = g.id AND status = 'active') as sensitivity_count
        FROM guns g
        JOIN categories c ON g.category_id = c.id
        WHERE g.status = 'active'
    """
    params = []
    if category_slug:
        query += " AND c.slug = ?"
        params.append(category_slug)

    query += " ORDER BY g.sort_order ASC, g.name ASC"
    cursor.execute(query, params)
    guns = cursor.fetchall()
    conn.close()

    return render_template(
        "guns.html",
        guns=guns,
        categories=categories,
        total_guns=total_guns,
        active_category=category_slug
    )

@app.route("/guns/<gun_slug>")
def gun_detail(gun_slug):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.*, c.name as category_name
        FROM guns g
        JOIN categories c ON g.category_id = c.id
        WHERE g.slug = ? OR g.id = ?
    """, (gun_slug, gun_slug))
    gun = cursor.fetchone()

    if not gun:
        conn.close()
        flash("Weapon not found in database.", "danger")
        return redirect(url_for("guns_list"))

    # Available device sensitivities for this gun
    cursor.execute("""
        SELECT s.*, d.model_name, b.name as brand_name
        FROM sensitivities s
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        WHERE s.gun_id = ? AND s.status = 'active'
        ORDER BY b.name ASC, d.model_name ASC
    """, (gun["id"],))
    device_sens = cursor.fetchall()

    conn.close()
    return render_template("gun_detail.html", gun=gun, device_sens=device_sens)

@app.route("/devices")
def devices_list():
    brand_slug = request.args.get("brand", "").strip()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.*, (SELECT COUNT(*) FROM devices WHERE brand_id = b.id AND status = 'active') as device_count
        FROM brands b
        WHERE b.status = 'active'
        ORDER BY b.sort_order ASC, b.name ASC
    """)
    brands = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM devices WHERE status = 'active'")
    total_devices = cursor.fetchone()[0]

    query = """
        SELECT d.*, b.name as brand_name, b.slug as brand_slug,
               (SELECT GROUP_CONCAT(ram, ', ') FROM ram_options WHERE device_id = d.id) as ram_list,
               (SELECT COUNT(*) FROM sensitivities WHERE device_id = d.id AND status = 'active') as sensitivity_count
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
        WHERE d.status = 'active'
    """
    params = []
    if brand_slug:
        query += " AND b.slug = ?"
        params.append(brand_slug)

    query += " ORDER BY b.name ASC, d.model_name ASC"
    cursor.execute(query, params)
    devices = cursor.fetchall()
    conn.close()

    return render_template(
        "devices.html",
        devices=devices,
        brands=brands,
        total_devices=total_devices,
        active_brand=brand_slug
    )

@app.route("/devices/<int:device_id>")
def device_detail(device_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT d.*, b.name as brand_name, b.slug as brand_slug,
               (SELECT GROUP_CONCAT(ram, ', ') FROM ram_options WHERE device_id = d.id) as ram_list
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
        WHERE d.id = ?
    """, (device_id,))
    device = cursor.fetchone()

    if not device:
        conn.close()
        flash("Device not found.", "danger")
        return redirect(url_for("devices_list"))

    # Sensitivities calibrated for this device
    cursor.execute("""
        SELECT s.*, g.name as gun_name, g.slug as gun_slug, c.name as category_name
        FROM sensitivities s
        JOIN guns g ON s.gun_id = g.id
        JOIN categories c ON g.category_id = c.id
        WHERE s.device_id = ? AND s.status = 'active'
        ORDER BY c.sort_order ASC, g.name ASC
    """, (device_id,))
    guns_sens = cursor.fetchall()

    conn.close()
    return render_template("device_detail.html", device=device, guns_sens=guns_sens)

@app.route("/sensitivity")
def sensitivity_page():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM categories ORDER BY sort_order ASC")
    categories = cursor.fetchall()

    cursor.execute("""
        SELECT g.*, c.name as category_name, c.slug as category_slug
        FROM guns g
        JOIN categories c ON g.category_id = c.id
        WHERE g.status = 'active'
        ORDER BY c.sort_order ASC, g.sort_order ASC
    """)
    all_guns = cursor.fetchall()

    cursor.execute("""
        SELECT b.*, (SELECT COUNT(*) FROM devices WHERE brand_id = b.id AND status = 'active') as device_count
        FROM brands b
        WHERE b.status = 'active'
        ORDER BY b.sort_order ASC
    """)
    all_brands = cursor.fetchall()

    conn.close()
    return render_template("sensitivity.html", categories=categories, all_guns=all_guns, all_brands=all_brands)

@app.route("/updates")
def updates_list():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM updates WHERE published = 1 ORDER BY created_at DESC")
    updates = cursor.fetchall()
    conn.close()
    return render_template("updates.html", updates=updates)

@app.route("/about")
def about_page():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        subject = request.form.get("subject", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all required fields.", "warning")
            return redirect(url_for("contact_page"))

        # In production this emails or stores inquiries
        flash(f"Thank you, {name}! Your message has been sent to ARMUGA and CATZX.", "success")
        return redirect(url_for("contact_page"))

    return render_template("contact.html")

# ==============================================================================
# CUSTOMER AUTHENTICATION & PORTAL
# ==============================================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and check_password_hash(user["password_hash"], password):
            if user["status"] != "active":
                conn.close()
                flash("Your account has been deactivated. Please contact support.", "danger")
                return redirect(url_for("login"))

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            # Update last login
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
            conn.commit()
            conn.close()

            flash(f"Welcome back, {user['name']}!", "success")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("dashboard"))
        else:
            conn.close()
            flash("Invalid email or password. Please try again.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for("register"))

        if password != confirm:
            flash("Passwords do not match.", "warning")
            return redirect(url_for("register"))

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            flash("An account with that email already exists. Please log in.", "warning")
            return redirect(url_for("login"))

        pwd_hash = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        """, (name, email, pwd_hash))
        new_id = cursor.lastrowid

        # Welcome notification
        cursor.execute("""
            INSERT INTO notifications (user_id, title, message)
            VALUES (?, ?, ?)
        """, (new_id, "Welcome to ZERO RECOIL", "Welcome to the official ARMUGA X CATZX Free Fire sensitivity tuning platform! Start bookmarking your favorite gun & device profiles."))

        conn.commit()
        conn.close()

        session["user_id"] = new_id
        session["user_name"] = name
        flash("Registration successful! Welcome to ZERO RECOIL.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        flash("If this email exists in our system, password reset instructions have been dispatched.", "success")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    # Saved Sensitivities
    cursor.execute("""
        SELECT s.*, g.name as gun_name, c.name as category_name,
               d.model_name, b.name as brand_name, ss.created_at as saved_date
        FROM saved_sensitivities ss
        JOIN sensitivities s ON ss.sensitivity_id = s.id
        JOIN guns g ON s.gun_id = g.id
        JOIN categories c ON g.category_id = c.id
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        WHERE ss.user_id = ?
        ORDER BY ss.created_at DESC
        LIMIT 6
    """, (user_id,))
    saved_list = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM saved_sensitivities WHERE user_id = ?", (user_id,))
    saved_count = cursor.fetchone()[0]

    # User's Device Requests
    cursor.execute("""
        SELECT * FROM device_requests
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    my_requests = cursor.fetchall()

    # Notifications
    cursor.execute("""
        SELECT * FROM notifications
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))
    notifications = cursor.fetchall()

    conn.close()
    return render_template(
        "dashboard.html",
        saved_list=saved_list,
        saved_count=saved_count,
        my_requests=my_requests,
        notifications=notifications
    )

@app.route("/saved")
@login_required
def saved_sensitivities():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.*, g.name as gun_name, c.name as category_name,
               d.model_name, b.name as brand_name, ss.created_at as saved_date
        FROM saved_sensitivities ss
        JOIN sensitivities s ON ss.sensitivity_id = s.id
        JOIN guns g ON s.gun_id = g.id
        JOIN categories c ON g.category_id = c.id
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        WHERE ss.user_id = ?
        ORDER BY ss.created_at DESC
    """, (user_id,))
    saved_list = cursor.fetchall()
    conn.close()

    return render_template("saved.html", saved_list=saved_list)

@app.route("/saved/remove/<int:id>", methods=["POST"])
@login_required
def remove_saved_sensitivity(id):
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_sensitivities WHERE sensitivity_id = ? AND user_id = ?", (id, user_id))
    conn.commit()
    conn.close()
    flash("Sensitivity removed from your saved list.", "success")
    return redirect(url_for("saved_sensitivities"))

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile_page():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        current_pwd = request.form.get("current_password", "")
        new_pwd = request.form.get("new_password", "")

        if not name:
            flash("Name cannot be empty.", "warning")
            return redirect(url_for("profile_page"))

        cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        session["user_name"] = name

        if new_pwd:
            cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            if not current_pwd or not check_password_hash(user["password_hash"], current_pwd):
                conn.close()
                flash("Current password incorrect. Password was not changed.", "danger")
                return redirect(url_for("profile_page"))

            new_hash = generate_password_hash(new_pwd)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user_id))
            flash("Profile and password updated successfully.", "success")
        else:
            flash("Profile updated successfully.", "success")

        conn.commit()
        conn.close()
        return redirect(url_for("profile_page"))

    conn.close()
    return render_template("profile.html")

@app.route("/notifications")
@login_required
def notifications_page():
    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    notifications = cursor.fetchall()
    # Mark read
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return render_template("notifications.html", notifications=notifications)

# ==============================================================================
# ADMIN AUTHENTICATION & DASHBOARD
# ==============================================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if "admin_id" in session:
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        next_url = request.form.get("next", "")

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE email = ?", (email,))
        admin = cursor.fetchone()
        conn.close()

        if admin and check_password_hash(admin["password_hash"], password):
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["name"]
            log_admin_activity(admin["name"], "Logged in", "auth", admin["id"], f"Admin session started for {admin['name']}")
            flash(f"Welcome to ZERO RECOIL Admin Panel, {admin['name']}!", "success")
            if next_url and next_url.startswith("/admin"):
                return redirect(next_url)
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid administrator credentials. Access denied.", "danger")
            return redirect(url_for("admin_login"))

    return render_template("admin/login.html")

@app.route("/admin/logout")
def admin_logout():
    admin_name = session.get("admin_name", "Admin")
    log_admin_activity(admin_name, "Logged out", "auth", session.get("admin_id"), "Session ended")
    session.pop("admin_id", None)
    session.pop("admin_name", None)
    flash("Admin logged out successfully.", "success")
    return redirect(url_for("admin_login"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # 7 Required Stats
    cursor.execute("SELECT COUNT(*) FROM users")
    users_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM guns")
    guns_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM brands")
    brands_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM devices")
    devices_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM sensitivities")
    sens_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM updates")
    updates_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM device_requests WHERE status != 'Completed'")
    requests_cnt = cursor.fetchone()[0]

    # Live Info
    cursor.execute("SELECT * FROM live_stream WHERE id = 1")
    live_info = cursor.fetchone()

    # Recent Sensitivities
    cursor.execute("""
        SELECT s.*, g.name as gun_name, d.model_name, b.name as brand_name
        FROM sensitivities s
        JOIN guns g ON s.gun_id = g.id
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        ORDER BY s.updated_at DESC
        LIMIT 6
    """)
    recent_sensitivities = cursor.fetchall()

    # Activity Audit Logs
    cursor.execute("SELECT * FROM activity_logs ORDER BY created_at DESC LIMIT 15")
    activity_logs = cursor.fetchall()

    conn.close()

    stats = {
        "users": users_cnt,
        "guns": guns_cnt,
        "brands": brands_cnt,
        "devices": devices_cnt,
        "sensitivities": sens_cnt,
        "updates": updates_cnt,
        "requests": requests_cnt
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        live_info=live_info,
        recent_sensitivities=recent_sensitivities,
        activity_logs=activity_logs
    )

# ---------------- Gun Management ----------------
@app.route("/admin/guns")
@admin_required
def admin_guns():
    category_slug = request.args.get("category", "")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM categories ORDER BY sort_order ASC")
    categories = cursor.fetchall()

    query = """
        SELECT g.*, c.name as category_name
        FROM guns g
        JOIN categories c ON g.category_id = c.id
    """
    params = []
    if category_slug:
        query += " WHERE c.slug = ?"
        params.append(category_slug)
    query += " ORDER BY c.sort_order ASC, g.sort_order ASC, g.name ASC"

    cursor.execute(query, params)
    guns = cursor.fetchall()
    conn.close()

    return render_template("admin/guns.html", guns=guns, categories=categories, active_cat=category_slug)

@app.route("/admin/guns/add", methods=["POST"])
@admin_required
def admin_add_gun():
    name = request.form.get("name", "").strip().upper()
    cat_id = request.form.get("category_id")
    image = request.form.get("image", "").strip()
    desc = request.form.get("description", "").strip()
    damage = int(request.form.get("damage", 50))
    rof = int(request.form.get("fire_rate", 50))
    range_val = int(request.form.get("range_val", 50))
    accuracy = int(request.form.get("accuracy", 50))

    slug = slugify(name)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO guns (name, slug, category_id, image, description, damage, fire_rate, range_val, accuracy, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """, (name, slug, cat_id, image, desc, damage, rof, range_val, accuracy))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Added Gun", "guns", new_id, f"Added {name} to category ID {cat_id}")
    flash(f"Gun {name} added successfully!", "success")
    return redirect(url_for("admin_guns"))

@app.route("/admin/guns/edit/<int:id>", methods=["POST"])
@admin_required
def admin_edit_gun(id):
    name = request.form.get("name", "").strip().upper()
    cat_id = request.form.get("category_id")
    image = request.form.get("image", "").strip()
    desc = request.form.get("description", "").strip()
    damage = int(request.form.get("damage", 50))
    rof = int(request.form.get("fire_rate", 50))
    range_val = int(request.form.get("range_val", 50))
    accuracy = int(request.form.get("accuracy", 50))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE guns
        SET name = ?, category_id = ?, image = ?, description = ?, damage = ?, fire_rate = ?, range_val = ?, accuracy = ?
        WHERE id = ?
    """, (name, cat_id, image, desc, damage, rof, range_val, accuracy, id))
    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Edited Gun", "guns", id, f"Updated specifications for {name}")
    flash(f"Gun {name} updated!", "success")
    return redirect(url_for("admin_guns"))

@app.route("/admin/guns/toggle/<int:id>", methods=["POST"])
@admin_required
def admin_toggle_gun_status(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, status FROM guns WHERE id = ?", (id,))
    gun = cursor.fetchone()
    if gun:
        new_status = "inactive" if gun["status"] == "active" else "active"
        cursor.execute("UPDATE guns SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()
        log_admin_activity(session["admin_name"], "Toggled Gun Status", "guns", id, f"Set {gun['name']} status to {new_status}")
    conn.close()
    return redirect(url_for("admin_guns"))

@app.route("/admin/guns/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_gun(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM guns WHERE id = ?", (id,))
    gun = cursor.fetchone()
    if gun:
        cursor.execute("DELETE FROM guns WHERE id = ?", (id,))
        conn.commit()
        log_admin_activity(session["admin_name"], "Deleted Gun", "guns", id, f"Deleted gun {gun['name']}")
        flash(f"Gun {gun['name']} deleted.", "success")
    conn.close()
    return redirect(url_for("admin_guns"))

@app.route("/admin/categories/add", methods=["POST"])
@admin_required
def admin_add_category():
    name = request.form.get("name", "").strip().upper()
    icon = request.form.get("icon", "fa-crosshairs").strip()
    slug = slugify(name)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name, slug, icon) VALUES (?, ?, ?)", (name, slug, icon))
        conn.commit()
        log_admin_activity(session["admin_name"], "Added Category", "categories", cursor.lastrowid, f"Created category {name}")
        flash(f"Category {name} created!", "success")
    except Exception as e:
        flash("Category already exists or error occurred.", "danger")
    finally:
        conn.close()
    return redirect(url_for("admin_guns"))

# ---------------- Device Management ----------------
@app.route("/admin/devices")
@admin_required
def admin_devices():
    brand_slug = request.args.get("brand", "")
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT b.*, (SELECT COUNT(*) FROM devices WHERE brand_id = b.id) as device_count
        FROM brands b
        ORDER BY b.name ASC
    """)
    brands = cursor.fetchall()

    query = """
        SELECT d.*, b.name as brand_name, b.slug as brand_slug,
               (SELECT GROUP_CONCAT(ram, ', ') FROM ram_options WHERE device_id = d.id) as ram_list
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
    """
    params = []
    if brand_slug:
        query += " WHERE b.slug = ?"
        params.append(brand_slug)
    query += " ORDER BY b.name ASC, d.model_name ASC"

    cursor.execute(query, params)
    devices = cursor.fetchall()
    conn.close()

    return render_template("admin/devices.html", devices=devices, brands=brands, active_brand=brand_slug)

@app.route("/admin/devices/add", methods=["POST"])
@admin_required
def admin_add_device():
    brand_id = request.form.get("brand_id")
    model_name = request.form.get("model_name", "").strip()
    processor = request.form.get("processor", "").strip()
    rams = request.form.get("rams", "6 GB, 8 GB").strip()
    refresh = request.form.get("refresh_rate", "120Hz")
    os_sys = request.form.get("operating_system", "Android 14")
    display = request.form.get("display", "").strip()

    slug = slugify(model_name)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO devices (brand_id, model_name, slug, processor, display, refresh_rate, operating_system, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
    """, (brand_id, model_name, slug, processor, display, refresh, os_sys))
    dev_id = cursor.lastrowid

    # Add RAM options
    for r in [x.strip() for x in rams.split(",") if x.strip()]:
        cursor.execute("INSERT INTO ram_options (device_id, ram) VALUES (?, ?)", (dev_id, r))

    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Added Device", "devices", dev_id, f"Added model {model_name} ({processor})")
    flash(f"Device {model_name} added successfully!", "success")
    return redirect(url_for("admin_devices"))

@app.route("/admin/devices/edit/<int:id>", methods=["POST"])
@admin_required
def admin_edit_device(id):
    brand_id = request.form.get("brand_id")
    model_name = request.form.get("model_name", "").strip()
    processor = request.form.get("processor", "").strip()
    rams = request.form.get("rams", "").strip()
    refresh = request.form.get("refresh_rate", "120Hz")
    os_sys = request.form.get("operating_system", "Android 14")
    display = request.form.get("display", "").strip()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE devices
        SET brand_id = ?, model_name = ?, processor = ?, display = ?, refresh_rate = ?, operating_system = ?
        WHERE id = ?
    """, (brand_id, model_name, processor, display, refresh, os_sys, id))

    # Update RAMs
    cursor.execute("DELETE FROM ram_options WHERE device_id = ?", (id,))
    for r in [x.strip() for x in rams.split(",") if x.strip()]:
        cursor.execute("INSERT INTO ram_options (device_id, ram) VALUES (?, ?)", (id, r))

    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Edited Device", "devices", id, f"Updated {model_name}")
    flash(f"Device {model_name} updated!", "success")
    return redirect(url_for("admin_devices"))

@app.route("/admin/devices/toggle/<int:id>", methods=["POST"])
@admin_required
def admin_toggle_device_status(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT model_name, status FROM devices WHERE id = ?", (id,))
    dev = cursor.fetchone()
    if dev:
        new_status = "inactive" if dev["status"] == "active" else "active"
        cursor.execute("UPDATE devices SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()
        log_admin_activity(session["admin_name"], "Toggled Device Status", "devices", id, f"Set {dev['model_name']} to {new_status}")
    conn.close()
    return redirect(url_for("admin_devices"))

@app.route("/admin/devices/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_device(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT model_name FROM devices WHERE id = ?", (id,))
    dev = cursor.fetchone()
    if dev:
        cursor.execute("DELETE FROM devices WHERE id = ?", (id,))
        conn.commit()
        log_admin_activity(session["admin_name"], "Deleted Device", "devices", id, f"Deleted device {dev['model_name']}")
        flash(f"Device {dev['model_name']} deleted.", "success")
    conn.close()
    return redirect(url_for("admin_devices"))

@app.route("/admin/brands/add", methods=["POST"])
@admin_required
def admin_add_brand():
    name = request.form.get("name", "").strip()
    logo = request.form.get("logo", "fa-mobile").strip()
    slug = slugify(name)

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO brands (name, slug, logo) VALUES (?, ?, ?)", (name, slug, logo))
        conn.commit()
        log_admin_activity(session["admin_name"], "Added Brand", "brands", cursor.lastrowid, f"Added brand {name}")
        flash(f"Brand {name} added!", "success")
    except:
        flash("Brand already exists or error occurred.", "danger")
    finally:
        conn.close()
    return redirect(url_for("admin_devices"))

# ---------------- Sensitivity Management ----------------
@app.route("/admin/sensitivities")
@admin_required
def admin_sensitivities():
    gun_id = request.args.get("gun_id")
    brand_id = request.args.get("brand_id")

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM guns ORDER BY name ASC")
    guns = cursor.fetchall()
    cursor.execute("SELECT id, name FROM brands ORDER BY name ASC")
    brands = cursor.fetchall()
    cursor.execute("""
        SELECT d.id, d.model_name, d.processor, b.name as brand_name,
               (SELECT GROUP_CONCAT(ram, ', ') FROM ram_options WHERE device_id = d.id) as ram_list
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
        ORDER BY b.name ASC, d.model_name ASC
    """)
    devices = cursor.fetchall()

    query = """
        SELECT s.*, g.name as gun_name, d.model_name, b.name as brand_name
        FROM sensitivities s
        JOIN guns g ON s.gun_id = g.id
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        WHERE 1=1
    """
    params = []
    if gun_id:
        query += " AND s.gun_id = ?"
        params.append(gun_id)
    if brand_id:
        query += " AND d.brand_id = ?"
        params.append(brand_id)

    query += " ORDER BY s.updated_at DESC"
    cursor.execute(query, params)
    sensitivities = cursor.fetchall()
    conn.close()

    return render_template(
        "admin/sensitivities.html",
        sensitivities=sensitivities,
        guns=guns,
        brands=brands,
        devices=devices,
        selected_gun_id=int(gun_id) if gun_id else None,
        selected_brand_id=int(brand_id) if brand_id else None
    )

@app.route("/admin/sensitivities/add", methods=["POST"])
@admin_required
def admin_add_sens():
    gun_id = request.form.get("gun_id")
    device_id = request.form.get("device_id")
    ram = request.form.get("ram", "6 GB").strip()
    processor = request.form.get("processor", "").strip()

    gen = int(request.form.get("general", 95))
    rd = int(request.form.get("red_dot", 90))
    s2 = int(request.form.get("scope_2x", 85))
    s4 = int(request.form.get("scope_4x", 80))
    snp = int(request.form.get("sniper", 65))
    fl = int(request.form.get("free_look", 75))

    aim = request.form.get("aim_precision", "Default")
    btn = int(request.form.get("fire_button_size", 45))
    dpi = int(request.form.get("dpi", 411))
    ctrl = request.form.get("control_settings", "")
    author = request.form.get("updated_by", session.get("admin_name", "ARMUGA"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sensitivities (
            gun_id, device_id, ram, processor, general, red_dot, scope_2x, scope_4x,
            sniper, free_look, aim_precision, fire_button_size, dpi, control_settings,
            updated_by, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
    """, (gun_id, device_id, ram, processor, gen, rd, s2, s4, snp, fl, aim, btn, dpi, ctrl, author))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_admin_activity(author, "Calibrated Sensitivity", "sensitivities", new_id, f"Added profile for Gun #{gun_id} + Device #{device_id} ({ram})")
    flash("Zero Recoil sensitivity profile added!", "success")
    return redirect(url_for("admin_sensitivities"))

@app.route("/admin/sensitivities/edit/<int:id>", methods=["POST"])
@admin_required
def admin_edit_sens(id):
    gun_id = request.form.get("gun_id")
    device_id = request.form.get("device_id")
    ram = request.form.get("ram", "").strip()
    processor = request.form.get("processor", "").strip()

    gen = int(request.form.get("general", 95))
    rd = int(request.form.get("red_dot", 90))
    s2 = int(request.form.get("scope_2x", 85))
    s4 = int(request.form.get("scope_4x", 80))
    snp = int(request.form.get("sniper", 65))
    fl = int(request.form.get("free_look", 75))

    aim = request.form.get("aim_precision", "Default")
    btn = int(request.form.get("fire_button_size", 45))
    dpi = int(request.form.get("dpi", 411))
    ctrl = request.form.get("control_settings", "")
    author = request.form.get("updated_by", session.get("admin_name", "ARMUGA"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sensitivities
        SET gun_id = ?, device_id = ?, ram = ?, processor = ?, general = ?, red_dot = ?,
            scope_2x = ?, scope_4x = ?, sniper = ?, free_look = ?, aim_precision = ?,
            fire_button_size = ?, dpi = ?, control_settings = ?, updated_by = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (gun_id, device_id, ram, processor, gen, rd, s2, s4, snp, fl, aim, btn, dpi, ctrl, author, id))
    conn.commit()
    conn.close()

    log_admin_activity(author, "Updated Sensitivity", "sensitivities", id, f"Re-calibrated sensitivity #{id}")
    flash("Sensitivity profile updated!", "success")
    return redirect(url_for("admin_sensitivities"))

@app.route("/admin/sensitivities/duplicate/<int:id>", methods=["POST"])
@admin_required
def admin_duplicate_sens(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sensitivities WHERE id = ?", (id,))
    orig = cursor.fetchone()
    if orig:
        cursor.execute("""
            INSERT INTO sensitivities (
                gun_id, device_id, ram, processor, general, red_dot, scope_2x, scope_4x,
                sniper, free_look, aim_precision, fire_button_size, dpi, graphics, fps,
                control_settings, updated_by, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (
            orig["gun_id"], orig["device_id"], orig["ram"], orig["processor"],
            orig["general"], orig["red_dot"], orig["scope_2x"], orig["scope_4x"],
            orig["sniper"], orig["free_look"], orig["aim_precision"], orig["fire_button_size"],
            orig["dpi"], orig["graphics"], orig["fps"], orig["control_settings"],
            session["admin_name"]
        ))
        new_id = cursor.lastrowid
        conn.commit()
        log_admin_activity(session["admin_name"], "Duplicated Sensitivity", "sensitivities", new_id, f"Duplicated profile from #{id}")
        flash("Sensitivity profile duplicated! You can now adjust its RAM or values.", "success")
    conn.close()
    return redirect(url_for("admin_sensitivities"))

@app.route("/admin/sensitivities/toggle/<int:id>", methods=["POST"])
@admin_required
def admin_toggle_sens_status(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM sensitivities WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        new_status = "inactive" if row["status"] == "active" else "active"
        cursor.execute("UPDATE sensitivities SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()
        log_admin_activity(session["admin_name"], "Toggled Sensitivity Status", "sensitivities", id, f"Set to {new_status}")
    conn.close()
    return redirect(url_for("admin_sensitivities"))

@app.route("/admin/sensitivities/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_sens(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sensitivities WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    log_admin_activity(session["admin_name"], "Deleted Sensitivity", "sensitivities", id, f"Deleted sensitivity record #{id}")
    flash("Sensitivity record deleted.", "success")
    return redirect(url_for("admin_sensitivities"))

# ---------------- Bulk CSV Import / Export (Section 21) ----------------
@app.route("/admin/bulk-csv")
@admin_required
def admin_bulk_csv():
    return render_template("admin/bulk_csv.html")

@app.route("/admin/export-csv")
@admin_required
def admin_export_csv():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT b.name as brand, d.model_name as model, s.ram, s.processor, g.name as gun,
               s.general, s.red_dot, s.scope_2x, s.scope_4x, s.sniper, s.free_look,
               s.aim_precision, s.fire_button_size, s.dpi, s.updated_by
        FROM sensitivities s
        JOIN guns g ON s.gun_id = g.id
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        ORDER BY b.name ASC, d.model_name ASC, g.name ASC
    """)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Brand", "Model", "RAM", "Processor", "Gun",
        "General", "Red Dot", "2X", "4X", "Sniper", "Free Look",
        "Aim Precision", "Fire Button Size", "DPI", "Updated By"
    ])
    for r in rows:
        writer.writerow([
            r["brand"], r["model"], r["ram"], r["processor"], r["gun"],
            r["general"], r["red_dot"], r["scope_2x"], r["scope_4x"], r["sniper"], r["free_look"],
            r["aim_precision"], r["fire_button_size"], r["dpi"], r["updated_by"]
        ])

    csv_data = output.getvalue()
    log_admin_activity(session["admin_name"], "Exported CSV", "sensitivities", None, f"Exported {len(rows)} records")
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=zero_recoil_sensitivities_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@app.route("/admin/sample-csv")
@admin_required
def admin_sample_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Brand", "Model", "RAM", "Processor", "Gun",
        "General", "Red Dot", "2X", "4X", "Sniper", "Free Look",
        "Aim Precision", "Fire Button Size", "DPI"
    ])
    writer.writerow(["POCO", "POCO M6 5G", "6 GB", "MediaTek Dimensity 6100+", "MP40", 98, 96, 92, 88, 72, 80, "Default", 46, 440])
    writer.writerow(["POCO", "POCO X6 Pro 5G", "12 GB", "MediaTek Dimensity 8300 Ultra", "M1887", 97, 95, 88, 84, 62, 70, "Default", 42, 490])
    writer.writerow(["Samsung", "Samsung Galaxy S23", "8 GB", "Snapdragon 8 Gen 2 for Galaxy", "SCAR", 90, 87, 83, 78, 62, 72, "Default", 47, 475])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=zero_recoil_sample_template.csv"}
    )

@app.route("/admin/import-csv", methods=["POST"])
@admin_required
def admin_import_csv():
    if "csv_file" not in request.files:
        flash("No CSV file selected.", "danger")
        return redirect(url_for("admin_bulk_csv"))

    file = request.files["csv_file"]
    if file.filename == "":
        flash("No file selected.", "danger")
        return redirect(url_for("admin_bulk_csv"))

    try:
        stream = io.StringIO(file.stream.read().decode("UTF8", errors="ignore"))
        reader = csv.DictReader(stream)

        conn = get_db()
        cursor = conn.cursor()

        # Cache existing brands, devices, guns
        cursor.execute("SELECT id, name FROM brands")
        brand_map = {r["name"].strip().lower(): r["id"] for r in cursor.fetchall()}

        cursor.execute("SELECT id, model_name FROM devices")
        dev_map = {r["model_name"].strip().lower(): r["id"] for r in cursor.fetchall()}

        cursor.execute("SELECT id, name FROM guns")
        gun_map = {r["name"].strip().lower(): r["id"] for r in cursor.fetchall()}

        imported_count = 0

        for row in reader:
            b_name = (row.get("Brand") or "").strip()
            m_name = (row.get("Model") or "").strip()
            g_name = (row.get("Gun") or "").strip()
            ram = (row.get("RAM") or "6 GB").strip()
            proc = (row.get("Processor") or "Octa-Core").strip()

            if not b_name or not m_name or not g_name:
                continue

            # Ensure brand exists
            b_key = b_name.lower()
            if b_key not in brand_map:
                cursor.execute("INSERT INTO brands (name, slug) VALUES (?, ?)", (b_name, slugify(b_name)))
                brand_map[b_key] = cursor.lastrowid

            # Ensure device exists
            m_key = m_name.lower()
            if m_key not in dev_map:
                cursor.execute("""
                    INSERT INTO devices (brand_id, model_name, slug, processor, status)
                    VALUES (?, ?, ?, ?, 'active')
                """, (brand_map[b_key], m_name, slugify(m_name), proc))
                dev_id = cursor.lastrowid
                dev_map[m_key] = dev_id
                cursor.execute("INSERT INTO ram_options (device_id, ram) VALUES (?, ?)", (dev_id, ram))
            else:
                dev_id = dev_map[m_key]

            # Ensure gun exists
            g_key = g_name.lower()
            if g_key not in gun_map:
                cursor.execute("INSERT INTO guns (name, slug, category_id, status) VALUES (?, ?, 1, 'active')", (g_name.upper(), slugify(g_name)))
                gun_id = cursor.lastrowid
                gun_map[g_key] = gun_id
            else:
                gun_id = gun_map[g_key]

            gen = int(row.get("General") or 95)
            rd = int(row.get("Red Dot") or 90)
            s2 = int(row.get("2X") or 85)
            s4 = int(row.get("4X") or 80)
            snp = int(row.get("Sniper") or 65)
            fl = int(row.get("Free Look") or 75)
            aim = row.get("Aim Precision") or "Default"
            btn = int(row.get("Fire Button Size") or 45)
            dpi = int(row.get("DPI") or 411)

            cursor.execute("""
                INSERT INTO sensitivities (
                    gun_id, device_id, ram, processor, general, red_dot, scope_2x, scope_4x,
                    sniper, free_look, aim_precision, fire_button_size, dpi, updated_by, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
            """, (gun_id, dev_id, ram, proc, gen, rd, s2, s4, snp, fl, aim, btn, dpi, session["admin_name"]))
            imported_count += 1

        conn.commit()
        conn.close()

        log_admin_activity(session["admin_name"], "Imported CSV", "sensitivities", None, f"Imported {imported_count} records via CSV")
        flash(f"Successfully imported {imported_count} sensitivity records!", "success")
    except Exception as e:
        flash(f"Error parsing CSV file: {str(e)}", "danger")

    return redirect(url_for("admin_bulk_csv"))

# ---------------- User Management ----------------
@app.route("/admin/users")
@admin_required
def admin_users():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, (SELECT COUNT(*) FROM saved_sensitivities WHERE user_id = u.id) as saved_count
        FROM users u
        ORDER BY u.created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return render_template("admin/users.html", users=users)

@app.route("/admin/users/toggle/<int:id>", methods=["POST"])
@admin_required
def admin_toggle_user_status(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, status FROM users WHERE id = ?", (id,))
    user = cursor.fetchone()
    if user:
        new_status = "inactive" if user["status"] == "active" else "active"
        cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, id))
        conn.commit()
        log_admin_activity(session["admin_name"], "Toggled User Status", "users", id, f"Set {user['name']} to {new_status}")
    conn.close()
    return redirect(url_for("admin_users"))

@app.route("/admin/users/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_user(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    log_admin_activity(session["admin_name"], "Deleted User", "users", id, f"Deleted user account #{id}")
    flash("User account deleted.", "success")
    return redirect(url_for("admin_users"))

# ---------------- Updates Management (Section 23) ----------------
@app.route("/admin/updates")
@admin_required
def admin_updates():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM updates ORDER BY created_at DESC")
    updates = cursor.fetchall()
    conn.close()
    return render_template("admin/updates.html", updates=updates)

@app.route("/admin/updates/add", methods=["POST"])
@admin_required
def admin_add_update():
    title = request.form.get("title", "").strip()
    image = request.form.get("image", "").strip()
    desc = request.form.get("description", "").strip()
    author = request.form.get("admin_name", "ARMUGA X CATZX")
    slug = slugify(title)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO updates (title, slug, description, image, admin_name, published)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (title, slug, desc, image, author))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Published Update", "updates", new_id, f"Published article: {title}")
    flash("Update published to community!", "success")
    return redirect(url_for("admin_updates"))

@app.route("/admin/updates/edit/<int:id>", methods=["POST"])
@admin_required
def admin_edit_update(id):
    title = request.form.get("title", "").strip()
    image = request.form.get("image", "").strip()
    desc = request.form.get("description", "").strip()
    author = request.form.get("admin_name", "ARMUGA X CATZX")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE updates
        SET title = ?, description = ?, image = ?, admin_name = ?
        WHERE id = ?
    """, (title, desc, image, author, id))
    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Edited Update", "updates", id, f"Updated article: {title}")
    flash("Update modified successfully!", "success")
    return redirect(url_for("admin_updates"))

@app.route("/admin/updates/toggle/<int:id>", methods=["POST"])
@admin_required
def admin_toggle_update_status(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT published FROM updates WHERE id = ?", (id,))
    row = cursor.fetchone()
    if row:
        new_val = 0 if row["published"] else 1
        cursor.execute("UPDATE updates SET published = ? WHERE id = ?", (new_val, id))
        conn.commit()
        log_admin_activity(session["admin_name"], "Toggled Update Status", "updates", id, f"Published set to {new_val}")
    conn.close()
    return redirect(url_for("admin_updates"))

@app.route("/admin/updates/delete/<int:id>", methods=["POST"])
@admin_required
def admin_delete_update(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM updates WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    log_admin_activity(session["admin_name"], "Deleted Update", "updates", id, f"Deleted update #{id}")
    flash("Update deleted.", "success")
    return redirect(url_for("admin_updates"))

# ---------------- Social Links Management (Section 25) ----------------
@app.route("/admin/social-links")
@admin_required
def admin_social_links():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM social_links ORDER BY id ASC")
    links = cursor.fetchall()
    conn.close()
    return render_template("admin/social_links.html", links=links)

@app.route("/admin/social-links/update/<int:id>", methods=["POST"])
@admin_required
def admin_update_social_link(id):
    title = request.form.get("title", "").strip()
    subtitle = request.form.get("subtitle", "").strip()
    url = request.form.get("url", "").strip()
    enabled = int(request.form.get("enabled", 1))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE social_links
        SET title = ?, subtitle = ?, url = ?, enabled = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (title, subtitle, url, enabled, id))
    conn.commit()
    conn.close()

    log_admin_activity(session["admin_name"], "Updated Social Link", "social_links", id, f"Updated {title} ({'Enabled' if enabled else 'Disabled'})")
    flash(f"Social link {title} updated!", "success")
    return redirect(url_for("admin_social_links"))

# ---------------- Live Stream Control (Section 24) ----------------
@app.route("/admin/live")
@admin_required
def admin_live():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM live_stream WHERE id = 1")
    live = cursor.fetchone()
    conn.close()
    return render_template("admin/live.html", live=live)

@app.route("/admin/live/update", methods=["POST"])
@admin_required
def admin_update_live():
    is_live = int(request.form.get("is_live", 0))
    stream_url = request.form.get("stream_url", "").strip()
    title = request.form.get("title", "").strip()
    admin_name = session.get("admin_name", "ARMUGA")

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE live_stream
        SET is_live = ?, stream_url = ?, title = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (is_live, stream_url, title, admin_name))
    conn.commit()
    conn.close()

    status_str = "LIVE NOW" if is_live else "OFFLINE"
    log_admin_activity(admin_name, "Changed Live Broadcast Status", "live_stream", 1, f"Status changed to {status_str}")
    flash(f"Live broadcast state set to: {status_str}", "success")
    return redirect(url_for("admin_live"))

# ---------------- Device Requests (Section 22) ----------------
@app.route("/admin/requests")
@admin_required
def admin_requests():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM device_requests ORDER BY created_at DESC")
    requests_list = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM device_requests WHERE status = 'Pending'")
    pending_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM device_requests WHERE status = 'In Progress'")
    in_prog_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM device_requests WHERE status = 'Completed'")
    completed_cnt = cursor.fetchone()[0]

    conn.close()
    return render_template(
        "admin/requests.html",
        requests=requests_list,
        pending_count=pending_cnt,
        in_progress_count=in_prog_cnt,
        completed_count=completed_cnt
    )

@app.route("/admin/requests/update/<int:id>", methods=["POST"])
@admin_required
def admin_update_request_status(id):
    new_status = request.form.get("status", "Pending")
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, brand, model FROM device_requests WHERE id = ?", (id,))
    req = cursor.fetchone()
    if req:
        cursor.execute("UPDATE device_requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (new_status, id))
        if req["user_id"] and new_status == "Completed":
            cursor.execute("""
                INSERT INTO notifications (user_id, title, message)
                VALUES (?, ?, ?)
            """, (req["user_id"], f"Sensitivity Ready: {req['brand']} {req['model']}", f"ARMUGA and CATZX have finished benchmarking {req['brand']} {req['model']}! Check out the new Zero Recoil sensitivities."))

        conn.commit()
        log_admin_activity(session["admin_name"], "Updated Device Request", "device_requests", id, f"Set request for {req['brand']} {req['model']} to {new_status}")
        flash(f"Request #{id} status set to {new_status}.", "success")
    conn.close()
    return redirect(url_for("admin_requests"))

# ---------------- Admin Settings ----------------
@app.route("/admin/settings", methods=["GET", "POST"])
@admin_required
def admin_settings():
    admin_id = session["admin_id"]
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        current_pwd = request.form.get("current_password", "")
        new_pwd = request.form.get("new_password", "")

        cursor.execute("UPDATE admins SET name = ? WHERE id = ?", (name, admin_id))
        session["admin_name"] = name

        if new_pwd:
            cursor.execute("SELECT password_hash FROM admins WHERE id = ?", (admin_id,))
            row = cursor.fetchone()
            if not current_pwd or not check_password_hash(row["password_hash"], current_pwd):
                conn.close()
                flash("Current administrator password incorrect.", "danger")
                return redirect(url_for("admin_settings"))

            cursor.execute("UPDATE admins SET password_hash = ? WHERE id = ?", (generate_password_hash(new_pwd), admin_id))
            flash("Admin password and profile updated.", "success")
        else:
            flash("Admin profile updated.", "success")

        conn.commit()
        conn.close()
        log_admin_activity(name, "Updated Admin Settings", "admins", admin_id, "Changed admin profile/credentials")
        return redirect(url_for("admin_settings"))

    conn.close()
    return render_template("admin/settings.html")

# ==============================================================================
# REST API ENDPOINTS
# ==============================================================================

@app.route("/api/brands")
def api_brands():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, slug, logo FROM brands WHERE status = 'active' ORDER BY sort_order ASC")
    brands = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(brands)

@app.route("/api/devices")
def api_devices():
    brand_id = request.args.get("brand_id")
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT d.id, d.model_name, d.slug, d.processor, d.refresh_rate,
               (SELECT GROUP_CONCAT(ram, ', ') FROM ram_options WHERE device_id = d.id) as ram_list
        FROM devices d
        WHERE d.status = 'active'
    """
    params = []
    if brand_id:
        query += " AND d.brand_id = ?"
        params.append(brand_id)
    query += " ORDER BY d.model_name ASC"

    cursor.execute(query, params)
    devices = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(devices)

@app.route("/api/device/<int:device_id>/details")
def api_device_details(device_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, b.name as brand_name
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
        WHERE d.id = ?
    """, (device_id,))
    dev = cursor.fetchone()
    if not dev:
        conn.close()
        return jsonify({"error": "Device not found"}), 404

    cursor.execute("SELECT ram FROM ram_options WHERE device_id = ?", (device_id,))
    rams = [r["ram"] for r in cursor.fetchall()]
    conn.close()

    res = dict(dev)
    res["rams"] = rams
    return jsonify(res)

@app.route("/api/sensitivity/lookup")
def api_sensitivity_lookup():
    gun_id = request.args.get("gun_id")
    device_id = request.args.get("device_id")
    ram = request.args.get("ram", "").strip()
    processor = request.args.get("processor", "").strip()

    if not gun_id or not device_id:
        return jsonify({"found": False, "error": "gun_id and device_id are required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Exact match: gun + device + ram
    cursor.execute("""
        SELECT s.*, g.name as gun_name, g.slug as gun_slug,
               d.model_name, b.name as brand_name
        FROM sensitivities s
        JOIN guns g ON s.gun_id = g.id
        JOIN devices d ON s.device_id = d.id
        JOIN brands b ON d.brand_id = b.id
        WHERE s.gun_id = ? AND s.device_id = ? AND s.ram = ? AND s.status = 'active'
        LIMIT 1
    """, (gun_id, device_id, ram))
    row = cursor.fetchone()

    # If exact RAM isn't in DB, check device default for this gun (fallback to same device)
    if not row:
        cursor.execute("""
            SELECT s.*, g.name as gun_name, g.slug as gun_slug,
                   d.model_name, b.name as brand_name
            FROM sensitivities s
            JOIN guns g ON s.gun_id = g.id
            JOIN devices d ON s.device_id = d.id
            JOIN brands b ON d.brand_id = b.id
            WHERE s.gun_id = ? AND s.device_id = ? AND s.status = 'active'
            ORDER BY s.updated_at DESC
            LIMIT 1
        """, (gun_id, device_id))
        row = cursor.fetchone()

    conn.close()

    if row:
        return jsonify({"found": True, "sensitivity": dict(row)})
    else:
        return jsonify({"found": False})

@app.route("/api/social-links")
def api_social_links():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, platform_key, title, subtitle, url, button_text, icon, enabled FROM social_links ORDER BY id ASC")
    links = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return jsonify(links)

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify({"guns": [], "devices": [], "brands": []})

    term = f"%{q}%"
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT g.id, g.name, g.slug, c.name as category_name
        FROM guns g
        JOIN categories c ON g.category_id = c.id
        WHERE g.name LIKE ? AND g.status = 'active'
        LIMIT 5
    """, (term,))
    guns = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT d.id, d.model_name, d.slug, b.name as brand_name
        FROM devices d
        JOIN brands b ON d.brand_id = b.id
        WHERE (d.model_name LIKE ? OR b.name LIKE ?) AND d.status = 'active'
        LIMIT 5
    """, (term, term))
    devices = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT b.id, b.name, b.slug,
               (SELECT COUNT(*) FROM devices WHERE brand_id = b.id AND status = 'active') as device_count
        FROM brands b
        WHERE b.name LIKE ? AND b.status = 'active'
        LIMIT 3
    """, (term,))
    brands = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return jsonify({"guns": guns, "devices": devices, "brands": brands})

@app.route("/api/save-sensitivity", methods=["POST"])
def api_save_sensitivity():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    data = request.get_json() or {}
    sens_id = data.get("sensitivity_id")
    if not sens_id:
        return jsonify({"error": "Missing sensitivity_id"}), 400

    user_id = session["user_id"]
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO saved_sensitivities (user_id, sensitivity_id) VALUES (?, ?)", (user_id, sens_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Saved to your dashboard!"})
    except Exception as e:
        conn.close()
        return jsonify({"success": True, "message": "Already saved to your dashboard!"})

@app.route("/api/request-device", methods=["POST"])
def api_request_device():
    data = request.get_json() or {}
    brand = (data.get("brand") or "").strip()
    model = (data.get("model") or "").strip()
    ram = (data.get("ram") or "").strip()
    proc = (data.get("processor") or "").strip()
    email = (data.get("user_email") or "").strip()
    notes = (data.get("notes") or "").strip()

    if not brand or not model or not email:
        return jsonify({"error": "Brand, model and email are required"}), 400

    user_id = session.get("user_id", None)

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO device_requests (user_id, user_email, brand, model, ram, processor, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')
    """, (user_id, email, brand, model, ram, proc, notes))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Request submitted to ARMUGA & CATZX!"})

if __name__ == "__main__":
    init_db()
    seed_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"ZERO RECOIL by ARMUGA X CATZX running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
