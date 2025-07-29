from django.urls import path, include
from . import views
# from django.views.generic import TemplateView


app_name = 'dashboard'

urlpatterns = [
    # path('countries/', CountryListAPIView.as_view(), name='country-list'),
    # path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('', views.user_dashboard, name='dashboard'),
    # path('clinical/', include('clinical.urls', namespace='clinical')),
]
