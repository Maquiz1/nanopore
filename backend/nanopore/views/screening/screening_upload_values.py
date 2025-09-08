import csv
import io
from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date

from nanopore.forms.screening.screening_upload_form import ScreeningUploadForm
from nanopore.models import Screening
from locations.models import Site
from demographic.models import Sex
from options.models import YesNo, EnrolledReason


def safe_int(val):
    """Convert string numbers like '1.0' to int, return None if invalid."""
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


def safe_eligible(row, consent, age18years, present_symptoms,
                  produce_resp_sample, unable_understand, not_willing):
    """
    Return a safe boolean for 'eligible'.
    1. Parse CSV value if present (handles True/False/1/0/Yes/No with extra spaces).
    2. If missing/invalid, calculate based on YesNo ForeignKeys.
    Always returns True or False (never None).
    """

    # --- Step 1: Parse CSV column ---
    csv_val = row.get("Eligible") or row.get("eligible")
    if csv_val is not None:
        # Remove spaces, tabs, non-breaking spaces, lowercase
        csv_val_str = str(csv_val).strip().replace("\xa0", "").lower()
        if csv_val_str in ["true", "1", "yes"]:
            return True
        elif csv_val_str in ["false", "0", "no"]:
            return False

    # --- Step 2: Fallback: calculate from YesNo FKs ---
    def val_to_bool(fk_obj, default="No"):
        """
        Convert a YesNo ForeignKey object to boolean.
        If None, uses default ('Yes' or 'No').
        """
        if fk_obj is None:
            return default.lower() == "yes"
        return getattr(fk_obj, "name", default).lower() == "yes"

    consent_val = val_to_bool(consent, "No")
    age18_val = val_to_bool(age18years, "No")
    symptom_val = val_to_bool(present_symptoms, "No")
    produce_val = val_to_bool(produce_resp_sample, "No")
    unable_val = val_to_bool(unable_understand, "No")
    not_willing_val = val_to_bool(not_willing, "No")

    # --- Step 3: Apply eligibility logic ---
    consent_logic = consent_val and not unable_val and not not_willing_val
    screening_logic = age18_val and symptom_val and produce_val

    return consent_logic and screening_logic



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
                consent = get_foreign(YesNo, row.get("Consent"))
                age18years = get_foreign(YesNo, row.get("Age18Years"))
                produce_resp_sample = get_foreign(YesNo, row.get("ProduceRespSample"))
                unable_understand = get_foreign(YesNo, row.get("UnableUnderstand"))
                not_willing = get_foreign(YesNo, row.get("NotWilling"))
                enrolled = get_foreign(YesNo, row.get("Enrolled"))
                present_symptoms = get_foreign(YesNo, row.get("PresentSymptoms"))
                genexpert_confirmation = get_foreign(YesNo, row.get("GenexpertConfirmation"))
                reasons = get_foreign(EnrolledReason, row.get("Reasons"))
                reasons_other = row.get("ReasonsOther") or None
                pid1 = row.get("PID1") or None
                pid2 = row.get("PID2") or None

                # --- Site (required) ---
                site = get_foreign(Site, row.get("Site"))
                if not site:
                    raise ValueError(f"Invalid or missing Site ID '{row.get('Site')}'")

                # --- Sex (optional) ---
                sex = get_foreign(Sex, row.get("Sex"))

                # --- Dates ---
                screening_date = parse_date(row.get("ScreeningDate"))
                dob = parse_date(row.get("DOB"))
                consent_date = parse_date(row.get("ConsentDate"))

                if not screening_date:
                    raise ValueError("Screening date is required.")

                # --- Calculate missing DOB or Age ---
                age_val = safe_int(row.get("Age"))
                if not dob and age_val:
                    dob = date(screening_date.year - age_val, screening_date.month, screening_date.day)
                    age = age_val
                elif dob:
                    age = screening_date.year - dob.year - ((screening_date.month, screening_date.day) < (dob.month, dob.day))
                else:
                    dob = None
                    age = age_val if age_val else None

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
                    consent_date = None  # Clear consent date if consent is No

                # --- Determine eligible safely ---
                eligible_val = safe_eligible(row, consent, age18years, present_symptoms,
                                             produce_resp_sample, unable_understand, not_willing)

                # --- Create or update Screening ---
                screening, created = Screening.objects.update_or_create(
                    pid=pid,
                    defaults={
                        "pid1": pid1,
                        "pid2": pid2,
                        "screening_date": screening_date,
                        "dob": dob,
                        "age": age,
                        "remarks": row.get("Remarks") or None,
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
                        "reasons_other": reasons_other,
                        "eligible": eligible_val,  # safe boolean
                    },
                )
                screening.save()  # eligible recalculated in model save()

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
