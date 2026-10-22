from django.urls import path
from nanopore.views import RecycleBinListView, RecycleBinDetailView, RecycleBinRestoreView

urlpatterns = [
    path("", RecycleBinListView.as_view(), name="recycle-bin"),
    path("<int:pk>/", RecycleBinDetailView.as_view(), name="recycle-bin-detail"),
    path("<int:pk>/restore/", RecycleBinRestoreView.as_view(), name="recycle-bin-restore"),
]
