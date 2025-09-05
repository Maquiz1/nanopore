from django.urls import path
from nanopore.views.exports.data_exports.csv_exports.screening_csv_views import ScreeningCsvDownloadView
from nanopore.views.exports.data_exports.csv_exports.enrollment_csv_views import EnrollmentCsvDownloadView
from nanopore.views.exports.data_exports.csv_exports.all_csv_views import AllCsvDownloadView

urlpatterns = [
    path('all/download/csv/', AllCsvDownloadView.as_view(), name='download-all-csv'),
    path('screenings/download/csv/', ScreeningCsvDownloadView.as_view(), name='download-screenings-csv'),
    path('enrollments/download/csv/', EnrollmentCsvDownloadView.as_view(), name='download-enrollments-csv'),
]
