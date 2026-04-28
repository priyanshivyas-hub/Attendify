import json
import random
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from database import get_db_connection, fetchone_dict, fetchall_dict
from utils.helpers import generate_class_instances
from create_tables import init_db
import os

def load_env_file():
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        pass

load_env_file()

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
mail = Mail(app)

# ==================== INIT TOTAL LECTURES ====================
def initialize_total_lectures():
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE courses SET total_lectures = 44 WHERE course_code = 'IT3CO05'")
        cursor.execute("UPDATE courses SET total_lectures = 42 WHERE course_code = 'IT3CO21'")
        cursor.execute("UPDATE courses SET total_lectures = 40 WHERE course_code = 'IT3CO29'")
        cursor.execute("UPDATE courses SET total_lectures = 45 WHERE course_code = 'IT3CO30'")
        cursor.execute("UPDATE courses SET total_lectures = 38 WHERE course_code = 'IT3CO32'")
        cursor.execute("UPDATE courses SET total_lectures = 43 WHERE course_code = 'IT3CO34'")
        cursor.execute("UPDATE courses SET total_lectures = 20 WHERE course_code = 'EN3NG10'")
        conn.commit()
        print("total_lectures initialized.")
    except Exception as e:
        print("Init error:", e)
    finally:
        cursor.close()
        conn.close()


# ==================== DECORATORS ====================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('Access denied', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ==================== AUTH ROUTES ====================
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    conn = get_db_connection()
    if not conn:
        flash('Database connection failed', 'danger')
        return redirect(url_for('index'))

    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM users WHERE LOWER(TRIM(email)) = LOWER(?)",
        (email,)
    )
    user = fetchone_dict(cursor)
    cursor.close()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['user_id'] = user['user_id']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        return redirect(url_for('dashboard'))
    else:
        flash('Invalid email or password', 'danger')
        return redirect(url_for('index'))


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        user_id = session['user_id']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE user_id = ?", (user_id,))
        user = fetchone_dict(cursor)
        if not check_password_hash(user['password_hash'], current_password):
            flash("Current password incorrect", "danger")
            return redirect(url_for('change_password'))
        if new_password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('change_password'))
        new_hash = generate_password_hash(new_password)
        cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Password changed successfully", "success")
        return redirect(url_for('dashboard'))
    return render_template("change_password.html")


@app.route('/forgot_password', methods=['GET','POST'])
def forgot_password():
    if request.method == "POST":
        email = request.form['email']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = fetchone_dict(cursor)
        cursor.close()
        conn.close()
        
        if not user:
            flash("Email not found", "danger")
            return redirect(url_for('forgot_password'))
        
        otp = str(random.randint(100000, 999999))
        session['reset_email'] = email
        session['reset_otp'] = otp
        
        # Store OTP in session and redirect to verify page
        flash(f"Your OTP is: {otp}", "success")
        return redirect(url_for('verify_otp'))
    
    return render_template("forgot_password.html")

@app.route('/verify_otp', methods=['GET','POST'])
def verify_otp():
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        if user_otp == session.get('reset_otp'):
            return redirect(url_for('reset_password'))
        flash("Invalid OTP", "danger")
    return render_template("verify_otp.html")


@app.route('/reset_password', methods=['GET','POST'])
def reset_password():
    if request.method == "POST":
        new_password = request.form['password']
        email = session.get('reset_email')
        password_hash = generate_password_hash(new_password)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = ?",(password_hash,email))
        conn.commit()
        cursor.close()
        conn.close()
        flash("Password updated successfully","success")
        return redirect(url_for('index'))
    return render_template("reset_password.html")


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'student':
        return redirect(url_for('student_dashboard'))
    if role == 'professor':
        return redirect(url_for('professor_dashboard'))
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('logout'))


# ==================== STUDENT ROUTES ====================
@app.route('/student/dashboard')
@login_required
@role_required('student')
def student_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('logout'))

    cursor = conn.cursor()

    # Get enrolled courses
    cursor.execute("""
        SELECT c.course_id, c.course_code, c.course_name, c.total_lectures
        FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE e.student_id = ?
    """, (user_id,))
    courses = fetchall_dict(cursor)

    for course in courses:
        # Total held
        cursor.execute("""
            SELECT COUNT(*) as total_held
            FROM class_instances ci
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            WHERE s.course_id = ? AND ci.class_date <= DATE('now') AND ci.status != 'cancelled'
        """, (course['course_id'],))
        held = fetchone_dict(cursor)
        course['total_held'] = held['total_held'] if held else 0

        # Attended
        cursor.execute("""
            SELECT COUNT(*) as attended
            FROM attendance a
            JOIN class_instances ci ON a.instance_id = ci.instance_id
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            WHERE s.course_id = ? AND a.student_id = ? AND a.status IN ('present','late')
            AND ci.class_date <= DATE('now') AND ci.status != 'cancelled'
        """, (course['course_id'], user_id))
        att = fetchone_dict(cursor)
        course['attended'] = att['attended'] if att else 0

        # Remaining
        cursor.execute("""
            SELECT COUNT(*) as remaining
            FROM class_instances ci
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            WHERE s.course_id = ? AND ci.class_date > DATE('now') AND ci.status != 'cancelled'
        """, (course['course_id'],))
        rem = fetchone_dict(cursor)
        course['remaining'] = rem['remaining'] if rem else 0

        # Percentage
        if course['total_held'] > 0:
            course['percentage'] = round(100.0 * course['attended'] / course['total_held'], 1)
        else:
            course['percentage'] = 0

    # Disputes
    cursor.execute("""
        SELECT d.*, c.course_code, ci.class_date
        FROM disputes d
        JOIN attendance a ON d.attendance_id = a.attendance_id
        JOIN class_instances ci ON a.instance_id = ci.instance_id
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE d.student_id = ? AND d.status = 'pending'
    """, (user_id,))
    disputes = fetchall_dict(cursor)
    
    # Holidays
    cursor.execute("SELECT * FROM holidays WHERE holiday_date >= DATE('now') LIMIT 5")
    holidays = fetchall_dict(cursor)

    # Threshold
    cursor.execute("SELECT custom_attendance_threshold FROM users WHERE user_id = ?", (user_id,))
    row = fetchone_dict(cursor)
    custom_threshold = row['custom_attendance_threshold'] if row and row['custom_attendance_threshold'] is not None else 75

    cursor.close()
    conn.close()

    return render_template('student_dashboard.html', courses=courses, disputes=disputes,
                           holidays=holidays, custom_threshold=custom_threshold)

@app.route('/student/dispute/<int:attendance_id>', methods=['POST'])
@login_required
@role_required('student')
def submit_dispute(attendance_id):
    reason = request.form.get('reason')
    student_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('student_dashboard'))
    cursor = conn.cursor()
    cursor.execute("SELECT attendance_id FROM attendance WHERE attendance_id = ? AND student_id = ?",
                   (attendance_id, student_id))
    if not fetchone_dict(cursor):
        flash('Invalid attendance record', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('student_dashboard'))
    cursor.execute("SELECT dispute_id FROM disputes WHERE attendance_id = ? AND status = 'pending'", (attendance_id,))
    if fetchone_dict(cursor):
        flash('Dispute already pending', 'warning')
    else:
        cursor.execute("INSERT INTO disputes (attendance_id, student_id, reason) VALUES (?, ?, ?)",
                       (attendance_id, student_id, reason))
        conn.commit()
        flash('Dispute submitted', 'success')
    cursor.close()
    conn.close()
    return redirect(url_for('student_dashboard'))


# ==================== PROFESSOR ROUTES ====================
@app.route('/professor/dashboard')
@login_required
@role_required('professor')
def professor_dashboard():
    professor_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('logout'))

    cursor = conn.cursor()

    # Today's classes
    today_weekday = datetime.now().strftime('%a')
    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.end_time, s.room,
               COALESCE(ci.status,'scheduled') as status,
               (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.course_id) AS total_students,
               (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'present') AS present,
               (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'absent') AS absent,
               (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'late') AS late,
               (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'excused') AS excused
        FROM schedule s
        JOIN courses c ON s.course_id = c.course_id
        LEFT JOIN class_instances ci ON ci.schedule_id = s.schedule_id AND ci.class_date = DATE('now')
        WHERE s.day_of_week = ? AND c.professor_id = ?
        AND (ci.status IS NULL OR ci.status != 'cancelled')
        ORDER BY s.start_time
    """, (today_weekday, professor_id))
    today_classes = fetchall_dict(cursor)

    # Upcoming classes (non‑cancelled)
    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.room,
               ci.class_date
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date > DATE('now') AND ci.class_date <= DATE('now', '+7 days')
        AND c.professor_id = ? AND ci.status != 'cancelled'
        ORDER BY ci.class_date
    """, (professor_id,))
    upcoming_classes = fetchall_dict(cursor)

    # ========== INSERTED CANCELLED CLASSES QUERIES ==========
    # Cancelled classes TODAY
    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.end_time, s.room,
               ci.cancellation_reason
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date = DATE('now') AND c.professor_id = ? AND ci.status = 'cancelled'
        ORDER BY s.start_time
    """, (professor_id,))
    cancelled_today = fetchall_dict(cursor)

    # Cancelled UPCOMING classes (next 7 days)
    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.room, ci.class_date,
               ci.cancellation_reason
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date > DATE('now') AND ci.class_date <= DATE('now', '+7 days')
        AND c.professor_id = ? AND ci.status = 'cancelled'
        ORDER BY ci.class_date
    """, (professor_id,))
    cancelled_upcoming = fetchall_dict(cursor)
    # ========================================================

    # Course summary
    cursor.execute("""
        SELECT c.course_code, c.course_name, c.total_lectures,
               COUNT(ci.instance_id) AS held_so_far,
               SUM(CASE WHEN ci.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM courses c
        LEFT JOIN schedule s ON c.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= DATE('now')
        WHERE c.professor_id = ?
        GROUP BY c.course_code, c.course_name, c.total_lectures
    """, (professor_id,))
    course_summary = fetchall_dict(cursor)

    # Pending disputes count
    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM disputes d
        JOIN attendance a ON d.attendance_id = a.attendance_id
        JOIN class_instances ci ON a.instance_id = ci.instance_id
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE c.professor_id = ? AND d.status = 'pending'
    """, (professor_id,))
    row = fetchone_dict(cursor)
    pending_count = row['count'] if row else 0

    cursor.close()
    conn.close()

    return render_template('professor_dashboard.html',
                           today_classes=today_classes,
                           upcoming_classes=upcoming_classes,
                           course_summary=course_summary,
                           pending_count=pending_count,
                           cancelled_today=cancelled_today,
                           cancelled_upcoming=cancelled_upcoming)

@app.route('/professor/class/<int:instance_id>/cancel', methods=['POST'])
@login_required
@role_required('professor')
def cancel_class(instance_id):
    professor_id = session['user_id']
    reason = request.form.get('reason', '')
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('professor_dashboard'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.instance_id FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.instance_id = ? AND c.professor_id = ?
    """, (instance_id, professor_id))
    if not fetchone_dict(cursor):
        flash('Access denied', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('professor_dashboard'))
    cursor.execute("""
        UPDATE class_instances SET status = 'cancelled', cancellation_reason = ? WHERE instance_id = ?
    """, (reason, instance_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Class cancelled', 'success')
    return redirect(url_for('professor_dashboard'))


@app.route('/professor/class/<int:instance_id>')
@login_required
@role_required('professor')
def class_attendance(instance_id):
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect(url_for('professor_dashboard'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.instance_id, ci.class_date, s.start_time, s.end_time, s.room,
               c.course_code, c.course_name
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.instance_id = ?
    """, (instance_id,))
    class_info = fetchone_dict(cursor)
    
    if not class_info:
        flash("Class not found", "danger")
        return redirect(url_for('professor_dashboard'))
    
    cursor.execute("""
        SELECT u.user_id, u.full_name, u.email, a.status AS attendance_status
        FROM enrollments e
        JOIN users u ON e.student_id = u.user_id
        JOIN schedule s ON e.course_id = s.course_id
        JOIN class_instances ci ON ci.schedule_id = s.schedule_id
        LEFT JOIN attendance a ON a.student_id = u.user_id AND a.instance_id = ci.instance_id
        WHERE ci.instance_id = ?
        ORDER BY u.full_name
    """, (instance_id,))
    students = fetchall_dict(cursor)
    
    cursor.execute("""
        SELECT
            SUM(CASE WHEN status='present' THEN 1 ELSE 0 END) AS present_count,
            SUM(CASE WHEN status='absent' THEN 1 ELSE 0 END) AS absent_count,
            SUM(CASE WHEN status='late' THEN 1 ELSE 0 END) AS late_count,
            SUM(CASE WHEN status='excused' THEN 1 ELSE 0 END) AS excused_count,
            COUNT(*) AS total_marked
        FROM attendance WHERE instance_id = ?
    """, (instance_id,))
    counts = fetchone_dict(cursor)
    if not counts or counts['total_marked'] == 0:
        counts = {"present_count":0,"absent_count":0,"late_count":0,"excused_count":0,"total_marked":0}
    
    cursor.close()
    conn.close()
    return render_template("class_attendance.html", class_info=class_info, students=students, counts=counts)

@app.route('/professor/class/<int:instance_id>/attendance', methods=['POST'])
@login_required
@role_required('professor')
def save_attendance(instance_id):
    professor_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('professor_dashboard'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.instance_id, ci.class_date
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.instance_id = ? AND c.professor_id = ?
    """, (instance_id, professor_id))
    row = fetchone_dict(cursor)
    if not row:
        flash('Access denied', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('professor_dashboard'))
    if row['class_date'] > datetime.now().strftime('%Y-%m-%d'):
        flash('Cannot mark attendance for future classes', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('professor_dashboard'))
    for key, value in request.form.items():
        if key.startswith('student_'):
            student_id = key.replace('student_', '')
            status = value
            cursor.execute("SELECT attendance_id FROM attendance WHERE instance_id = ? AND student_id = ?",
                           (instance_id, student_id))
            existing = fetchone_dict(cursor)
            if existing:
                cursor.execute("""
                    UPDATE attendance SET status = ?, marked_by = ?, marked_at = DATETIME('now')
                    WHERE instance_id = ? AND student_id = ?
                """, (status, professor_id, instance_id, student_id))
            else:
                cursor.execute("""
                    INSERT INTO attendance (instance_id, student_id, status, marked_by)
                    VALUES (?, ?, ?, ?)
                """, (instance_id, student_id, status, professor_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Attendance saved', 'success')
    return redirect(url_for('class_attendance', instance_id=instance_id))


@app.route('/professor/class/<int:instance_id>/restore', methods=['POST'])
@login_required
@role_required('professor')
def restore_class(instance_id):
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.instance_id FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.instance_id = ? AND c.professor_id = ?
    """, (instance_id, professor_id))
    if not fetchone_dict(cursor):
        flash('Access denied', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('professor_dashboard'))
    cursor.execute("""
        UPDATE class_instances SET status = 'scheduled', cancellation_reason = NULL WHERE instance_id = ?
    """, (instance_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Class restored to scheduled', 'success')
    return redirect(url_for('professor_dashboard'))


@app.route('/professor/disputes')
@login_required
@role_required('professor')
def view_disputes():
    professor_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('professor_dashboard'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, u.full_name AS student_name, u.email,
               c.course_code, c.course_name, ci.class_date, a.status AS original_status
        FROM disputes d
        JOIN attendance a ON d.attendance_id = a.attendance_id
        JOIN class_instances ci ON a.instance_id = ci.instance_id
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        JOIN users u ON d.student_id = u.user_id
        WHERE c.professor_id = ? AND d.status = 'pending'
        ORDER BY d.submitted_at DESC
    """, (professor_id,))
    disputes = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('disputes.html', disputes=disputes)


@app.route('/professor/dispute/<int:dispute_id>/resolve', methods=['POST'])
@login_required
@role_required('professor')
def resolve_dispute(dispute_id):
    action = request.form.get('action')
    professor_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('view_disputes'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.dispute_id, d.attendance_id
        FROM disputes d
        JOIN attendance a ON d.attendance_id = a.attendance_id
        JOIN class_instances ci ON a.instance_id = ci.instance_id
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE d.dispute_id = ? AND c.professor_id = ?
    """, (dispute_id, professor_id))
    dispute = fetchone_dict(cursor)
    if not dispute:
        flash('Dispute not found', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('view_disputes'))
    if action == 'approve':
        cursor.execute("UPDATE attendance SET status = 'present' WHERE attendance_id = ?", (dispute['attendance_id'],))
        cursor.execute("UPDATE disputes SET status = 'approved' WHERE dispute_id = ?", (dispute_id,))
        flash('Dispute approved', 'success')
    else:
        cursor.execute("UPDATE disputes SET status = 'rejected' WHERE dispute_id = ?", (dispute_id,))
        flash('Dispute rejected', 'info')
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_disputes'))


# ==================== PROFESSOR LOCATION ROUTES ====================
@app.route('/professor/location', methods=['GET', 'POST'])
@login_required
@role_required('professor')
def manage_location():
    professor_id = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('professor_dashboard'))
    cursor = conn.cursor()
    if request.method == 'POST':
        location_type = request.form.get('location_type')
        building = request.form.get('building')
        room = request.form.get('room')
        status = request.form.get('status')
        notes = request.form.get('notes')
        cursor.execute("SELECT professor_id FROM professor_current_location WHERE professor_id = ?", (professor_id,))
        existing = fetchone_dict(cursor)
        if existing:
            cursor.execute("""
                UPDATE professor_current_location
                SET location_type = ?, building = ?, room = ?, status = ?, notes = ?, updated_at = DATETIME('now')
                WHERE professor_id = ?
            """, (location_type, building, room, status, notes, professor_id))
        else:
            cursor.execute("""
                INSERT INTO professor_current_location (professor_id, location_type, building, room, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (professor_id, location_type, building, room, status, notes))
        cursor.execute("""
            INSERT INTO professor_location_history (professor_id, location_type, building, room, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (professor_id, location_type, building, room, status, notes))
        conn.commit()
        flash('Location updated successfully', 'success')
    cursor.execute("SELECT * FROM professor_current_location WHERE professor_id = ?", (professor_id,))
    location = fetchone_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('manage_location.html', location=location)


@app.route('/api/professor/location/<int:professor_id>')
def get_professor_location(professor_id):
    conn = get_db_connection()
    if not conn:
        return {'error': 'Database error'}, 500
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vw_professor_live_status WHERE user_id = ?", (professor_id,))
    location = fetchone_dict(cursor)
    conn.close()
    if location:
        return {
            'professor_id': location['user_id'],
            'professor_name': location['full_name'],
            'location_type': location['location_type'],
            'building': location['building'],
            'room': location['room'],
            'status': location['status'],
            'last_updated': location['updated_at'] if location['updated_at'] else None
        }
    return {'error': 'Location not found'}, 404


@app.route('/student/professors/locations')
@login_required
@role_required('student')
def view_professor_locations():
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('student_dashboard'))
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT * FROM vw_professor_live_status ORDER BY full_name")
    professors = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('professor_locations.html', professors=professors)

# ==================== PROFESSOR COURSE MANAGEMENT ====================
@app.route('/professor/courses')
@login_required
@role_required('professor')
def manage_courses():
    """Professor manages their courses"""
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get professor's courses
    cursor.execute("""
        SELECT c.*, 
               (SELECT COUNT(*) FROM enrollments WHERE course_id = c.course_id) as total_students,
               (SELECT COUNT(*) FROM class_instances ci 
                JOIN schedule s ON ci.schedule_id = s.schedule_id 
                WHERE s.course_id = c.course_id AND ci.class_date <= DATE('now')) as classes_held
        FROM courses c
        WHERE c.professor_id = ?
        ORDER BY c.course_code
    """, (professor_id,))
    courses = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return render_template('professor_courses.html', courses=courses)


@app.route('/professor/course/add', methods=['POST'])
@login_required
@role_required('professor')
def add_course():
    """Add a new course"""
    professor_id = session['user_id']
    
    course_code = request.form.get('course_code')
    course_name = request.form.get('course_name')
    credits = request.form.get('credits')
    total_lectures = request.form.get('total_lectures')
    
    if not course_code or not course_name:
        flash('Course code and name required', 'danger')
        return redirect(url_for('manage_courses'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO courses (course_code, course_name, department, credits, professor_id, semester, year, total_lectures)
            VALUES (?, ?, 'IT', ?, ?, 'Current', 2026, ?)
        """, (course_code, course_name, credits or 3, professor_id, total_lectures or 40))
        conn.commit()
        flash('Course added successfully!', 'success')
    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
    finally:
        cursor.close()
        conn.close()
    
    return redirect(url_for('manage_courses'))


@app.route('/professor/course/<int:course_id>/delete', methods=['POST'])
@login_required
@role_required('professor')
def delete_course(course_id):
    """Delete a course (only if owned by professor)"""
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM courses WHERE course_id = ? AND professor_id = ?", (course_id, professor_id))
    course = fetchone_dict(cursor)
    
    if not course:
        flash('Course not found or access denied', 'danger')
    else:
        cursor.execute("DELETE FROM enrollments WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM schedule WHERE course_id = ?", (course_id,))
        cursor.execute("DELETE FROM class_instances WHERE schedule_id IN (SELECT schedule_id FROM schedule WHERE course_id = ?)", (course_id,))
        cursor.execute("DELETE FROM courses WHERE course_id = ?", (course_id,))
        conn.commit()
        flash('Course deleted successfully', 'success')
    
    cursor.close()
    conn.close()
    return redirect(url_for('manage_courses'))


@app.route('/professor/course/<int:course_id>/students')
@login_required
@role_required('professor')
def course_students(course_id):
    """View all students in a course with attendance stats"""
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verify ownership
    cursor.execute("SELECT * FROM courses WHERE course_id = ? AND professor_id = ?", (course_id, professor_id))
    course = fetchone_dict(cursor)
    
    if not course:
        flash('Access denied', 'danger')
        return redirect(url_for('manage_courses'))
    
    # Get all students with attendance
    cursor.execute("""
        SELECT u.user_id, u.full_name, u.email,
               COUNT(DISTINCT CASE WHEN a.status IN ('present','late') THEN a.attendance_id END) as attended,
               COUNT(DISTINCT ci.instance_id) as total_classes,
               ROUND(CAST(COUNT(DISTINCT CASE WHEN a.status IN ('present','late') THEN a.attendance_id END) AS FLOAT) / 
                     NULLIF(COUNT(DISTINCT ci.instance_id), 0) * 100, 1) as percentage
        FROM users u
        JOIN enrollments e ON u.user_id = e.student_id
        JOIN schedule s ON e.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= DATE('now') AND ci.status != 'cancelled'
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id AND a.student_id = u.user_id
        WHERE e.course_id = ?
        GROUP BY u.user_id, u.full_name, u.email
        ORDER BY u.full_name
    """, (course_id,))
    students = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return render_template('course_students.html', course=course, students=students)

@app.route('/professor/course/<int:course_id>/mark-attendance', methods=['GET', 'POST'])
@login_required
@role_required('professor')
def mark_course_attendance(course_id):
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get today's class instance for this course
    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE c.course_id = ? AND c.professor_id = ? AND ci.class_date = DATE('now')
    """, (course_id, professor_id))
    class_info = fetchone_dict(cursor)
    
    if not class_info:
        cursor.close()
        conn.close()
        flash('No class scheduled today for this course', 'warning')
        return redirect(url_for('manage_courses'))
    
    if request.method == 'POST':
        for key, value in request.form.items():
            if key.startswith('student_'):
                student_id = key.replace('student_', '')
                status = value
                cursor.execute("SELECT attendance_id FROM attendance WHERE instance_id = ? AND student_id = ?",
                               (class_info['instance_id'], student_id))
                existing = fetchone_dict(cursor)
                if existing:
                    cursor.execute("UPDATE attendance SET status = ?, marked_by = ? WHERE instance_id = ? AND student_id = ?",
                                   (status, professor_id, class_info['instance_id'], student_id))
                else:
                    cursor.execute("INSERT INTO attendance (instance_id, student_id, status, marked_by) VALUES (?,?,?,?)",
                                   (class_info['instance_id'], student_id, status, professor_id))
        conn.commit()
        cursor.close()
        conn.close()
        flash('Attendance saved!', 'success')
        return redirect(url_for('manage_courses'))
    
    # GET: Show student list with current status
    cursor.execute("""
        SELECT u.user_id, u.full_name, u.email,
               a.status as current_status
        FROM users u
        JOIN enrollments e ON u.user_id = e.student_id
        LEFT JOIN attendance a ON a.instance_id = ? AND a.student_id = u.user_id
        WHERE e.course_id = ?
        ORDER BY u.full_name
    """, (class_info['instance_id'], course_id))
    students = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return render_template('mark_attendance.html', class_info=class_info, students=students)


@app.route('/professor/course/<int:course_id>/send-count', methods=['POST'])
@login_required
@role_required('professor')
def send_class_count(course_id):
    """Send today's class attendance count to admin"""
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get today's attendance summary
    cursor.execute("""
        SELECT c.course_code, c.course_name,
               COUNT(DISTINCT a.attendance_id) as total_marked,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present,
               SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent,
               SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late
        FROM courses c
        JOIN schedule s ON c.course_id = s.course_id
        JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date = DATE('now')
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id
        WHERE c.course_id = ? AND c.professor_id = ?
        GROUP BY c.course_code, c.course_name
    """, (course_id, professor_id))
    
    data = fetchone_dict(cursor)
    
    if data:
        # Find admin
        cursor.execute("SELECT user_id FROM users WHERE role = 'admin' LIMIT 1")
        admin = fetchone_dict(cursor)
        
        if admin:
            content = f"📊 Attendance Report - {data['course_code']}\n"
            content += f"Present: {data['present']} | Absent: {data['absent']} | Late: {data['late']} | Total: {data['total_marked']}"
            
            cursor.execute("INSERT OR IGNORE INTO conversations (user1_id, user2_id) VALUES (?,?)", 
                          (professor_id, admin['user_id']))
            cursor.execute("SELECT conv_id FROM conversations WHERE user1_id=? AND user2_id=?", 
                          (professor_id, admin['user_id']))
            conv = fetchone_dict(cursor)
            
            cursor.execute("INSERT INTO messages (conv_id, sender_id, content) VALUES (?,?,?)",
                          (conv['conv_id'], professor_id, content))
            conn.commit()
            flash('Attendance count sent to admin!', 'success')
        else:
            flash('No admin found', 'danger')
    else:
        flash('No class held today for this course', 'warning')
    
    cursor.close()
    conn.close()
    return redirect(url_for('manage_courses'))


   
# ==================== ADMIN ROUTES ====================
@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    conn = get_db_connection()
    if not conn:
        flash('Database error', 'danger')
        return redirect(url_for('logout'))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'student'")
    student_count = fetchone_dict(cursor)['count']
    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'professor'")
    professor_count = fetchone_dict(cursor)['count']
    cursor.execute("SELECT COUNT(*) AS count FROM courses")
    course_count = fetchone_dict(cursor)['count']
    cursor.execute("SELECT COUNT(*) AS count FROM class_instances WHERE class_date = DATE('now')")
    today_classes = fetchone_dict(cursor)['count']
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html',
                           student_count=student_count, professor_count=professor_count,
                           course_count=course_count, today_classes=today_classes)


@app.route('/admin/generate_attendance', methods=['POST'])
@login_required
@role_required('admin')
def generate_random_attendance():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.instance_id, s.course_id
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        WHERE ci.class_date <= DATE('now')
    """)
    instances = fetchall_dict(cursor)
    for inst in instances:
        cursor.execute("SELECT student_id FROM enrollments WHERE course_id = ?", (inst['course_id'],))
        students = fetchall_dict(cursor)
        for stu in students:
            r = random.random()
            if r < 0.7:
                status = 'present'
            elif r < 0.85:
                status = 'absent'
            elif r < 0.95:
                status = 'late'
            else:
                status = 'excused'
            cursor.execute("""
                INSERT INTO attendance (instance_id, student_id, status, marked_by, marked_at)
                SELECT ?, ?, ?, ?, DATETIME('now')
                WHERE NOT EXISTS (SELECT 1 FROM attendance WHERE instance_id = ? AND student_id = ?)
            """, (inst['instance_id'], stu['student_id'], status, inst['course_id'],
                  inst['instance_id'], stu['student_id']))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Random attendance generated for past classes', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/professor_activity')
@login_required
@role_required('admin')
def professor_activity():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.user_id, u.full_name,
               COUNT(DISTINCT ci.instance_id) AS total_classes,
               COUNT(DISTINCT CASE WHEN a.attendance_id IS NOT NULL THEN ci.instance_id END) AS marked_count,
               ROUND(CAST(COUNT(DISTINCT CASE WHEN a.attendance_id IS NOT NULL THEN ci.instance_id END) AS FLOAT) /
                     NULLIF(COUNT(DISTINCT ci.instance_id), 0) * 100, 1) AS completion_percentage
        FROM users u
        LEFT JOIN courses c ON u.user_id = c.professor_id
        LEFT JOIN schedule s ON c.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= DATE('now')
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id
        WHERE u.role = 'professor'
        GROUP BY u.user_id, u.full_name
        ORDER BY u.full_name
    """)
    professors = []
    for row in cursor.fetchall():
        professors.append({
            'user_id': row[0],
            'full_name': row[1],
            'total_classes': row[2] or 0,
            'marked_count': row[3] or 0,
            'completion_percentage': row[4] if row[4] is not None else 0
        })
    cursor.close()
    conn.close()
    return render_template('professor_activity.html', professors=professors)


@app.route('/professor/send_report', methods=['POST'])
@login_required
@role_required('professor')
def send_attendance_report():
    professor_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE role = 'admin'")
    admin = fetchone_dict(cursor)
    if not admin:
        flash('No admin user found', 'danger')
        return redirect(url_for('professor_dashboard'))
    cursor.execute("""
        SELECT c.course_code, COUNT(a.attendance_id) AS total_marked,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) AS present
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id
        WHERE ci.class_date = DATE('now') AND c.professor_id = ?
        GROUP BY c.course_code
    """, (professor_id,))
    summary = fetchall_dict(cursor)
    content = "Today's Attendance Report:\n"
    for row in summary:
        content += f"{row['course_code']}: {row['present']}/{row['total_marked']} present\n"
    cursor.execute("""
        SELECT conv_id FROM conversations
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    """, (professor_id, admin['user_id'], admin['user_id'], professor_id))
    conv = fetchone_dict(cursor)
    if not conv:
        cursor.execute("INSERT INTO conversations (user1_id, user2_id) VALUES (?, ?)",
                       (professor_id, admin['user_id']))
        conn.commit()
        conv_id = cursor.lastrowid
    else:
        conv_id = conv['conv_id']
    cursor.execute("INSERT INTO messages (conv_id, sender_id, content) VALUES (?, ?, ?)",
                   (conv_id, professor_id, content))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Report sent to admin', 'success')
    return redirect(url_for('professor_dashboard'))


@app.route('/admin/generate_instances', methods=['POST'])
@login_required
@role_required('admin')
def trigger_generate_instances():
    count = generate_class_instances()
    flash(f'Generated {count} class instances', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/my-analytics')
@login_required
@role_required('student')
def my_analytics():
    """Student's personal analytics"""
    return render_template('my_analytics.html')

@app.route('/api/my-attendance-data')
@login_required
def api_my_attendance():
    """Get logged-in student's attendance summary"""
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.course_code, c.course_name,
               COUNT(DISTINCT a.attendance_id) as attended,
               COUNT(DISTINCT ci.instance_id) as total_classes,
               ROUND(CAST(COUNT(DISTINCT a.attendance_id) AS FLOAT) / NULLIF(COUNT(DISTINCT ci.instance_id), 0) * 100, 1) as percentage
        FROM courses c
        JOIN enrollments e ON c.course_id = e.course_id
        LEFT JOIN schedule s ON c.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= DATE('now')
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id AND a.student_id = ? AND a.status IN ('present', 'late')
        WHERE e.student_id = ?
        GROUP BY c.course_code, c.course_name
    """, (user_id, user_id))
    
    data = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return jsonify(data)

# ==================== MESSAGING ====================
@app.route('/messages')
@login_required
def message_list():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.conv_id,
               CASE WHEN c.user1_id = ? THEN u2.user_id ELSE u1.user_id END AS other_user_id,
               CASE WHEN c.user1_id = ? THEN u2.full_name ELSE u1.full_name END AS other_name,
               CASE WHEN c.user1_id = ? THEN u2.role ELSE u1.role END AS other_role,
               (SELECT content FROM messages WHERE conv_id = c.conv_id ORDER BY sent_at DESC LIMIT 1) AS last_message,
               (SELECT sent_at FROM messages WHERE conv_id = c.conv_id ORDER BY sent_at DESC LIMIT 1) AS last_time
        FROM conversations c
        JOIN users u1 ON c.user1_id = u1.user_id
        JOIN users u2 ON c.user2_id = u2.user_id
        WHERE c.user1_id = ? OR c.user2_id = ?
        ORDER BY last_time DESC
    """, (user_id, user_id, user_id, user_id, user_id))
    convs = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('messaging.html', conversations=convs)


@app.route('/messages/<int:user_id>')
@login_required
def message_thread(user_id):
    current_user = session['user_id']
    conn = get_db_connection()
    if not conn:
        flash("Database error", "danger")
        return redirect(url_for('message_list'))
    cursor = conn.cursor()
    cursor.execute("""
        SELECT conv_id FROM conversations
        WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)
    """, (current_user, user_id, user_id, current_user))
    row = fetchone_dict(cursor)
    if row:
        conv_id = row['conv_id']
    else:
        cursor.execute("INSERT INTO conversations (user1_id, user2_id) VALUES (?, ?)",
                       (current_user, user_id))
        conn.commit()
        conv_id = cursor.lastrowid
    cursor.execute("""
        SELECT m.*, u.full_name AS sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.user_id
        WHERE m.conv_id = ? ORDER BY m.sent_at
    """, (conv_id,))
    messages = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('message_thread.html', messages=messages, conv_id=conv_id)


@app.route('/messages/<int:conv_id>/send', methods=['POST'])
@login_required
def send_message(conv_id):
    content = request.form.get('content')
    sender_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO messages (conv_id, sender_id, content) VALUES (?, ?, ?)",
                   (conv_id, sender_id, content))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(request.referrer)


@app.route('/messages/new')
@login_required
def new_message():
    current_user = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, full_name, role, department FROM users WHERE user_id != ? ORDER BY role, full_name",
                   (current_user,))
    users = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('new_message.html', users=users)


# ==================== NAVIGATION ====================
@app.route('/navigation', methods=['GET'])
@login_required
def navigation():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT location_id, name, latitude, longitude FROM locations")
    locations = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('navigation.html', locations=locations)

# ==================== AI CHATBOT ====================
import chatbot


@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot_page():
    if request.method == 'POST':
        user_msg = request.form.get('message')
        bot_reply = chatbot.get_bot_response(user_msg)
        return jsonify({'reply': bot_reply})
    return render_template('chatbot.html')


# ==================== CUSTOM ATTENDANCE THRESHOLD ====================
@app.route('/set_threshold', methods=['POST'])
@login_required
@role_required('student')
def set_threshold():
    threshold = request.form.get('threshold')
    if threshold and threshold.isdigit():
        threshold = int(threshold)
        if 0 <= threshold <= 100:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET custom_attendance_threshold = ? WHERE user_id = ?",
                           (threshold, session['user_id']))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Attendance threshold updated', 'success')
    return redirect(url_for('student_dashboard'))


# ==================== ISSUES ====================
@app.route('/report_issue', methods=['GET', 'POST'])
@login_required
def report_issue():
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        category_id = request.form.get('category')
        title = request.form.get('title')
        description = request.form.get('description')
        location_id = request.form.get('location') or None
        reporter_id = session['user_id']
        cursor.execute("""
            INSERT INTO issues (reporter_id, category_id, title, description, location_id, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (reporter_id, category_id, title, description, location_id))
        conn.commit()
        flash('Issue reported successfully', 'success')
        return redirect(url_for('list_issues'))
    cursor.execute("SELECT * FROM issue_categories")
    categories = fetchall_dict(cursor)
    cursor.execute("SELECT location_id, name FROM locations")
    locations = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('report_issue.html', categories=categories, locations=locations)


@app.route('/issues')
@login_required
def list_issues():
    role = session.get('role')
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if role == 'student':
        cursor.execute("""
            SELECT i.*, ic.name as category_name
            FROM issues i
            JOIN issue_categories ic ON i.category_id = ic.cat_id
            WHERE i.reporter_id = ?
            ORDER BY i.created_at DESC
        """, (user_id,))
    else:
        cursor.execute("""
            SELECT i.*, ic.name as category_name, u.full_name as reporter_name
            FROM issues i
            JOIN issue_categories ic ON i.category_id = ic.cat_id
            JOIN users u ON i.reporter_id = u.user_id
            ORDER BY i.created_at DESC
        """)
    
    issues = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return render_template('issues_list.html', issues=issues, role=role)


@app.route('/issues/<int:issue_id>', methods=['GET', 'POST'])
@login_required
def issue_detail(issue_id):
    role = session.get('role')
    user_id = session.get('user_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        status = request.form.get('status')
        if status:
            cursor.execute("UPDATE issues SET status = ? WHERE issue_id = ?", (status, issue_id))
            conn.commit()
            flash('Status updated!', 'success')
            return redirect(url_for('list_issues'))
    
    cursor.execute("""
        SELECT i.*, ic.name as category_name, u.full_name as reporter_name
        FROM issues i
        JOIN issue_categories ic ON i.category_id = ic.cat_id
        JOIN users u ON i.reporter_id = u.user_id
        WHERE i.issue_id = ?
    """, (issue_id,))
    issue = fetchone_dict(cursor)
    cursor.close()
    conn.close()
    
    return render_template('issue_detail.html', issue=issue, role=role)

# ==================== FACE RECOGNITION ====================
import base64
import os

@app.route('/face-recognition')
@login_required
def face_recognition_page():
    return render_template('face_recognition.html')


@app.route('/api/face/register', methods=['POST'])
@login_required
def api_register_face():
    """Register face image for a user"""
    data = request.json
    image_data = data.get('image', '')
    user_id = session['user_id']
    
    try:
        # Decode base64 image
        import re
        
        # Remove the data:image/... prefix if present
        image_data = re.sub('^data:image/.+;base64,', '', image_data)
        image_bytes = base64.b64decode(image_data)
        
        # Ensure faces directory exists
        faces_dir = os.path.join('static', 'faces')
        os.makedirs(faces_dir, exist_ok=True)
        
        # Save face image
        face_path = f'static/faces/user_{user_id}.jpg'
        with open(face_path, 'wb') as f:
            f.write(image_bytes)
        
        # Store in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create user_faces table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_faces (
                face_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                face_image_path TEXT,
                is_active INTEGER DEFAULT 1,
                registered_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # Deactivate old faces
        cursor.execute("UPDATE user_faces SET is_active = 0 WHERE user_id = ?", (user_id,))
        
        # Insert new face
        cursor.execute("""
            INSERT INTO user_faces (user_id, face_image_path, is_active)
            VALUES (?, ?, 1)
        """, (user_id, face_path))
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Face registered successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/face/mark-attendance', methods=['POST'])
@login_required
def api_mark_attendance_face():
    """Mark attendance using face verification"""
    data = request.json
    instance_id = data.get('instance_id')
    
    if not instance_id:
        return jsonify({'success': False, 'message': 'No class selected'})
    
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if face is registered
    cursor.execute("SELECT * FROM user_faces WHERE user_id = ? AND is_active = 1", (user_id,))
    face = fetchone_dict(cursor)
    
    if not face:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Please register your face first. <a href="/face-recognition">Click here</a>'})
    
    # Check if already marked
    cursor.execute("SELECT * FROM attendance WHERE instance_id = ? AND student_id = ?", (instance_id, user_id))
    existing = fetchone_dict(cursor)
    
    if existing:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': 'Attendance already marked for this class!'})
    
    # Mark attendance
    cursor.execute("""
        INSERT INTO attendance (instance_id, student_id, status, marked_by, marked_at)
        VALUES (?, ?, 'present', ?, DATETIME('now'))
    """, (instance_id, user_id, user_id))
    conn.commit()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'message': '✅ Attendance marked successfully!'})

@app.route('/api/student/today-classes')
@login_required
@role_required('student')
def api_today_classes():
    """Get today's classes for the student"""
    user_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT ci.instance_id, c.course_code, c.course_name, s.start_time
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        JOIN enrollments e ON c.course_id = e.course_id
        WHERE ci.class_date = DATE('now')
        AND e.student_id = ?
        AND ci.status != 'cancelled'
        ORDER BY s.start_time
    """, (user_id,))
    
    classes = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return jsonify(classes)


@app.route('/api/professor/today-classes')
@login_required
@role_required('professor')
def api_professor_today_classes():
    """Get today's classes for the professor"""
    professor_id = session['user_id']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date = DATE('now')
        AND c.professor_id = ?
        AND ci.status != 'cancelled'
        ORDER BY s.start_time
    """, (professor_id,))
    
    classes = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return jsonify(classes)   

# ==================== NOTIFICATIONS ====================
@app.route('/api/notifications')
@login_required
def api_get_notifications():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY timestamp DESC LIMIT 20
    """, (user_id,))
    notifs = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return jsonify(notifs)


@app.route('/api/notifications/mark-read', methods=['POST'])
@login_required
def api_mark_notifications_read():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/unread_count')
def api_unread_count():
    if 'user_id' not in session:
        return {'count': 0}
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) AS unread_count
        FROM messages m
        JOIN conversations c ON m.conv_id = c.conv_id
        WHERE (c.user1_id = ? OR c.user2_id = ?) AND m.sender_id != ? AND m.is_read = 0
    """, (user_id, user_id, user_id))
    result = cursor.fetchone()
    count = result[0] if result and result[0] else 0
    cursor.close()
    conn.close()
    return {'count': count}


# ==================== ANALYTICS ROUTES ====================
@app.route('/analytics')
@login_required
@role_required('professor', 'admin')
def analytics_dashboard():
    """Analytics dashboard page"""
    return render_template('analytics.html')


@app.route('/api/analytics/course/<int:course_id>/trends')
@login_required
@role_required('professor', 'admin')
def api_course_trends(course_id):
    """Get attendance trends for a course"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ci.class_date,
               COUNT(DISTINCT a.student_id) as present_count,
               COUNT(DISTINCT e.student_id) as total_students
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id AND a.status IN ('present', 'late')
        LEFT JOIN enrollments e ON s.course_id = e.course_id
        WHERE s.course_id = ? AND ci.class_date >= DATE('now', '-84 days')
        GROUP BY ci.class_date
        ORDER BY ci.class_date
    """, (course_id,))
    data = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route('/api/analytics/at-risk-students')
@login_required
@role_required('professor', 'admin')
def api_at_risk_students():
    """Get at-risk students"""
    threshold = request.args.get('threshold', 75, type=int)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.full_name, c.course_code, c.course_name,
               COUNT(DISTINCT a.attendance_id) as attended,
               COUNT(DISTINCT ci.instance_id) as total_classes,
               ROUND(CAST(COUNT(DISTINCT a.attendance_id) AS FLOAT) / NULLIF(COUNT(DISTINCT ci.instance_id), 0) * 100, 1) as percentage
        FROM users u
        JOIN enrollments e ON u.user_id = e.student_id
        JOIN courses c ON e.course_id = c.course_id
        LEFT JOIN schedule s ON c.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= DATE('now')
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id AND a.student_id = u.user_id AND a.status IN ('present', 'late')
        WHERE u.role = 'student'
        GROUP BY u.user_id, u.full_name, c.course_code, c.course_name
        HAVING percentage < ?
        ORDER BY percentage ASC
    """, (threshold,))
    data = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return jsonify(data)


@app.route('/debug/db')
def debug_db():
    return "Connected to database: attendify.db (SQLite)"

@app.route('/admin/special_days', methods=['GET','POST'])
@login_required
@role_required('admin')
def special_days():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT day_of_week FROM schedule ORDER BY day_of_week")
    days = fetchall_dict(cursor)
    
    if request.method == "POST":
        class_date = request.form['class_date']
        follow_day = request.form['follow_day']
        note = request.form.get('note', '')
        admin_id = session['user_id']
        
        cursor.execute("""
            INSERT INTO special_class_days (class_date, follow_day, created_by, note)
            VALUES (?, ?, ?, ?)
        """, (class_date, follow_day, admin_id, note))
        conn.commit()
        
        # Generate class instances for this special day
        cursor.execute("SELECT schedule_id FROM schedule WHERE day_of_week = ?", (follow_day,))
        schedules = fetchall_dict(cursor)
        for s in schedules:
            cursor.execute("""
                INSERT INTO class_instances (schedule_id, class_date, status)
                VALUES (?, ?, 'scheduled')
            """, (s['schedule_id'], class_date))
        conn.commit()
        flash("Special class day created!", "success")
    
    cursor.execute("SELECT * FROM special_class_days ORDER BY class_date DESC")
    special_days = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    
    return render_template("admin_special_days.html", days=days, special_days=special_days)

# ==================== QUIZ ROUTES (Working, No AI) ====================

BUILTIN_QUESTIONS = [
    {
        "question": "What does DBMS stand for?",
        "type": "mcq",
        "options": {"A":"Database Management System","B":"Data Backup Management Software","C":"Double Byte Management System","D":"None"},
        "correct":"A","marks":1
    },
    {
        "question": "Which is an operating system?",
        "type": "mcq",
        "options": {"A":"Python","B":"Linux","C":"MySQL","D":"HTML"},
        "correct":"B","marks":1
    },
    {
        "question": "Explain normalization in databases.",
        "type":"short_answer",
        "correct":"normalization reduces redundancy",
        "marks":3
    }
]

@app.route('/quiz/create', methods=['GET','POST'])
@login_required
@role_required('professor','admin')
def create_quiz():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        title = request.form.get('title')
        description = request.form.get('description','')
        quiz_type = request.form.get('quiz_type','mcq')
        time_limit = request.form.get('time_limit', type=int) or None
        start_time = request.form.get('start_time')
        end_time = request.form.get('end_time')
        total_marks = request.form.get('total_marks',0, type=int)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO quizzes (course_id, title, description, quiz_type, time_limit, start_time, end_time, total_marks, created_by, ai_generated)
            VALUES (?,?,?,?,?,?,?,?,?,0)
        """, (course_id, title, description, quiz_type, time_limit, start_time, end_time, total_marks, session['user_id']))
        quiz_id = cursor.lastrowid

        # Add matching questions from built‑in bank
        for q in BUILTIN_QUESTIONS:
            if quiz_type == 'mcq' and q['type'] != 'mcq': continue
            if quiz_type == 'short_answer' and q['type'] != 'short_answer': continue
            if q['type'] == 'mcq':
                cursor.execute("""
                    INSERT INTO quiz_questions (quiz_id, question_text, question_type, option_a, option_b, option_c, option_d, correct_answer, marks, ai_generated)
                    VALUES (?,?,?,?,?,?,?,?,?,0)
                """, (quiz_id, q['question'], q['type'], q['options']['A'], q['options']['B'], q['options']['C'], q['options']['D'], q['correct'], q['marks']))
            else:
                cursor.execute("""
                    INSERT INTO quiz_questions (quiz_id, question_text, question_type, correct_answer, marks, ai_generated)
                    VALUES (?,?,?,?,?,0)
                """, (quiz_id, q['question'], q['type'], q['correct'], q['marks']))
        conn.commit()
        cursor.close(); conn.close()
        flash('Quiz created with questions!','success')
        return redirect(url_for('manage_quizzes'))

    conn = get_db_connection()
    cursor = conn.cursor()
    if session['role'] == 'admin':
        cursor.execute("SELECT course_id, course_name, course_code FROM courses")
    else:
        cursor.execute("SELECT course_id, course_name, course_code FROM courses WHERE professor_id=?", (session['user_id'],))
    courses = fetchall_dict(cursor)
    cursor.close(); conn.close()
    return render_template('create_quiz.html', courses=courses)


@app.route('/quiz/manage')
@login_required
@role_required('professor','admin')
def manage_quizzes():
    conn = get_db_connection()
    cursor = conn.cursor()
    if session['role'] == 'admin':
        cursor.execute("SELECT * FROM quizzes ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM quizzes WHERE created_by=? ORDER BY created_at DESC", (session['user_id'],))
    quizzes = fetchall_dict(cursor)
    for quiz in quizzes:
        cursor.execute("SELECT COUNT(*) as cnt FROM quiz_attempts WHERE quiz_id=?", (quiz['quiz_id'],))
        quiz['attempts'] = cursor.fetchone()['cnt']
    cursor.close(); conn.close()
    return render_template('manage_quizzes.html', quizzes=quizzes)


@app.route('/quiz/results/<int:quiz_id>')
@login_required
@role_required('professor','admin')
def quiz_results(quiz_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM quizzes WHERE quiz_id=?", (quiz_id,))
    quiz = fetchone_dict(cursor)
    if not quiz: return "Quiz not found", 404
    cursor.execute("""
        SELECT a.*, u.full_name, u.email
        FROM quiz_attempts a
        JOIN users u ON a.student_id = u.user_id
        WHERE a.quiz_id=? AND a.end_time IS NOT NULL
        ORDER BY a.score DESC
    """, (quiz_id,))
    attempts = fetchall_dict(cursor)
    cursor.close(); conn.close()
    return render_template('quiz_results.html', quiz=quiz, attempts=attempts)


@app.route('/quiz/active')
@login_required
@role_required('student')
def active_quizzes():
    conn = get_db_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    cursor.execute("""
        SELECT q.*, c.course_name
        FROM quizzes q
        JOIN courses c ON q.course_id = c.course_id
        WHERE q.start_time <= ? AND q.end_time >= ?
        ORDER BY q.start_time
    """, (now, now))
    quizzes = fetchall_dict(cursor)
    for quiz in quizzes:
        cursor.execute("SELECT end_time FROM quiz_attempts WHERE quiz_id=? AND student_id=? AND end_time IS NOT NULL",
                       (quiz['quiz_id'], session['user_id']))
        quiz['submitted'] = cursor.fetchone() is not None
    cursor.close(); conn.close()
    return render_template('active_quizzes.html', quizzes=quizzes)


@app.route('/quiz/take/<int:quiz_id>', methods=['GET','POST'])
@login_required
@role_required('student')
def take_quiz(quiz_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT face_id FROM user_faces WHERE user_id=? AND is_active=1", (session['user_id'],))
    if not cursor.fetchone():
        flash('You must register your face before taking a quiz.','danger')
        return redirect(url_for('face_recognition_page'))

    cursor.execute("SELECT end_time FROM quiz_attempts WHERE quiz_id=? AND student_id=? AND end_time IS NOT NULL",
                   (quiz_id, session['user_id']))
    if cursor.fetchone():
        flash('You have already submitted this quiz.','warning')
        return redirect(url_for('active_quizzes'))

    cursor.execute("SELECT * FROM quizzes WHERE quiz_id=?", (quiz_id,))
    quiz = fetchone_dict(cursor)
    if not quiz: return "Quiz not found", 404

    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    if now < quiz['start_time'] or now > quiz['end_time']:
        flash('Quiz is not available at this time.','danger')
        return redirect(url_for('active_quizzes'))

    cursor.execute("SELECT start_time FROM quiz_attempts WHERE quiz_id=? AND student_id=? AND end_time IS NULL",
                   (quiz_id, session['user_id']))
    attempt = fetchone_dict(cursor)
    time_left = None
    if attempt:
        start = datetime.strptime(attempt['start_time'], '%Y-%m-%d %H:%M:%S')
        if quiz['time_limit']:
            deadline = start + timedelta(minutes=quiz['time_limit'])
            remaining = (deadline - datetime.now()).seconds // 60
            if remaining <= 0:
                flash('Time expired!','danger')
                return redirect(url_for('active_quizzes'))
            time_left = remaining

    if request.method == 'POST':
        if not attempt:
            cursor.execute("INSERT INTO quiz_attempts (quiz_id, student_id, start_time, face_verified) VALUES (?,?,datetime('now'),1)",
                           (quiz_id, session['user_id']))
            attempt_id = cursor.lastrowid
        else:
            attempt_id = attempt['attempt_id']

        total_score = 0
        for key, value in request.form.items():
            if key.startswith('q_'):
                qid = key.split('_')[1]
                student_answer = value
                cursor.execute("SELECT * FROM quiz_questions WHERE question_id=?", (qid,))
                q = fetchone_dict(cursor)
                marks_obt = 0
                is_correct = 0
                if q['question_type'] == 'mcq':
                    if student_answer.strip().lower() == q['correct_answer'].strip().lower():
                        marks_obt = q['marks']; is_correct = 1
                else:
                    if q['correct_answer'].lower() in student_answer.lower():
                        marks_obt = q['marks']; is_correct = 1
                total_score += marks_obt
                cursor.execute("""
                    INSERT INTO quiz_answers (attempt_id, question_id, student_answer, is_correct, marks_obtained)
                    VALUES (?,?,?,?,?)
                """, (attempt_id, qid, student_answer, is_correct, marks_obt))

        cursor.execute("UPDATE quiz_attempts SET end_time=datetime('now'), score=?, total_marks=? WHERE attempt_id=?",
                       (total_score, quiz['total_marks'], attempt_id))
        conn.commit()
        cursor.close(); conn.close()
        flash(f'Quiz submitted! You scored {total_score}/{quiz["total_marks"]}','success')
        return redirect(url_for('active_quizzes'))

    cursor.execute("SELECT * FROM quiz_questions WHERE quiz_id=? ORDER BY question_id", (quiz_id,))
    questions = fetchall_dict(cursor)
    cursor.close(); conn.close()
    return render_template('take_quiz.html', quiz=quiz, questions=questions, time_left=time_left)

init_db()    
# ==================== MAIN ====================
if __name__ == '__main__':
    initialize_total_lectures()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)