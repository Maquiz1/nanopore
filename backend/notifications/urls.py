from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("recipients/", views.EmailRecipientListView.as_view(), name="recipients"),
    path("recipients/add/", views.EmailRecipientCreateView.as_view(), name="recipient_add"),
    path("recipients/<int:pk>/edit/", views.EmailRecipientUpdateView.as_view(), name="recipient_edit"),
    path("recipients/<int:pk>/delete/", views.EmailRecipientDeleteView.as_view(), name="recipient_delete"),
    path("site-urls/", views.SiteConfigurationListView.as_view(), name="site_urls"),
    path("site-urls/add/", views.SiteConfigurationCreateView.as_view(), name="site_url_add"),
    path("site-urls/<int:pk>/edit/", views.SiteConfigurationUpdateView.as_view(), name="site_url_edit"),
    path("site-urls/<int:pk>/delete/", views.SiteConfigurationDeleteView.as_view(), name="site_url_delete"),
    path("logs/", views.EmailLogListView.as_view(), name="logs"),
]
