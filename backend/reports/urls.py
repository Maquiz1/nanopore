from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path('', views.dashboard_report, name='index'),
    path("", views.ReportDashboardView.as_view(), name="index"),
    path("summary/", views.SummaryReportView.as_view(), name="summary"),
    path("forms/", views.FormsReportView.as_view(), name="forms"),
    
    # Export
    path("summary/export/<str:fmt>/", views.export_summary, name="export_summary"),
    path("forms/export/<str:fmt>/", views.export_forms, name="export_forms"),
]
