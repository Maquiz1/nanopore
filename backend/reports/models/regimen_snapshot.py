# reports/models/regimen.py
from django.db import models
from .general_base import DataQualitySnapshot

class RegimenDQSnapshot(models.Model):
    snapshot = models.ForeignKey(
        DataQualitySnapshot,
        on_delete=models.CASCADE,
        related_name="regimen_details"
    )

    # Zone & Site info
    zone = models.ForeignKey(
        "locations.Zone",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    site = models.ForeignKey(
        "locations.Site",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Totals
    total_regimens = models.IntegerField(default=0)

    # Missing / data quality issues
    missing_date = models.IntegerField(default=0)
    missing_drug = models.IntegerField(default=0)
    missing_changes = models.IntegerField(default=0)
    missing_reason = models.IntegerField(default=0)
    missing_specify_when_other = models.IntegerField(default=0)

    total_issues = models.IntegerField(default=0)

    class Meta:
        unique_together = ("snapshot", "zone", "site")
        indexes = [
            models.Index(fields=["snapshot", "zone"]),
            models.Index(fields=["snapshot", "site"]),
        ]

    def __str__(self):
        return f"Regimen Snapshot {self.snapshot.snapshot_date} | Zone: {self.zone_name} | Site: {self.site_name}"
