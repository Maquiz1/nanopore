from django.shortcuts import render
from django.apps import apps
from django.db.models import Sum
from django.utils.dateparse import parse_date

from reports.models import DataQualitySnapshot
from locations.models import Zone, Site


DQ_MODELS = {
    "screening": "ScreeningDQSnapshot",
    "enrollment": "EnrollmentDQSnapshot",
    "clinic": "ClinicDQSnapshot",
    "diagnosis": "DiagnosisDQSnapshot",
    "regimen": "RegimenDQSnapshot",
    "zonal_lab": "ZonalLaboratoryDQSnapshot",
}


def specific_form_snapshot_view(request, form):

    model_name = DQ_MODELS.get(form)

    if not model_name:
        raise ValueError("Invalid form")

    Model = apps.get_model("reports", model_name)

    zone_id = request.GET.get("zone")
    site_id = request.GET.get("site")

    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))

    qs = Model.objects.select_related("snapshot", "zone", "site")

    # Filters
    if zone_id:
        qs = qs.filter(zone_id=zone_id)

    if site_id:
        qs = qs.filter(site_id=site_id)

    if start_date:
        qs = qs.filter(snapshot__snapshot_date__gte=start_date)

    if end_date:
        qs = qs.filter(snapshot__snapshot_date__lte=end_date)

    # Default last 7 snapshots
    if not start_date and not end_date:
        last_snapshots = (
            DataQualitySnapshot.objects
            .order_by("-snapshot_date")
            .values_list("snapshot_date", flat=True)[:7]
        )

        qs = qs.filter(snapshot__snapshot_date__in=list(last_snapshots))

    # ------------------------
    # Trend
    # ------------------------

    trend = (
        qs.values("snapshot__snapshot_date")
        .annotate(total=Sum("total_issues"))
        .order_by("snapshot__snapshot_date")
    )

    dates = [
        x["snapshot__snapshot_date"].strftime("%Y-%m-%d")
        for x in trend
    ]

    totals = [x["total"] or 0 for x in trend]

    # ------------------------
    # Zone ranking
    # ------------------------

    zone_data = (
        qs.values("zone__name")
        .annotate(total=Sum("total_issues"))
        .order_by("-total")
    )

    zone_labels = [x["zone__name"] for x in zone_data]
    zone_totals = [x["total"] or 0 for x in zone_data]

    # ------------------------
    # Facility table
    # ------------------------

    facility_data = (
        qs.values("site__name")
        .annotate(total=Sum("total_issues"))
        .order_by("-total")
    )

    facility_table = [
        {"site": x["site__name"], "total": x["total"] or 0}
        for x in facility_data
    ]

    # ------------------------
    # Dynamic Issue Breakdown
    # ------------------------

    issue_fields = [
        f.name for f in Model._meta.fields
        if f.name.startswith("missing_")
        or f.name.startswith("duplicate_")
        or f.name.startswith("invalid_")
        or f.name.startswith("pending_")
    ]

    breakdown = qs.aggregate(**{
        field: Sum(field)
        for field in issue_fields
    })

    zones = Zone.objects.order_by("name")

    if zone_id:
        sites = Site.objects.filter(
            district__region__zone_id=zone_id
        ).order_by("name")
    else:
        sites = Site.objects.order_by("name")

    context = {

        "form": form,

        "dates": dates,
        "totals": totals,

        "zone_labels": zone_labels,
        "zone_totals": zone_totals,

        "facility_table": facility_table,

        "breakdown": breakdown,

        "zones": zones,
        "sites": sites,

        "filters": request.GET,
    }

    return render(
        request,
        "reports/snapshots/form_queries_snapshot.html",
        context
    )