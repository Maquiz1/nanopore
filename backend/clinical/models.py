from django.db import models
from django.contrib.auth import get_user_model
from locations.models import Site  # assuming you have a Site model

User = get_user_model()

# SITE_TYPE_CHOICES = [
#         ("clinic", "Clinic Site"),
#         ("clinic_lab", "Clinic + Lab Site"),
#         ("lab_only", "Lab Only Site"),
#     ]
    
# class SiteType(models.Model):
#     name = models.CharField(max_length=50, unique=True)  # e.g., Clinic, Zonal, National
#     code = models.CharField(max_length=20, unique=True)  # e.g., clinic, zonal, national

#     def __str__(self):
#         return self.name
    
# class LaboratoryLevel(models.Model):
#     name = models.CharField(max_length=50, unique=True)  # Clinic, Zonal, National
#     code = models.CharField(max_length=20, unique=True)  # clinic, zonal, national

#     def __str__(self):
#         return self.name


# class Laboratory(models.Model):
#     name = models.CharField(max_length=255, unique=True)
#     code = models.CharField(max_length=50, unique=True, blank=True, null=True)
#     location = models.TextField(blank=True, null=True)

#     contact_person = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="laboratories")
#     contact_email = models.EmailField(blank=True, null=True)

#     lab_level = models.ForeignKey(LaboratoryLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name="laboratories")

#     # Flexible links
#     site = models.ForeignKey("locations.Site", on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_labs")
#     zone = models.ForeignKey("locations.Zone", on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs")
#     country = models.ForeignKey("locations.Country", on_delete=models.SET_NULL, null=True, blank=True, related_name="national_labs")

#     def __str__(self):
#         return self.name

    
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
