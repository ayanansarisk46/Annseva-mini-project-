"""
================================================================================
AnnSeva - Configuration File (config.py)
================================================================================
College Viva Note:
This file loads environment variables from .env and sets up configuration
parameters for Flask, Database (MySQL with SQLite fallback), Maps, and Mail.

Why use config.py?
- Keeps sensitive credentials (passwords, secret keys) out of source code.
- Centralizes application settings so changes take effect across all modules.
================================================================================
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into environment
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Base Configuration Class for AnnSeva Application."""

    # Secret key for signing session cookies and CSRF tokens
    SECRET_KEY = os.getenv('SECRET_KEY', 'annseva-dev-key-change-in-production')

    # Hosted platforms provide a database URL directly.
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    # MySQL Database Connection Details
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'annseva_db')

    # Flag to determine whether to fallback to SQLite if MySQL is unavailable
    USE_SQLITE_FALLBACK = os.getenv('USE_SQLITE_FALLBACK', 'True').lower() in ('true', '1', 't')

    # Google Maps JavaScript API Key (Optional)
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')

    # Email notification settings (Flask-Mail / SMTP)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'noreply@annseva.org')

    # SQLAlchemy Track Modifications (disabled to save memory)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def get_database_uri(cls):
        """
        Dynamically determine Database URI.
        1. Uses a hosted DATABASE_URL when supplied.
        2. Attempts to connect to MySQL using PyMySQL locally.
        3. If MySQL is not running or fails, falls back cleanly to SQLite
           so the student project runs effortlessly without configuration errors.
        """
        if cls.DATABASE_URL:
            database_url = cls.DATABASE_URL
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url

        import pymysql
        try:
            # Test MySQL connection
            conn = pymysql.connect(
                host=cls.MYSQL_HOST,
                user=cls.MYSQL_USER,
                password=cls.MYSQL_PASSWORD,
                port=cls.MYSQL_PORT,
                connect_timeout=2
            )
            # Create database if it does not exist
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{cls.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            conn.close()

            # MySQL connection string
            # Format: mysql+pymysql://<user>:<password>@<host>:<port>/<database>
            if cls.MYSQL_PASSWORD:
                uri = f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"
            else:
                uri = f"mysql+pymysql://{cls.MYSQL_USER}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DB}"
            print("[INFO] Connected successfully to MySQL Database:", cls.MYSQL_DB)
            return uri
        except Exception as e:
            if cls.USE_SQLITE_FALLBACK:
                sqlite_path = os.path.join(BASE_DIR, 'annseva.db')
                print(f"[NOTE] MySQL connection not active ({e}).")
                print(f"[INFO] Using SQLite database for seamless development: {sqlite_path}")
                return f"sqlite:///{sqlite_path}"
            else:
                raise e
