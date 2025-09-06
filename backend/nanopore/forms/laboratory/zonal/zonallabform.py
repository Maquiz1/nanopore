from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import ZonalLaboratory

class ZonalLaboratoryForm(forms.ModelForm):
    class Meta:
        model = ZonalLaboratory
        fields = ["screening", "test_name", "result", "test_date", "remarks"]
        widgets = {
            "screening": forms.HiddenInput(),  # hidden field for POST
            "test_name": forms.TextInput(attrs={"class": "form-control"}),
            "result": forms.TextInput(attrs={"class": "form-control"}),
            "test_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        screening_instance = kwargs.pop("screening_instance", None)
        super().__init__(*args, **kwargs)
        if screening_instance:
            self.fields["screening"].initial = screening_instance.pk
        # Keep readonly display in template
        self.readonly_screening = screening_instance

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")
        if screening and self.instance.pk is None:
            if hasattr(screening, "zonal_laboratory"):
                raise ValidationError(f"This screening {screening} already has a zonal lab record.")
        return cleaned_data
