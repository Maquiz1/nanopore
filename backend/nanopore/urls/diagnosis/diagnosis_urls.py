from nanopore.models import Diagnosis  # the View button opens the form read only
from django.urls import path
from nanopore.views import (
    DiagnosisListView,
    DiagnosisDetailView,
    DiagnosisFormView,
    DiagnosisDeleteView,
    DiagnosisCsvUploadView,
)

urlpatterns = [
    path("", DiagnosisListView.as_view(), name="diagnosis-list"),
    path("<int:pk>/", DiagnosisFormView.as_view(view_only=True, view_model=Diagnosis, edit_url_name="nanopore:diagnosis-update"), name="diagnosis-detail"),
    path("diagnosis/form/", DiagnosisFormView.as_view(), name="diagnosis-create"),  # create
    path("diagnosis/form/<int:pk>/", DiagnosisFormView.as_view(), name="diagnosis-update"),  # update
    path("diagnosis/<int:pk>/delete/", DiagnosisDeleteView.as_view(), name="diagnosis-delete"),
    
    path('upload/', DiagnosisCsvUploadView.as_view(), name="diagnosis-upload-csv"),
]
