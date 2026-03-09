from django.shortcuts import render
from django.db.models import Sum
from reports.models import DataQualitySnapshot, MissingFormsDQSnapshot


def missing_forms_dashboard(request):

    latest_snapshot = DataQualitySnapshot.objects.order_by("-snapshot_date").first()

    rows = []
    totals = {}

    if latest_snapshot:
        rows = (
            MissingFormsDQSnapshot.objects
            .filter(snapshot=latest_snapshot)
            .select_related("zone", "site")
            .order_by("zone__name", "site__name")
        )

        totals = rows.aggregate(
            missing_enrollment=Sum("missing_enrollment"),
            missing_clinic=Sum("missing_clinic"),
            missing_diagnosis=Sum("missing_diagnosis"),
            missing_regimen=Sum("missing_regimen"),
            missing_zonal=Sum("missing_zonal"),
            total_issues=Sum("total_issues"),
        )

    return render(request, "snapshots/missing_forms_dashboard.html", {
        "snapshot": latest_snapshot,
        "rows": rows,
        "totals": totals,
    })
