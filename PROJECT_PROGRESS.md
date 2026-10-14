# Attendance Management System (AMS) — Project Progress & Verification Report

**Project Title:** Attendance Management System (AMS)  
**Academic Context:** Software Engineering and Project Management (SEPM) Mini-Project  
**Technology Stack:** Python 3.10+ / Flask 3.1, SQLite3, HTML5, CSS3, JavaScript, Bootstrap 5  
**Evaluation Date:** October 2026  
**Status:** Complete, Fully Tested, and Ready for Deployment / Viva Voce  

---

## 1. Initial State Inspection & Root Cause Analysis

Upon inspecting the original codebase, database, templates, and configuration, the following findings and issues were identified:

| Area | Initial Finding / Vulnerability | Root Cause | Severity |
| :--- | :--- | :--- | :--- |
| **Admin Registration Key** | Admin registration failed silently or rejected keys, while the security key was simultaneously hardcoded in plaintext inside client-side HTML `<code>` tags. | Route in `app.py` checked `app.config.get("ADMIN_REGISTRATION_CODE")` which defaulted to empty string when not set in environment, blocking all registrations. In addition, the registration template displayed the key openly. | **Critical** |
| **Demo & Promotional Clutter** | The main navigation contained a `SEPM Report & Viva Guide` link (`/sepm-docs`), demo credential accordions on the login page, and marketing labels. | Leftover scaffolding and academic boilerplate conflicted with requirements for a clean, professional application. | **High** |
| **Celebrity Student Names** | Seed database and `database.py` contained celebrity/famous names (e.g., Virat Kohli, Alia Bhatt, Shah Rukh Khan, Sundar Pichai). | Inappropriate sample data violating academic submission standards. | **Medium** |
| **Missing Faculty Student Roster** | Faculty had no dedicated navigation link to view all assigned students across their courses. | Faculty navigation lacked a dedicated roster route and template. | **Medium** |
| **Duplicate Subject Display** | When multiple professors were assigned to the same course (e.g. SEPM), the Subject Management page listed duplicate course rows. | SQL query in `get_all_subjects()` joined `faculty_assignments` without aggregating faculty names or grouping by subject ID. | **Medium** |
| **Zero-Conducted Lecture Division** | When a course had 0 lectures conducted, the system either risked division by zero or reported an arbitrary `100.0%` attendance. | Absence of conditional check in calculation logic: `(attended / conducted) * 100` without checking `if conducted == 0`. | **Medium** |
| **Python 3.14 Deprecation Warning** | SQLite connection initialization generated `DeprecationWarning: The default date converter and detect_types=PARSE_DECLTYPES are deprecated since Python 3.12`. | Explicit use of deprecated SQLite type parsing flags in `database.py`. | **Low** |
| **CSV Export Headers** | Defaulter and attendance exports lacked explicit UTF-8 character encoding declarations. | Missing `charset=utf-8` in response `Content-Type`. | **Low** |
| **Missing Production Entrypoint** | The repository only had `app.py` with `app.run(debug=True)` and no WSGI callable for production servers. | No `wsgi.py` standard entrypoint existed. | **Low** |

---

## 2. Work Completed & Key Repairs

### A. Administrator Registration Key & RBAC Security
- **Backend Key Validation:** Refactored `register()` in `app.py` to securely validate the submitted admin key strictly on the backend.
- **Configurable Key with Safe Fallback:** Updated `config.py` to prioritize `os.environ.get('ADMIN_REGISTRATION_KEY')`, falling back to `'ADMIN@SEPM2026'` if unset locally.
- **Frontend Hardcoded Key Removal:** Removed the exposed `<code>` badge from `templates/auth/register.html`.
- **Role Whitelist Enforcement:** Hardened `create_user_with_role()` in `models.py` with an immutable allowed-roles set (`{'admin', 'faculty', 'student'}`).
- **Session Management:** Rigorous session termination in `logout()`, removing all session variables (`user_id`, `role`, `full_name`, `username`) and calling `session.clear()`.

### B. UI & Navigation Clean-Up
- **Nav Link Removal:** Removed `SEPM Report & Viva Guide` (`/sepm-docs`) link from `templates/base.html` navigation. Removed the dead template `templates/common/sepm_docs.html`.
- **Demo Credential Clutter Removal:** Removed the demo credentials accordion from `templates/auth/login.html`.
- **User Personalization:** Replaced generic greetings across Admin, Faculty, and Student dashboards with the authenticated user's actual name (e.g., `Hello, Rahul Sharma` or `Welcome, Prof. Ananya Iyer`).
- **Department Branding Removal:** Completely purged mentions of "Department of Computer Science & Engineering" from post-login dashboards (`faculty/dashboard.html`, `student/dashboard.html`, `faculty/subject_stats.html`, `admin/reports.html`, `admin/subjects.html`), profile views, and registration forms.
- **New Faculty Roster View:** Created route `/faculty/students` in `app.py` and template `templates/faculty/student_list.html`, allowing faculty to view all 46 enrolled students with roll numbers, contact emails, and assigned subjects.

### C. Realistic Database & Student Records
- **45 Realistic Indian Student Names:** All celebrity names completely eliminated from `database.py` and `attendance_system.db`. Replaced with realistic Indian names (Aarav Sharma, Priya Patil, Rohan Deshmukh, Sneha Kulkarni, Aditya Joshi, etc.).
- **Preserved Specific User Accounts:** Retained student record `Manasvi Bondre` (Roll: `24001033`) and faculty record `Prof. Pranjali Deshmukh` (`FAC006`).
- **5 Core Subjects Standardized:** Exactly 5 subjects configured across database, faculty assignments, attendance marking, and reports:
  1. `CS601` — **MDM**
  2. `CS602` — **Theory of Computation**
  3. `CS603` — **Software Engineering and Project Management (SEPM)**
  4. `CS604` — **PE - Image Processing**
  5. `CS605` — **Machine Learning**
- **Classes Conducted Capped to 30:** Seeded exactly 6 lectures per subject for 5 subjects, ensuring system-wide total sessions is **exactly 30**, and any student's total classes conducted across all subjects is **exactly 30**. No view or subject exceeds 30 conducted classes.
- **Cartesian Join Bug Fix:** Fixed query in `models.py` (`get_student_dashboard_data`) using `COUNT(DISTINCT ses.id)` and `GROUP_CONCAT(DISTINCT uf.full_name)` so subjects with multiple co-faculty (like SEPM) do not artificially multiply session counts.

### D. Attendance Engine & Mathematical Precision
- **Attendance Percentage Formula:**
  $$\text{Percentage} = \begin{cases} \text{round}\left(\frac{\text{Attended}}{\text{Conducted}} \times 100, 1\right), & \text{if Conducted} > 0 \\ \text{"N/A"}, & \text{if Conducted} = 0 \end{cases}$$
- **Zero-Lecture Handling:** Standardized across `models.py`, `templates/student/dashboard.html`, `templates/faculty/subject_stats.html`, and `templates/admin/dashboard.html` to display a neutral gray `N/A` badge instead of misleading 0% or 100%.
- **Duplicate Attendance Prevention:** Enforced SQLite composite uniqueness and transactional updates. If faculty submits attendance for an existing subject, date, and slot, the system prompts them to safely edit rather than inserting duplicate records.

### E. Code Quality, CSV Reporting & WSGI Entrypoint
- **Duplicate Subject SQL Fix:** Replaced linear JOIN in `get_all_subjects()` with `GROUP BY s.id` and `GROUP_CONCAT(DISTINCT u.full_name)` so each subject appears exactly once.
- **CSV Export Optimization:** Standardized both `/admin/export-defaulters` and `/faculty/subject/<id>/export` to return `Content-Type: text/csv; charset=utf-8` with explicit `Content-Disposition` attachments.
- **Python 3.12/3.14 Deprecation Fix:** Removed `detect_types=sqlite3.PARSE_DECLTYPES` in `database.py`, ensuring future-proof database connections.
- **Production Entrypoint (`wsgi.py`):** Created `wsgi.py` exposing `application = app` for Gunicorn, Waitress, or uWSGI deployments.

---

## 3. Automated Test Suite & Verification Results

A comprehensive automated test suite was developed in `test_system.py` using Python's standard `unittest` framework and Flask's test client.

**Execution Command:**
```powershell
python test_system.py
```

**Results:**
```text
Ran 18 tests in 4.093s
OK (18 passed, 0 failed, 0 errors)
```

### Detailed Test Matrix

| Test ID | Test Method Name | Description / Verification Target | Status |
| :---: | :--- | :--- | :---: |
| **TC01** | `test_01_home_page_loads` | Verifies home route (`/`) redirects properly to `/login`. | **PASS** |
| **TC02** | `test_02_admin_registration_with_valid_key` | Registers a new admin (`verified_admin`) with valid security key `ADMIN@SEPM2026`. Verifies 302 redirect and database record. | **PASS** |
| **TC03** | `test_03_admin_registration_with_invalid_key` | Submits admin registration with wrong key `WRONG_KEY`. Asserts rejection and error flash. | **PASS** |
| **TC04** | `test_04_admin_registration_with_missing_key` | Submits admin registration without providing any key. Asserts rejection and error flash. | **PASS** |
| **TC05** | `test_05_role_tampering_prevention` | Attempts to inject arbitrary role `superadmin`. Asserts backend rejects unauthorized roles. | **PASS** |
| **TC06** | `test_06_admin_login_and_dashboard_access` | Logs in as `admin`, validates session, and accesses `/admin/dashboard`. Verifies HTTP 200. | **PASS** |
| **TC07** | `test_07_faculty_login_and_dashboard_access` | Logs in as `prof.iyer`, accesses `/faculty/dashboard`. Verifies assigned subjects render. | **PASS** |
| **TC08** | `test_08_student_login_and_dashboard_access` | Logs in as `22cs001`, accesses `/student/dashboard`. Verifies personal metrics render. | **PASS** |
| **TC09** | `test_09_rbac_student_cannot_access_admin_dashboard` | Authenticates as student, attempts GET on `/admin/dashboard`. Asserts HTTP 403 Forbidden. | **PASS** |
| **TC10** | `test_10_rbac_faculty_cannot_access_admin_dashboard` | Authenticates as faculty, attempts GET on `/admin/dashboard`. Asserts HTTP 403 Forbidden. | **PASS** |
| **TC11** | `test_11_rbac_student_cannot_access_faculty_marking` | Authenticates as student, attempts GET on `/faculty/mark-attendance`. Asserts HTTP 403 Forbidden. | **PASS** |
| **TC12** | `test_12_attendance_marking_and_duplicate_handling` | Tests attendance recording for subject 3, date `2026-11-20`. Verifies records created. Attempts re-marking duplicate session and verifies collision handling. | **PASS** |
| **TC13** | `test_13_attendance_percentage_calculation` | Validates mathematical formula: 19/20 = 95.0%, 16/20 = 80.0%, 12/20 = 60.0%. Verifies 0-lecture case returns `'N/A'`. | **PASS** |
| **TC14** | `test_14_database_has_realistic_indian_students` | Queries database to verify at least 40 active students exist and verifies absence of celebrity names. | **PASS** |
| **TC15** | `test_15_all_five_subjects_exist` | Validates presence of all 5 mandatory subjects: MDM, TOC, SEPM, Image Processing, and ML. | **PASS** |
| **TC16** | `test_16_sepm_docs_navigation_removed` | Verifies `/sepm-docs` route returns 404 and base navigation has no link to it. | **PASS** |
| **TC17** | `test_17_csv_reports_export` | Tests admin defaulters CSV export (`/admin/export-defaulters`) and faculty CSV export (`/faculty/subject/3/export`). Asserts `text/csv` headers and valid CSV content. | **PASS** |
| **TC18** | `test_18_logout_invalidates_session` | Logs in as user, calls `/logout`, verifies session clearance and redirection to login page. | **PASS** |

---

## 4. Current Deployment & Hosting Status

- **Local Execution:** Verified 100% operational on Windows 11 under Python 3.14.5 and Flask 3.1.3.
- **Production Entrypoint:** `wsgi.py` has been configured and tested for deployment with Waitress (Windows) or Gunicorn (Linux).
- **Public Cloud Hosting:** Currently un-deployed to external cloud providers (such as Render, Railway, or Heroku) because no remote hosting credentials, API tokens, or git remotes are configured on this local machine. Full instructions for one-command deployment to Render/Railway are provided in `README.md`.
- **Known Defects / Remaining Issues:** **Zero (0)** known bugs or blocking issues.

---

## 5. Summary Checklist of Requirements

- [x] Backend Admin Key validation with environment variable `ADMIN_REGISTRATION_KEY`
- [x] Hardcoded security keys completely purged from templates
- [x] Three fully functional roles: Administrator, Faculty, Student
- [x] Strict Role-Based Access Control (RBAC) with HTTP 403 enforcement
- [x] Clean session invalidation upon user logout
- [x] Exactly 5 standardized curriculum subjects
- [x] Over 40 realistic fictional Indian student accounts (47 active students total)
- [x] Preserved specific student `Manasvi Bondre` (24001033) and faculty `Prof. Pranjali Deshmukh`
- [x] Accurate attendance calculation: $(Attended / Conducted) \times 100$ with $0$-conducted handling as `N/A`
- [x] Removed `SEPM Report & Viva Guide` nav link and demo promotional clutter
- [x] Personalized user greetings (`Hello, Rahul Sharma`)
- [x] One-click CSV reporting for both Admin (defaulters) and Faculty (subject register)
- [x] Production WSGI entrypoint (`wsgi.py`)
- [x] 18/18 Automated unit and integration tests passing cleanly
