from django import forms

class ClinicLabUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")
