from django.urls import path
from . import views

from reports.views import (
    EnrollmentSummaryView,
    CompletedStudySummaryView,
    EligibilitySummaryView,
    SubstudyDetailView,
    SubstudyExportView,
    CompletedRecordsView,
    InProgressRecordsView,
    RecordsByZoneView,
    RecordsBySiteView,
    ExportRecordsView,
    
    # Existing CSV download views
    ScreeningCsvDownloadView,
    EnrollmentCsvDownloadView,
    AllCsvDownloadView,
    
    # Models export views
    list_models_view,
    ExportModelRawDataView,
    DownloadModelLabelsView,
    DownloadModelFieldsView,
    ExportAllModelsRawDataView,  # <-- New view
    
    
    DataQualityReportView,
    DataQualityReportPDFView,
    
    NotificationsView,
    AlertsView,
    )

app_name = "reports"

urlpatterns = [
    # Dashboard & Summary
    path('', views.dashboard_report, name='index'),
    path("", views.ReportDashboardView.as_view(), name="index"),
    path("summary/", views.SummaryReportView.as_view(), name="summary"),
    path("forms/", views.FormsReportView.as_view(), name="forms"),
    path("enrollment-summary/", EnrollmentSummaryView.as_view(), name="enrollment-summary"),
    path("completed_study_summary/", CompletedStudySummaryView.as_view(), name="completed_study_summary"),
    path("substudy/<str:substudy>/", SubstudyDetailView.as_view(), name="substudy_detail"),
    path("eligibility_summary/", EligibilitySummaryView.as_view(), name="eligibility_summary"),

    # Export endpoints
    path("summary/export/<str:fmt>/", views.export_summary, name="export_summary"),
    path("forms/export/<str:fmt>/", views.export_forms, name="export_forms"),
    path('substudy/export/<export_format>/', SubstudyExportView.as_view(), name='export_substudy'),
    path("records/export/<str:export_format>/", ExportRecordsView.as_view(), name='export_records'),

    # Records views
    path("records/completed/", CompletedRecordsView.as_view(), name="records_completed"),
    path("records/in-progress/", InProgressRecordsView.as_view(), name="records_in_progress"),
    path("zone/<int:zone_id>/<str:status>/", RecordsByZoneView.as_view(), name="records_by_zone_status"),
    path("site/<int:site_id>/<str:status>/", RecordsBySiteView.as_view(), name="records_by_site_status"),

    # Models listing & downloads
    path('list-all-models/', list_models_view, name='list_models'),
    path('download/<str:model_name>/', ExportModelRawDataView.as_view(), name='download_model_data'),

    # New endpoints for labels and field names
    path('download/<str:model_name>/labels/', DownloadModelLabelsView.as_view(), name='download_model_labels'),
    path('download/<str:model_name>/fields/', DownloadModelFieldsView.as_view(), name='download_model_fields'),

    # Export all models into a single CSV
    path('download/all-models/csv/', ExportAllModelsRawDataView.as_view(), name='download_raw_data_all_models'),

    # Legacy CSV downloads
    path('all/download/csv/', AllCsvDownloadView.as_view(), name='download-all-csv'),
    path('screenings/download/csv/', ScreeningCsvDownloadView.as_view(), name='download-screenings-csv'),
    path('enrollments/download/csv/', EnrollmentCsvDownloadView.as_view(), name='download-enrollments-csv'),
    
    
    path('data-quality/', DataQualityReportView.as_view(), name='data_quality_report'),
    
    path('data-quality/pdf/', DataQualityReportPDFView.as_view(), name='data_quality_pdf'),

    path('notifications/', DataQualityReportView.as_view(), name='notifications-list'),
    path('alerts/', DataQualityReportPDFView.as_view(), name='alerts-list'),


]
