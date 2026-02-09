from django import forms
from .models import Site
from django.core.exceptions import ValidationError

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = [
            'name', 'pid_prefix', 'district', 'site_type', 'site_level',
            'target', 'substudy2Target', 'substudy4Target', 'description', 'value', 'is_active'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'is_active': forms.CheckboxInput(),
        }

    def clean(self):
        cleaned_data = super().clean()
        errors = {}

        # Required fields
        if not cleaned_data.get('name'):
            errors['name'] = "Site name is required."

        if not cleaned_data.get('district'):
            errors['district'] = "District is required."

        if cleaned_data.get('target') is None or cleaned_data['target'] < 0:
            errors['target'] = "Target must be 0 or greater."

        if cleaned_data.get('substudy2Target') is None or cleaned_data['substudy2Target'] < 0:
            errors['substudy2Target'] = "Substudy 2 target must be 0 or greater."

        if cleaned_data.get('substudy4Target') is None or cleaned_data['substudy4Target'] < 0:
            errors['substudy4Target'] = "Substudy 4 target must be 0 or greater."

        if errors:
            raise ValidationError(errors)

        return cleaned_data
