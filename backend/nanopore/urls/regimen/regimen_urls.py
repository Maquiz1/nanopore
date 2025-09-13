# nanopore/urls.py
from django.urls import path
from nanopore.views import (
    RegimenChangesUpdateView,
    RegimenChangesDeleteView,
    RegimenChangesFormView
)

urlpatterns = [
    path("regimen/create/", RegimenChangesFormView.as_view(), name="regimen-save"),
    path("regimen/<int:pk>/edit/", RegimenChangesUpdateView.as_view(), name="regimen-change-edit"),
    path("regimen/<int:pk>/delete/", RegimenChangesDeleteView.as_view(), name="regimen-change-delete"),
]
