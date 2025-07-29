from django.urls import include, path
from . import views

urlpatterns = [
    path('', include('dashboard.urls')),
    path('clinical/', include('clinical.urls', namespace='clinical')),
    # path("", include("locations.urls")),
    # path("", include("mentorship.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("sign_up/", views.sign_up, name="sign_up"),
]