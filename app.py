import json
import random
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps

from navigation import NavigationGraph
import chatbot
from config import Config
from database import get_db_connection, check_password, fetchone_dict, fetchall_dict
from utils.helpers import generate_class_instances

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY


# ==================== INIT TOTAL LECTURES ====================
def initialize_total_lectures():
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return
    cursor = conn.cursor()
    try:
        cursor.execute("""
        IF NOT EXISTS (
            SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'courses' AND COLUMN_NAME = 'total_lectures'
        )
        BEGIN
            ALTER TABLE courses ADD total_lectures INT NULL;
        END
        """)

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


# ==================== AUTH ====================
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
        "SELECT * FROM users WHERE LTRIM(RTRIM(LOWER(email))) = LOWER(?)",
        (email,)
    )

    user = fetchone_dict(cursor)

    cursor.close()
    conn.close()

    if user and check_password(password, user['password_hash']):
        session['user_id'] = user['user_id']
        session['role'] = user['role']
        session['full_name'] = user['full_name']
        return redirect(url_for('dashboard'))

    flash('Invalid email or password', 'danger')
    return redirect(url_for('index'))

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
        WHERE ci.class_date <= CAST(GETDATE() AS DATE)
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
                IF NOT EXISTS (SELECT 1 FROM attendance WHERE instance_id = ? AND student_id = ?)
                INSERT INTO attendance (instance_id, student_id, status, marked_by, marked_at)
                VALUES (?, ?, ?, ?, GETDATE())
            """, (inst['instance_id'], stu['student_id'],
                  inst['instance_id'], stu['student_id'], status, inst['course_id']))
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
               SUM(CASE WHEN a.marked_by IS NOT NULL THEN 1 ELSE 0 END) AS marked_count
        FROM users u
        LEFT JOIN courses c ON u.user_id = c.professor_id
        LEFT JOIN schedule s ON c.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= CAST(GETDATE() AS DATE)
        LEFT JOIN attendance a ON ci.instance_id = a.instance_id
        WHERE u.role = 'professor'
        GROUP BY u.user_id, u.full_name
    """)
    professors = fetchall_dict(cursor)
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
        WHERE ci.class_date = CAST(GETDATE() AS DATE) AND c.professor_id = ?
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
    if conv:
        conv_id = conv['conv_id']
    else:
        cursor.execute("""
        INSERT INTO conversations (user1_id, user2_id) 
        OUTPUT INSERTED.conv_id 
        VALUES (?, ?)
    """, (professor_id, admin['user_id']))

    inserted = fetchone_dict(cursor)
    conv_id = inserted['conv_id']    
    cursor.execute("INSERT INTO messages (conv_id, sender_id, content) VALUES (?, ?, ?)",
                   (conv_id, professor_id, content))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Report sent to admin', 'success')
    return redirect(url_for('professor_dashboard'))


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

    query = """
    SELECT 
        c.course_id,
        c.course_code,
        c.course_name,
        ISNULL(held.total_held, 0) AS total_held,
        ISNULL(att.attended, 0) AS attended,
        ISNULL(rem.remaining, 0) AS remaining,
        CASE 
            WHEN ISNULL(held.total_held, 0) > 0 
            THEN ROUND(100.0 * ISNULL(att.attended, 0) / held.total_held, 1)
            ELSE 0 
        END AS percentage
    FROM courses c
    OUTER APPLY (
        SELECT COUNT(DISTINCT ci.instance_id) AS total_held
        FROM schedule s
        JOIN class_instances ci ON s.schedule_id = ci.schedule_id
        WHERE s.course_id = c.course_id
          AND ci.class_date <= CAST(GETDATE() AS DATE)
          AND ci.status != 'cancelled'
    ) held
    OUTER APPLY (
        SELECT COUNT(DISTINCT a.attendance_id) AS attended
        FROM enrollments e
        JOIN schedule s ON s.course_id = c.course_id
        JOIN class_instances ci ON s.schedule_id = ci.schedule_id
        LEFT JOIN attendance a ON a.instance_id = ci.instance_id 
                              AND a.student_id = e.student_id
                              AND a.status IN ('present', 'late')
        WHERE e.student_id = ? AND e.course_id = c.course_id
          AND ci.class_date <= CAST(GETDATE() AS DATE)
          AND ci.status != 'cancelled'
    ) att
    OUTER APPLY (
        SELECT COUNT(DISTINCT ci.instance_id) AS remaining
        FROM schedule s
        JOIN class_instances ci ON s.schedule_id = ci.schedule_id
        WHERE s.course_id = c.course_id
          AND ci.class_date > CAST(GETDATE() AS DATE)
          AND ci.status != 'cancelled'
    ) rem
    WHERE c.course_id IN (SELECT course_id FROM enrollments WHERE student_id = ?)
    ORDER BY c.course_code
    """
    cursor.execute(query, (user_id, user_id))
    courses = fetchall_dict(cursor)

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

    cursor.execute("""
        SELECT * FROM holidays WHERE holiday_date >= CAST(GETDATE() AS DATE) 
        ORDER BY holiday_date OFFSET 0 ROWS FETCH NEXT 5 ROWS ONLY
    """)
    holidays = fetchall_dict(cursor)

    cursor.execute("SELECT custom_attendance_threshold FROM users WHERE user_id = ?", (user_id,))
    row = fetchone_dict(cursor)
    custom_threshold = row['custom_attendance_threshold'] if row and row['custom_attendance_threshold'] is not None else 75

    cursor.close()
    conn.close()

    return render_template('student_dashboard.html', courses=courses, disputes=disputes, holidays=holidays, custom_threshold=custom_threshold)


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

    cursor.execute("""
        SELECT 
            ci.instance_id,
            c.course_code,
            c.course_name,
            s.start_time,
            s.end_time,
            s.room,
            ci.status,
            (SELECT COUNT(*) FROM enrollments e WHERE e.course_id = c.course_id) AS total_students,
            (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id) AS marked,
            (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'present') AS present,
            (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'absent') AS absent,
            (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'late') AS late,
            (SELECT COUNT(*) FROM attendance a WHERE a.instance_id = ci.instance_id AND a.status = 'excused') AS excused
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date = CAST(GETDATE() AS DATE)
          AND c.professor_id = ?
          AND ci.status != 'cancelled'
        ORDER BY s.start_time
    """, (professor_id,))
    today_classes = fetchall_dict(cursor)

    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.room,
               ci.class_date, DATENAME(weekday, ci.class_date) AS day_name
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date > CAST(GETDATE() AS DATE)
          AND ci.class_date <= DATEADD(day, 7, CAST(GETDATE() AS DATE))
          AND c.professor_id = ?
          AND ci.status != 'cancelled'
        ORDER BY ci.class_date
    """, (professor_id,))
    upcoming_classes = fetchall_dict(cursor)

    cursor.execute("""
        SELECT c.course_code, c.course_name, c.total_lectures,
               COUNT(ci.instance_id) AS held_so_far,
               SUM(CASE WHEN ci.status = 'cancelled' THEN 1 ELSE 0 END) AS cancelled
        FROM courses c
        LEFT JOIN schedule s ON c.course_id = s.course_id
        LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id AND ci.class_date <= CAST(GETDATE() AS DATE)
        WHERE c.professor_id = ?
        GROUP BY c.course_code, c.course_name, c.total_lectures
    """, (professor_id,))
    course_summary = fetchall_dict(cursor)

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

    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.end_time, s.room,
               ci.cancellation_reason
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date = CAST(GETDATE() AS DATE)
          AND c.professor_id = ?
          AND ci.status = 'cancelled'
        ORDER BY s.start_time
    """, (professor_id,))
    cancelled_today = fetchall_dict(cursor)

    cursor.execute("""
        SELECT ci.instance_id, c.course_code, c.course_name, s.start_time, s.room,
               ci.class_date, DATENAME(weekday, ci.class_date) AS day_name,
               ci.cancellation_reason
        FROM class_instances ci
        JOIN schedule s ON ci.schedule_id = s.schedule_id
        JOIN courses c ON s.course_id = c.course_id
        WHERE ci.class_date > CAST(GETDATE() AS DATE)
          AND ci.class_date <= DATEADD(day, 7, CAST(GETDATE() AS DATE))
          AND c.professor_id = ?
          AND ci.status = 'cancelled'
        ORDER BY ci.class_date
    """, (professor_id,))
    cancelled_upcoming = fetchall_dict(cursor)

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

    # Verify ownership
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
    UPDATE class_instances 
    SET status = 'cancelled',
        cancellation_reason = ?
    WHERE instance_id = ?
""", (reason, instance_id))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Class cancelled', 'success')
    return redirect(url_for('professor_dashboard'))

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

    if row['class_date'] > datetime.now().date():
        flash('Cannot mark attendance for future classes', 'danger')
        cursor.close()
        conn.close()
        return redirect(url_for('professor_dashboard'))

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

    for key, value in request.form.items():
        if key.startswith('student_'):
            student_id = key.replace('student_', '')
            status = value
            cursor.execute("SELECT attendance_id FROM attendance WHERE instance_id = ? AND student_id = ?",
                           (instance_id, student_id))
            existing = fetchone_dict(cursor)
            if existing:
                cursor.execute("""
                    UPDATE attendance SET status = ?, marked_by = ?, marked_at = GETDATE()
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
        UPDATE class_instances 
        SET status = 'scheduled', cancellation_reason = NULL
        WHERE instance_id = ?
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
        cursor.execute("UPDATE attendance SET status = 'present' WHERE attendance_id = ?", 
                   (dispute['attendance_id'],))
        cursor.execute("UPDATE disputes SET status = 'approved' WHERE dispute_id = ?",
                   (dispute_id,))
        flash('Dispute approved', 'success')
    else:
        cursor.execute("UPDATE disputes SET status = 'rejected' WHERE dispute_id = ?",
                   (dispute_id,))
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
                SET location_type = ?, building = ?, room = ?, 
                    status = ?, notes = ?, updated_at = GETDATE()
                WHERE professor_id = ?
            """, (location_type, building, room, status, notes, professor_id))
        else:
            cursor.execute("""
                INSERT INTO professor_current_location
                (professor_id, location_type, building, room, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (professor_id, location_type, building, room, status, notes))

        cursor.execute("""
            INSERT INTO professor_location_history
            (professor_id, location_type, building, room, status, notes)
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
    cursor.execute("""
        SELECT *
        FROM vw_professor_live_status
        WHERE user_id = ?
    """, (professor_id,))
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
            'last_updated': location['updated_at'].strftime('%Y-%m-%d %H:%M') if location['updated_at'] else None
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
    cursor.execute("""
        SELECT *
        FROM vw_professor_live_status
        ORDER BY full_name
    """)
    professors = fetchall_dict(cursor)
    cursor.close()
    conn.close()
    return render_template('professor_locations.html', professors=professors)


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
    row = fetchone_dict(cursor)
    student_count = row['count'] if row else 0

    cursor.execute("SELECT COUNT(*) AS count FROM users WHERE role = 'professor'")
    row = fetchone_dict(cursor)
    professor_count = row['count'] if row else 0

    cursor.execute("SELECT COUNT(*) AS count FROM courses")
    row = fetchone_dict(cursor)
    course_count = row['count'] if row else 0

    cursor.execute("SELECT COUNT(*) AS count FROM class_instances WHERE class_date = CAST(GETDATE() AS DATE)")
    row = fetchone_dict(cursor)
    today_classes = row['count'] if row else 0

    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html',
                           student_count=student_count,
                           professor_count=professor_count,
                           course_count=course_count,
                           today_classes=today_classes)


@app.route('/admin/generate_instances', methods=['POST'])
@login_required
@role_required('admin')
def trigger_generate_instances():
    count = generate_class_instances()
    flash(f'Generated {count} class instances', 'success')
    return redirect(url_for('admin_dashboard'))


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
               (SELECT TOP 1 content FROM messages WHERE conv_id = c.conv_id ORDER BY sent_at DESC) AS last_message,
               (SELECT TOP 1 sent_at FROM messages WHERE conv_id = c.conv_id ORDER BY sent_at DESC) AS last_time
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

    # Step 1: Check if conversation already exists
    cursor.execute("""
        SELECT conv_id FROM conversations
        WHERE (user1_id = ? AND user2_id = ?)
           OR (user1_id = ? AND user2_id = ?)
    """, (current_user, user_id, user_id, current_user))

    row = fetchone_dict(cursor)

    if row:
        conv_id = row['conv_id']
    else:
        # Step 2: Create new conversation
        cursor.execute("""
            INSERT INTO conversations (user1_id, user2_id)
            VALUES (?, ?)
        """, (current_user, user_id))

        conn.commit()

        # Step 3: Fetch the newly created conversation
        cursor.execute("""
            SELECT conv_id FROM conversations
            WHERE (user1_id = ? AND user2_id = ?)
               OR (user1_id = ? AND user2_id = ?)
        """, (current_user, user_id, user_id, current_user))

        new_row = fetchone_dict(cursor)

        if not new_row:
            flash("Conversation creation failed", "danger")
            cursor.close()
            conn.close()
            return redirect(url_for('message_list'))

        conv_id = new_row['conv_id']

    # Step 4: Fetch messages
    cursor.execute("""
        SELECT m.*, u.full_name AS sender_name
        FROM messages m
        JOIN users u ON m.sender_id = u.user_id
        WHERE m.conv_id = ?
        ORDER BY m.sent_at
    """, (conv_id,))

    messages = fetchall_dict(cursor)

    # Step 5: Mark messages as read
    cursor.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE conv_id = ? AND sender_id != ?
    """, (conv_id, current_user))

    conn.commit()

    cursor.close()
    conn.close()

    return render_template(
        'message_thread.html',
        other_user_id=user_id,
        messages=messages,
        conv_id=conv_id
    )

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
    cursor.execute("""
        SELECT user_id, full_name, role, department
        FROM users
        WHERE user_id != ?
        ORDER BY role, full_name
    """, (current_user,))
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
            user_id = session['user_id']
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET custom_attendance_threshold = ? WHERE user_id = ?",
                           (threshold, user_id))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Attendance threshold updated', 'success')
    return redirect(url_for('student_dashboard'))


# ==================== ISSUES (Reporting & Workflow) ====================
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
            INSERT INTO issues (reporter_id, category_id, title, description, location_id)
            VALUES (?, ?, ?, ?, ?)
        """, (reporter_id, category_id, title, description, location_id))
        conn.commit()
        flash('Issue reported successfully', 'success')
        return redirect(url_for('student_dashboard'))
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
    user_id = session['user_id']
    role = session['role']
    conn = get_db_connection()
    cursor = conn.cursor()
    if role == 'student':
        cursor.execute("""
            SELECT i.*, ic.name AS category_name
            FROM issues i
            JOIN issue_categories ic ON i.category_id = ic.cat_id
            WHERE i.reporter_id = ?
            ORDER BY i.created_at DESC
        """, (user_id,))
    elif role in ('professor', 'admin'):
        cursor.execute("""
            SELECT i.*, ic.name AS category_name, u.full_name AS reporter_name
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
    user_id = session['user_id']
    role = session['role']
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        if 'status' in request.form:
            new_status = request.form.get('status')
            cursor.execute("UPDATE issues SET status = ? WHERE issue_id = ?", (new_status, issue_id))
        if 'assign' in request.form and role == 'admin':
            assign_to = request.form.get('assign_to')
            cursor.execute("UPDATE issues SET assigned_to = ? WHERE issue_id = ?", (assign_to, issue_id))
        if 'comment' in request.form:
            comment = request.form.get('comment')
            cursor.execute("INSERT INTO issue_comments (issue_id, user_id, comment) VALUES (?, ?, ?)",
                           (issue_id, user_id, comment))
        conn.commit()
    cursor.execute("""
        SELECT i.*, ic.name AS category_name, u_reporter.full_name AS reporter_name,
               u_assigned.full_name AS assigned_name
        FROM issues i
        JOIN issue_categories ic ON i.category_id = ic.cat_id
        JOIN users u_reporter ON i.reporter_id = u_reporter.user_id
        LEFT JOIN users u_assigned ON i.assigned_to = u_assigned.user_id
        WHERE i.issue_id = ?
    """, (issue_id,))
    issue = fetchone_dict(cursor)

    assignable_users = []
    if role in ('admin', 'professor'):
        cursor.execute("SELECT user_id, full_name FROM users WHERE role IN ('professor', 'admin')")
        assignable_users = fetchall_dict(cursor)

    cursor.execute("""
        SELECT c.*, u.full_name AS commenter_name
        FROM issue_comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.issue_id = ?
        ORDER BY c.created_at
    """, (issue_id,))
    comments = fetchall_dict(cursor)

    cursor.close()
    conn.close()
    return render_template('issue_detail.html', issue=issue, comments=comments,
                           assignable_users=assignable_users, role=role)


@app.route('/debug/db')
def debug_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DB_NAME() AS dbname")
    row = fetchone_dict(cursor)
    db_name = row['dbname'] if row else 'unknown'
    cursor.close()
    conn.close()
    return f"Connected to database: **{db_name}**"


@app.route('/api/unread_count')
@login_required
def unread_count():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*)
        FROM messages m
        JOIN conversations c ON m.conv_id = c.conv_id
        WHERE (c.user1_id = ? OR c.user2_id = ?) AND m.sender_id != ? AND m.is_read = 0
    """, (user_id, user_id, user_id))
    row = fetchone_dict(cursor)
    count = row['count'] if row else 0
    cursor.close()
    conn.close()
    return {'count': count}


# ==================== MAIN ====================
if __name__ == '__main__':
    initialize_total_lectures()
    app.run(debug=True)