import os

class Config:
    SECRET_KEY = 'attendify-secret-key-2024'
    SQL_DATABASE = 'attendify.db'
    
    # Email settings
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "en24it3010086@medicaps.ac.in"
    
    # Read password from environment variable (set manually or in .env)
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')