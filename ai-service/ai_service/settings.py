"""
Django settings for ai_service project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-ai-service-change-me'
DEBUG = True
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'pgvector.django',
    'app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_service.wsgi.application'

DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.postgresql')

if DB_ENGINE == 'django.db.backends.sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': os.getenv('DB_POSTGRES_NAME', 'ktra1_ai_db'),
            'USER': os.getenv('DB_POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_POSTGRES_PASSWORD', '123456'),
            'HOST': os.getenv('DB_POSTGRES_HOST', 'postgres'),
            'PORT': os.getenv('DB_POSTGRES_PORT', '5432'),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AI_SERVICE_PORT = int(os.getenv('AI_SERVICE_PORT', '8005'))
CUSTOMER_SERVICE_URL = os.getenv('CUSTOMER_SERVICE_URL', 'http://127.0.0.1:8001')
PRODUCT_SERVICE_URL = os.getenv('PRODUCT_SERVICE_URL', 'http://127.0.0.1:8003')
KB_SERVICE_URL = os.getenv('KB_SERVICE_URL', 'http://127.0.0.1:8010')
LSTM_ARTIFACT_DIR = os.getenv('LSTM_ARTIFACT_DIR', str(BASE_DIR / 'artifacts' / 'lstm'))
LSTM_MAX_SEQ_LEN = int(os.getenv('LSTM_MAX_SEQ_LEN', '20'))
LSTM_EMBED_DIM = int(os.getenv('LSTM_EMBED_DIM', '64'))
LSTM_HIDDEN_DIM = int(os.getenv('LSTM_HIDDEN_DIM', '128'))

# Chat UI is embedded into customer pages via iframe from api-gateway.
X_FRAME_OPTIONS = 'ALLOWALL'
