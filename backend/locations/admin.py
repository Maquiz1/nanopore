from django.contrib import admin
from .models import Country, SiteLevel, SiteType, Zone, Region, District, Site


# =========================
# Inlines (single level only — Django limitation)
# =========================

class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 1


class RegionInline(admin.TabularInline):
    model = Region
    extra = 1


class DistrictInline(admin.TabularInline):
    model = District
    extra = 1


class SiteInline(admin.TabularInline):
    model = Site
    extra = 1


# =========================
# Validation mixin (ALLOW ZERO)
# =========================

class TargetValidationMixin:
    """
    Forces model validation but allows 0.
    """

    def save_model(self, request, obj, form, change):
        # full_clean validates MinValueValidator(0)
        obj.full_clean()
        super().save_model(request, obj, form, change)


# =========================
# Admin registrations
# =========================

@admin.register(Country)
class CountryAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ['name', 'target', 'substudy2Target', 'substudy4Target']
    inlines = [ZoneInline]

    fieldsets = (
        ("Basic", {"fields": ("name", "is_active")}),
        ("Targets", {
            "fields": ("target", "substudy2Target", "substudy4Target"),
            "description": "Targets may be zero (0)."
        }),
    )


@admin.register(Zone)
class ZoneAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'target', 'substudy2Target', 'substudy4Target')
    inlines = [RegionInline]

    fieldsets = (
        ("Basic", {"fields": ("name", "country")}),
        ("Targets", {"fields": ("target", "substudy2Target", "substudy4Target")}),
    )


@admin.register(Region)
class RegionAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ['name', 'zone', 'target', 'substudy2Target', 'substudy4Target']
    inlines = [DistrictInline]


@admin.register(District)
class DistrictAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ['id', 'value', 'name', 'region', 'target', 'substudy2Target', 'substudy4Target']
    inlines = [SiteInline]


@admin.register(Site)
class SiteAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = [
        'id', 'value', 'name', 'district', 'pid_prefix',
        'get_site_type', 'get_site_level',
        'target', 'substudy2Target', 'substudy4Target'
    ]

    fieldsets = (
        ("Basic", {"fields": ("name", "district")}),
        ("Targets", {"fields": ("target", "substudy2Target", "substudy4Target")}),
    )

    def get_site_type(self, obj):
        return obj.site_type.name if obj.site_type else "-"

    get_site_type.short_description = "Site Type"

    def get_site_level(self, obj):
        return obj.site_level.name if obj.site_level else "-"

    get_site_level.short_description = "Site Level"


@admin.register(SiteType)
class SiteTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']


@admin.register(SiteLevel)
class SiteLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
