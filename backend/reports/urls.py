from django.urls import path
from . import views
from .views import EnrollmentSummaryView,CompletedStudySummaryView

app_name = "reports"

urlpatterns = [
    path('', views.dashboard_report, name='index'),
    path("", views.ReportDashboardView.as_view(), name="index"),
    path("summary/", views.SummaryReportView.as_view(), name="summary"),
    path("forms/", views.FormsReportView.as_view(), name="forms"),
    path("enrollment-summary/", EnrollmentSummaryView.as_view(), name="enrollment-summary"),
    path("completed_study_summary/", CompletedStudySummaryView.as_view(), name="completed_study_summary"),

    # Export
    path("summary/export/<str:fmt>/", views.export_summary, name="export_summary"),
    path("forms/export/<str:fmt>/", views.export_forms, name="export_forms"),
]
