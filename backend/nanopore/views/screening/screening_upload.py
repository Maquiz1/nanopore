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
from clinical.models import YesNo
from reasons.models import EnrolledReason


class ScreeningCsvUploadView(View):
    template_name = "nanopore/screening/screening_upload.html"

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

        # Prepare YesNo and EnrolledReason maps
        yesno_map = {yn.name.lower(): yn for yn in YesNo.objects.all()}
        reason_map = {r.reason.lower(): r for r in EnrolledReason.objects.all()}

        for idx, row in enumerate(reader, start=2):
            pid = row.get("PID") or row.get("pid")
            if not pid:
                row_errors.append(f"Row {idx}: Missing PID")
                continue

            try:
                # --- Required YesNo fields ---
                def get_yesno(val):
                    if not val:
                        return None
                    return yesno_map.get(val.strip().lower())

                age18years = get_yesno(row.get("Age >=18") or row.get("Age18Years"))
                produce_resp_sample = get_yesno(row.get("Produce Respiratory Sample") or row.get("ProduceRespSample"))
                consent = get_yesno(row.get("Consent"))
                unable_understand = get_yesno(row.get("Unable Understand") or row.get("UnableUnderstand"))
                not_willing = get_yesno(row.get("Not Willing") or row.get("NotWilling"))
                enrolled = get_yesno(row.get("Enrolled"))

                # Check for missing required YesNo
                required_fields = {
                    "Age18Years": age18years,
                    "ProduceRespSample": produce_resp_sample,
                    "Consent": consent,
                    "UnableUnderstand": unable_understand,
                    "NotWilling": not_willing,
                    "Enrolled": enrolled
                }
                missing = [k for k, v in required_fields.items() if not v]
                if missing:
                    raise ValueError(f"Missing or invalid required fields: {', '.join(missing)}")

                # --- Optional YesNo fields ---
                present_symptoms = get_yesno(row.get("Present Symptoms") or row.get("PresentSymptoms"))
                genexpert_confirmation = get_yesno(row.get("Genexpert Confirmation") or row.get("GenexpertConfirmation"))

                # --- EnrolledReason ---
                reasons_val = row.get("Reason") or row.get("Reasons")
                reasons = reason_map.get(reasons_val.strip().lower()) if reasons_val else None
                reasons_other = row.get("Other Reason") or row.get("reasons_other") or None

                # --- Dates ---
                screening_date = parse_date(row.get("Screening Date") or row.get("ScreeningDate"))
                dob = parse_date(row.get("DOB"))
                consent_date = parse_date(row.get("Consent Date") or row.get("ConsentDate"))

                if not screening_date:
                    raise ValueError("Screening date is required.")
                if not dob and not row.get("Age"):
                    raise ValueError("Either DOB or Age is required.")

                # --- Site & Sex ---
                site_name = row.get("Site")
                site = Site.objects.filter(name=site_name).first()
                if not site:
                    raise ValueError(f"Site '{site_name}' not found.")

                sex_name = row.get("Sex")
                sex = Sex.objects.filter(name__iexact=sex_name).first()
                if not sex:
                    raise ValueError(f"Sex '{sex_name}' not found.")

                # --- Age calculation ---
                if not dob:
                    age = int(row.get("Age"))
                    dob = date(screening_date.year - age, screening_date.month, screening_date.day)
                else:
                    age = screening_date.year - dob.year - ((screening_date.month, screening_date.day) < (dob.month, dob.day))

                # --- Consent date validation ---
                if consent.name.lower() == "yes":
                    if not consent_date:
                        raise ValueError("Consent date is required when consent is Yes.")
                    if consent_date < screening_date:
                        raise ValueError("Consent date cannot be before Screening date.")
                    if consent_date > date.today():
                        raise ValueError("Consent date cannot be in the future.")
                else:
                    if consent_date:
                        raise ValueError("Consent date should be empty when consent is No.")

                # --- Create or update Screening ---
                screening, created = Screening.objects.update_or_create(
                    pid=pid,
                    defaults={
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
                        "eligible": False,  # ensures DB not null; model recalculates
                    },
                )
                # Trigger model's save() to recalc eligible
                screening.save()

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            except Exception as e:
                row_errors.append(f"Row {idx} (PID={pid}): {str(e)}")

        # --- Display results ---
        if row_errors:
            messages.error(request, "Some rows had errors. Please fix them and re-upload the CSV.")
            return render(request, self.template_name, {
                "form": ScreeningUploadForm(),
                "row_errors": row_errors,
                "count_created": count_created,
                "count_updated": count_updated
            })

        if count_created or count_updated:
            messages.success(request, f"Imported {count_created} new and updated {count_updated} screenings.")
        return redirect("nanopore:form-status-list")
