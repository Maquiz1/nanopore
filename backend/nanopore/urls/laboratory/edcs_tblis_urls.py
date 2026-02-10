# nanopore/urls/zonal_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    EdcsTBLISLaboratoryListView,
    # ZonalLaboratoryDetailView,
    # ZonalLaboratoryDeleteView,
    # ZonalLabFormView,
    EdcsTBLISCsvUploadView
)

urlpatterns = [
    path("edcs-tblis-list/", EdcsTBLISLaboratoryListView.as_view(), name="edcs-tblis-laboratory-list"),
    # path("zonal-lab/<int:pk>/", ZonalLaboratoryDetailView.as_view(), name="zonal-laboratory-detail"),
    # path("zonal-lab/form/", ZonalLabFormView.as_view(), name="zonal-laboratory-create"),
    # path("zonal-lab/form/<int:pk>/", ZonalLabFormView.as_view(), name="zonal-laboratory-update"),
    # path("zonal-lab/<int:pk>/delete/", ZonalLaboratoryDeleteView.as_view(), name="zonal-laboratory-delete"),
    
    path('upload-edcs-tblis/', EdcsTBLISCsvUploadView.as_view(), name="edcs-tblis-upload-csv"),
]
