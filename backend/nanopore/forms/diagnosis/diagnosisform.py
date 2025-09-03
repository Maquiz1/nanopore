from django import forms
from nanopore.models import Diagnosis

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ["screening", "diagnosis_name", "diagnosis_date", "remarks"]
        widgets = {
            "screening": forms.Select(attrs={"class": "form-select"}),
            "diagnosis_name": forms.TextInput(attrs={"class": "form-control"}),
            "diagnosis_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
