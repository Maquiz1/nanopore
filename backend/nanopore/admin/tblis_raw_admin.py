from django.contrib import admin
from nanopore.models import TblisRawData, TblisUploadBatch


@admin.register(TblisUploadBatch)
class TblisUploadBatchAdmin(admin.ModelAdmin):
    list_display = ("source_file_name", "created_at", "uploaded_by")
    list_filter = ("created_at",)
    search_fields = ("source_file_name",)
    readonly_fields = ("created_at",)

@admin.register(TblisRawData)
class TblisRawDataAdmin(admin.ModelAdmin):
    list_display = ("labno", "upload_batch", "uploaded_at", "uploaded_by", "is_merged")
    list_filter = ("is_merged", "upload_batch", "uploaded_at")
    search_fields = ("labno",)
    readonly_fields = ("uploaded_at",)
