from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, TaskListCreateView, TaskRetrieveUpdateDeleteView, TaskListView, TaskCreateUpdateView, TaskDeleteView

app_name = 'task'

urlpatterns = [
    # Web URLs
    path('', TaskListView.as_view(), name='task_index'),
    path('add/', TaskCreateUpdateView.as_view(), name='task_add'),
    path('edit/<int:pk>/', TaskCreateUpdateView.as_view(), name='task_edit'),
    path('delete/<int:pk>/', TaskDeleteView.as_view(), name='task_delete'),

    # API URLs
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/tasks/', TaskListCreateView.as_view(), name='task_list_create'),
    path('api/tasks/<int:pk>/', TaskRetrieveUpdateDeleteView.as_view(), name='task_detail'),
]
