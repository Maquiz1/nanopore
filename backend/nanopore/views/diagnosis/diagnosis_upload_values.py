import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date

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


def safe_int(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def get_foreign(obj_class, val):
    """Safely get foreign key object by ID, return None if missing/invalid."""
    pk = safe_int(val)
    if pk is None:
        return None
    return obj_class.objects.filter(pk=pk).first()


def safe_date(val):
    """Parse CSV date safely into Python date."""
    if not val or str(val).strip() == "":
        return None
    try:
        return parse_date(val)
    except Exception:
        return None
    
def to_bool(val):
    """Convert '1' → True, empty/None → False."""
    return str(val).strip() == "1" if val is not None else False


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
                tb_diagnosis_date = safe_date(row.get("TbDiagnosisDate"))
                tb_diagnosis_made = get_foreign(TBDiagnosisMade, row.get("TbDiagnosisMade"))
                diagnosis_made_other = row.get("DiagnosisMadeOther") or None
                bacteriological_diagnosis = get_foreign(DiagnosisBacteriological, row.get("BacteriologicalDiagnosis"))
                tb_diagnosed_clinically = get_foreign(DiagnosedClinically, row.get("TbDiagnosedClinically"))
                tb_clinically_other = row.get("TbClinicallyOther") or None
                clinician_received_date = safe_date(row.get("ClinicianReceivedDate"))
                tb_treatment = get_foreign(TBTreatmentStarted, row.get("TbTreatment"))
                tb_treatment_date = safe_date(row.get("TbTreatmentDate"))
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
                diagnosis, created = Diagnosis.objects.update_or_create(
                    screening=screening,
                    defaults={
                        "tb_diagnosis": tb_diagnosis,
                        "tb_diagnosis_date": tb_diagnosis_date,
                        "tb_diagnosis_made": tb_diagnosis_made,
                        "diagnosis_made_other": diagnosis_made_other,
                        "bacteriological_diagnosis": bacteriological_diagnosis,
                        "tb_diagnosed_clinically": tb_diagnosed_clinically,
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
