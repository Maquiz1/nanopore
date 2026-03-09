from django.shortcuts import render
from django.db.models import Sum

from reports.models import (
    DataQualitySnapshot,
    ScreeningDQSnapshot,
    EnrollmentDQSnapshot,
    ClinicDQSnapshot,
    DiagnosisDQSnapshot,
    RegimenDQSnapshot,
    ZonalLaboratoryDQSnapshot,
)


def specific_form_snapshot_view(request):

    snapshots = DataQualitySnapshot.objects.order_by("snapshot_date")

    dates = []
    screening = []
    enrollment = []
    clinic = []
    diagnosis = []
    regimen = []
    zonal = []

    for snap in snapshots:

        dates.append(snap.snapshot_date.strftime("%Y-%m-%d"))

        screening.append(
            ScreeningDQSnapshot.objects.filter(snapshot=snap)
            .aggregate(total=Sum("total_issues"))["total"] or 0
        )

        enrollment.append(
            EnrollmentDQSnapshot.objects.filter(snapshot=snap)
            .aggregate(total=Sum("total_issues"))["total"] or 0
        )

        clinic.append(
            ClinicDQSnapshot.objects.filter(snapshot=snap)
            .aggregate(total=Sum("total_issues"))["total"] or 0
        )

        diagnosis.append(
            DiagnosisDQSnapshot.objects.filter(snapshot=snap)
            .aggregate(total=Sum("total_issues"))["total"] or 0
        )

        regimen.append(
            RegimenDQSnapshot.objects.filter(snapshot=snap)
            .aggregate(total=Sum("total_issues"))["total"] or 0
        )

        zonal.append(
            ZonalLaboratoryDQSnapshot.objects.filter(snapshot=snap)
            .aggregate(total=Sum("total_issues"))["total"] or 0
        )

    context = {
        "dates": dates,
        "screening": screening,
        "enrollment": enrollment,
        "clinic": clinic,
        "diagnosis": diagnosis,
        "regimen": regimen,
        "zonal": zonal,
    }

    return render(
        request,
        "snapshots/form_queries_snapshot.html",
        context
    )