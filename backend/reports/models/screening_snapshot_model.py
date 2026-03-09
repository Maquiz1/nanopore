# reports/models/screening.py
from django.db import models
from .general_base_snapshot_model import DataQualitySnapshot

class ScreeningDQSnapshot(models.Model):
    snapshot = models.ForeignKey(
        DataQualitySnapshot,
        on_delete=models.CASCADE,
        related_name="screening_details"
    )

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

    total_screenings = models.IntegerField(default=0)

    missing_screening_date = models.IntegerField(default=0)
    missing_pid1 = models.IntegerField(default=0)
    missing_pid2 = models.IntegerField(default=0)
    missing_sex = models.IntegerField(default=0)
    missing_age_dob = models.IntegerField(default=0)
    missing_consent = models.IntegerField(default=0)
    missing_consent_date_when_yes = models.IntegerField(default=0)
    missing_age18years = models.IntegerField(default=0)
    missing_present_symptoms = models.IntegerField(default=0)
    missing_genexpert_confirmation = models.IntegerField(default=0)
    missing_produce_resp_sample = models.IntegerField(default=0)
    missing_unable_understand = models.IntegerField(default=0)
    missing_not_willing = models.IntegerField(default=0)
    missing_enrolled = models.IntegerField(default=0)
    missing_reasons = models.IntegerField(default=0)
    missing_reasons_other = models.IntegerField(default=0)

    duplicate_pids = models.IntegerField(default=0)
    mismatched_pids = models.IntegerField(default=0)
    invalid_length_pids = models.IntegerField(default=0)

    total_issues = models.IntegerField(default=0)

    class Meta:
        unique_together = ("snapshot", "zone", "site")
        indexes = [
            models.Index(fields=["snapshot", "zone"]),
            models.Index(fields=["snapshot", "site"]),
        ]
