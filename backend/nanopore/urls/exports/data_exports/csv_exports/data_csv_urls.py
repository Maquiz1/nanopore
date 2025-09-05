from django.urls import path
from nanopore.views import ScreeningCsvDownloadView

urlpatterns = [
    path('screenings/download/', ScreeningCsvDownloadView.as_view(), name='download-screenings'),
    path('screenings/download/', ScreeningCsvDownloadView.as_view(), name='download-screenings-csv'),
]
