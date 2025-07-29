# forms.py
from django import forms
from .models import VisitDay,Visit,AssignedCompetence

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['site', 'mentor', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class VisitDayForm(forms.ModelForm):
    class Meta:
        model = VisitDay
        fields = ['date']

    def __init__(self, *args, **kwargs):
        self.visit = kwargs.pop('visit', None)
        super().__init__(*args, **kwargs)

    def clean_date(self):
        date = self.cleaned_data['date']
        if VisitDay.objects.filter(visit=self.visit, date=date).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Another VisitDay already exists with this date.")
        return date
    

class MentorGradeForm(forms.ModelForm):
    class Meta:
        model = AssignedCompetence
        fields = ['mentor_grade', 'mentor_remarks']
        widgets = {
            'mentor_grade': forms.Select(choices=[
                ('', '---'),
                ('Excellent', 'Excellent'),
                ('Good', 'Good'),
                ('Fair', 'Fair'),
                ('Poor', 'Poor')
            ])
        }


class MenteeSelfAssessmentForm(forms.ModelForm):
    class Meta:
        model = AssignedCompetence
        fields = ['mentee_self_grade', 'remarks']
        widgets = {
            'mentee_self_grade': forms.Select(choices=[('', '---'), ('Excellent', 'Excellent'), ('Good', 'Good'), ('Fair', 'Fair'), ('Poor', 'Poor')])
        }
        
class AssignedCompetenceForm(forms.ModelForm):
    class Meta:
        model = AssignedCompetence
        fields = ['visit_day', 'mentee', 'disease', 'competence', 'remarks']
        # exclude = ['visit_day']  # Remove from editable fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional: limit competence choices by disease if you want (dynamic in the view or via JS)
        # self.fields['competence'].queryset = Competence.objects.none()

        # Optional: if visit_day is known, you can limit mentee choices to site mentees or exclude mentor
        # self.fields['mentee'].queryset = User.objects.exclude(pk=self.instance.visit_day.visit.mentor.pk)

