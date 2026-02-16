from django import forms
from nanopore.models import Enrollment
from django.core.exceptions import ValidationError
import datetime
from common.labels.enrollment.labels import Enrollment_LABELS   # ✅ import from core app
from options.models import DiseasesMedicalConditions,YesNoUnknown,PositiveNegativeUnknown,CategoryTreated

class EnrollmentForm(forms.ModelForm):
        
    class Meta:
        model = Enrollment
        fields = [
            "screening",
            "enrollment_date",
            "remarks",
            # Symptoms / initial assessment
            "cough2weeks",
            "poor_weight",
            "coughing_blood",
            "unexplained_fever",
            "night_sweats",
            "neck_lymph",
            "history_tb",
            "date_information_collected",
            # History / previous treatment
            "tx_previous",
            "tb_category",
            "tb_category_specify",
            "tx_month",
            "tx_unknown_month",
            "tx_year",
            "tx_unknown_year",
            "dr_ds",
            "ltf_months",
            "ltf_months_unknown",
            "tb_regimen",
            "tb_regimen_specify",
            "regimen_months",
            "regimen_months_unknown",
            "tb_otcome",
            # Health conditions
            "hiv_status",
            "other_diseases",
            "diseases_medical",
            "diseases_specify",
            # Samples
            "sputum_collected",
            "sputum_date",
            "sputum_reasons",
        ]
        # fields = TB_LABELS.keys()
        labels = Enrollment_LABELS

        widgets = {
            "screening": forms.Select(attrs={"class": "form-select"}),
            "enrollment_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "cough2weeks": forms.Select(attrs={"class": "form-select"}),
            "poor_weight": forms.Select(attrs={"class": "form-select"}),
            "coughing_blood": forms.Select(attrs={"class": "form-select"}),
            "unexplained_fever": forms.Select(attrs={"class": "form-select"}),
            "night_sweats": forms.Select(attrs={"class": "form-select"}),
            "neck_lymph": forms.Select(attrs={"class": "form-select"}),
            "history_tb": forms.Select(attrs={"class": "form-select"}),
            "date_information_collected": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            "tx_previous": forms.Select(attrs={"class": "form-select"}),
            "tb_category": forms.Select(attrs={"class": "form-select"}),
            "tb_category_specify": forms.TextInput(attrs={"class": "form-control"}),
            "tx_month": forms.NumberInput(attrs={"class": "form-control"}),
            # "tx_unknown_month": forms.CheckboxSelectMultiple(),
            # "tx_unknown_month": forms.BooleanField(attrs={"class": "form-control","required":False,"label":"Consent given?"}),
            "tx_year": forms.NumberInput(attrs={"class": "form-control"}),
            # "tx_unknown_year": forms.CheckboxSelectMultiple(),
            "dr_ds": forms.Select(attrs={"class": "form-select"}),
            "ltf_months": forms.NumberInput(attrs={"class": "form-control"}),
            # "ltf_months_unknown": forms.CheckboxSelectMultiple(),
            "tb_regimen": forms.Select(attrs={"class": "form-select"}),
            "tb_regimen_specify": forms.TextInput(attrs={"class": "form-control"}),
            "regimen_months": forms.NumberInput(attrs={"class": "form-control"}),
            # "regimen_months_unknown": forms.CheckboxSelectMultiple(),
            "tb_otcome": forms.Select(attrs={"class": "form-select"}),

            "hiv_status": forms.Select(attrs={"class": "form-select"}),
            "other_diseases": forms.Select(attrs={"class": "form-select"}),
            "diseases_medical": forms.CheckboxSelectMultiple(),
            "diseases_specify": forms.TextInput(attrs={"class": "form-control"}),

            "sputum_collected": forms.Select(attrs={"class": "form-select"}),
            "sputum_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "sputum_reasons": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        self.screening_instance = kwargs.pop("screening_instance", None)
        super().__init__(*args, **kwargs)

        if self.screening_instance:
            self.fields["screening"].disabled = True
            self.fields["screening"].initial = self.screening_instance

        # OPTIONAL — ordering only
        self.fields["tb_category"].queryset = CategoryTreated.objects.all().order_by("value")
        self.fields["hiv_status"].queryset = PositiveNegativeUnknown.objects.all().order_by("value")
        self.fields["tx_previous"].queryset = YesNoUnknown.objects.all().order_by("value")

        self.fields["other_diseases"].queryset = YesNoUnknown.objects.all().order_by("value")
        self.fields["diseases_medical"].queryset = DiseasesMedicalConditions.objects.all().order_by("value")

    def clean_screening(self):
        if self.instance.pk:
            return self.instance.screening
        if self.screening_instance:
            return self.screening_instance
        raise ValidationError("Screening / PID is required")

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")
        enrollment_date = cleaned_data.get("enrollment_date")
        date_info = cleaned_data.get("date_information_collected")
        sputum_date = cleaned_data.get("sputum_date")
        today = datetime.date.today()

        # Normalize dates
        for field in ["enrollment_date", "date_information_collected", "sputum_date"]:
            value = cleaned_data.get(field)
            if value is None:
                continue
            elif isinstance(value, datetime.datetime):
                cleaned_data[field] = value.date()
            elif isinstance(value, str):
                try:
                    cleaned_data[field] = datetime.date.fromisoformat(value)
                except ValueError:
                    self.add_error(field, f"Invalid date format for {field}")

        # Validate enrollment_date
        enrollment_date = cleaned_data.get("enrollment_date")
        if enrollment_date:
            if enrollment_date > today:
                self.add_error("enrollment_date", "Enrollment date cannot be in the future.")
            if screening and enrollment_date < screening.screening_date:
                self.add_error("enrollment_date", "Enrollment date cannot be before the screening date.")

        # Validate date_information_collected
        date_info = cleaned_data.get("date_information_collected")
        if date_info:
            if date_info > today:
                self.add_error("date_information_collected", "Date of information collection cannot be in the future.")
            # if enrollment_date and date_info < enrollment_date:
            #     self.add_error("date_information_collected", "Date of information collection cannot be before enrollment date.")

        # Validate sputum_date
        if sputum_date:
            if sputum_date > today:
                self.add_error("sputum_date", "Sputum collection date cannot be in the future.")
            # if enrollment_date and sputum_date < enrollment_date:
            #     self.add_error("sputum_date", "Sputum collection date cannot be before enrollment date.")

        # Prevent duplicate enrollment
        if screening and hasattr(screening, "enrollment") and not self.instance.pk:
            raise ValidationError(f"This screening {screening} is already enrolled.")

        return cleaned_data
