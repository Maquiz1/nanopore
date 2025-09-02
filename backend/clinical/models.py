from django.db import models

class YesNo(models.Model):
    name = models.CharField(max_length=10, unique=True)  # e.g., "Yes" or "No"

    class Meta:
        verbose_name = "Yes/No Option"
        verbose_name_plural = "Yes/No Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class YesNoNA(models.Model):
    name = models.CharField(max_length=10, unique=True)  # e.g., "Yes", "No", "NA"

    class Meta:
        verbose_name = "Yes/No/NA Option"
        verbose_name_plural = "Yes/No/NA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        # verbose_name = "Yes/No/NA Option"
        # verbose_name_plural = "Yes/No/NA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name

class Competence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='competences')

    class Meta:
        # verbose_name = "Yes/No/NA Option"
        # verbose_name_plural = "Yes/No/NA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
