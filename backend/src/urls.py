from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib import admin

admin.site.site_header = "Digital Mentorship LogBook Admin"
admin.site.site_title = "Mentorship Admin Portal"
admin.site.index_title = "Welcome to the LogBook Admin Panel"

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')  # your dashboard home url name
    else:
        return redirect('users:login')  # your login url name

urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    path('household/', include('household.urls')),
    path('manuals/', include('documents.urls', namespace='documents')),
    path("clinical/", include("clinical.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("users/", include("users.urls")),
    path('reports/', include('reports.urls')),  # if mentorship app is included separately
    path('mentorship/', include('mentorship.urls')),  # if mentorship app is included separately
    path('locations/', include('locations.urls', namespace='locations')),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
