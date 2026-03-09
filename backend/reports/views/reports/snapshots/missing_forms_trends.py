from django.db.models import Sum
from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot
from django.shortcuts import render

def missing_forms_trends(request):

    qs = (
        MissingFormsDQSnapshot.objects
        .values("snapshot__snapshot_date")
        .annotate(total=Sum("total_issues"))
        .order_by("snapshot__snapshot_date")
    )

    dates = [x["snapshot__snapshot_date"].strftime("%Y-%m-%d") for x in qs]
    totals = [x["total"] for x in qs]

    return render(request, "reports/snapshots/missing_forms_trends.html", {
        "dates": dates,
        "totals": totals,
    })
