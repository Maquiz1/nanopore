# locations/models.py

from django.db import models

class Country(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

class Zone(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        # db_table = "zone"
        ordering = ["name"]

    def __str__(self):
        return self.name

class Region(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}, {self.country.name}"

class District(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}, {self.region.name}"


class SiteType(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    name = models.CharField(max_length=50, unique=True)  # Clinic, Laboratory
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class SiteLevel(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    name = models.CharField(max_length=50, unique=True)  # e.g., "Local", "Zonal", "National"
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class Site(models.Model):
    value = models.IntegerField(blank=True, null=True)  # e.g., 1 for Yes, 0 for No
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    pid_prefix = models.CharField(max_length=13, default="")  # e.g., TZ01-
    site_type = models.ForeignKey(SiteType, on_delete=models.CASCADE, null=True, blank=True)
    site_level = models.ForeignKey(SiteLevel, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.district.name}"
