from django.db import migrations


def normalize(apps, schema_editor):
    """TB-LIS rows uploaded before dates were read kept them as written (3/24/2025): store them as yyyy-mm-dd."""
    from nanopore.tblis_file import normalize_stored_dates
    normalize_stored_dates(apps.get_model("nanopore", "TblisRawData"))


class Migration(migrations.Migration):

    dependencies = [
        ("nanopore", "0053_change_history"),
    ]

    operations = [
        migrations.RunPython(normalize, migrations.RunPython.noop, elidable=True),
    ]
