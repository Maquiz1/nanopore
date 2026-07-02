from django.db import models

class TblisNotInEdcs(models.Model):
    """
    Stores TBLIS raw rows that could not find a matching EDCS record.
    """
    labno = models.CharField(max_length=255, db_index=True)
    raw_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TBLIS Unmatched: {self.labno}"

class EdcsNotInTblis(models.Model):
    """
    Stores EDCS records (unique_lab_no and pid) that were missing from the TBLIS upload.
    """
    unique_lab_no = models.CharField(max_length=255, db_index=True)
    pid = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"EDCS Missing in TBLIS: {self.unique_lab_no}"

class EdcsTblisMismatch(models.Model):
    """
    Tracks fields where the existing EDCS data conflicted with the uploaded TBLIS data.
    """
    labno = models.CharField(max_length=255, db_index=True)
    pid = models.CharField(max_length=255, blank=True, null=True)
    field_name = models.CharField(max_length=255)
    edcs_value = models.TextField(blank=True, null=True)
    tblis_value = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Mismatch: {self.labno} [{self.field_name}]"
