from django.urls import path
from nanopore.views import CheckPIDView, SystemControlsView

urlpatterns = [
    path("check-pid/", CheckPIDView.as_view(), name="check-pid"),
    path("system-controls/", SystemControlsView.as_view(), name="system-controls"),
]
