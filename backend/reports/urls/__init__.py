# reports/urls.py
from django.urls import path, include

urlpatterns = [
    # path("", ModelsListView.as_view(), name="models-list"),
    path('', include('reports.urls.exports')),  # Export URLs
    # path('', include('reports.urls.records')),  # If you have record/list URLs
]
