from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import ClinicLaboratory
from common.labels.laboratory.clinic.clinic_labels import CLINIC_LABELS
from options.models import SampleReason


class ClinicLaboratoryForm(forms.ModelForm):

    reason_for_change = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3
        }),
        label="Reason for Change"
    )

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

            "reason_for_change",
        ]

        labels = CLINIC_LABELS

        widgets = {
            "screening": forms.Select(attrs={"class": "form-select"}),
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "sample_received": forms.Select(attrs={"class": "form-select"}),
            "sample_reason": forms.Select(attrs={"class": "form-select"}),
            "other_reason": forms.TextInput(attrs={"class": "form-control"}),
            "new_sample": forms.Select(attrs={"class": "form-select"}),
            "new_reason": forms.TextInput(attrs={"class": "form-control"}),
            "number_received": forms.Select(attrs={"class": "form-select"}),

            "date_sample1_collected": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_sample1_received": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_sample2_collected": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "date_sample2_received": forms.DateInput(attrs={"type": "date", "class": "form-control"}),

            "appearance_sample1": forms.Select(attrs={"class": "form-select"}),
            "sample1_volume": forms.TextInput(attrs={"class": "form-control"}),
            "appearance_sample2": forms.Select(attrs={"class": "form-select"}),
            "sample2_volume": forms.TextInput(attrs={"class": "form-control"}),

            "afb_microscopy_conducted": forms.Select(attrs={"class": "form-select"}),
            "afb_a_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "technique_a": forms.Select(attrs={"class": "form-select"}),
            "afb_a_results": forms.Select(attrs={"class": "form-select"}),
            "afb_b_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "technique_b": forms.Select(attrs={"class": "form-select"}),
            "afb_b_results": forms.Select(attrs={"class": "form-select"}),

            "xpert_mtb_rif_conducted": forms.Select(attrs={"class": "form-select"}),
            "xpert_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "xpert_mtb": forms.Select(attrs={"class": "form-select"}),
            "error_code": forms.NumberInput(attrs={"class": "form-control"}),
            "xpert_rif": forms.Select(attrs={"class": "form-select"}),
            "ct_value": forms.NumberInput(attrs={"class": "form-control", "step": "0.1"}),
        }

    # ─────────────────────────────
    # INIT
    # ─────────────────────────────
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["screening"].disabled = True

        # Order sample reasons
        self.fields["sample_reason"].queryset = SampleReason.objects.order_by("value")

        # Required fields
        self.fields["date_sample1_collected"].required = True
        self.fields["appearance_sample1"].required = True
        self.fields["sample1_volume"].required = True

        # 🔒 If locked → disable all fields visually
        if self.instance.pk and getattr(self.instance, "is_locked", False):
            for field in self.fields:
                self.fields[field].disabled = True

        # 🟡 If reviewed → show reason hint
        if self.instance.pk and getattr(self.instance, "is_reviewed", False):
            self.fields["reason_for_change"].widget.attrs["placeholder"] = (
                "This record has been reviewed. Provide reason for change."
            )

    # ─────────────────────────────
    # SAMPLE VALIDATION
    # ─────────────────────────────
    def validate_sample(self, sample_no, date_collected, appearance, volume):

        if not date_collected:
            raise ValidationError(f"Date of Sample {sample_no} collection is required.")

        if not appearance:
            raise ValidationError(f"Appearance of Sample {sample_no} is required.")

        if not volume:
            raise ValidationError(f"Sample {sample_no} volume is required.")

        try:
            vol = float(volume)
            if vol <= 0:
                raise ValidationError(
                    f"Sample {sample_no} volume must be greater than zero."
                )
        except (TypeError, ValueError):
            raise ValidationError(
                f"Sample {sample_no} volume must be numeric."
            )

    # ─────────────────────────────
    # CLEAN
    # ─────────────────────────────
    def clean(self):
        cleaned_data = super().clean()

        # 🔒 HARD BLOCK IF LOCKED
        if self.instance.pk and getattr(self.instance, "is_locked", False):
            raise ValidationError(
                "This record is locked and cannot be modified. "
                "Please unlock the record before editing."
            )

        sample_received = cleaned_data.get("sample_received")

        if sample_received == 1:
            self.validate_sample(
                1,
                cleaned_data.get("date_sample1_collected"),
                cleaned_data.get("appearance_sample1"),
                cleaned_data.get("sample1_volume"),
            )

        if sample_received == 2:
            self.validate_sample(
                1,
                cleaned_data.get("date_sample1_collected"),
                cleaned_data.get("appearance_sample1"),
                cleaned_data.get("sample1_volume"),
            )
            self.validate_sample(
                2,
                cleaned_data.get("date_sample2_collected"),
                cleaned_data.get("appearance_sample2"),
                cleaned_data.get("sample2_volume"),
            )

        # Prevent duplicate lab record
        screening = cleaned_data.get("screening")
        if screening:
            qs = ClinicLaboratory.objects.filter(screening=screening)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise ValidationError(
                    f"This screening {screening} already has a laboratory record."
                )

        # 🟡 REQUIRE REASON IF REVIEWED AND DATA CHANGED
        if self.instance.pk and getattr(self.instance, "is_reviewed", False):

            changed_fields = [
                field for field in self.changed_data
                if field != "reason_for_change"
            ]

            if changed_fields:
                reason = cleaned_data.get("reason_for_change")
                if not reason:
                    raise ValidationError(
                        "This record has been reviewed. Reason for Change is required."
                    )

        return cleaned_data