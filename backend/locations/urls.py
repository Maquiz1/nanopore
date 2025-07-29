from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('countries/', views.CountryListView.as_view(), name='country-list'),
    path('countries/<int:pk>/', views.CountryDetailView.as_view(), name='country-detail'),
    path('regions/<int:pk>/', views.RegionDetailView.as_view(), name='region-detail'),
    path('districts/<int:pk>/', views.DistrictDetailView.as_view(), name='district-detail'),
    path('sites/<int:pk>/', views.SiteDetailView.as_view(), name='site-detail'),
]
