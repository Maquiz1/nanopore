from django.contrib import admin
from .models import (
    DataQualitySnapshot,
    ScreeningDQSnapshot,
    EnrollmentDQSnapshot,
    ClinicDQSnapshot,
    DiagnosisDQSnapshot,
)

# -------------------------------
# Base Snapshot Admin
# -------------------------------
@admin.register(DataQualitySnapshot)
class DataQualitySnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot_date", "created_at")
    list_filter = ("snapshot_date",)
    search_fields = ("snapshot_date",)


# -------------------------------
# Screening Snapshot Admin
# -------------------------------
@admin.register(ScreeningDQSnapshot)
class ScreeningDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_screenings_value", "total_issues")
    list_filter = ("snapshot",)  # Can't filter by zone/site if not fields
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name if obj.zone else "-"
    zone_name.short_description = "Zone"

    def site_name(self, obj):
        return obj.site.name if obj.site else "-"
    site_name.short_description = "Site"

    def total_screenings_value(self, obj):
        return obj.total_screenings
    total_screenings_value.short_description = "Total Screenings"


# -------------------------------
# Enrollment Snapshot Admin
# -------------------------------
@admin.register(EnrollmentDQSnapshot)
class EnrollmentDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_enrollments", "total_issues")
    list_filter = ("snapshot",)
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name if obj.zone else "-"
    zone_name.short_description = "Zone"

    def site_name(self, obj):
        return obj.site.name if obj.site else "-"
    site_name.short_description = "Site"

    def total_enrollments(self, obj):
        return obj.total_enrollments
    total_enrollments.short_description = "Total Enrollments"


# -------------------------------
# Clinic Snapshot Admin
# -------------------------------
@admin.register(ClinicDQSnapshot)
class ClinicDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_clinics", "total_issues")
    list_filter = ("snapshot",)
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name if obj.zone else "-"
    zone_name.short_description = "Zone"

    def site_name(self, obj):
        return obj.site.name if obj.site else "-"
    site_name.short_description = "Site"

    def total_clinics(self, obj):
        return obj.total_clinics
    total_clinics.short_description = "Total Clinics"


# -------------------------------
# Diagnosis Snapshot Admin
# -------------------------------
@admin.register(DiagnosisDQSnapshot)
class DiagnosisDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_diagnoses", "total_issues")
    list_filter = ("snapshot",)
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name if obj.zone else "-"
    zone_name.short_description = "Zone"

    def site_name(self, obj):
        return obj.site.name if obj.site else "-"
    site_name.short_description = "Site"

    def total_diagnoses(self, obj):
        return obj.total_diagnoses
    total_diagnoses.short_description = "Total Diagnoses"



# -------------------------------
# Regimen Snapshot Admin
# -------------------------------
from .models import RegimenDQSnapshot

@admin.register(RegimenDQSnapshot)
class RegimenDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_regimens", "total_issues")
    list_filter = ("snapshot",)
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name if hasattr(obj, "zone_name") else "-"
    zone_name.short_description = "Zone"

    def site_name(self, obj):
        return obj.site.name if hasattr(obj, "site_name") else "-"
    site_name.short_description = "Site"

    def total_regimens(self, obj):
        return obj.total_regimens
    total_regimens.short_description = "Total Regimens"


from .models import ZonalLaboratoryDQSnapshot

# -------------------------------
# Zonal Laboratory Snapshot Admin
# -------------------------------
@admin.register(ZonalLaboratoryDQSnapshot)
class ZonalLaboratoryDQSnapshotAdmin(admin.ModelAdmin):
    list_display = ("snapshot", "zone_name", "site_name", "total_records", "total_issues")
    list_filter = ("snapshot",)
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name or "-"
    zone_name.short_description = "Zone"

    def site_name(self, obj):
        return obj.site.name or "-"
    site_name.short_description = "Site"
    
    
from .models import MissingFormsDQSnapshot

@admin.register(MissingFormsDQSnapshot)
class MissingFormsDQSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "snapshot", "zone_name", "site_name",
        "missing_enrollment", "missing_clinic",
        "missing_diagnosis", "missing_regimen", "missing_zonal",
        "total_issues"
    )
    list_filter = ("snapshot",)
    search_fields = ("snapshot__snapshot_date",)

    def zone_name(self, obj):
        return obj.zone.name if obj.zone else "-"
    def site_name(self, obj):
        return obj.site.name if obj.site else "-"