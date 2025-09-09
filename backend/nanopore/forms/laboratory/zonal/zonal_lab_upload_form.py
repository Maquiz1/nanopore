from django import forms

class ZonalLabUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")
