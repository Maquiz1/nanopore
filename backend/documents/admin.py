from django.contrib import admin
from .models import UserManual

@admin.register(UserManual)
class UserManualAdmin(admin.ModelAdmin):
    list_display = ('title', 'uploaded_at')
