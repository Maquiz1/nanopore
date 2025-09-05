from django.urls import path
from nanopore.views import (
    ScreeningListView,
    ScreeningDetailView,
    ScreeningCreateView,
    ScreeningUpdateView,
    ScreeningDeleteView,
    ScreeningFormView,
    ScreeningCsvUploadView,
)

urlpatterns = [
    path("", ScreeningListView.as_view(), name="screening-list"),
    path("<int:pk>/", ScreeningDetailView.as_view(), name="screening-detail"),
    # path("create/", ScreeningCreateView.as_view(), name="screening-create"),
    # path("<int:pk>/update/", ScreeningUpdateView.as_view(), name="screening-update"),
    path('screening/create/', ScreeningFormView.as_view(), name='screening-create'),
    path('screening/<int:pk>/update/', ScreeningFormView.as_view(), name='screening-update'),
    path("<int:pk>/delete/", ScreeningDeleteView.as_view(), name="screening-delete"),
    
    path('upload/', ScreeningCsvUploadView.as_view(), name="screening-upload-csv"),

]
