from django import forms
from datetime import date
from django.core.exceptions import ValidationError
from nanopore.models import Screening
from clinical.models import YesNo
from demographic.models import Sex
from reasons.models import EnrolledReason
from locations.models import Zone


class ScreeningForm(forms.ModelForm):
    sex = forms.ModelChoiceField(
        queryset=Sex.objects.all(),
        empty_label="Select",
        label="Sex",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    present_symptoms = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="4. Does the patient present with signs and symptoms suggestive of pulmonary TB or another pulmonary infection?",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    genexpert_confirmation = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="4(a). Is the patient diagnosed with TB as confirmed by GeneXpert MTB/Rif (Ultra)?",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,
    )

    produce_resp_sample = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="5. Is the patient capable of producing a sputum sample?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    age18years = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="6. Is the Patient at least 18 years old?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    consent = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="7. Has the patient provided written informed consent?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    consent_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="8. Date of Consent",
        required=False,
        input_formats=["%d/%m/%Y", "%Y-%m-%d"],
    )

    not_willing = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="9. Not willing to sign the informed consent form?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    unable_understand = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="10. Unable to understand the informed consent form and/or the study procedures?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    enrolled = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="11(a). Was this patient enrolled?",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,  # ✅ handled in clean()
    )

    reasons = forms.ModelChoiceField(
        queryset=EnrolledReason.objects.all(),
        empty_label="Select",
        label="11(b). If not, what was the reason?",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False,  # ✅ handled in clean()
    )

    reasons_other = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        label="11(b). Other, please explain:",
        required=False,  # ✅ handled in clean()
    )

    class Meta:
        model = Screening
        fields = "__all__"
        widgets = {
            "pid": forms.HiddenInput(),
            "pid1": forms.TextInput(attrs={"class": "form-control", "maxlength": 3}),
            "pid2": forms.TextInput(attrs={"class": "form-control", "maxlength": 3}),
            "screening_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "dob": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "age": forms.NumberInput(attrs={"class": "form-control", "readonly": True}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["screening_date"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]
        self.fields["dob"].input_formats = ["%d/%m/%Y", "%Y-%m-%d"]

        # Auto-populate age at screening
        dob = self.initial.get("dob") or getattr(self.instance, "dob", None)
        screening_date = self.initial.get("screening_date") or getattr(self.instance, "screening_date", date.today())
        if dob:
            age_at_screening = screening_date.year - dob.year - (
                (screening_date.month, screening_date.day) < (dob.month, dob.day)
            )
            self.initial["age"] = age_at_screening

        # current_age relative to today for display only
        if dob:
            today = date.today()
            self.current_age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        else:
            self.current_age = None

    @property
    def zone(self):
        site = self.initial.get("site") or getattr(self.instance, "site", None)
        if site and site.district and site.district.region and site.district.region.zone:
            return site.district.region.zone
        return None

    def clean(self):
        cleaned_data = super().clean()

        site = cleaned_data.get("site") or getattr(self.instance, "site", None)
        zone = self.zone

        present_symptoms = cleaned_data.get("present_symptoms")
        genexpert_confirmation = cleaned_data.get("genexpert_confirmation")

        # Conditional required based on Zone
        if zone and zone.name.lower() == "dar es salaam":
            if not present_symptoms:
                self.add_error("present_symptoms", "This field is required for Dar es Salaam zone.")
        elif zone:
            if not genexpert_confirmation:
                self.add_error("genexpert_confirmation", "This field is required for zones outside Dar es Salaam.")

        # PID validation
        pid1 = cleaned_data.get("pid1")
        pid2 = cleaned_data.get("pid2")
        if not pid1 or not pid2:
            raise ValidationError("Both PID1 and PID2 are required.")
        if pid1 != pid2:
            raise ValidationError("PID2 must match PID1.")

        pid_prefix = site.pid_prefix if site else ""
        final_pid = f"{pid_prefix}{pid1}"
        cleaned_data["pid"] = final_pid
        if Screening.objects.filter(pid=final_pid).exclude(pk=self.instance.pk).exists():
            raise ValidationError(f"The PID {final_pid} already exists. Please choose another PID1.")

        

        # Age calculation at screening
        dob = cleaned_data.get("dob")
        screening_date = cleaned_data.get("screening_date")

        if not dob:
            raise ValidationError("Date of Birth is required to calculate age.")

        if not screening_date:
            raise ValidationError("Screening date is required.")

        if screening_date < dob:
            raise ValidationError("Screening date cannot be before Date of Birth.")


        # Check if screening date is before dob
        if screening_date < dob:
            raise ValidationError("Screening date cannot be before Date of Birth.")

        # Check if screening date is within allowed range
        min_date = date(2025, 1, 20)
        today = date.today()
        if screening_date < min_date or screening_date > today:
            raise ValidationError(f"Screening date must be between {min_date.strftime('%Y-%m-%d')} and today.")


        age_at_screening = screening_date.year - dob.year - (
            (screening_date.month, screening_date.day) < (dob.month, dob.day)
        )
        if age_at_screening < 18:
            raise ValidationError("Patient must be at least 18 years old at the time of screening.")

        cleaned_data["age"] = age_at_screening

        # Eligibility logic
        consent = cleaned_data.get("consent")
        unable_understand = cleaned_data.get("unable_understand")
        not_willing = cleaned_data.get("not_willing")
        age18years = cleaned_data.get("age18years")
        produce_resp_sample = cleaned_data.get("produce_resp_sample")

        eligible = True
        if not (consent and unable_understand and not_willing):
            eligible = False
        elif not (consent.name == "Yes" and unable_understand.name == "No" and not_willing.name == "No"):
            eligible = False

        if age_at_screening < 18 or not (age18years and age18years.name == "Yes"):
            eligible = False

        if zone and zone.name.lower() == "dar es salaam":
            if not (present_symptoms and present_symptoms.name == "Yes"):
                eligible = False
        elif zone:
            if not (genexpert_confirmation and genexpert_confirmation.name == "Yes"):
                eligible = False

        if not (produce_resp_sample and produce_resp_sample.name == "Yes"):
            eligible = False

        cleaned_data["eligible"] = eligible

        # ✅ Enrolled required only if eligible=True
        enrolled = cleaned_data.get("enrolled")
        reasons = cleaned_data.get("reasons")
        reasons_other = cleaned_data.get("reasons_other")

        if eligible:
            if not enrolled:
                self.add_error("enrolled", "This field is required because patient is eligible.")
            elif enrolled.name == "No":
                if not reasons:
                    self.add_error("reasons", "This field is required if patient is not enrolled.")
                elif reasons.name.lower().startswith("other"):
                    if not reasons_other:
                        self.add_error("reasons_other", "This field is required if 'Other' is selected as a reason.")

        return cleaned_data
