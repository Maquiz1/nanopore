# nanopore/urls/clinic_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    ClinicLaboratoryListView,
    ClinicLaboratoryDetailView,
    ClinicLaboratoryDeleteView,
    ClinicLaboratoryFormView,
)

urlpatterns = [
    path("", ClinicLaboratoryListView.as_view(), name="clinic-laboratory-list"),
    path("clinic-laboratory/<int:pk>/", ClinicLaboratoryDetailView.as_view(), name="clinic-laboratory-detail"),
    path("clinic-laboratory/form/", ClinicLaboratoryFormView.as_view(), name="clinic-laboratory-create"),
    path("clinic-laboratory/form/<int:pk>/", ClinicLaboratoryFormView.as_view(), name="clinic-laboratory-update"),
    path("clinic-laboratory/<int:pk>/delete/", ClinicLaboratoryDeleteView.as_view(), name="clinic-laboratory-delete"),
]
