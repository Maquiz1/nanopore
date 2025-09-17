import csv
import io
from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError

from nanopore.forms.enrollment.enrollment_upload_form import EnrollmentUploadForm
from nanopore.models.enrollment import Enrollment
from nanopore.models.screening import Screening
from locations.models import Site
from options.models import (
    YesNo, YesNoUnknown, CategoryTreated,
    DrDsTB, TreatmentRegimen, TreatmentOutcome,
    PositiveNegativeUnknown, DiseasesMedicalConditions,
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



class EnrollmentCsvUploadView(View):
    template_name = "nanopore/enrollment/enrollment_upload_values.html"

    def get(self, request, *args, **kwargs):
        form = EnrollmentUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = EnrollmentUploadForm(request.POST, request.FILES)
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
                cough2weeks = get_foreign(YesNo, row.get("Cough2Weeks"))
                poor_weight = get_foreign(YesNo, row.get("PoorWeight"))
                coughing_blood = get_foreign(YesNo, row.get("CoughingBlood"))
                unexplained_fever = get_foreign(YesNo, row.get("UnexplainedFever"))
                night_sweats = get_foreign(YesNo, row.get("NightSweats"))
                neck_lymph = get_foreign(YesNo, row.get("NeckLymph"))
                history_tb = get_foreign(YesNo, row.get("HistoryTb"))
                tx_previous = get_foreign(YesNoUnknown, row.get("TxPrevious"))
                tb_category = get_foreign(CategoryTreated, row.get("TbCategory"))
                tb_category_specify = row.get("TbCategorySpecify") or None
                tx_month = safe_int(row.get("TxMonth"))

                # --- Boolean unknown fields ---
                tx_unknown_month = to_bool(row.get("TxUnknownMonth"))
                tx_year = safe_int(row.get("TxYear"))
                tx_unknown_year = to_bool(row.get("TxUnknownYear"))
                ltf_months = safe_int(row.get("LtfMonths"))
                ltf_months_unknown = to_bool(row.get("LtfMonthsUnknown"))
                tb_regimen = get_foreign(TreatmentRegimen, row.get("TbRegimen"))
                tb_regimen_specify = row.get("TbRegimenSpecify") or None
                regimen_months = safe_int(row.get("RegimenMonths"))
                regimen_months_unknown = to_bool(row.get("RegimenMonthsUnknown"))

                tb_outcome = get_foreign(TreatmentOutcome, row.get("TbOutcome"))
                hiv_status = get_foreign(PositiveNegativeUnknown, row.get("HivStatus"))
                other_diseases = get_foreign(YesNoUnknown, row.get("OtherDiseases"))
                diseases_medical = split_m2m(DiseasesMedicalConditions, row.get("DiseasesMedical"))
                diseases_specify = row.get("DiseasesSpecify") or None
                sputum_collected = get_foreign(YesNo, row.get("SputumCollected"))
                sputum_date = parse_date_field(row.get("SputumDate"))
                sputum_reasons = row.get("SputumReasons") or None
                remarks = row.get("Remarks") or None

                enrollment_date = parse_date_field(row.get("EnrollmentDate"))
                date_information_collected = parse_date_field(row.get("DateInformationCollected"))
                if not enrollment_date:
                    raise ValueError("EnrollmentDate is required.")
                if not date_information_collected:
                    raise ValueError("DateInformationCollected is required.")

                # --- Create or update Enrollment ---
                enrollment, created = Enrollment.objects.update_or_create(
                    screening=screening,
                    defaults={
                        "enrollment_date": enrollment_date,
                        "cough2weeks": cough2weeks,
                        "poor_weight": poor_weight,
                        "coughing_blood": coughing_blood,
                        "unexplained_fever": unexplained_fever,
                        "night_sweats": night_sweats,
                        "neck_lymph": neck_lymph,
                        "history_tb": history_tb,
                        "date_information_collected": date_information_collected,
                        "tx_previous": tx_previous,
                        "tb_category": tb_category,
                        "tb_category_specify": tb_category_specify,
                        "tx_month": tx_month,
                        "tx_unknown_month": tx_unknown_month,
                        "tx_year": tx_year,
                        "tx_unknown_year": tx_unknown_year,
                        "dr_ds": get_foreign(DrDsTB, row.get("DrDs")),
                        "ltf_months": ltf_months,
                        "ltf_months_unknown": ltf_months_unknown,
                        "tb_regimen": tb_regimen,
                        "tb_regimen_specify": tb_regimen_specify,
                        "regimen_months": regimen_months,
                        "regimen_months_unknown": regimen_months_unknown,
                        "tb_otcome": tb_outcome,
                        "hiv_status": hiv_status,
                        "other_diseases": other_diseases,
                        "diseases_specify": diseases_specify,
                        "sputum_collected": sputum_collected,
                        "sputum_date": sputum_date,
                        "sputum_reasons": sputum_reasons,
                        "remarks": remarks,
                    },
                )
                # --- Set ManyToMany separately ---
                enrollment.diseases_medical.set(diseases_medical)
                enrollment.save()

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
                    "form": EnrollmentUploadForm(),
                    "row_errors": row_errors,
                    "count_created": count_created,
                    "count_updated": count_updated,
                },
            )

        if count_created or count_updated:
            messages.success(
                request,
                f"Imported {count_created} new and updated {count_updated} enrollments."
            )
        return redirect("nanopore:form-status-list")
