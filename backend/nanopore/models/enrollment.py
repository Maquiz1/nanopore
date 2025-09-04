from django.db import models
from django.contrib.auth import get_user_model
from . import Screening

User = get_user_model()

class Enrollment(models.Model):
    screening = models.OneToOneField(Screening, on_delete=models.CASCADE, related_name="enrollment")
    enrollment_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments_updated")

    class Meta:
        ordering = ["screening"]

    def __str__(self):
        return f"Enrollment for {self.screening.pid}"
