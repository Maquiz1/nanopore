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


# @staff_member_required
def list_models_view(request):
    models_list = [
        {
            "name": "Screening",
            "description": "All Screening records",
            "download_url": reverse("reports:download_model_data", args=["Screening"]),
            "labels_url": reverse("reports:download_model_labels", args=["Screening"]),
            "fields_url": reverse("reports:download_model_fields", args=["Screening"]),
        },
        {
            "name": "Enrollment",
            "description": "All Enrollment records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["Enrollment"]),
            "labels_url": reverse("reports:download_model_labels", args=["Enrollment"]),
            "fields_url": reverse("reports:download_model_fields", args=["Enrollment"]),
        },
        {
            "name": "ClinicLaboratory",
            "description": "All ClinicLaboratory records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["ClinicLaboratory"]),
            "labels_url": reverse("reports:download_model_labels", args=["ClinicLaboratory"]),
            "fields_url": reverse("reports:download_model_fields", args=["ClinicLaboratory"]),
        },
        {
            "name": "Diagnosis",
            "description": "All Diagnosis records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["Diagnosis"]),
            "labels_url": reverse("reports:download_model_labels", args=["Diagnosis"]),
            "fields_url": reverse("reports:download_model_fields", args=["Diagnosis"]),
        },
        {
            "name": "ZonalLaboratory",
            "description": "All ZonalLaboratory records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["ZonalLaboratory"]),
            "labels_url": reverse("reports:download_model_labels", args=["ZonalLaboratory"]),
            "fields_url": reverse("reports:download_model_fields", args=["ZonalLaboratory"]),
        },
        {
            "name": "RegimenChanges",
            "description": "All RegimenChanges records linked to Screening",
            "download_url": reverse("reports:download_model_data", args=["RegimenChanges"]),
            "labels_url": reverse("reports:download_model_labels", args=["RegimenChanges"]),
            "fields_url": reverse("reports:download_model_fields", args=["RegimenChanges"]),
        },
    ]
    return render(
        request, "reports/data_export/list_models.html", {"models_list": models_list}
    )
