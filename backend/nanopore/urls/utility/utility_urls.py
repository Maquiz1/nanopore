from django.urls import path
from nanopore.views import CheckPIDView, SystemControlsView, MasterDataListView

urlpatterns = [
    path("check-pid/", CheckPIDView.as_view(), name="check-pid"),
    path("system-controls/", SystemControlsView.as_view(), name="system-controls"),
    path("master-data/", MasterDataListView.as_view(), name="master-data-list"),
]
