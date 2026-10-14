import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ams-sepm-college-project-secure-session-key-2026')
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'attendance_system.db')
    ADMIN_REGISTRATION_KEY = os.environ.get('ADMIN_REGISTRATION_KEY', os.environ.get('AMS_ADMIN_REGISTRATION_CODE', 'ADMIN@SEPM2026'))
    ATTENDANCE_THRESHOLD = 75.0  # Percentage required to be eligible for university exams
    DEBUG = True

