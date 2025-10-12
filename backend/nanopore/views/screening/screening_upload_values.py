import csv
import io
from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from datetime import datetime

from nanopore.forms.screening.screening_upload_form import ScreeningUploadForm
from nanopore.models import Screening
from locations.models import Site
from demographic.models import Sex
from options.models import YesNo, EnrolledReason


def clean_text(val):
    """Strip spaces and normalize empty strings to None."""
    if val is None:
        return None
    cleaned = str(val).strip()
    return cleaned if cleaned else None


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


class ScreeningCsvUploadValuesView(View):
    template_name = "nanopore/screening/screening_upload_values.html"

    def get(self, request, *args, **kwargs):
        form = ScreeningUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = ScreeningUploadForm(request.POST, request.FILES)
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
                # --- Foreign Keys ---
                consent = get_foreign(YesNo, row.get("Consent"), required=True, field_name="Consent")
                age18years = get_foreign(YesNo, row.get("Age18Years"), required=True, field_name="Age18Years")
                produce_resp_sample = get_foreign(YesNo, row.get("ProduceRespSample"), required=True, field_name="ProduceRespSample")
                unable_understand = get_foreign(YesNo, row.get("UnableUnderstand"), required=True, field_name="UnableUnderstand")
                not_willing = get_foreign(YesNo, row.get("NotWilling"), required=True, field_name="NotWilling")
                enrolled = get_foreign(YesNo, row.get("Enrolled"))
                present_symptoms = get_foreign(YesNo, row.get("PresentSymptoms"))
                genexpert_confirmation = get_foreign(YesNo, row.get("GenexpertConfirmation"))
                reasons = get_foreign(EnrolledReason, row.get("Reasons"))
                pid1 = row.get("PID1") or None
                pid2 = row.get("PID2") or None

                # --- Format PIDs ---
                def format_pid(val, field_name):
                    if val is None or str(val).strip() == "":
                        raise ValueError(f"{field_name} is required")
                    if not str(val).strip().isdigit():
                        raise ValueError(f"{field_name} must be numeric (got '{val}')")
                    return f"{int(val):03d}"  # pad to 3 digits

                pid1 = format_pid(pid1, "PID1")
                pid2 = format_pid(pid2, "PID2")

                if pid1 != pid2:
                    raise ValueError(f"PID1 ({pid1}) and PID2 ({pid2}) do not match.")

                # --- Site (required) ---
                site = get_foreign(Site, row.get("Site"))
                if not site:
                    raise ValueError(f"Invalid or missing Site ID '{row.get('Site')}'")

                # --- Sex (optional) ---
                sex = get_foreign(Sex, row.get("Sex"))

                # --- Dates ---
                screening_date = parse_date_field(row.get("ScreeningDate"))
                dob = parse_date_field(row.get("DOB"))
                consent_date = parse_date_field(row.get("ConsentDate"))

                if not screening_date:
                    raise ValueError("Screening date is required.")

                # --- Age / DOB validation (must be >= 18) ---
                eligible = str(row.get("Eligible")).strip().lower() == "true"  # Adjust depending on how Eligible is stored

                if eligible:
                    # Parse DOB string to date if exists
                    dob_str = row.get("DOB")
                    dob = None
                    if dob_str:
                        try:
                            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()  # adjust format to match your CSV
                        except ValueError:
                            raise ValueError(f"Invalid DOB format: {dob_str}")

                    age_val = safe_int(row.get("Age"))

                    if dob:
                        age_from_dob = screening_date.year - dob.year - (
                            (screening_date.month, screening_date.day) < (dob.month, dob.day)
                        )
                        if age_from_dob < 18:
                            raise ValueError("Participant must be at least 18 years old based on DOB.")
                        age = age_from_dob
                    elif age_val is not None:
                        if age_val < 18:
                            raise ValueError("Participant must be at least 18 years old based on Age.")
                        age = age_val
                    else:
                        raise ValueError("Either Age or DOB is required.")
                else:
                    age = age_val if age_val is not None else None


                # --- Consent date validation ---
                if consent and consent.name.lower() == "yes":
                    if consent_date:
                        if consent_date < screening_date:
                            raise ValueError("Consent date cannot be before Screening date.")
                        if consent_date > date.today():
                            raise ValueError("Consent date cannot be in the future.")
                    else:
                        raise ValueError("Consent date is required when consent is Yes.")
                else:
                    consent_date = None

                # --- Create or update Screening ---
                screening, created = Screening.objects.update_or_create(
                    pid=pid,
                    defaults={
                        "pid1": pid1,
                        "pid2": pid2,
                        "screening_date": screening_date,
                        "dob": dob,
                        "age": age,
                        "remarks": clean_text(row.get("Remarks")),
                        "site": site,
                        "sex": sex,
                        "age18years": age18years,
                        "produce_resp_sample": produce_resp_sample,
                        "consent": consent,
                        "consent_date": consent_date,
                        "unable_understand": unable_understand,
                        "not_willing": not_willing,
                        "enrolled": enrolled,
                        "present_symptoms": present_symptoms,
                        "genexpert_confirmation": genexpert_confirmation,
                        "reasons": reasons,
                        "reasons_other": clean_text(row.get("ReasonsOther")),
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
                    "form": ScreeningUploadForm(),
                    "row_errors": row_errors,
                    "count_created": count_created,
                    "count_updated": count_updated,
                },
            )

        if count_created or count_updated:
            messages.success(
                request,
                f"Imported {count_created} new and updated {count_updated} screenings."
            )
        return redirect("nanopore:form-status-list")
