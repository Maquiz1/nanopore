from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("users.urls")),
    path('mentorship/', include('mentorship.urls')),  # if mentorship app is included separately
    path('locations/', include('locations.urls', namespace='locations')),
    path("admin/", admin.site.urls),
]
