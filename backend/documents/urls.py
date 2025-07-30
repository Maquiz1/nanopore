from django.urls import path
from .views import (
    UserManualListView,
    UserManualCreateView,
    UserManualUpdateView,
    UserManualDetailView,
    UserManualDeleteView,
    UserManualDownloadView,
)

app_name = "documents"

urlpatterns = [
    path('', UserManualListView.as_view(), name='usermanual-list'),
    path('create/', UserManualCreateView.as_view(), name='usermanual-create'),
    path('<int:pk>/', UserManualDetailView.as_view(), name='usermanual-detail'),
    path('<int:pk>/update/', UserManualUpdateView.as_view(), name='usermanual-update'),
    path('<int:pk>/delete/', UserManualDeleteView.as_view(), name='usermanual-delete'),
    path('<int:pk>/download/', UserManualDownloadView.as_view(), name='usermanual-download'),
]
