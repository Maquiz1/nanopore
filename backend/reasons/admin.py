from django.contrib import admin
from .models import EnrolledReason

@admin.register(EnrolledReason)
class EnrolledReasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'reason')
    search_fields = ('reason',)
