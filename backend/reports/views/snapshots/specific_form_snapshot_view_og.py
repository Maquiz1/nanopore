import json
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
    form = request.GET.get("form")

    start_date = parse_date(request.GET.get("start_date", ""))
    end_date = parse_date(request.GET.get("end_date", ""))

    snapshots = DataQualitySnapshot.objects.order_by("snapshot_date")

    if start_date:
        snapshots = snapshots.filter(snapshot_date__gte=start_date)


    if end_date:
        snapshots = snapshots.filter(snapshot_date__lte=end_date)

    if not start_date and not end_date:
        snapshots = list(DataQualitySnapshot.objects.order_by("-snapshot_date")[:7])
        snapshots.reverse()
    else:
        snapshots = list(snapshots)

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

        total_values.append(s_val + e_val + c_val + d_val + r_val + z_val)

    # TOP FORMS
    top_forms = {
        "Screening": sum(screening),
        "Enrollment": sum(enrollment),
        "Clinic": sum(clinic),
        "Diagnosis": sum(diagnosis),
        "Regimen": sum(regimen),
        "Zonal Lab": sum(zonal),
    }

    top_forms_sorted = sorted(top_forms.items(), key=lambda x: x[1], reverse=True)

    top_form_labels = [x[0] for x in top_forms_sorted]
    top_form_totals = [x[1] for x in top_forms_sorted]

    

    # =====================
    # Zone Trends
    # =====================

    zone_trends = {}

    zones = Zone.objects.all()

    for zone in zones:

        zone_data = []

        for snap in snapshots:

            s = ScreeningDQSnapshot.objects.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            e = EnrollmentDQSnapshot.objects.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            c = ClinicDQSnapshot.objects.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            d = DiagnosisDQSnapshot.objects.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            r = RegimenDQSnapshot.objects.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            z = ZonalLaboratoryDQSnapshot.objects.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0

            zone_total = s + e + c + d + r + z

            zone_data.append(zone_total)

        zone_trends[zone.name] = zone_data
        
    # =====================
    # Zone Performance Table
    # =====================

    zone_performance = []

    for zone in zones:

        s = (
            ScreeningDQSnapshot.objects.filter(zone=zone).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        e = (
            EnrollmentDQSnapshot.objects.filter(zone=zone).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        c = (
            ClinicDQSnapshot.objects.filter(zone=zone).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        d = (
            DiagnosisDQSnapshot.objects.filter(zone=zone).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        r = (
            RegimenDQSnapshot.objects.filter(zone=zone).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        z = (
            ZonalLaboratoryDQSnapshot.objects.filter(zone=zone).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )

        zone_performance.append(
            {
                "zone": zone.name,
                "screening": s,
                "enrollment": e,
                "clinic": c,
                "diagnosis": d,
                "regimen": r,
                "zonal": z,
                "total": s + e + c + d + r + z,
            }
        )

    zone_total = {
        "screening": sum(x["screening"] for x in zone_performance),
        "enrollment": sum(x["enrollment"] for x in zone_performance),
        "clinic": sum(x["clinic"] for x in zone_performance),
        "diagnosis": sum(x["diagnosis"] for x in zone_performance),
        "regimen": sum(x["regimen"] for x in zone_performance),
        "zonal": sum(x["zonal"] for x in zone_performance),
        "total": sum(x["total"] for x in zone_performance),
    }


    # TOP ZONES

    top_zones = sorted(
        zone_performance,
        key=lambda x: x["total"],
        reverse=True
    )

    top_zone_labels = [x["zone"] for x in top_zones]
    top_zone_totals = [x["total"] for x in top_zones]
    
    # =====================
    # Facility Performance Table
    # =====================

    facility_table = []

    for site in Site.objects.all():

        s = (
            ScreeningDQSnapshot.objects.filter(site=site).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        e = (
            EnrollmentDQSnapshot.objects.filter(site=site).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        c = (
            ClinicDQSnapshot.objects.filter(site=site).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        d = (
            DiagnosisDQSnapshot.objects.filter(site=site).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        r = (
            RegimenDQSnapshot.objects.filter(site=site).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )
        z = (
            ZonalLaboratoryDQSnapshot.objects.filter(site=site).aggregate(
                total=Sum("total_issues")
            )["total"]
            or 0
        )

        facility_table.append(
            {
                "site": site.name,
                "screening": s,
                "enrollment": e,
                "clinic": c,
                "diagnosis": d,
                "regimen": r,
                "zonal": z,
                "total": s + e + c + d + r + z,
            }
        )

    facility_total = {
        "screening": sum(x["screening"] for x in facility_table),
        "enrollment": sum(x["enrollment"] for x in facility_table),
        "clinic": sum(x["clinic"] for x in facility_table),
        "diagnosis": sum(x["diagnosis"] for x in facility_table),
        "regimen": sum(x["regimen"] for x in facility_table),
        "zonal": sum(x["zonal"] for x in facility_table),
        "total": sum(x["total"] for x in facility_table),
    }

    # =====================
    # Top Sites Chart
    # =====================

    top_sites_qs = (
        ScreeningDQSnapshot.objects.values("site__name")
        .annotate(total=Sum("total_issues"))
        .order_by("-total")
    )

    top_site_labels = [x["site__name"] for x in top_sites_qs]
    top_site_totals = [x["total"] or 0 for x in top_sites_qs]

    context = {
        "dates": json.dumps(dates),

        "screening": json.dumps(screening),
        "enrollment": json.dumps(enrollment),
        "clinic": json.dumps(clinic),
        "diagnosis": json.dumps(diagnosis),
        "regimen": json.dumps(regimen),
        "zonal": json.dumps(zonal),

        "total_values": json.dumps(total_values),

        # Charts
        "zone_trends": json.dumps(zone_trends),
        "top_site_labels": json.dumps(top_site_labels),
        "top_site_totals": json.dumps(top_site_totals),
        
        "top_zone_labels": json.dumps(top_zone_labels),
        "top_zone_totals": json.dumps(top_zone_totals),

        "top_form_labels": json.dumps(top_form_labels),
        "top_form_totals": json.dumps(top_form_totals),

        # Tables
        "zone_performance": zone_performance,
        "zone_total": zone_total,

        "facility_table": facility_table,
        "facility_total": facility_total,

        # Cards
        "latest_counts": {
            "screening": screening[-1] if screening else 0,
            "enrollment": enrollment[-1] if enrollment else 0,
            "clinic": clinic[-1] if clinic else 0,
            "diagnosis": diagnosis[-1] if diagnosis else 0,
            "regimen": regimen[-1] if regimen else 0,
            "zonal": zonal[-1] if zonal else 0,
        },

        # Filters
        "zones": Zone.objects.all(),
        "sites": Site.objects.all(),
        "form": form,
        "filters": request.GET,
    }
    
    return render(request, "snapshots/form_queries_snapshot.html", context)
