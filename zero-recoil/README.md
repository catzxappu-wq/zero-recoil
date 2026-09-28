# ZERO RECOIL — ARMUGA X CATZX
### Professional Free Fire Sensitivity Finder Platform

> **MASTER YOUR AIM. CONTROL YOUR RECOIL.**  
> **FIND YOUR PERFECT FREE FIRE SENSITIVITY**

---

## 🎯 Platform Overview

**ZERO RECOIL** is a production-ready, full-stack esports sensitivity finder platform designed for Free Fire players. Engineered with a **premium RED × BLACK esports theme**, this platform provides calibrated, non-fabricated sensitivity benchmarks based on:

$$\text{Gun} \longrightarrow \text{Device Brand} \longrightarrow \text{Device Model} \longrightarrow \text{RAM} \longrightarrow \text{Processor} \longrightarrow \text{Zero Recoil Settings}$$

---

## ⚡ Key Features

1. **6-Step Interactive Sensitivity Wizard**:
   - Step 1: Select Weapon (Assault Rifles, SMG, Shotguns, Snipers, Pistols)
   - Step 2: Select Device Brand (POCO, Xiaomi, Redmi, Samsung, Realme, OnePlus, iQOO, Apple, etc.)
   - Step 3: Select Device Model (POCO M6 5G, POCO X6 Pro, Samsung S23, etc.)
   - Step 4: Select Hardware RAM (4 GB, 6 GB, 8 GB, 12 GB, 16 GB)
   - Step 5: Confirm Processor (Dimensity, Snapdragon, Bionic)
   - Step 6: Social Media Unlock (Instagram 01, Instagram 02, YouTube subscribe)
   - Step 7: Zero Recoil Sensitivity Matrix (General, Red Dot, 2X Scope, 4X Scope, Sniper Scope, Free Look, Fire Button Size %, DPI, Aim Precision, Graphics, High FPS).
2. **Missing Device Request Flow**:
   - If an exact configuration is not yet benchmarked, the system prevents fake random numbers and presents a formal **"Request This Device"** modal.
3. **Copy / Save / Share Actions**:
   - **Copy Settings**: Formats and copies all HUD and sensitivity numbers into your clipboard.
   - **Save**: Saves configuration directly to the player's account.
   - **Share**: Creates shareable URLs with weapon and device preview.
4. **Live Stream System**:
   - Real-time `🔴 ARMUGA X CATZX IS LIVE` banner on the homepage controlled directly from the admin panel with YouTube Live stream embedding and URL management.
5. **Customer Portal**:
   - Player registration and authentication.
   - Profile management and password updates.
   - Saved sensitivity vault with 1-click clipboard copy.
   - Real-time notification center and device request tracking.
6. **Dual Administrator System**:
   - Dedicated access for both **ARMUGA** and **CATZX**.
   - Admin audit log tracking every action with timestamps ("Updated by ARMUGA" or "Updated by CATZX").
   - Full CRUD for Guns, Brands, Device Models, and Sensitivity Profiles.
   - Bulk CSV Import & Export for handling hundreds of sensitivity profiles.
   - Social link channel configuration without modifying codebase.

---

## 🛡️ Default Administrator Accounts

| Administrator | Email Address | Password | Role |
| :--- | :--- | :--- | :--- |
| **ARMUGA** | `armuga@zerorecoil.gg` | `armuga1234` | Lead Tester & Admin |
| **CATZX** | `catzx@zerorecoil.gg` | `catzx1234` | Analyst & Admin |

---

## 🎨 Design Theme & Esports Aesthetics

- **Background**: `#050505` (Deep OLED Gaming Black)
- **Secondary Background**: `#0B0B0B`
- **Dark Red**: `#5A0000`
- **Crimson**: `#B00000`
- **Bright Red**: `#FF1A1A`
- **Text & Highlights**: `#FFFFFF` & `#A8A8A8`
- **Typography**: `Orbitron` (headings), `Rajdhani` (esports tags), `Inter` (body)
- **Responsive Layout**: Mobile-first with touch-friendly cards and a dedicated bottom mobile navigation dock.

---

## 🚀 Running the Application

### 1. Requirements
- Python 3.10+ (Tested and verified on Python 3.15)
- SQLite3 (Included with standard Python)
- Flask 3.0+

### 2. Quick Start Command
```powershell
python app.py
```

Open your browser at:
```
http://127.0.0.1:5000
```

### 3. Run Automated Tests
```powershell
python test_app.py
```
*(Runs comprehensive unit and integration tests across database seeding, public endpoints, customer authentication, admin dashboard, CSV tools, and API lookup).*

---

## 📁 Project Structure

```
zero-recoil/
├── app.py                     # Main Flask routing, controllers, APIs, and business logic
├── auth.py                    # Session decorators, role guards, activity logging
├── database.py                # SQLite schema creation & comprehensive seed data
├── test_app.py                # Automated end-to-end test suite
├── requirements.txt           # Python package requirements
├── zero_recoil.db             # Relational SQLite database
├── static/
│   ├── css/
│   │   └── custom.css         # Custom esports styles, neon red glow, glass cards
│   └── js/
│       └── main.js            # Toast notifications, search autocomplete, clipboard copy
└── templates/
    ├── base.html              # Base layout with header, live banner & mobile bottom nav
    ├── index.html             # Hero section, feature cards, guns & devices preview
    ├── sensitivity.html       # 6-step interactive sensitivity wizard & social unlock
    ├── guns.html              # Guns database with category filters & stat bars
    ├── gun_detail.html        # Individual gun page with calibrated device profiles
    ├── devices.html           # All devices database with brand filters & search
    ├── device_detail.html     # Dedicated device page showing hardware specs & guns
    ├── updates.html           # Patch notes & announcements with red NEW badges
    ├── about.html             # Brand story of ARMUGA X CATZX & testing methodology
    ├── contact.html           # Player inquiry and support form
    ├── login.html             # Customer player login
    ├── register.html          # Customer registration
    ├── forgot_password.html   # Password reset
    ├── dashboard.html         # Customer dashboard (saved sensitivities, request tracker)
    ├── saved.html             # Saved sensitivities vault
    ├── profile.html           # Customer profile settings
    ├── notifications.html     # Customer notification center
    └── admin/
        ├── base.html          # Admin sidebar layout & session header
        ├── login.html         # ARMUGA & CATZX admin login
        ├── dashboard.html     # Admin dashboard with 7 metrics & activity audit log
        ├── guns.html          # Gun management (add, edit, delete, toggle)
        ├── devices.html       # Device & brand management
        ├── sensitivities.html # Sensitivity profile CRUD, search, filter & duplicate
        ├── bulk_csv.html      # Bulk CSV import & export engine
        ├── users.html         # Player account manager
        ├── updates.html       # News & update publisher
        ├── social_links.html  # Instagram 1, 2 & YouTube unlock channel controls
        ├── live.html          # Live stream status controller
        ├── requests.html      # Missing device requests manager
        └── settings.html      # Admin profile & credentials
```

---

## 🏆 Verified Example (From Prompt)

When searching for:
$$\textbf{Gun: MP40} \longrightarrow \textbf{Brand: POCO} \longrightarrow \textbf{Model: POCO M6 5G} \longrightarrow \textbf{RAM: 6 GB} \longrightarrow \textbf{Processor: MediaTek Dimensity 6100+}$$

The platform retrieves the exact competitive profile calibrated by **ARMUGA**:
- **General**: `98`
- **Red Dot**: `96`
- **2X Scope**: `92`
- **4X Scope**: `88`
- **Sniper Scope**: `72`
- **Free Look**: `80`
- **Fire Button Size**: `46%`
- **DPI**: `440`
- **Aim Precision**: `Default`
- **Graphics**: `Smooth (High FPS)`
- **Pro Drag Tip**: *"Quick Weapon Switch: ON, Left Fire: Always, Drag straight upwards from waist level."*
