from django import forms
from nanopore.models import ClinicLaboratory
from django.core.exceptions import ValidationError

class ClinicLaboratoryForm(forms.ModelForm):
    class Meta:
        model = ClinicLaboratory
        fields = ["screening", "test_name", "result", "test_date", "remarks"]
        widgets = {
            "screening": forms.Select(attrs={"class": "form-select"}),
            "test_name": forms.TextInput(attrs={"class": "form-control"}),
            "result": forms.TextInput(attrs={"class": "form-control"}),
            "test_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")
        if hasattr(screening, "clinic_laboratory"):
            raise ValidationError(f"This screening {screening} already has a laboratory record.")
        return cleaned_data
