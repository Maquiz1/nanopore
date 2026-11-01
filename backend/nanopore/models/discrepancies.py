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


class TblisFollowUp(models.Model):
    """
    A row of the latest TB-LIS upload left out because its specimen or GeneXpert
    wasn't recorded (tblis_file.FOLLOW_UP_REASONS). Replaced at every upload.
    """
    labno = models.CharField(max_length=255, db_index=True)
    reason = models.CharField(max_length=30)
    specimen = models.CharField(max_length=50, blank=True)
    genexpert = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True)
    facility = models.CharField(max_length=200, blank=True)
    received = models.CharField(max_length=10, blank=True)
    has_dst = models.BooleanField(default=False)
    upload_batch = models.ForeignKey("nanopore.TblisUploadBatch", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["region", "facility", "labno"]

    def __str__(self):
        return f"TB-LIS follow-up: {self.labno}"
