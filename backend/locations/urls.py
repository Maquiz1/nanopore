from django.urls import path
from . import views

app_name = 'locations'

urlpatterns = [
    path('countries/', views.CountryListView.as_view(), name='country-list'),
    path('countries/<int:pk>/', views.CountryDetailView.as_view(), name='country-detail'),
    path('regions/<int:pk>/', views.RegionDetailView.as_view(), name='region-detail'),
    path('districts/<int:pk>/', views.DistrictDetailView.as_view(), name='district-detail'),
    path('sites/<int:pk>/', views.SiteDetailView.as_view(), name='site-detail'),
    path('sites/', views.AllSitesListView.as_view(), name='all-sites'),
    path('site/add/', views.SiteCreateView.as_view(), name='site-add'),
    path('site/edit/<int:pk>/', views.SiteUpdateView.as_view(), name='site-edit'),
]
