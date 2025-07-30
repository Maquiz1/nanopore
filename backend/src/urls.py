from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("", include("users.urls")),
    path('reports/', include('reports.urls')),  # if mentorship app is included separately
    path('mentorship/', include('mentorship.urls')),  # if mentorship app is included separately
    path('locations/', include('locations.urls', namespace='locations')),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
