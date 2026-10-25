"""Make sure every role in utils/access.py exists as a group, so admins can assign it
(COORDINATOR is new; DATA_MANAGER and STATISTICIAN were only created by seed_roles)."""
from django.db import migrations

ROLES = ["NURSE", "CLINICIAN", "LABORATORY_TECHNICIAN", "DATA_SPECIALIST", "DATA_MANAGER",
         "STATISTICIAN", "REVIEWER", "COORDINATOR", "ADMIN"]


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    for name in ROLES:
        Group.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0007_remove_old_snapshot_tasks"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(create_groups, migrations.RunPython.noop),
    ]
