from django import forms

class EdcsTBLISLabUploadForm(forms.Form):
    file = forms.FileField(label="Upload Zona-Tblis CSV File")
