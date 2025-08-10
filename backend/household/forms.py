from django import forms
from .models import Household

class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ['household_head_name', 'number_of_men', 'number_of_women', 'household_head_phone_number']
