from django.urls import path

from nanopore.views.history_view import RecordHistoryView
from nanopore.views import CheckPIDView, SystemControlsView, MasterDataListView

urlpatterns = [
    path("history/<str:form_key>/<int:pk>/", RecordHistoryView.as_view(), name="record-history"),
    path("check-pid/", CheckPIDView.as_view(), name="check-pid"),
    path("system-controls/", SystemControlsView.as_view(), name="system-controls"),
    path("master-data/", MasterDataListView.as_view(), name="master-data-list"),
]
