import csv
import io
from functools import wraps
from datetime import datetime, date
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, g, make_response, abort
)
from config import Config
import database
import models

app = Flask(__name__)
app.config.from_object(Config)

# Register database teardown
app.teardown_appcontext(database.close_db)

# ==========================================
# AUTHENTICATION & ROLE DECORATORS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login', next=request.url))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash("Access denied. You do not have permission to view this resource.", "danger")
                if user_role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user_role == 'faculty':
                    return redirect(url_for('faculty_dashboard'))
                elif user_role == 'student':
                    return redirect(url_for('student_dashboard'))
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.context_processor
def inject_global_vars():
    """Injects user session data and settings into all Jinja2 templates."""
    return {
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role': session.get('role'),
            'full_name': session.get('full_name'),
            'roll_number': session.get('roll_number'),
            'faculty_id': session.get('faculty_id')
        },
        'now': datetime.now(),
        'today_date': date.today().strftime('%Y-%m-%d'),
        'attendance_threshold': Config.ATTENDANCE_THRESHOLD
    }

# ==========================================
# PUBLIC & AUTHENTICATION ROUTES
# ==========================================

@app.route('/')
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        elif role == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username_or_email = request.form.get('username_or_email', '').strip()
        password = request.form.get('password', '').strip()

        if not username_or_email or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template('auth/login.html')

        user, err = models.authenticate_user(username_or_email, password)
        if err:
            flash(err, "danger")
            return render_template('auth/login.html')

        # Set session
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        session['email'] = user['email']

        # Fetch role specific info
        user_details = models.get_user_by_id(user['id'])
        if user['role'] == 'student' and 'student_details' in user_details:
            session['roll_number'] = user_details['student_details']['roll_number']
        elif user['role'] == 'faculty' and 'faculty_details' in user_details:
            session['faculty_id'] = user_details['faculty_details']['faculty_id']

        flash(f"Welcome back, {user['full_name']}!", "success")

        next_url = request.args.get('next')
        if next_url and next_url.startswith('/'):
            return redirect(next_url)

        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif user['role'] == 'faculty':
            return redirect(url_for('faculty_dashboard'))
        elif user['role'] == 'student':
            return redirect(url_for('student_dashboard'))

    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    subjects = models.get_all_subjects()

    if request.method == 'POST':
        role = request.form.get('role', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        phone = request.form.get('phone', '').strip()

        # Basic validations
        if role not in ('admin', 'faculty', 'student'):
            flash("Invalid role selected.", "danger")
            return render_template('auth/register.html', subjects=subjects)

        if not full_name or not username or not email or not password:
            flash("All mandatory fields must be filled.", "danger")
            return render_template('auth/register.html', subjects=subjects)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('auth/register.html', subjects=subjects)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('auth/register.html', subjects=subjects)

        extra_data = {}

        # Role specific security and fields
        if role == 'admin':
            admin_key = request.form.get('admin_key', '').strip()
            if admin_key != Config.ADMIN_REGISTRATION_KEY:
                flash("Invalid Administrator Security Key. Authorization failed.", "danger")
                return render_template('auth/register.html', subjects=subjects)

        elif role == 'student':
            roll_number = request.form.get('roll_number', '').strip().upper()
            if not roll_number:
                flash("Roll number is required for student registration.", "danger")
                return render_template('auth/register.html', subjects=subjects)
            extra_data['roll_number'] = roll_number
            extra_data['department'] = request.form.get('department', 'Computer Science & Engineering')
            extra_data['semester'] = request.form.get('semester', 6)
            extra_data['section'] = request.form.get('section', 'A').strip().upper()
            extra_data['batch_year'] = request.form.get('batch_year', '2022-2026')

        elif role == 'faculty':
            faculty_id = request.form.get('faculty_id', '').strip().upper()
            if not faculty_id:
                flash("Faculty ID is required for faculty registration.", "danger")
                return render_template('auth/register.html', subjects=subjects)
            extra_data['faculty_id'] = faculty_id
            extra_data['department'] = request.form.get('department', 'Computer Science & Engineering')
            extra_data['designation'] = request.form.get('designation', 'Assistant Professor')
            extra_data['subject_id'] = request.form.get('subject_id')

        # Create user
        user_id, err = models.create_user_with_role(
            username=username,
            email=email,
            password=password,
            role=role,
            full_name=full_name,
            phone=phone,
            extra_data=extra_data
        )

        if err:
            flash(err, "danger")
            return render_template('auth/register.html', subjects=subjects)

        flash(f"Account for {full_name} ({role.capitalize()}) registered successfully! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('auth/register.html', subjects=subjects)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('login'))

# ==========================================
# ADMIN DASHBOARD & MANAGEMENT ROUTES
# ==========================================

@app.route('/admin')
@role_required('admin')
def admin_dashboard():
    stats = models.get_admin_dashboard_stats()
    recent_sessions = models.get_faculty_sessions_history(limit=8)
    subjects = models.get_all_subjects()
    defaulters = models.get_defaulter_list_system_wide()[:5]  # Top 5 for preview
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_sessions=recent_sessions,
        subjects=subjects,
        defaulters=defaulters
    )

@app.route('/admin/users')
@role_required('admin')
def admin_users():
    role_filter = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip()
    users = models.get_all_users(role=role_filter if role_filter else None, search=search if search else None)
    return render_template('admin/users.html', users=users, selected_role=role_filter, search=search)

@app.route('/admin/users/create', methods=['GET', 'POST'])
@role_required('admin')
def admin_create_user():
    subjects = models.get_all_subjects()
    if request.method == 'POST':
        role = request.form.get('role', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        phone = request.form.get('phone', '').strip()

        if role not in ('admin', 'faculty', 'student'):
            flash("Invalid role selected.", "danger")
            return render_template('admin/user_form.html', mode='create', subjects=subjects)

        if not full_name or not username or not email or not password:
            flash("Full name, username, email, and password are required.", "danger")
            return render_template('admin/user_form.html', mode='create', subjects=subjects)

        extra_data = {}
        if role == 'student':
            extra_data['roll_number'] = request.form.get('roll_number', '').strip().upper()
            extra_data['department'] = request.form.get('department', 'Computer Science & Engineering')
            extra_data['semester'] = request.form.get('semester', 6)
            extra_data['section'] = request.form.get('section', 'A')
            extra_data['batch_year'] = request.form.get('batch_year', '2022-2026')
        elif role == 'faculty':
            extra_data['faculty_id'] = request.form.get('faculty_id', '').strip().upper()
            extra_data['department'] = request.form.get('department', 'Computer Science & Engineering')
            extra_data['designation'] = request.form.get('designation', 'Assistant Professor')
            extra_data['subject_id'] = request.form.get('subject_id')

        uid, err = models.create_user_with_role(username, email, password, role, full_name, phone, extra_data)
        if err:
            flash(err, "danger")
            return render_template('admin/user_form.html', mode='create', subjects=subjects)

        flash(f"User {full_name} created successfully.", "success")
        return redirect(url_for('admin_users'))

    return render_template('admin/user_form.html', mode='create', subjects=subjects)

@app.route('/admin/users/edit/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def admin_edit_user(user_id):
    user = models.get_user_by_id(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('admin_users'))

    subjects = models.get_all_subjects()

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        is_active = 1 if request.form.get('is_active') == '1' else 0

        extra_data = {}
        if user['role'] == 'student':
            extra_data['roll_number'] = request.form.get('roll_number', '').strip().upper()
            extra_data['department'] = request.form.get('department', 'Computer Science & Engineering')
            extra_data['semester'] = request.form.get('semester', 6)
            extra_data['section'] = request.form.get('section', 'A')
            extra_data['batch_year'] = request.form.get('batch_year', '2022-2026')
        elif user['role'] == 'faculty':
            extra_data['faculty_id'] = request.form.get('faculty_id', '').strip().upper()
            extra_data['department'] = request.form.get('department', 'Computer Science & Engineering')
            extra_data['designation'] = request.form.get('designation', 'Assistant Professor')

        success, msg = models.update_user_details(user_id, full_name, email, phone, extra_data, is_active)
        if success:
            flash(msg, "success")
            return redirect(url_for('admin_users'))
        else:
            flash(msg, "danger")

    return render_template('admin/user_form.html', mode='edit', user=user, subjects=subjects)

@app.route('/admin/users/toggle-status/<int:user_id>', methods=['POST'])
@role_required('admin')
def admin_toggle_user_status(user_id):
    success, msg = models.toggle_user_active_status(user_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@role_required('admin')
def admin_delete_user(user_id):
    success, msg = models.delete_user_by_id(user_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('admin_users'))

@app.route('/admin/subjects')
@role_required('admin')
def admin_subjects():
    subjects = models.get_all_subjects()
    return render_template('admin/subjects.html', subjects=subjects)

@app.route('/admin/subjects/create', methods=['GET', 'POST'])
@role_required('admin')
def admin_create_subject():
    faculty_list = models.get_all_users(role='faculty')
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        name = request.form.get('name', '').strip()
        dept = request.form.get('department', 'Computer Science & Engineering').strip()
        semester = int(request.form.get('semester', 6))
        credits = int(request.form.get('credits', 4))
        faculty_id = request.form.get('faculty_id')

        if not code or not name:
            flash("Subject code and name are required.", "danger")
            return render_template('admin/subject_form.html', mode='create', faculty_list=faculty_list)

        success, msg = models.save_subject(code, name, dept, semester, credits, faculty_id)
        if success:
            flash(msg, "success")
            return redirect(url_for('admin_subjects'))
        else:
            flash(msg, "danger")

    return render_template('admin/subject_form.html', mode='create', faculty_list=faculty_list)

@app.route('/admin/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@role_required('admin')
def admin_edit_subject(subject_id):
    subject = models.get_subject_by_id(subject_id)
    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for('admin_subjects'))

    faculty_list = models.get_all_users(role='faculty')

    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        name = request.form.get('name', '').strip()
        dept = request.form.get('department', 'Computer Science & Engineering').strip()
        semester = int(request.form.get('semester', 6))
        credits = int(request.form.get('credits', 4))
        faculty_id = request.form.get('faculty_id')

        if not code or not name:
            flash("Subject code and name are required.", "danger")
            return render_template('admin/subject_form.html', mode='edit', subject=subject, faculty_list=faculty_list)

        success, msg = models.save_subject(code, name, dept, semester, credits, faculty_id, subject_id=subject_id)
        if success:
            flash(msg, "success")
            return redirect(url_for('admin_subjects'))
        else:
            flash(msg, "danger")

    return render_template('admin/subject_form.html', mode='edit', subject=subject, faculty_list=faculty_list)

@app.route('/admin/subjects/delete/<int:subject_id>', methods=['POST'])
@role_required('admin')
def admin_delete_subject(subject_id):
    success, msg = models.delete_subject_by_id(subject_id)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('admin_subjects'))

@app.route('/admin/attendance')
@role_required('admin')
def admin_attendance():
    subject_id = request.args.get('subject_id', type=int)
    sessions = models.get_faculty_sessions_history(subject_id=subject_id, limit=100)
    subjects = models.get_all_subjects()
    return render_template('admin/attendance_logs.html', sessions=sessions, subjects=subjects, selected_subject_id=subject_id)

@app.route('/admin/reports')
@role_required('admin')
def admin_reports():
    subjects = models.get_all_subjects()
    defaulters = models.get_defaulter_list_system_wide()
    stats = models.get_admin_dashboard_stats()
    return render_template('admin/reports.html', subjects=subjects, defaulters=defaulters, stats=stats)

@app.route('/admin/reports/export/defaulters')
@role_required('admin')
def export_defaulters_csv():
    defaulters = models.get_defaulter_list_system_wide()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Roll Number', 'Student Name', 'Email', 'Department', 'Total Classes', 'Attended', 'Missed', 'Attendance %', 'Shortage %', 'Status'])
    for d in defaulters:
        cw.writerow([
            d['roll_number'],
            d['full_name'],
            d['email'],
            d['department'],
            d['total_classes'],
            d['attended'],
            d['missed'],
            f"{d['percentage']}%",
            f"{d['shortage']}%",
            'Defaulter (< 75%)'
        ])
    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = f"attachment; filename=ams_defaulters_list_{date.today().strftime('%Y%m%d')}.csv"
    response.headers['Content-type'] = 'text/csv'
    return response

# ==========================================
# FACULTY DASHBOARD & ATTENDANCE ROUTES
# ==========================================

@app.route('/faculty')
@role_required('faculty')
def faculty_dashboard():
    faculty_user_id = session.get('user_id')
    assigned_subjects = models.get_faculty_assigned_subjects(faculty_user_id)
    recent_sessions = models.get_faculty_sessions_history(faculty_user_id=faculty_user_id, limit=10)
    return render_template(
        'faculty/dashboard.html',
        assigned_subjects=assigned_subjects,
        recent_sessions=recent_sessions
    )

@app.route('/faculty/mark-attendance', methods=['GET', 'POST'])
@role_required('faculty')
def faculty_mark_attendance():
    faculty_user_id = session.get('user_id')
    assigned_subjects = models.get_faculty_assigned_subjects(faculty_user_id)

    if not assigned_subjects:
        flash("You are not currently assigned to any subjects. Please contact the administrator.", "warning")
        return redirect(url_for('faculty_dashboard'))

    # Determine which subject to load
    subject_id = request.args.get('subject_id', type=int)
    if not subject_id and assigned_subjects:
        subject_id = assigned_subjects[0]['id']

    students = models.get_students_for_subject(subject_id)

    if request.method == 'POST':
        selected_subject_id = int(request.form.get('subject_id', subject_id))
        session_date = request.form.get('session_date', date.today().strftime('%Y-%m-%d'))
        session_slot = request.form.get('session_slot', '09:00 - 10:00 AM')
        topic = request.form.get('topic', 'Course Lecture Topic')

        # Safeguard: Check if attendance for this subject, date and slot already exists
        existing = models.check_existing_session(selected_subject_id, session_date, session_slot)
        if existing:
            flash(
                f"Attendance for this subject on {session_date} ({session_slot}) has already been recorded! "
                f"You can edit the existing session instead.",
                "warning"
            )
            return redirect(url_for('faculty_edit_attendance', session_id=existing['id']))

        # Extract student attendance statuses from form
        attendance_status_dict = {}
        for st in students:
            st_id_str = str(st['student_id'])
            # Radio button format: status_STUDENT_ID = 'Present' or 'Absent'
            status_val = request.form.get(f'status_{st_id_str}', 'Absent')
            attendance_status_dict[st_id_str] = status_val

        success, result = models.record_attendance_session(
            subject_id=selected_subject_id,
            faculty_user_id=faculty_user_id,
            session_date=session_date,
            session_slot=session_slot,
            topic=topic,
            attendance_status_dict=attendance_status_dict
        )

        if success:
            flash(f"Attendance recorded successfully for {session_date} ({len(students)} students processed)!", "success")
            return redirect(url_for('faculty_session_history', subject_id=selected_subject_id))
        else:
            flash(result, "danger")

    return render_template(
        'faculty/mark_attendance.html',
        assigned_subjects=assigned_subjects,
        selected_subject_id=subject_id,
        students=students,
        current_date=date.today().strftime('%Y-%m-%d')
    )

@app.route('/faculty/edit-attendance/<int:session_id>', methods=['GET', 'POST'])
@role_required('faculty', 'admin')
def faculty_edit_attendance(session_id):
    session_data, records = models.get_session_details(session_id)
    if not session_data:
        flash("Attendance session not found.", "danger")
        return redirect(url_for('faculty_dashboard'))

    if request.method == 'POST':
        session_date = request.form.get('session_date', session_data['session_date'])
        session_slot = request.form.get('session_slot', session_data['session_slot'])
        topic = request.form.get('topic', session_data['topic'])

        attendance_status_dict = {}
        for rec in records:
            st_id_str = str(rec['student_id'])
            status_val = request.form.get(f'status_{st_id_str}', 'Absent')
            attendance_status_dict[st_id_str] = status_val

        success, msg = models.update_existing_attendance_session(
            session_id=session_id,
            session_date=session_date,
            session_slot=session_slot,
            topic=topic,
            attendance_status_dict=attendance_status_dict
        )

        if success:
            flash("Attendance records updated successfully.", "success")
            if session.get('role') == 'admin':
                return redirect(url_for('admin_attendance'))
            return redirect(url_for('faculty_session_history', subject_id=session_data['subject_id']))
        else:
            flash(msg, "danger")

    return render_template('faculty/edit_attendance.html', session_data=session_data, records=records)

@app.route('/faculty/session/<int:session_id>')
@login_required
def faculty_view_session(session_id):
    session_data, records = models.get_session_details(session_id)
    if not session_data:
        flash("Session not found.", "danger")
        return redirect(url_for('faculty_dashboard'))

    present_count = sum(1 for r in records if r['status'] == 'Present')
    absent_count = len(records) - present_count
    pct = round((present_count / len(records) * 100), 1) if records else 0

    return render_template(
        'faculty/session_view.html',
        session_data=session_data,
        records=records,
        present_count=present_count,
        absent_count=absent_count,
        pct=pct
    )

@app.route('/faculty/sessions')
@role_required('faculty')
def faculty_session_history():
    faculty_user_id = session.get('user_id')
    subject_id = request.args.get('subject_id', type=int)
    assigned_subjects = models.get_faculty_assigned_subjects(faculty_user_id)
    sessions = models.get_faculty_sessions_history(faculty_user_id=faculty_user_id, subject_id=subject_id, limit=100)
    return render_template(
        'faculty/session_history.html',
        sessions=sessions,
        assigned_subjects=assigned_subjects,
        selected_subject_id=subject_id
    )

@app.route('/faculty/subject-stats/<int:subject_id>')
@role_required('faculty', 'admin')
def faculty_subject_stats(subject_id):
    subject = models.get_subject_by_id(subject_id)
    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for('faculty_dashboard'))

    total_conducted, student_rows = models.get_subject_student_attendance_summary(subject_id)
    defaulter_count = sum(1 for s in student_rows if s['is_defaulter'])
    avg_pct = round(sum(s['percentage'] for s in student_rows) / len(student_rows), 1) if student_rows else 0.0

    return render_template(
        'faculty/subject_stats.html',
        subject=subject,
        total_conducted=total_conducted,
        student_rows=student_rows,
        defaulter_count=defaulter_count,
        avg_pct=avg_pct
    )

@app.route('/faculty/reports/export/<int:subject_id>')
@role_required('faculty', 'admin')
def export_subject_csv(subject_id):
    subject = models.get_subject_by_id(subject_id)
    if not subject:
        flash("Subject not found.", "danger")
        return redirect(url_for('faculty_dashboard'))

    total_conducted, student_rows = models.get_subject_student_attendance_summary(subject_id)

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([f"Attendance Register - {subject['name']} ({subject['code']})"])
    cw.writerow([f"Total Lectures Conducted: {total_conducted}", f"Generated On: {date.today().strftime('%Y-%m-%d')}"])
    cw.writerow([])
    cw.writerow(['Roll Number', 'Student Name', 'Email', 'Lectures Conducted', 'Lectures Attended', 'Lectures Missed', 'Attendance %', 'Status'])

    for s in student_rows:
        status_text = 'Defaulter (< 75%)' if s['is_defaulter'] else 'Eligible'
        cw.writerow([
            s['roll_number'],
            s['full_name'],
            s['email'],
            s['total_conducted'],
            s['attended'],
            s['missed'],
            f"{s['percentage']}%",
            status_text
        ])

    response = make_response(si.getvalue())
    response.headers['Content-Disposition'] = f"attachment; filename=ams_{subject['code']}_attendance.csv"
    response.headers['Content-type'] = 'text/csv'
    return response

# ==========================================
# STUDENT DASHBOARD & HISTORY ROUTES
# ==========================================

@app.route('/student')
@role_required('student')
def student_dashboard():
    student_user_id = session.get('user_id')
    data = models.get_student_dashboard_data(student_user_id)
    if not data:
        flash("Student profile not found. Please contact administration.", "danger")
        return redirect(url_for('logout'))

    recent_history = models.get_student_full_attendance_history(student_user_id)[:10]

    return render_template(
        'student/dashboard.html',
        data=data,
        recent_history=recent_history
    )

@app.route('/student/history')
@role_required('student')
def student_history():
    student_user_id = session.get('user_id')
    subject_id = request.args.get('subject_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    subjects = models.get_all_subjects()
    history = models.get_student_full_attendance_history(
        student_user_id,
        subject_id=subject_id if subject_id else None,
        status=status if status in ('Present', 'Absent') else None,
        date_from=date_from if date_from else None,
        date_to=date_to if date_to else None
    )

    present_count = sum(1 for h in history if h['status'] == 'Present')
    absent_count = sum(1 for h in history if h['status'] == 'Absent')
    total_classes = len(history)
    filter_pct = round((present_count / total_classes * 100), 1) if total_classes > 0 else 0.0

    return render_template(
        'student/history.html',
        history=history,
        subjects=subjects,
        selected_subject_id=subject_id,
        selected_status=status,
        date_from=date_from,
        date_to=date_to,
        present_count=present_count,
        absent_count=absent_count,
        total_classes=total_classes,
        filter_pct=filter_pct
    )

# ==========================================
# COMMON & SEPM DOCUMENTATION ROUTES
# ==========================================

@app.route('/profile')
@login_required
def user_profile():
    user = models.get_user_by_id(session['user_id'])
    return render_template('common/profile.html', user=user)

@app.route('/sepm-docs')
def sepm_docs():
    """Renders the comprehensive SEPM Project Report directly within the web app."""
    return render_template('common/sepm_docs.html')

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# ==========================================
# INITIALIZATION RUNNER
# ==========================================

if __name__ == '__main__':
    with app.app_context():
        database.init_db()
        database.seed_database_if_empty()
    print("Starting Attendance Management System on http://127.0.0.1:5000 ...")
    app.run(host='127.0.0.1', port=5000, debug=True)
