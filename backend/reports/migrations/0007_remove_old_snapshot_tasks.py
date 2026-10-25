"""The seven per-form snapshot jobs are replaced by one `snapshot_queries` job.

Celery Beat's database scheduler keeps jobs that disappear from settings, so the
old ones are removed here (they would keep writing the old, wrong counts).
"""
from django.db import migrations

OLD_TASKS = [
    "reports.tasks.create_screening_dq_snapshot",
    "reports.tasks.create_enrollment_dq_snapshot",
    "reports.tasks.create_clinic_lab_dq_snapshot",
    "reports.tasks.create_diagnosis_dq_snapshot",
    "reports.tasks.create_regimen_dq_snapshot",
    "reports.tasks.create_zonal_lab_dq_snapshot",
    "reports.tasks.create_missing_forms_dq_snapshot",
]


def remove_old_tasks(apps, schema_editor):
    PeriodicTask = apps.get_model("django_celery_beat", "PeriodicTask")
    PeriodicTask.objects.filter(task__in=OLD_TASKS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0006_query_snapshots"),
        ("django_celery_beat", "0019_alter_periodictasks_options"),
    ]

    operations = [
        migrations.RunPython(remove_old_tasks, migrations.RunPython.noop),
    ]
