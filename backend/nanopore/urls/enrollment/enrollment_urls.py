from nanopore.models import Enrollment  # the View button opens the form read only
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
    path("<int:pk>/", EnrollmentFormView.as_view(view_only=True, view_model=Enrollment, edit_url_name="nanopore:enrollment-update"), name="enrollment-detail"),
    path("enrollment/form/", EnrollmentFormView.as_view(), name="enrollment-create"),
    path("enrollment/form/<int:pk>/", EnrollmentFormView.as_view(), name="enrollment-update"),
    path("<int:pk>/delete/", EnrollmentDeleteView.as_view(), name="enrollment-delete"),
    
    path('upload/', EnrollmentCsvUploadView.as_view(), name="enrollment-upload-csv"),
]
