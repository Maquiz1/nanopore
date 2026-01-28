from datetime import timedelta
from django.apps import apps
from django.utils import timezone
from utils.permissions import filter_queryset_by_user_role


def diagnosis_report_total(request):
    """
    Diagnosis data quality issues (navbar totals).

    Rules:
    - tb_outcome2 checked only if tb_treatment=1 and ≥6 months.
    - tb_outcome2_date checked only if tb_outcome2 in 1–5.
    """

    if not request.user.is_authenticated:
        return {"diagnosis_report_total": 0}

    Diagnosis = apps.get_model("nanopore", "Diagnosis")

    diagnoses = Diagnosis.objects.all()
    diagnoses = filter_queryset_by_user_role(
        request.user, diagnoses, site_field="screening__site"
    )

    # ─────────────────────────────────────────────
    # TB DIAGNOSIS
    # ─────────────────────────────────────────────
    missing_tb_diagnosis = diagnoses.filter(tb_diagnosis__isnull=True).count()
    missing_tb_diagnosis_date = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_date__isnull=True).count()
    missing_tb_diagnosis_made = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made__isnull=True).count()
    missing_tb_treatment = diagnoses.filter(tb_diagnosis=1, tb_treatment__isnull=True).count()
    missing_diagnosis_made_other = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=96, diagnosis_made_other__isnull=True).count()
    missing_tb_diagnosed_clinically = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=1, tb_diagnosed_clinically__isnull=True).count()
    missing_tb_clinically_other = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=1, tb_diagnosed_clinically__id=96, tb_clinically_other__isnull=True).count()
    missing_bacteriological_diagnosis = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, bacteriological_diagnosis__isnull=True).count()
    missing_clinician_received_date = diagnoses.filter(tb_diagnosis=1, tb_diagnosis_made=2, clinician_received_date__isnull=True).count()

    missing_tb_other_diagnosis = diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis__isnull=True).count()
    missing_tb_diagnosis_made2 = diagnoses.filter(tb_diagnosis=2, tb_diagnosis_made2__isnull=True).count()
    missing_tb_other_specify = diagnoses.filter(tb_diagnosis=2, tb_other_diagnosis=96, tb_other_specify__isnull=True).count()

    # ─────────────────────────────────────────────
    # TB TREATMENT
    # ─────────────────────────────────────────────
    missing_tb_treatment_date = diagnoses.filter(tb_treatment=1, tb_treatment_date__isnull=True).count()
    missing_tb_register_number = diagnoses.filter(tb_treatment=1, tb_register_number__isnull=True).count()
    missing_tb_regimen = diagnoses.filter(tb_treatment=1, tb_regimen__isnull=True).count()
    missing_regimen_changed = diagnoses.filter(tb_treatment=1, regimen_changed__isnull=True).count()
    missing_tb_facility = diagnoses.filter(tb_treatment=2, tb_facility__isnull=True).count()
    missing_tb_reason = diagnoses.filter(tb_treatment=96, tb_reason__isnull=True).count()

    # ─────────────────────────────────────────────
    # TB OUTCOME CHECK (≥6 MONTHS TREATMENT)
    # ─────────────────────────────────────────────
    six_months_ago = timezone.now().date() - timedelta(days=180)
    long_treatment = diagnoses.filter(tb_treatment=1, tb_treatment_date__lte=six_months_ago)

    pending_tb_outcome = long_treatment.filter(tb_outcome2__isnull=True).count()
    pending_tb_outcome_date = long_treatment.filter(tb_outcome2__in=[1, 2, 3, 4, 5], tb_outcome2_date__isnull=True).count()

    # ─────────────────────────────────────────────
    # TOTAL
    # ─────────────────────────────────────────────
    diagnosis_report_total = (
        missing_tb_diagnosis
        + missing_tb_diagnosis_date
        + missing_tb_diagnosis_made
        + missing_tb_treatment
        + missing_diagnosis_made_other
        + missing_tb_diagnosed_clinically
        + missing_tb_clinically_other
        + missing_bacteriological_diagnosis
        + missing_clinician_received_date
        + missing_tb_other_diagnosis
        + missing_tb_diagnosis_made2
        + missing_tb_other_specify
        + missing_tb_treatment_date
        + missing_tb_register_number
        + missing_tb_regimen
        + missing_regimen_changed
        + missing_tb_facility
        + missing_tb_reason
        + pending_tb_outcome
        + pending_tb_outcome_date
    )

    return {
        "diagnosis_report_total": diagnosis_report_total,
        "missing_tb_diagnosis": missing_tb_diagnosis,
        "missing_tb_diagnosis_date": missing_tb_diagnosis_date,
        "missing_tb_diagnosis_made": missing_tb_diagnosis_made,
        "missing_tb_treatment": missing_tb_treatment,
        "missing_diagnosis_made_other": missing_diagnosis_made_other,
        "missing_tb_diagnosed_clinically": missing_tb_diagnosed_clinically,
        "missing_tb_clinically_other": missing_tb_clinically_other,
        "missing_bacteriological_diagnosis": missing_bacteriological_diagnosis,
        "missing_clinician_received_date": missing_clinician_received_date,
        "missing_tb_other_diagnosis": missing_tb_other_diagnosis,
        "missing_tb_diagnosis_made2": missing_tb_diagnosis_made2,
        "missing_tb_other_specify": missing_tb_other_specify,
        "missing_tb_treatment_date": missing_tb_treatment_date,
        "missing_tb_register_number": missing_tb_register_number,
        "missing_tb_regimen": missing_tb_regimen,
        "missing_regimen_changed": missing_regimen_changed,
        "missing_tb_facility": missing_tb_facility,
        "missing_tb_reason": missing_tb_reason,
        "pending_tb_outcome": pending_tb_outcome,
        "pending_tb_outcome_date": pending_tb_outcome_date,
    }
