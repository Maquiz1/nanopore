# reports/context_processors/form_queries/zonal_laboratory_context.py
from django.apps import apps
from reports.services.zonal_dq import get_ctrl_isolate_counts, get_zonal_counts
from reports.services.zonal_dq.ctrl import get_ctrl_dar_counts
from utils import access
from utils.access import can_see_queries
from reports.context_processors.cache_helpers import cached_context

@cached_context(ttl=300)
def zonal_report_total(request):
    if not request.user.is_authenticated:
        return {"context_zonal_report_total": 0, "context_ctrl_isolates_report_total": 0, "context_ctrl_dar_work_total": 0}

    Zonal = apps.get_model("nanopore", "ZonalLaboratory")

    stats, total_issues = get_zonal_counts(request.user, Zonal)
    can_see_ctrl = can_see_queries(request.user, access.CTRL_ISOLATES)

    return {
        # CTRL work (Dar): Nanopore and LPA checkbox queries, counted here and not under EDCS/TBLIS
        "context_ctrl_dar_work_total": sum(get_ctrl_dar_counts(request.user).values()) if can_see_ctrl else 0,
        "context_zonal_report_total": total_issues,  # just total issues
        "context_ctrl_isolates_report_total": (
            sum(get_ctrl_isolate_counts(request.user).values())
            if can_see_ctrl else 0
        ),
        **stats  # optional: counts of individual categories
    }
