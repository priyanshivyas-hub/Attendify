from datetime import datetime, timedelta
from database import get_db_connection  # absolute import

def generate_class_instances(days_ahead=30):
    """
    Generate class instances for the next N days based on schedule.
    Skips holidays.
    Returns number of instances created.
    """
    conn = get_db_connection()
    if not conn:
        return 0

    cursor = conn.cursor()

    # Get all active schedules
    cursor.execute("""
        SELECT s.*, c.course_id 
        FROM schedule s
        JOIN courses c ON s.course_id = c.course_id
    """)
    schedules = cursor.fetchall()

    # Get holidays for the period
    end_date = datetime.now() + timedelta(days=days_ahead)
    cursor.execute("""
        SELECT holiday_date FROM holidays 
        WHERE holiday_date BETWEEN CAST(GETDATE() AS DATE) AND %s
    """, (end_date.strftime('%Y-%m-%d'),))
    holidays = [row['holiday_date'] for row in cursor.fetchall()]

    # Day mapping (Monday=0, Sunday=6)
    day_map = {
        'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6
    }

    instances_created = 0
    today = datetime.now().date()

    for schedule in schedules:
        target_day = day_map[schedule['day_of_week']]

        for days_offset in range(days_ahead):
            check_date = today + timedelta(days=days_offset)

            if check_date.weekday() != target_day:
                continue
            if check_date in holidays:
                continue

            cursor.execute("""
                SELECT instance_id FROM class_instances 
                WHERE schedule_id = %s AND class_date = %s
            """, (schedule['schedule_id'], check_date))

            if not cursor.fetchone():
                try:
                    cursor.execute("""
                        INSERT INTO class_instances (schedule_id, class_date, status)
                        VALUES (%s, %s, 'scheduled')
                    """, (schedule['schedule_id'], check_date))
                    instances_created += 1
                    conn.commit()
                except Exception:
                    conn.rollback()

    cursor.close()
    conn.close()
    return instances_created