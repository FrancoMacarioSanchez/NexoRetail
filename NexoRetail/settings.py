"""
Django settings for NexoRetail project.
Configurado para desarrollo local con PostgreSQL en Docker y Multi-Tenancy.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getevn('SECRET_KEY')


GEMINI_API_KEY =  os.getevn('GEMINI_API_KEY')
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
        'DIRS': [BASE_DIR / 'templates'], # <-- Agrega esta línea
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
# DATABASE (Conexión local a PostgreSQL en Docker)
# ==========================================

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'constructora_db',
        'USER': 'postgres',
        'PASSWORD': 'postgrespassword',
        'HOST': '127.0.0.1',
        'PORT': '5433', # <-- El nuevo puerto
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# Configurado para Argentina (ideal para corralones)
LANGUAGE_CODE = 'es-ar'
TIME_ZONE = 'America/Argentina/Buenos_Aires'

USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/default-auto-field/

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'