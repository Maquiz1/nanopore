# locations/models.py

from django.db import models

class Country(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

class Zone(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)

    class Meta:
        # db_table = "zone"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Region(models.Model):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class District(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}, {self.region.name}"


class SiteType(models.Model):
    name = models.CharField(max_length=50, unique=True)  # Clinic, Laboratory
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class SiteLevel(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., "Local", "Zonal", "National"
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Site(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    pid_prefix = models.CharField(max_length=13, default="")  # e.g., TZ01-
    site_type = models.ForeignKey(SiteType, on_delete=models.CASCADE, null=True, blank=True)
    site_level = models.ForeignKey(SiteLevel, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.district.name}"
