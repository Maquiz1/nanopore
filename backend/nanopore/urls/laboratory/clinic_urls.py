from django.urls import path
from nanopore.views import (
    ClinicLaboratoryListView,
    ClinicLaboratoryDetailView,
    ClinicLaboratoryCreateView,
    ClinicLaboratoryUpdateView,
    ClinicLaboratoryDeleteView,
)

urlpatterns = [
    path("", ClinicLaboratoryListView.as_view(), name="clinic-laboratory-list"),
    path("<int:pk>/", ClinicLaboratoryDetailView.as_view(), name="clinic-laboratory-detail"),
    path("create/", ClinicLaboratoryCreateView.as_view(), name="clinic-laboratory-create"),
    path("<int:pk>/update/", ClinicLaboratoryUpdateView.as_view(), name="clinic-laboratory-update"),
    path("<int:pk>/delete/", ClinicLaboratoryDeleteView.as_view(), name="clinic-laboratory-delete"),
]
