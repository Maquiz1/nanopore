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
                # --- Link to existing Screening ---
                screening = Screening.objects.filter(pid=pid).first()
                if not screening:
                    raise ValueError(f"No Screening found with PID={pid}")

                # --- Foreign Keys and fields ---
                sample_received = get_foreign(YesNo, row.get("SampleReceived"))
                sample_reason = get_foreign(SampleReason, row.get("SampleReason"))
                other_reason = row.get("OtherReason") or None
                new_sample = get_foreign(YesNo, row.get("NewSample"))
                new_reason = row.get("NewReason") or None
                number_received = get_foreign(SampleNumber, row.get("NumberReceived"))

                date_sample1_collected = parse_date(row.get("DateSample1Collected"))
                date_sample1_received = parse_date(row.get("DateSample1Received"))
                appearance_sample1 = get_foreign(SampleAppearance, row.get("AppearanceSample1"))
                sample1_volume = row.get("Sample1Volume") or None

                date_sample2_collected = parse_date(row.get("DateSample2Collected"))
                date_sample2_received = parse_date(row.get("DateSample2Received"))
                appearance_sample2 = get_foreign(SampleAppearance, row.get("AppearanceSample2"))
                sample2_volume = row.get("Sample2Volume") or None

                afb_microscopy_conducted = get_foreign(YesNo, row.get("AFBMicroscopyConducted"))
                afb_a_date = parse_date(row.get("AFBA_Date"))
                technique_a = get_foreign(AFBTechnique, row.get("TechniqueA"))
                afb_a_results = get_foreign(AFBMicroscopyResult, row.get("AFBA_Results"))

                afb_b_date = parse_date(row.get("AFBB_Date"))
                technique_b = get_foreign(AFBTechnique, row.get("TechniqueB"))
                afb_b_results = get_foreign(AFBMicroscopyResult, row.get("AFBB_Results"))

                xpert_mtb_rif_conducted = get_foreign(YesNo, row.get("XpertMTBRIFConducted"))
                xpert_date = parse_date(row.get("XpertDate"))
                xpert_mtb = get_foreign(XpertMTB, row.get("XpertMTB"))
                error_code = safe_int(row.get("ErrorCode"))
                xpert_rif = get_foreign(XpertRIF, row.get("XpertRIF"))
                ct_value = safe_decimal(row.get("CTValue"))
                ct_na = get_foreign(NoSPCResult, row.get("CTNA"))

                test_name = row.get("TestName") or "Clinic Lab Test"
                result = row.get("Result") or None
                test_date = parse_date(row.get("TestDate"))
                remarks = row.get("Remarks") or None

                if not test_date:
                    raise ValueError("TestDate is required.")

                # --- Create or update ClinicLaboratory ---
                lab, created = ClinicLaboratory.objects.update_or_create(
                    screening=screening,
                    defaults={
                        # "test_name": test_name,
                        # "result": result,
                        # "test_date": test_date,
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
        return redirect("nanopore:clinic-lab-list")
