from django.urls import path
from nanopore.views import (
    EnrollmentListView,
    EnrollmentDetailView,
    EnrollmentDeleteView,
    EnrollmentFormView,
    EnrollmentCsvUploadView
)

urlpatterns = [
    path("", EnrollmentListView.as_view(), name="enrollment-list"),
    path("<int:pk>/", EnrollmentDetailView.as_view(), name="enrollment-detail"),
    path("enrollment/form/", EnrollmentFormView.as_view(), name="enrollment-create"),
    path("enrollment/form/<int:pk>/", EnrollmentFormView.as_view(), name="enrollment-update"),
    path("<int:pk>/delete/", EnrollmentDeleteView.as_view(), name="enrollment-delete"),
    
    path('upload/', EnrollmentCsvUploadView.as_view(), name="enrollment-upload-csv"),
]
