from pathlib import Path
import environ
import ast
import os

# Set the base directory using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ and read from .env using pathlib
env = environ.Env()

# env = environ.Env(
#     DEBUG=(bool, False),
#     EMAIL_PORT=(int, 25),
#     EMAIL_USE_TLS=(bool, False),
# )

env.read_env(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)


# Debug flag, True in dev, False in prod
# DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Allowed hosts from environment
ALLOWED_HOSTS = ast.literal_eval(env("ALLOWED_HOSTS", default="[]"))


# Application definition

INSTALLED_APPS = [
    "documents.apps.DocumentsConfig",
    "reports.apps.ReportsConfig",
    "clinical.apps.ClinicalConfig",
    "dashboard.apps.DashboardConfig",
    "locations.apps.LocationsConfig",
    "mentorship.apps.MentorshipConfig",
    "users.apps.UsersConfig",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'src.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'src.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Location to collect static files for production
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Additional directories to look for static files
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Optional shared static folder
]


# Media files (uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'uploads'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGIN_URL = '/users/login/'  # URL to redirect if not logged in
LOGIN_REDIRECT_URL = '/dashboard/'  # where to go after login success
LOGOUT_REDIRECT_URL = '/users/login/'  # after logout


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'logbook.models': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    },
}


# Optional: Customize message tags for Bootstrap
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# DEFAULT_FROM_EMAIL = 'admin@example.com'


# if DEBUG:
#     # Development email backend: writes emails to files for inspection
#     EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
#     EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
# else:
#     # Production email backend: for example, SMTP or Mailgun
#     EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#     EMAIL_HOST = 'smtp.mailgun.org'  # or your SMTP host
#     EMAIL_PORT = 587
#     EMAIL_USE_TLS = True
#     EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  # Your SMTP user from env vars
#     EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')  # Your SMTP password
#     DEFAULT_FROM_EMAIL = 'YourSite <no-reply@yoursite.com>'

if DEBUG:
    # EMAIL_BACKEND = env('DEV_EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
    # EMAIL_FILE_PATH = env('EMAIL_FILE_PATH', default=str(BASE_DIR / 'sent_emails'))
    
    # Development email backend: writes emails to files for inspection
    EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
    EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'
else:
    EMAIL_BACKEND = env('EMAIL_BACKEND')
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env('EMAIL_PORT')
    EMAIL_USE_TLS = env('EMAIL_USE_TLS')
    EMAIL_HOST_USER = env('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')