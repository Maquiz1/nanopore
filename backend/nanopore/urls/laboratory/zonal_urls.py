# nanopore/urls/zonal_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    ZonalLaboratoryListView,
    ZonalLaboratoryDetailView,
    ZonalLaboratoryDeleteView,
    ZonalLabFormView,
)

urlpatterns = [
    path("", ZonalLaboratoryListView.as_view(), name="zonal-laboratory-list"),
    path("zonal-lab/<int:pk>/", ZonalLaboratoryDetailView.as_view(), name="zonal-laboratory-detail"),
    path("zonal-lab/form/", ZonalLabFormView.as_view(), name="zonal-laboratory-create"),
    path("zonal-lab/form/<int:pk>/", ZonalLabFormView.as_view(), name="zonal-laboratory-update"),
    path("zonal-lab/<int:pk>/delete/", ZonalLaboratoryDeleteView.as_view(), name="zonal-laboratory-delete"),
]
