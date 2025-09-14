from django import forms

class RegimenChangesUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")
