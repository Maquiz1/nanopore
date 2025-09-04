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

    def __init__(self, *args, **kwargs):
        # optional: pass `screening_instance` to prefill
        self.screening_instance = kwargs.pop("screening_instance", None)
        super().__init__(*args, **kwargs)
        if self.screening_instance:
            # Disable field and set initial value
            self.fields["screening"].disabled = True
            self.fields["screening"].initial = self.screening_instance

    def clean_screening(self):
        """
        Skip validation for disabled screening field,
        always use `self.screening_instance` if creating.
        """
        if self.instance.pk:  # updating existing enrollment
            return self.instance.screening
        if self.screening_instance:
            return self.screening_instance
        raise ValidationError("Screening / PID is required")

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")

        # prevent duplicate enrollment on create
        if screening and hasattr(screening, "enrollment") and not self.instance.pk:
            raise ValidationError(f"This screening {screening} is already enrolled.")
        return cleaned_data
