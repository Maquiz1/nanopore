# reports/context_processors.py

from django.apps import apps
from django.db.models import Count, Case, When, IntegerField, Q
from utils.permissions import filter_queryset_by_user_role
from utils.roles import get_role_context
from reports.services.zonal_dq_counts import get_zonal_dq_counts

def zonal_report_total(request):
    if not request.user.is_authenticated:
        return {"context_zonal_report_total": 0}

    Zonal = apps.get_model("nanopore", "ZonalLaboratory")
    role_context = get_role_context(request.user)

    qs = Zonal.objects.all()
    qs = filter_queryset_by_user_role(request.user, qs, site_field="screening__site")

    counts_data = get_zonal_dq_counts(qs)
    stats = counts_data["stats"]              # individual counts
    total_issues = counts_data["total_issues"]  # includes duplicates

    return {
        "context_zonal_report_total": total_issues,  # just total issues
        **stats  # optional: counts of individual categories
    }

