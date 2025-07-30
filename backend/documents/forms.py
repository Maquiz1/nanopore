from django import forms
from .models import UserManual

class UserManualCreateForm(forms.ModelForm):
    class Meta:
        model = UserManual
        fields = ['title', 'file']

    def clean_title(self):
        title = self.cleaned_data['title']
        if UserManual.objects.filter(title__iexact=title).exists():
            raise forms.ValidationError("A manual with this title already exists.")
        return title


class UserManualUpdateForm(forms.ModelForm):
    class Meta:
        model = UserManual
        fields = ['title', 'file']

    def __init__(self, *args, **kwargs):
        self.manual_id = kwargs.pop('manual_id', None)
        super().__init__(*args, **kwargs)

    def clean_title(self):
        title = self.cleaned_data['title']
        qs = UserManual.objects.filter(title__iexact=title)
        if self.manual_id:
            qs = qs.exclude(pk=self.manual_id)
        if qs.exists():
            raise forms.ValidationError("A manual with this title already exists.")
        return title
