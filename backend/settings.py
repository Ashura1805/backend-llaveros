import os
from pathlib import Path
import dj_database_url 

# 🔥 IMPORTACIONES DE FIREBASE
import firebase_admin
from firebase_admin import credentials

try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# SEGURIDAD
SECRET_KEY = os.environ.get('SECRET_KEY', "django-insecure-clave-desarrollo")

# DEBUG: False en la nube (si detecta Railway), True en tu PC
DEBUG = 'RAILWAY_ENVIRONMENT' not in os.environ and 'K_SERVICE' not in os.environ

ALLOWED_HOSTS = ['*']

CSRF_TRUSTED_ORIGINS = [
    'https://llaveros-backend-1005201168643.us-central1.run.app',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.railway.app'
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'corsheaders',
    "rest_framework",
    "rest_framework.authtoken",
    "api",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Tu autenticación personalizada de Firebase (si la usas)
        # 'api.authentication.FirebaseAuthentication', 
        
        # Mantenemos las estándar
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10
}

AUTH_USER_MODEL = 'api.Cliente'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True
ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"

# ---------------------------------------------------------
# BASE DE DATOS
# ---------------------------------------------------------
# Nota: Trata de usar variables de entorno para la URL real en producción por seguridad
RAILWAY_DB_URL = "mysql://root:pMNjlBIWSLJLrNHvljdFpfqnCokDvvHl@nozomi.proxy.rlwy.net:31358/railway"

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', RAILWAY_DB_URL),
        conn_max_age=600,
        ssl_require=False
    )
}
# ---------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    { "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator" },
    { "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator" },
    { "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator" },
    { "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator" },
]

LANGUAGE_CODE = "es-ec"
TIME_ZONE = "America/Guayaquil"
USE_I18N = True
USE_TZ = True

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================================
# 📧 CONFIGURACIÓN DE CORREO (GMAIL)
# ==========================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'

# 🔥 CORRECCIÓN: Puerto 465 es el estándar para SSL
EMAIL_PORT = 465 
EMAIL_USE_SSL = True
EMAIL_USE_TLS = False

EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
EMAIL_TIMEOUT = 30 

# ==========================================
# 🔥 INICIALIZACIÓN DE FIREBASE ADMIN SDK
# ==========================================
# Esto permite que Django envíe notificaciones Push a los celulares
if not firebase_admin._apps:
    try:
        # Busca el archivo en la carpeta raíz del proyecto
        cred_path = os.path.join(BASE_DIR, 'serviceAccountKey.json')
        
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("--- FIREBASE: Iniciado desde Archivo Local: " + cred_path + " ---")
        else:
            # Opción B: Si usas variables de entorno en Railway (Más seguro)
            # Aquí podrías cargar el JSON desde una variable si lo configuras luego
            print("--- FIREBASE: No se encontró serviceAccountKey.json ---")
            
    except Exception as e:
        print(f"--- FIREBASE ERROR: {e} ---")