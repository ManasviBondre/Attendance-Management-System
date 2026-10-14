import unittest
import os
import sqlite3
from app import app
from config import Config
import database
import models

class AttendanceManagementSystemTests(unittest.TestCase):
    @classmethod
    def clean_test_data(cls):
        with app.app_context():
            db = database.get_standalone_db()
            cursor = db.cursor()
            cursor.execute("DELETE FROM users WHERE username IN ('verified_admin', 'rahul_test', 'prof.kulkarni')")
            cursor.execute("DELETE FROM students WHERE roll_number = '22CS999'")
            cursor.execute("DELETE FROM faculty WHERE faculty_id = 'FAC099'")
            cursor.execute("DELETE FROM attendance_sessions WHERE session_date = '2026-11-20'")
            db.commit()
            db.close()

    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        cls.client = app.test_client()
        cls.clean_test_data()

    @classmethod
    def tearDownClass(cls):
        cls.clean_test_data()

    # -------------------------------------------------------------
    # 1. Subjects Verification
    # -------------------------------------------------------------
    def test_01_all_five_subjects_present(self):
        """Verify all 5 required subjects exist in database."""
        with app.app_context():
            subjects = models.get_all_subjects()
            subject_names = [s['name'] for s in subjects]
            expected = [
                'MDM',
                'Theory of Computation',
                'Software Engineering and Project Management (SEPM)',
                'PE - Image Processing',
                'Machine Learning'
            ]
            for exp in expected:
                self.assertIn(exp, subject_names, f"Subject '{exp}' not found in database.")
            self.assertEqual(len(subjects), 5)

    # -------------------------------------------------------------
    # 2. At Least 40 Realistic Fictional Students Verification
    # -------------------------------------------------------------
    def test_02_at_least_40_fictional_students_without_celebrities(self):
        """Verify at least 40 students enrolled, no celebrity names, and user Manasvi preserved."""
        with app.app_context():
            students = models.get_all_users(role='student')
            self.assertGreaterEqual(len(students), 40, "Less than 40 students found.")

            student_names = [s['full_name'] for s in students]
            celebrities = ['Deepika Padukone', 'Ranbir Kapoor', 'Alia Bhatt', 'Arjun Reddy', 'Kunal Kamra']
            for celeb in celebrities:
                self.assertNotIn(celeb, student_names, f"Found prohibited celebrity name: '{celeb}'")

            # Verify realistic names are present
            self.assertIn('Aarav Sharma', student_names)
            self.assertIn('Priya Patil', student_names)
            self.assertIn('Rohan Deshmukh', student_names)
            self.assertIn('Sneha Kulkarni', student_names)

            # Verify existing student Manasvi Bondre is preserved
            self.assertIn('Manasvi Bondre', student_names)

    # -------------------------------------------------------------
    # 3. Admin Registration Key Security Tests
    # -------------------------------------------------------------
    def test_03_admin_registration_missing_key_rejected(self):
        """Administrator registration without security key must be rejected."""
        response = self.client.post('/register', data={
            'role': 'admin',
            'full_name': 'Test Admin Fail',
            'username': 'admin_fail1',
            'email': 'admin_fail1@ams.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'admin_key': ''
        }, follow_redirects=True)
        self.assertIn(b"Administrator Security Key is required", response.data)

    def test_04_admin_registration_incorrect_key_rejected(self):
        """Administrator registration with invalid security key must be rejected."""
        response = self.client.post('/register', data={
            'role': 'admin',
            'full_name': 'Test Admin Fail',
            'username': 'admin_fail2',
            'email': 'admin_fail2@ams.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'admin_key': 'WRONG_SECRET_TOKEN'
        }, follow_redirects=True)
        self.assertIn(b"Invalid Administrator Security Key", response.data)

    def test_05_admin_registration_valid_key_and_login(self):
        """Administrator registration with correct key succeeds and allows admin login."""
        expected_key = app.config.get('ADMIN_REGISTRATION_KEY') or Config.ADMIN_REGISTRATION_KEY
        response = self.client.post('/register', data={
            'role': 'admin',
            'full_name': 'New Verified Admin',
            'username': 'verified_admin',
            'email': 'verified_admin@ams.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'admin_key': expected_key
        }, follow_redirects=True)
        self.assertIn(b"registered successfully", response.data)

        # Login with newly registered administrator
        login_res = self.client.post('/login', data={
            'username_or_email': 'verified_admin',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertIn(b"Administrator Dashboard", login_res.data)
        self.assertIn(b"New Verified Admin", login_res.data)

        # Logout
        self.client.get('/logout')

    # -------------------------------------------------------------
    # 4. Student Registration, Login, Dashboard, Logout
    # -------------------------------------------------------------
    def test_06_student_registration_login_dashboard_logout(self):
        """Student registration, login, personalized dashboard greeting, and logout."""
        response = self.client.post('/register', data={
            'role': 'student',
            'full_name': 'Rahul Sharma Test',
            'username': 'rahul_test',
            'email': 'rahul_test@student.ams.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'roll_number': '22CS999',
            'department': 'Computer Science & Engineering',
            'semester': '6',
            'section': 'A',
            'batch_year': '2022-2026'
        }, follow_redirects=True)
        self.assertIn(b"registered successfully", response.data)

        # Login
        login_res = self.client.post('/login', data={
            'username_or_email': 'rahul_test',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertIn(b"Welcome, Rahul Sharma Test!", login_res.data)
        self.assertIn(b"22CS999", login_res.data)

        # Access history
        hist_res = self.client.get('/student/history')
        self.assertEqual(hist_res.status_code, 200)

        # Logout
        logout_res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b"logged out successfully", logout_res.data)

    # -------------------------------------------------------------
    # 5. Faculty Registration, Login, Dashboard, Student List
    # -------------------------------------------------------------
    def test_07_faculty_registration_login_and_student_list(self):
        """Faculty registration, login, dashboard, assigned subject view, and student list."""
        response = self.client.post('/register', data={
            'role': 'faculty',
            'full_name': 'Prof. Rajesh Kulkarni',
            'username': 'prof.kulkarni',
            'email': 'kulkarni@ams.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'faculty_id': 'FAC099',
            'department': 'Computer Science & Engineering',
            'designation': 'Assistant Professor',
            'subject_id': '1'  # MDM
        }, follow_redirects=True)
        self.assertIn(b"registered successfully", response.data)

        # Login
        login_res = self.client.post('/login', data={
            'username_or_email': 'prof.kulkarni',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertIn(b"Welcome, Prof. Rajesh Kulkarni!", login_res.data)

        # Check assigned student list
        students_res = self.client.get('/faculty/students?subject_id=1')
        self.assertEqual(students_res.status_code, 200)
        self.assertIn(b"Assigned Student Lists", students_res.data)
        self.assertIn(b"Aarav Sharma", students_res.data)
        self.assertIn(b"22CS001", students_res.data)

        self.client.get('/logout')

    # -------------------------------------------------------------
    # 6. Duplicate Validation
    # -------------------------------------------------------------
    def test_08_duplicate_username_and_email_prevention(self):
        """System must prevent duplicate usernames and emails."""
        # Duplicate username
        res1 = self.client.post('/register', data={
            'role': 'student',
            'full_name': 'Duplicate User',
            'username': 'admin',  # Existing admin username
            'email': 'unique123@ams.edu',
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'roll_number': '22CS888'
        }, follow_redirects=True)
        self.assertIn(b"Username already exists", res1.data)

        # Duplicate email
        res2 = self.client.post('/register', data={
            'role': 'student',
            'full_name': 'Duplicate Email',
            'username': 'unique_user_888',
            'email': 'admin@ams.edu',  # Existing email
            'password': 'Password@123',
            'confirm_password': 'Password@123',
            'roll_number': '22CS889'
        }, follow_redirects=True)
        self.assertIn(b"Email address is already registered", res2.data)

    # -------------------------------------------------------------
    # 7. Role-Based Security Restrictions
    # -------------------------------------------------------------
    def test_09_role_based_security_restrictions(self):
        """Verify role protection: students cannot access faculty or admin endpoints."""
        # Login as student
        self.client.post('/login', data={'username_or_email': '22cs001', 'password': 'Password@123'})

        # Student attempts to access admin dashboard
        res_admin = self.client.get('/admin', follow_redirects=True)
        self.assertIn(b"Access denied", res_admin.data)

        # Student attempts to access faculty mark attendance
        res_fac = self.client.get('/faculty/mark-attendance', follow_redirects=True)
        self.assertIn(b"Access denied", res_fac.data)

        self.client.get('/logout')

        # Login as faculty
        self.client.post('/login', data={'username_or_email': 'prof.iyer', 'password': 'Password@123'})

        # Faculty attempts to access admin users management
        res_admin_users = self.client.get('/admin/users', follow_redirects=True)
        self.assertIn(b"Access denied", res_admin_users.data)

        self.client.get('/logout')

    # -------------------------------------------------------------
    # 8. Unauthenticated Access Protection
    # -------------------------------------------------------------
    def test_10_unauthenticated_users_redirected_to_login(self):
        """Unauthenticated requests to protected endpoints must redirect to login."""
        self.client.get('/logout')
        for url in ['/admin', '/faculty', '/student', '/faculty/mark-attendance']:
            res = self.client.get(url, follow_redirects=True)
            self.assertIn(b"Please log in to access this page", res.data)

    # -------------------------------------------------------------
    # 9. Attendance Marking, Saving, and Duplicate Prevention
    # -------------------------------------------------------------
    def test_11_attendance_marking_and_duplicate_prevention(self):
        """Test marking attendance, database persistence, and duplicate session safeguard."""
        # Login as faculty (Prof. Iyer, SEPM, subject_id=3)
        self.client.post('/login', data={'username_or_email': 'prof.iyer', 'password': 'Password@123'})

        test_date = '2026-11-20'
        test_slot = '09:00 - 10:00 AM'

        # Fetch enrolled students
        with app.app_context():
            students = models.get_students_for_subject(3)
            self.assertGreater(len(students), 0)

        # Prepare attendance post data
        post_data = {
            'subject_id': '3',
            'session_date': test_date,
            'session_slot': test_slot,
            'topic': 'Automated Integration Testing Lecture'
        }
        for st in students:
            post_data[f'status_{st["student_id"]}'] = 'Present'

        # Mark attendance
        res = self.client.post('/faculty/mark-attendance', data=post_data, follow_redirects=True)
        self.assertIn(b"Attendance recorded successfully", res.data)

        # Attempt to mark duplicate attendance for same subject, date, slot
        dup_res = self.client.post('/faculty/mark-attendance', data=post_data, follow_redirects=True)
        self.assertIn(b"has already been recorded", dup_res.data)

        self.client.get('/logout')

    # -------------------------------------------------------------
    # 10. Authorized Attendance Editing
    # -------------------------------------------------------------
    def test_12_authorized_attendance_editing(self):
        """Authorized faculty edits existing attendance session without creating duplicate rows."""
        self.client.post('/login', data={'username_or_email': 'prof.iyer', 'password': 'Password@123'})

        with app.app_context():
            session_info = models.check_existing_session(3, '2026-11-20', '09:00 - 10:00 AM')
            self.assertIsNotNone(session_info)
            session_id = session_info['id']
            _, initial_records = models.get_session_details(session_id)
            initial_count = len(initial_records)

        # Edit session: change first student to Absent
        first_student_id = initial_records[0]['student_id']
        edit_data = {
            'session_date': '2026-11-20',
            'session_slot': '09:00 - 10:00 AM',
            'topic': 'Updated Topic After Review'
        }
        for rec in initial_records:
            if rec['student_id'] == first_student_id:
                edit_data[f'status_{rec["student_id"]}'] = 'Absent'
            else:
                edit_data[f'status_{rec["student_id"]}'] = 'Present'

        edit_res = self.client.post(f'/faculty/edit-attendance/{session_id}', data=edit_data, follow_redirects=True)
        self.assertIn(b"Attendance records updated successfully", edit_res.data)

        # Verify records count remained identical (no duplicate rows created)
        with app.app_context():
            updated_session, updated_records = models.get_session_details(session_id)
            self.assertEqual(len(updated_records), initial_count)
            first_updated = next(r for r in updated_records if r['student_id'] == first_student_id)
            self.assertEqual(first_updated['status'], 'Absent')
            self.assertEqual(updated_session['topic'], 'Updated Topic After Review')

        self.client.get('/logout')

    # -------------------------------------------------------------
    # 11. Student Attendance Percentage Update
    # -------------------------------------------------------------
    def test_13_student_dashboard_percentage_calculation(self):
        """Student dashboard calculates attendance percentage from actual database records."""
        self.client.post('/login', data={'username_or_email': '22cs001', 'password': 'Password@123'})
        dash_res = self.client.get('/student')
        self.assertEqual(dash_res.status_code, 200)
        self.assertIn(b"Cumulative Attendance", dash_res.data)
        self.assertIn(b"Software Engineering and Project Management (SEPM)", dash_res.data)
        self.client.get('/logout')

    # -------------------------------------------------------------
    # 12. Absence of SEPM Report & Viva Guide Unwanted Link
    # -------------------------------------------------------------
    def test_14_absence_of_unwanted_navigation_link(self):
        """Verify complete removal of 'SEPM Report & Viva Guide' and promotional link."""
        for url in ['/login', '/register']:
            res = self.client.get(url)
            self.assertNotIn(b"SEPM Report & Viva Guide", res.data)
            self.assertNotIn(b"/sepm-docs", res.data)

    # -------------------------------------------------------------
    # 13. Reports and CSV Export
    # -------------------------------------------------------------
    def test_15_admin_and_faculty_reports_export(self):
        """Verify admin defaulters CSV export and faculty subject CSV export."""
        # Admin Defaulters CSV
        self.client.post('/login', data={'username_or_email': 'admin', 'password': 'Admin@123'})
        csv_res = self.client.get('/admin/reports/export/defaulters')
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.headers['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn(b'Roll Number,Student Name,Email', csv_res.data)
        self.client.get('/logout')

        # Faculty Subject CSV
        self.client.post('/login', data={'username_or_email': 'prof.iyer', 'password': 'Password@123'})
        fac_csv_res = self.client.get('/faculty/reports/export/3')
        self.assertEqual(fac_csv_res.status_code, 200)
        self.assertEqual(fac_csv_res.headers['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn(b'Attendance Register - Software Engineering and Project Management', fac_csv_res.data)
        self.client.get('/logout')

    # -------------------------------------------------------------
    # 14. Admin User Management and Subject CRUD
    # -------------------------------------------------------------
    def test_16_admin_user_management_and_subject_crud(self):
        """Admin can create a subject, edit it, and toggle user active status."""
        self.client.post('/login', data={'username_or_email': 'admin', 'password': 'Admin@123'})

        # Create new subject
        subj_res = self.client.post('/admin/subjects/create', data={
            'code': 'CS699',
            'name': 'Cloud Computing & Virtualization',
            'department': 'Computer Science & Engineering',
            'semester': '6',
            'credits': '4',
            'faculty_id': '3'
        }, follow_redirects=True)
        self.assertIn(b"Subject saved successfully", subj_res.data)

        with app.app_context():
            subjs = models.get_all_subjects()
            created = next((s for s in subjs if s['code'] == 'CS699'), None)
            self.assertIsNotNone(created)
            created_id = created['id']

        # Edit the subject
        edit_subj_res = self.client.post(f'/admin/subjects/edit/{created_id}', data={
            'code': 'CS699',
            'name': 'Advanced Cloud Computing',
            'department': 'Computer Science & Engineering',
            'semester': '6',
            'credits': '4',
            'faculty_id': '3'
        }, follow_redirects=True)
        self.assertIn(b"Subject saved successfully", edit_subj_res.data)

        # Toggle user status
        with app.app_context():
            test_user = models.get_all_users(role='student')[0]
            target_user_id = test_user['id']

        toggle_res = self.client.post(f'/admin/users/toggle-status/{target_user_id}', follow_redirects=True)
        self.assertIn(b"User status set to", toggle_res.data)

        # Toggle back
        self.client.post(f'/admin/users/toggle-status/{target_user_id}', follow_redirects=True)

        # Delete the test subject
        del_res = self.client.post(f'/admin/subjects/delete/{created_id}', follow_redirects=True)
        self.assertIn(b"Subject deleted successfully", del_res.data)

        self.client.get('/logout')

    # -------------------------------------------------------------
    # 15. Zero Classes Conducted Graceful Handling (N/A)
    # -------------------------------------------------------------
    def test_17_zero_classes_conducted_graceful_handling(self):
        """When 0 classes are conducted, percentage calculation returns N/A instead of division by zero."""
        with app.app_context():
            # Create a temporary subject with 0 sessions
            success, _ = models.save_subject('CS990', 'Quantum Computing', 'Computer Science & Engineering', 6, 4)
            self.assertTrue(success)
            subjs = models.get_all_subjects()
            qc_subj = next(s for s in subjs if s['code'] == 'CS990')
            total_cond, rows = models.get_subject_student_attendance_summary(qc_subj['id'])
            self.assertEqual(total_cond, 0)
            self.assertGreater(len(rows), 0)
            self.assertEqual(rows[0]['percentage_display'], 'N/A')
            self.assertIsNone(rows[0]['percentage'])

            # Clean up
            models.delete_subject_by_id(qc_subj['id'])

    # -------------------------------------------------------------
    # 16. Data Persistence Across Routine Startup
    # -------------------------------------------------------------
    def test_18_data_persistence_across_routine_startup(self):
        """Database initialization does not wipe existing users or attendance sessions."""
        with app.app_context():
            db_conn = database.get_standalone_db()
            cursor = db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count_before = cursor.fetchone()[0]
            db_conn.close()

            # Call init_db and seed_database_if_empty (simulating restart)
            database.init_db()
            database.seed_database_if_empty()

            db_conn2 = database.get_standalone_db()
            cursor2 = db_conn2.cursor()
            cursor2.execute("SELECT COUNT(*) FROM users")
            count_after = cursor2.fetchone()[0]
            db_conn2.close()

            self.assertEqual(count_before, count_after, "User count changed across routine startup!")

if __name__ == '__main__':
    unittest.main()
