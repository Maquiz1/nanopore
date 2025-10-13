from django.urls import path
from nanopore.views import (
    RegimenChangesFormView,
    RegimenChangesEditView,
    RegimenChangesDeleteView,
    RegimenChangesCsvUploadView,
)

# app_name = "nanopore"

urlpatterns = [
    path("save/", RegimenChangesFormView.as_view(), name="regimen-save"),
    path("<int:pk>/edit/", RegimenChangesEditView.as_view(), name="regimen-edit"),
    path("<int:pk>/delete/", RegimenChangesDeleteView.as_view(), name="regimen-delete"),
    path("upload/", RegimenChangesCsvUploadView.as_view(), name="regimen-changes-upload-csv"),
]






# # nanopore/urls.py
# from django.urls import path
# from nanopore.views import (
#     RegimenChangesUpdateView,
#     RegimenChangesDeleteView,
#     RegimenChangesFormView,
#     RegimenChangesCsvUploadView
# )

# urlpatterns = [
#     path("regimen/create/", RegimenChangesFormView.as_view(), name="regimen-save"),
#     path("regimen/<int:pk>/edit/", RegimenChangesUpdateView.as_view(), name="regimen-change-edit"),
#     path("regimen/<int:pk>/delete/", RegimenChangesDeleteView.as_view(), name="regimen-change-delete"),
#     path("regimen/upload/", RegimenChangesCsvUploadView.as_view(), name="regimen-changes-upload-csv"),
# ]


