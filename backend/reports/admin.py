from django.contrib import admin
from .models import DataQualitySnapshot
from .models import ScreeningDQSnapshot

@admin.register(DataQualitySnapshot)
class DataQualitySnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot_date", "created_at")
    ordering = ("-snapshot_date",)


@admin.register(ScreeningDQSnapshot)
class ScreeningDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_screenings", "total_issues")
    list_filter = ("snapshot", "zone_name", "site_name")
    ordering = ("-snapshot", "zone_name", "site_name")