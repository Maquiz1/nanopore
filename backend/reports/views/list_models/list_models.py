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
            "count": EdcsTblisZonal.objects.count(),
            "description": "All Edcs/TBLIS records linked to Screening",
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
