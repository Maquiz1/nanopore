from django.urls import path

from .views import (
    CheckPIDView,
    ClinicLaboratoryCreateView,
    ClinicLaboratoryDeleteView,
    ClinicLaboratoryDetailView,
    ClinicLaboratoryListView,
    ClinicLaboratoryUpdateView,
    DiagnosisCreateView,
    DiagnosisDeleteView,
    DiagnosisDetailView,
    DiagnosisListView,
    DiagnosisUpdateView,
    EnrollmentCreateView,
    EnrollmentDeleteView,
    EnrollmentDetailView,
    EnrollmentListView,
    EnrollmentUpdateView,
    ScreeningCreateView,
    ScreeningDeleteView,
    ScreeningDetailView,
    ScreeningListView,
    ScreeningUpdateView,
    StatusListView,
    ZonalLaboratoryCreateView,
    ZonalLaboratoryDeleteView,
    ZonalLaboratoryDetailView,
    ZonalLaboratoryListView,
    ZonalLaboratoryUpdateView,
)


from .views.laboratory import *


app_name = "nanopore"

urlpatterns = [
    # ----------------- Screening -----------------
    path("screenings/", ScreeningListView.as_view(), name="screening-list"),
    path("screenings/<int:pk>/", ScreeningDetailView.as_view(), name="screening-detail"),
    path("screenings/create/", ScreeningCreateView.as_view(), name="screening-create"),
    path("screenings/<int:pk>/update/", ScreeningUpdateView.as_view(), name="screening-update"),
    path("screenings/<int:pk>/delete/", ScreeningDeleteView.as_view(), name="screening-delete"),

    # ----------------- Enrollment -----------------
    path("enrollments/", EnrollmentListView.as_view(), name="enrollment-list"),
    path("enrollments/<int:pk>/", EnrollmentDetailView.as_view(), name="enrollment-detail"),
    path("enrollments/create/", EnrollmentCreateView.as_view(), name="enrollment-create"),
    path("enrollments/<int:pk>/update/", EnrollmentUpdateView.as_view(), name="enrollment-update"),
    path("enrollments/<int:pk>/delete/", EnrollmentDeleteView.as_view(), name="enrollment-delete"),

    # ----------------- Clinic Laboratory -----------------
    path("clinic-labs/", ClinicLaboratoryListView.as_view(), name="clinic-laboratory-list"),
    path("clinic-labs/<int:pk>/", ClinicLaboratoryDetailView.as_view(), name="clinic-laboratory-detail"),
    path("clinic-labs/create/", ClinicLaboratoryCreateView.as_view(), name="clinic-laboratory-create"),
    path("clinic-labs/<int:pk>/update/", ClinicLaboratoryUpdateView.as_view(), name="clinic-laboratory-update"),
    path("clinic-labs/<int:pk>/delete/", ClinicLaboratoryDeleteView.as_view(), name="clinic-laboratory-delete"),

    # ----------------- Diagnosis -----------------
    path("diagnoses/", DiagnosisListView.as_view(), name="diagnosis-list"),
    path("diagnoses/<int:pk>/", DiagnosisDetailView.as_view(), name="diagnosis-detail"),
    path("diagnoses/create/", DiagnosisCreateView.as_view(), name="diagnosis-create"),
    path("diagnoses/<int:pk>/update/", DiagnosisUpdateView.as_view(), name="diagnosis-update"),
    path("diagnoses/<int:pk>/delete/", DiagnosisDeleteView.as_view(), name="diagnosis-delete"),

    # ----------------- Zonal Laboratory -----------------
    path("zonal-labs/", ZonalLaboratoryListView.as_view(), name="zonal-laboratory-list"),
    path("zonal-labs/<int:pk>/", ZonalLaboratoryDetailView.as_view(), name="zonal-laboratory-detail"),
    path("zonal-labs/create/", ZonalLaboratoryCreateView.as_view(), name="zonal-laboratory-create"),
    path("zonal-labs/<int:pk>/update/", ZonalLaboratoryUpdateView.as_view(), name="zonal-laboratory-update"),
    path("zonal-labs/<int:pk>/delete/", ZonalLaboratoryDeleteView.as_view(), name="zonal-laboratory-delete"),

    # ----------------- Status -----------------
    path("status/", StatusListView.as_view(), name="status-list"),
    path("status/screened/", ScreeningListView.as_view(), name="screened-list"),
    path("status/eligible/", ScreeningListView.as_view(), name="eligible-list"),
    path("status/enrolled/", ScreeningListView.as_view(), name="enrolled-list"),
    path("status/completed/", ScreeningListView.as_view(), name="completed-list"),

    # ----------------- Utility -----------------
    path("check-pid/", CheckPIDView.as_view(), name="check_pid"),
]
