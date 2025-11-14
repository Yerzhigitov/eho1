import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///eko_slastin.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки администратора по умолчанию
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin123'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'admin@eko-slastin.kg'
    
    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)