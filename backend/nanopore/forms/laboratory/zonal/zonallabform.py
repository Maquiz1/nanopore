from django import forms
from nanopore.models import ZonalLaboratory

class ZonalLaboratoryForm(forms.ModelForm):
    class Meta:
        model = ZonalLaboratory
        fields = ["screening", "test_name", "result", "test_date", "remarks"]
        widgets = {
            "screening": forms.Select(attrs={"class": "form-select"}),
            "test_name": forms.TextInput(attrs={"class": "form-control"}),
            "result": forms.TextInput(attrs={"class": "form-control"}),
            "test_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
