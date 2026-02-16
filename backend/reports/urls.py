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
    
    list_all_models_view,
    ExportModelDataView,
    ExportAllModelsCombinedView,
    ExportModelRawDataView,

    AllOverviewQueriesDashboardView,
    MissingFormQueriesDashboardView,
    SpecificFormQueriesDashboardView,
    MissingFormDetailsQueriesView,
    
    # FormsDataQualityReportView,
    ScreeningDataQualityReportView,
    EnrollmentDataQualityReportView,
    ClinicDataQualityReportView,
    DiagnosisDataQualityReportView,
    RegimenDataQualityReportView,
    # ZonalDataQualityReportView,
    
    ZonalDataQualityView,
    EdcsTBLISDataQualityView,
    
    # DataQualityReportPDFView,
    
    NotificationsView,
    AlertsView,
    
    DreamFundQueriesPDFView,
    
    missing_forms_dashboard,
    missing_forms_trends,
    )

app_name = "reports"

urlpatterns = [
    # Dashboard & Summary
    path('reportsSummary', views.dashboard_report, name='index'),
    path("dashboardSummary", views.ReportDashboardView.as_view(), name="index"),
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
    path('list-models/', list_models_view, name='list_models'),
    
    # Export page (template with all models)
    path('list-all-models/', list_all_models_view, name='list_models_view'),

    # Single model export or filtered
    path('export-models/', ExportModelDataView.as_view(), name='export_data'),

    # Export all models combined into one CSV
    path('export-all-combined/', ExportAllModelsCombinedView.as_view(), name='export_all_combined'),

    # Direct raw export per model
    path('download/<str:model_name>/', ExportModelRawDataView.as_view(), name='download_model_data'),

    # New endpoints for labels and field names
    path('download/<str:model_name>/labels/', DownloadModelLabelsView.as_view(), name='download_model_labels'),
    path('download/<str:model_name>/fields/', DownloadModelFieldsView.as_view(), name='download_model_fields'),

    # Export all models into a single CSV
    # path('download/all-models/csv/', ExportAllModelsRawDataView.as_view(), name='download_raw_data_all_models'),

    # Legacy CSV downloads
    path('all/download/csv/', AllCsvDownloadView.as_view(), name='download-all-csv'),
    path('screenings/download/csv/', ScreeningCsvDownloadView.as_view(), name='download-screenings-csv'),
    path('enrollments/download/csv/', EnrollmentCsvDownloadView.as_view(), name='download-enrollments-csv'),

    path('data-quality/all-issues/', AllOverviewQueriesDashboardView.as_view(), name='all_queries_overview'),
    path("queries/", MissingFormQueriesDashboardView.as_view(), name="missing_form_queries"),
    path("specific-form-queries/", SpecificFormQueriesDashboardView.as_view(), name="specific_form_queries"),
    
    # path("missing-form-details-queries/", MissingFormDetailsQueriesView.as_view(), name="missing_form_details_queries"),
    path("missing-form-details-queries/<str:form_type>/", MissingFormDetailsQueriesView.as_view(), name="missing_form_details_queries"),
    
    # path('data-quality/', FormsDataQualityReportView.as_view(), name='forms_quality_report'),
    path('screening-quality/', ScreeningDataQualityReportView.as_view(), name='screening_quality_report'),
    path('enrollment-quality/', EnrollmentDataQualityReportView.as_view(), name='enrollment_quality_report'),
    path('clinic-quality/', ClinicDataQualityReportView.as_view(), name='clinic_quality_report'),
    path('diagnosis-quality/', DiagnosisDataQualityReportView.as_view(), name='diagnosis_quality_report'),
    path('regimen-quality/', RegimenDataQualityReportView.as_view(), name='regimen_quality_report'),
    # path('zonal-quality/', ZonalDataQualityReportView.as_view(), name='zonal_quality_report'),
    path('zonal-quality/', ZonalDataQualityView.as_view(), name='zonal_quality_report'),
    path('edcs-tblis-quality/', EdcsTBLISDataQualityView.as_view(), name='edcs_tblis_quality_report'),

    path('data-quality/pdf/', DreamFundQueriesPDFView.as_view(), name='data_quality_pdf'),
    path('data-quality/pdf/document/', DreamFundQueriesPDFView.as_view(), name='data_quality_pdf_document'),
    path('enrollment/data-quality/pdf/document/', DreamFundQueriesPDFView.as_view(), name='enrollment_data_quality_pdf'),

    path('notifications/', AllOverviewQueriesDashboardView.as_view(), name='notifications-list'),
    path('alerts/', AllOverviewQueriesDashboardView.as_view(), name='alerts-list'),
    
    path(
    "dq/missing-forms/",
    missing_forms_dashboard,
    name="missing_forms_dashboard"
    ),
    path(
    "dq/missing-forms-trends/",
    missing_forms_trends,
    name="missing_forms_trends"
    ),
]
