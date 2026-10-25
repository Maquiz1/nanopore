# reports/models/query_snapshot_model.py
from django.db import models


class QuerySnapshotRun(models.Model):
    """One run of `snapshot_queries` (once a day). A day without a run has no data."""
    snapshot_date = models.DateField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    seconds = models.FloatField(default=0)

    class Meta:
        ordering = ["-snapshot_date"]

    def __str__(self):
        return f"Query snapshot {self.snapshot_date}"


class QueryCount(models.Model):
    """
    How many records a query flagged on a day, per site. Only checks with
    at least one record are stored; missing rows mean 0.

    Rows with site = None are the all-sites totals, counted in one pass like the
    live pages (so duplicates across sites are counted the same way).
    """
    run = models.ForeignKey(QuerySnapshotRun, on_delete=models.CASCADE, related_name="counts")
    zone = models.ForeignKey("locations.Zone", on_delete=models.SET_NULL, null=True, blank=True)
    site = models.ForeignKey("locations.Site", on_delete=models.CASCADE, null=True, blank=True)
    form = models.CharField(max_length=30)   # screening, enrollment, ..., missing_forms, substudy
    query = models.CharField(max_length=80)  # the live page's query key, e.g. missing_lj_results
    count = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["run", "form"]),
            models.Index(fields=["run", "site"]),
        ]

    def __str__(self):
        return f"{self.run.snapshot_date} {self.site or 'All sites'} {self.form}.{self.query}={self.count}"
