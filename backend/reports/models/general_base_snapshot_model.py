# reports/models/general_base.py
from django.db import models

class DataQualitySnapshot(models.Model):
    snapshot_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("snapshot_date",)
        ordering = ["-snapshot_date"]

    def __str__(self):
        return f"Snapshot {self.snapshot_date}"
