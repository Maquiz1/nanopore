from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context


def forms_report_total(request):
    """
    Returns clinical workflow / form completion issues count for navbar.
    Includes missing enrollments, labs, diagnosis, regimen, and pending TB outcomes.
    """
    forms_report_total = 0

    if not request.user.is_authenticated:
        return {"forms_report_total": forms_report_total}

    Screening = apps.get_model('nanopore', 'Screening')
    screenings = Screening.objects.all()
    screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")

    role_context = get_role_context(request.user)
    is_zonal_lab = role_context.get("is_zonal_lab", False)
    is_admin = role_context.get("is_admin", False)
    is_reviewer = role_context.get("is_reviewer", False)

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

    forms_report_total = (
        eligible_not_enrolled_count +
        missing_clinic_count +
        missing_diagnosis_count +
        missing_regimen_count +
        pending_outcomes_count +
        pending_outcomes_date_count
    )

    # --- Include Substudy2 for higher roles ---
    if is_zonal_lab or is_admin or is_reviewer or request.user.is_superuser:
        forms_report_total += screenings.filter(
            clinic_laboratory__xpert_mtb_rif_conducted=1,
            clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
            zonal_laboratory__isnull=True
        ).count()

    return {"forms_report_total": forms_report_total}
