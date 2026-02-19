from django.urls import path
from dashboard.views import DashboardHomeView,GraphsHomeView,SiteTargetsView

app_name = "dashboard"

urlpatterns = [
    path("Dashboard", DashboardHomeView.as_view(), name="dashboard"),
    path("Graphs", GraphsHomeView.as_view(), name="graphs"),
    path("site-targets/", SiteTargetsView.as_view(), name="site-targets"),    
]
