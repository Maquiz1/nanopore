from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import ClinicLaboratory
from common.labels.laboratory.clinic.clinic_labels import (
    CLINIC_LABELS,
)  # ✅ import from core app
from options.models import SampleReason

class ClinicLaboratoryForm(forms.ModelForm):
    class Meta:
        model = ClinicLaboratory
        fields = [
            # General info
            "screening",
            # 🔹 Sputum sample
            "sample_received",
            "sample_reason",
            "other_reason",
            "new_sample",
            "new_reason",
            "number_received",
            "date_sample1_collected",
            "date_sample1_received",
            "appearance_sample1",
            "sample1_volume",
            "date_sample2_collected",
            "date_sample2_received",
            "appearance_sample2",
            "sample2_volume",
            # 🔹 AFB Microscopy
            "afb_microscopy_conducted",
            "afb_a_date",
            "technique_a",
            "afb_a_results",
            "afb_b_date",
            "technique_b",
            "afb_b_results",
            # 🔹 Xpert MTB/RIF (Ultra)
            "xpert_mtb_rif_conducted",
            "xpert_date",
            "xpert_mtb",
            "error_code",
            "xpert_rif",
            "ct_value",
            "ct_na",
            "remarks",
        ]
        # fields = TB_LABELS.keys()
        labels = CLINIC_LABELS

        widgets = {
            # General info
            "screening": forms.Select(attrs={"class": "form-select", "disabled": True}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            # 🔹 Sputum sample
            "sample_received": forms.Select(attrs={"class": "form-select"}),
            "date_sample1_received": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "sample_reason": forms.Select(attrs={"class": "form-select"}),
            "other_reason": forms.TextInput(attrs={"class": "form-control"}),
            "new_sample": forms.Select(attrs={"class": "form-select"}),
            "new_reason": forms.TextInput(attrs={"class": "form-control"}),
            "number_received": forms.Select(attrs={"class": "form-select"}),
            "date_sample1_collected": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "date_sample2_collected": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "date_sample1_received": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "date_sample2_received": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "appearance_sample1": forms.Select(attrs={"class": "form-select"}),
            "sample1_volume": forms.TextInput(attrs={"class": "form-control"}),
            "appearance_sample2": forms.Select(attrs={"class": "form-select"}),
            "sample2_volume": forms.TextInput(attrs={"class": "form-control"}),
            # 🔹 AFB Microscopy
            "afb_microscopy_conducted": forms.Select(attrs={"class": "form-select"}),
            "afb_a_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "technique_a": forms.Select(attrs={"class": "form-select"}),
            "afb_a_results": forms.Select(attrs={"class": "form-select"}),
            "afb_b_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "technique_b": forms.Select(attrs={"class": "form-select"}),
            "afb_b_results": forms.Select(attrs={"class": "form-select"}),
            # 🔹 Xpert MTB/RIF (Ultra)
            "xpert_mtb_rif_conducted": forms.Select(attrs={"class": "form-select"}),
            "xpert_date": forms.DateInput(
                attrs={"type": "date", "class": "form-control"}
            ),
            "xpert_mtb": forms.Select(attrs={"class": "form-select"}),
            "error_code": forms.NumberInput(attrs={"class": "form-control"}),
            "xpert_rif": forms.Select(attrs={"class": "form-select"}),
            "ct_value": forms.NumberInput(
                attrs={"class": "form-control", "step": "0.1"}
            ),
            # "ct_na": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["screening"].disabled = True

        # ✅ order display by clinical code
        self.fields["sample_reason"].queryset = (
            SampleReason.objects.order_by("value")
        )

        # ✅ Make required fields
        self.fields["date_sample1_collected"].required = True
        self.fields["appearance_sample1"].required = True
        self.fields["sample1_volume"].required = True

    def validate_sample(self, sample_no, date_collected, appearance, volume):

        if not date_collected:
            raise ValidationError(f"Date of Sample {sample_no} collection is required.")

        if not appearance:
            raise ValidationError(f"Appearance of Sample {sample_no} is required.")

        if not volume:
            raise ValidationError(f"Sample {sample_no} volume is required.")

        try:
            vol = float(volume)   # accepts int / decimal / float
            if vol <= 0:
                raise ValidationError(f"Sample {sample_no} volume must be greater than zero.")
        except (TypeError, ValueError):
            raise ValidationError(f"Sample {sample_no} volume must be numeric.")


    def clean(self):
        cleaned_data = super().clean()

        sample_received = cleaned_data.get("sample_received")

        date_sample1_collected = cleaned_data.get("date_sample1_collected")
        appearance_sample1 = cleaned_data.get("appearance_sample1")
        sample1_volume = cleaned_data.get("sample1_volume")

        date_sample2_collected = cleaned_data.get("date_sample2_collected")
        appearance_sample2 = cleaned_data.get("appearance_sample2")
        sample2_volume = cleaned_data.get("sample2_volume")

        # ─────────────────────────────
        # SAMPLE VALIDATION
        # ─────────────────────────────

        if sample_received == 1:

            self.validate_sample(
                1,
                date_sample1_collected,
                appearance_sample1,
                sample1_volume,
            )

        if sample_received == 2:

            self.validate_sample(
                1,
                date_sample1_collected,
                appearance_sample1,
                sample1_volume,
            )

            self.validate_sample(
                2,
                date_sample2_collected,
                appearance_sample2,
                sample2_volume,
            )

        # ─────────────────────────────
        # Prevent duplicate lab record
        # ─────────────────────────────

        screening = cleaned_data.get("screening")
        if screening:
            qs = ClinicLaboratory.objects.filter(screening=screening)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError(
                    f"This screening {screening} already has a laboratory record."
                )

        return cleaned_data
