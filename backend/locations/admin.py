from django.contrib import admin
from .models import Country, Region, District, Site

# Inline for Region inside Country
class RegionInline(admin.TabularInline):
    model = Region
    extra = 1

# Inline for District inside Region
class DistrictInline(admin.TabularInline):
    model = District
    extra = 1

# Inline for Site inside District
class SiteInline(admin.TabularInline):
    model = Site
    extra = 1

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [RegionInline]

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'country']
    inlines = [DistrictInline]

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['name', 'region']
    inlines = [SiteInline]

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ['name', 'district']
