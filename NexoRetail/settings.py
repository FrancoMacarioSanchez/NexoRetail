"""
Django settings for NexoRetail project.
Configurado para desarrollo local y producción en Render con Multi-Tenancy.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Cargar variables de entorno desde el archivo .env (solo aplica en local)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'clave-secreta-desarrollo-por-defecto')

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# Si DEBUG en el .env es "True", será verdadero, de lo contrario será False.
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']


# ==========================================
# MULTI-TENANCY CONFIGURATION (django-tenants)
# ==========================================

TENANT_MODEL = "customers.Client"
TENANT_DOMAIN_MODEL = "customers.Domain"

# Aplicaciones compartidas (globales)
SHARED_APPS = [
    'django_tenants',
    'customers', # App para gestionar los inquilinos (corralones) y sus dominios
    
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Aplicaciones que se replican por cada tenant (tus módulos del SaaS)
TENANT_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    
    # Tus apps del sistema mayorista de construcción:
    'productos',  # Inventario, Proveedores, Compras
    'sales',     # Ventas, Presupuestos, Clientes, Envíos
    'core',      # Empleados, Permisos, Informes
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

INSTALLED_APPS.append('rest_framework')
INSTALLED_APPS.append('django.contrib.humanize')


# ==========================================
# MIDDLEWARE
# ==========================================

MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware', # <-- Obligatorio primero para tenants
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'NexoRetail.urls'

# Router necesario para django-tenants
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'NexoRetail.wsgi.application'


# ==========================================
# DATABASE (Conexión dinámica Local/Render)
# ==========================================

# Configuración base (Local con Docker)
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'constructora_db',
        'USER': 'postgres',
        'PASSWORD': 'postgrespassword',
        'HOST': '127.0.0.1',
        'PORT': '5433',
    }
}

# Si existe DATABASE_URL (en Render), sobrescribe la configuración base
db_from_env = dj_database_url.config(
    default=os.getenv('DATABASE_URL'),
    engine='django_tenants.postgresql_backend',
    conn_max_age=600
)

if db_from_env:
    DATABASES['default'].update(db_from_env)


# ==========================================
# PASSWORD VALIDATION
# ==========================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==========================================
# INTERNATIONALIZATION
# ==========================================

LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True
USE_TZ = True


# ==========================================
# STATIC FILES
# ==========================================

STATIC_URL = 'static/'

# Directorio donde Render recolectará los archivos estáticos en producción
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'