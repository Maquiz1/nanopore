import csv
import io
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
            return redirect("nanopore:form-status-list")

        data_set = file.read().decode("utf-8")
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)

        count_created = 0
        count_updated = 0
        row_errors = []

        def get_yesno(value):
            if not value:
                return None
            return YesNo.objects.filter(name__iexact=value.strip()).first()

        def get_enrolled_reason(value):
            if not value:
                return None
            return EnrolledReason.objects.filter(reason__iexact=value.strip()).first()

        for idx, row in enumerate(reader, start=2):
            pid = row.get("PID") or row.get("pid")
            if not pid:
                row_errors.append(f"Row {idx}: Missing PID")
                continue

            try:
                # Required YesNo fields
                age18years = get_yesno(row.get("Age18Years"))
                produce_resp_sample = get_yesno(row.get("ProduceRespSample"))
                consent = get_yesno(row.get("Consent"))
                unable_understand = get_yesno(row.get("UnableUnderstand"))
                not_willing = get_yesno(row.get("NotWilling"))
                enrolled = get_yesno(row.get("Enrolled"))

                missing_fields = []
                for field_name, value in [
                    ("Age18Years", age18years),
                    ("ProduceRespSample", produce_resp_sample),
                    ("Consent", consent),
                    ("UnableUnderstand", unable_understand),
                    ("NotWilling", not_willing),
                    ("Enrolled", enrolled)
                ]:
                    if not value:
                        missing_fields.append(field_name)

                if missing_fields:
                    raise ValueError(f"Missing or invalid required fields: {', '.join(missing_fields)}")

                # Optional fields
                present_symptoms = get_yesno(row.get("PresentSymptoms"))
                genexpert_confirmation = get_yesno(row.get("GenexpertConfirmation"))
                reasons = get_enrolled_reason(row.get("Reasons"))
                reasons_other = row.get("OtherReason") or None
                
                screening_date = parse_date(row.get("ScreeningDate"))
                dob = parse_date(row.get("DOB"))
                age = int(row["Age"]) if row.get("Age") else None

                site = Site.objects.filter(name=row.get("Site")).first()
                sex = Sex.objects.filter(name=row.get("Sex")).first()
                remarks = row.get("Remarks") or None

                screening, created = Screening.objects.update_or_create(
                    pid=pid,
                    defaults={
                        "screening_date": screening_date,
                        "dob": dob,
                        "age": age,
                        "remarks": remarks,
                        "site": site,
                        "sex": sex,
                        "age18years": age18years,
                        "produce_resp_sample": produce_resp_sample,
                        "consent": consent,
                        "unable_understand": unable_understand,
                        "not_willing": not_willing,
                        "enrolled": enrolled,
                        "present_symptoms": present_symptoms,
                        "genexpert_confirmation": genexpert_confirmation,
                        "reasons": reasons,
                        "reasons_other": reasons_other,
                    },
                )

                if created:
                    count_created += 1
                else:
                    count_updated += 1

            except Exception as e:
                row_errors.append(f"Row {idx} (PID={pid}): {str(e)}")

        if count_created or count_updated:
            messages.success(
                request,
                f"Imported {count_created} new and updated {count_updated} screenings."
            )

        if row_errors:
            for err in row_errors:
                messages.error(request, err)

        return redirect("nanopore:form-status-list")
