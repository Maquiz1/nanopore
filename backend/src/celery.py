import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")

app = Celery("src")

# Load settings from Django settings, prefixed with CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from installed apps
app.autodiscover_tasks()