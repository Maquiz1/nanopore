from django.urls import path
from .views import DashboardHomeView
from .views import UserManualListView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='dashboard'),
    path('', UserManualListView.as_view(), name='manual-list'),
]
