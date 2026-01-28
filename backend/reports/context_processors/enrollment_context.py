# reports/context_processors.py
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def enrollment_report_total(request):
    """
    Navbar count for Enrollment data quality issues — aligned with clinic/diagnosis style.

    Counts:
    - Enrollments missing any critical field
    """
    if not request.user.is_authenticated:
        return {
            "enrollment_report_total": 0,
            # Individual missing field counts
            "missing_enrollment_date": 0,
            "missing_cough2weeks": 0,
            "missing_poor_weight": 0,
            "missing_coughing_blood": 0,
            "missing_unexplained_fever": 0,
            "missing_night_sweats": 0,
            "missing_neck_lymph": 0,
            "missing_history_tb": 0,
            "missing_date_information_collected": 0,
            "missing_tx_previous": 0,
        }

    Enrollment = apps.get_model('nanopore', 'Enrollment')

    # ── Role-filtered base queryset ─────────────────────────────────────────
    enrollments = Enrollment.objects.all()
    enrollments = filter_queryset_by_user_role(
        request.user,
        enrollments,
        site_field="screening__site"
    )

    # ── Missing field counts ────────────────────────────────────────────────
    # (assuming these are boolean/choice/date fields — adjust __isnull vs __exact=False if needed)
    missing_enrollment_date          = enrollments.filter(enrollment_date__isnull=True).count()
    missing_cough2weeks              = enrollments.filter(cough2weeks__isnull=True).count()
    missing_poor_weight              = enrollments.filter(poor_weight__isnull=True).count()
    missing_coughing_blood           = enrollments.filter(coughing_blood__isnull=True).count()
    missing_unexplained_fever        = enrollments.filter(unexplained_fever__isnull=True).count()
    missing_night_sweats             = enrollments.filter(night_sweats__isnull=True).count()
    missing_neck_lymph               = enrollments.filter(neck_lymph__isnull=True).count()
    missing_history_tb               = enrollments.filter(history_tb__isnull=True).count()
    missing_date_information_collected = enrollments.filter(date_information_collected__isnull=True).count()
    missing_tx_previous              = enrollments.filter(tx_previous__isnull=True).count()

    # ── Aggregate total issues ──────────────────────────────────────────────
    # Sum of all individual missing counts (same record can contribute multiple issues)
    enrollment_report_total = (
        missing_enrollment_date
        + missing_cough2weeks
        + missing_poor_weight
        + missing_coughing_blood
        + missing_unexplained_fever
        + missing_night_sweats
        + missing_neck_lymph
        + missing_history_tb
        + missing_date_information_collected
        + missing_tx_previous
    )

    return {
        "enrollment_report_total": enrollment_report_total,
        "missing_enrollment_date": missing_enrollment_date,
        "missing_cough2weeks": missing_cough2weeks,
        "missing_poor_weight": missing_poor_weight,
        "missing_coughing_blood": missing_coughing_blood,
        "missing_unexplained_fever": missing_unexplained_fever,
        "missing_night_sweats": missing_night_sweats,
        "missing_neck_lymph": missing_neck_lymph,
        "missing_history_tb": missing_history_tb,
        "missing_date_information_collected": missing_date_information_collected,
        "missing_tx_previous": missing_tx_previous,
    }