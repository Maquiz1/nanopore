from django.urls import path
from nanopore.views import StatusListView, ScreeningListView

urlpatterns = [
    path("", StatusListView.as_view(), name="status-list"),
    path("screened/", ScreeningListView.as_view(), name="screened-list"),
    path("eligible/", ScreeningListView.as_view(), name="eligible-list"),
    path("enrolled/", ScreeningListView.as_view(), name="enrolled-list"),
    path("completed/", ScreeningListView.as_view(), name="completed-list"),
]
