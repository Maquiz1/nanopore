from pathlib import Path
import environ
import os
import ast
from django.contrib.messages import constants as messages

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environ
env = environ.Env()
env.read_env(BASE_DIR / ".env")

# Security
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = ast.literal_eval(env("ALLOWED_HOSTS", default="[]"))
# ALLOWED_HOSTS=['*']

# Database settings based on DEBUG
# if DEBUG:
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'db.sqlite3',
#         }
#     }
# else:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        # 'ENGINE': 'django.db.backends.mysql',
        "NAME": env("DB_NAME"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "HOST": env("DB_HOST"),
        "PORT": env("DB_PORT"),
    }
}

# Installed apps
INSTALLED_APPS = [
    "rest_framework",
    "common.apps.CommonConfig",
    "options.apps.OptionsConfig",
    "demographic.apps.DemographicConfig",
    # 'status.apps.StatusConfig',
    # 'reasons.apps.ReasonsConfig',
    "nanopore.apps.NanoporeConfig",
    "household.apps.HouseholdConfig",
    "documents.apps.DocumentsConfig",
    "reports.apps.ReportsConfig",
    "clinical.apps.ClinicalConfig",
    "dashboard.apps.DashboardConfig",
    "locations.apps.LocationsConfig",
    # "mentorship.apps.MentorshipConfig",
    "users.apps.UsersConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_celery_beat",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # 'users.middleware.AutoLogoutMiddleware',  # ✅ Auto logout
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URLs and templates
ROOT_URLCONF = "src.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "reports.context_processors.forms_context.forms_report_total",
                "reports.context_processors.screening_context.screening_report_total",
                "reports.context_processors.enrollment_context.enrollment_report_total",
                "reports.context_processors.clinic_laboratory_context.clinic_report_total",
                "reports.context_processors.diagnosis_context.diagnosis_report_total",
                "reports.context_processors.zonal_laboratory_context.zonal_report_total",
                "reports.context_processors.regimen_context.regimen_report_total",
                "reports.context_processors.specific_queries_total.specific_queries_total",   # ← add this line
                'reports.context_processors.total_context.global_total_issues',
            ],
        },
    },
]

WSGI_APPLICATION = "src.wsgi.application"

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static and media files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "uploads"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# # Auth redirect settings
# LOGIN_URL = '/users/login/'
# LOGIN_REDIRECT_URL = '/dashboard/'
# LOGOUT_REDIRECT_URL = '/users/login/'

# ✅ Session Settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Log out user when browser closes
SESSION_COOKIE_AGE = 1800  # Session timeout (in seconds) → 30 minutes
SESSION_SAVE_EVERY_REQUEST = True  # Extend session on each user activity
SESSION_ENGINE = "django.contrib.sessions.backends.db"  # Store sessions in DB (default)

# ✅ Authentication Redirects
LOGIN_URL = "users:login"  # Redirect here if not logged in
LOGIN_REDIRECT_URL = "dashboard:dashboard"  # Go here after successful login
LOGOUT_REDIRECT_URL = "users:login"  # Redirect here after logout
SESSION_ENGINE = "django.contrib.sessions.backends.db"


# Email settings
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "sent_emails"
else:
    EMAIL_BACKEND = env("EMAIL_BACKEND")
    EMAIL_HOST = env("EMAIL_HOST")
    EMAIL_PORT = env.int("EMAIL_PORT")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS")
    EMAIL_HOST_USER = env("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "logbook.models": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}

# Message tags for Bootstrap compatibility
MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# External API keys
AT_USERNAME = env("AT_USERNAME")
AT_API_KEY = env("AT_API_KEY")


# Allow up to 10,000 form fields
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000


# # Or set a fixed duration (seconds)
# SESSION_COOKIE_AGE = 10  # 10 seconds
# SESSION_SAVE_EVERY_REQUEST = True  # Extend session on activity

# # ✅ Sessions expire when the browser closes
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# # ✅ Or expire after 1 hour (3600 seconds)
# SESSION_COOKIE_AGE = 10

# # ✅ Refresh expiry time with every request (active users stay logged in)
# SESSION_SAVE_EVERY_REQUEST = True

# # ✅ Recommended security flags
# SESSION_COOKIE_SECURE = False  # Set True in production (HTTPS only)
# SESSION_COOKIE_HTTPONLY = True
# SESSION_ENGINE = "django.contrib.sessions.backends.db"


# # ✅ Sessions
# SESSION_EXPIRE_AT_BROWSER_CLOSE = True     # logout when browser closes
# SESSION_COOKIE_AGE = 10                    # session timeout (10 seconds)
# SESSION_SAVE_EVERY_REQUEST = True          # extend session on activity
# SESSION_ENGINE = "django.contrib.sessions.backends.db"

# # ✅ Authentication redirects
# LOGIN_URL = 'users:login'
# LOGIN_REDIRECT_URL = 'dashboard:dashboard'   # where to go after login
# LOGOUT_REDIRECT_URL = 'users:login'          # where to go after logout



# Redis broker
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Timezone
CELERY_TIMEZONE = "Africa/Dar_es_Salaam"
CELERY_ENABLE_UTC = True


CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

from celery.schedules import crontab

# Celery Beat
CELERY_BEAT_SCHEDULE = {
    "daily_screening_snapshot": {
        "task": "reports.tasks.create_screening_dq_snapshot",
        "schedule": crontab(hour=0, minute=0),
    },
    "daily_enrollment_snapshot": {
        "task": "reports.tasks.create_enrollment_dq_snapshot",
        "schedule": crontab(hour=0, minute=30),
    },
    "daily_clinic_snapshot": {
        "task": "reports.tasks.create_clinic_lab_dq_snapshot",
        "schedule": crontab(hour=1, minute=0),
    },
    "daily_diagnosis_snapshot": {
        "task": "reports.tasks.create_diagnosis_dq_snapshot",
        "schedule": crontab(hour=1, minute=30),
    },
    "daily_regimen_snapshot": {
        "task": "reports.tasks.create_regimen_dq_snapshot",
        "schedule": crontab(hour=2, minute=0),
    },
    "daily_zonal_snapshot": {
        "task": "reports.tasks.create_zonal_lab_dq_snapshot",
        "schedule": crontab(hour=2, minute=30),
    },
    "daily_forms_snapshot": {
        "task": "reports.tasks.create_missing_forms_dq_snapshot",
        "schedule": crontab(hour=19, minute=46),
    },
}

