# Attendance Management System (AMS) — Viva Voce & Technical Architecture Guide

**Project Title:** Attendance Management System (AMS)  
**Subject:** Software Engineering and Project Management (SEPM)  
**Target Audience:** Students, Project Evaluators, External Examiners  
**Technology Stack:** Python 3 (Flask), SQLite3, HTML5, Bootstrap 5, Vanilla JavaScript  

---

## 1. Project Architecture & Technology Choices

### Architectural Pattern: Layered Model-View-Controller (MVC)
The Attendance Management System is built strictly adhering to the classical **3-Tier Layered MVC Architecture**:

```
+-----------------------------------------------------------------------+
|                        PRESENTATION LAYER (VIEW)                      |
|   HTML5 + Jinja2 Templates + Bootstrap 5 + Vanilla JavaScript (CSS/JS)|
+-----------------------------------------------------------------------+
                                   | HTTP Requests / HTML Responses
                                   v
+-----------------------------------------------------------------------+
|                       APPLICATION LAYER (CONTROLLER)                  |
|   Flask Application Routes (app.py) + Auth / RBAC Decorators          |
+-----------------------------------------------------------------------+
                                   | Function Calls / Python Data Types
                                   v
+-----------------------------------------------------------------------+
|                        BUSINESS & DATA LAYER (MODEL)                  |
|   Domain Models & Calculation Engine (models.py)                      |
|   Database Connection Manager & Seed Logic (database.py)              |
+-----------------------------------------------------------------------+
                                   | SQL Queries (ACID Transactions)
                                   v
+-----------------------------------------------------------------------+
|                       PERSISTENCE LAYER (DATABASE)                    |
|   SQLite Relational Database (attendance_system.db)                   |
+-----------------------------------------------------------------------+
```

### Technology Selection Rationale

1. **Python & Flask (Backend Framework):**
   - *Microframework Efficiency:* Unlike monolithic frameworks like Django, Flask is lightweight and unopinionated, providing routing, template rendering, and session handling without heavy ORM boilerplate.
   - *Clarity for Evaluation:* Code flow from HTTP route $\rightarrow$ query $\rightarrow$ template is completely explicit and easy to trace line-by-line during a viva.
   - *Standard Library Integration:* Uses Python standard library modules (`sqlite3`, `csv`, `os`, `math`) minimizing third-party dependency vulnerabilities.

2. **SQLite3 (Database Engine):**
   - *Serverless & Zero-Configuration:* Runs entirely within the local process space; no separate database server daemon (like MySQL or PostgreSQL) needs to be configured, making it ideal for self-contained college projects and offline defense demonstrations.
   - *ACID Compliance:* Supports full Atomic, Consistent, Isolated, and Durable transactions, ensuring attendance records are never partially committed.
   - *Portability:* The entire database is stored in a single binary file (`attendance_system.db`) which can be backed up or inspected easily.

3. **Bootstrap 5 & Vanilla JavaScript (Frontend):**
   - *Zero Build-Step:* No Node.js, Webpack, or npm pipelines required; templates render server-side instantly.
   - *Responsive Grid:* Clean, accessible layout across desktop workstations and mobile screens.
   - *Interactive DOM Helpers:* Vanilla JavaScript handles instant table search filtering, live attendance counter tallies, and password visibility toggles without third-party framework overhead.

---

## 2. Database Schema & Relational Design

The database schema is normalized to **Third Normal Form (3NF)** to eliminate data redundancy, update anomalies, and ensure referential integrity.

### Entity-Relationship (ER) Overview

```
 [ USERS ] 1 ───< N [ FACULTY_ASSIGNMENTS ] >─── 1 [ SUBJECTS ]
     │                                                    │
     │ 1                                                  │ 1
     │                                                    │
     v N                                                  v N
 [ ENROLLMENTS ] >────────────────────────────────────────┘
     │
     │
     v (Attends)
 [ ATTENDANCE_RECORDS ] N >─── 1 [ ATTENDANCE_SESSIONS ] N >─── 1 [ SUBJECTS ]
                                          │
                                          v N
                                      [ USERS (Faculty) ]
```

### Table Definitions & Constraints

1. **`users` (User Master Table):**
   - `id` (INTEGER, Primary Key, Autoincrement)
   - `username` (VARCHAR(50), Unique, Not Null) — System login handle (e.g. `admin`, `prof.iyer`, `22cs001`)
   - `email` (VARCHAR(100), Unique, Not Null) — Email address
   - `password_hash` (VARCHAR(255), Not Null) — Salted PBKDF2:SHA256 password hash
   - `full_name` (VARCHAR(100), Not Null) — Display name
   - `role` (VARCHAR(20), Not Null) — Constrained to `admin`, `faculty`, `student`
   - `phone` (VARCHAR(20), Nullable)
   - `roll_number` (VARCHAR(30), Unique, Nullable) — Unique student registration ID
   - `department` (VARCHAR(50), Nullable) — Academic department (e.g. `Computer Science & Engineering`)
   - `semester` (INTEGER, Nullable) — Current enrolled semester
   - `section` (VARCHAR(10), Nullable) — Academic division
   - `is_active` (BOOLEAN, Default 1) — Logical soft-delete / access flag
   - `created_at` (TIMESTAMP)

2. **`subjects` (Curriculum Master):**
   - `id` (INTEGER, Primary Key, Autoincrement)
   - `subject_code` (VARCHAR(20), Unique, Not Null) — Course code (e.g. `CS601`, `CS603`)
   - `subject_name` (VARCHAR(100), Not Null) — Standard course title
   - `department` (VARCHAR(50), Not Null)
   - `semester` (INTEGER, Not Null)
   - `credits` (INTEGER, Default 4)

3. **`faculty_assignments` (Faculty-to-Course Association):**
   - Composite mapping connecting a faculty user to an assigned subject.
   - Enforces Foreign Keys to `users(id)` and `subjects(id)` with `ON DELETE CASCADE`.

4. **`enrollments` (Student-to-Course Association):**
   - Connects students to active courses.
   - Enforces composite uniqueness on `(student_id, subject_id)` so a student cannot be enrolled twice in the same subject.

5. **`attendance_sessions` (Lecture Ledger Header):**
   - `id` (INTEGER, Primary Key, Autoincrement)
   - `subject_id` (INTEGER, FK $\rightarrow$ `subjects.id`)
   - `faculty_id` (INTEGER, FK $\rightarrow$ `users.id`)
   - `session_date` (DATE, Not Null) — ISO formatted date (`YYYY-MM-DD`)
   - `time_slot` (VARCHAR(30), Not Null) — Standard lecture slot (e.g. `09:00 - 10:00 AM`)
   - `topic` (TEXT, Nullable) — Curriculum syllabus topic covered
   - **Composite Unique Constraint:** `UNIQUE(subject_id, session_date, time_slot)` prevents duplicate lecture entries for the same subject at the same time.

6. **`attendance_records` (Student Session Ledger Item):**
   - `id` (INTEGER, Primary Key, Autoincrement)
   - `session_id` (INTEGER, FK $\rightarrow$ `attendance_sessions.id` `ON DELETE CASCADE`)
   - `student_id` (INTEGER, FK $\rightarrow$ `users.id` `ON DELETE CASCADE`)
   - `status` (VARCHAR(10), Not Null) — Constrained to `'Present'` or `'Absent'`
   - `remarks` (TEXT, Nullable)
   - **Composite Unique Constraint:** `UNIQUE(session_id, student_id)` prevents recording multiple attendance statuses for the same student in a single lecture.

---

## 3. Key Algorithms & Mathematical Calculations

### A. Real-Time Attendance Percentage Calculation

For any student $i$ in subject $j$:
$$\text{Percentage}_{i,j} = \begin{cases} \text{round}\left(\frac{\text{Classes Attended}_{i,j}}{\text{Classes Conducted}_{j}} \times 100, 1\right), & \text{if Conducted}_{j} > 0 \\ \text{"N/A"}, & \text{if Conducted}_{j} = 0 \end{cases}$$

- **Zero-Lecture Safe Guard:** If a newly assigned subject has 0 conducted classes, computing $\frac{A}{C}$ would throw a `ZeroDivisionError` or falsely display `0.0%` or `100.0%`. The algorithm returns `"N/A"`, rendered with a gray badge in the UI.

### B. Statutory Shortage (Defaulter) Detection

The statutory university threshold is defined as $\tau = 75.0\%$.
- **Defaulter Condition:**
  $$\text{IsDefaulter}(i) = \left(\text{Conducted} > 0\right) \land \left(\text{Percentage}_i < 75.0\right)$$
- If `IsDefaulter` is true, high-priority alert cards are displayed on the Student Portal, and the student is included in the Admin and Faculty Defaulter Lists and CSV exports.

### C. Attendance Optimization & Recovery Advisories

#### 1. Shortage Recovery: Classes Needed to Reach 75%
If a student is below 75%, how many **consecutive future classes ($x$)** must they attend without missing any to restore eligibility?

$$\frac{A + x}{C + x} \ge 0.75$$
$$A + x \ge 0.75(C + x)$$
$$A + x \ge 0.75C + 0.75x$$
$$0.25x \ge 0.75C - A$$
$$x \ge \frac{0.75C - A}{0.25} = 3C - 4A$$

Taking the ceiling for discrete class sessions:
$$x = \max\left(0, \left\lceil \frac{0.75C - A}{0.25} \right\rceil\right)$$

*Example:* A student attended $A = 12$ out of $C = 20$ classes ($60.0\%$).
$$x = \lceil 3(20) - 4(12) \rceil = \lceil 60 - 48 \rceil = 12 \text{ classes}$$
*UI Banner:* "Attend the next **12** consecutive classes to reach 75% attendance."

#### 2. Safe Absence Margin: Classes That Can Be Safely Missed
If a student currently has $\ge 75\%$, how many **future classes ($y$)** can they miss consecutively before falling below 75%?

$$\frac{A}{C + y} \ge 0.75$$
$$A \ge 0.75(C + y)$$
$$0.75y \le A - 0.75C$$
$$y \le \frac{A - 0.75C}{0.75}$$

Taking the floor for discrete class sessions:
$$y = \max\left(0, \left\lfloor \frac{A - 0.75C}{0.75} \right\rfloor\right)$$

*Example:* A student attended $A = 19$ out of $C = 20$ classes ($95.0\%$).
$$y = \left\lfloor \frac{19 - 0.75(20)}{0.75} \right\rfloor = \left\lfloor \frac{19 - 15}{0.75} \right\rfloor = \lfloor 5.33 \rfloor = 5 \text{ classes}$$
*UI Banner:* "You can safely miss up to **5** classes while maintaining $\ge 75\%$."

---

## 4. Security Architecture & Role-Based Access Control (RBAC)

### A. Password Security
- Passwords are never stored in plaintext.
- The system employs Werkzeug's `generate_password_hash` utilizing `scrypt` or `pbkdf2:sha256` with a cryptographically secure random salt.
- Authentication validates input using constant-time hash comparison via `check_password_hash` to defend against timing attacks.

### B. Administrator Registration Security Key
- **Threat Model:** In an open web deployment, any visitor could access the registration page and select the "Administrator" role to gain full control.
- **Enforcement Mechanism:**
  1. The client-side form reveals the Admin Security Key field only when the "Administrator" role is selected.
  2. The registration route in `app.py` enforces backend validation:
     ```python
     expected_key = os.environ.get('ADMIN_REGISTRATION_KEY', app.config.get('ADMIN_REGISTRATION_KEY', 'ADMIN@SEPM2026'))
     if role == 'admin' and admin_key != expected_key:
         flash('Invalid Administrator Registration Key.', 'danger')
         return redirect(url_for('register'))
     ```
  3. The key is never rendered or stored in client-side HTML or JS.
  4. Role tampering (e.g. sending `role=superuser` via curl or Postman) is rejected by a strict backend whitelist check: `if role not in {'admin', 'faculty', 'student'}: abort(400)`.

### C. Session Integrity & Access Control Decorators
- User sessions are stored in cryptographically signed client-side cookies managed by Flask's `SECRET_KEY`.
- Endpoint protection is enforced through Python function decorators:
  - `@login_required`: Redirects unauthenticated users to `/login`.
  - `@role_required(['admin'])`: Compares `session.get('role')` against permitted roles; unauthorized requests immediately raise `HTTP 403 Forbidden`.
- **Session Termination:** Calling `/logout` completely clears the server-side reference and deletes all session dictionary keys (`session.clear()`).

---

## 5. Viva Voce Examination Questions & Model Answers

### Q1: What is the primary purpose and scope of your project?
**Answer:**  
The Attendance Management System (AMS) is a web-based enterprise application developed to automate student attendance recording, eliminate errors in manual paper registers, prevent attendance fraud, automatically compute statutory attendance percentages, and provide early warning alerts for students falling below the mandatory 75% university attendance threshold.

### Q2: What Software Development Life Cycle (SDLC) model did you adopt?
**Answer:**  
We followed an **Agile Scrum Methodology** with 2-week sprint iterations:
- *Sprint 1:* Requirements engineering, ER modeling, and SQLite schema definition.
- *Sprint 2:* User authentication, role-based access control, and backend admin key verification.
- *Sprint 3:* Faculty marking module, live JavaScript counters, and duplicate attendance prevention.
- *Sprint 4:* Student portal, attendance shortage/recovery algorithms, and CSV export reporting.
- *Sprint 5:* Comprehensive automated testing (18 unit/integration tests) and WSGI deployment preparation.

### Q3: Why did you choose SQLite over MySQL or PostgreSQL?
**Answer:**  
SQLite is a zero-configuration, serverless, self-contained relational database engine that supports full ACID transactions. For this college project:
1. It eliminates external database server setup and configuration dependencies.
2. The entire system is portable within a single file (`attendance_system.db`).
3. For academic departmental loads (hundreds of students and daily attendance sessions), SQLite offers microsecond query latencies and zero memory footprint overhead.
Should the system scale across a multi-campus university with high concurrent write loads, the architectural separation in `database.py` allows seamless migration to PostgreSQL by simply replacing the connection handler.

### Q4: How do you prevent duplicate attendance entries for the same lecture?
**Answer:**  
Duplicate attendance prevention is enforced at two levels:
1. **Database Level:** The `attendance_sessions` table has a composite unique constraint `UNIQUE(subject_id, session_date, time_slot)`, and `attendance_records` enforces `UNIQUE(session_id, student_id)`.
2. **Application Level:** When a faculty member attempts to submit attendance for a subject, date, and slot that already exists, the controller intercepts the collision, notifies the user that attendance for this session was already recorded, and provides a direct link to edit the existing session instead of inserting duplicate rows.

### Q5: How do you handle cases where a subject has had 0 conducted lectures?
**Answer:**  
In naive implementations, dividing attended classes by conducted classes (`attended / conducted`) when `conducted == 0` causes a `ZeroDivisionError` crash, or displays an incorrect `0.0%` or `100.0%`. In our system, the calculation engine checks:
`if total_conducted == 0: percentage_display = 'N/A'`.  
The templates render a neutral "No Classes" badge instead of false defaulter alerts.

### Q6: How does the system calculate the number of classes a student must attend to reach 75%?
**Answer:**  
Using the formula derived from $\frac{A + x}{C + x} \ge 0.75$, we obtain $x \ge \frac{0.75C - A}{0.25} = 3C - 4A$. Taking the mathematical ceiling $\lceil 3C - 4A \rceil$ gives the exact minimum number of consecutive future lectures the student must attend to satisfy the 75% statutory requirement.

### Q7: How do you protect administrative registration from unauthorized public users?
**Answer:**  
We implemented a backend-verified master security key (`ADMIN_REGISTRATION_KEY`). Even if an attacker un-hides the Admin radio button in HTML or crafts a direct POST request with `role=admin`, the backend route checks the submitted key against the server's environment configuration. If the key is missing or incorrect, registration is rejected, an error is flashed, and no administrator account is created.

### Q8: What security measures prevent students from marking or editing attendance?
**Answer:**  
Role-Based Access Control (RBAC) is enforced at the route level via the `@role_required(['faculty', 'admin'])` decorator. Even if a student discovers the URL `/faculty/mark-attendance` or attempts to send a POST request with attendance data, the decorator detects that `session['role'] == 'student'` and immediately halts the request with an `HTTP 403 Forbidden` response.

### Q9: How are passwords secured in the database?
**Answer:**  
Passwords are never stored in plaintext. They are hashed using Werkzeug's `generate_password_hash`, which applies the standard PBKDF2:SHA256 algorithm with a random cryptographic salt. During login, `check_password_hash` hashes the incoming password with the stored salt using constant-time comparison, neutralizing rainbow table attacks and timing analysis.

### Q10: How do you test the application?
**Answer:**  
We developed an automated regression test suite in `test_system.py` containing 18 automated tests that execute via `python test_system.py`. It verifies:
- Unauthenticated redirection and login session integrity.
- Admin registration with valid, invalid, and missing keys.
- Role tampering prevention.
- Role-based 403 Forbidden access boundaries.
- Attendance marking, duplicate collision detection, and transactional editing.
- Percentage calculations including edge cases (0 lectures conducted).
- Defaulter and subject attendance register CSV exports.
- Session clearance on logout.
All 18 tests pass deterministically.
