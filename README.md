# Attendance Management System (AMS)

A full-stack, production-quality Attendance Management System developed as a Software Engineering and Project Management (SEPM) college mini-project. The application digitizes student attendance management, eliminates paper registers, prevents proxy marking, calculates attendance percentages automatically, and provides early warnings for students with attendance shortages below the mandatory 75% university threshold.

---

## 🌟 Key Features by User Role

### 🛡️ 1. Administrator Module
- **Dashboard Analytics:** Instant overview of total students (47), faculty (6), subjects (5), attendance sessions, system-wide average attendance, and attendance defaulters count.
- **User Lifecycle Management:** Add, view, update, toggle active/inactive status, or delete users across Administrator, Faculty, and Student roles.
- **Subject Management:** Full curriculum management for all 5 core subjects with faculty assignment and student enrollment tracking.
- **System-Wide Attendance Logs:** Searchable audit trail of every lecture conducted across all departments.
- **Defaulter & Audit Reporting:** Instantly identify students below the 75% statutory threshold with one-click **CSV export** for official academic notices.

### 👨‍🏫 2. Faculty Module
- **Personalized Portal:** Greeting addressed directly to the authenticated professor's name and department.
- **Assigned Course Roster:** Direct access to assigned subjects (`MDM`, `Theory of Computation`, `SEPM`, `PE - Image Processing`, `Machine Learning`).
- **Student Roster View:** Dedicated student lists view showing all assigned students with roll numbers and contact details.
- **Interactive Attendance Marker:**
  - Fast **"Mark All Present"** and **"Mark All Absent"** bulk toggles.
  - Live **interactive counter bar** displaying Present, Absent, and Percentage in real-time.
  - Instant live filter to search any student by Roll Number or Name.
- **Duplicate Entry Safeguard:** Automatically prevents recording multiple attendance sessions for the same subject on the same date and slot, offering a safe "Edit Session" pathway.
- **Attendance Rectification:** Ability to safely edit and update attendance records with SQLite ACID transactions.
- **Subject Analytics & Defaulter Register:** Complete student-by-student attendance register with CSV export.

### 🎓 3. Student Module
- **Personalized Student Portal:** Student's full name, roll number, semester, section, and academic batch.
- **Cumulative Attendance Metric:** Instant calculation of overall attendance percentage.
- **Statutory Shortage Warning Banner:** High-visibility alert banner displayed automatically if cumulative or subject attendance falls below **75.0%**.
- **Attendance Optimization Advice:** Dynamic calculation showing:
  - *"Attend next X consecutive classes to reach 75%"* (if in shortage).
  - *"You can afford to miss Y classes safely"* (if in good standing).
- **Subject-Wise Breakdown:** 5 individual subject cards showing classes held, attended, missed, and percentage progress bars. Handles subjects with 0 conducted classes gracefully with an `N/A` badge.
- **Lecture-by-Lecture Audit Log:** Full searchable history with date, time slot, faculty, topic, and Present/Absent badges.
- **Strict Read-Only Access:** Role-enforced protection preventing students from modifying attendance records.

---

## 📚 Standardized Curriculum Subjects

The application is preconfigured with the 5 core 6th-semester CSE subjects:
1. `CS601` — **MDM**
2. `CS602` — **Theory of Computation**
3. `CS603` — **Software Engineering and Project Management (SEPM)**
4. `CS604` — **PE - Image Processing**
5. `CS605` — **Machine Learning**

---

## 🔑 Test Accounts & Evaluation Credentials

The application includes a pre-seeded, deterministic database containing realistic Indian student names, faculty members, and an administrator. You can log into any account using the credentials below:

| Role | Username | Email | Password | Details |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin@ams.edu` | `Admin@123` | Full administrative control & reporting |
| **Faculty (SEPM)** | `prof.iyer` | `ananya.iyer@ams.edu` | `Password@123` | Prof. Ananya Iyer — Teaches SEPM |
| **Faculty (TOC)** | `dr.sharma` | `rajesh.sharma@ams.edu` | `Password@123` | Dr. Rajesh Sharma — Professor & HOD |
| **Faculty (ML)** | `dr.malhotra` | `vikram.malhotra@ams.edu` | `Password@123` | Dr. Vikram Malhotra — Teaches Machine Learning |
| **Faculty (Image Proc)** | `prof.patel` | `sneha.patel@ams.edu` | `Password@123` | Prof. Sneha Patel — Teaches Image Processing |
| **Faculty (MDM)** | `prof.verma` | `arvind.verma@ams.edu` | `Password@123` | Dr. Arvind Verma — Teaches MDM |
| **Faculty (SEPM)** | `FAC006` | `pranjali.deshmukh@college.edu` | `Password@123` | Prof. Pranjali Deshmukh — Teaches SEPM |
| **Student (High %)** | `22cs001` | `22cs001@student.ams.edu` | `Password@123` | Aarav Sharma — **95.0% Attendance (Eligible)** |
| **Student (Safe %)** | `22cs002` | `22cs002@student.ams.edu` | `Password@123` | Aditi Rao — **80.0% Attendance (Eligible)** |
| **Student (Defaulter %)**| `22cs003` | `22cs003@student.ams.edu` | `Password@123` | Rohan Gupta — **60.0% Attendance (Defaulter Alert)** |
| **Student (Defaulter %)**| `22cs004` | `22cs004@student.ams.edu` | `Password@123` | Priya Nair — **55.0% Attendance (Defaulter Alert)** |
| **Student (Account)**| `24001033`| `24001033@student.ams.edu` | `Password@123` | Manasvi Bondre — 6th Sem Student |

> **Note on Student Logins:** All 47 students can log in using their roll numbers (`22cs001` through `22cs045`, plus `24001033`) with password `Password@123`.

---

## 🔒 Administrator Registration Security Key

Creating an Administrator account via the public registration page requires backend verification against a master security key. This prevents unauthorized public users from gaining admin privileges.

- **Default Key:** `ADMIN@SEPM2026`
- **Configuring via Environment Variable:**
  - **Windows PowerShell:**
    ```powershell
    $env:ADMIN_REGISTRATION_KEY="MySecretAdminKey2026"
    python app.py
    ```
  - **Windows Command Prompt (CMD):**
    ```cmd
    set ADMIN_REGISTRATION_KEY=MySecretAdminKey2026
    python app.py
    ```
  - **Linux / macOS Bash:**
    ```bash
    export ADMIN_REGISTRATION_KEY="MySecretAdminKey2026"
    python app.py
    ```

Students and Faculty members can register freely with their academic IDs without an admin key.

---

## 💻 Setup Instructions for VS Code on Windows

### Step 1: Open the Project in VS Code
1. Open Visual Studio Code.
2. Go to **File $\rightarrow$ Open Folder...** and select `Project-AMS` (`c:\Users\<Username>\Downloads\Project-AMS`).

### Step 2: Open an Integrated Terminal
Press ``Ctrl + ` `` (backtick) or select **Terminal $\rightarrow$ New Terminal**. Ensure the terminal is **PowerShell**.

### Step 3: (Optional) Create & Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 4: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 5: Run the Application
```powershell
python app.py
```

### Step 6: Access the Web Portal
Open your browser and navigate to:
```
http://127.0.0.1:5000
```
The database (`attendance_system.db`) initializes and seeds automatically upon first run.

---

## 🧪 How to Run Automated Tests

The application includes an automated test suite verifying role-based access control, admin registration security, attendance marking, percentage formulas, CSV exports, and session clearance.

To run the full test suite in your terminal:
```powershell
python test_system.py
```

**Expected Output:**
```text
Ran 18 tests in ~4.0s
OK
```

---

## 📁 Project Directory Structure

```
Project-AMS/
│
├── app.py                      # Main Flask application routes & controllers
├── config.py                   # App configuration & threshold settings
├── database.py                 # SQLite schema, connection manager & seed data
├── models.py                   # Business logic, calculations & database models
├── test_system.py              # 18 automated unit and integration tests
├── wsgi.py                     # Production WSGI server entrypoint
├── requirements.txt            # Python dependencies (Flask, Werkzeug)
├── README.md                   # Setup guide, test credentials & usage instructions
├── PROJECT_PROGRESS.md         # Completed work, repairs log & test verification report
├── PROJECT_EXPLANATION.md      # Architecture, database schema & viva voce Q&A guide
├── SEPM_PROJECT_REPORT.md      # Comprehensive academic project report
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
    │   ├── login.html          # Clean login page with password toggle
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
    │   ├── student_list.html   # Dedicated assigned student roster
    │   ├── mark_attendance.html# Interactive marker, live counters & fast toggles
    │   ├── edit_attendance.html# Safe attendance session updating
    │   ├── session_view.html   # Detailed single session student roster
    │   ├── session_history.html# Past lecture history table
    │   └── subject_stats.html  # Subject-wise percentage & defaulter highlights
    ├── student/
    │   ├── dashboard.html      # Student overview, 75% shortage alert & advice
    │   └── history.html        # Filterable lecture-by-lecture audit history
    ├── common/
    │   └── profile.html        # User account & academic credentials
    └── errors/
        ├── 403.html            # Forbidden / Access Denied
        ├── 404.html            # Page Not Found
        └── 500.html            # Internal Server Error
```

---

## 🚀 Production Deployment Notes

To run with a production WSGI server instead of Flask's built-in development server:

- **Windows (using Waitress):**
  ```powershell
  pip install waitress
  waitress-serve --listen=0.0.0.0:5000 wsgi:application
  ```

- **Linux / Docker (using Gunicorn):**
  ```bash
  pip install gunicorn
  gunicorn -w 4 -b 0.0.0.0:5000 wsgi:application
  ```
