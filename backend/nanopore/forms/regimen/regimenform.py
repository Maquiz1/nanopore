from django import forms
from nanopore.models import RegimenChanges

class RegimenChangesForm(forms.ModelForm):
    class Meta:
        model = RegimenChanges
        fields = ["date", "drug", "changes", "reason", "specify"]
        labels = {
            "date": "4(b). Date of regimen change",
            "drug": "4(c). Drug(s) changed",
            "changes": "4(d). Nature of change",
            "reason": "4(e). Reason for change",
            "specify": "4(f). If other, please specify",
        }
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "drug": forms.TextInput(attrs={"class": "form-control"}),
            "changes": forms.Select(attrs={"class": "form-select"}),
            "reason": forms.Select(attrs={"class": "form-select"}),
            "specify": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
