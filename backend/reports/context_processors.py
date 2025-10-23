from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from django.db.models import F,Q, Count
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def global_report_total(request):
    """
    Global report summary counts for navbar:
    Includes both screening data quality issues and pending clinical workflow tasks.
    """

    report_total = 0
    screening_report_total = 0

    if not request.user.is_authenticated:
        return {"report_total": report_total, "screening_report_total": screening_report_total}

    # --- Models ---
    Screening = apps.get_model('nanopore', 'Screening')

    # --- Role-based filter ---
    screenings = Screening.objects.all()
    screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

    role_context = get_role_context(request.user)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin = role_context.get("is_admin", False)
    is_reviewer = role_context.get("is_reviewer", False)

    # --- 🔹 Screening Data Quality Issues ---
    # Missing required fields
    missing_fields_qs = screenings.filter(
        Q(pid1__isnull=True) | Q(pid2__isnull=True) |
        Q(sex__isnull=True) | Q(site__isnull=True) |
        Q(screening_date__isnull=True) |
        (Q(age__isnull=True) & Q(dob__isnull=True)) |
        Q(consent__isnull=True)
    )

    # Duplicate PIDs
    duplicate_pids = (
        screenings.values('pid')
        .annotate(pid_count=Count('id'))
        .filter(pid_count__gt=1)
    )
    duplicate_pid_list = [d['pid'] for d in duplicate_pids]
    duplicate_pid_qs = screenings.filter(pid__in=duplicate_pid_list)

    # PID1 ≠ PID2
    mismatched_pid_qs = screenings.filter(~Q(pid1=F('pid2')), pid1__isnull=False, pid2__isnull=False)

    # PID length ≠ 16
    invalid_length_qs = screenings.exclude(pid__isnull=True).exclude(pid__exact='').exclude(pid__regex=r'^.{16}$')

    # Not eligible
    not_eligible_qs = screenings.filter(eligible=False)

    # Combine all data quality issues
    screening_report_total = (
        missing_fields_qs.count() +
        duplicate_pid_qs.count() +
        mismatched_pid_qs.count() +
        invalid_length_qs.count() +
        not_eligible_qs.count()
    )

    # --- 🔸 Clinical Workflow Checks (existing logic) ---
    six_months_ago = timezone.now().date() - timedelta(days=180)
    treatment_started_6m_ago = screenings.filter(
        diagnosis__tb_treatment=1,
        diagnosis__tb_treatment_date__isnull=False,
        diagnosis__tb_treatment_date__lte=six_months_ago
    )
    pending_tb_outcomes = treatment_started_6m_ago.filter(diagnosis__tb_outcome2__isnull=True)
    pending_tb_outcomes_date = treatment_started_6m_ago.filter(diagnosis__tb_outcome2_date__isnull=True)

    eligible_not_enrolled_count = screenings.filter(eligible=True, enrollment__isnull=True).count()
    missing_clinic_count = screenings.filter(eligible=True, clinic_laboratory__isnull=True).count()
    missing_diagnosis_count = screenings.filter(eligible=True, diagnosis__isnull=True).count()
    missing_regimen_count = screenings.filter(eligible=True, diagnosis__regimen_changed=True)\
                                     .filter(~Q(regimen_changes__isnull=False)).distinct().count()
    pending_outcomes_count = pending_tb_outcomes.count()
    pending_outcomes_date_count = pending_tb_outcomes_date.count()

    report_total = (
        eligible_not_enrolled_count +
        missing_clinic_count +
        missing_diagnosis_count +
        missing_regimen_count +
        pending_outcomes_count +
        pending_outcomes_date_count
    )

    # --- Include Substudy2 for higher roles ---
    if is_zonal_lab or is_admin or is_reviewer or request.user.is_superuser:
        report_total += screenings.filter(
            clinic_laboratory__xpert_mtb_rif_conducted=1,
            clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
            zonal_laboratory__isnull=True
        ).count()

    # --- Return both counts globally ---
    return {
        "report_total": report_total,
        "screening_report_total": screening_report_total,
    }
