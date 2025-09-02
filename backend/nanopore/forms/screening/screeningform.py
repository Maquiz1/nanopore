from django import forms
from datetime import date
from nanopore.models import Screening
from clinical.models import YesNo
from django.core.exceptions import ValidationError

class ScreeningForm(forms.ModelForm):
    # Yes/No dropdowns
    genexpert_confirmation = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="Genexpert confirmation",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    consent = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="Has the patient provided written informed consent?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    unable_understand = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="Unable to understand the informed consent form?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    not_willing = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="Not willing to sign the informed consent form?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    enrolled = forms.ModelChoiceField(
        queryset=YesNo.objects.all(),
        empty_label="Select",
        label="Was this patient enrolled?",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Screening
        fields = "__all__"
        widgets = {
            "pid": forms.HiddenInput(),
            "pid1": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": 3,
                "placeholder": "Enter PID1",
                "id": "id_pid1",
            }),
            "pid2": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": 3,
                "placeholder": "Repeat PID1 for validation",
                "title": "Must match PID1 to ensure uniqueness",
                "id": "id_pid2",
            }),
            "screening_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "dob": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pid1 = cleaned_data.get("pid1")
        pid2 = cleaned_data.get("pid2")
        dob = cleaned_data.get("dob")
        age = cleaned_data.get("age")
        today = date.today()

        # Validate PID1 == PID2
        if pid1 and pid2:
            if pid1 != pid2:
                raise ValidationError("PID2 must match PID1.")
        else:
            raise ValidationError("Both PID1 and PID2 are required.")

        # Combine PID with prefix (set prefix in view or model)
        pid_prefix = getattr(self.instance, "pid_prefix", "")
        final_pid = f"{pid_prefix}{pid1}"
        cleaned_data["pid"] = final_pid

        # Ensure unique PID
        if Screening.objects.filter(pid=final_pid).exclude(pk=self.instance.pk).exists():
            raise ValidationError(f"The PID {final_pid} already exists. Use a different PID1.")

        # Auto-calculate Age <-> DOB
        if dob and not age:
            cleaned_data["age"] = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        elif age and not dob:
            cleaned_data["dob"] = date(today.year - age, today.month, today.day)
        elif not dob and not age:
            raise ValidationError("Provide either Date of Birth or Age.")

        # Auto-calculate eligibility
        consent = cleaned_data.get("consent")
        unable_understand = cleaned_data.get("unable_understand")
        not_willing = cleaned_data.get("not_willing")
        if consent and unable_understand and not_willing:
            cleaned_data["eligible"] = consent.name == "Yes" and unable_understand.name == "No" and not_willing.name == "No"
        else:
            cleaned_data["eligible"] = False

        return cleaned_data
