from django.urls import path, include

app_name = "nanopore"

urlpatterns = [
    path("screenings/", include("nanopore.urls.screening_urls")),
    path("enrollments/", include("nanopore.urls.enrollment_urls")),
    path("clinic-labs/", include("nanopore.urls.laboratory.clinic_urls")),
    path("zonal-labs/", include("nanopore.urls.laboratory.zonal_urls")),
    path("diagnoses/", include("nanopore.urls.diagnosis_urls")),
    path("form-status/", include("nanopore.urls.form_status_urls")),
    path("", include("nanopore.urls.utility_urls")),  # check-pid
]
