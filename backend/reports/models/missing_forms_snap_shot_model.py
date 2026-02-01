from django.db import models
from reports.models import DataQualitySnapshot
from nanopore.models import Screening

class MissingFormsDQSnapshot(models.Model):
    snapshot = models.ForeignKey(DataQualitySnapshot, on_delete=models.CASCADE)
    zone = models.ForeignKey("locations.Zone", null=True, blank=True, on_delete=models.SET_NULL)
    site = models.ForeignKey("locations.Site", null=True, blank=True, on_delete=models.SET_NULL)
    screening = models.ForeignKey(Screening, null=True, blank=True, on_delete=models.SET_NULL)
    
    missing_enrollment = models.IntegerField(default=0)
    missing_clinic = models.IntegerField(default=0)
    missing_diagnosis = models.IntegerField(default=0)
    missing_regimen = models.IntegerField(default=0)
    missing_zonal = models.IntegerField(default=0)

    total_issues = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Missing Forms Data Quality Snapshot"
        verbose_name_plural = "Missing Forms Data Quality Snapshots"
        unique_together = ("snapshot", "zone", "site")
        indexes = [
            models.Index(fields=["snapshot", "zone"]),
            models.Index(fields=["snapshot", "site"]),
        ]
