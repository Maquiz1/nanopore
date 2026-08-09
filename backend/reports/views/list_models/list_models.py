from django.shortcuts import render
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

# Import your main models
from nanopore.models.screening import Screening
from nanopore.models.enrollment import Enrollment
# Import other models if needed
from nanopore.models.clinic_lab import ClinicLaboratory
from nanopore.models.diagnosis import Diagnosis
from nanopore.models.zonal_lab import ZonalLaboratory
from nanopore.models.regimen_changes import RegimenChanges

from nanopore.models.edcs_tblis_zonal import EdcsTblisZonal


# @staff_member_required
def list_models_view(request):
    total_screenings = Screening.objects.count()
    models_list = [
        {
            "name": "Screening",
            "count": total_screenings,
            "description": "All Screening records",
            "download_url": reverse("reports:download_model_data", args=["Screening"]),
            "labels_url": reverse("reports:download_model_labels", args=["Screening"]),
            "fields_url": reverse("reports:download_model_fields", args=["Screening"]),
        },
        {
            "name": "Enrollment",
            "count": Enrollment.objects.count(),
            "description": "All Enrollment records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["Enrollment"]),
            "labels_url": reverse("reports:download_model_labels", args=["Enrollment"]),
            "fields_url": reverse("reports:download_model_fields", args=["Enrollment"]),
        },
        {
            "name": "ClinicLaboratory",
            "count": ClinicLaboratory.objects.count(),
            "description": "All ClinicLaboratory records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["ClinicLaboratory"]),
            "labels_url": reverse("reports:download_model_labels", args=["ClinicLaboratory"]),
            "fields_url": reverse("reports:download_model_fields", args=["ClinicLaboratory"]),
        },
        {
            "name": "Diagnosis",
            "count": Diagnosis.objects.count(),
            "description": "All Diagnosis records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["Diagnosis"]),
            "labels_url": reverse("reports:download_model_labels", args=["Diagnosis"]),
            "fields_url": reverse("reports:download_model_fields", args=["Diagnosis"]),
        },
        {
            "name": "ZonalLaboratory",
            "count": ZonalLaboratory.objects.count(),
            "description": "All ZonalLaboratory records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["ZonalLaboratory"]),
            "labels_url": reverse("reports:download_model_labels", args=["ZonalLaboratory"]),
            "fields_url": reverse("reports:download_model_fields", args=["ZonalLaboratory"]),
        },
        {
            "name": "RegimenChanges",
            "count": RegimenChanges.objects.count(),
            "description": "All RegimenChanges records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["RegimenChanges"]),
            "labels_url": reverse("reports:download_model_labels", args=["RegimenChanges"]),
            "fields_url": reverse("reports:download_model_fields", args=["RegimenChanges"]),
        },
        {
            "name": "EdcsTblisZonal",
            "count": _get_edcs_tblis_count(),
            "description": "CTRL zone (merged from TBLIS) + all other zones",
            "download_url": reverse("reports:download_model_data", args=["EdcsTblisZonal"]),
            "labels_url": reverse("reports:download_model_labels", args=["EdcsTblisZonal"]),
            "fields_url": reverse("reports:download_model_fields", args=["EdcsTblisZonal"]),
        },
    ]
    return render(
        request, "reports/data_export/list_models.html", {
            "models_list": models_list,
            "total_screenings": total_screenings
        }
    )


def _get_edcs_tblis_count():
    """
    EdcsTblisZonal count uses two rules:
      - CTRL zone (PID prefixes DF_TZ_SS2_14 to DF_TZ_SS2_19):
            count only records that were successfully merged from the *latest* TBLIS upload
            (i.e., their unique_lab_no appears in TblisRawData with is_merged=True for the latest batch).
      - All other zones:
            count all records regardless of merge status.
    """
    from django.db.models import Q
    from nanopore.models import TblisRawData, TblisUploadBatch

    ctrl_prefixes = [
        "DF_TZ_SS2_14", "DF_TZ_SS2_15", "DF_TZ_SS2_16",
        "DF_TZ_SS2_17", "DF_TZ_SS2_18", "DF_TZ_SS2_19",
    ]
    ctrl_q = Q()
    for prefix in ctrl_prefixes:
        ctrl_q |= Q(screening__pid__startswith=prefix)

    latest_batch = TblisUploadBatch.objects.first()
    
    if latest_batch:
        merged_labnos = TblisRawData.objects.filter(
            upload_batch=latest_batch, 
            is_merged=True
        ).values("labno")
    else:
        merged_labnos = []

    ctrl_merged_count = EdcsTblisZonal.objects.filter(
        ctrl_q,
        unique_lab_no__in=merged_labnos,
    ).count()

    other_zones_count = EdcsTblisZonal.objects.exclude(ctrl_q).count()

    return ctrl_merged_count + other_zones_count
