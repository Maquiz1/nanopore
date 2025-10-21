from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.contrib import admin

# admin.site.site_header = "Dream Fund - Nanopore Database Admin"
# admin.site.site_title = "Dream Fund - Nanopore Database Admin Portal"
# admin.site.index_title = "Welcome to the Dream Fund - Nanopore Database Admin Panel"

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('task:task_index')  # your dashboard home url name
    else:
        return redirect('users:login')  # your login url name

urlpatterns = [
    path('', root_redirect, name='root_redirect'),
    # path('options/', include('options.urls')),
    path('task/', include('task.urls')),
    path('nanopore/', include('nanopore.urls')),
    path('household/', include('household.urls')),
    path('manuals/', include('documents.urls', namespace='documents')),
    path("clinical/", include("clinical.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("users/", include("users.urls")),
    path('reports/', include('reports.urls')),  # if mentorship app is included separately
    # path('mentorship/', include('mentorship.urls')),  # if mentorship app is included separately
    path('locations/', include('locations.urls', namespace='locations')),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
