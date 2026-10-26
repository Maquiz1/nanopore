from reports.services.zonal_dq import get_zonal_counts
from django.apps import apps


def zonal_report_total(request):
    if not request.user.is_authenticated:
        return {"context_zonal_report_total": 0}

    Zonal = apps.get_model("nanopore", "ZonalLaboratory")

    _, total = get_zonal_counts(request.user, Zonal)

    return {"context_zonal_report_total": total}
