from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from demographic.models import Sex
from locations.models import Site
from clinical.models import YesNo
from reasons.models import EnrolledReason
from django.contrib.auth import get_user_model

User = get_user_model()

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
    dob = models.DateField()
    age = models.IntegerField()
    eligible = models.BooleanField(default=False)

    # Inclusion / Consent fields
    age18years = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_age18years")
    present_symptoms = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_present_symptoms", blank=True, null=True)
    produce_resp_sample = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_produce_resp_sample")
    genexpert_confirmation = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_genexpert_confirmation", blank=True, null=True)
    consent = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_consent")
    consent_date = models.DateField(blank=True, null=True)
    unable_understand = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_unable_understand")
    not_willing = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_not_willing")
    enrolled = models.ForeignKey(YesNo, on_delete=models.PROTECT, related_name="screening_enrolled")
    reasons = models.ForeignKey(EnrolledReason, on_delete=models.PROTECT, related_name="screening_enrolled_reasons", null=True, blank=True)
    reasons_other = models.TextField(blank=True, null=True)
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="screenings_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="screenings_updated")

    class Meta:
        ordering = ["screening_date", "pid"]

    def __str__(self):
        return f"{self.pid} - {self.site}"

    def save(self, *args, **kwargs):
        pid_prefix = self.site.pid_prefix if self.site else ""
        if self.pid1:
            self.pid = f"{pid_prefix}{self.pid1}"

        today = date.today()
        if self.dob and not self.age:
            self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))
        elif self.age and not self.dob:
            self.dob = date(today.year - self.age, today.month, today.day)
        elif self.dob and self.age:
            self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

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

    def clean(self):
        super().clean()
        today = timezone.now().date()
        min_date = date(2025, 1, 20)

        if self.screening_date < min_date:
            raise ValidationError({"screening_date": "Screening date cannot be before 20 Jan 2025."})
        if self.screening_date > today:
            raise ValidationError({"screening_date": "Screening date cannot be in the future."})
        if self.consent and self.consent.name.lower() == "yes":
            if not self.consent_date:
                raise ValidationError({"consent_date": "Consent date is required when consent is Yes."})
            if self.consent_date < self.screening_date:
                raise ValidationError({"consent_date": "Consent date must be on or after the screening date."})
            if self.consent_date > today:
                raise ValidationError({"consent_date": "Consent date cannot be in the future."})
        else:
            if self.consent_date:
                raise ValidationError({"consent_date": "Consent date should be empty when consent is No."})
