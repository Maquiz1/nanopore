from django.urls import path
from .views import HouseholdCreateView, HouseholdListView



app_name = 'household'
# URL patterns for the household app

urlpatterns = [
    path('create/', HouseholdCreateView.as_view(), name='create_household'),
    path('list/', HouseholdListView.as_view(), name='household-list'),
]
