# reports/urls/exports.py
from django.urls import path
from reports.views import ScreeningCsvExportView,ModelsListView,ModelCsvExportView,ModelCsvExportView,AllModelsSingleCsvExportView


app_name = "reports"

urlpatterns = [
    path('models/', ModelsListView.as_view(), name="models-list"),
    path("export/<str:app_label>/<str:model_name>/", ModelCsvExportView.as_view(), name="download-model-csv"),

    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='download-all-csv'),
    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='index'),
    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='summary'),
    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='forms'),
    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='enrollment-summary'),
    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='completed_study_summary'),
    path('screenings/csv/', ScreeningCsvExportView.as_view(), name='eligibility_summary'),
    
    path("models/", ModelsListView.as_view(), name="models-list"),
    path("export/<str:app_label>/<str:model_name>/", ModelCsvExportView.as_view(), name="download-model-csv"),
    path("export/all/", AllModelsSingleCsvExportView.as_view(), name="download-all-models"),

    # path('screenings/csv/', ScreeningCsvExportView.as_view(), name='completed_study_summary'),
    # path('screenings/csv/', ScreeningCsvExportView.as_view(), name='index'),
]
