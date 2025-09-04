from django.urls import path
from nanopore.views import (
    DiagnosisListView,
    DiagnosisDetailView,
    DiagnosisCreateView,
    DiagnosisUpdateView,
    DiagnosisDeleteView,
)

urlpatterns = [
    path("", DiagnosisListView.as_view(), name="diagnosis-list"),
    path("<int:pk>/", DiagnosisDetailView.as_view(), name="diagnosis-detail"),
    path("create/", DiagnosisCreateView.as_view(), name="diagnosis-create"),
    path("<int:pk>/update/", DiagnosisUpdateView.as_view(), name="diagnosis-update"),
    path("<int:pk>/delete/", DiagnosisDeleteView.as_view(), name="diagnosis-delete"),
]
