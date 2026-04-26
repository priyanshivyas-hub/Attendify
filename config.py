import os

class Config:
    SECRET_KEY = 'attendify-secret-key-2024'
    
    SQL_DATABASE = 'attendify.db'
    
    # Real Email Settings
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "en24it3010086@medicaps.ac.in"  # Your email (sender)
    MAIL_PASSWORD = "YOUR-ACTUAL-COLLEGE-PASSWORD"   # ← Just put your real password here