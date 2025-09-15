import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError

from nanopore.forms.diagnosis.diagnosis_upload_form import DiagnosisUploadForm
from nanopore.models.diagnosis import Diagnosis
from nanopore.models.screening import Screening
from options.models import (
    YesNo,
    TBDiagnosisMade,
    DiagnosisBacteriological,
    DiagnosedClinically,
    TBTreatmentStarted,
    RegimenPrescribed,
    TBTreatmentOutcome,
)


# --- helpers ---
def safe_int(val, required=False, field_name=None):
    """Convert to int if possible, else raise error if required."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid integer value for {field_name}: {val}")


def safe_decimal(val, required=False, field_name=None):
    """Convert to float if possible, else raise error if required."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid decimal value for {field_name}: {val}")


def parse_date_field(val, required=False, field_name=None):
    """Safely parse date string into YYYY-MM-DD, raise error if required."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required date for {field_name}")
        return None
    parsed = parse_date(str(val))
    if not parsed and required:
        raise ValidationError(f"Invalid date format for {field_name}: {val}")
    return parsed


def get_foreign(obj_class, val, required=False, field_name=None):
    """Safely get foreign key object by PK or by `value` field."""
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required foreign key for {field_name}")
        return None

    pk = safe_int(val)
    if hasattr(obj_class, "value"):
        obj = obj_class.objects.filter(value=pk).first()
    else:
        obj = obj_class.objects.filter(pk=pk).first()

    if required and not obj:
        raise ValidationError(f"Invalid foreign key for {field_name}: {val}")
    return obj


def split_m2m(obj_class, val, required=False, field_name=None):
    """Split comma-separated M2M values and return queryset list."""
    if not val or str(val).lower() in ["none", "nan", ""]:
        if required:
            raise ValidationError(f"Missing required M2M values for {field_name}")
        return []

    result = []
    for v in str(val).split(","):
        v = v.strip()
        if v:
            obj = get_foreign(obj_class, v, required=True, field_name=field_name)
            if obj:
                result.append(obj)
    return result


def to_bool(val):
    """Convert 1 / 1.0 / '1' → True, else False."""
    if val is None:
        return False
    try:
        return int(float(str(val).strip())) == 1
    except (ValueError, TypeError):
        return False

class DiagnosisCsvUploadView(View):
    template_name = "nanopore/diagnosis/diagnosis_upload_values.html"

    def get(self, request, *args, **kwargs):
        form = DiagnosisUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = DiagnosisUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        file = form.cleaned_data["file"]
        if not file.name.endswith(".csv"):
            messages.error(request, "Please upload a CSV file.")
            return render(request, self.template_name, {"form": form})

        data_set = file.read().decode("utf-8")
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)

        count_created = 0
        count_updated = 0
        row_errors = []

        for idx, row in enumerate(reader, start=2):
            pid = row.get("PID") or row.get("pid")
            if not pid:
                row_errors.append(f"Row {idx}: Missing PID")
                continue

            try:
                # --- Link to existing Screening ---
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValueError(f"No Screening found with PID={pid}")

                # --- Foreign Keys ---
                tb_diagnosis = get_foreign(YesNo, row.get("TbDiagnosis"))
                tb_diagnosis_date = parse_date_field(row.get("TbDiagnosisDate"))
                tb_diagnosis_made = get_foreign(TBDiagnosisMade, row.get("TbDiagnosisMade"))
                diagnosis_made_other = row.get("DiagnosisMadeOther") or None
                bacteriological_diagnosis = get_foreign(DiagnosisBacteriological, row.get("BacteriologicalDiagnosis"))
                tb_diagnosed_clinically = get_foreign(DiagnosedClinically, row.get("TbDiagnosedClinically"))
                tb_clinically_other = row.get("TbClinicallyOther") or None
                clinician_received_date = parse_date_field(row.get("ClinicianReceivedDate"))
                tb_treatment = get_foreign(TBTreatmentStarted, row.get("TbTreatment"))
                tb_treatment_date = parse_date_field(row.get("TbTreatmentDate"))
                tb_facility = row.get("TbFacility") or None
                tb_reason = row.get("TbReason") or None
                tb_register_number = row.get("TbRegisterNumber") or None
                tb_regimen = get_foreign(RegimenPrescribed, row.get("TbRegimen"))
                tb_regimen_other = row.get("TbRegimenOther") or None
                regimen_changed = get_foreign(YesNo, row.get("RegimenChanged"))
                tb_outcome2 = get_foreign(TBTreatmentOutcome, row.get("TbOutcome2"))
                tb_outcome2_date = row.get("TbOutcome2Date") or None
                remarks = row.get("Remarks") or None
                
                # # --- Boolean unknown fields ---
                # tx_unknown_month = to_bool(row.get("TxUnknownMonth"))

                # --- Create or update Diagnosis ---
                # --- Create or update Diagnosis ---
                diagnosis, created = Diagnosis.objects.update_or_create(
                    screening=screening,
                    defaults={
                        "tb_diagnosis": tb_diagnosis,
                        "tb_diagnosis_date": tb_diagnosis_date,
                        "tb_diagnosis_made": tb_diagnosis_made,
                        "diagnosis_made_other": diagnosis_made_other,
                        "bacteriological_diagnosis": bacteriological_diagnosis,
                        "tb_clinically_other": tb_clinically_other,
                        "clinician_received_date": clinician_received_date,
                        "tb_treatment": tb_treatment,
                        "tb_treatment_date": tb_treatment_date,
                        "tb_facility": tb_facility,
                        "tb_reason": tb_reason,
                        "tb_register_number": tb_register_number,
                        "tb_regimen": tb_regimen,
                        "tb_regimen_other": tb_regimen_other,
                        "regimen_changed": regimen_changed,
                        "tb_outcome2": tb_outcome2,
                        "tb_outcome2_date": tb_outcome2_date,
                        "remarks": remarks,
                    },
                )

                # --- Assign ManyToMany field separately ---
                if tb_diagnosed_clinically:
                    # If your CSV can have multiple IDs, split by comma and filter
                    if isinstance(tb_diagnosed_clinically, str):
                        ids = [safe_int(i) for i in tb_diagnosed_clinically.split(",") if safe_int(i) is not None]
                        objects = DiagnosedClinically.objects.filter(pk__in=ids)
                    else:
                        objects = [tb_diagnosed_clinically]

                    diagnosis.tb_diagnosed_clinically.set(objects)

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            except Exception as e:
                row_errors.append(f"Row {idx} (PID={pid}): {str(e)}")

        # --- Display results ---
        if row_errors:
            messages.error(
                request,
                "Some rows had errors. Please fix them and re-upload the CSV."
            )
            return render(
                request,
                self.template_name,
                {
                    "form": DiagnosisUploadForm(),
                    "row_errors": row_errors,
                    "count_created": count_created,
                    "count_updated": count_updated,
                },
            )

        if count_created or count_updated:
            messages.success(
                request,
                f"Imported {count_created} new and updated {count_updated} diagnosis."
            )
        return redirect("nanopore:forms-status-list")
