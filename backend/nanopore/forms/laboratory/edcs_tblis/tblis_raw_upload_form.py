from django import forms
from django.core.validators import FileExtensionValidator

class TblisRawUploadForm(forms.Form):
    file = forms.FileField(
        label="Select the raw TBLIS export (.xlsx, .xls or .csv) exactly as received from CTRL",
        validators=[FileExtensionValidator(allowed_extensions=['csv', 'xls', 'xlsx'])],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': '.csv,.xls,.xlsx'})
    )
