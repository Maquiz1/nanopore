from django.db import models
from django.contrib.auth import get_user_model
from nanopore.models import Screening
from options.models import (
    RegimenTypeOfChange,
    RegimenReasonForChange,
    )


User = get_user_model()

class RegimenChanges(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="regimen_changes")  
    
    pid = models.CharField(max_length=16, editable=False)

    date = models.DateField(max_length=20, blank=True, null=True)
    drug = models.CharField(max_length=255, blank=True, null=True)
    changes = models.ForeignKey(RegimenTypeOfChange, on_delete=models.SET_NULL, blank=True, null=True, related_name="changes")
    reason = models.ForeignKey(RegimenReasonForChange, on_delete=models.SET_NULL, blank=True, null=True, related_name="reason")
    specify = models.TextField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="regimen_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="regimen_updated")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Regimen Change for {self.screening.pid}: {self.date}"
