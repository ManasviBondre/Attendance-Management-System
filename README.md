# Attendance Management System (AMS) — SEPM Mini-Project

A full-stack, production-quality Attendance Management System developed as a Software Engineering and Project Management (SEPM) college mini-project. The application digitizes student attendance management, eliminates paper registers, prevents proxy marking, calculates attendance percentages automatically, and provides early warnings for students with attendance shortages below 75%.

---

## 🌟 Key Features by User Role

### 🛡️ 1. Administrator Module
- **Dashboard Analytics:** Instant overview of total students (45), faculty (5), subjects (5), attendance sessions (100), system average attendance (80.4%), and attendance defaulters count (4).
- **User Lifecycle Management:** Register, view, edit, toggle active/inactive status, or delete users across Admin, Faculty, and Student roles.
- **Subject Management:** Full curriculum management for all 5 core subjects with faculty assignment and student enrollment tracking.
- **System-Wide Attendance Logs:** Searchable audit trail of every lecture conducted across all departments.
- **Defaulter & Audit Reporting:** Instantly identify students below the 75% statutory threshold with one-click **CSV export** for official academic notices.

### 👨‍🏫 2. Faculty Module
- **Personalized Greeting:** Greeting addressed directly to the authenticated professor's name and department.
- **Assigned Course Roster:** Direct access to assigned subjects (`MDM`, `Theory of Computation`, `SEPM`, `PE - Image Processing`, `Machine Learning`).
- **Interactive Attendance Marker:**
  - Fast **"Mark All Present"** and **"Mark All Absent"** bulk toggles.
  - Live **interactive counter bar** displaying Present, Absent, and Percentage in real-time.
  - Instant live filter to find any student by Roll Number or Name.
- **Duplicate Entry Safeguard:** Automatically prevents recording multiple attendance sessions for the same subject on the same date and slot, offering a safe "Edit Session" pathway.
- **Attendance Rectification:** Ability to safely edit and update attendance records with SQLite ACID transactions.
- **Subject Analytics & Defaulter Identification:** Complete student-by-student attendance register with CSV export.

### 🎓 3. Student Module
- **Personalized Student Portal:** Student's full name, roll number, semester, section, and academic batch.
- **Cumulative Attendance Gauge:** Instant calculation of overall attendance percentage.
- **Statutory Shortage Warning Banner:** High-visibility alert banner displayed automatically if cumulative or subject attendance falls below **75.0%**.
- **Attendance Optimization Advice:** Dynamic calculation showing:
  - *"Attend next X consecutive classes to reach 75%"* (if in shortage).
  - *"You can afford to miss Y classes safely"* (if in good standing).
- **Subject-Wise Breakdown:** 5 individual subject cards showing classes held, attended, missed, and percentage progress bars.
- **Lecture-by-Lecture Audit Log:** Full searchable history with date, time slot, faculty, topic, and Present/Absent badges.
- **Strict Read-Only Access:** Role-enforced protection preventing students from modifying attendance records.

---

## 📚 Preconfigured Subjects

The application comes preconfigured with the 5 core 6th-semester CSE subjects:
1. `CS601` — **MDM**
2. `CS602` — **Theory of Computation**
3. `CS603` — **Software Engineering and Project Management (SEPM)**
4. `CS604` — **PE - Image Processing**
5. `CS605` — **Machine Learning**

---

## 🔑 Test Accounts & Evaluation Credentials

The application includes a pre-seeded, deterministic database containing **45 students**, **5 faculty members**, and **1 administrator**. You can log into any account using the credentials below:

| Role | Username | Email | Password | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@ams.edu` | `Admin@123` | Full administrative control & reporting |
| **Faculty (SEPM)** | `prof.iyer` | `ananya.iyer@ams.edu` | `Password@123` | Prof. Ananya Iyer — Teaches SEPM |
| **Faculty (TOC)** | `dr.sharma` | `rajesh.sharma@ams.edu` | `Password@123` | Dr. Rajesh Sharma — Professor & HOD |
| **Faculty (ML)** | `dr.malhotra` | `vikram.malhotra@ams.edu` | `Password@123` | Dr. Vikram Malhotra — Teaches Machine Learning |
| **Faculty (Image Proc)** | `prof.patel` | `sneha.patel@ams.edu` | `Password@123` | Prof. Sneha Patel — Teaches Image Processing |
| **Faculty (MDM)** | `prof.verma` | `arvind.verma@ams.edu` | `Password@123` | Dr. Arvind Verma — Teaches MDM |
| **Student (High %)** | `22cs001` | `22cs001@student.ams.edu` | `Password@123` | Aarav Sharma — **95.0% Attendance (Eligible)** |
| **Student (Safe %)** | `22cs002` | `22cs002@student.ams.edu` | `Password@123` | Aditi Rao — **80.0% Attendance (Eligible)** |
| **Student (Defaulter %)**| `22cs003` | `22cs003@student.ams.edu` | `Password@123` | Rohan Gupta — **60.0% Attendance (Defaulter Alert)** |
| **Student (Defaulter %)**| `22cs004` | `22cs004@student.ams.edu` | `Password@123` | Priya Nair — **55.0% Attendance (Defaulter Alert)** |

> **Note on Student Usernames:** All 45 students can log in using their lower-case roll numbers (e.g. `22cs001` to `22cs045`) with password `Password@123`.

---

## 🔒 Administrator Registration Security Key

To ensure visitor access control, creating an Administrator account via the public registration page requires the master security key:
- **Admin Registration Security Key:** `ADMIN@SEPM2026`
*(Can also be customized via the `ADMIN_REGISTRATION_KEY` environment variable in `config.py`).*

Students and Faculty members can register freely with their respective academic IDs without requiring an admin key.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Google Chrome, Mozilla Firefox, or Microsoft Edge

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the Web Portal
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
The database (`attendance_system.db`) initializes and seeds automatically upon first run.

---

## 📑 SEPM Project Report & Viva Voce Guide

A comprehensive, formal SEPM project report is included:
- **In-App View:** Click **"SEPM Report & Viva Guide"** in the top navigation bar of the web app (`/sepm-docs`), or click **"Print / Save as PDF"** for examination submission.
- **Markdown Document:** [SEPM_PROJECT_REPORT.md](SEPM_PROJECT_REPORT.md) in the project root directory.

Topics covered in the report:
1. Problem Statement & Existing Manual System Analysis
2. Iterative Agile SDLC Methodology & Sprint Decomposition
3. IEEE 830 Software Requirement Specification (SRS)
4. System Architecture & 3-Tier Layered MVC Pattern
5. Use Case Diagrams & Data Flow Diagrams (DFD Level 0 & Level 1)
6. Database Design, 3NF Normalization & Entity-Relationship Diagram (ERD)
7. Software Testing Matrix & Verification Results
8. COCOMO Cost Estimation & Risk Management (RMMM Plan)
9. Viva Voce Questions & Answers Guide with examination answers

---

## 📁 Project Directory Structure

```
AMS -Project/
│
├── app.py                      # Main Flask application & route controllers
├── config.py                   # App configuration & threshold settings
├── database.py                 # SQLite schema, connection manager & seed data
├── models.py                   # Business logic, calculations & database models
├── requirements.txt            # Python dependencies (Flask, Werkzeug)
├── README.md                   # Setup guide & test credentials
├── SEPM_PROJECT_REPORT.md      # Full formal SEPM academic project report
├── attendance_system.db        # SQLite database (auto-generated & seeded)
│
├── static/
│   ├── css/
│   │   └── style.css           # Custom academic UI styling & print rules
│   └── js/
│       └── main.js             # Live counters, show/hide password, instant search
│
└── templates/
    ├── base.html               # Base layout with role-aware navbar & footer
    ├── auth/
    │   ├── login.html          # Clean login page with password toggle & credentials
    │   └── register.html       # Role-specific registration with admin security key
    ├── admin/
    │   ├── dashboard.html      # Admin stats, subject status & defaulter alert preview
    │   ├── users.html          # User CRUD directory with role filter & search
    │   ├── user_form.html      # Create / edit user profiles
    │   ├── subjects.html       # Manage subjects & faculty assignments
    │   ├── subject_form.html   # Create / edit subject details
    │   ├── attendance_logs.html# Global attendance session audit log
    │   └── reports.html        # Official defaulter registers & CSV export
    ├── faculty/
    │   ├── dashboard.html      # Personalized faculty portal & assigned classes
    │   ├── mark_attendance.html# Interactive marker, live counters & fast toggles
    │   ├── edit_attendance.html# Safe attendance session updating
    │   ├── session_view.html   # Detailed single session student roster
    │   ├── session_history.html# Past lecture history table
    │   └── subject_stats.html  # Subject-wise percentage & defaulter highlights
    ├── student/
    │   ├── dashboard.html      # Student overview, 75% shortage alert & advice
    │   └── history.html        # Filterable lecture-by-lecture audit history
    ├── common/
    │   ├── profile.html        # User account & academic credentials
    │   └── sepm_docs.html      # Interactive in-app SEPM report & viva guide
    └── errors/
        ├── 403.html            # Forbidden / Access Denied
        ├── 404.html            # Page Not Found
        └── 500.html            # Internal Server Error
```
