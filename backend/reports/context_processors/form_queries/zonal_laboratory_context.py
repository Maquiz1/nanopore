# reports/context_processors/form_queries/zonal_laboratory_context.py
from django.apps import apps
from reports.services.zonal_dq import get_zonal_dq
from reports.context_processors.cache_helpers import cached_context

@cached_context(ttl=300)
def zonal_report_total(request):
    if not request.user.is_authenticated:
        return {"context_zonal_report_total": 0}

    Zonal = apps.get_model("nanopore", "ZonalLaboratory")

    _, stats, total_issues, _ = get_zonal_dq(request.user, Zonal)

    return {
        "context_zonal_report_total": total_issues,  # just total issues
        **stats  # optional: counts of individual categories
    }
