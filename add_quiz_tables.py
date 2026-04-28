# add_quiz_tables.py
import sqlite3, os
DB_PATH = os.path.join(os.path.dirname(__file__), 'attendify.db')
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables = [
    """CREATE TABLE IF NOT EXISTS quizzes (
        quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        title TEXT,
        description TEXT,
        quiz_type TEXT CHECK(quiz_type IN ('mcq','short_answer','mixed')),
        time_limit INTEGER,
        start_time TEXT,
        end_time TEXT,
        total_marks INTEGER,
        created_by INTEGER,
        created_at TEXT DEFAULT (datetime('now')),
        ai_generated INTEGER DEFAULT 0,
        FOREIGN KEY (course_id) REFERENCES courses(course_id),
        FOREIGN KEY (created_by) REFERENCES users(user_id)
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_questions (
        question_id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        question_text TEXT,
        question_type TEXT CHECK(question_type IN ('mcq','short_answer')),
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct_answer TEXT,
        marks INTEGER DEFAULT 1,
        ai_generated INTEGER DEFAULT 0,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_attempts (
        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        quiz_id INTEGER,
        student_id INTEGER,
        start_time TEXT DEFAULT (datetime('now')),
        end_time TEXT,
        score INTEGER,
        total_marks INTEGER,
        face_verified INTEGER DEFAULT 0,
        FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id),
        FOREIGN KEY (student_id) REFERENCES users(user_id)
    )""",
    """CREATE TABLE IF NOT EXISTS quiz_answers (
        answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER,
        question_id INTEGER,
        student_answer TEXT,
        is_correct INTEGER,
        marks_obtained REAL,
        ai_feedback TEXT,
        FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(attempt_id),
        FOREIGN KEY (question_id) REFERENCES quiz_questions(question_id)
    )"""
]

for table in tables:
    cursor.execute(table)

conn.commit()
conn.close()
print("✅ Quiz tables created successfully!")