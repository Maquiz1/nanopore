from django.urls import path
from nanopore.views import CheckPIDView

urlpatterns = [
    path("check-pid/", CheckPIDView.as_view(), name="check-pid"),
]
