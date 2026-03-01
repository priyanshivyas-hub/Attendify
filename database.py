import os
import psycopg2
import bcrypt


def get_db_connection():
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")

        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode="require"
        )

        print("POSTGRES CONNECTED")
        return conn

    except Exception as e:
        print("DB ERROR:", e)
        return None


def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def fetchone_dict(cursor):
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


def fetchall_dict(cursor):
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]