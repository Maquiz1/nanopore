from datetime import timedelta
from django.apps import apps
from django.utils import timezone
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def diagnosis_report_total(request):
    """
    Navbar count for Diagnosis data quality issues — aligned with clinic_report_total style.

    Counts:
    - Missing critical diagnosis/treatment fields
    - Treatment started ≥ 6 months ago missing outcome (tb_outcome2)
    - Treatment started ≥ 6 months ago missing outcome date (tb_outcome2_date)
    """
    if not request.user.is_authenticated:
        return {
            "diagnosis_report_total": 0,
            # Missing core diagnosis fields
            "missing_tb_diagnosis": 0,
            "missing_tb_diagnosis_date": 0,
            "missing_tb_diagnosis_made": 0,
            "missing_bacteriological_diagnosis": 0,
            "missing_tb_treatment": 0,
            "missing_tb_treatment_date": 0,
            "missing_tb_facility": 0,
            "missing_tb_regimen": 0,
            "missing_tb_outcome2": 0,
            "missing_tb_outcome2_date": 0,
            # Long-term treatment workflow issues
            "pending_tb_outcome": 0,
            "pending_tb_outcome_date": 0,
        }

    Diagnosis = apps.get_model("nanopore", "Diagnosis")

    # ── Role-filtered base queryset ─────────────────────────────────────────
    diagnoses = Diagnosis.objects.all()
    diagnoses = filter_queryset_by_user_role(
        request.user,
        diagnoses,
        site_field="screening__site"
    )

    # ── Q helpers (following clinic_report_total pattern) ───────────────────
    tb_treatment_is_1_q = Q(tb_treatment__value=1) | Q(tb_treatment__name__iexact="1")

    # For fields that might be choices or FKs — we check __isnull or empty string
    # (you can adjust if some fields use different choice values)

    # ── Missing field counts ────────────────────────────────────────────────
    missing_tb_diagnosis          = diagnoses.filter(tb_diagnosis__isnull=True).count()
    missing_tb_diagnosis_date     = diagnoses.filter(tb_diagnosis_date__isnull=True).count()
    missing_tb_diagnosis_made     = diagnoses.filter(tb_diagnosis_made__isnull=True).count()
    missing_bacteriological_diagnosis = diagnoses.filter(bacteriological_diagnosis__isnull=True).count()
    missing_tb_treatment          = diagnoses.filter(tb_treatment__isnull=True).count()
    missing_tb_treatment_date     = diagnoses.filter(tb_treatment_is_1_q, tb_treatment_date__isnull=True).count()
    missing_tb_facility           = diagnoses.filter(tb_facility__isnull=True).count()
    missing_tb_regimen            = diagnoses.filter(tb_treatment_is_1_q, tb_regimen__isnull=True).count()
    missing_tb_outcome2           = diagnoses.filter(tb_outcome2__isnull=True).count()
    missing_tb_outcome2_date      = diagnoses.filter(tb_outcome2__isnull=False, tb_outcome2_date__isnull=True).count()

    # ── Long-term treatment checks (≥ 6 months) ─────────────────────────────
    six_months_ago = timezone.now().date() - timedelta(days=180)

    long_treatment_base = diagnoses.filter(
        tb_treatment_is_1_q,
        tb_treatment_date__isnull=False,
        tb_treatment_date__lte=six_months_ago
    )

    pending_tb_outcome = long_treatment_base.filter(tb_outcome2__isnull=True)
    pending_tb_outcome_date = long_treatment_base.filter(tb_outcome2_date__isnull=True)

    # ── Aggregate total issues ──────────────────────────────────────────────
    diagnosis_report_total = (
        missing_tb_diagnosis
        + missing_tb_diagnosis_date
        + missing_tb_diagnosis_made
        + missing_bacteriological_diagnosis
        + missing_tb_treatment
        + missing_tb_treatment_date
        + missing_tb_facility
        + missing_tb_regimen
        + missing_tb_outcome2
        + missing_tb_outcome2_date
        + pending_tb_outcome.count()
        + pending_tb_outcome_date.count()
    )

    return {
        "diagnosis_report_total": diagnosis_report_total,
        "missing_tb_diagnosis": missing_tb_diagnosis,
        "missing_tb_diagnosis_date": missing_tb_diagnosis_date,
        "missing_tb_diagnosis_made": missing_tb_diagnosis_made,
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