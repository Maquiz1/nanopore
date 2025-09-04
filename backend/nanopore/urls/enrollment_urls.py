from django.urls import path
from nanopore.views import (
    EnrollmentListView,
    EnrollmentDetailView,
    EnrollmentCreateView,
    EnrollmentUpdateView,
    EnrollmentDeleteView,
)

urlpatterns = [
    path("", EnrollmentListView.as_view(), name="enrollment-list"),
    path("<int:pk>/", EnrollmentDetailView.as_view(), name="enrollment-detail"),
    path("create/", EnrollmentCreateView.as_view(), name="enrollment-create"),
    path("<int:pk>/update/", EnrollmentUpdateView.as_view(), name="enrollment-update"),
    path("<int:pk>/delete/", EnrollmentDeleteView.as_view(), name="enrollment-delete"),
]
