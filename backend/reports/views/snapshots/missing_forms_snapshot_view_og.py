import json
from django.shortcuts import render
from django.db.models import Sum
from django.utils.dateparse import parse_date

from reports.models import MissingFormsDQSnapshot, DataQualitySnapshot
from locations.models import Zone, Site


def missing_forms_trends(request):

    zone_id = request.GET.get("zone")
    site_id = request.GET.get("site")
    form_type = request.GET.get("form")

    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))

    # ------------------------------------------------
    # Base Queryset
    # ------------------------------------------------

    qs = MissingFormsDQSnapshot.objects.select_related(
        "snapshot", "zone", "site"
    )

    # ------------------------------------------------
    # Filters
    # ------------------------------------------------

    if zone_id:
        qs = qs.filter(zone_id=zone_id)

    if site_id:
        qs = qs.filter(site_id=site_id)

    if start_date:
        qs = qs.filter(snapshot__snapshot_date__gte=start_date)

    if end_date:
        qs = qs.filter(snapshot__snapshot_date__lte=end_date)

    # ------------------------------------------------
    # Default Last 7 Days
    # ------------------------------------------------

    if not start_date and not end_date:
        last_dates = (
            DataQualitySnapshot.objects
            .order_by("-snapshot_date")
            .values_list("snapshot_date", flat=True)[:7]
        )

        qs = qs.filter(snapshot__snapshot_date__in=list(last_dates))

    # ------------------------------------------------
    # Total Trend
    # ------------------------------------------------

    total_trend = (
        qs.values("snapshot__snapshot_date")
        .annotate(total=Sum("total_issues"))
        .order_by("snapshot__snapshot_date")
    )

    total_dates = [
        x["snapshot__snapshot_date"].strftime("%Y-%m-%d")
        for x in total_trend
    ]

    total_values = [x["total"] or 0 for x in total_trend]

    # ------------------------------------------------
    # Detailed Trends
    # ------------------------------------------------

    trend_qs = (
        qs.values("snapshot__snapshot_date")
        .annotate(
            enrollment=Sum("missing_enrollment"),
            clinic=Sum("missing_clinic"),
            diagnosis=Sum("missing_diagnosis"),
            regimen=Sum("missing_regimen"),
            zonal=Sum("missing_zonal"),
        )
        .order_by("snapshot__snapshot_date")
    )

    dates = [x["snapshot__snapshot_date"].strftime("%Y-%m-%d") for x in trend_qs]

    enrollment = [x["enrollment"] or 0 for x in trend_qs]
    clinic = [x["clinic"] or 0 for x in trend_qs]
    diagnosis = [x["diagnosis"] or 0 for x in trend_qs]
    regimen = [x["regimen"] or 0 for x in trend_qs]
    zonal = [x["zonal"] or 0 for x in trend_qs]

    # ------------------------------------------------
    # Zone Ranking Chart
    # ------------------------------------------------

    zone_data = (
        qs.values("zone__name")
        .annotate(total=Sum("total_issues"))
        .order_by("-total")
    )

    zone_labels = [x["zone__name"] for x in zone_data]
    zone_totals = [x["total"] or 0 for x in zone_data]

    # ------------------------------------------------
    # Site Ranking Chart
    # ------------------------------------------------

    site_data = (
        qs.values("site__name")
        .annotate(total=Sum("total_issues"))
        .order_by("-total")[:10]
    )

    site_labels = [x["site__name"] for x in site_data]
    site_totals = [x["total"] or 0 for x in site_data]

    # ------------------------------------------------
    # Latest Snapshot Cards
    # ------------------------------------------------

    latest_snapshot = DataQualitySnapshot.objects.order_by("-snapshot_date").first()

    latest_counts = {
        "enrollment": 0,
        "clinic": 0,
        "diagnosis": 0,
        "regimen": 0,
        "zonal": 0,
        "total": 0,
    }

    if latest_snapshot:

        latest_qs = qs.filter(snapshot=latest_snapshot)

        latest_counts = latest_qs.aggregate(
            enrollment=Sum("missing_enrollment"),
            clinic=Sum("missing_clinic"),
            diagnosis=Sum("missing_diagnosis"),
            regimen=Sum("missing_regimen"),
            zonal=Sum("missing_zonal"),
            total=Sum("total_issues"),
        )

    # ------------------------------------------------
    # Facility Performance Table
    # ------------------------------------------------

    facility_qs = (
        qs.values("site__name")
        .annotate(
            enrollment=Sum("missing_enrollment"),
            clinic=Sum("missing_clinic"),
            diagnosis=Sum("missing_diagnosis"),
            regimen=Sum("missing_regimen"),
            zonal=Sum("missing_zonal"),
            total=Sum("total_issues"),
        )
        .order_by("-total")
    )

    facility_table = [
        {
            "site": x["site__name"],
            "enrollment": x["enrollment"] or 0,
            "clinic": x["clinic"] or 0,
            "diagnosis": x["diagnosis"] or 0,
            "regimen": x["regimen"] or 0,
            "zonal": x["zonal"] or 0,
            "total": x["total"] or 0,
        }
        for x in facility_qs
    ]

    facility_total = {
        "enrollment": sum(x["enrollment"] for x in facility_table),
        "clinic": sum(x["clinic"] for x in facility_table),
        "diagnosis": sum(x["diagnosis"] for x in facility_table),
        "regimen": sum(x["regimen"] for x in facility_table),
        "zonal": sum(x["zonal"] for x in facility_table),
        "total": sum(x["total"] for x in facility_table),
    }

    # ------------------------------------------------
    # Zone Performance Table
    # ------------------------------------------------

    zone_perf_qs = (
        qs.values("zone__name")
        .annotate(
            enrollment=Sum("missing_enrollment"),
            clinic=Sum("missing_clinic"),
            diagnosis=Sum("missing_diagnosis"),
            regimen=Sum("missing_regimen"),
            zonal=Sum("missing_zonal"),
            total=Sum("total_issues"),
        )
        .order_by("-total")
    )

    zone_performance = [
        {
            "zone": x["zone__name"],
            "enrollment": x["enrollment"] or 0,
            "clinic": x["clinic"] or 0,
            "diagnosis": x["diagnosis"] or 0,
            "regimen": x["regimen"] or 0,
            "zonal": x["zonal"] or 0,
            "total": x["total"] or 0,
        }
        for x in zone_perf_qs
    ]

    zone_total = {
        "enrollment": sum(x["enrollment"] for x in zone_performance),
        "clinic": sum(x["clinic"] for x in zone_performance),
        "diagnosis": sum(x["diagnosis"] for x in zone_performance),
        "regimen": sum(x["regimen"] for x in zone_performance),
        "zonal": sum(x["zonal"] for x in zone_performance),
        "total": sum(x["total"] for x in zone_performance),
    }

    zones = Zone.objects.order_by("name")

    if zone_id:
        sites = Site.objects.filter(zone_id=zone_id).order_by("name")
    else:
        sites = Site.objects.order_by("name")

    # ------------------------------------------------
    # Context
    # ------------------------------------------------

    context = {

        "total_dates": json.dumps(total_dates),
        "total_values": json.dumps(total_values),

        "dates": json.dumps(dates),
        "enrollment": json.dumps(enrollment),
        "clinic": json.dumps(clinic),
        "diagnosis": json.dumps(diagnosis),
        "regimen": json.dumps(regimen),
        "zonal": json.dumps(zonal),

        "zone_labels": json.dumps(zone_labels),
        "zone_totals": json.dumps(zone_totals),

        "site_labels": json.dumps(site_labels),
        "site_totals": json.dumps(site_totals),

        "facility_table": facility_table,
        "facility_total": facility_total,

        "zone_performance": zone_performance,
        "zone_total": zone_total,

        "latest_counts": latest_counts,

        "zones": zones,
        "sites": sites,
        "filters": request.GET
    }

    return render(
        request,
        "snapshots/missing_forms_trends.html",
        context
    )