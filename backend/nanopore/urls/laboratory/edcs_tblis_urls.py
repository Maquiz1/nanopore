# nanopore/urls/laboratory/zonal_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    EdcsTBLISLaboratoryListView,
    EdcsTBLISCsvUploadView,
    EdcsTblisFormView,
    TblisRawUploadView,
    DiscrepancyDownloadView,
    RevokeEdcsTblisTaskView,
    TaskStatusView,
    EdcsTblisDownloadCsvView,
    TriggerCsvExportView,
    ServeCsvExportView,
)

urlpatterns = [
    path("edcs-tblis-list/", EdcsTBLISLaboratoryListView.as_view(), name="edcs-tblis-laboratory-list"),
    path("edcs-tblis/form/<int:pk>/update", EdcsTblisFormView.as_view(), name="edcs-tblis-laboratory-update"),
    path("edcs-tblis/form/<int:pk>/view", EdcsTblisFormView.as_view(), name="edcs-tblis-laboratory-view"),
    path('upload-edcs-tblis/', EdcsTBLISCsvUploadView.as_view(), name="edcs-tblis-upload-csv"),
    path('upload-tblis-raw/', TblisRawUploadView.as_view(), name="tblis-raw-upload"),
    path('upload-tblis-raw/discrepancies/<str:discrepancy_type>/', DiscrepancyDownloadView.as_view(), name="tblis-raw-discrepancies"),
    path('edcs-tblis/revoke/<str:task_id>/', RevokeEdcsTblisTaskView.as_view(), name='task-revoke'),
    path("task-status/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
    path("edcs-tblis/download/", EdcsTblisDownloadCsvView.as_view(), name="edcs-tblis-download-csv"),
    path("edcs-tblis/export/trigger/", TriggerCsvExportView.as_view(), name="edcs-tblis-export-trigger"),
    path("edcs-tblis/export/serve/<str:filename>/", ServeCsvExportView.as_view(), name="edcs-tblis-export-serve"),
]
