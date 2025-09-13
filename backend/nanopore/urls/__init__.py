from django.urls import path, include

app_name = "nanopore"

urlpatterns = [
    path("screenings/", include("nanopore.urls.screening.screening_urls")),
    path("enrollments/", include("nanopore.urls.enrollment.enrollment_urls")),
    path("clinic-labs/", include("nanopore.urls.laboratory.clinic_urls")),
    path("zonal-labs/", include("nanopore.urls.laboratory.zonal_urls")),
    path("diagnoses/", include("nanopore.urls.diagnosis.diagnosis_urls")),
    path("regimen/", include("nanopore.urls.regimen.regimen_urls")),
    path("form-status/", include("nanopore.urls.form_status.form_status_urls")),
    path("screenings/download/", include("nanopore.urls.exports.data_exports.csv_exports.data_csv_urls")),
    path("screenings/download/", include("nanopore.urls.exports.data_exports.xlsx_exports.data_xlsx_urls")),
    path("", include("nanopore.urls.utility.utility_urls")),  # check-pid
]
