from django.urls import path
from .views import DashboardHomeView
# from nanopore.views import ScreeningListView


app_name = "dashboard"

urlpatterns = [
    path("", DashboardHomeView.as_view(), name="dashboard"),
    # path("", ScreeningListView.as_view(), name="dashboard"),
]
