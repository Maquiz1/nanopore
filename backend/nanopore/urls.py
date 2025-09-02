from django.urls import path
from .views import (
    ScreeningListView,
    ScreeningDetailView,
    ScreeningCreateView,
    ScreeningUpdateView,
    ScreeningDeleteView,
    StatusListView,
)

app_name = "nanopore"

urlpatterns = [
    path("screenings/", ScreeningListView.as_view(), name="screening-list"),
    path("screenings/<int:pk>/", ScreeningDetailView.as_view(), name="screening-detail"),
    path("screenings/create/", ScreeningCreateView.as_view(), name="screening-create"),
    path("screenings/<int:pk>/update/", ScreeningUpdateView.as_view(), name="screening-update"),
    path("screenings/<int:pk>/delete/", ScreeningDeleteView.as_view(), name="screening-delete"),

    path("status/", StatusListView.as_view(), name="status-list"),
    path("status/completed/", ScreeningListView.as_view(), name="completed-list"),
    path("status/enrolled/", ScreeningListView.as_view(), name="enrolled-list"),
    path("status/eligible/", ScreeningListView.as_view(), name="eligible-list"),
]
