from django import forms
from datetime import date
from nanopore.models import Screening
from clinical.models import YesNo
from django.core.exceptions import ValidationError
from reasons.models import EnrolledReason

class ScreeningForm(forms.ModelForm):
    # Consent / Eligibility fields

    # INCLUSION fields

    present_symptoms = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="4. Does the patient present with signs and symptoms suggestive of pulmonary TB or another pulmonary infection of bacterial, viral, or fungal origin?",
        widget=forms.Select(attrs={"class": "form-select"}),
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
    
    genexpert_confirmation = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="Genexpert confirmation",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False
    )
    
    consent = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="7. Has the patient provided written informed consent to participate?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    
    # EXCLUSION fields

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
    
    # Enrollment fields
    enrolled = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="11(a). Was this patient enrolled?",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False
    )
    reasons = forms.ModelChoiceField(
        queryset=EnrolledReason.objects.all(),
        empty_label="Select",
        label="11(b).If not, what was the reason?",
        widget=forms.Select(attrs={"class": "form-select"}),
        required=False
    )
    reasons_other = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        label="11(b). Other, please explain:",
        required=False
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
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "consent_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pid1 = cleaned_data.get("pid1")
        pid2 = cleaned_data.get("pid2")

        if not pid1 or not pid2:
            raise ValidationError("Both PID1 and PID2 are required.")
        if pid1 != pid2:
            raise ValidationError("PID2 must match PID1.")

        # Generate final PID from site prefix
        site = cleaned_data.get("site") or getattr(self.instance, "site", None)
        pid_prefix = site.pid_prefix if site else ""
        final_pid = f"{pid_prefix}{pid1}"
        cleaned_data["pid"] = final_pid

        # Ensure unique PID
        if Screening.objects.filter(pid=final_pid).exclude(pk=self.instance.pk).exists():
            raise ValidationError(f"The PID {final_pid} already exists. Please choose another PID1.")

        # Auto-calculate Age ↔ DOB
        dob = cleaned_data.get("dob")
        age = cleaned_data.get("age")
        today = date.today()
        if dob and not age:
            cleaned_data["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        elif age and not dob:
            cleaned_data["dob"] = date(today.year - age, today.month, today.day)
        elif not dob and not age:
            raise ValidationError("Provide either Date of Birth or Age.")

        # Compute eligibility
        # consent = cleaned_data.get("consent")
        # unable_understand = cleaned_data.get("unable_understand")
        # not_willing = cleaned_data.get("not_willing")
        
        # cleaned_data["eligible"] = (
        #     consent.name == "Yes" and unable_understand.name == "No" and not_willing.name == "No"
        # ) if consent and unable_understand and not_willing else False
        
        
        # Compute eligibility
        consent = cleaned_data.get("consent")
        unable_understand = cleaned_data.get("unable_understand")
        not_willing = cleaned_data.get("not_willing")
        age18years = cleaned_data.get("age18years")
        present_symptoms = cleaned_data.get("present_symptoms")
        produce_resp_sample = cleaned_data.get("produce_resp_sample")

        consent_logic = (
            consent and unable_understand and not_willing and
            consent.name == "Yes" and unable_understand.name == "No" and not_willing.name == "No"
        )

        screening_criteria_logic = (
            age18years and present_symptoms and produce_resp_sample and
            age18years.name == "Yes" and present_symptoms.name == "Yes" and produce_resp_sample.name == "Yes"
        )

        cleaned_data["eligible"] = consent_logic and screening_criteria_logic

        return cleaned_data
