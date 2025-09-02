from django.db import models

class EnrolledReason(models.Model):
    reason = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "enrolled_reason"
        ordering = ["reason"]

    def __str__(self):
        return self.reason
