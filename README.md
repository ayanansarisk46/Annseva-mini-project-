# AnnSeva – Food Donation and Management System

> **TY Computer Science Mini Project**  
> A full-stack web application bridging the gap between food donors (hotels, caterers, banquet halls, restaurants) and verified local NGOs to eliminate food wastage and eradicate hunger.

---

## 1. Project Introduction & Problem Statement

### The Problem
Every single day, thousands of kilograms of edible, freshly prepared surplus food from wedding receptions, hotels, corporate seminars, restaurants, and catering events end up dumped in municipal landfills. Simultaneously, thousands of under-privileged citizens, orphans, and shelter residents in nearby urban localities suffer from nutritional insecurity and hunger.

Traditional attempts to donate excess food fail because:
- Donors do not have direct contacts of active local NGOs.
- Finding NGOs via random phone calls takes too long; hot cooked food spoils within 4 to 6 hours.
- Donors and NGOs do not know raw GPS coordinates (latitude/longitude), needing clean city and area addresses instead.
- Lack of centralized real-time tracking, resulting in logistical chaos and food waste.

### The AnnSeva Solution
**AnnSeva** is a web-based food donation and management platform engineered using Python Flask, MySQL, Chart.js, and Google Maps. Donors can list surplus meals in seconds using their natural address/locality. An automated proximity-matching algorithm immediately pairs the donation with the nearest registered NGO, alerts the NGO team, tracks collection across distinct lifecycle stages, and generates **live auto-refreshing transparency reports** with real-time Chart.js visualizations.

---

## 2. Key Objectives

1. **Reduce Landfill Waste:** Divert wholesome leftover meals from trash bins into human consumption.
2. **Locality-Based Proximity Matching:** Connect donors with the nearest suitable NGO using locality and city keywords without requiring GPS numbers.
3. **Role-Based Access Control:** Distinct, protected dashboards for **DONOR** and **NGO** roles.
4. **Lifecycle Tracking:** Monitor donation workflow from `PENDING` &rarr; `ACCEPTED` &rarr; `PICKED UP` &rarr; `COMPLETED` (or `REJECTED`).
5. **Live Real-Time Transparency:** Live auto-updating Chart.js visualizations (polling every 4 seconds) showing total food rescued, meals served, and a real-time activity stream.
6. **In-App & Email Notifications:** Automated alerts dispatched at every milestone of the collection journey with live badge counter updates.

---

## 3. Technology Stack

| Layer | Technologies Used | Description |
|---|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (ES6) | Clean, responsive interface with live auto-refresh polling and animated status indicators. |
| **Backend** | Python 3, Flask | Lightweight, fast web framework configured for live network hosting (`0.0.0.0:5000`). |
| **Authentication** | Flask-Login, Werkzeug | Session-based login with PBKDF2:SHA256 password hashing. |
| **Database** | MySQL (with SQLite Auto-Fallback) | Clean schema without GPS coordinate dependencies. Works with MySQL / MariaDB (XAMPP) and SQLite. |
| **ORM** | Flask-SQLAlchemy | Object-Relational Mapping for safe, parameterised queries (no SQL injection). |
| **Data Analytics** | Chart.js | Real-time live auto-refreshing charts for transparency reporting. |
| **Mapping Engine** | Google Maps JavaScript API + Leaflet.js | Dual-mode map rendering with automatic address geocoding. |
| **Notification** | In-App Alerts + SMTP Email Structure | Real-time notifications stored in DB with live polling counter updates. |

---

## 4. Main Project Workflow

```
[ FOOD DONOR ]
      │
      ▼
 1. Sign In / Register (Name, Email, Password, Address/Locality)
      │
      ▼
 2. Add Food Donation (Food Type, Quantity, Pickup Locality, Date, Time Window)
      │
      ▼
 3. Database Stores Record with Status: 'PENDING'
      │
      ▼
 4. PYTHON LOCALITY MATCHING ENGINE (services/matching.py)
    • Matches donor's pickup address with local NGO operating centers
    • Scores exact area matches (e.g. Andheri to Andheri, Bandra to Bandra)
    • Assigns the best matching NGO to the donation record
      │
      ▼
 5. Dispatches In-App & Email Alert to Selected NGO
      │
      ▼
[ COMMUNITY NGO ]
      │
      ▼
 6. NGO Reviews Request on Dashboard
      │
      ├─── [ REJECT ] ──► Status updated to 'REJECTED' ──► Donor notified
      │
      └─── [ ACCEPT ] ──► Status updated to 'ACCEPTED' ──► Donor notified with NGO contact
                                │
                                ▼
 7. NGO Volunteer Arrives at Donor Location
                                │
                                ▼
 8. NGO Clicks [ 🚚 MARK PICKED UP ] ──► Status: 'PICKED UP' ──► Donor notified
                                │
                                ▼
 9. Food Transported & Distributed to Local Beneficiaries / Shelters
                                │
                                ▼
10. NGO Clicks [ ✅ MARK COMPLETE ] ──► Status: 'COMPLETED'
                                │
                                ▼
11. Donor Notified & Transparency Reports Automatically Recalculate
    (Total Food Saved in kg & Meals Provided increased in real-time)
```

---

## 5. Database Architecture & Schema

The schema is defined in `database.sql` and implemented via SQLAlchemy in `models.py`.

### A. `users` Table
Stores authentication and profile information for both Donors and NGOs.
- `id` (INT, Primary Key, AUTO_INCREMENT)
- `name` (VARCHAR(100), NOT NULL)
- `email` (VARCHAR(120), UNIQUE, NOT NULL, INDEXED)
- `password` (VARCHAR(255), NOT NULL, Hashed)
- `role` (ENUM('DONOR', 'NGO'), NOT NULL)
- `phone` (VARCHAR(20), NULL)
- `location` (VARCHAR(255), NOT NULL)
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

### B. `donations` Table
Tracks food requests and status transitions.
- `id` (INT, Primary Key, AUTO_INCREMENT)
- `donor_id` (INT, Foreign Key &rarr; `users.id` ON DELETE CASCADE)
- `ngo_id` (INT, Foreign Key &rarr; `users.id` ON DELETE SET NULL)
- `food_type` (VARCHAR(100), NOT NULL)
- `quantity` (FLOAT, NOT NULL)
- `unit` (VARCHAR(20), DEFAULT 'kg')
- `location` (VARCHAR(255), NOT NULL)
- `pickup_date` (DATE, NOT NULL)
- `pickup_time` (VARCHAR(30), NOT NULL)
- `description` (TEXT, NULL)
- `status` (ENUM('PENDING', 'ACCEPTED', 'PICKED UP', 'COMPLETED', 'REJECTED'), DEFAULT 'PENDING')
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)
- `completed_at` (DATETIME, NULL)

### C. `notifications` Table
Stores alert messages for users.
- `id` (INT, Primary Key, AUTO_INCREMENT)
- `user_id` (INT, Foreign Key &rarr; `users.id` ON DELETE CASCADE)
- `message` (VARCHAR(500), NOT NULL)
- `is_read` (BOOLEAN, DEFAULT FALSE)
- `created_at` (DATETIME, DEFAULT CURRENT_TIMESTAMP)

---

## 6. Pre-configured Demo Credentials

For your college viva and viva demonstrations, the database comes pre-seeded with sample Donors, NGOs, and donations.

> **Tip for Viva:** On the `/login` page, you can click any of the **Quick Demo Login buttons** to auto-fill these credentials in 1 click!

| User Role | Name | Email | Password | Locality |
|---|---|---|---|---|
| **ADMIN** | AnnSeva Administrator | `admin@annseva.org` | `admin123` | Headquarters, Mumbai |
| **DONOR** | Green Valley Hotel | `donor1@hotel.com` | `password123` | Andheri West, Mumbai |
| **DONOR** | Royal Caterers & Banquet | `donor2@caterer.com` | `password123` | BKC, Mumbai |
| **NGO** | Roti Bank Foundation | `ngo1@rotibank.org` | `password123` | Andheri East, Mumbai |
| **NGO** | FeedTheNeedy Trust | `ngo2@feedthechildren.org` | `password123` | Kurla West, Mumbai |

---

## 7. Installation & Setup Guide

### Step 1: Open Terminal in Project Directory
```bash
cd "c:\Users\SHARIK\OneDrive\Desktop\AI Project"
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Live Server
```bash
python app.py
```
The server will start live on:
- Local Machine: `http://127.0.0.1:5000`
- Network Interface: `http://0.0.0.0:5000`

---

## 8. Admin Control Center & Platform Management

The Admin Control Panel provides centralized superuser management over AnnSeva operations:

### Accessing the Admin Panel:
1. Click **`👑 Admin Panel`** in the top navigation bar, on the homepage, or on the reports page.
2. You can also sign in manually with Admin credentials (`admin@annseva.org` / `admin123`) or click the **👑 Admin (System Control)** quick pill on the login page.
3. You will be directed to `/admin/dashboard` (Control Center).
4. **Master Features in Admin Panel**:
   - **📊 Operational KPIs**: Real-time totals for registered users, food donations, food saved (kg), and meals served.
   - **🔄 Status Lifecycle Pipeline**: Live pipeline breakdown across Pending, Accepted, Picked Up, Completed, and Rejected states.
   - **👥 User Management (`/admin/users`)**: Search, filter, inspect, and delete Donor and NGO accounts.
   - **🍲 Donations Audit (`/admin/donations`)**: Audit and manage food donation records across all 5 operational lifecycle states.

### Terminal Database Management:
```bash
# Reset database so report counters start at 0 (Zero-State Demo Mode):
python seed_data.py --zero

# Or re-seed with pre-filled sample donations:
python seed_data.py --reset
```

---

## 9. College Viva & Examination Q&A Guide

### Q1: Why are latitude and longitude not required from users?
**Answer:** In practical real-world scenarios, donors (hotel managers, caterers, households) and NGOs do not know their raw GPS coordinates (e.g. 19.1197, 72.8464). Requiring raw GPS coordinates complicates the user experience and leads to form input errors. AnnSeva accepts natural physical addresses (e.g. "Andheri West, Mumbai") and matches donors with NGOs based on locality tokens. For map visual display, our backend resolver translates addresses into map pins automatically.

### Q2: How does the matching algorithm work?
**Answer:** The matching engine is in `services/matching.py`:
1. It retrieves all active registered NGOs.
2. It extracts significant locality and city tokens from the donor's pickup address (ignoring stopwords like "road", "near", "opposite").
3. It compares these tokens against each NGO's operational address.
4. Higher weighted scores are given to specific urban localities (e.g. Andheri, Bandra, Kurla) followed by city-level matches.
5. The NGO with the highest matching locality score is automatically assigned, and notification alerts are dispatched.

### Q3: How do the Live Reports work?
**Answer:** On the `/reports` page, real-time polling fetches latest metrics from `/api/reports-data` every 4 seconds without reloading the page. It updates the KPI counters, recalculates the Chart.js doughnut and bar charts smoothly, and populates a **Live Recent Activity Stream** table showing the latest donation transactions.
