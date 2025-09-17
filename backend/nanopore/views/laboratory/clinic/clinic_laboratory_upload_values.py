import csv
import io
from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError

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
)


# --- helpers ---
# def normalize_headers(reader):
#     """Normalize headers: strip spaces, lowercase for consistency."""
#     reader.fieldnames = [fn.strip().lower() for fn in reader.fieldnames]
#     return reader

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
    """
    Safely get foreign key object by its `value` field only (not pk).
    Always shows the field name in errors.
    """
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None

    # normalize "2.0" → "2"
    val_str = str(val).strip()
    if val_str.replace(".", "", 1).isdigit():
        if "." in val_str:
            val_str = str(int(float(val_str)))  # convert 2.0 -> 2

    try:
        obj = obj_class.objects.filter(value=val_str).first()
    except Exception as e:
        raise ValidationError(f"Error while looking up {field_name}={val_str}: {str(e)}")

    if required and not obj:
        raise ValidationError(f"Invalid value for {field_name}: {val_str}")

    return obj




def split_m2m(obj_class, val, required=False, field_name=None):
    """
    Split comma-separated values and fetch objects by their `value` field.
    Normalizes numbers like '2.0' → '2'.
    Always includes field_name in error messages.
    """
    if not val or str(val).lower() in ["none", "nan", ""]:
        if required:
            raise ValidationError(f"Missing required M2M values for {field_name}")
        return []

    result = []
    for raw in str(val).split(","):
        v = raw.strip()
        if not v:
            continue

        # normalize "2.0" → "2"
        if v.replace(".", "", 1).isdigit():
            if "." in v:
                v = str(int(float(v)))

        try:
            obj = obj_class.objects.filter(value=v).first()
        except Exception as e:
            raise ValidationError(f"Error while looking up {field_name}={v}: {str(e)}")

        if not obj:
            raise ValidationError(f"Invalid value for {field_name}: {v}")

        result.append(obj)

    return result


def to_bool(val):
    """Convert 1 / 1.0 / '1' / 'on' → True, else False."""
    if val is None:
        return False

    if isinstance(val, str) and val.strip().lower() == "on":
        return True

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

                # --- Foreign Keys with defaults for NOT NULL ---
                sample_received = get_foreign(YesNo, row.get("SampleReceived"),required=True,field_name="SampleReceived")
                new_sample = get_foreign(YesNo, row.get("NewSample"))
                afb_microscopy_conducted = get_foreign(YesNo, row.get("AFBMicroscopyConducted"),required=True,field_name="AFBMicroscopyConducted")
                xpert_mtb_rif_conducted = get_foreign(YesNo, row.get("XpertMTBRifConducted"),required=True,field_name="XpertMTBRifConducted")

                sample_reason = get_foreign(SampleReason, row.get("SampleReason"))
                number_received = get_foreign(SampleNumber, row.get("NumberReceived"),required=True,field_name="NumberReceived")
                appearance_sample1 = get_foreign(SampleAppearance, row.get("AppearanceSample1"),required=True,field_name="AppearanceSample1")
                appearance_sample2 = get_foreign(SampleAppearance, row.get("AppearanceSample2"))
                technique_a = get_foreign(AFBTechnique, row.get("TechniqueA"))
                technique_b = get_foreign(AFBTechnique, row.get("TechniqueB"))
                afb_a_results = get_foreign(AFBMicroscopyResult, row.get("AFBA_Results"))
                afb_b_results = get_foreign(AFBMicroscopyResult, row.get("AFBB_Results"))
                xpert_mtb = get_foreign(XpertMTB, row.get("XpertMTB"))
                xpert_rif = get_foreign(XpertRIF, row.get("XpertRIF"))

                # --- Other fields ---
                other_reason = row.get("OtherReason") or None
                new_reason = row.get("NewReason") or None
                date_sample1_collected = parse_date_field(row.get("DateSample1Collected"),required=True,field_name="DateSample1Collected")
                date_sample1_received = parse_date_field(row.get("DateSample1Received"),required=True,field_name="DateSample1Received")
                sample1_volume = row.get("Sample1Volume") or None
                date_sample2_collected = parse_date_field(row.get("DateSample2Collected"))
                date_sample2_received = parse_date_field(row.get("DateSample2Received"))
                sample2_volume = row.get("Sample2Volume") or None
                afb_a_date = parse_date_field(row.get("AFBA_Date"))
                afb_b_date = parse_date_field(row.get("AFBB_Date"))
                xpert_date = parse_date_field(row.get("XpertDate"))
                error_code = safe_int(row.get("ErrorCode"))
                ct_value = safe_decimal(row.get("CTValue"))
                ct_na = to_bool(row.get("CTNA"))
                remarks = row.get("Remarks") or None

                # --- Create or update record ---
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
            messages.error(request, "Some rows had errors. Please fix them and re-upload the CSV.")
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
