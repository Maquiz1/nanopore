from django.shortcuts import render
from django.db.models import Sum
from django.utils.dateparse import parse_date

from reports.models import (
    DataQualitySnapshot,
    ScreeningDQSnapshot,
    EnrollmentDQSnapshot,
    ClinicDQSnapshot,
    DiagnosisDQSnapshot,
    RegimenDQSnapshot,
    ZonalLaboratoryDQSnapshot,
)

from locations.models import Zone, Site


def specific_form_snapshot_view(request):

    zone_id = request.GET.get("zone")
    site_id = request.GET.get("site")

    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))

    snapshots = DataQualitySnapshot.objects.order_by("snapshot_date")

    if start_date:
        snapshots = snapshots.filter(snapshot_date__gte=start_date)

    if end_date:
        snapshots = snapshots.filter(snapshot_date__lte=end_date)

    # Default last 7 snapshots
    if not start_date and not end_date:
        snapshots = snapshots.order_by("-snapshot_date")[:7]
        snapshots = reversed(list(snapshots))

    dates = []
    screening = []
    enrollment = []
    clinic = []
    diagnosis = []
    regimen = []
    zonal = []
    total_values = []

    for snap in snapshots:

        dates.append(snap.snapshot_date.strftime("%Y-%m-%d"))

        s = ScreeningDQSnapshot.objects.filter(snapshot=snap)
        e = EnrollmentDQSnapshot.objects.filter(snapshot=snap)
        c = ClinicDQSnapshot.objects.filter(snapshot=snap)
        d = DiagnosisDQSnapshot.objects.filter(snapshot=snap)
        r = RegimenDQSnapshot.objects.filter(snapshot=snap)
        z = ZonalLaboratoryDQSnapshot.objects.filter(snapshot=snap)

        if zone_id:
            s = s.filter(zone_id=zone_id)
            e = e.filter(zone_id=zone_id)
            c = c.filter(zone_id=zone_id)
            d = d.filter(zone_id=zone_id)
            r = r.filter(zone_id=zone_id)
            z = z.filter(zone_id=zone_id)

        if site_id:
            s = s.filter(site_id=site_id)
            e = e.filter(site_id=site_id)
            c = c.filter(site_id=site_id)
            d = d.filter(site_id=site_id)
            r = r.filter(site_id=site_id)
            z = z.filter(site_id=site_id)

        s_val = s.aggregate(total=Sum("total_issues"))["total"] or 0
        e_val = e.aggregate(total=Sum("total_issues"))["total"] or 0
        c_val = c.aggregate(total=Sum("total_issues"))["total"] or 0
        d_val = d.aggregate(total=Sum("total_issues"))["total"] or 0
        r_val = r.aggregate(total=Sum("total_issues"))["total"] or 0
        z_val = z.aggregate(total=Sum("total_issues"))["total"] or 0

        screening.append(s_val)
        enrollment.append(e_val)
        clinic.append(c_val)
        diagnosis.append(d_val)
        regimen.append(r_val)
        zonal.append(z_val)

        total_values.append(
            s_val + e_val + c_val + d_val + r_val + z_val
        )

    # ------------------------
    # Latest Snapshot Cards
    # ------------------------

    latest_snapshot = DataQualitySnapshot.objects.order_by("-snapshot_date").first()

    latest_counts = {
        "screening": 0,
        "enrollment": 0,
        "clinic": 0,
        "diagnosis": 0,
        "regimen": 0,
        "zonal": 0,
        "total": 0,
    }

    if latest_snapshot:

        s = ScreeningDQSnapshot.objects.filter(snapshot=latest_snapshot).aggregate(total=Sum("total_issues"))["total"] or 0
        e = EnrollmentDQSnapshot.objects.filter(snapshot=latest_snapshot).aggregate(total=Sum("total_issues"))["total"] or 0
        c = ClinicDQSnapshot.objects.filter(snapshot=latest_snapshot).aggregate(total=Sum("total_issues"))["total"] or 0
        d = DiagnosisDQSnapshot.objects.filter(snapshot=latest_snapshot).aggregate(total=Sum("total_issues"))["total"] or 0
        r = RegimenDQSnapshot.objects.filter(snapshot=latest_snapshot).aggregate(total=Sum("total_issues"))["total"] or 0
        z = ZonalLaboratoryDQSnapshot.objects.filter(snapshot=latest_snapshot).aggregate(total=Sum("total_issues"))["total"] or 0

        latest_counts = {
            "screening": s,
            "enrollment": e,
            "clinic": c,
            "diagnosis": d,
            "regimen": r,
            "zonal": z,
            "total": s + e + c + d + r + z,
        }

    # ------------------------
    # Zone Performance Table
    # ------------------------

    zone_qs = ScreeningDQSnapshot.objects.values("zone__name").annotate(
        total=Sum("total_issues")
    ).order_by("-total")

    zone_performance = [
        {
            "zone": x["zone__name"],
            "total": x["total"] or 0
        }
        for x in zone_qs
    ]

    zone_total = {
        "total": sum(x["total"] for x in zone_performance)
    }

    # ------------------------
    # Facility Performance Table
    # ------------------------

    facility_qs = ScreeningDQSnapshot.objects.values("site__name").annotate(
        total=Sum("total_issues")
    ).order_by("-total")

    facility_table = [
        {
            "site": x["site__name"],
            "total": x["total"] or 0
        }
        for x in facility_qs
    ]

    facility_total = {
        "total": sum(x["total"] for x in facility_table)
    }

    # ------------------------
    # Charts
    # ------------------------

    zone_labels = [x["zone"] for x in zone_performance]
    zone_totals = [x["total"] for x in zone_performance]

    site_labels = [x["site"] for x in facility_table[:10]]
    site_totals = [x["total"] for x in facility_table[:10]]

    zones = Zone.objects.order_by("name")

    if zone_id:
        sites = Site.objects.filter(
            district__region__zone_id=zone_id
        ).order_by("name")
    else:
        sites = Site.objects.order_by("name")

    context = {

        "dates": dates,

        "screening": screening,
        "enrollment": enrollment,
        "clinic": clinic,
        "diagnosis": diagnosis,
        "regimen": regimen,
        "zonal": zonal,

        "total_dates": dates,
        "total_values": total_values,

        "zone_labels": zone_labels,
        "zone_totals": zone_totals,

        "site_labels": site_labels,
        "site_totals": site_totals,

        "zone_performance": zone_performance,
        "zone_total": zone_total,

        "facility_table": facility_table,
        "facility_total": facility_total,

        "latest_counts": latest_counts,

        "zones": zones,
        "sites": sites,
        "filters": request.GET
    }

    return render(
        request,
        "snapshots/form_queries_snapshot.html",
        context
    )