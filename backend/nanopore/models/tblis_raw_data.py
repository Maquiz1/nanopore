from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class TblisUploadBatch(models.Model):
    """One uploaded TBLIS CSV file and its associated raw rows."""

    source_file_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"TBLIS upload: {self.source_file_name} ({self.created_at:%Y-%m-%d %H:%M})"


class TblisRawData(models.Model):
    """
    Staging model to store raw TBLIS CSV data before merging it into the EdcsTblisZonal model.
    Using a JSONField allows for flexible parsing of large CSV files regardless of column changes.
    """
    labno = models.CharField(max_length=255, db_index=True, help_text="Extracted from the raw TBLIS row")
    raw_data = models.JSONField(default=dict, help_text="The entire raw row from the CSV")
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    upload_batch = models.ForeignKey(
        TblisUploadBatch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rows",
    )
    is_merged = models.BooleanField(default=False, help_text="True if this row was successfully merged into EdcsTblisZonal")

    class Meta:
        ordering = ["labno"]

    def __str__(self):
        return f"Raw TBLIS: {self.labno}"
