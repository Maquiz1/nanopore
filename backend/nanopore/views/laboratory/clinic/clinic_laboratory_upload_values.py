import csv
import io
from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date

from nanopore.forms.laboratory.clinic.clinic_lab_upload_form import ClinicLabUploadForm
from nanopore.models.clinic_lab import ClinicLaboratory
from nanopore.models.screening import Screening
from options.models import (
    YesNo,
    SampleReason,
    SampleNumber,
    SampleAppearance,
    AFBTechnique,
    AFBMicroscopyResult,
    XpertMTB,
    XpertRIF,
    NoSPCResult,
)


def safe_int(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def safe_decimal(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def get_foreign(obj_class, val):
    """Safely get foreign key object by ID, return None if missing/invalid."""
    pk = safe_int(val)
    if pk is None:
        return None
    return obj_class.objects.filter(pk=pk).first()


# def to_bool(val):
#     """Convert '1' → True, empty/None → False."""
#     return str(val).strip() == "1" if val is not None else False


def to_bool(val):
    """Convert 1 / 1.0 / '1' → True, else False."""
    if val is None:
        return False
    try:
        return int(float(str(val).strip())) == 1
    except (ValueError, TypeError):
        return False


class ClinicLabCsvUploadView(View):
    template_name = "nanopore/laboratory/clinic/clinic_laboratory_upload.html"

    def get(self, request, *args, **kwargs):
        form = ClinicLabUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = ClinicLabUploadForm(request.POST, request.FILES)
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
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValueError(f"No Screening found with PID={pid}")

                # --- Convert all foreign key CSV values to int first ---
                fks = {
                    "sample_received": safe_int(row.get("SampleReceived")),
                    "sample_reason": safe_int(row.get("SampleReason")),
                    "new_sample": safe_int(row.get("NewSample")),
                    "number_received": safe_int(row.get("NumberReceived")),
                    "appearance_sample1": safe_int(row.get("AppearanceSample1")),
                    "appearance_sample2": safe_int(row.get("AppearanceSample2")),
                    "technique_a": safe_int(row.get("TechniqueA")),
                    "technique_b": safe_int(row.get("TechniqueB")),
                    "afb_a_results": safe_int(row.get("AFBA_Results")),
                    "afb_b_results": safe_int(row.get("AFBB_Results")),
                    "afb_microscopy_conducted": safe_int(row.get("AFBMicroscopyConducted")),
                    "xpert_mtb_rif_conducted": safe_int(row.get("XpertMTBRIFConducted")),
                    "xpert_mtb": safe_int(row.get("XpertMTB")),
                    "xpert_rif": safe_int(row.get("XpertRIF")),
                }

                # --- Get FK objects ---
                sample_received = get_foreign(YesNo, fks["sample_received"])
                sample_reason = get_foreign(SampleReason, fks["sample_reason"])
                new_sample = get_foreign(YesNo, fks["new_sample"])
                number_received = get_foreign(SampleNumber, fks["number_received"])
                appearance_sample1 = get_foreign(SampleAppearance, fks["appearance_sample1"])
                appearance_sample2 = get_foreign(SampleAppearance, fks["appearance_sample2"])
                technique_a = get_foreign(AFBTechnique, fks["technique_a"])
                technique_b = get_foreign(AFBTechnique, fks["technique_b"])
                afb_a_results = get_foreign(AFBMicroscopyResult, fks["afb_a_results"])
                afb_b_results = get_foreign(AFBMicroscopyResult, fks["afb_b_results"])
                afb_microscopy_conducted = get_foreign(YesNo, fks["afb_microscopy_conducted"])
                xpert_mtb_rif_conducted = get_foreign(YesNo, fks["xpert_mtb_rif_conducted"])
                xpert_mtb = get_foreign(XpertMTB, fks["xpert_mtb"])
                xpert_rif = get_foreign(XpertRIF, fks["xpert_rif"])

                # --- Other fields ---
                other_reason = row.get("OtherReason") or None
                new_reason = row.get("NewReason") or None
                date_sample1_collected = parse_date(row.get("DateSample1Collected"))
                date_sample1_received = parse_date(row.get("DateSample1Received"))
                sample1_volume = row.get("Sample1Volume") or None
                date_sample2_collected = parse_date(row.get("DateSample2Collected"))
                date_sample2_received = parse_date(row.get("DateSample2Received"))
                sample2_volume = row.get("Sample2Volume") or None
                afb_a_date = parse_date(row.get("AFBA_Date"))
                afb_b_date = parse_date(row.get("AFBB_Date"))
                xpert_date = parse_date(row.get("XpertDate"))
                error_code = safe_int(row.get("ErrorCode"))
                ct_value = safe_decimal(row.get("CTValue"))
                ct_na = to_bool(row.get("CTNA"))
                remarks = row.get("Remarks") or None

                # --- Create or update ---
                lab, created = ClinicLaboratory.objects.update_or_create(
                    screening=screening,
                    defaults={
                        "sample_received": sample_received,
                        "sample_reason": sample_reason,
                        "other_reason": other_reason,
                        "new_sample": new_sample,
                        "new_reason": new_reason,
                        "number_received": number_received,
                        "date_sample1_collected": date_sample1_collected,
                        "date_sample1_received": date_sample1_received,
                        "appearance_sample1": appearance_sample1,
                        "sample1_volume": sample1_volume,
                        "date_sample2_collected": date_sample2_collected,
                        "date_sample2_received": date_sample2_received,
                        "appearance_sample2": appearance_sample2,
                        "sample2_volume": sample2_volume,
                        "afb_microscopy_conducted": afb_microscopy_conducted,
                        "afb_a_date": afb_a_date,
                        "technique_a": technique_a,
                        "afb_a_results": afb_a_results,
                        "afb_b_date": afb_b_date,
                        "technique_b": technique_b,
                        "afb_b_results": afb_b_results,
                        "xpert_mtb_rif_conducted": xpert_mtb_rif_conducted,
                        "xpert_date": xpert_date,
                        "xpert_mtb": xpert_mtb,
                        "error_code": error_code,
                        "xpert_rif": xpert_rif,
                        "ct_value": ct_value,
                        "ct_na": ct_na,
                        "remarks": remarks,
                    },
                )

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            except Exception as e:
                row_errors.append(f"Row {idx} (PID={pid}): {str(e)}")

        if row_errors:
            messages.error(
                request,
                "Some rows had errors. Please fix them and re-upload the CSV."
            )
            return render(
                request,
                self.template_name,
                {
                    "form": ClinicLabUploadForm(),
                    "row_errors": row_errors,
                    "count_created": count_created,
                    "count_updated": count_updated,
                },
            )

        if count_created or count_updated:
            messages.success(
                request,
                f"Imported {count_created} new and updated {count_updated} clinic lab records."
            )
        return redirect("nanopore:form-status-list")
