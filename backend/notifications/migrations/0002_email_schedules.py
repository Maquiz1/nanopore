"""Create the Sunday email jobs in Periodic Tasks (see notifications/schedules.py)."""
from django.db import migrations


def create_schedules(apps, schema_editor):
    from notifications.schedules import ensure_schedules
    ensure_schedules(apps.get_model("django_celery_beat", "PeriodicTask"),
                     apps.get_model("django_celery_beat", "CrontabSchedule"))


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [migrations.RunPython(create_schedules, migrations.RunPython.noop)]
