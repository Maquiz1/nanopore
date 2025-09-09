from django import forms

class DiagnosisUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")
