import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from nanopore.forms.screening.screening_upload_form import ScreeningUploadForm
from locations.models import Site   # adjust if your model imports differ
from nanopore.models import Screening
from demographic.models import Sex
from django.utils.dateparse import parse_date

class ScreeningCsvUploadView(View):
    template_name = "nanopore/screening/screening_upload.html"

    def get(self, request, *args, **kwargs):
        form = ScreeningUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = ScreeningUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.cleaned_data["file"]

            if not file.name.endswith(".csv"):
                messages.error(request, "Please upload a CSV file.")
                return redirect("nanopore:form-status-list")

            data_set = file.read().decode("utf-8")
            io_string = io.StringIO(data_set)
            reader = csv.DictReader(io_string)

            count_created = 0
            count_updated = 0

            for row in reader:
                pid = row.get("PID") or row.get("pid")
                if not pid:
                    continue  # skip rows without PID

                screening, created = Screening.objects.update_or_create(
                    pid=pid,
                    defaults={
                        "screening_date": parse_date(row.get("Screening Date")),
                        "dob": parse_date(row.get("DOB")),
                        "age": row.get("Age") or None,
                        "remarks": row.get("Remarks"),
                        "site": Site.objects.filter(name=row.get("Site")).first(),
                        "sex": Sex.objects.filter(name=row.get("Sex")).first(),
                        # 🔹 Add other fields mapping here
                    },
                )
                if created:
                    count_created += 1
                else:
                    count_updated += 1

            messages.success(request, f"Imported {count_created} new and updated {count_updated} screenings.")
            return redirect("nanopore:form-status-list")

        return render(request, self.template_name, {"form": form})
