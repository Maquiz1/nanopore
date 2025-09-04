# nanopore/forms/enrollment/enrollmentform.py
from django import forms
from nanopore.models import Enrollment
from django.core.exceptions import ValidationError

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["screening", "enrollment_date", "remarks"]
        widgets = {
            "screening": forms.Select(attrs={"class": "form-select"}),
            "enrollment_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")
        # prevent duplicate enrollment when creating
        if screening and hasattr(screening, "enrollment") and not self.instance.pk:
            raise ValidationError(f"This screening {screening} is already enrolled.")
        return cleaned_data
