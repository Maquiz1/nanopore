from django.urls import path
from .views import DashboardHomeView

app_name = "dashboard"

urlpatterns = [
    path("Dashboard", DashboardHomeView.as_view(), name="dashboard"),
]
