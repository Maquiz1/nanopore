# reports/models/enrollment.py
from django.db import models
from .general_base import DataQualitySnapshot


class EnrollmentDQSnapshot(models.Model):
    snapshot = models.ForeignKey(
        DataQualitySnapshot,
        on_delete=models.CASCADE,
        related_name="enrollment_details"
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

    # =====================================================
    # COUNTS
    # =====================================================
    total_enrollments = models.IntegerField(default=0)

    missing_hiv_status = models.IntegerField(default=0)
    missing_other_diseases = models.IntegerField(default=0)
    missing_sputum_collected = models.IntegerField(default=0)
    missing_sputum_date = models.IntegerField(default=0)
    missing_sputum_reasons = models.IntegerField(default=0)
    missing_diseases_medical = models.IntegerField(default=0)
    missing_diseases_specify = models.IntegerField(default=0)

    missing_dr_ds = models.IntegerField(default=0)
    missing_tb_regimen = models.IntegerField(default=0)
    missing_tb_outcome = models.IntegerField(default=0)

    missing_tb_regimen_specify = models.IntegerField(default=0)
    missing_tb_regimen_specify_8 = models.IntegerField(default=0)
    missing_tb_category_specify = models.IntegerField(default=0)

    invalid_ltf_months = models.IntegerField(default=0)

    missing_tx_month_without_unknown = models.IntegerField(default=0)
    invalid_tx_month_with_unknown = models.IntegerField(default=0)
    missing_tx_year_without_unknown = models.IntegerField(default=0)
    invalid_tx_year_with_unknown = models.IntegerField(default=0)
    invalid_unknown_year_dependencies = models.IntegerField(default=0)

    missing_regimen_months_without_unknown = models.IntegerField(default=0)
    invalid_regimen_months_with_unknown = models.IntegerField(default=0)

    total_issues = models.IntegerField(default=0)

    class Meta:
        unique_together = ("snapshot", "zone", "site")
        ordering = ["zone", "site"]

    def __str__(self):
        return f"Enrollment DQ | {self.snapshot.snapshot_date} | {self.zone} | {self.site}"
