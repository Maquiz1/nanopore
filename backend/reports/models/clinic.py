# reports/models/clinic.py
from django.db import models
from . general_base import DataQualitySnapshot

class ClinicDQSnapshot(models.Model):
    snapshot = models.ForeignKey(
        DataQualitySnapshot,
        on_delete=models.CASCADE,
        related_name="clinic_details"
    )

    zone = models.ForeignKey("locations.Zone", on_delete=models.CASCADE)
    site = models.ForeignKey("locations.Site", on_delete=models.CASCADE)

    total_clinics = models.IntegerField(default=0)

    missing_sample_received = models.IntegerField(default=0)
    missing_number_received = models.IntegerField(default=0)
    missing_sample_reason_when_received_2 = models.IntegerField(default=0)
    missing_new_reason_when_new_sample_2 = models.IntegerField(default=0)
    missing_other_reason_when_sample_reason_96 = models.IntegerField(default=0)

    missing_date_sample1_collected = models.IntegerField(default=0)
    missing_date_sample1_received = models.IntegerField(default=0)
    missing_appearance_sample1 = models.IntegerField(default=0)
    missing_sample1_volume = models.IntegerField(default=0)

    missing_date_sample2_collected = models.IntegerField(default=0)
    missing_date_sample2_received = models.IntegerField(default=0)
    missing_appearance_sample2 = models.IntegerField(default=0)
    missing_sample2_volume = models.IntegerField(default=0)

    missing_afb_microscopy_conducted = models.IntegerField(default=0)
    missing_afb_a_date = models.IntegerField(default=0)
    missing_technique_a = models.IntegerField(default=0)
    missing_afb_a_results = models.IntegerField(default=0)
    missing_afb_b_date = models.IntegerField(default=0)
    missing_technique_b = models.IntegerField(default=0)
    missing_afb_b_results = models.IntegerField(default=0)

    missing_xpert_mtb_rif_conducted = models.IntegerField(default=0)
    missing_xpert_date = models.IntegerField(default=0)
    missing_xpert_mtb = models.IntegerField(default=0)
    missing_error_code = models.IntegerField(default=0)
    missing_xpert_rif = models.IntegerField(default=0)
    missing_ct_value = models.IntegerField(default=0)

    total_issues = models.IntegerField(default=0)

    class Meta:
        unique_together = ("snapshot", "zone", "site")
        indexes = [
            models.Index(fields=["snapshot", "zone"]),
            models.Index(fields=["snapshot", "site"]),
        ]
