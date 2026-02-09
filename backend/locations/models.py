from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator


# ==================================================
# Shared abstract base for targets
# ==================================================

class TargetBase(models.Model):
    target = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    substudy2Target = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    substudy4Target = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        abstract = True

    def clean(self):
        errors = {}

        if self.target is None:
            errors["target"] = "Overall enrollment target is required."

        if self.substudy2Target is None:
            errors["substudy2Target"] = "Substudy 2 target is required."

        if self.substudy4Target is None:
            errors["substudy4Target"] = "Substudy 4 target is required."

        if errors:
            raise ValidationError(errors)


# ==================================================
# Country
# ==================================================

class Country(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"


# ==================================================
# Zone
# ==================================================

class Zone(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


# ==================================================
# Region
# ==================================================

class Region(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    country = models.ForeignKey(Country, on_delete=models.CASCADE)
    zone = models.ForeignKey(Zone, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name}, {self.country.name}"


# ==================================================
# District
# ==================================================

class District(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name}, {self.region.name}"


# ==================================================
# Site Type
# ==================================================

class SiteType(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


# ==================================================
# Site Level
# ==================================================

class SiteLevel(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    name = models.CharField(max_length=50, unique=True)
    code = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name


# ==================================================
# Site
# ==================================================

class Site(TargetBase):
    value = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    pid_prefix = models.CharField(max_length=13, default="")
    site_type = models.ForeignKey(SiteType, on_delete=models.CASCADE, null=True, blank=True)
    site_level = models.ForeignKey(SiteLevel, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.district.name}"
