from reports.services.regimen_dq import get_regimen_queryset, get_regimen_dq


def regimen_report_total(request):
    if not request.user.is_authenticated:
        return {"context_regimen_report_total": 0}

    qs = get_regimen_queryset(request.user)
    _, totals = get_regimen_dq(qs)

    return {
        "context_regimen_report_total": totals["regimen_report_total"]
    }
