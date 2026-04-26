import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database import get_db_connection, fetchall_dict
import plotly.graph_objs as go
import plotly.utils
import json

class AnalyticsEngine:
    def __init__(self):
        pass
    
    def get_attendance_trends(self, course_id, weeks=12):
        """Get attendance trends over time"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ci.class_date,
                COUNT(DISTINCT a.student_id) as present_count,
                COUNT(DISTINCT e.student_id) as total_students,
                CAST(COUNT(DISTINCT a.student_id) AS FLOAT) / 
                NULLIF(COUNT(DISTINCT e.student_id), 0) * 100 as attendance_percentage
            FROM class_instances ci
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            LEFT JOIN attendance a ON ci.instance_id = a.instance_id AND a.status IN ('present', 'late')
            LEFT JOIN enrollments e ON s.course_id = e.course_id
            WHERE s.course_id = ?
                AND ci.class_date >= DATEADD(WEEK, -?, GETDATE())
            GROUP BY ci.class_date
            ORDER BY ci.class_date
        """, (course_id, weeks))
        
        data = fetchall_dict(cursor)
        cursor.close()
        conn.close()
        
        return data
    
    def get_student_risk_analysis(self, threshold=75):
        """Identify at-risk students"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            WITH student_attendance AS (
                SELECT 
                    u.user_id,
                    u.full_name,
                    c.course_code,
                    c.course_name,
                    COUNT(DISTINCT a.attendance_id) as attended,
                    COUNT(DISTINCT ci.instance_id) as total_classes,
                    CAST(COUNT(DISTINCT a.attendance_id) AS FLOAT) / 
                    NULLIF(COUNT(DISTINCT ci.instance_id), 0) * 100 as percentage
                FROM users u
                JOIN enrollments e ON u.user_id = e.student_id
                JOIN courses c ON e.course_id = c.course_id
                LEFT JOIN schedule s ON c.course_id = s.course_id
                LEFT JOIN class_instances ci ON s.schedule_id = ci.schedule_id
                LEFT JOIN attendance a ON ci.instance_id = a.instance_id 
                    AND a.student_id = u.user_id
                    AND a.status IN ('present', 'late')
                WHERE u.role = 'student'
                    AND ci.class_date <= GETDATE()
                GROUP BY u.user_id, u.full_name, c.course_code, c.course_name
            )
            SELECT * FROM student_attendance
            WHERE percentage < ?
            ORDER BY percentage ASC
        """, (threshold,))
        
        at_risk = fetchall_dict(cursor)
        cursor.close()
        conn.close()
        
        return at_risk
    
    def generate_course_heatmap(self):
        """Generate attendance heatmap data"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                DATENAME(WEEKDAY, ci.class_date) as day_of_week,
                DATEPART(HOUR, s.start_time) as hour,
                AVG(CASE WHEN a.status IN ('present', 'late') THEN 1.0 ELSE 0.0 END) * 100 as attendance_rate
            FROM class_instances ci
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            LEFT JOIN attendance a ON ci.instance_id = a.instance_id
            WHERE ci.class_date >= DATEADD(MONTH, -1, GETDATE())
            GROUP BY DATENAME(WEEKDAY, ci.class_date), DATEPART(HOUR, s.start_time)
            ORDER BY day_of_week, hour
        """)
        
        data = fetchall_dict(cursor)
        cursor.close()
        conn.close()
        
        return data
    
    def predict_future_attendance(self, student_id, course_id):
        """Predict future attendance using simple ML"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                ci.class_date,
                CASE WHEN a.status IN ('present', 'late') THEN 1 ELSE 0 END as attended
            FROM class_instances ci
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            LEFT JOIN attendance a ON ci.instance_id = a.instance_id 
                AND a.student_id = ?
            WHERE s.course_id = ?
                AND ci.class_date <= GETDATE()
            ORDER BY ci.class_date
        """, (student_id, course_id))
        
        history = fetchall_dict(cursor)
        cursor.close()
        conn.close()
        
        if len(history) < 5:
            return {"error": "Not enough data"}
        
        # Simple moving average prediction
        df = pd.DataFrame(history)
        df['moving_avg'] = df['attended'].rolling(window=3).mean()
        
        recent_trend = df['moving_avg'].tail(3).mean()
        total_classes = len(df)
        attended = df['attended'].sum()
        current_percentage = (attended / total_classes) * 100
        
        # Predict remaining classes
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as remaining
            FROM class_instances ci
            JOIN schedule s ON ci.schedule_id = s.schedule_id
            WHERE s.course_id = ?
                AND ci.class_date > GETDATE()
                AND ci.status != 'cancelled'
        """, (course_id,))
        
        remaining = fetchall_dict(cursor)[0]['remaining']
        cursor.close()
        conn.close()
        
        predicted_future_attended = recent_trend * remaining
        predicted_final = ((attended + predicted_future_attended) / 
                          (total_classes + remaining)) * 100
        
        return {
            "current_percentage": current_percentage,
            "predicted_final": predicted_final,
            "trend": "improving" if recent_trend > 0.7 else "declining",
            "risk_level": "high" if predicted_final < 75 else "medium" if predicted_final < 80 else "low"
        }

analytics = AnalyticsEngine()