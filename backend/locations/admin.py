from django.contrib import admin
from .models import Country, SiteLevel, SiteType, Zone, Region, District, Site

# Inline for Site inside District
class SiteInline(admin.TabularInline):
    model = Site
    extra = 1

# Inline for District inside Region
class DistrictInline(admin.TabularInline):
    model = District
    extra = 1
    inlines = [SiteInline]  # Django does not support nested inlines natively

# Inline for Region inside Zone
class RegionInline(admin.TabularInline):
    model = Region
    extra = 1
    inlines = [DistrictInline]  # Again, Django native admin does not support multiple levels of inlines

# Inline for Zone inside Country
class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 1
    inlines = [RegionInline]

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [ZoneInline]

@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone']

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'region']

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'district', 'pid_prefix', 'get_site_type', 'get_site_level']

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
