from django.urls import path
from . import views

app_name = 'clinical'

urlpatterns = [
    path('diseases/', views.DiseaseListView.as_view(), name='disease-list'),
    path('diseases/<int:pk>/', views.DiseaseDetailView.as_view(), name='disease-detail'),
    path('competences/<int:pk>/', views.CompetenceDetailView.as_view(), name='competence-detail'),
]
