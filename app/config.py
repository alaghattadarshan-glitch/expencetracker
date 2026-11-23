import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'expense_tracker_secret_devops_2026')
    DEBUG = os.getenv('FLASK_DEBUG', '0') == '1'
    PORT = int(os.getenv('PORT', 5000))
    
    # Database Settings
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_NAME = os.getenv('DB_NAME', 'expense_tracker')
    DB_USER = os.getenv('DB_USER', 'expense_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'expense_password')
