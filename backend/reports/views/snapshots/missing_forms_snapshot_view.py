import json
from django.shortcuts import render
from django.db.models import Sum
from django.utils.dateparse import parse_date

from reports.models import MissingFormsDQSnapshot, DataQualitySnapshot
from locations.models import Zone, Site


def missing_forms_trends(request):

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

    # ------------------------------------------------
    # BASE FILTERED QUERYSET
    # ------------------------------------------------

    qs = MissingFormsDQSnapshot.objects.filter(snapshot__in=snapshots)

    if zone_id:
        qs = qs.filter(zone_id=zone_id)

    if site_id:
        qs = qs.filter(site_id=site_id)

    # ------------------------------------------------
    # TRENDS
    # ------------------------------------------------

    dates = []
    enrollment = []
    clinic = []
    diagnosis = []
    regimen = []
    zonal = []
    total_values = []

    for snap in snapshots:

        dates.append(snap.snapshot_date.strftime("%Y-%m-%d"))

        e_val = qs.filter(snapshot=snap).aggregate(
            total=Sum("missing_enrollment")
        )["total"] or 0

        c_val = qs.filter(snapshot=snap).aggregate(
            total=Sum("missing_clinic")
        )["total"] or 0

        d_val = qs.filter(snapshot=snap).aggregate(
            total=Sum("missing_diagnosis")
        )["total"] or 0

        r_val = qs.filter(snapshot=snap).aggregate(
            total=Sum("missing_regimen")
        )["total"] or 0

        z_val = qs.filter(snapshot=snap).aggregate(
            total=Sum("missing_zonal")
        )["total"] or 0

        if form:

            if form == "enrollment":
                c_val = d_val = r_val = z_val = 0

            elif form == "clinic":
                e_val = d_val = r_val = z_val = 0

            elif form == "diagnosis":
                e_val = c_val = r_val = z_val = 0

            elif form == "regimen":
                e_val = c_val = d_val = z_val = 0

            elif form == "zonal":
                e_val = c_val = d_val = r_val = 0

        enrollment.append(e_val)
        clinic.append(c_val)
        diagnosis.append(d_val)
        regimen.append(r_val)
        zonal.append(z_val)

        total_values.append(e_val + c_val + d_val + r_val + z_val)

    # ------------------------------------------------
    # LATEST SNAPSHOT DATA (For Tables and Rankings)
    # ------------------------------------------------
    latest_snapshot = snapshots[-1] if snapshots else None

    # ------------------------------------------------
    # ZONE GROUPED TRENDS
    # ------------------------------------------------

    zone_trends = {}

    for zone in Zone.objects.all():

        zone_data = []

        for snap in snapshots:

            e = qs.filter(snapshot=snap, zone=zone).aggregate(
                total=Sum("missing_enrollment")
            )["total"] or 0

            c = qs.filter(snapshot=snap, zone=zone).aggregate(
                total=Sum("missing_clinic")
            )["total"] or 0

            d = qs.filter(snapshot=snap, zone=zone).aggregate(
                total=Sum("missing_diagnosis")
            )["total"] or 0

            r = qs.filter(snapshot=snap, zone=zone).aggregate(
                total=Sum("missing_regimen")
            )["total"] or 0

            z = qs.filter(snapshot=snap, zone=zone).aggregate(
                total=Sum("missing_zonal")
            )["total"] or 0

            if form:

                if form == "enrollment":
                    c = d = r = z = 0

                elif form == "clinic":
                    e = d = r = z = 0

                elif form == "diagnosis":
                    e = c = r = z = 0

                elif form == "regimen":
                    e = c = d = z = 0

                elif form == "zonal":
                    e = c = d = r = 0

            zone_data.append(e + c + d + r + z)

        zone_trends[zone.name] = zone_data

    # ------------------------------------------------
    # ZONE PERFORMANCE TABLE (Latest Snapshot only)
    # ------------------------------------------------

    zone_performance = []

    for zone in Zone.objects.all():
        
        if not latest_snapshot:
            zone_performance.append({
                "zone": zone.name, "enrollment": 0, "clinic": 0, "diagnosis": 0, 
                "regimen": 0, "zonal": 0, "total": 0
            })
            continue

        e = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_enrollment"))[
            "missing_enrollment__sum"
        ] or 0

        c = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_clinic"))[
            "missing_clinic__sum"
        ] or 0

        d = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_diagnosis"))[
            "missing_diagnosis__sum"
        ] or 0

        r = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_regimen"))[
            "missing_regimen__sum"
        ] or 0

        z = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_zonal"))[
            "missing_zonal__sum"
        ] or 0

        zone_performance.append({
            "zone": zone.name,
            "enrollment": e,
            "clinic": c,
            "diagnosis": d,
            "regimen": r,
            "zonal": z,
            "total": e + c + d + r + z
        })

    zone_total = {
        "enrollment": sum(x["enrollment"] for x in zone_performance),
        "clinic": sum(x["clinic"] for x in zone_performance),
        "diagnosis": sum(x["diagnosis"] for x in zone_performance),
        "regimen": sum(x["regimen"] for x in zone_performance),
        "zonal": sum(x["zonal"] for x in zone_performance),
        "total": sum(x["total"] for x in zone_performance),
    }

    # ------------------------------------------------
    # FACILITY TABLE (Latest Snapshot only)
    # ------------------------------------------------

    facility_table = []

    for site in Site.objects.all():
        
        if not latest_snapshot:
            facility_table.append({
                "site": site.name, "enrollment": 0, "clinic": 0, "diagnosis": 0, 
                "regimen": 0, "zonal": 0, "total": 0
            })
            continue

        e = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_enrollment"))[
            "missing_enrollment__sum"
        ] or 0

        c = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_clinic"))[
            "missing_clinic__sum"
        ] or 0

        d = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_diagnosis"))[
            "missing_diagnosis__sum"
        ] or 0

        r = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_regimen"))[
            "missing_regimen__sum"
        ] or 0

        z = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_zonal"))[
            "missing_zonal__sum"
        ] or 0

        facility_table.append({
            "site": site.name,
            "enrollment": e,
            "clinic": c,
            "diagnosis": d,
            "regimen": r,
            "zonal": z,
            "total": e + c + d + r + z
        })

    facility_table = sorted(
        facility_table,
        key=lambda x: x["total"],
        reverse=True
    )

    facility_total = {
        "enrollment": sum(x["enrollment"] for x in facility_table),
        "clinic": sum(x["clinic"] for x in facility_table),
        "diagnosis": sum(x["diagnosis"] for x in facility_table),
        "regimen": sum(x["regimen"] for x in facility_table),
        "zonal": sum(x["zonal"] for x in facility_table),
        "total": sum(x["total"] for x in facility_table),
    }

    # ------------------------------------------------
    # ZONE FORM BREAKDOWN (Latest Snapshot only)
    # ------------------------------------------------

    zone_form_breakdown = {}

    for zone in Zone.objects.all():

        e = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_enrollment"))["missing_enrollment__sum"] or 0 if latest_snapshot else 0
        c = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_clinic"))["missing_clinic__sum"] or 0 if latest_snapshot else 0
        d = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_diagnosis"))["missing_diagnosis__sum"] or 0 if latest_snapshot else 0
        r = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_regimen"))["missing_regimen__sum"] or 0 if latest_snapshot else 0
        z = qs.filter(zone=zone, snapshot=latest_snapshot).aggregate(Sum("missing_zonal"))["missing_zonal__sum"] or 0 if latest_snapshot else 0

        zone_form_breakdown[zone.name] = {
            "Enrollment": e,
            "Clinic": c,
            "Diagnosis": d,
            "Regimen": r,
            "Zonal Lab": z
        }
        
        
    # ------------------------------------------------
    # SITE FORM BREAKDOWN (Latest Snapshot only)
    # ------------------------------------------------

    site_form_breakdown = {}

    for site in Site.objects.all():

        e = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_enrollment"))["missing_enrollment__sum"] or 0 if latest_snapshot else 0
        c = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_clinic"))["missing_clinic__sum"] or 0 if latest_snapshot else 0
        d = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_diagnosis"))["missing_diagnosis__sum"] or 0 if latest_snapshot else 0
        r = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_regimen"))["missing_regimen__sum"] or 0 if latest_snapshot else 0
        z = qs.filter(site=site, snapshot=latest_snapshot).aggregate(Sum("missing_zonal"))["missing_zonal__sum"] or 0 if latest_snapshot else 0

        site_form_breakdown[site.name] = {
            "Enrollment": e,
            "Clinic": c,
            "Diagnosis": d,
            "Regimen": r,
            "Zonal Lab": z
        }
    
    
    # ------------------------------------------------
    # TOP SITES (Top 10 from latest facility_table)
    # ------------------------------------------------

    top_sites = facility_table[:10]

    site_labels = [x["site"] for x in top_sites]
    site_totals = [x["total"] for x in top_sites]

    # ------------------------------------------------
    # TOP ZONES (From latest zone_performance)
    # ------------------------------------------------

    top_zones = sorted(zone_performance, key=lambda x: x["total"], reverse=True)

    zone_labels = [x["zone"] for x in top_zones]
    zone_totals = [x["total"] for x in top_zones]

    # ------------------------------------------------
    # LATEST COUNTS
    # ------------------------------------------------

    latest_counts = {
        "enrollment": enrollment[-1] if enrollment else 0,
        "clinic": clinic[-1] if clinic else 0,
        "diagnosis": diagnosis[-1] if diagnosis else 0,
        "regimen": regimen[-1] if regimen else 0,
        "zonal": zonal[-1] if zonal else 0,
        "total": total_values[-1] if total_values else 0,
    }

    # ------------------------------------------------
    # CONTEXT
    # ------------------------------------------------

    context = {

        "dates": json.dumps(dates),

        "enrollment": json.dumps(enrollment),
        "clinic": json.dumps(clinic),
        "diagnosis": json.dumps(diagnosis),
        "regimen": json.dumps(regimen),
        "zonal": json.dumps(zonal),

        "total_values": json.dumps(total_values),

        "zone_trends": json.dumps(zone_trends),

        "zone_labels": json.dumps(zone_labels),
        "zone_totals": json.dumps(zone_totals),

        "site_labels": json.dumps(site_labels),
        "site_totals": json.dumps(site_totals),

        "zone_performance": zone_performance,
        "zone_total": zone_total,

        "facility_table": facility_table,
        "facility_total": facility_total,

        "context_zone_forms": json.dumps(zone_form_breakdown),
        "context_site_forms": json.dumps(site_form_breakdown),

        "latest_counts": latest_counts,

        "zones": Zone.objects.all(),
        "sites": Site.objects.filter(zone_id=zone_id) if zone_id else Site.objects.all(),
        "form": form,
        "filters": request.GET,
    }

    return render(
        request,
        "snapshots/missing_forms_trends.html",
        context
    )