from django.urls import path
from .views import DashboardHomeView
# from .views import DashboardHomeView2
# from nanopore.views import ScreeningListView


app_name = "dashboard"

urlpatterns = [
    path("Dashboard", DashboardHomeView.as_view(), name="dashboard"),
    # path("Dashboard2", DashboardHomeView2, name="dashboard"),

    # path("", ScreeningListView.as_view(), name="dashboard"),
]
