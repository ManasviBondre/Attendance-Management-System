import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from flask import g, has_app_context
from config import Config

def get_db():
    """Opens a new database connection if there is none yet for the current application context, or returns a standalone connection."""
    if has_app_context():
        if 'db' not in g:
            g.db = sqlite3.connect(
                Config.DATABASE,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db
    return get_standalone_db()

def get_standalone_db():
    """Provides a standalone database connection for initial setup and seed scripts."""
    conn = sqlite3.connect(
        Config.DATABASE,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def close_db(e=None):
    """Closes the database again at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initializes the database schema."""
    conn = get_standalone_db()
    cursor = conn.cursor()

    cursor.executescript("""
    -- 1. Users Table
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'faculty', 'student')),
        full_name TEXT NOT NULL,
        phone TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 2. Students Table
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        roll_number TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL DEFAULT 'Computer Science & Engineering',
        semester INTEGER NOT NULL DEFAULT 6,
        section TEXT NOT NULL DEFAULT 'A',
        batch_year TEXT NOT NULL DEFAULT '2022-2026',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- 3. Faculty Table
    CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER UNIQUE NOT NULL,
        faculty_id TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL DEFAULT 'Computer Science & Engineering',
        designation TEXT NOT NULL DEFAULT 'Assistant Professor',
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    -- 4. Subjects Table
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        department TEXT NOT NULL DEFAULT 'Computer Science & Engineering',
        semester INTEGER NOT NULL DEFAULT 6,
        credits INTEGER NOT NULL DEFAULT 4,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- 5. Faculty Subject Assignments
    CREATE TABLE IF NOT EXISTS faculty_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE (faculty_id, subject_id)
    );

    -- 6. Student Subject Enrollment
    CREATE TABLE IF NOT EXISTS student_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject_id INTEGER NOT NULL,
        enrolled_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        UNIQUE (student_id, subject_id)
    );

    -- 7. Attendance Sessions
    CREATE TABLE IF NOT EXISTS attendance_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_id INTEGER NOT NULL,
        faculty_id INTEGER NOT NULL,
        session_date DATE NOT NULL,
        session_slot TEXT NOT NULL DEFAULT '09:00 - 10:00 AM',
        topic TEXT DEFAULT 'Course Module Discussion',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
        UNIQUE (subject_id, session_date, session_slot)
    );

    -- 8. Attendance Records
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        student_id INTEGER NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
        remarks TEXT,
        FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
        UNIQUE (session_id, student_id)
    );

    -- Indexes for performance
    CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
    CREATE INDEX IF NOT EXISTS idx_students_roll ON students(roll_number);
    CREATE INDEX IF NOT EXISTS idx_faculty_fid ON faculty(faculty_id);
    CREATE INDEX IF NOT EXISTS idx_sessions_subj_date ON attendance_sessions(subject_id, session_date);
    CREATE INDEX IF NOT EXISTS idx_records_session ON attendance_records(session_id);
    CREATE INDEX IF NOT EXISTS idx_records_student ON attendance_records(student_id);
    """)

    conn.commit()
    conn.close()

def seed_database_if_empty():
    """Populates realistic initial data if the database is currently empty."""
    conn = get_standalone_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users;")
    user_count = cursor.fetchone()[0]

    if user_count > 0:
        conn.close()
        return  # Already seeded

    print("[AMS Seed] Seeding database with initial users, subjects, and attendance...")

    # Default common password for test accounts: Password@123
    test_password_hash = generate_password_hash("Password@123")
    admin_password_hash = generate_password_hash("Admin@123")

    # 1. Create Administrator
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, role, full_name, phone)
        VALUES (?, ?, ?, ?, ?, ?);
    """, ('admin', 'admin@ams.edu', admin_password_hash, 'admin', 'System Administrator', '+91 9876543210'))

    # 2. Five Required Subjects
    subjects_data = [
        ('CS601', 'MDM', 'Computer Science & Engineering', 6, 4),
        ('CS602', 'Theory of Computation', 'Computer Science & Engineering', 6, 4),
        ('CS603', 'Software Engineering and Project Management (SEPM)', 'Computer Science & Engineering', 6, 4),
        ('CS604', 'PE - Image Processing', 'Computer Science & Engineering', 6, 3),
        ('CS605', 'Machine Learning', 'Computer Science & Engineering', 6, 4)
    ]
    cursor.executemany("""
        INSERT INTO subjects (code, name, department, semester, credits)
        VALUES (?, ?, ?, ?, ?);
    """, subjects_data)

    # 3. Create 5 Faculty Members
    faculty_data = [
        ('prof.verma', 'arvind.verma@ams.edu', 'Dr. Arvind Verma', 'FAC001', 'Associate Professor', 'CS601'),
        ('dr.sharma', 'rajesh.sharma@ams.edu', 'Dr. Rajesh Sharma', 'FAC002', 'Professor & HOD', 'CS602'),
        ('prof.iyer', 'ananya.iyer@ams.edu', 'Prof. Ananya Iyer', 'FAC003', 'Assistant Professor', 'CS603'),
        ('prof.patel', 'sneha.patel@ams.edu', 'Prof. Sneha Patel', 'FAC004', 'Assistant Professor', 'CS604'),
        ('dr.malhotra', 'vikram.malhotra@ams.edu', 'Dr. Vikram Malhotra', 'FAC005', 'Associate Professor', 'CS605')
    ]

    for uname, email, fname, fid, desig, subj_code in faculty_data:
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name, phone)
            VALUES (?, ?, ?, 'faculty', ?, ?);
        """, (uname, email, test_password_hash, fname, '+91 9811122233'))
        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO faculty (user_id, faculty_id, department, designation)
            VALUES (?, ?, 'Computer Science & Engineering', ?);
        """, (user_id, fid, desig))
        faculty_db_id = cursor.lastrowid

        # Assign to subject
        cursor.execute("SELECT id FROM subjects WHERE code = ?", (subj_code,))
        subj_id = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO faculty_subjects (faculty_id, subject_id)
            VALUES (?, ?);
        """, (faculty_db_id, subj_id))

    # 4. Create 45 Realistic Student Records (exceeding requirement of >= 40)
    student_names = [
        "Aarav Sharma", "Aditi Rao", "Rohan Gupta", "Priya Nair", "Kavya Deshmukh",
        "Siddharth Verma", "Ananya Joshi", "Rahul Mehta", "Sneha Kulkarni", "Vikram Rathore",
        "Pooja Hegde", "Arjun Reddy", "Isha Patel", "Karan Malhotra", "Tanvi Bhat",
        "Rishi Saxena", "Divya Menon", "Harsh Vardhan", "Riya Sen", "Manish Pandey",
        "Meera Nambiar", "Gaurav Choudhary", "Shreya Ghoshal", "Nikhil Chopra", "Anushka Das",
        "Varun Dhawan", "Neha Singhania", "Akash Deep", "Swati Mishra", "Kunal Kamra",
        "Deepika Padukone", "Ranbir Kapoor", "Kriti Sanon", "Ayushmann Khurrana", "Bhumi Pednekar",
        "Kartik Aaryan", "Shraddha Kapoor", "Vicky Kaushal", "Taapsee Pannu", "Rajkummar Rao",
        "Sanya Malhotra", "Ishaan Khatter", "Alia Bhatt", "Abhishek Bachchan", "Fatima Sana"
    ]

    student_db_ids = []
    for idx, name in enumerate(student_names, start=1):
        roll = f"22CS{idx:03d}"
        uname = roll.lower()
        email = f"{uname}@student.ams.edu"

        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, full_name, phone)
            VALUES (?, ?, ?, 'student', ?, ?);
        """, (uname, email, test_password_hash, name, f"+91 97000{idx:05d}"))
        user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO students (user_id, roll_number, department, semester, section, batch_year)
            VALUES (?, ?, 'Computer Science & Engineering', 6, 'A', '2022-2026');
        """, (user_id, roll))
        student_id = cursor.lastrowid
        student_db_ids.append((student_id, roll, name))

    # Enroll all students in all 5 subjects
    cursor.execute("SELECT id FROM subjects;")
    all_subject_rows = cursor.fetchall()
    all_subject_ids = [row[0] for row in all_subject_rows]

    for s_id, _, _ in student_db_ids:
        for subj_id in all_subject_ids:
            cursor.execute("""
                INSERT INTO student_subjects (student_id, subject_id)
                VALUES (?, ?);
            """, (s_id, subj_id))

    # 5. Seed Attendance Sessions & Records
    # We will generate 20 lecture dates per subject over the preceding 5 weeks.
    # Deterministic attendance logic ensuring:
    # - Aarav Sharma (22CS001): High attendance ~ 95%
    # - Aditi Rao (22CS002): Safe borderline ~ 78%
    # - Rohan Gupta (22CS003): Low attendance (Defaulter) ~ 60%
    # - Priya Nair (22CS004): Low attendance (Defaulter) ~ 55%
    # - Other students range between 68% and 95%
    cursor.execute("""
        SELECT fs.faculty_id, fs.subject_id, s.name, s.code
        FROM faculty_subjects fs
        JOIN subjects s ON fs.subject_id = s.id
        ORDER BY s.id;
    """)
    assignments = cursor.fetchall()

    base_date = datetime.now() - timedelta(days=32)
    session_slots = [
        '09:00 - 10:00 AM',
        '10:00 - 11:00 AM',
        '11:15 - 12:15 PM',
        '01:15 - 02:15 PM',
        '02:15 - 03:15 PM'
    ]

    lecture_topics = {
        'CS601': [
            "Introduction to Mobile Data Management", "Architecture of Mobile DBMS",
            "Data Dissemination Schemes", "Broadcast Disk Scheduling", "Mobile Transaction Processing",
            "ACID Properties in Mobile DB", "Kangaroo Transactions", "Cache Invalidation Strategies",
            "Location Dependent Query Processing", "Spatial Indexing R-Trees", "Replication in Pervasive Systems",
            "PCO & Weak Consistency", "Energy Efficient Data Storage", "Disconnected Operations Mode",
            "Mobile Cloud Database Integration", "Security in Mobile Databases", "Case Study: Firebase & SQLite",
            "Sensor Data Stream Management", "Review and Mid-term Evaluation", "Advanced Topics in MDM"
        ],
        'CS602': [
            "Introduction to Automata & Alphabet", "DFA Construction & State Minimization",
            "NFA with Epsilon Transitions", "NFA to DFA Equivalence (Subset Construction)", "Regular Expressions & Identities",
            "Pumping Lemma for Regular Languages", "Closure Properties of Regular Sets", "Context Free Grammars (CFG)",
            "Derivation Trees & Ambiguity", "Chomsky Normal Form (CNF)", "Pushdown Automata (PDA) Design",
            "Equivalence of PDA and CFG", "Pumping Lemma for CFLs", "Turing Machine Formal Definition",
            "Turing Machine Variants & Multi-tape", "Decidability and Undecidability", "Halting Problem Proof",
            "Post Correspondence Problem (PCP)", "Complexity Classes P vs NP", "NP-Completeness and Reductions"
        ],
        'CS603': [
            "Introduction to Software Engineering & SDLC", "Waterfall and V-Model Paradigms",
            "Agile Principles & Scrum Framework", "SRS Documentation (IEEE 830 Standard)", "Functional vs Non-Functional Requirements",
            "Use Case Modeling & Activity Diagrams", "Software Architectural Styles (MVC, Layered)", "Modular Design, Coupling & Cohesion",
            "Database Schema Design for AMS", "Function Point & COCOMO Cost Estimation", "Risk Management & Mitigation Planning",
            "Gantt Charts & Critical Path Method", "Clean Code & Refactoring Practices", "Unit Testing & Integration Test Plans",
            "Black-box vs White-box Testing Techniques", "Software Quality Metrics & ISO Standards", "Version Control & CI/CD Pipelines",
            "Software Maintenance & Re-engineering", "SEPM Project Review & Verification", "Final Project Assessment & Viva Prep"
        ],
        'CS604': [
            "Digital Image Fundamentals & Pixels", "Elements of Visual Perception",
            "Image Sampling and Quantization", "Basic Spatial Domain Operations", "Histogram Processing & Equalization",
            "Spatial Filtering (Smoothing Filters)", "Sharpening Spatial Filters (Laplacian)", "Frequency Domain & 2D DFT",
            "Filtering in Frequency Domain", "Image Restoration & Noise Models", "Inverse Filtering & Wiener Filter",
            "Color Image Fundamentals (RGB, HSI)", "Morphological Operations: Dilation/Erosion", "Opening, Closing & Hit-or-Miss",
            "Image Segmentation: Edge Detection", "Sobel, Prewitt and Canny Operators", "Thresholding & Otsu's Algorithm",
            "Region Based Segmentation", "Object Recognition Basics", "Deep Learning in Computer Vision"
        ],
        'CS605': [
            "Foundations of Machine Learning", "Supervised vs Unsupervised Paradigms",
            "Linear Regression with Gradient Descent", "Multiple Linear Regression & Cost Function", "Logistic Regression for Binary Classification",
            "Decision Trees & Information Gain (ID3)", "Pruning & CART Algorithm", "Ensemble Methods: Random Forests",
            "Support Vector Machines (SVM)", "Kernel Trick and Hyperplane Optimization", "K-Nearest Neighbors (KNN)",
            "Naive Bayes Classifier", "Unsupervised Clustering: K-Means", "Hierarchical Clustering & Dendrograms",
            "Principal Component Analysis (PCA)", "Model Evaluation: Confusion Matrix, ROC-AUC", "Bias-Variance Tradeoff & Regularization",
            "Neural Network Architecture & Backprop", "Intro to Deep Learning & PyTorch", "Practical ML Pipeline Review"
        ]
    }

    # Generate 20 distinct session dates
    valid_dates = []
    curr = base_date
    while len(valid_dates) < 20:
        # Weekdays only (Monday=0 to Friday=4)
        if curr.weekday() < 5:
            valid_dates.append(curr.strftime('%Y-%m-%d'))
        curr += timedelta(days=1)

    for subj_idx, row in enumerate(assignments):
        fac_id = row['faculty_id']
        subj_id = row['subject_id']
        code = row['code']
        topics = lecture_topics.get(code, [f"Topic {i+1}" for i in range(20)])
        slot = session_slots[subj_idx % len(session_slots)]

        for day_idx, s_date in enumerate(valid_dates):
            topic = topics[day_idx % len(topics)]
            cursor.execute("""
                INSERT INTO attendance_sessions (subject_id, faculty_id, session_date, session_slot, topic)
                VALUES (?, ?, ?, ?, ?);
            """, (subj_id, fac_id, s_date, slot, topic))
            session_id = cursor.lastrowid

            # Generate attendance records for all 45 students for this session
            record_tuples = []
            for s_id, roll, name in student_db_ids:
                stud_num = int(roll[4:])  # 1 to 45

                # Deterministic attendance logic based on student number and session date:
                # Student 1: >90% present
                # Student 2: ~78% present
                # Student 3 & 4: ~58-62% (Defaulter, alert triggered!)
                # Student 5-10: 80-90%
                # Student 11: 65% (Defaulter)
                # Student 12-40: 75-92%
                # Student 41-45: Mixed (some >80%, some ~70%)
                is_present = True

                if stud_num == 1:
                    is_present = (day_idx != 4)  # missed only 1 out of 20 = 95%
                elif stud_num == 2:
                    is_present = (day_idx not in (3, 7, 12, 16))  # missed 4 out of 20 = 80%
                elif stud_num == 3:
                    # Missed 8 out of 20 = 60%
                    is_present = (day_idx not in (1, 3, 6, 8, 10, 13, 15, 18))
                elif stud_num == 4:
                    # Missed 9 out of 20 = 55%
                    is_present = (day_idx not in (0, 2, 5, 7, 9, 12, 14, 16, 19))
                elif stud_num == 11:
                    # Missed 7 out of 20 = 65%
                    is_present = (day_idx not in (2, 4, 7, 11, 14, 17, 19))
                elif stud_num == 25:
                    # Missed 7 out of 20 = 65%
                    is_present = (day_idx not in (1, 5, 8, 10, 13, 16, 18))
                else:
                    # Deterministic hash formula
                    hash_val = (stud_num * 17 + day_idx * 13 + subj_idx * 7) % 100
                    # 82% overall attendance rate
                    is_present = (hash_val >= 18)

                status = 'Present' if is_present else 'Absent'
                remarks = 'Present in lecture' if is_present else 'Unexcused Absence'
                record_tuples.append((session_id, s_id, status, remarks))

            cursor.executemany("""
                INSERT INTO attendance_records (session_id, student_id, status, remarks)
                VALUES (?, ?, ?, ?);
            """, record_tuples)

    conn.commit()
    conn.close()
    print("[AMS Seed] Successfully seeded database with complete college data.")
