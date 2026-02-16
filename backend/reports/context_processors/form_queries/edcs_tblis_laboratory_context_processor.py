from reports.services.zonal_dq import get_zonal_dq
from django.apps import apps


def edcs_tblis_report_total(request):
    if not request.user.is_authenticated:
        return {"context_edcs_tblis_report_total": 0}

    Zonal = apps.get_model("nanopore", "EdcsTblisZonal")

    _, _, total, _ = get_zonal_dq(request.user, Zonal)

    return {"context_edcs_tblis_report_total": total}
