from django.db import models

class Disease(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Competence(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='competences')

    def __str__(self):
        return self.name
