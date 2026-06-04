# nanopore/urls/laboratory/zonal_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    EdcsTBLISLaboratoryListView,
    EdcsTBLISCsvUploadView,
    EdcsTblisFormView,
    RevokeEdcsTblisTaskView,
    TaskStatusView,
    EdcsTblisDownloadCsvView,
)

urlpatterns = [
    path("edcs-tblis-list/", EdcsTBLISLaboratoryListView.as_view(), name="edcs-tblis-laboratory-list"),
    path("edcs-tblis/form/<int:pk>/update", EdcsTblisFormView.as_view(), name="edcs-tblis-laboratory-update"),
    path("edcs-tblis/form/<int:pk>/view", EdcsTblisFormView.as_view(), name="edcs-tblis-laboratory-view"),
    path('upload-edcs-tblis/', EdcsTBLISCsvUploadView.as_view(), name="edcs-tblis-upload-csv"),
    path('edcs-tblis/revoke/<str:task_id>/', RevokeEdcsTblisTaskView.as_view(), name='task-revoke'),
    path("task-status/<str:task_id>/", TaskStatusView.as_view(), name="task-status"),
    path("edcs-tblis/download/", EdcsTblisDownloadCsvView.as_view(), name="edcs-tblis-download-csv"),
]
