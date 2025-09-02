from django.db import models

class Sex(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        db_table = "sex"
        ordering = ["name"]

    def __str__(self):
        return self.name
