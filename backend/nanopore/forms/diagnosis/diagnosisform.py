from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import Diagnosis, Screening

class DiagnosisForm(forms.ModelForm):
    class Meta:
        model = Diagnosis
        fields = ["screening", "diagnosis_name", "diagnosis_date", "remarks"]
        widgets = {
            "screening": forms.HiddenInput(),  # hidden input, won't be editable
            "diagnosis_name": forms.TextInput(attrs={"class": "form-control"}),
            "diagnosis_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
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
