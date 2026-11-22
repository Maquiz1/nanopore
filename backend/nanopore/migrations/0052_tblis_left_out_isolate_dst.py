from django.db import migrations, models
import django.db.models.deletion


def remember_left_out(apps, schema_editor):
    """Rejections weren't stored; the latest upload's follow-up list still has some of them."""
    TblisFollowUp = apps.get_model("nanopore", "TblisFollowUp")
    TblisLeftOut = apps.get_model("nanopore", "TblisLeftOut")
    TblisRawData = apps.get_model("nanopore", "TblisRawData")
    records, done = [], set()
    for row in TblisFollowUp.objects.filter(upload_batch__isnull=False).select_related("upload_batch"):
        key = (row.labno, row.upload_batch_id)
        if key in done or TblisRawData.objects.filter(labno=row.labno, upload_batch_id=row.upload_batch_id).exists():
            continue
        done.add(key)
        records.append(TblisLeftOut(labno=row.labno, reason=row.reason, upload_batch_id=row.upload_batch_id,
                                    seen_at=row.upload_batch.created_at))
    TblisLeftOut.objects.bulk_create(records, batch_size=1000)


class Migration(migrations.Migration):

    dependencies = [
        ('nanopore', '0051_tblis_follow_up'),
    ]

    operations = [
        migrations.CreateModel(
            name='TblisLeftOut',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('labno', models.CharField(db_index=True, max_length=255)),
                ('reason', models.CharField(max_length=30)),
                ('seen_at', models.DateTimeField()),
                ('upload_batch', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='nanopore.tblisuploadbatch')),
            ],
            options={
                'ordering': ['-seen_at', 'labno'],
            },
        ),
        migrations.CreateModel(
            name='TblisIsolateDst',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=100)),
                ('values', models.JSONField(default=dict)),
                ('before_known', models.BooleanField(default=True, help_text="False: merged before this was recorded, so the site's own values aren't known")),
                ('zonal_lab', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='nanopore.zonallaboratory')),
            ],
        ),
        migrations.RunPython(remember_left_out, migrations.RunPython.noop, elidable=True),
    ]
