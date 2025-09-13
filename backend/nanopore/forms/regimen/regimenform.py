from django import forms
from nanopore.models import RegimenChanges

class RegimenChangesForm(forms.ModelForm):
    class Meta:
        model = RegimenChanges
        fields = ["date", "drug", "changes", "reason", "specify"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "drug": forms.TextInput(attrs={"class": "form-control"}),
            "changes": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.Select(attrs={"class": "form-select"}),
            "specify": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
