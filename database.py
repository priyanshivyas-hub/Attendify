import os
import psycopg2
import bcrypt

def get_db_connection():
    try:
        DATABASE_URL = os.environ.get("DATABASE_URL")
        if not DATABASE_URL:
            raise Exception("DATABASE_URL not found in environment variables")

        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        return conn

    except Exception as e:
        print("DATABASE ERROR:", e)
        return None


def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))