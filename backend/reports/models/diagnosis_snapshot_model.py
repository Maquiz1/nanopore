# reports/models/diagnosis.py
from django.db import models
from .general_base_snapshot_model import DataQualitySnapshot

class DiagnosisDQSnapshot(models.Model):
    snapshot = models.ForeignKey(
        DataQualitySnapshot,
        on_delete=models.CASCADE,
        related_name="diagnosis_details"
    )

    zone = models.ForeignKey("locations.Zone", on_delete=models.CASCADE)
    site = models.ForeignKey("locations.Site", on_delete=models.CASCADE)

    total_diagnoses = models.IntegerField(default=0)

    missing_tb_diagnosis = models.IntegerField(default=0)
    missing_tb_diagnosis_date = models.IntegerField(default=0)
    missing_tb_diagnosis_made = models.IntegerField(default=0)
    missing_tb_treatment = models.IntegerField(default=0)

    missing_diagnosis_made_other = models.IntegerField(default=0)
    missing_tb_diagnosed_clinically = models.IntegerField(default=0)
    missing_tb_clinically_other = models.IntegerField(default=0)

    missing_bacteriological_diagnosis = models.IntegerField(default=0)
    missing_clinician_received_date = models.IntegerField(default=0)

    missing_tb_other_diagnosis = models.IntegerField(default=0)
    missing_tb_diagnosis_made2 = models.IntegerField(default=0)
    missing_tb_other_specify = models.IntegerField(default=0)

    missing_tb_treatment_date = models.IntegerField(default=0)
    missing_tb_register_number = models.IntegerField(default=0)
    duplicate_tb_register_number = models.IntegerField(default=0)

    missing_tb_regimen = models.IntegerField(default=0)
    missing_regimen_changed = models.IntegerField(default=0)
    missing_tb_facility = models.IntegerField(default=0)
    missing_tb_reason = models.IntegerField(default=0)

    pending_tb_outcome = models.IntegerField(default=0)
    pending_tb_outcome_date = models.IntegerField(default=0)

    total_issues = models.IntegerField(default=0)

    class Meta:
        unique_together = ("snapshot", "zone", "site")
        indexes = [
            models.Index(fields=["snapshot", "zone"]),
            models.Index(fields=["snapshot", "site"]),
        ]
