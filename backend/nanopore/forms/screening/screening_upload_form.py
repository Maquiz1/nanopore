from django import forms

class ScreeningUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")
