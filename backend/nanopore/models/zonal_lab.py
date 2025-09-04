from django.db import models
from django.contrib.auth import get_user_model
from . import Screening

User = get_user_model()

class ZonalLaboratory(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="zonal_laboratory")
    test_name = models.CharField(max_length=100)
    result = models.CharField(max_length=100, blank=True, null=True)
    test_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_updated")

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid} (Zonal Lab)"
