from django.urls import path
from . import views
from .views import (
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
    )

app_name = "reports"

urlpatterns = [
    path('', views.dashboard_report, name='index'),
    path("", views.ReportDashboardView.as_view(), name="index"),
    path("summary/", views.SummaryReportView.as_view(), name="summary"),
    path("forms/", views.FormsReportView.as_view(), name="forms"),
    path("enrollment-summary/", EnrollmentSummaryView.as_view(), name="enrollment-summary"),
    path("completed_study_summary/", CompletedStudySummaryView.as_view(), name="completed_study_summary"),
    path("substudy/<str:substudy>/", SubstudyDetailView.as_view(), name="substudy_detail"),
    path("eligibility_summary/", EligibilitySummaryView.as_view(), name="eligibility_summary"),

    # Export
    path("summary/export/<str:fmt>/", views.export_summary, name="export_summary"),
    path("forms/export/<str:fmt>/", views.export_forms, name="export_forms"),
    # urls.py
    path('substudy/export/<export_format>/', SubstudyExportView.as_view(), name='export_substudy'),
    
    
    path("records/completed/", CompletedRecordsView.as_view(), name="records_completed"),
    path("records/in-progress/", InProgressRecordsView.as_view(), name="records_in_progress"),
    path("zone/<int:zone_id>/<str:status>/", RecordsByZoneView.as_view(), name="records_by_zone_status"),
    path("site/<int:site_id>/<str:status>/", RecordsBySiteView.as_view(), name="records_by_site_status"),
    
    path('records/export/<str:export_format>/', ExportRecordsView.as_view(), name='export_records'),

]
