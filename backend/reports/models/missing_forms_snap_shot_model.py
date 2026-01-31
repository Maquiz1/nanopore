from django.db import models
from reports.models import DataQualitySnapshot
from nanopore.models import Screening

class MissingFormsDQSnapshot(models.Model):
    snapshot = models.ForeignKey(DataQualitySnapshot, on_delete=models.CASCADE)
    zone = models.ForeignKey("locations.Zone", null=True, blank=True, on_delete=models.SET_NULL)
    site = models.ForeignKey("locations.Site", null=True, blank=True, on_delete=models.SET_NULL)
    screening = models.ForeignKey(Screening, null=True, blank=True, on_delete=models.SET_NULL)
    
    missing_enrollment = models.BooleanField(default=False)
    missing_clinic = models.BooleanField(default=False)
    missing_diagnosis = models.BooleanField(default=False)
    missing_regimen = models.BooleanField(default=False)
    missing_zonal = models.BooleanField(default=False)

    total_issues = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Missing Forms Data Quality Snapshot"
        verbose_name_plural = "Missing Forms Data Quality Snapshots"
