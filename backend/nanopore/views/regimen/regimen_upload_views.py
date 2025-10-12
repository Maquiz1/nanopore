import csv
import io
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date
from django.contrib.auth import get_user_model

from nanopore.forms.regimen.regimen_changes_upload_form import RegimenChangesUploadForm
from nanopore.models.regimen_changes import RegimenChanges
from nanopore.models.screening import Screening
from options.models import RegimenTypeOfChange, RegimenReasonForChange

User = get_user_model()


def safe_int(val):
    if val is None or str(val).strip() == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def get_foreign(obj_class, val):
    """Safely get foreign key object by ID or return None if missing/invalid."""
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


class RegimenChangesCsvUploadView(View):
    template_name = "nanopore/regimen/regimen_upload.html"

    def get(self, request, *args, **kwargs):
        form = RegimenChangesUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = RegimenChangesUploadForm(request.POST, request.FILES)
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

                # --- Parse fields ---
                date = safe_date(row.get("Date"))
                drug = row.get("Drug") or None
                changes = get_foreign(RegimenTypeOfChange, row.get("Changes"))
                reason = get_foreign(RegimenReasonForChange, row.get("Reason"))
                specify = row.get("Specify") or None

                # --- Create or update RegimenChanges ---
                regimen_change, created = RegimenChanges.objects.update_or_create(
                    screening=screening,
                    date=date,
                    drug=drug,
                    defaults={
                        "changes": changes,
                        "reason": reason,
                        "specify": specify,
                        "updated_by": request.user,
                    },
                )

                if created:
                    regimen_change.created_by = request.user
                    regimen_change.save()
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
                    "form": RegimenChangesUploadForm(),
                    "row_errors": row_errors,
                    "count_created": count_created,
                    "count_updated": count_updated,
                },
            )

        if count_created or count_updated:
            messages.success(
                request,
                f"Imported {count_created} new and updated {count_updated} regimen changes."
            )
        return redirect("nanopore:form-status-list")
