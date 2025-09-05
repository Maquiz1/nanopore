from django.urls import path
from nanopore.views.exports.data_exports.xlsx_exports.screening_xlsx_views import ScreeningXlsxDownloadView
from nanopore.views.exports.data_exports.xlsx_exports.enrollment_xlsx_views import EnrollmentXlsxDownloadView
from nanopore.views.exports.data_exports.xlsx_exports.all_xlsx_views import AllXlsxDownloadView

urlpatterns = [
    path('all/download/xlsx/', AllXlsxDownloadView.as_view(), name='download-all-xlsx'),
    path('screenings/download/xlsx/', ScreeningXlsxDownloadView.as_view(), name='download-screenings-xlsx'),
    path('enrollments/download/xlsx/', EnrollmentXlsxDownloadView.as_view(), name='download-enrollments-xlsx'),
]
