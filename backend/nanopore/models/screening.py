from django.db import models
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date
from demographic.models import Sex
from locations.models import Site
from options.models import YesNo, EnrolledReason
from django.contrib.auth import get_user_model
import re

User = get_user_model()

three_digit_validator = RegexValidator(
    regex=r'^\d{3}$',
    message="This field must be exactly 3 digits."
)

class Screening(models.Model):
    screening_date = models.DateField()
    pid1 = models.CharField(max_length=3, validators=[three_digit_validator])
    pid2 = models.CharField(max_length=3, validators=[three_digit_validator])
    pid = models.CharField(max_length=16, unique=True, editable=False)
    sex = models.ForeignKey(Sex, on_delete=models.SET_NULL, null=True, blank=True, related_name="screenings_sex")
    dob = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    eligible = models.BooleanField(default=False)

    # Inclusion / Consent fields
    age18years = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_age18years")
    present_symptoms = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_present_symptoms")
    produce_resp_sample = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_produce_resp_sample")
    genexpert_confirmation = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_genexpert_confirmation")
    consent = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_consent")
    consent_date = models.DateField(blank=True, null=True)
    unable_understand = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_unable_understand")
    not_willing = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_not_willing")
    enrolled = models.ForeignKey(YesNo, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_enrolled")
    reasons = models.ForeignKey(EnrolledReason, on_delete=models.SET_NULL, blank=True, null=True, related_name="screening_enrolled_reasons")
    reasons_other = models.TextField(blank=True, null=True)
    site = models.ForeignKey(Site, on_delete=models.SET_NULL, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="screenings_created")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name="screenings_updated")
    test2 = models.CharField(blank=True, null=True)
    test3 = models.CharField(blank=True, null=True)

    class Meta:
        ordering = ["screening_date", "pid"]
        indexes = [
            models.Index(fields=["site", "pid"])
        ]

    def __str__(self):
        return f"{self.pid} - {self.site}"
    
    # @property
    # def substudy(self):
    #     cl = self.clinic_laboratory
    #     if cl:
    #         if cl.xpert_mtb_rif_conducted == 1 and cl.xpert_mtb in [2, 3, 4, 5, 6]:
    #             return "Substudy 2"
    #         elif (cl.xpert_mtb_rif_conducted == 1 and cl.xpert_mtb in [1, 7, 8, 9]) or cl.xpert_mtb_rif_conducted == 2:
    #             return "Substudy 4"
    #         elif (cl.xpert_mtb_rif_conducted == 1 and cl.xpert_mtb is None) or cl.xpert_mtb_rif_conducted is None:
    #             return "Uncategorized"
    #     return "-"
    
    # def substudy(self):
    #     cl = getattr(self, 'clinic_laboratory', None)
    #     if cl:
    #         if cl.xpert_mtb_rif_conducted == 1 and cl.xpert_mtb in [2, 3, 4, 5, 6]:
    #             return "Substudy 2"
    #         elif (cl.xpert_mtb_rif_conducted == 1 and cl.xpert_mtb in [1, 7, 8, 9]) or cl.xpert_mtb_rif_conducted == 2:
    #             return "Substudy 4"
    #         elif (cl.xpert_mtb_rif_conducted == 1 and cl.xpert_mtb is None) or cl.xpert_mtb_rif_conducted is None:
    #             return "Uncategorized"
    #     return "Uncategorized"

    def save(self, *args, **kwargs):
        # Generate PID
        pid_prefix = self.site.pid_prefix if self.site else ""
        if self.pid1:
            self.pid = f"{pid_prefix}{self.pid1}"

        # --- Eligibility calculation ---
        consent_logic = all([
            self.consent and self.consent.name.strip().lower() == 'yes',
            self.unable_understand and self.unable_understand.name.strip().lower() == 'no',
            self.not_willing and self.not_willing.name.strip().lower() == 'no',
        ])
        screening_logic = all([
            self.age18years and self.age18years.name.strip().lower() == 'yes',
            self.produce_resp_sample and self.produce_resp_sample.name.strip().lower() == 'yes',
        ])
        zone_name = ''
        if self.site and self.site.district and self.site.district.region and self.site.district.region.zone:
            zone_name = self.site.district.region.zone.name.strip().lower()
        if zone_name == "dar es salaam":
            screening_logic = screening_logic and (self.present_symptoms and self.present_symptoms.name.strip().lower() == 'yes')
        else:
            screening_logic = screening_logic and (self.genexpert_confirmation and self.genexpert_confirmation.name.strip().lower() == 'yes')

        self.eligible = consent_logic and screening_logic
        
        if self.remarks:
            self.remarks = re.sub(r"\s+", " ", self.remarks.strip())
        if self.reasons_other:
            self.reasons_other = re.sub(r"\s+", " ", self.reasons_other.strip())

        super().save(*args, **kwargs)


    def clean(self):
        super().clean()
        today = timezone.now().date()
        min_date = date(2025, 1, 20)

        # --- Screening date validation ---
        if self.screening_date is None:
            raise ValidationError({"screening_date": "Screening date is required."})
        
        if self.screening_date < min_date:
            raise ValidationError({"screening_date": "Screening date cannot be before 20 Jan 2025."})
        if self.screening_date > today:
            raise ValidationError({"screening_date": "Screening date cannot be in the future."})

        # --- Age / DOB validation (independent, at least one required) ---
        if not self.dob and self.age is None:
            raise ValidationError({"age": "Either Age or DOB is required."})

        calculated_age = None
        if self.dob and self.screening_date:
            if self.screening_date < self.dob:
                raise ValidationError({"dob": "Screening date cannot be before Date of Birth."})

            calculated_age = self.screening_date.year - self.dob.year - (
                (self.screening_date.month, self.screening_date.day) < (self.dob.month, self.dob.day)
            )

            if calculated_age < 18:
                raise ValidationError({"dob": "Participant must be at least 18 years old based on DOB."})

        if self.age is not None:
            if self.age < 18:
                raise ValidationError({"age": "Participant must be at least 18 years old based on Age."})

        # If both are given, check consistency (only if screening_date available)
        # if self.dob and self.age is not None and calculated_age is not None:
        #     if calculated_age != self.age:
        #         raise ValidationError({
        #             "age": f"Provided Age ({self.age}) does not match age from DOB ({calculated_age})."
        #         })


        # --- Consent date validation ---
        if self.consent and self.consent.name.strip().lower() == "yes":
            if not self.consent_date:
                raise ValidationError({"consent_date": "Consent date is required when consent is Yes."})
            if self.consent_date < self.screening_date:
                raise ValidationError({"consent_date": "Consent date must be on or after the screening date."})
            if self.consent_date > today:
                raise ValidationError({"consent_date": "Consent date cannot be in the future."})
        else:
            if self.consent_date:
                raise ValidationError({"consent_date": "Consent date should be empty when consent is No."})
