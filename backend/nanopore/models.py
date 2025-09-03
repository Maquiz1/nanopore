from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model
from datetime import date

# Related models
from demographic.models import Sex
from locations.models import Site
from clinical.models import YesNo
from reasons.models import EnrolledReason

User = get_user_model()

# Validator for 3-digit PID parts
three_digit_validator = RegexValidator(
    regex=r'^\d{3}$',
    message="This field must be exactly 3 digits."
)


class Screening(models.Model):
    screening_date = models.DateField()
    pid1 = models.CharField(max_length=3, validators=[three_digit_validator])
    pid2 = models.CharField(max_length=3, validators=[three_digit_validator])
    pid = models.CharField(max_length=255, unique=True, editable=False)

    sex = models.ForeignKey(Sex, on_delete=models.SET_NULL, null=True, blank=True)
    dob = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

    # Eligibility (hidden boolean)
    eligible = models.BooleanField(default=False)

    # Inclusion / Consent fields
    
    age18years = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_age18years")
    present_symptoms = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_present_symptoms")
    produce_resp_sample = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_produce_resp_sample")

    genexpert_confirmation = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_genexpert_confirmation", blank=True, null=True
    )
    
    
    consent = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_consent"
    )
    consent_date = models.DateField(blank=True, null=True)

    # Exclusion fields
    unable_understand = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_unable_understand"
    )
    not_willing = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_not_willing"
    )

    # Enrollment
    enrolled = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_enrolled", null=True, blank=True
    )
    reasons = models.ForeignKey(
        EnrolledReason, on_delete=models.PROTECT, related_name="screening_enrolled_reasons", null=True, blank=True
    )
    reasons_other = models.TextField(blank=True, null=True)


    site = models.ForeignKey(Site, on_delete=models.SET_NULL, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="screenings_created"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, blank=True, null=True, related_name="screenings_updated"
    )

    class Meta:
        # db_table = "screening"
        ordering = ["screening_date", "pid"]

    def __str__(self):
        return f"{self.pid} - {self.site}"

    def save(self, *args, **kwargs):
        # Always generate PID from site prefix + pid1
        pid_prefix = self.site.pid_prefix if self.site else ""
        if self.pid1:
            self.pid = f"{pid_prefix}{self.pid1}"

        # Auto-calculate Age <-> DOB
        today = date.today()
        if self.dob and not self.age:
            self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        elif self.age and not self.dob:
            self.dob = date(today.year - self.age, today.month, today.day)
        elif self.dob and self.age:
            self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

        # Compute eligibility
        # self.eligible = (
        #     (self.consent and self.consent.name == 'Yes') and
        #     (self.unable_understand and self.unable_understand.name == 'No') and
        #     (self.not_willing and self.not_willing.name == 'No')
        # )
        
        consent_logic = (
            (self.consent and self.consent.name == 'Yes') and
            (self.unable_understand and self.unable_understand.name == 'No') and
            (self.not_willing and self.not_willing.name == 'No')
            )
        
        screening_criteria_logic = (
            (self.age18years and self.age18years.name == 'Yes') and
            (self.present_symptoms and self.present_symptoms.name == 'Yes') and
            (self.produce_resp_sample and self.produce_resp_sample.name == 'Yes')
        )

        self.eligible = consent_logic and screening_criteria_logic

        super().save(*args, **kwargs)


class Enrollment(models.Model):
    screening = models.OneToOneField(
        Screening, on_delete=models.CASCADE, related_name="enrollment"
    )
    enrollment_date = models.DateField()
    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments_created"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="enrollments_updated"
    )

    class Meta:
        # db_table = "enrollment"
        ordering = ["screening"]

    def __str__(self):
        return f"Enrollment for {self.screening.pid}"
    
    
class ClinicLaboratory(models.Model):
    # enrollment = models.ForeignKey(
    #     "Enrollment", on_delete=models.CASCADE, related_name="clinic_labs"
    # )
    screening = models.OneToOneField(
        Screening, on_delete=models.CASCADE, related_name="clinic_laboratory"
    )
    test_name = models.CharField(max_length=100)
    result = models.CharField(max_length=100, blank=True, null=True)
    test_date = models.DateField()

    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_labs_created"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="clinic_labs_updated"
    )

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid}"


class Diagnosis(models.Model):
    screening = models.OneToOneField(
        Screening, on_delete=models.CASCADE, related_name="diagnosis"
    )
    diagnosis_name = models.CharField(max_length=200)
    diagnosis_date = models.DateField()

    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses_created"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="diagnoses_updated"
    )

    class Meta:
        ordering = ["-diagnosis_date"]

    def __str__(self):
        return f"Diagnosis for {self.screening.pid}: {self.diagnosis_name}"


class ZonalLaboratory(models.Model):
    # Zonal labs are for all patients in the zone, so link directly to screening
    screening = models.OneToOneField(
        "Screening", on_delete=models.CASCADE, related_name="zonal_laboratory"
    )
    test_name = models.CharField(max_length=100)
    result = models.CharField(max_length=100, blank=True, null=True)
    test_date = models.DateField()

    remarks = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_created"
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="zonal_labs_updated"
    )

    class Meta:
        ordering = ["-test_date"]

    def __str__(self):
        return f"{self.test_name} for {self.screening.pid} (Zonal Lab)"
