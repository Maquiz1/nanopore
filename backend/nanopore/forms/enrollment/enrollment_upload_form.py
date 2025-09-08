from django import forms

class EnrollmentUploadForm(forms.Form):
    file = forms.FileField(label="Upload CSV File")
