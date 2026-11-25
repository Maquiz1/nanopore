from nanopore.forms.reason_for_change import REASON, ReasonForChangeMixin
from django import forms
from nanopore.models import RegimenChanges

class RegimenChangesForm(ReasonForChangeMixin, forms.ModelForm):
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

    def clean(self):
        cleaned = super().clean()
        reason = cleaned.get("reason")
        if reason and "other" in reason.name.lower():
            if not (cleaned.get("specify") or "").strip():
                self.add_error("specify", "Please specify the other reason.")
        else:
            cleaned["specify"] = None
        return cleaned

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Not 4(e) (why the regimen changed): why a saved row is being corrected
        self.fields[REASON].label = "Why are you correcting this saved row?"

