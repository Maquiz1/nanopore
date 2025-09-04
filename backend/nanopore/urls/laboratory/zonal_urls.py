from django.urls import path
from nanopore.views import (
    ZonalLaboratoryListView,
    ZonalLaboratoryDetailView,
    ZonalLaboratoryCreateView,
    ZonalLaboratoryUpdateView,
    ZonalLaboratoryDeleteView,
)

urlpatterns = [
    path("", ZonalLaboratoryListView.as_view(), name="zonal-laboratory-list"),
    path("<int:pk>/", ZonalLaboratoryDetailView.as_view(), name="zonal-laboratory-detail"),
    path("create/", ZonalLaboratoryCreateView.as_view(), name="zonal-laboratory-create"),
    path("<int:pk>/update/", ZonalLaboratoryUpdateView.as_view(), name="zonal-laboratory-update"),
    path("<int:pk>/delete/", ZonalLaboratoryDeleteView.as_view(), name="zonal-laboratory-delete"),
]
