import os
from dotenv import load_dotenv

load_dotenv()  # loads from .env

class Config:
    SECRET_KEY = 'attendify-secret-key-2024'
    SQL_DATABASE = 'attendify.db'
    
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "en24it3010086@medicaps.ac.in"
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')   # read from environment