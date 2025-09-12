from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import Diagnosis, Screening
from options.models import (
    YesNo, TBDiagnosisMade, DiagnosisBacteriological, DiagnosedClinically,
    TBTreatmentStarted, RegimenPrescribed, TBTreatmentOutcome
)

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = [
            "screening",
            "tb_diagnosis", "tb_diagnosis_date", "tb_diagnosis_made", "diagnosis_made_other",
            "bacteriological_diagnosis", "tb_diagnosed_clinically", "tb_clinically_other",
            "clinician_received_date", "tb_treatment", "tb_treatment_date", "tb_facility",
            "tb_reason", "tb_register_number", "tb_regimen", "tb_regimen_other",
            "regimen_changed", "tb_outcome2", "tb_outcome2_date", 
            "tb_other_diagnosis","tb_other_specify","tb_diagnosis_made2",
            "remarks"
        ]
        labels = {
            "tb_diagnosis": "4(a). Was a TB diagnosis made?",
            "tb_diagnosis_date": "TB Diagnosis Date",
            "tb_diagnosis_made": "TB Diagnosis Made (Method)",
            "diagnosis_made_other": "Other Diagnosis Made",
            "bacteriological_diagnosis": "Bacteriological Diagnosis",
            "tb_diagnosed_clinically": "Diagnosed Clinically",
            "tb_clinically_other": "Other Clinical Diagnosis",
            "clinician_received_date": "Date Received by Clinician",
            "tb_treatment": "TB Treatment Started",
            "tb_treatment_date": "TB Treatment Date",
            "tb_facility": "Treatment Facility",
            "tb_reason": "Reason for TB Diagnosis",
            "tb_register_number": "TB Register Number",
            "tb_regimen": "TB Regimen Prescribed",
            "tb_regimen_other": "Other TB Regimen",
            "regimen_changed": "Regimen Changed",
            "tb_outcome2": "TB Treatment Outcome",
            "tb_outcome2_date": "Outcome Date",
            "tb_other_diagnosis": "12a. What diagnosis other than TB was made?",
            "tb_other_specify": "If Other Mention If Bacterial pneumonia, specify causative species if known",
            "tb_diagnosis_made2": "12b. How was this diagnosis made?",
            "remarks": "Remarks / Notes",
        }
        widgets = {
            "screening": forms.HiddenInput(),
            "tb_diagnosis": forms.Select(attrs={"class": "form-select"}),
            "tb_diagnosis_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tb_diagnosis_made": forms.Select(attrs={"class": "form-select"}),
            "diagnosis_made_other": forms.TextInput(attrs={"class": "form-control"}),

            "bacteriological_diagnosis": forms.Select(attrs={"class": "form-select"}),
            "tb_diagnosed_clinically": forms.Select(attrs={"class": "form-select"}),
            "tb_clinically_other": forms.TextInput(attrs={"class": "form-control"}),

            "clinician_received_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tb_treatment": forms.Select(attrs={"class": "form-select"}),
            "tb_treatment_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "tb_facility": forms.TextInput(attrs={"class": "form-control"}),
            "tb_reason": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "tb_register_number": forms.TextInput(attrs={"class": "form-control"}),
            "tb_regimen": forms.Select(attrs={"class": "form-select"}),
            "tb_regimen_other": forms.TextInput(attrs={"class": "form-control"}),
            "regimen_changed": forms.Select(attrs={"class": "form-select"}),
            "tb_outcome2": forms.Select(attrs={"class": "form-select"}),
            "tb_outcome2_date": forms.DateInput(attrs={"type": "date","class": "form-control"}),
            "tb_other_diagnosis": forms.Select(attrs={"class": "form-select"}),
            "tb_other_specify": forms.TextInput(attrs={"class": "form-control"}),
            "tb_diagnosis_made2": forms.Select(attrs={"class": "form-select"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        self.screening_instance = kwargs.pop("screening_instance", None)
        super().__init__(*args, **kwargs)

        # If we have a screening instance, assign it to hidden field initial
        if self.screening_instance:
            self.fields["screening"].initial = self.screening_instance.pk

        # For read-only display in template
        self.readonly_screening = self.screening_instance

    def clean(self):
        cleaned_data = super().clean()

        # Only validate for new records
        if self.instance.pk is None and self.screening_instance:
            if hasattr(self.screening_instance, "diagnosis"):
                raise ValidationError(f"This screening {self.screening_instance} already has a diagnosis record.")

        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Assign the actual Screening instance
        if not obj.pk and self.screening_instance:
            obj.screening = self.screening_instance

        if commit:
            obj.save()
            self.save_m2m()

        return obj
