"""Email settings kept in the database (editable by admins) and a log of every email sent."""
from django.db import models


class EmailRecipient(models.Model):
    """Extra people copied on the weekly report emails (not on account emails, which carry private links)."""
    CC, BCC = "cc", "bcc"
    TYPE_CHOICES = [(CC, "CC"), (BCC, "BCC")]

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    type = models.CharField(max_length=3, choices=TYPE_CHOICES, default=CC)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["type", "email"]

    def __str__(self):
        return f"{self.get_type_display()}: {self.email}"


class SiteConfiguration(models.Model):
    """The address of the system used in email links, and the sender shown in emails.
    The first active one is used; without one, links use SITE_URL from .env."""
    name = models.CharField(max_length=100, unique=True)
    site_url = models.URLField(help_text="e.g. https://dream.nimr.or.tz")
    from_name = models.CharField(max_length=100, blank=True, help_text="Sender name, e.g. DREAM Nanopore.")
    from_email = models.EmailField(blank=True, help_text="Sender address. Blank uses DEFAULT_FROM_EMAIL from .env.")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-is_active", "name"]

    def __str__(self):
        return f"{self.name} ({self.site_url})"


TASK_LABELS = {
    "account_activation": "Account activation",
    "password_reset": "Password reset",
    "weekly_queries": "Weekly open queries",
    "weekly_treatment_outcomes": "Weekly treatment without outcome",
}


class EmailLog(models.Model):
    SENT, FAILED = "sent", "failed"
    STATUS_CHOICES = [(SENT, "Sent"), (FAILED, "Failed")]

    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    task_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} -> {self.recipient} ({self.status})"

    @property
    def task_label(self):
        return TASK_LABELS.get(self.task_type, self.task_type)
