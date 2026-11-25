# nanopore/urls/zonal_laboratory_urls.py
from django.urls import path
from nanopore.views import (
    ZonalLaboratoryListView,
    ZonalLaboratoryDeleteView,
    ZonalLabFormView,
    ZonalLabCsvUploadView
)
from nanopore.views.laboratory.zonal.ctrl_dar_form_views import CtrlDarLpaView, CtrlDarNanoporeView
from nanopore.views.laboratory.zonal.ctrl_isolate_form_view import CtrlIsolateFormView
from nanopore.views.laboratory.zonal.zonal_sections_view import ZonalLabHubView, ZonalLabSectionView

urlpatterns = [
    path("", ZonalLaboratoryListView.as_view(), name="zonal-laboratory-list"),
    path("zonal-lab/<int:pk>/", ZonalLabFormView.as_view(view_only=True), name="zonal-laboratory-detail"),
    path("zonal-lab/form/", ZonalLabFormView.as_view(), name="zonal-laboratory-create"),
    path("zonal-lab/form/<int:pk>/", ZonalLabFormView.as_view(), name="zonal-laboratory-update"),
    path("zonal-lab/<int:pk>/sections/", ZonalLabHubView.as_view(), name="zonal-lab-hub"),
    path("zonal-lab/sections/<str:section>/", ZonalLabSectionView.as_view(), name="zonal-lab-section-new"),
    path("zonal-lab/<int:pk>/sections/<str:section>/", ZonalLabSectionView.as_view(), name="zonal-lab-section"),
    path("zonal-lab/ctrl/<int:pk>/", CtrlIsolateFormView.as_view(), name="ctrl-isolate-update"),
    path("zonal-lab/ctrl-dar/nanopore/<int:pk>/", CtrlDarNanoporeView.as_view(), name="ctrl-dar-nanopore"),
    path("zonal-lab/ctrl-dar/lpa/<int:pk>/", CtrlDarLpaView.as_view(), name="ctrl-dar-lpa"),
    path("zonal-lab/<int:pk>/delete/", ZonalLaboratoryDeleteView.as_view(), name="zonal-laboratory-delete"),
    
    path('upload/', ZonalLabCsvUploadView.as_view(), name="zonal-upload-csv"),
]
