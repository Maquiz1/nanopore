from django.db import models
from django.contrib.auth import get_user_model
from . import Screening

User = get_user_model()

class Diagnosis(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="diagnosis")
    diagnosis_name = models.CharField(max_length=200)
    diagnosis_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses_updated")

    class Meta:
        ordering = ["-diagnosis_date"]

    def __str__(self):
        return f"Diagnosis for {self.screening.pid}: {self.diagnosis_name}"
