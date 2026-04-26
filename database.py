import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'attendify.db')

def get_db_connection():
    """Connect to SQLite database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        return conn
    except Exception as e:
        print("Connection error:", e)
        return None

def fetchone_dict(cursor):
    """Fetch one row as dictionary"""
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)

def fetchall_dict(cursor):
    """Fetch all rows as list of dictionaries"""
    rows = cursor.fetchall()
    if not rows:
        return []
    return [dict(row) for row in rows]