from django import forms
from django.core.validators import FileExtensionValidator

class TblisRawUploadForm(forms.Form):
    file = forms.FileField(
        label="Select Raw TBLIS CSV file to upload",
        validators=[FileExtensionValidator(allowed_extensions=['csv'])],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv'})
    )
