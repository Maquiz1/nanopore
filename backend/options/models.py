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
    
    
class EnrolledReason(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Enrolled Reason Option"
        verbose_name_plural = "Enrolled Reason Options"
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
    value = models.IntegerField(unique=True)  # e.g., 1 = Positive, 2 = Negative , 99 = Unknown
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



#  CLINIC LABORATORY
class SampleReason(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Sample Reason Option"
        verbose_name_plural = "Sample Reason Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class SampleNumber(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Sample Number Option"
        verbose_name_plural = "Sample Number Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class SampleAppearance(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Sample Appearance Option"
        verbose_name_plural = "Sample Appearance Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class AFBTechnique(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "AFB Technique Option"
        verbose_name_plural = "AFB Technique Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    

class AFBMicroscopyResult(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "AFB Microscopy Result Option"
        verbose_name_plural = "AFB Microscopy Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class XpertMTB(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Xpert MTB Result Option"
        verbose_name_plural = "Xpert MTB Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class XpertRIF(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Xpert RIF Result Option"
        verbose_name_plural = "Xpert RIF Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name


class NoSPCResult(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "No SPC Result Option"
        verbose_name_plural = "No SPC Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name



# DIAGNOSIS
class TBDiagnosisMade(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "TB Diagnosis Made Option"
        verbose_name_plural = "TB Diagnosis Made Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class DiagnosisBacteriological(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Diagnosis Bacteriological Option"
        verbose_name_plural = "Diagnosis Bacteriological Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
class DiagnosedClinically(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Diagnosis Clinically Option"
        verbose_name_plural = "Diagnosis Clinically Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class TBTreatmentStarted(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "TBTreatmentStarted Option"
        verbose_name_plural = "TBTreatmentStarted Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class RegimenPrescribed(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "RegimenPrescribed Option"
        verbose_name_plural = "RegimenPrescribed Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class RegimenTypeOfChange(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Regimen Type Of Change Option"
        verbose_name_plural = "Regimen Type Of Change Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class RegimenReasonForChange(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Regimen Reason For Change Option"
        verbose_name_plural = "Regimen Reason For Change Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class TBTreatmentOutcome(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "TB Treatment Outcome Option"
        verbose_name_plural = "TB Treatment Outcome Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
    
class TBOtherDiagnosis(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "TB Other Diagnosis Option"
        verbose_name_plural = "TB Other Diagnosis Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class TBOtherDiagnosisMade(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "TB Other Diagnosis Made Option"
        verbose_name_plural = "TB Other Diagnosis Made Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
# ZONAL LAB TABLES
class CultureMethod(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Culture Method Option"
        verbose_name_plural = "Culture Method Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class MicroscopyType(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "MicroscopyType Option"
        verbose_name_plural = "MicroscopyType Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    

class CultureMicroscopyResults(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Culture Microscopy Results Option"
        verbose_name_plural = "Culture Microscopy Results Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class LJCultureResult(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "LJ Culture Result Option"
        verbose_name_plural = "LJ Culture Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class MGITCultureResult(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "MGIT Culture Result Option"
        verbose_name_plural = "MGIT Culture Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class PhenotypicDSTResults(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Phenotypic DST Result Option"
        verbose_name_plural = "Phenotypic DST Result Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
# class XpertXDRResults(models.Model):
#     value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
#     name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
#     description = models.TextField(blank=True, null=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
#     # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

#     class Meta:
#         verbose_name = "XpertXDR Result Option"
#         verbose_name_plural = "PhenXpertXDR Result Options"
#         ordering = ["id"]

#     def __str__(self):
#         return self.name
    
class XpertXDRResults(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Xpert XDR Result Option"
        verbose_name_plural = "Xpert XDR Results Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class XpertXDRResultsThree(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Xpert XDR Result Option 3"
        verbose_name_plural = "Xpert XDR Result Options 3"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
    
class XpertXDRResultsTwo(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "XpertXDR Result Option 2"
        verbose_name_plural = "Xpert XDR Result Options 2"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class FirstLineDrugs(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "First Line Drugs Option"
        verbose_name_plural = "First Line Drugs Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
     
class SecondLineDrugs(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Second Line Drugs Option"
        verbose_name_plural = "Second Line Drugs Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class MTBResultsLPA(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "MTB Results LPA Option"
        verbose_name_plural = "MTB Results LPA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class RIFResultLPA(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "RIF Results LPA Option"
        verbose_name_plural = "RIF Results LPA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class INHResultLPA(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "INH Results LPA Option"
        verbose_name_plural = "INH Results LPA Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class NanoporeResults(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Nanopore Results Option"
        verbose_name_plural = "Nanopore Results Options"
        ordering = ["id"]

    def __str__(self):
        return self.name

class NanoporeSequencingResults(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Nanopore Sequencing Results Option"
        verbose_name_plural = "Nanopore Sequencing Results Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
class NanoporeSequencingDelayedReasons(models.Model):
    value = models.IntegerField(unique=True)  # e.g., 1 for Yes, 0 for No
    name = models.CharField(max_length=200, unique=True)  # e.g., "Yes" or "No"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_created")
    # updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="yesno_na_options_updated")

    class Meta:
        verbose_name = "Nanopore Sequencing Delayed Reasons Option"
        verbose_name_plural = "Nanopore Sequencing Delayed Reasons Options"
        ordering = ["id"]

    def __str__(self):
        return self.name
    
    
    


