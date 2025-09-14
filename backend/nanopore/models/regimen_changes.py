from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models import Screening
from options.models import RegimenTypeOfChange, RegimenReasonForChange

User = get_user_model()


class RegimenChanges(models.Model):
    screening = models.ForeignKey(
        Screening,
        on_delete=models.CASCADE,
        related_name="regimen_changes"
    )
    pid = models.CharField(max_length=16, editable=False)  # auto-set from screening

    date = models.DateField(blank=True, null=True)
    drug = models.CharField(max_length=255, blank=True, null=True)
    changes = models.ForeignKey(
        RegimenTypeOfChange,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="regimen_changes"
    )
    reason = models.ForeignKey(
        RegimenReasonForChange,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="regimen_reasons"
    )
    specify = models.TextField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regimen_created"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="regimen_updated"
    )

    class Meta:
        ordering = ["-date"]
        verbose_name = "Regimen Change"
        verbose_name_plural = "Regimen Changes"

    def save(self, *args, **kwargs):
        # Auto-fill pid from linked screening
        if not self.pid and self.screening:
            self.pid = self.screening.pid
        super().save(*args, **kwargs)

    def __str__(self):
        drug_display = self.drug if self.drug else "N/A"
        date_display = self.date.strftime("%Y-%m-%d") if self.date else "N/A"
        return f"Regimen Change for {self.pid}: {drug_display} on {date_display}"
