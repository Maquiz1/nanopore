from reports.services.zonal_dq import get_zonal_counts
from django.apps import apps
from reports.context_processors.cache_helpers import cached_context


@cached_context(ttl=300)
def edcs_tblis_report_total(request):
    if not request.user.is_authenticated:
        return {"context_edcs_tblis_report_total": 0}

    Zonal = apps.get_model("nanopore", "EdcsTblisZonal")

    _, total = get_zonal_counts(request.user, Zonal)

    return {"context_edcs_tblis_report_total": total}
