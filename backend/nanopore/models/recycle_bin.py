from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class DeletedRecord(models.Model):
    """
    One recycle-bin entry: a deleted record together with every record that was
    deleted with it (e.g. a Screening and all its forms), so it can be restored.
    See nanopore/recycle_bin.py.
    """
    model_name = models.CharField(max_length=100)       # model the admin deleted, e.g. "Screening"
    object_id = models.CharField(max_length=64)         # its primary key
    pid = models.CharField(max_length=32, blank=True)   # participant ID, for searching
    summary = models.JSONField(default=dict)            # {"Enrollment": 1, "RegimenChanges": 3, ...}
    payload = models.JSONField(default=list)            # serialized records, restore order (parents first)
    reason = models.TextField(blank=True)

    deleted_at = models.DateTimeField(auto_now_add=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_records")
    restored_at = models.DateTimeField(null=True, blank=True)
    restored_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="restored_records")

    class Meta:
        ordering = ["-deleted_at"]
        indexes = [models.Index(fields=["pid"]), models.Index(fields=["model_name"])]

    @property
    def is_restored(self):
        return self.restored_at is not None

    @property
    def total_records(self):
        return sum(self.summary.values())

    def __str__(self):
        return f"{self.model_name} {self.pid or self.object_id} deleted {self.deleted_at:%Y-%m-%d %H:%M}"
