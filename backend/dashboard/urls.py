from django.urls import path
from dashboard.views import DashboardHomeView,GraphsHomeView

app_name = "dashboard"

urlpatterns = [
    path("Dashboard", DashboardHomeView.as_view(), name="dashboard"),
    path("Graphs", GraphsHomeView.as_view(), name="graphs"),
]
