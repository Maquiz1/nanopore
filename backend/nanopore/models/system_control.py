from django.conf import settings
from django.db import models

class SystemControl(models.Model):
    enable_form_submissions = models.BooleanField(
        default=True, 
        help_text="If unchecked, the 'Submit' button on all forms will be disabled."
    )
    enable_new_screening = models.BooleanField(
        default=True,
        help_text="If unchecked, the 'New Screening' button will be hidden from the dashboard."
    )
    zonal_lab_by_section = models.BooleanField(
        default=True,
        help_text="If checked, Zonal Lab records open section by section; if unchecked, as the single full form.",
    )

    # Per-form switches: off = no new records of that form (saved ones stay editable)
    allow_new_enrollment = models.BooleanField(default=True)
    allow_new_clinic_lab = models.BooleanField(default=True)
    allow_new_zonal_lab = models.BooleanField(default=True)
    allow_new_diagnosis = models.BooleanField(default=True)
    allow_new_regimen = models.BooleanField(default=True)
    allow_new_nanopore_run = models.BooleanField(default=True)

    # Study status (nanopore/study_lock.py): locked = read and export only
    study_locked = models.BooleanField(default=False)
    study_locked_at = models.DateTimeField(null=True, blank=True)
    study_locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    study_lock_reason = models.TextField(blank=True)
    # Form-level locks: {form key: {"at": ISO time, "by": user id, "reason": text}} (nanopore/study_lock.py)
    locked_forms = models.JSONField(default=dict, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Control"
        verbose_name_plural = "System Controls"

    def __str__(self):
        return f"System Controls (Updated {self.updated_at.strftime('%Y-%m-%d %H:%M')})"
