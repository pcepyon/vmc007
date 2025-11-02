"""
Django settings for data_ingestion project.
Minimal configuration for MVP with testing support.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(dotenv_path=BASE_DIR / '.env')

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-mvp-dev-key-change-in-production')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'data_ingestion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS settings
CORS_ALLOWED_ORIGINS_LIST = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

# Add production frontend URL from environment variable
FRONTEND_URL = os.environ.get('FRONTEND_URL')
if FRONTEND_URL:
    # Clean the URL (remove trailing slash if present)
    FRONTEND_URL = FRONTEND_URL.rstrip('/')
    CORS_ALLOWED_ORIGINS_LIST.append(FRONTEND_URL)
    print(f"[CORS] Added frontend URL: {FRONTEND_URL}")
else:
    print("[CORS] WARNING: FRONTEND_URL environment variable not set!")

# Also check for multiple frontend URLs (comma-separated)
ADDITIONAL_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '')
if ADDITIONAL_ORIGINS:
    for origin in ADDITIONAL_ORIGINS.split(','):
        origin = origin.strip().rstrip('/')
        if origin:
            CORS_ALLOWED_ORIGINS_LIST.append(origin)
            print(f"[CORS] Added additional origin: {origin}")

CORS_ALLOWED_ORIGINS = CORS_ALLOWED_ORIGINS_LIST
CORS_ALLOW_CREDENTIALS = True

# Print final CORS configuration for debugging
print(f"[CORS] Final allowed origins: {CORS_ALLOWED_ORIGINS}")

ROOT_URLCONF = 'data_ingestion.urls'

# Database - PostgreSQL via Supabase
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'postgres'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# For testing, use SQLite in-memory database
# Check both sys.argv and environment variable for pytest
import sys
if 'test' in sys.argv or 'pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [],
}

# Admin API Key Authentication (MVP Simplification)
ADMIN_API_KEY = os.environ.get('ADMIN_API_KEY', 'mvp-admin-key-123')

# File Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Security settings for production
if not DEBUG:
    # Railway uses X-Forwarded-Proto header - trust it to avoid redirect loops
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
