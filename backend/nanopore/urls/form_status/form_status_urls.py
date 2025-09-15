from django.urls import path
from nanopore.views import FormStatusListView, ScreeningListView

urlpatterns = [
    path("form-status/", FormStatusListView.as_view(), name="form-status-list"),
    path("screened/", FormStatusListView.as_view(), name="screened-list"),
    path("eligible/", FormStatusListView.as_view(), name="eligible-list"),
    path("enrolled/", FormStatusListView.as_view(), name="enrolled-list"),
    path("completed/", FormStatusListView.as_view(), name="completed-list"),
]
