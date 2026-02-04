from django.contrib import admin
from .models import Country, SiteLevel, SiteType, Zone, Region, District, Site
from django.core.exceptions import ValidationError

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

class TargetValidationMixin:
    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(Country)
class CountryAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ['name','target','substudy2Target','substudy4Target']
    inlines = [ZoneInline]
    
    fieldsets = (
        ("Basic", {"fields": ("name", "is_active")}),
        ("Targets", {"fields": ("target", "substudy2Target", "substudy4Target")}),
    )
    
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)

@admin.register(Zone)
class ZoneAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'description','target','substudy2Target','substudy4Target')
    
    fieldsets = (
        ("Basic", {"fields": ("name", "country")}),
        ("Targets", {"fields": ("target", "substudy2Target", "substudy4Target")}),
    )
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)
        
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['name', 'zone','target','substudy2Target','substudy4Target']
    
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)
        
@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ['id','value','name', 'region','target','substudy2Target','substudy4Target']
    
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)
        
@admin.register(Site)
class SiteAdmin(TargetValidationMixin, admin.ModelAdmin):
    list_display = ['id','value','name', 'district', 'pid_prefix', 'get_site_type', 'get_site_level','target','substudy2Target','substudy4Target']

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

    
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)
        
@admin.register(SiteType)
class SiteTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)
        
@admin.register(SiteLevel)
class SiteLevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code']
    
    # def clean(self):
    #     errors = {}

    #     if not self.target:
    #         errors["target"] = "Overall enrollment target is required."

    #     if not self.substudy2Target:
    #         errors["substudy2Target"] = "Substudy 2 target is required."

    #     if not self.substudy4Target:
    #         errors["substudy4Target"] = "Substudy 4 target is required."

    #     if errors:
    #         raise ValidationError(errors)
    
