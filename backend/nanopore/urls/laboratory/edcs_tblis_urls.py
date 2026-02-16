# nanopore/urls/laboratory/zonal_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    EdcsTBLISLaboratoryListView,
    # ZonalLaboratoryDetailView,
    # ZonalLaboratoryDeleteView,
    # ZonalLabFormView,
    EdcsTBLISCsvUploadView,
    EdcsTblisFormView,
    task_status
)

urlpatterns = [
    path("edcs-tblis-list/", EdcsTBLISLaboratoryListView.as_view(), name="edcs-tblis-laboratory-list"),
    # path("zonal-lab/<int:pk>/", ZonalLaboratoryDetailView.as_view(), name="zonal-laboratory-detail"),
    # path("zonal-lab/form/", ZonalLabFormView.as_view(), name="zonal-laboratory-create"),
    path("edcs-tblis/form/<int:pk>/update", EdcsTblisFormView.as_view(), name="edcs-tblis-laboratory-update"),
    path("edcs-tblis/form/<int:pk>/view", EdcsTblisFormView.as_view(), name="edcs-tblis-laboratory-view"),
    # path("zonal-lab/<int:pk>/delete/", ZonalLaboratoryDeleteView.as_view(), name="zonal-laboratory-delete"),
    
    path('upload-edcs-tblis/', EdcsTBLISCsvUploadView.as_view(), name="edcs-tblis-upload-csv"),
    
    path("task-status/<str:task_id>/", task_status, name="task-status"),

]
