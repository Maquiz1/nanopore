from django.db import models
from django.conf import settings

class EdcsTblisMergeSummary(models.Model):
    """
    Stores the summary statistics from each run of the
    merge_clinic_zonal_lab_tblis_data management command.
    The list page displays the latest record.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    # ── File-level counts ─────────────────────────────────────────────────────
    total_columns          = models.IntegerField(default=0)
    total_edcs_records     = models.IntegerField(default=0)
    total_tblis_rows       = models.IntegerField(default=0)
    matched_records        = models.IntegerField(default=0)
    missing_records        = models.IntegerField(default=0)
    edcs_not_in_tblis      = models.IntegerField(default=0)
    tblis_not_in_edcs      = models.IntegerField(default=0)

    # ── TBLIS date range (from filename) ──────────────────────────────────────
    tblis_date_from        = models.CharField(max_length=20, blank=True, null=True)
    tblis_date_to          = models.CharField(max_length=20, blank=True, null=True)

    # ── Mismatch stats ────────────────────────────────────────────────────────
    total_mismatch_columns = models.IntegerField(default=0)
    total_mismatch_records = models.IntegerField(default=0)
    # JSON: {"field_name": count, ...}
    mismatch_by_field      = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "EDCS–TBLIS Merge Summary"
        verbose_name_plural = "EDCS–TBLIS Merge Summaries"

    def __str__(self):
        return f"Merge summary {self.created_at:%Y-%m-%d %H:%M}"
