from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from datetime import date

# Related models
from demographic.models import Sex
from locations.models import Site
from clinical.models import YesNo

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
    consent = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_consent"
    )
    consent_date = models.DateField(blank=True, null=True)
    
    genexpert_confirmation = models.ForeignKey(
        YesNo, on_delete=models.PROTECT, related_name="screening_genexpert_confirmation"
    )

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
        db_table = "screening"
        ordering = ["screening_date", "pid"]

    def __str__(self):
        return f"{self.pid} - {self.site}"

    def save(self, *args, **kwargs):
        # Ensure PID is generated from prefix + pid1
        pid_prefix = getattr(self, "pid_prefix", "")  # set in view or model
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
        self.eligible = (
            (self.consent and self.consent.name == 'Yes') and
            (self.unable_understand and self.unable_understand.name == 'No') and
            (self.not_willing and self.not_willing.name == 'No')
        )

        super().save(*args, **kwargs)

class Enrollment(models.Model):
    screening = models.OneToOneField(
        Screening, on_delete=models.CASCADE, related_name="enrollment"
    )
    enrollment_date = models.DateField()  # ✅ required

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
        db_table = "enrollment"
        ordering = ["screening"]

    def __str__(self):
        return f"Enrollment for {self.screening.pid}"
