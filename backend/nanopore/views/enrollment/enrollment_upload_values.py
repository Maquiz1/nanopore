import csv
import io
from datetime import date
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views import View
from django.utils.dateparse import parse_date

from nanopore.forms.enrollment.enrollment_upload_form import EnrollmentUploadForm
from nanopore.models.enrollment import Enrollment
from nanopore.models.screening import Screening
from locations.models import Site
from options.models import (
    YesNo, YesNoUnknown, CategoryTreated, MonthUnknown, YearUnknown,
    DrDsTB, TreatmentRegimen, TreatmentOutcome, PositiveNegativeUnknown,
    DiseasesMedicalConditions,
)


def safe_int(val):
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


def get_many_to_many(obj_class, val):
    """Return queryset of ManyToMany objects from comma-separated IDs."""
    if not val:
        return obj_class.objects.none()
    ids = [safe_int(x) for x in str(val).split(",") if safe_int(x) is not None]
    return obj_class.objects.filter(pk__in=ids)


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
                tx_previous = get_foreign(YesNoUnknown, row.get("TxPrevious"))
                tb_category = get_foreign(CategoryTreated, row.get("TbCategory"))
                tb_category_specify = row.get("TbCategorySpecify") or None
                tx_month = safe_int(row.get("TxMonth"))
                tx_unknown_month = get_foreign(MonthUnknown, row.get("TxUnknownMonth"))
                tx_year = safe_int(row.get("TxYear"))
                tx_unknown_year = get_foreign(YearUnknown, row.get("TxUnknownYear"))
                dr_ds = get_foreign(DrDsTB, row.get("DrDs"))
                ltf_months = safe_int(row.get("LtfMonths"))
                ltf_months_unknown = get_foreign(MonthUnknown, row.get("LtfMonthsUnknown"))
                tb_regimen = get_foreign(TreatmentRegimen, row.get("TbRegimen"))
                tb_regimen_specify = row.get("TbRegimenSpecify") or None
                regimen_months = safe_int(row.get("RegimenMonths"))
                regimen_months_unknown = get_foreign(MonthUnknown, row.get("RegimenMonthsUnknown"))
                tb_outcome = get_foreign(TreatmentOutcome, row.get("TbOutcome"))
                hiv_status = get_foreign(PositiveNegativeUnknown, row.get("HivStatus"))
                other_diseases = get_foreign(YesNoUnknown, row.get("OtherDiseases"))
                diseases_medical = get_many_to_many(DiseasesMedicalConditions, row.get("DiseasesMedical"))
                diseases_specify = row.get("DiseasesSpecify") or None
                sputum_collected = get_foreign(YesNo, row.get("SputumCollected"))
                sputum_date = parse_date(row.get("SputumDate"))
                sputum_reasons = row.get("SputumReasons") or None
                remarks = row.get("Remarks") or None

                enrollment_date = parse_date(row.get("EnrollmentDate"))
                date_information_collected = parse_date(row.get("DateInformationCollected"))
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
                        "date_information_collected": date_information_collected,
                        "tx_previous": tx_previous,
                        "tb_category": tb_category,
                        "tb_category_specify": tb_category_specify,
                        "tx_month": tx_month,
                        "tx_unknown_month": tx_unknown_month,
                        "tx_year": tx_year,
                        "tx_unknown_year": tx_unknown_year,
                        "dr_ds": dr_ds,
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
        return redirect("nanopore:enrollment-list")
