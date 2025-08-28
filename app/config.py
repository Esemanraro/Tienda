import os
from datetime import timedelta

class Config:
    # Security Keys - moved to environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32)
    CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY') or os.urandom(32)
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:////Users/frobertsv./CascadeProjects/ALOHA Tienda 2025/tienditas-aloha-app-2/tiendita.db'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Session Security
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'instance', 'tiendita.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload Security
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max-limit
    UPLOAD_FOLDER = os.path.join('static', 'images', 'toys')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Password Security
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPER = True
    PASSWORD_REQUIRE_LOWER = True
    PASSWORD_REQUIRE_NUMBERS = True
    
    # Rate Limiting
    RATELIMIT_DEFAULT = '100/hour'
    RATELIMIT_LOGIN = '5/minute'
    RATELIMIT_STORAGE_URL = 'memory://'
    MAX_LOGIN_ATTEMPTS = 5
    ACCOUNT_LOCKOUT_DURATION = 30  # minutes
    
    # Two-Factor Authentication
    ADMIN_2FA_REQUIRED = True
    ADMIN_2FA_ISSUER = 'Tienditas-Aloha'
    ADMIN_2FA_SECRET_LENGTH = 32
    
    # Age Verification
    MIN_AGE = 8
    MAX_AGE = 18
    REQUIRE_PARENTAL_CONSENT = True
    
    # Transaction Limits
    MAX_DAILY_TRANSACTION_AMOUNT = 50.0
    MAX_SINGLE_TRANSACTION_AMOUNT = 20.0
    MAX_DAILY_TRANSACTIONS = 10
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Logging Configuration
    SECURITY_LOG_FILENAME = 'security.log'
    TRANSACTION_LOG_FILENAME = 'transactions.log'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False
    
    # Override some security settings for development
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True

    # Ensure development uses the correct database file
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'tiendita-dev.db')

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Enhanced security for production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PREFERRED_URL_SCHEME = 'https'
