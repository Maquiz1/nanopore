from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import ClinicLaboratory
from common.labels.laboratory.clinic.clinic_labels import CLINIC_LABELS   # ✅ import from core app

class ClinicLaboratoryForm(forms.ModelForm):
    class Meta:
        model = ClinicLaboratory
        fields = [
            # General info
            "screening",
                        
            # 🔹 Sputum sample
            "sample_received",
            "date_sample1_received",
            "sample_reason",
            "other_reason",
            "new_sample",
            "new_reason",
            "number_received",
            "date_sample1_collected",
            "date_sample2_collected",
            "date_sample2_received",
            "appearance_sample1",
            "sample1_volume",
            "appearance_sample2",
            "sample2_volume",

            # 🔹 AFB Microscopy
            "afb_microscopy_conducted",
            "afb_a_date",
            "technique_a",
            "afb_a_results",
            "afb_b_date",
            "technique_b",
            "afb_b_results",

            # 🔹 Xpert MTB/RIF (Ultra)
            "xpert_mtb_rif_conducted",
            "xpert_date",
            "xpert_mtb",
            "error_code",
            "xpert_rif",
            "ct_value",
            "ct_na",
            
            "remarks",
        ]
        # fields = TB_LABELS.keys()
        labels = CLINIC_LABELS
        
        widgets = {
            # General info
            "screening": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),

            # 🔹 Sputum sample
            "sample_received": forms.Select(attrs={"class": "form-select"}),
            "date_sample1_received": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "sample_reason": forms.Select(attrs={"class": "form-select"}),
            "other_reason": forms.TextInput(attrs={"class": "form-control"}),
            "new_sample": forms.Select(attrs={"class": "form-select"}),
            "new_reason": forms.TextInput(attrs={"class": "form-control"}),
            "number_received": forms.Select(attrs={"class": "form-select"}),
            "date_sample1_collected": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_sample2_collected": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_sample2_received": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "appearance_sample1": forms.Select(attrs={"class": "form-select"}),
            "sample1_volume": forms.TextInput(attrs={"class": "form-control"}),
            "appearance_sample2": forms.Select(attrs={"class": "form-select"}),
            "sample2_volume": forms.TextInput(attrs={"class": "form-control"}),

            # 🔹 AFB Microscopy
            "afb_microscopy_conducted": forms.Select(attrs={"class": "form-select"}),
            "afb_a_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "technique_a": forms.Select(attrs={"class": "form-select"}),
            "afb_a_results": forms.Select(attrs={"class": "form-select"}),
            "afb_b_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "technique_b": forms.Select(attrs={"class": "form-select"}),
            "afb_b_results": forms.Select(attrs={"class": "form-select"}),

            # 🔹 Xpert MTB/RIF (Ultra)
            "xpert_mtb_rif_conducted": forms.Select(attrs={"class": "form-select"}),
            "xpert_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "xpert_mtb": forms.Select(attrs={"class": "form-select"}),
            "error_code": forms.NumberInput(attrs={"class": "form-control"}),
            "xpert_rif": forms.Select(attrs={"class": "form-select"}),
            "ct_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
            # "ct_na": forms.Select(attrs={"class": "form-select"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['screening'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")
        if screening:
            # Exclude the current instance when checking for duplicates
            qs = ClinicLaboratory.objects.filter(screening=screening)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(f"This screening {screening} already has a laboratory record.")
        return cleaned_data
