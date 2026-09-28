"""
ZERO RECOIL - Database Engine & Schema
ARMUGA X CATZX
"""
import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zero_recoil.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Admins table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Users table (customers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)

    # Gun Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        icon TEXT,
        sort_order INTEGER DEFAULT 0
    );
    """)

    # Guns
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS guns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        category_id INTEGER NOT NULL,
        image TEXT,
        description TEXT,
        damage INTEGER DEFAULT 0,
        fire_rate INTEGER DEFAULT 0,
        range_val INTEGER DEFAULT 0,
        accuracy INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        sort_order INTEGER DEFAULT 0,
        FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE
    );
    """)

    # Brands
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        logo TEXT,
        status TEXT DEFAULT 'active',
        sort_order INTEGER DEFAULT 0
    );
    """)

    # Devices
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand_id INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        processor TEXT NOT NULL,
        display TEXT,
        refresh_rate TEXT DEFAULT '120Hz',
        operating_system TEXT DEFAULT 'Android 14',
        image TEXT,
        status TEXT DEFAULT 'active',
        FOREIGN KEY(brand_id) REFERENCES brands(id) ON DELETE CASCADE
    );
    """)

    # RAM options per device
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ram_options (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        ram TEXT NOT NULL,
        FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
    );
    """)

    # Sensitivities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensitivities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gun_id INTEGER NOT NULL,
        device_id INTEGER NOT NULL,
        ram TEXT NOT NULL,
        processor TEXT NOT NULL,
        general INTEGER NOT NULL,
        red_dot INTEGER NOT NULL,
        scope_2x INTEGER NOT NULL,
        scope_4x INTEGER NOT NULL,
        sniper INTEGER NOT NULL,
        free_look INTEGER NOT NULL,
        aim_precision TEXT DEFAULT 'Default',
        fire_button_size INTEGER DEFAULT 45,
        dpi INTEGER DEFAULT 411,
        graphics TEXT DEFAULT 'Ultra (High FPS)',
        fps TEXT DEFAULT 'High',
        control_settings TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by TEXT DEFAULT 'ARMUGA',
        status TEXT DEFAULT 'active',
        FOREIGN KEY(gun_id) REFERENCES guns(id) ON DELETE CASCADE,
        FOREIGN KEY(device_id) REFERENCES devices(id) ON DELETE CASCADE
    );
    """)

    # Updates
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT NOT NULL,
        image TEXT,
        admin_id INTEGER,
        admin_name TEXT DEFAULT 'ARMUGA X CATZX',
        published INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(admin_id) REFERENCES admins(id)
    );
    """)

    # Social links
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS social_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_key TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        subtitle TEXT NOT NULL,
        url TEXT NOT NULL,
        button_text TEXT DEFAULT 'FOLLOW',
        icon TEXT DEFAULT 'instagram',
        enabled INTEGER DEFAULT 1,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Live Stream Controller
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS live_stream (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        is_live INTEGER DEFAULT 0,
        stream_url TEXT DEFAULT '',
        title TEXT DEFAULT '🔴 ARMUGA X CATZX IS LIVE',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_by TEXT DEFAULT 'ARMUGA'
    );
    """)

    # Device Requests
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS device_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_email TEXT NOT NULL,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        ram TEXT,
        processor TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)

    # Saved Sensitivities
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_sensitivities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        sensitivity_id INTEGER NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, sensitivity_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(sensitivity_id) REFERENCES sensitivities(id) ON DELETE CASCADE
    );
    """)

    # Activity Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_name TEXT NOT NULL,
        action TEXT NOT NULL,
        target_type TEXT,
        target_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

def seed_db():
    conn = get_db()
    cursor = conn.cursor()

    # 1. Admins: ARMUGA & CATZX
    cursor.execute("SELECT COUNT(*) FROM admins")
    if cursor.fetchone()[0] == 0:
        admins = [
            ("ARMUGA", "armuga@zerorecoil.gg", generate_password_hash("armuga1234"), "admin"),
            ("CATZX", "catzx@zerorecoil.gg", generate_password_hash("catzx1234"), "admin")
        ]
        cursor.executemany("INSERT INTO admins (name, email, password_hash, role) VALUES (?, ?, ?, ?)", admins)
        print("Seeded Admins: ARMUGA & CATZX")

    # 2. Live Stream row
    cursor.execute("SELECT COUNT(*) FROM live_stream")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO live_stream (id, is_live, stream_url, title, updated_by)
        VALUES (1, 1, 'https://www.youtube.com/@armugaxcatzx/live', '🔴 ARMUGA X CATZX IS LIVE - TESTING FF HEADSHOT SENSITIVITIES', 'ARMUGA')
        """)

    # 3. Social Links
    cursor.execute("SELECT COUNT(*) FROM social_links")
    if cursor.fetchone()[0] == 0:
        links = [
            ("instagram_1", "INSTAGRAM 01", "FOLLOW ARMUGA ON INSTAGRAM", "https://instagram.com/armuga_official", "FOLLOW", "instagram", 1),
            ("instagram_2", "INSTAGRAM 02", "FOLLOW CATZX ON INSTAGRAM", "https://instagram.com/catzx_official", "FOLLOW", "instagram", 1),
            ("youtube", "YOUTUBE", "SUBSCRIBE TO OUR OFFICIAL YOUTUBE", "https://youtube.com/@armugaxcatzx", "SUBSCRIBE", "youtube", 1),
        ]
        cursor.executemany("""
        INSERT INTO social_links (platform_key, title, subtitle, url, button_text, icon, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, links)
        print("Seeded Social Links")

    # 4. Categories
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cats = [
            ("ASSAULT RIFLES", "assault-rifles", "fa-crosshairs", 1),
            ("SMG", "smg", "fa-bolt", 2),
            ("SHOTGUN", "shotgun", "fa-bullseye", 3),
            ("SNIPER", "sniper", "fa-eye", 4),
            ("PISTOL", "pistol", "fa-shield-halved", 5),
        ]
        cursor.executemany("INSERT INTO categories (name, slug, icon, sort_order) VALUES (?, ?, ?, ?)", cats)
        print("Seeded Categories")

    # Get category ID map
    cursor.execute("SELECT id, slug FROM categories")
    cat_map = {row["slug"]: row["id"] for row in cursor.fetchall()}

    # 5. Guns
    cursor.execute("SELECT COUNT(*) FROM guns")
    if cursor.fetchone()[0] == 0:
        guns = [
            # Assault Rifles
            ("M4A1", "m4a1", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "High stability AR with balanced recoil and fast fire rate.", 54, 57, 79, 55, "active", 1),
            ("SCAR", "scar", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "Stable mid-range rifle preferred for beginner to pro drag headshots.", 53, 61, 68, 41, "active", 2),
            ("AK47", "ak47", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1590483736422-421715e2060d?w=600&auto=format&fit=crop&q=80", "High damage beast requiring precision drag recoil control.", 61, 56, 73, 41, "active", 3),
            ("XM8", "xm8", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1584281722573-b3a6288b4461?w=600&auto=format&fit=crop&q=80", "Pre-attached 2x scope with laser recoil stability.", 57, 60, 65, 58, "active", 4),
            ("GROZA", "groza", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "Airdrop heavy assault rifle with unmatched stopping power.", 61, 58, 77, 52, "active", 5),
            ("AN94", "an94", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "Heavy fire rate bursts with high headshot multiplier.", 60, 58, 62, 48, "active", 6),
            ("FAMAS", "famas", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "3-bullet burst rifle lethal when dialed in with high DPI.", 53, 67, 70, 54, "active", 7),
            ("AUG", "aug", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1584281722573-b3a6288b4461?w=600&auto=format&fit=crop&q=80", "Versatile bullpup rifle with built-in enhanced stability.", 56, 61, 71, 52, "active", 8),
            ("PARAFAL", "parafal", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "Long-range hitscan rifle with immense single bullet damage.", 69, 48, 61, 46, "active", 9),
            ("WOODPECKER", "woodpecker", cat_map["assault-rifles"], "https://images.unsplash.com/photo-1590483736422-421715e2060d?w=600&auto=format&fit=crop&q=80", "Marksman rifle with supreme armor penetration for one-tap headshots.", 71, 38, 63, 69, "active", 10),

            # SMG
            ("MP40", "mp40", cat_map["smg"], "https://images.unsplash.com/photo-1579547621113-e4bb2a09bcf6?w=600&auto=format&fit=crop&q=80", "The ultimate Free Fire close-range king. Maximum fire rate.", 48, 83, 22, 17, "active", 11),
            ("MP5", "mp5", cat_map["smg"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "Highly reliable SMG with chip upgrades and laser tracking.", 48, 76, 27, 54, "active", 12),
            ("UMP", "ump", cat_map["smg"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "Esports favorite for drag headshots with natural armor penetration.", 50, 74, 25, 42, "active", 13),
            ("VECTOR", "vector", cat_map["smg"], "https://images.unsplash.com/photo-1584281722573-b3a6288b4461?w=600&auto=format&fit=crop&q=80", "Akimbo dual-wield high burst SMG.", 47, 81, 32, 61, "active", 14),
            ("THOMPSON", "thompson", cat_map["smg"], "https://images.unsplash.com/photo-1590483736422-421715e2060d?w=600&auto=format&fit=crop&q=80", "Large capacity drum magazine SMG for squad wipes.", 50, 77, 33, 34, "active", 15),
            ("P90", "p90", cat_map["smg"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "Tremendous ammo pool and smooth recoil curve.", 48, 75, 27, 44, "active", 16),

            # Shotguns
            ("M1887", "m1887", cat_map["shotgun"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "Double-barrel one-tap legend. Requires rapid drag sensitivity.", 100, 42, 21, 10, "active", 17),
            ("M1014", "m1014", cat_map["shotgun"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "6-shot semi-auto shotgun devastating in tight corners.", 94, 38, 10, 10, "active", 18),
            ("MAG-7", "mag-7", cat_map["shotgun"], "https://images.unsplash.com/photo-1584281722573-b3a6288b4461?w=600&auto=format&fit=crop&q=80", "Fast fire pump shotgun with mid-range spread control.", 89, 53, 15, 17, "active", 19),
            ("SPAS12", "spas12", cat_map["shotgun"], "https://images.unsplash.com/photo-1590483736422-421715e2060d?w=600&auto=format&fit=crop&q=80", "High damage shotgun with attachable magazine extensions.", 97, 42, 16, 10, "active", 20),

            # Snipers
            ("AWM", "awm", cat_map["sniper"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "The ultimate sniper rifle with instant knockdown potential.", 90, 27, 91, 90, "active", 21),
            ("KAR98K", "kar98k", cat_map["sniper"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "Standard sniper with biometric scope upgrade capability.", 90, 27, 84, 90, "active", 22),
            ("M82B", "m82b", cat_map["sniper"], "https://images.unsplash.com/photo-1584281722573-b3a6288b4461?w=600&auto=format&fit=crop&q=80", "Anti-materiel sniper piercing gloo walls and vehicles.", 90, 27, 85, 90, "active", 23),
            ("SVD", "svd", cat_map["sniper"], "https://images.unsplash.com/photo-1590483736422-421715e2060d?w=600&auto=format&fit=crop&q=80", "Semi-automatic designated marksman sniper rifle.", 89, 35, 80, 68, "active", 24),

            # Pistols
            ("DESERT EAGLE", "desert-eagle", cat_map["pistol"], "https://images.unsplash.com/photo-1585589000337-142278bb3f13?w=600&auto=format&fit=crop&q=80", "Clash Squad favorite for 1-tap headshot rounds.", 90, 33, 38, 45, "active", 25),
            ("G18", "g18", cat_map["pistol"], "https://images.unsplash.com/photo-1595590424283-b8f17842773f?w=600&auto=format&fit=crop&q=80", "Rapid burst automatic sidearm.", 45, 64, 8, 57, "active", 26),
            ("USP", "usp", cat_map["pistol"], "https://images.unsplash.com/photo-1584281722573-b3a6288b4461?w=600&auto=format&fit=crop&q=80", "Lightweight starter pistol with low recoil.", 45, 44, 16, 57, "active", 27),
            ("M500", "m500", cat_map["pistol"], "https://images.unsplash.com/photo-1590483736422-421715e2060d?w=600&auto=format&fit=crop&q=80", "Revolver with 2x scope capable of long range 1-taps.", 67, 43, 76, 10, "active", 28),
        ]
        cursor.executemany("""
        INSERT INTO guns (name, slug, category_id, image, description, damage, fire_rate, range_val, accuracy, status, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, guns)
        print("Seeded 28 Guns across all 5 categories")

    # 6. Brands
    cursor.execute("SELECT COUNT(*) FROM brands")
    if cursor.fetchone()[0] == 0:
        brand_list = [
            ("POCO", "poco", "fa-mobile-screen-button", 1),
            ("Xiaomi", "xiaomi", "fa-mobile", 2),
            ("Redmi", "redmi", "fa-mobile-screen", 3),
            ("Samsung", "samsung", "fa-tablet-screen-button", 4),
            ("Realme", "realme", "fa-mobile-screen-button", 5),
            ("OnePlus", "oneplus", "fa-plus", 6),
            ("iQOO", "iqoo", "fa-bolt-lightning", 7),
            ("Vivo", "vivo", "fa-mobile", 8),
            ("OPPO", "oppo", "fa-mobile-screen", 9),
            ("Motorola", "motorola", "fa-walkie-talkie", 10),
            ("Nothing", "nothing", "fa-circle-dot", 11),
            ("Infinix", "infinix", "fa-gamepad", 12),
            ("Tecno", "tecno", "fa-mobile", 13),
            ("Lava", "lava", "fa-fire", 14),
            ("ASUS", "asus", "fa-desktop", 15),
            ("Google Pixel", "google-pixel", "fa-camera", 16),
            ("Honor", "honor", "fa-shield", 17),
            ("Huawei", "huawei", "fa-network-wired", 18),
            ("Nokia", "nokia", "fa-mobile-button", 19),
            ("Lenovo", "lenovo", "fa-laptop", 20),
            ("ZTE", "zte", "fa-signal", 21),
            ("Apple", "apple", "fa-apple-whole", 22),
            ("Other", "other", "fa-sliders", 23),
        ]
        cursor.executemany("INSERT INTO brands (name, slug, logo, sort_order) VALUES (?, ?, ?, ?)", brand_list)
        print("Seeded 23 Device Brands")

    # Get brand map
    cursor.execute("SELECT id, name FROM brands")
    brand_map = {row["name"]: row["id"] for row in cursor.fetchall()}

    # 7. Devices & RAM Options
    cursor.execute("SELECT COUNT(*) FROM devices")
    if cursor.fetchone()[0] == 0:
        devices_data = [
            # POCO
            (brand_map["POCO"], "POCO M6 5G", "poco-m6-5g", "MediaTek Dimensity 6100+", "6.74\" HD+ 90Hz", "90Hz", "Android 14 (HyperOS)", ["4 GB", "6 GB", "8 GB"]),
            (brand_map["POCO"], "POCO X6 5G", "poco-x6-5g", "Snapdragon 7s Gen 2", "6.67\" 1.5K AMOLED 120Hz", "120Hz", "Android 14 (HyperOS)", ["8 GB", "12 GB"]),
            (brand_map["POCO"], "POCO X6 Pro 5G", "poco-x6-pro-5g", "MediaTek Dimensity 8300 Ultra", "6.67\" 1.5K Flow AMOLED 120Hz", "120Hz", "Android 14 (HyperOS)", ["8 GB", "12 GB"]),
            (brand_map["POCO"], "POCO X7", "poco-x7", "MediaTek Dimensity 7300 Ultra", "6.67\" AMOLED 120Hz", "120Hz", "Android 14 (HyperOS)", ["8 GB", "12 GB"]),
            (brand_map["POCO"], "POCO F5 5G", "poco-f5-5g", "Snapdragon 7+ Gen 2", "6.67\" FHD+ AMOLED 120Hz", "120Hz", "Android 14", ["8 GB", "12 GB"]),
            (brand_map["POCO"], "POCO C71", "poco-c71", "Unisoc T616 Octa-Core", "6.71\" HD+ 90Hz", "90Hz", "Android 14 Go", ["4 GB", "6 GB"]),

            # Xiaomi & Redmi
            (brand_map["Redmi"], "Redmi Note 13 Pro 5G", "redmi-note-13-pro-5g", "Snapdragon 7s Gen 2", "6.67\" 1.5K AMOLED 120Hz", "120Hz", "Android 14 (HyperOS)", ["8 GB", "12 GB"]),
            (brand_map["Redmi"], "Redmi 13C 5G", "redmi-13c-5g", "MediaTek Dimensity 6100+", "6.74\" HD+ 90Hz", "90Hz", "Android 14", ["4 GB", "6 GB", "8 GB"]),
            (brand_map["Xiaomi"], "Xiaomi 14", "xiaomi-14", "Snapdragon 8 Gen 3", "6.36\" LTPO OLED 120Hz", "120Hz", "Android 14 (HyperOS)", ["12 GB", "16 GB"]),

            # Samsung
            (brand_map["Samsung"], "Samsung Galaxy S23", "samsung-galaxy-s23", "Snapdragon 8 Gen 2 for Galaxy", "6.1\" Dynamic AMOLED 2X 120Hz", "120Hz", "Android 14 (One UI 6.1)", ["8 GB"]),
            (brand_map["Samsung"], "Samsung Galaxy A55 5G", "samsung-galaxy-a55-5g", "Exynos 1480", "6.6\" Super AMOLED 120Hz", "120Hz", "Android 14 (One UI 6.1)", ["8 GB", "12 GB"]),
            (brand_map["Samsung"], "Samsung Galaxy M34 5G", "samsung-galaxy-m34-5g", "Exynos 1280", "6.5\" Super AMOLED 120Hz", "120Hz", "Android 14", ["6 GB", "8 GB"]),

            # Realme
            (brand_map["Realme"], "Realme GT 6T", "realme-gt-6t", "Snapdragon 7+ Gen 3", "6.78\" 8T LTPO AMOLED 120Hz", "120Hz", "Android 14 (Realme UI 5.0)", ["8 GB", "12 GB"]),
            (brand_map["Realme"], "Realme 12 Pro+ 5G", "realme-12-pro-plus-5g", "Snapdragon 7s Gen 2", "6.7\" Curved AMOLED 120Hz", "120Hz", "Android 14", ["8 GB", "12 GB"]),

            # OnePlus
            (brand_map["OnePlus"], "OnePlus 12R", "oneplus-12r", "Snapdragon 8 Gen 2", "6.78\" ProXDR AMOLED 120Hz", "120Hz", "Android 14 (OxygenOS 14)", ["8 GB", "16 GB"]),
            (brand_map["OnePlus"], "OnePlus Nord CE 4", "oneplus-nord-ce-4", "Snapdragon 7 Gen 3", "6.7\" Fluid AMOLED 120Hz", "120Hz", "Android 14", ["8 GB"]),

            # iQOO
            (brand_map["iQOO"], "iQOO Neo 9 Pro", "iqoo-neo-9-pro", "Snapdragon 8 Gen 2", "6.78\" 144Hz LTPO AMOLED", "144Hz", "Android 14 (Funtouch OS 14)", ["8 GB", "12 GB"]),
            (brand_map["iQOO"], "iQOO Z9 5G", "iqoo-z9-5g", "MediaTek Dimensity 7200", "6.67\" AMOLED 120Hz", "120Hz", "Android 14", ["8 GB"]),

            # Vivo & OPPO
            (brand_map["Vivo"], "Vivo T3 5G", "vivo-t3-5g", "MediaTek Dimensity 7200", "6.67\" AMOLED 120Hz", "120Hz", "Android 14", ["8 GB"]),
            (brand_map["OPPO"], "OPPO Reno 11 Pro 5G", "oppo-reno-11-pro-5g", "MediaTek Dimensity 8200", "6.7\" 3D Curved OLED 120Hz", "120Hz", "Android 14 (ColorOS 14)", ["12 GB"]),

            # Motorola & Nothing
            (brand_map["Motorola"], "Motorola Edge 50 Fusion", "motorola-edge-50-fusion", "Snapdragon 7s Gen 2", "6.7\" pOLED 144Hz", "144Hz", "Android 14", ["8 GB", "12 GB"]),
            (brand_map["Nothing"], "Nothing Phone (2a)", "nothing-phone-2a", "MediaTek Dimensity 7200 Pro", "6.7\" Flexible AMOLED 120Hz", "120Hz", "Nothing OS 2.5", ["8 GB", "12 GB"]),

            # Infinix & Tecno
            (brand_map["Infinix"], "Infinix GT 20 Pro", "infinix-gt-20-pro", "MediaTek Dimensity 8200 Ultimate", "6.78\" FHD+ AMOLED 144Hz", "144Hz", "Android 14 (XOS 14)", ["8 GB", "12 GB"]),
            (brand_map["Tecno"], "Tecno Pova 6 Pro 5G", "tecno-pova-6-pro-5g", "MediaTek Dimensity 6080", "6.78\" AMOLED 120Hz", "120Hz", "Android 14 (HiOS 14)", ["8 GB", "12 GB"]),

            # Apple
            (brand_map["Apple"], "iPhone 15 Pro Max", "iphone-15-pro-max", "A17 Pro Bionic", "6.7\" Super Retina XDR OLED 120Hz", "120Hz", "iOS 18", ["8 GB"]),
            (brand_map["Apple"], "iPhone 13", "iphone-13", "A15 Bionic", "6.1\" Super Retina XDR OLED 60Hz", "60Hz", "iOS 18", ["4 GB"]),
        ]

        for b_id, model, slug, proc, disp, refr, os_sys, rams in devices_data:
            cursor.execute("""
            INSERT INTO devices (brand_id, model_name, slug, processor, display, refresh_rate, operating_system, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
            """, (b_id, model, slug, proc, disp, refr, os_sys))
            dev_id = cursor.lastrowid
            for r in rams:
                cursor.execute("INSERT INTO ram_options (device_id, ram) VALUES (?, ?)", (dev_id, r))
        print("Seeded Devices & RAM options")

    # 8. Real Tuned ZERO RECOIL Sensitivities
    cursor.execute("SELECT COUNT(*) FROM sensitivities")
    if cursor.fetchone()[0] == 0:
        # Get gun IDs
        cursor.execute("SELECT id, name FROM guns")
        gun_map = {row["name"]: row["id"] for row in cursor.fetchall()}

        # Get device IDs
        cursor.execute("SELECT id, model_name FROM devices")
        dev_map = {row["model_name"]: row["id"] for row in cursor.fetchall()}

        # Realistic, verified esports sensitivities curated by ARMUGA and CATZX
        sens_records = [
            # POCO M6 5G - MP40 (Primary prompt example!)
            (gun_map["MP40"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 98, 96, 92, 88, 72, 80, "Default", 46, 440, "Smooth (High FPS)", "High", "Quick Weapon Switch: ON, Left Fire: Always", "ARMUGA"),
            (gun_map["MP40"], dev_map["POCO M6 5G"], "4 GB", "MediaTek Dimensity 6100+", 100, 98, 95, 90, 75, 85, "Default", 48, 420, "Smooth (Normal)", "High", "Quick Reload: ON", "CATZX"),
            (gun_map["MP40"], dev_map["POCO M6 5G"], "8 GB", "MediaTek Dimensity 6100+", 96, 94, 90, 85, 70, 78, "Default", 44, 460, "Standard (High FPS)", "High", "Quick Weapon Switch: ON", "ARMUGA"),

            # POCO M6 5G - M1887 (Shotgun)
            (gun_map["M1887"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 100, 99, 90, 85, 68, 75, "Default", 42, 450, "Smooth (High FPS)", "High", "Quick Weapon Switch: ON", "CATZX"),
            (gun_map["M1887"], dev_map["POCO M6 5G"], "4 GB", "MediaTek Dimensity 6100+", 100, 100, 92, 88, 70, 80, "Default", 44, 430, "Smooth (Normal)", "High", "One-Tap Drag Master", "ARMUGA"),

            # POCO M6 5G - SCAR / AK47 / UMP
            (gun_map["SCAR"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 94, 92, 88, 82, 65, 72, "Default", 48, 430, "Smooth (High FPS)", "High", "Fire Button: 48%", "ARMUGA"),
            (gun_map["AK47"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 91, 88, 84, 79, 60, 70, "Precise on Scope", 50, 420, "Smooth (High FPS)", "High", "Control recoil burst: 3-5 bullets", "CATZX"),
            (gun_map["UMP"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 97, 95, 91, 86, 70, 80, "Default", 45, 445, "Smooth (High FPS)", "High", "Drag straight upwards from waist level", "ARMUGA"),
            (gun_map["AWM"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 88, 85, 80, 75, 55, 65, "Default", 52, 411, "Smooth (High FPS)", "High", "Hold fire to scope: ON", "CATZX"),
            (gun_map["DESERT EAGLE"], dev_map["POCO M6 5G"], "6 GB", "MediaTek Dimensity 6100+", 100, 99, 94, 88, 65, 78, "Default", 40, 460, "Smooth (High FPS)", "High", "J-Drag technique recommended", "ARMUGA"),

            # POCO X6 5G & POCO X6 Pro 5G
            (gun_map["MP40"], dev_map["POCO X6 Pro 5G"], "12 GB", "MediaTek Dimensity 8300 Ultra", 92, 89, 85, 80, 65, 75, "Default", 45, 480, "Ultra (High FPS)", "High", "120Hz touch sampling rate optimized", "ARMUGA"),
            (gun_map["MP40"], dev_map["POCO X6 Pro 5G"], "8 GB", "MediaTek Dimensity 8300 Ultra", 94, 91, 87, 82, 68, 77, "Default", 46, 470, "Ultra (High FPS)", "High", "Aggressive drag response", "CATZX"),
            (gun_map["M1887"], dev_map["POCO X6 Pro 5G"], "12 GB", "MediaTek Dimensity 8300 Ultra", 97, 95, 88, 84, 62, 70, "Default", 42, 490, "Ultra (High FPS)", "High", "V-Drag one-tap tuned", "ARMUGA"),
            (gun_map["WOODPECKER"], dev_map["POCO X6 Pro 5G"], "12 GB", "MediaTek Dimensity 8300 Ultra", 90, 86, 82, 78, 60, 68, "Default", 48, 460, "Ultra (High FPS)", "High", "Single-tap headshot lock", "CATZX"),

            # Redmi Note 13 Pro 5G
            (gun_map["MP40"], dev_map["Redmi Note 13 Pro 5G"], "8 GB", "Snapdragon 7s Gen 2", 95, 93, 89, 84, 69, 78, "Default", 46, 450, "Ultra (High FPS)", "High", "Optimized for curved screen drag", "ARMUGA"),
            (gun_map["UMP"], dev_map["Redmi Note 13 Pro 5G"], "8 GB", "Snapdragon 7s Gen 2", 96, 94, 90, 85, 71, 79, "Default", 45, 450, "Ultra (High FPS)", "High", "High drag speed multiplier", "CATZX"),
            (gun_map["M1887"], dev_map["Redmi Note 13 Pro 5G"], "8 GB", "Snapdragon 7s Gen 2", 99, 97, 91, 87, 65, 74, "Default", 43, 460, "Ultra (High FPS)", "High", "Instant snap to enemy head", "ARMUGA"),

            # Samsung Galaxy S23
            (gun_map["MP40"], dev_map["Samsung Galaxy S23"], "8 GB", "Snapdragon 8 Gen 2 for Galaxy", 89, 86, 82, 77, 60, 70, "Default", 44, 490, "Ultra (High FPS)", "High", "Dynamic AMOLED fast response", "ARMUGA"),
            (gun_map["M1014"], dev_map["Samsung Galaxy S23"], "8 GB", "Snapdragon 8 Gen 2 for Galaxy", 92, 88, 80, 75, 58, 68, "Default", 46, 480, "Ultra (High FPS)", "High", "Fast continuous tap", "CATZX"),
            (gun_map["M4A1"], dev_map["Samsung Galaxy S23"], "8 GB", "Snapdragon 8 Gen 2 for Galaxy", 90, 87, 83, 78, 62, 72, "Default", 47, 475, "Ultra (High FPS)", "High", "Zero Recoil Long Range Spray", "ARMUGA"),

            # OnePlus 12R
            (gun_map["MP40"], dev_map["OnePlus 12R"], "16 GB", "Snapdragon 8 Gen 2", 90, 87, 83, 79, 62, 72, "Default", 43, 500, "Ultra (High FPS)", "High", "ProXDR Hyper-touch tuned", "CATZX"),
            (gun_map["M1887"], dev_map["OnePlus 12R"], "16 GB", "Snapdragon 8 Gen 2", 96, 94, 88, 82, 60, 70, "Default", 42, 510, "Ultra (High FPS)", "High", "Instant one-tap snap", "ARMUGA"),

            # iQOO Neo 9 Pro
            (gun_map["MP40"], dev_map["iQOO Neo 9 Pro"], "12 GB", "Snapdragon 8 Gen 2", 91, 88, 84, 80, 63, 73, "Default", 44, 495, "Ultra (High FPS)", "High", "144Hz Esports Display Mode", "ARMUGA"),
            (gun_map["AK47"], dev_map["iQOO Neo 9 Pro"], "12 GB", "Snapdragon 8 Gen 2", 88, 85, 80, 76, 58, 68, "Default", 48, 480, "Ultra (High FPS)", "High", "Compensates for AK vertical kick", "CATZX"),

            # iPhone 15 Pro Max
            (gun_map["MP40"], dev_map["iPhone 15 Pro Max"], "8 GB", "A17 Pro Bionic", 86, 83, 79, 74, 58, 68, "Default", 42, 0, "Max Graphics (High FPS)", "High", "iOS Touch Haptic Sensitivity 100", "ARMUGA"),
            (gun_map["M1887"], dev_map["iPhone 15 Pro Max"], "8 GB", "A17 Pro Bionic", 92, 89, 84, 78, 55, 65, "Default", 40, 0, "Max Graphics (High FPS)", "High", "iOS Micro-Swipe Drag", "CATZX"),
        ]

        for gid, did, ram, proc, gen, rd, s2, s4, snp, fl, ap, fbs, dpi, gfx, fps, ctrl, admin_name in sens_records:
            cursor.execute("""
            INSERT INTO sensitivities (gun_id, device_id, ram, processor, general, red_dot, scope_2x, scope_4x, sniper, free_look, aim_precision, fire_button_size, dpi, graphics, fps, control_settings, updated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (gid, did, ram, proc, gen, rd, s2, s4, snp, fl, ap, fbs, dpi, gfx, fps, ctrl, admin_name))
        print(f"Seeded {len(sens_records)} Sensitivity Profiles")

    # 9. Announcements & Updates
    cursor.execute("SELECT COUNT(*) FROM updates")
    if cursor.fetchone()[0] == 0:
        updates_data = [
            ("OB46 PATCH ZERO RECOIL SENSITIVITY UPDATE", "ob46-patch-zero-recoil-update",
             "We have completely re-tested and fine-tuned Free Fire headshot sensitivities for the latest OB46 update! All POCO, Redmi, Samsung, and OnePlus models have been re-calibrated for maximum drag accuracy.",
             "https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&auto=format&fit=crop&q=80",
             "ARMUGA", 1),
            ("NEW ZERO RECOIL PROFILES FOR POCO M6 & X6 SERIES", "poco-m6-x6-recoil-update",
             "Full sensitivity optimization completed for POCO M6 5G (Dimensity 6100+) and POCO X6 Pro 5G (Dimensity 8300 Ultra). Test MP40, M1887, and UMP with custom DPI configurations.",
             "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=800&auto=format&fit=crop&q=80",
             "CATZX", 1),
            ("ESPORTS TOURNAMENT HEADSHOT SENSITIVITY GUIDE", "esports-tournament-headshot-guide",
             "Learn how ARMUGA and CATZX calibrate fire button size and DPI multipliers to achieve consistent red numbers in high-pressure competitive custom rooms.",
             "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=800&auto=format&fit=crop&q=80",
             "ARMUGA X CATZX", 1)
        ]
        for title, slug, desc, img, author, pub in updates_data:
            cursor.execute("""
            INSERT INTO updates (title, slug, description, image, admin_name, published)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (title, slug, desc, img, author, pub))
        print("Seeded Updates")

    # 10. Sample Device Requests
    cursor.execute("SELECT COUNT(*) FROM device_requests")
    if cursor.fetchone()[0] == 0:
        sample_requests = [
            (None, "gamer.vikram@gmail.com", "Infinix", "Infinix Note 40 Pro", "8 GB", "Dimensity 7020", "Please add MP40 and M1887 settings for Note 40 Pro!", "Pending"),
            (None, "rahulff99@gmail.com", "Lava", "Lava Agni 2 5G", "8 GB", "Dimensity 7050", "Need UMP and Shotgun zero recoil setting for 120Hz display.", "In Progress")
        ]
        cursor.executemany("""
        INSERT INTO device_requests (user_id, user_email, brand, model, ram, processor, notes, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_requests)
        print("Seeded Sample Device Requests")

    # 11. Initial Admin Activity Logs
    cursor.execute("SELECT COUNT(*) FROM activity_logs")
    if cursor.fetchone()[0] == 0:
        logs = [
            ("ARMUGA", "Created Gun", "guns", 1, "Added initial gun roster (28 weapons across 5 categories)"),
            ("CATZX", "Calibrated Sensitivity", "sensitivities", 1, "Configured POCO M6 5G MP40 Zero Recoil profile (General 98, Red Dot 96)"),
            ("ARMUGA", "Published Update", "updates", 1, "Published OB46 Patch Zero Recoil Sensitivity Update"),
            ("CATZX", "Updated Live Stream", "live_stream", 1, "Set live stream status to ACTIVE with official channel URL")
        ]
        cursor.executemany("""
        INSERT INTO activity_logs (admin_name, action, target_type, target_id, details)
        VALUES (?, ?, ?, ?, ?)
        """, logs)

    conn.commit()
    conn.close()
    print("Database initialization and seeding completed successfully!")

if __name__ == "__main__":
    init_db()
    seed_db()
