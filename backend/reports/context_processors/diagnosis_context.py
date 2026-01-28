from datetime import timedelta
from django.apps import apps
from django.utils import timezone
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def diagnosis_report_total(request):
    """
    Navbar totals for Diagnosis data quality issues.

    Conditional rules:
    1️⃣ If tb_diagnosis = 1:
        - tb_diagnosis_date must exist
        - tb_diagnosis_made must exist
        - tb_treatment must exist
    2️⃣ If tb_diagnosis = 2:
        - tb_other_diagnosis must exist
        - tb_diagnosis_made2 must exist
        - If tb_other_diagnosis = 96, tb_other_specify must exist
    3️⃣ Other treatment/outcome rules remain unchanged.
    """

    if not request.user.is_authenticated:
        return {
            "diagnosis_report_total": 0,
            "missing_tb_diagnosis": 0,
            "missing_tb_diagnosis_date": 0,
            "missing_tb_diagnosis_made": 0,
            "missing_tb_treatment_if_diag1": 0,
            "missing_tb_other_diagnosis": 0,
            "missing_tb_diagnosis_made2": 0,
            "missing_tb_other_specify": 0,
            "missing_bacteriological_diagnosis": 0,
            "missing_tb_treatment": 0,
            "missing_tb_treatment_date": 0,
            "missing_tb_facility": 0,
            "missing_tb_regimen": 0,
            "missing_tb_outcome2": 0,
            "missing_tb_outcome2_date": 0,
            "pending_tb_outcome": 0,
            "pending_tb_outcome_date": 0,
        }

    Diagnosis = apps.get_model("nanopore", "Diagnosis")

    diagnoses = Diagnosis.objects.all()
    diagnoses = filter_queryset_by_user_role(request.user, diagnoses, site_field="screening__site")

    # ── Missing TB diagnosis
    missing_tb_diagnosis = diagnoses.filter(tb_diagnosis__isnull=True).count()

    # ── Conditional TB diagnosis = 1
    missing_tb_diagnosis_date = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True).count()
    missing_tb_diagnosis_made = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True).count()
    missing_tb_treatment_if_diag1 = diagnoses.filter(tb_diagnosis=1, tb_treatment__isnull=True).count()

    # ── Conditional TB diagnosis = 2
    missing_tb_other_diagnosis = diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True).count()
    missing_tb_diagnosis_made2 = diagnoses.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True).count()
    missing_tb_other_specify = diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis=96, tb_other_specify__isnull=True).count()

    # ── Other fields
    missing_bacteriological_diagnosis = diagnoses.filter(bacteriological_diagnosis__isnull=True).count()
    missing_tb_treatment = diagnoses.filter(tb_diagnosis__isnull=False, tb_treatment__isnull=True).count()
    missing_tb_treatment_date = diagnoses.filter(tb_treatment=1, tb_treatment_date__isnull=True).count()
    missing_tb_facility = diagnoses.filter(tb_treatment=1, tb_facility__isnull=True).count()
    missing_tb_regimen = diagnoses.filter(tb_treatment=1, tb_regimen__isnull=True).count()
    missing_tb_outcome2 = diagnoses.filter(tb_treatment=1, tb_outcome2__isnull=True).count()
    missing_tb_outcome2_date = diagnoses.filter(tb_treatment=1, tb_outcome2__isnull=False, tb_outcome2_date__isnull=True).count()

    # ── Long-term treatment ≥ 6 months
    six_months_ago = timezone.now().date() - timedelta(days=180)
    long_treatment = diagnoses.filter(
        tb_treatment=1,
        tb_treatment_date__isnull=False,
        tb_treatment_date__lte=six_months_ago
    )

    pending_tb_outcome = long_treatment.filter(tb_outcome2__isnull=True)
    pending_tb_outcome_date = long_treatment.filter(tb_outcome2_date__isnull=True)

    # ── Aggregate total issues
    diagnosis_report_total = (
        missing_tb_diagnosis
        + missing_tb_diagnosis_date
        + missing_tb_diagnosis_made
        + missing_tb_treatment_if_diag1
        + missing_tb_other_diagnosis
        + missing_tb_diagnosis_made2
        + missing_tb_other_specify
        + missing_bacteriological_diagnosis
        + missing_tb_treatment
        + missing_tb_treatment_date
        + missing_tb_facility
        + missing_tb_regimen
        + missing_tb_outcome2
        + missing_tb_outcome2_date
    )

    return {
        "diagnosis_report_total": diagnosis_report_total,
        "missing_tb_diagnosis": missing_tb_diagnosis,
        "missing_tb_diagnosis_date": missing_tb_diagnosis_date,
        "missing_tb_diagnosis_made": missing_tb_diagnosis_made,
        "missing_tb_treatment_if_diag1": missing_tb_treatment_if_diag1,
        "missing_tb_other_diagnosis": missing_tb_other_diagnosis,
        "missing_tb_diagnosis_made2": missing_tb_diagnosis_made2,
        "missing_tb_other_specify": missing_tb_other_specify,
        "missing_bacteriological_diagnosis": missing_bacteriological_diagnosis,
        "missing_tb_treatment": missing_tb_treatment,
        "missing_tb_treatment_date": missing_tb_treatment_date,
        "missing_tb_facility": missing_tb_facility,
        "missing_tb_regimen": missing_tb_regimen,
        "missing_tb_outcome2": missing_tb_outcome2,
        "missing_tb_outcome2_date": missing_tb_outcome2_date,
        "pending_tb_outcome": pending_tb_outcome.count(),
        "pending_tb_outcome_date": pending_tb_outcome_date.count(),
    }
