from reports.services.regimen_dq import get_regimen_queryset, get_regimen_dq
from reports.context_processors.cache_helpers import cached_context


@cached_context(ttl=300)
def regimen_report_total(request):
    if not request.user.is_authenticated:
        return {"context_regimen_report_total": 0}

    qs = get_regimen_queryset(request.user)
    _, totals = get_regimen_dq(qs)

    return {
        "context_regimen_report_total": totals["regimen_report_total"]
    }
