# forms.py
from django import forms
from .models import VisitDay,Visit,AssignedCompetence

class VisitForm(forms.ModelForm):
    class Meta:
        model = Visit
        fields = ['site', 'mentor', 'start_date', 'end_date']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-select'}),
            'mentor': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
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
        fields = ['mentee_grade', 'mentee_remarks']
        widgets = {
            'mentee_grade': forms.Select(choices=[('', '---'), ('Excellent', 'Excellent'), ('Good', 'Good'), ('Fair', 'Fair'), ('Poor', 'Poor')])
        }
        
class AssignedCompetenceForm(forms.ModelForm):
    class Meta:
        model = AssignedCompetence
        fields = ['visit_day', 'mentee', 'disease', 'competence', 'mentor_remarks']
        widgets = {
            'visit_day': forms.Select(attrs={'class': 'form-select'}),
            'mentee': forms.Select(attrs={'class': 'form-select'}),
            'disease': forms.Select(attrs={'class': 'form-select'}),
            'competence': forms.Select(attrs={'class': 'form-select'}),
            'mentor_remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Optional dynamic queryset filtering can stay here
        # self.fields['competence'].queryset = Competence.objects.none()
        # self.fields['mentee'].queryset = User.objects.exclude(pk=self.instance.visit_day.visit.mentor.pk)
