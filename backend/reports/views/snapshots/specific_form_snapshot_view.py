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

    # ------------------------------------------------
    # BASE FILTERED QUERYSETS
    # ------------------------------------------------

    screening_qs = ScreeningDQSnapshot.objects.filter(snapshot__in=snapshots)
    enrollment_qs = EnrollmentDQSnapshot.objects.filter(snapshot__in=snapshots)
    clinic_qs = ClinicDQSnapshot.objects.filter(snapshot__in=snapshots)
    diagnosis_qs = DiagnosisDQSnapshot.objects.filter(snapshot__in=snapshots)
    regimen_qs = RegimenDQSnapshot.objects.filter(snapshot__in=snapshots)
    zonal_qs = ZonalLaboratoryDQSnapshot.objects.filter(snapshot__in=snapshots)

    if zone_id:
        screening_qs = screening_qs.filter(zone_id=zone_id)
        enrollment_qs = enrollment_qs.filter(zone_id=zone_id)
        clinic_qs = clinic_qs.filter(zone_id=zone_id)
        diagnosis_qs = diagnosis_qs.filter(zone_id=zone_id)
        regimen_qs = regimen_qs.filter(zone_id=zone_id)
        zonal_qs = zonal_qs.filter(zone_id=zone_id)

    if site_id:
        screening_qs = screening_qs.filter(site_id=site_id)
        enrollment_qs = enrollment_qs.filter(site_id=site_id)
        clinic_qs = clinic_qs.filter(site_id=site_id)
        diagnosis_qs = diagnosis_qs.filter(site_id=site_id)
        regimen_qs = regimen_qs.filter(site_id=site_id)
        zonal_qs = zonal_qs.filter(site_id=site_id)

    # ------------------------------------------------
    # TRENDS
    # ------------------------------------------------

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

        s_val = screening_qs.filter(snapshot=snap).aggregate(total=Sum("total_issues"))["total"] or 0
        e_val = enrollment_qs.filter(snapshot=snap).aggregate(total=Sum("total_issues"))["total"] or 0
        c_val = clinic_qs.filter(snapshot=snap).aggregate(total=Sum("total_issues"))["total"] or 0
        d_val = diagnosis_qs.filter(snapshot=snap).aggregate(total=Sum("total_issues"))["total"] or 0
        r_val = regimen_qs.filter(snapshot=snap).aggregate(total=Sum("total_issues"))["total"] or 0
        z_val = zonal_qs.filter(snapshot=snap).aggregate(total=Sum("total_issues"))["total"] or 0

        # Apply form filter
        if form == "screening":
            e_val = c_val = d_val = r_val = z_val = 0
        elif form == "enrollment":
            s_val = c_val = d_val = r_val = z_val = 0
        elif form == "clinic":
            s_val = e_val = d_val = r_val = z_val = 0
        elif form == "diagnosis":
            s_val = e_val = c_val = r_val = z_val = 0
        elif form == "regimen":
            s_val = e_val = c_val = d_val = z_val = 0
        elif form == "zonal":
            s_val = e_val = c_val = d_val = r_val = 0

        screening.append(s_val)
        enrollment.append(e_val)
        clinic.append(c_val)
        diagnosis.append(d_val)
        regimen.append(r_val)
        zonal.append(z_val)

        total_values.append(s_val + e_val + c_val + d_val + r_val + z_val)

    # ------------------------------------------------
    # ZONE TRENDS
    # ------------------------------------------------

    zone_trends = {}

    for zone in Zone.objects.all():

        zone_data = []

        for snap in snapshots:

            s = screening_qs.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            e = enrollment_qs.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            c = clinic_qs.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            d = diagnosis_qs.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            r = regimen_qs.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
            z = zonal_qs.filter(snapshot=snap, zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0

            zone_data.append(s + e + c + d + r + z)

        zone_trends[zone.name] = zone_data

    # ------------------------------------------------
    # ZONE TABLE
    # ------------------------------------------------

    zone_performance = []

    for zone in Zone.objects.all():

        s = screening_qs.filter(zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
        e = enrollment_qs.filter(zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
        c = clinic_qs.filter(zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
        d = diagnosis_qs.filter(zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
        r = regimen_qs.filter(zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0
        z = zonal_qs.filter(zone=zone).aggregate(total=Sum("total_issues"))["total"] or 0

        zone_performance.append({
            "zone": zone.name,
            "screening": s,
            "enrollment": e,
            "clinic": c,
            "diagnosis": d,
            "regimen": r,
            "zonal": z,
            "total": s + e + c + d + r + z
        })

    zone_total = {
        "screening": sum(x["screening"] for x in zone_performance),
        "enrollment": sum(x["enrollment"] for x in zone_performance),
        "clinic": sum(x["clinic"] for x in zone_performance),
        "diagnosis": sum(x["diagnosis"] for x in zone_performance),
        "regimen": sum(x["regimen"] for x in zone_performance),
        "zonal": sum(x["zonal"] for x in zone_performance),
        "total": sum(x["total"] for x in zone_performance),
    }

    # ------------------------------------------------
    # FACILITY TABLE
    # ------------------------------------------------

    facility_table = []

    for site in Site.objects.all():

        s = screening_qs.filter(site=site).aggregate(total=Sum("total_issues"))["total"] or 0
        e = enrollment_qs.filter(site=site).aggregate(total=Sum("total_issues"))["total"] or 0
        c = clinic_qs.filter(site=site).aggregate(total=Sum("total_issues"))["total"] or 0
        d = diagnosis_qs.filter(site=site).aggregate(total=Sum("total_issues"))["total"] or 0
        r = regimen_qs.filter(site=site).aggregate(total=Sum("total_issues"))["total"] or 0
        z = zonal_qs.filter(site=site).aggregate(total=Sum("total_issues"))["total"] or 0

        facility_table.append({
            "site": site.name,
            "screening": s,
            "enrollment": e,
            "clinic": c,
            "diagnosis": d,
            "regimen": r,
            "zonal": z,
            "total": s + e + c + d + r + z
        })

    facility_total = {
        "screening": sum(x["screening"] for x in facility_table),
        "enrollment": sum(x["enrollment"] for x in facility_table),
        "clinic": sum(x["clinic"] for x in facility_table),
        "diagnosis": sum(x["diagnosis"] for x in facility_table),
        "regimen": sum(x["regimen"] for x in facility_table),
        "zonal": sum(x["zonal"] for x in facility_table),
        "total": sum(x["total"] for x in facility_table),
    }

    # ------------------------------------------------
    # TOP SITES
    # ------------------------------------------------

    top_sites_qs = screening_qs.values("site__name").annotate(total=Sum("total_issues")).order_by("-total")

    top_site_labels = [x["site__name"] for x in top_sites_qs]
    top_site_totals = [x["total"] or 0 for x in top_sites_qs]

    # ------------------------------------------------
    # TOP ZONES
    # ------------------------------------------------

    top_zones = sorted(zone_performance, key=lambda x: x["total"], reverse=True)

    top_zone_labels = [x["zone"] for x in top_zones]
    top_zone_totals = [x["total"] for x in top_zones]

    # ------------------------------------------------
    # TOP FORMS
    # ------------------------------------------------

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

    context = {
        "dates": json.dumps(dates),

        "screening": json.dumps(screening),
        "enrollment": json.dumps(enrollment),
        "clinic": json.dumps(clinic),
        "diagnosis": json.dumps(diagnosis),
        "regimen": json.dumps(regimen),
        "zonal": json.dumps(zonal),

        "total_values": json.dumps(total_values),

        "zone_trends": json.dumps(zone_trends),

        "top_site_labels": json.dumps(top_site_labels),
        "top_site_totals": json.dumps(top_site_totals),

        "top_zone_labels": json.dumps(top_zone_labels),
        "top_zone_totals": json.dumps(top_zone_totals),

        "top_form_labels": json.dumps(top_form_labels),
        "top_form_totals": json.dumps(top_form_totals),

        "zone_performance": zone_performance,
        "zone_total": zone_total,

        "facility_table": facility_table,
        "facility_total": facility_total,

        "latest_counts": {
            "screening": screening[-1] if screening else 0,
            "enrollment": enrollment[-1] if enrollment else 0,
            "clinic": clinic[-1] if clinic else 0,
            "diagnosis": diagnosis[-1] if diagnosis else 0,
            "regimen": regimen[-1] if regimen else 0,
            "zonal": zonal[-1] if zonal else 0,
        },

        "zones": Zone.objects.all(),
        "sites": Site.objects.filter(zone_id=zone_id) if zone_id else Site.objects.all(),
        "form": form,
        "filters": request.GET,
    }

    return render(request, "snapshots/form_queries_snapshot.html", context)