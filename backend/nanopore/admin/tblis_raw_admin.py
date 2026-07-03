from django.contrib import admin
from nanopore.models import TblisRawData

@admin.register(TblisRawData)
class TblisRawDataAdmin(admin.ModelAdmin):
    list_display = ("labno", "uploaded_at", "uploaded_by", "is_merged")
    list_filter = ("is_merged", "uploaded_at")
    search_fields = ("labno",)
    readonly_fields = ("uploaded_at",)
