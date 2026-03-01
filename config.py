import os

class Config:
    SECRET_KEY = 'your-secret-key'           # Change to a random string
    SQL_SERVER = 'localhost'                  # or your server name (e.g., 'LAPTOP-T3LOQ03A\SQLEXPRESS')
    SQL_DATABASE = 'attendify'
    SQL_USERNAME = 'attendify_user'           # SQL Server login username
    SQL_PASSWORD = 'P@ssw0rd123'              # password for that login
    # If using Windows Authentication, set SQL_USERNAME and SQL_PASSWORD to empty strings
    # and modify database.py to use trusted=True