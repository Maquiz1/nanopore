from django.db import models
from django.contrib.auth import get_user_model
from locations.models import Site  # assuming you have a Site model

User = get_user_model()

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Disease Option"
        verbose_name_plural = "Disease Options"
        ordering = ["id"]

    def __str__(self):
        return self.name

class Competence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='competences')

    class Meta:
        verbose_name = "Competence"
        verbose_name_plural = "Competences"
        ordering = ["id"]

    def __str__(self):
        return self.name
