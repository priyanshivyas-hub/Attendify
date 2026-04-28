import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendify.db')

def init_db():
    """Create tables and insert dummy data if the database is empty."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # If users already exist, skip initialisation
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone()[0] > 0:
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("Database already contains data.")
            conn.close()
            return

    print("Creating tables and inserting dummy data...")

    # --- ALL YOUR TABLE DEFINITIONS (from your original create_tables.py) ---
    tables = [
        """CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, full_name TEXT NOT NULL,
            role TEXT CHECK (role IN ('student','professor','admin')),
            department TEXT, custom_attendance_threshold INTEGER DEFAULT 75)""",
        """CREATE TABLE IF NOT EXISTS courses (
            course_id INTEGER PRIMARY KEY AUTOINCREMENT, course_code TEXT UNIQUE,
            course_name TEXT, department TEXT, credits INTEGER,
            professor_id INTEGER, semester TEXT, year INTEGER,
            total_lectures INTEGER, FOREIGN KEY (professor_id) REFERENCES users(user_id))""",
        """CREATE TABLE IF NOT EXISTS enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER,
            course_id INTEGER, UNIQUE(student_id, course_id),
            FOREIGN KEY (student_id) REFERENCES users(user_id),
            FOREIGN KEY (course_id) REFERENCES courses(course_id))""",
        """CREATE TABLE IF NOT EXISTS schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT, course_id INTEGER,
            day_of_week TEXT, start_time TEXT, end_time TEXT, room TEXT,
            FOREIGN KEY (course_id) REFERENCES courses(course_id))""",
        """CREATE TABLE IF NOT EXISTS class_instances (
            instance_id INTEGER PRIMARY KEY AUTOINCREMENT, schedule_id INTEGER,
            class_date TEXT, status TEXT DEFAULT 'scheduled', cancellation_reason TEXT,
            FOREIGN KEY (schedule_id) REFERENCES schedule(schedule_id))""",
        """CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT, instance_id INTEGER,
            student_id INTEGER, status TEXT, marked_by INTEGER,
            marked_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (instance_id) REFERENCES class_instances(instance_id),
            FOREIGN KEY (student_id) REFERENCES users(user_id))""",
        """CREATE TABLE IF NOT EXISTS disputes (
            dispute_id INTEGER PRIMARY KEY AUTOINCREMENT, attendance_id INTEGER,
            student_id INTEGER, reason TEXT, status TEXT DEFAULT 'pending',
            submitted_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (attendance_id) REFERENCES attendance(attendance_id))""",
        """CREATE TABLE IF NOT EXISTS holidays (
            holiday_id INTEGER PRIMARY KEY AUTOINCREMENT, holiday_date TEXT,
            name TEXT, type TEXT)""",
        """CREATE TABLE IF NOT EXISTS locations (
            location_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
            latitude REAL, longitude REAL, type TEXT, building TEXT)""",
        """CREATE TABLE IF NOT EXISTS conversations (
            conv_id INTEGER PRIMARY KEY AUTOINCREMENT, user1_id INTEGER,
            user2_id INTEGER, created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user1_id, user2_id))""",
        """CREATE TABLE IF NOT EXISTS messages (
            msg_id INTEGER PRIMARY KEY AUTOINCREMENT, conv_id INTEGER,
            sender_id INTEGER, content TEXT, sent_at TEXT DEFAULT (datetime('now')),
            is_read INTEGER DEFAULT 0)""",
        """CREATE TABLE IF NOT EXISTS issue_categories (
            cat_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT,
            default_assignee_role TEXT)""",
        """CREATE TABLE IF NOT EXISTS issues (
            issue_id INTEGER PRIMARY KEY AUTOINCREMENT, reporter_id INTEGER,
            category_id INTEGER, title TEXT, description TEXT,
            location_id INTEGER, status TEXT DEFAULT 'pending',
            assigned_to INTEGER, created_at TEXT DEFAULT (datetime('now')))""",
        """CREATE TABLE IF NOT EXISTS issue_comments (
            comment_id INTEGER PRIMARY KEY AUTOINCREMENT, issue_id INTEGER,
            user_id INTEGER, comment TEXT, created_at TEXT DEFAULT (datetime('now')))""",
        """CREATE TABLE IF NOT EXISTS professor_current_location (
            professor_id INTEGER PRIMARY KEY, location_type TEXT,
            building TEXT, room TEXT, status TEXT, notes TEXT,
            updated_at TEXT DEFAULT (datetime('now')))""",
        """CREATE TABLE IF NOT EXISTS special_class_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT, class_date TEXT,
            follow_day TEXT, approved INTEGER DEFAULT 0,
            created_by INTEGER, note TEXT, created_at TEXT DEFAULT (datetime('now')))""",
        """CREATE TABLE IF NOT EXISTS notifications (
            notification_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, type TEXT, data TEXT,
            timestamp TEXT DEFAULT (datetime('now')), is_read INTEGER DEFAULT 0)""",
        """CREATE VIEW IF NOT EXISTS vw_professor_live_status AS
            SELECT u.user_id, u.full_name, u.department, pcl.location_type,
                   pcl.building, pcl.room, pcl.status, pcl.notes, pcl.updated_at,
                   CAST((julianday('now') - julianday(pcl.updated_at)) * 1440 AS INTEGER) AS minutes_since_update
            FROM users u LEFT JOIN professor_current_location pcl ON u.user_id = pcl.professor_id
            WHERE u.role = 'professor'"""
    ]

    for table in tables:
        cursor.execute(table)

    print("✅ Tables created.")

    password = generate_password_hash('password123')

    # --- USERS ---
    cursor.execute("INSERT INTO users (email, password_hash, full_name, role, department) VALUES (?,?,?,?,?)",
                   ('admin@medicaps.ac.in', password, 'Admin User', 'admin', 'Administration'))

    professors = [
        ('sagar.pandya@medicaps.ac.in', 'Prof. Sagar Pandya', 'professor', 'IT'),
        ('rahul.pawar@medicaps.ac.in', 'Prof. Rahul Singh Pawar', 'professor', 'IT'),
        ('neha.modak@medicaps.ac.in', 'Ms. Neha Modak', 'professor', 'IT'),
        ('jyoti.kukade@medicaps.ac.in', 'Prof. Jyoti Kukade', 'professor', 'IT'),
        ('prabhat.pandey@medicaps.ac.in', 'Dr. Prabhat Pandey', 'professor', 'IT'),
        ('vandana.birle@medicaps.ac.in', 'Prof. Vandana Birle', 'professor', 'IT'),
        ('nf2@medicaps.ac.in', 'NF2 (Soft Skills)', 'professor', 'HSS'),
        ('dean.it@medicaps.ac.in', 'Dean of IT', 'professor', 'IT'),
        ('dean.cse@medicaps.ac.in', 'Dean of CSE', 'professor', 'CSE'),
        ('vc@medicaps.ac.in', 'Vice Chancellor', 'admin', 'Administration'),
    ]
    for p in professors:
        cursor.execute("INSERT INTO users (email, password_hash, full_name, role, department) VALUES (?,?,?,?,?)",
                       (p[0], password, p[1], p[2], p[3]))

    students = [
        ('en24it3010061@medicaps.ac.in', 'KUSH GANGRADE'),
        ('en24it3010062@medicaps.ac.in', 'KUSHAL PATHAK'),
        # ... (include all 60 students from your original list)
        ('en25it3l10001@medicaps.ac.in', 'TEJASV GAWANDE'),
    ]
    for s in students:
        cursor.execute("INSERT INTO users (email, password_hash, full_name, role, department) VALUES (?,?,?,?,?)",
                       (s[0], password, s[1], 'student', 'IT'))

    print(f"✅ Users added: {1+len(professors)+len(students)} total")

    # --- COURSES ---
    courses_data = [
        ('IT3CO05','Database Management Systems','IT',4,2,'Even',2026,44),
        ('IT3CO21','Operating System','IT',4,3,'Even',2026,42),
        ('IT3CO29','Computational Statistics','IT',3,4,'Even',2026,40),
        ('IT3CO30','Artificial Intelligence','IT',4,5,'Even',2026,45),
        ('IT3CO32','Microprocessor & Microcontroller','IT',4,6,'Even',2026,38),
        ('IT3CO34','Design and Analysis of Algorithms','IT',4,7,'Even',2026,43),
        ('EN3NG10','Soft Skills-II','HSS',2,8,'Even',2026,20),
    ]
    for c in courses_data:
        cursor.execute("INSERT INTO courses (course_code, course_name, department, credits, professor_id, semester, year, total_lectures) VALUES (?,?,?,?,?,?,?,?)", c)

    print("✅ Courses added.")

    # --- ENROLLMENTS ---
    cursor.execute("SELECT user_id FROM users WHERE role='student'")
    student_ids = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT course_id FROM courses")
    course_ids = [row[0] for row in cursor.fetchall()]
    count = 0
    for sid in student_ids:
        for cid in course_ids:
            cursor.execute("INSERT OR IGNORE INTO enrollments (student_id, course_id) VALUES (?,?)", (sid, cid))
            count += 1
    print(f"✅ Enrollments added: {count}")

    # --- SCHEDULE ---
    schedule_data = [
        (1,'Mon','08:30','09:20','B-103'),(1,'Wed','09:20','10:10','B-103'),
        (2,'Tue','10:20','11:10','B-003'),(2,'Thu','11:10','12:00','B-003'),
        (3,'Wed','08:30','09:20','B-003'),(3,'Fri','10:20','11:10','B-003'),
        (4,'Mon','12:50','13:40','B-003'),(4,'Wed','13:40','14:20','B-003'),
        (5,'Tue','08:30','09:20','B-103'),(5,'Thu','09:20','10:10','B-103'),
        (6,'Mon','10:20','11:10','B-003'),(6,'Fri','12:50','13:40','B-003'),
        (7,'Tue','12:50','13:40','B-003'),(7,'Thu','13:40','14:20','B-003'),
    ]
    for s in schedule_data:
        cursor.execute("INSERT INTO schedule (course_id, day_of_week, start_time, end_time, room) VALUES (?,?,?,?,?)", s)
    print("✅ Schedule added.")

    # --- CLASS INSTANCES (today +/- 30 days) ---
    cursor.execute("SELECT schedule_id, day_of_week FROM schedule")
    schedules = cursor.fetchall()
    today = datetime.now().date()
    instance_count = 0
    for i in range(-30, 31):
        date = today + timedelta(days=i)
        weekday = date.strftime('%a')
        for sch in schedules:
            if sch[1] == weekday:
                cursor.execute("INSERT INTO class_instances (schedule_id, class_date, status) VALUES (?,?,?)",
                               (sch[0], date.strftime('%Y-%m-%d'), 'scheduled'))
                instance_count += 1
    print(f"✅ Class instances added: {instance_count}")

    # --- ATTENDANCE ---
    cursor.execute("SELECT instance_id FROM class_instances WHERE class_date <= DATE('now')")
    instances = [row[0] for row in cursor.fetchall()]
    att_count = 0
    for inst in instances:
        cursor.execute("""
            SELECT DISTINCT e.student_id FROM enrollments e
            JOIN schedule s ON e.course_id = s.course_id
            WHERE s.schedule_id = (SELECT schedule_id FROM class_instances WHERE instance_id = ?)
        """, (inst,))
        enrolled_students = [row[0] for row in cursor.fetchall()]
        for stu in enrolled_students:
            r = random.random()
            if r < 0.65: status = 'present'
            elif r < 0.80: status = 'absent'
            elif r < 0.90: status = 'late'
            else: status = 'excused'
            cursor.execute("INSERT OR IGNORE INTO attendance (instance_id, student_id, status, marked_by) VALUES (?,?,?,?)",
                           (inst, stu, status, 1))
            att_count += 1
    print(f"✅ Attendance records added: {att_count}")

    # --- HOLIDAYS ---
    holidays = [
        ('2026-01-26','Republic Day','National'),
        ('2026-03-04','Holi','Festival'),
        ('2026-03-21','Eid-Ul-Fitar','Festival'),
        ('2026-03-31','Mahavir Jayanti','Festival'),
        ('2026-04-03','Good Friday','Religious'),
        ('2026-04-14','Dr. Ambedkar Jayanti','National'),
        ('2026-05-01','Labour Day','International'),
    ]
    for h in holidays:
        cursor.execute("INSERT INTO holidays (holiday_date, name, type) VALUES (?,?,?)", h)
    print("✅ Holidays added.")

    # --- LOCATIONS ---
    locations = [
        ('Main Gate',22.7196,75.8577,'gate','Main'),
        ('Admin Block',22.7189,75.8569,'building','Admin'),
        ('Library',22.7202,75.8581,'building','Central'),
        ('CSE Block',22.7210,75.8590,'building','CSE'),
        ('IT Block',22.7215,75.8595,'building','IT'),
        ('Auditorium',22.7175,75.8555,'facility','Main'),
        ('Canteen',22.7206,75.8576,'facility','Central'),
        ('Sports Complex',22.7250,75.8630,'facility','Sports'),
        ('Boys Hostel',22.7260,75.8640,'hostel','Residential'),
        ('Girls Hostel',22.7270,75.8650,'hostel','Residential'),
    ]
    for l in locations:
        cursor.execute("INSERT INTO locations (name, latitude, longitude, type, building) VALUES (?,?,?,?,?)", l)
    print("✅ Locations added.")

    # --- CONVERSATIONS & MESSAGES ---
    cursor.execute("SELECT user_id, full_name FROM users WHERE role='student'")
    all_students = cursor.fetchall()
    cursor.execute("SELECT user_id, full_name FROM users WHERE role='professor'")
    all_professors = cursor.fetchall()
    msg_count = 0
    for prof in all_professors:
        for stu in all_students[:3]:
            cursor.execute("INSERT OR IGNORE INTO conversations (user1_id, user2_id) VALUES (?,?)", (stu[0], prof[0]))
            cursor.execute("SELECT conv_id FROM conversations WHERE user1_id=? AND user2_id=?", (stu[0], prof[0]))
            conv = cursor.fetchone()
            if conv:
                conv_id = conv[0]
                cursor.execute("INSERT INTO messages (conv_id, sender_id, content) VALUES (?,?,?)",
                               (conv_id, prof[0], f"Hello {stu[1]}! How can I help you with the course?"))
                cursor.execute("INSERT INTO messages (conv_id, sender_id, content) VALUES (?,?,?)",
                               (conv_id, stu[0], f"Thank you {prof[1]}! I had a doubt about the last lecture."))
                msg_count += 2
    print(f"✅ Messages: {msg_count}")

    # --- PROFESSOR LOCATIONS ---
    statuses = ['Free', 'In Class', 'Busy', 'Available Soon']
    buildings = ['IT Block', 'Admin Block', 'Library', 'CSE Block']
    for prof in all_professors:
        cursor.execute("INSERT OR IGNORE INTO professor_current_location (professor_id, location_type, building, room, status, notes) VALUES (?,?,?,?,?,?)",
                       (prof[0], 'Office', random.choice(buildings), f'Room {random.randint(101,350)}', random.choice(statuses), ''))
    print("✅ Professor locations added.")

    # --- ISSUE CATEGORIES ---
    categories = [('Classroom Issue','dean'),('Lab Equipment','hod'),('Network Issue','maintenance'),('Cleanliness','maintenance'),('Other','admin')]
    for cat in categories:
        cursor.execute("INSERT INTO issue_categories (name, default_assignee_role) VALUES (?,?)", cat)
    print("✅ Issue categories added.")

    conn.commit()
    conn.close()
    print("Database initialised with dummy data.")