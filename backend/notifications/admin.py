from django.contrib import admin

from .models import EmailLog, EmailRecipient, SiteConfiguration


@admin.register(EmailRecipient)
class EmailRecipientAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "type", "is_active")
    list_filter = ("type", "is_active")


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "site_url", "from_email", "is_active")


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "recipient", "subject", "task_type", "status")
    list_filter = ("status", "task_type")
    search_fields = ("recipient", "subject")
