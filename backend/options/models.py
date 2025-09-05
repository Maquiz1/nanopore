from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()    

class YesNo(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_options_updated")

    class Meta:
        verbose_name = "Yes/No Option"
        verbose_name_plural = "Yes/No Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class YesNoNA(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Yes/No/NA Option"
        verbose_name_plural = "Yes/No/NA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    

class YesNoUnknown(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Yes/No/Unknown Option"
        verbose_name_plural = "Yes/No/Unknown Options"
        ordering = ["id"]

    def __str__(self):
        return self.name

class CategoryTreated(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Category Treated Option"
        verbose_name_plural = "Category Treated Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class Unknown(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Unknown Option"
        verbose_name_plural = "Unknown Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
class MonthUnknown(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Month Unknown Option"
        verbose_name_plural = "Month Unknown Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
class YearUnknown(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Year Unknown Option"
        verbose_name_plural = "Year Unknown Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class MonthYearUnknown(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Month Year Unknown Option"
        verbose_name_plural = "Month Year Unknown Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class DrDsTB(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "DrDsTB Option"
        verbose_name_plural = "DrDsTB Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class TreatmentRegimen(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Treatment Regimen Option"
        verbose_name_plural = "Treatment Regimen Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class TreatmentOutcome(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Treatment Outcome Option"
        verbose_name_plural = "Treatment Outcome Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class PositiveNegative(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Positive/Negative Option"
        verbose_name_plural = "Positive/Negative Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class PositiveNegativeUnknown(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Positive/Negative Unknown Option"
        verbose_name_plural = "Positive/Negative Unknown Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
class PositiveNegativeNA(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Positive/Negative NA Option"
        verbose_name_plural = "Positive/Negative NA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class DiseasesMedicalConditions(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Diseases/Medical Conditions Option"
        verbose_name_plural = "Diseases/Medical Conditions Options"
        ordering = ["id"]

    def __str__(self):
        return self.name

