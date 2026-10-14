from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from datetime import datetime

# ==========================================
# AUTHENTICATION & USER HELPERS
# ==========================================

def authenticate_user(username_or_email, password):
    """
    Validates user credentials against username or email.
    Returns (user_dict, error_message).
    """
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM users 
        WHERE (LOWER(username) = LOWER(?) OR LOWER(email) = LOWER(?))
    """, (username_or_email.strip(), username_or_email.strip()))
    user = cursor.fetchone()

    if not user:
        return None, "Invalid username/email or password."

    if not user['is_active']:
        return None, "This account has been deactivated by the administrator."

    if not check_password_hash(user['password_hash'], password):
        return None, "Invalid username/email or password."

    return dict(user), None

def get_user_by_id(user_id):
    """Retrieves user profile and role-specific details."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return None
    
    user_dict = dict(user)
    if user['role'] == 'student':
        cursor.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
        s_row = cursor.fetchone()
        if s_row:
            user_dict['student_details'] = dict(s_row)
    elif user['role'] == 'faculty':
        cursor.execute("SELECT * FROM faculty WHERE user_id = ?", (user_id,))
        f_row = cursor.fetchone()
        if f_row:
            user_dict['faculty_details'] = dict(f_row)

    return user_dict

# ==========================================
# ADMIN QUERIES
# ==========================================

def get_admin_dashboard_stats():
    """Calculates key counts and health metrics for the admin overview."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM faculty")
    total_faculty = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance_sessions")
    total_sessions = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance_records")
    total_records = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM attendance_records WHERE status = 'Present'")
    total_present = cursor.fetchone()[0]

    if total_records > 0:
        overall_pct = round((total_present / total_records * 100), 1)
        overall_pct_display = f"{overall_pct}%"
    else:
        overall_pct = None
        overall_pct_display = "N/A"

    # Count defaulter students (< 75% overall)
    cursor.execute("""
        SELECT s.id,
               COUNT(ar.id) as total_conducted,
               SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) as total_present
        FROM students s
        LEFT JOIN attendance_records ar ON s.id = ar.student_id
        GROUP BY s.id
    """)
    defaulter_count = 0
    for row in cursor.fetchall():
        cond = row['total_conducted'] or 0
        pres = row['total_present'] or 0
        pct = (pres / cond * 100) if cond > 0 else 100.0
        if cond > 0 and pct < Config.ATTENDANCE_THRESHOLD:
            defaulter_count += 1

    return {
        'total_students': total_students,
        'total_faculty': total_faculty,
        'total_subjects': total_subjects,
        'total_sessions': total_sessions,
        'total_records': total_records,
        'overall_pct': overall_pct,
        'overall_pct_display': overall_pct_display,
        'defaulter_count': defaulter_count
    }

def get_all_users(role=None, search=None):
    """Fetches user list with optional role and search filters."""
    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT u.id, u.username, u.email, u.role, u.full_name, u.phone, u.is_active, u.created_at,
               s.roll_number, s.department as student_dept, s.semester, s.section,
               f.faculty_id, f.department as faculty_dept, f.designation
        FROM users u
        LEFT JOIN students s ON u.id = s.user_id
        LEFT JOIN faculty f ON u.id = f.user_id
        WHERE 1=1
    """
    params = []

    if role and role in ('admin', 'faculty', 'student'):
        query += " AND u.role = ?"
        params.append(role)

    if search:
        s_term = f"%{search.strip()}%"
        query += """ AND (
            u.full_name LIKE ? OR 
            u.username LIKE ? OR 
            u.email LIKE ? OR 
            s.roll_number LIKE ? OR 
            f.faculty_id LIKE ?
        )"""
        params.extend([s_term, s_term, s_term, s_term, s_term])

    query += " ORDER BY u.role, u.full_name ASC"
    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

def create_user_with_role(username, email, password, role, full_name, phone=None, extra_data=None):
    """
    Creates a new user and associated role row (student or faculty) within a single transaction.
    Returns (user_id, None) on success, or (None, error_message).
    """
    db = get_db()
    cursor = db.cursor()
    extra_data = extra_data or {}
    role = (role or '').strip().lower()
    if role not in ('admin', 'faculty', 'student'):
        return None, "Invalid user role specified."

    # Check unique username and email
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
    if cursor.fetchone():
        return None, "Username already exists. Please choose a different username."

    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
    if cursor.fetchone():
        return None, "Email address is already registered."

    pw_hash = generate_password_hash(password)

    try:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name, phone, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (username.strip(), email.strip().lower(), pw_hash, role, full_name.strip(), phone))
        user_id = cursor.lastrowid

        if role == 'student':
            roll_number = extra_data.get('roll_number', '').strip().upper()
            if not roll_number:
                db.rollback()
                return None, "Roll Number is required for student registration."
            
            # Check roll uniqueness
            cursor.execute("SELECT id FROM students WHERE roll_number = ?", (roll_number,))
            if cursor.fetchone():
                db.rollback()
                return None, f"Roll Number '{roll_number}' is already registered."

            dept = extra_data.get('department', 'Computer Science & Engineering')
            sem = int(extra_data.get('semester', 6))
            sec = extra_data.get('section', 'A').strip().upper()
            batch = extra_data.get('batch_year', '2022-2026')

            cursor.execute("""
                INSERT INTO students (user_id, roll_number, department, semester, section, batch_year)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, roll_number, dept, sem, sec, batch))
            student_id = cursor.lastrowid

            # Enroll student in all current subjects
            cursor.execute("SELECT id FROM subjects")
            for subj_row in cursor.fetchall():
                cursor.execute("""
                    INSERT OR IGNORE INTO student_subjects (student_id, subject_id)
                    VALUES (?, ?)
                """, (student_id, subj_row['id']))

        elif role == 'faculty':
            faculty_id = extra_data.get('faculty_id', '').strip().upper()
            if not faculty_id:
                db.rollback()
                return None, "Faculty ID is required for faculty registration."
            
            cursor.execute("SELECT id FROM faculty WHERE faculty_id = ?", (faculty_id,))
            if cursor.fetchone():
                db.rollback()
                return None, f"Faculty ID '{faculty_id}' is already registered."

            dept = extra_data.get('department', 'Computer Science & Engineering')
            desig = extra_data.get('designation', 'Assistant Professor')

            cursor.execute("""
                INSERT INTO faculty (user_id, faculty_id, department, designation)
                VALUES (?, ?, ?, ?)
            """, (user_id, faculty_id, dept, desig))
            faculty_db_id = cursor.lastrowid

            # If a subject was selected for assignment
            subj_id = extra_data.get('subject_id')
            if subj_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO faculty_subjects (faculty_id, subject_id)
                    VALUES (?, ?)
                """, (faculty_db_id, int(subj_id)))

        db.commit()
        return user_id, None
    except Exception as e:
        db.rollback()
        return None, f"Database error while creating user: {str(e)}"

def update_user_details(user_id, full_name, email, phone=None, extra_data=None, is_active=1):
    """Updates user information across users and role-specific tables."""
    db = get_db()
    cursor = db.cursor()
    extra_data = extra_data or {}

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        return False, "User not found."

    # Check email duplicate on another user
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?) AND id != ?", (email.strip(), user_id))
    if cursor.fetchone():
        return False, "Another user is already registered with this email address."

    try:
        cursor.execute("""
            UPDATE users 
            SET full_name = ?, email = ?, phone = ?, is_active = ?
            WHERE id = ?
        """, (full_name.strip(), email.strip().lower(), phone, is_active, user_id))

        if user['role'] == 'student':
            roll_number = extra_data.get('roll_number', '').strip().upper()
            if roll_number:
                cursor.execute("SELECT id FROM students WHERE roll_number = ? AND user_id != ?", (roll_number, user_id))
                if cursor.fetchone():
                    db.rollback()
                    return False, f"Roll Number '{roll_number}' belongs to another student."

            dept = extra_data.get('department', 'Computer Science & Engineering')
            sem = int(extra_data.get('semester', 6))
            sec = extra_data.get('section', 'A')
            batch = extra_data.get('batch_year', '2022-2026')

            cursor.execute("""
                UPDATE students 
                SET roll_number = ?, department = ?, semester = ?, section = ?, batch_year = ?
                WHERE user_id = ?
            """, (roll_number, dept, sem, sec, batch, user_id))

        elif user['role'] == 'faculty':
            faculty_id = extra_data.get('faculty_id', '').strip().upper()
            if faculty_id:
                cursor.execute("SELECT id FROM faculty WHERE faculty_id = ? AND user_id != ?", (faculty_id, user_id))
                if cursor.fetchone():
                    db.rollback()
                    return False, f"Faculty ID '{faculty_id}' belongs to another faculty."

            dept = extra_data.get('department', 'Computer Science & Engineering')
            desig = extra_data.get('designation', 'Assistant Professor')

            cursor.execute("""
                UPDATE faculty 
                SET faculty_id = ?, department = ?, designation = ?
                WHERE user_id = ?
            """, (faculty_id, dept, desig, user_id))

        db.commit()
        return True, "User updated successfully."
    except Exception as e:
        db.rollback()
        return False, f"Error updating user: {str(e)}"

def toggle_user_active_status(user_id):
    """Toggles user is_active flag."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT is_active, role FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return False, "User not found."
    
    new_status = 0 if row['is_active'] == 1 else 1
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    return True, f"User status set to {'Active' if new_status else 'Inactive'}."

def delete_user_by_id(user_id):
    """Deletes user and cascades related records."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT role, username FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        return False, "User not found."
    
    if row['username'] == 'admin':
        return False, "Primary system administrator account cannot be deleted."

    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    return True, "User deleted successfully."

# ==========================================
# SUBJECT QUERIES
# ==========================================

def get_all_subjects():
    """Returns all subjects along with assigned faculty and student enrollment count."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.code, s.name, s.department, s.semester, s.credits,
               f.id as faculty_id,
               GROUP_CONCAT(DISTINCT f.faculty_id) as faculty_code,
               GROUP_CONCAT(DISTINCT u.full_name) as faculty_name,
               (SELECT COUNT(*) FROM student_subjects ss WHERE ss.subject_id = s.id) as enrolled_students,
               (SELECT COUNT(*) FROM attendance_sessions ses WHERE ses.subject_id = s.id) as total_sessions
        FROM subjects s
        LEFT JOIN faculty_subjects fs ON s.id = fs.subject_id
        LEFT JOIN faculty f ON fs.faculty_id = f.id
        LEFT JOIN users u ON f.user_id = u.id
        GROUP BY s.id
        ORDER BY s.code ASC
    """)
    return [dict(row) for row in cursor.fetchall()]

def get_subject_by_id(subject_id):
    """Returns single subject details."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.*, fs.faculty_id
        FROM subjects s
        LEFT JOIN faculty_subjects fs ON s.id = fs.subject_id
        WHERE s.id = ?
    """, (subject_id,))
    row = cursor.fetchone()
    return dict(row) if row else None

def save_subject(code, name, department, semester, credits, faculty_id=None, subject_id=None):
    """Creates or updates a subject."""
    db = get_db()
    cursor = db.cursor()
    code = code.strip().upper()
    name = name.strip()

    try:
        if subject_id:
            # Check duplicate code
            cursor.execute("SELECT id FROM subjects WHERE code = ? AND id != ?", (code, subject_id))
            if cursor.fetchone():
                return False, f"Subject code '{code}' already exists."

            cursor.execute("""
                UPDATE subjects 
                SET code = ?, name = ?, department = ?, semester = ?, credits = ?
                WHERE id = ?
            """, (code, name, department, semester, credits, subject_id))
            curr_subj_id = subject_id
        else:
            cursor.execute("SELECT id FROM subjects WHERE code = ?", (code,))
            if cursor.fetchone():
                return False, f"Subject code '{code}' already exists."

            cursor.execute("""
                INSERT INTO subjects (code, name, department, semester, credits)
                VALUES (?, ?, ?, ?, ?)
            """, (code, name, department, semester, credits))
            curr_subj_id = cursor.lastrowid

            # Auto-enroll all students in this semester
            cursor.execute("SELECT id FROM students WHERE semester = ?", (semester,))
            for st in cursor.fetchall():
                cursor.execute("""
                    INSERT OR IGNORE INTO student_subjects (student_id, subject_id)
                    VALUES (?, ?)
                """, (st['id'], curr_subj_id))

        # Update faculty assignment
        cursor.execute("DELETE FROM faculty_subjects WHERE subject_id = ?", (curr_subj_id,))
        if faculty_id:
            cursor.execute("""
                INSERT INTO faculty_subjects (faculty_id, subject_id)
                VALUES (?, ?)
            """, (int(faculty_id), curr_subj_id))

        db.commit()
        return True, "Subject saved successfully."
    except Exception as e:
        db.rollback()
        return False, f"Error saving subject: {str(e)}"

def delete_subject_by_id(subject_id):
    """Deletes a subject and its associated sessions/records."""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        db.commit()
        return True, "Subject deleted successfully."
    except Exception as e:
        db.rollback()
        return False, f"Error deleting subject: {str(e)}"

# ==========================================
# FACULTY QUERIES
# ==========================================

def get_faculty_assigned_subjects(faculty_user_id):
    """Retrieves all subjects assigned to the logged-in faculty."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id, s.code, s.name, s.department, s.semester, s.credits,
               f.id as faculty_db_id,
               (SELECT COUNT(*) FROM student_subjects ss WHERE ss.subject_id = s.id) as student_count,
               (SELECT COUNT(*) FROM attendance_sessions ses WHERE ses.subject_id = s.id AND ses.faculty_id = f.id) as sessions_taken
        FROM faculty f
        JOIN faculty_subjects fs ON f.id = fs.faculty_id
        JOIN subjects s ON fs.subject_id = s.id
        WHERE f.user_id = ?
        ORDER BY s.code ASC
    """, (faculty_user_id,))
    return [dict(row) for row in cursor.fetchall()]

def get_students_for_subject(subject_id):
    """Retrieves enrolled students for a subject, ordered by roll number."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT s.id as student_id, s.roll_number, s.department, s.semester, s.section,
               u.full_name, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN student_subjects ss ON s.id = ss.student_id
        WHERE ss.subject_id = ? AND u.is_active = 1
        ORDER BY s.roll_number ASC
    """, (subject_id,))
    return [dict(row) for row in cursor.fetchall()]

def check_existing_session(subject_id, session_date, session_slot):
    """Safeguard to check if a session already exists for subject, date, slot."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT ses.id, ses.topic, u.full_name as faculty_name,
               (SELECT COUNT(*) FROM attendance_records WHERE session_id = ses.id) as record_count
        FROM attendance_sessions ses
        JOIN faculty f ON ses.faculty_id = f.id
        JOIN users u ON f.user_id = u.id
        WHERE ses.subject_id = ? AND ses.session_date = ? AND ses.session_slot = ?
    """, (subject_id, session_date, session_slot))
    row = cursor.fetchone()
    return dict(row) if row else None

def record_attendance_session(subject_id, faculty_user_id, session_date, session_slot, topic, attendance_status_dict):
    """
    Creates an attendance session and inserts attendance records for each student.
    Guards against duplicates.
    """
    db = get_db()
    cursor = db.cursor()

    # Get faculty DB id
    cursor.execute("SELECT id FROM faculty WHERE user_id = ?", (faculty_user_id,))
    fac_row = cursor.fetchone()
    if not fac_row:
        return False, "Faculty profile not found."
    faculty_db_id = fac_row['id']

    # Safeguard check
    existing = check_existing_session(subject_id, session_date, session_slot)
    if existing:
        return False, f"Attendance already exists for this subject on {session_date} ({session_slot}). Please edit the existing session instead."

    try:
        cursor.execute("""
            INSERT INTO attendance_sessions (subject_id, faculty_id, session_date, session_slot, topic)
            VALUES (?, ?, ?, ?, ?)
        """, (subject_id, faculty_db_id, session_date, session_slot, topic.strip()))
        session_id = cursor.lastrowid

        # Insert records
        records = []
        for student_id_str, status in attendance_status_dict.items():
            st_status = 'Present' if status == 'Present' else 'Absent'
            records.append((session_id, int(student_id_str), st_status))

        cursor.executemany("""
            INSERT INTO attendance_records (session_id, student_id, status)
            VALUES (?, ?, ?)
        """, records)

        db.commit()
        return True, session_id
    except Exception as e:
        db.rollback()
        return False, f"Failed to record attendance: {str(e)}"

def update_existing_attendance_session(session_id, session_date, session_slot, topic, attendance_status_dict):
    """Updates an existing session's metadata and student attendance status."""
    db = get_db()
    cursor = db.cursor()

    try:
        cursor.execute("""
            UPDATE attendance_sessions 
            SET session_date = ?, session_slot = ?, topic = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session_date, session_slot, topic.strip(), session_id))

        for student_id_str, status in attendance_status_dict.items():
            st_status = 'Present' if status == 'Present' else 'Absent'
            cursor.execute("""
                INSERT INTO attendance_records (session_id, student_id, status)
                VALUES (?, ?, ?)
                ON CONFLICT(session_id, student_id) 
                DO UPDATE SET status = excluded.status
            """, (session_id, int(student_id_str), st_status))

        db.commit()
        return True, "Attendance updated successfully."
    except Exception as e:
        db.rollback()
        return False, f"Failed to update session: {str(e)}"

def get_session_details(session_id):
    """Fetches session info along with student attendance roster."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT ses.*, s.name as subject_name, s.code as subject_code,
               u.full_name as faculty_name, f.faculty_id as faculty_code
        FROM attendance_sessions ses
        JOIN subjects s ON ses.subject_id = s.id
        JOIN faculty f ON ses.faculty_id = f.id
        JOIN users u ON f.user_id = u.id
        WHERE ses.id = ?
    """, (session_id,))
    session_row = cursor.fetchone()
    if not session_row:
        return None, None

    cursor.execute("""
        SELECT ar.id as record_id, ar.status, ar.remarks,
               s.id as student_id, s.roll_number, u.full_name as student_name
        FROM attendance_records ar
        JOIN students s ON ar.student_id = s.id
        JOIN users u ON s.user_id = u.id
        WHERE ar.session_id = ?
        ORDER BY s.roll_number ASC
    """, (session_id,))
    records = [dict(r) for r in cursor.fetchall()]

    return dict(session_row), records

def get_faculty_sessions_history(faculty_user_id=None, subject_id=None, limit=50):
    """Returns list of past attendance sessions with present/absent summary statistics."""
    db = get_db()
    cursor = db.cursor()

    query = """
        SELECT ses.id, ses.session_date, ses.session_slot, ses.topic, ses.created_at,
               s.code as subject_code, s.name as subject_name,
               u.full_name as faculty_name,
               COUNT(ar.id) as total_marked,
               SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM attendance_sessions ses
        JOIN subjects s ON ses.subject_id = s.id
        JOIN faculty f ON ses.faculty_id = f.id
        JOIN users u ON f.user_id = u.id
        LEFT JOIN attendance_records ar ON ses.id = ar.session_id
        WHERE 1=1
    """
    params = []

    if faculty_user_id:
        query += " AND f.user_id = ?"
        params.append(faculty_user_id)

    if subject_id:
        query += " AND ses.subject_id = ?"
        params.append(subject_id)

    query += " GROUP BY ses.id ORDER BY ses.session_date DESC, ses.session_slot DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    results = []
    for row in cursor.fetchall():
        d = dict(row)
        tot = d['total_marked'] or 0
        pres = d['present_count'] or 0
        d['percentage'] = round((pres / tot * 100), 1) if tot > 0 else 0.0
        results.append(d)
    return results

def get_subject_student_attendance_summary(subject_id):
    """
    Computes attendance percentage for all students enrolled in a subject.
    Identifies students below threshold.
    """
    db = get_db()
    cursor = db.cursor()

    # Total sessions conducted for this subject
    cursor.execute("SELECT COUNT(*) FROM attendance_sessions WHERE subject_id = ?", (subject_id,))
    total_conducted = cursor.fetchone()[0]

    cursor.execute("""
        SELECT s.id as student_id, s.roll_number, u.full_name, u.email,
               COUNT(ar.id) as student_conducted,
               SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) as attended,
               SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) as missed
        FROM students s
        JOIN users u ON s.user_id = u.id
        JOIN student_subjects ss ON s.id = ss.student_id
        LEFT JOIN attendance_sessions ses ON ses.subject_id = ss.subject_id
        LEFT JOIN attendance_records ar ON (ar.session_id = ses.id AND ar.student_id = s.id)
        WHERE ss.subject_id = ? AND u.is_active = 1
        GROUP BY s.id
        ORDER BY s.roll_number ASC
    """, (subject_id,))

    rows = []
    for r in cursor.fetchall():
        d = dict(r)
        conducted = total_conducted
        attended = d['attended'] or 0
        missed = conducted - attended
        if conducted > 0:
            pct = round((attended / conducted * 100), 1)
            is_defaulter = pct < Config.ATTENDANCE_THRESHOLD
            pct_display = f"{pct}%"
        else:
            pct = None
            is_defaulter = False
            pct_display = "N/A"
        d['total_conducted'] = conducted
        d['attended'] = attended
        d['missed'] = missed
        d['percentage'] = pct
        d['percentage_display'] = pct_display
        d['is_defaulter'] = is_defaulter
        rows.append(d)

    return total_conducted, rows

# ==========================================
# STUDENT QUERIES
# ==========================================

def get_student_dashboard_data(student_user_id):
    """
    Computes student's overall attendance, subject-wise attendance,
    and eligibility status.
    """
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT s.*, u.full_name, u.email, u.phone
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.user_id = ?
    """, (student_user_id,))
    student = cursor.fetchone()
    if not student:
        return None

    student_id = student['id']

    # Subject-wise attendance calculation
    cursor.execute("""
        SELECT s.id as subject_id, s.code as subject_code, s.name as subject_name,
               s.credits, uf.full_name as faculty_name,
               COUNT(ses.id) as total_conducted,
               SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) as attended,
               SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) as missed
        FROM student_subjects ss
        JOIN subjects s ON ss.subject_id = s.id
        LEFT JOIN faculty_subjects fs ON s.id = fs.subject_id
        LEFT JOIN faculty f ON fs.faculty_id = f.id
        LEFT JOIN users uf ON f.user_id = uf.id
        LEFT JOIN attendance_sessions ses ON ses.subject_id = s.id
        LEFT JOIN attendance_records ar ON (ar.session_id = ses.id AND ar.student_id = ?)
        WHERE ss.student_id = ?
        GROUP BY s.id
        ORDER BY s.code ASC
    """, (student_id, student_id))

    subjects_summary = []
    total_all_conducted = 0
    total_all_attended = 0

    for r in cursor.fetchall():
        conducted = r['total_conducted'] or 0
        attended = r['attended'] or 0
        missed = conducted - attended
        if conducted > 0:
            pct = round((attended / conducted * 100), 1)
            is_defaulter = pct < Config.ATTENDANCE_THRESHOLD
            pct_display = f"{pct}%"
        else:
            pct = None
            is_defaulter = False
            pct_display = "N/A"

        total_all_conducted += conducted
        total_all_attended += attended

        # Calculate how many classes student needs to attend to reach 75%
        # Or how many classes student can afford to miss without dropping below 75%
        advice = ""
        if conducted > 0:
            if pct < Config.ATTENDANCE_THRESHOLD:
                # Need: (attended + x) / (conducted + x) >= 0.75 => x >= (0.75 * conducted - attended) / (1 - 0.75)
                needed = int(((0.75 * conducted) - attended) / 0.25 + 0.999)
                needed = max(needed, 1)
                advice = f"Attend next {needed} consecutive class{'es' if needed > 1 else ''} to reach 75%."
            else:
                # Can miss: (attended) / (conducted + y) >= 0.75 => y <= (attended / 0.75) - conducted
                can_miss = int((attended / 0.75) - conducted)
                if can_miss > 0:
                    advice = f"You can afford to miss {can_miss} class{'es' if can_miss > 1 else ''} safely."
                else:
                    advice = "Borderline attendance. Do not miss the next class!"
        else:
            advice = "No classes conducted yet."

        subjects_summary.append({
            'subject_id': r['subject_id'],
            'subject_code': r['subject_code'],
            'subject_name': r['subject_name'],
            'credits': r['credits'],
            'faculty_name': r['faculty_name'] or 'Department Faculty',
            'conducted': conducted,
            'attended': attended,
            'missed': missed,
            'percentage': pct,
            'percentage_display': pct_display,
            'is_defaulter': is_defaulter,
            'advice': advice
        })

    overall_conducted = total_all_conducted
    overall_attended = total_all_attended
    overall_missed = overall_conducted - overall_attended
    if overall_conducted > 0:
        overall_pct = round((overall_attended / overall_conducted * 100), 1)
        overall_defaulter = overall_pct < Config.ATTENDANCE_THRESHOLD
        overall_pct_display = f"{overall_pct}%"
    else:
        overall_pct = None
        overall_defaulter = False
        overall_pct_display = "N/A"

    return {
        'student': dict(student),
        'overall_conducted': overall_conducted,
        'overall_attended': overall_attended,
        'overall_missed': overall_missed,
        'overall_pct': overall_pct,
        'overall_pct_display': overall_pct_display,
        'is_defaulter': overall_defaulter,
        'threshold': Config.ATTENDANCE_THRESHOLD,
        'subjects': subjects_summary
    }

def get_student_full_attendance_history(student_user_id, subject_id=None, status=None, date_from=None, date_to=None):
    """Retrieves detailed lecture-by-lecture history for the student."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("SELECT id FROM students WHERE user_id = ?", (student_user_id,))
    st_row = cursor.fetchone()
    if not st_row:
        return []
    student_id = st_row['id']

    query = """
        SELECT ar.id, ar.status, ar.remarks,
               ses.session_date, ses.session_slot, ses.topic,
               s.code as subject_code, s.name as subject_name,
               u.full_name as faculty_name
        FROM attendance_records ar
        JOIN attendance_sessions ses ON ar.session_id = ses.id
        JOIN subjects s ON ses.subject_id = s.id
        JOIN faculty f ON ses.faculty_id = f.id
        JOIN users u ON f.user_id = u.id
        WHERE ar.student_id = ?
    """
    params = [student_id]

    if subject_id:
        query += " AND s.id = ?"
        params.append(subject_id)

    if status and status in ('Present', 'Absent'):
        query += " AND ar.status = ?"
        params.append(status)

    if date_from:
        query += " AND ses.session_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND ses.session_date <= ?"
        params.append(date_to)

    query += " ORDER BY ses.session_date DESC, ses.session_slot DESC"

    cursor.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]

# ==========================================
# REPORTING & EXPORT HELPERS
# ==========================================

def get_defaulter_list_system_wide():
    """Returns list of students below 75% attendance overall and subject-wise."""
    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT s.id, s.roll_number, s.department, s.semester, s.section,
               u.full_name, u.email, u.phone,
               COUNT(ar.id) as total_classes,
               SUM(CASE WHEN ar.status = 'Present' THEN 1 ELSE 0 END) as attended,
               SUM(CASE WHEN ar.status = 'Absent' THEN 1 ELSE 0 END) as missed
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN attendance_records ar ON s.id = ar.student_id
        WHERE u.is_active = 1
        GROUP BY s.id
        ORDER BY s.roll_number ASC
    """)

    defaulters = []
    for row in cursor.fetchall():
        total = row['total_classes'] or 0
        att = row['attended'] or 0
        pct = round((att / total * 100), 1) if total > 0 else 100.0
        if pct < Config.ATTENDANCE_THRESHOLD:
            d = dict(row)
            d['percentage'] = pct
            d['shortage'] = round(Config.ATTENDANCE_THRESHOLD - pct, 1)
            defaulters.append(d)

    return defaulters
