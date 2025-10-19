from django.utils import timezone
from datetime import timedelta
from django.apps import apps
from django.db.models import Q
from utils.permissions import filter_queryset_by_user_role


def global_report_total(request):
    """
    Calculate report total for the logged-in user to show in navbar.
    """
    report_total = 0
    if request.user.is_authenticated:
        Screening = apps.get_model('nanopore', 'Screening')
        screenings = Screening.objects.all()
        screenings = filter_queryset_by_user_role(request.user, screenings, site_field="site")
        
        # Optional: count pending outcomes (same logic as your view)
        six_months_ago = timezone.now().date() - timedelta(days=180)
        treatment_started_6m_ago = screenings.filter(
            diagnosis__tb_treatment=1,
            diagnosis__tb_treatment_date__isnull=False,
            diagnosis__tb_treatment_date__lte=six_months_ago
        )
        pending_tb_outcomes = treatment_started_6m_ago.filter(diagnosis__tb_outcome2__isnull=True)
        pending_tb_outcomes_date = treatment_started_6m_ago.filter(diagnosis__tb_outcome2_date__isnull=True)

        # Sum all relevant counts
        report_total = (
            screenings.filter(eligible=True, enrollment__isnull=True).count() +
            screenings.filter(eligible=True, clinic_laboratory__isnull=True).count() +
            screenings.filter(eligible=True, diagnosis__isnull=True).count() +
            screenings.filter(eligible=True, diagnosis__regimen_changed=True)
                     .filter(~Q(regimen_changes__isnull=False)).distinct().count() +
            screenings.filter(
                clinic_laboratory__xpert_mtb_rif_conducted=1,
                clinic_laboratory__xpert_mtb__in=[2, 3, 4, 5, 6],
                zonal_laboratory__isnull=True
            ).count() +
            pending_tb_outcomes.count() +
            pending_tb_outcomes_date.count()
        )

    return {"report_total": report_total}
