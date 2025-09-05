from django.urls import path
from nanopore.views.exports.data_exports.xlsx_exports.data_xlsx_views import ScreeningExcelDownloadView

urlpatterns = [
    path('screenings/download/', ScreeningExcelDownloadView.as_view(), name='download-screenings-excel'),
]
