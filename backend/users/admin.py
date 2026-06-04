from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Prefix, Position


# -------------------------
# Basic models
# -------------------------

@admin.register(Prefix)
class PrefixAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "get_sites", "prefix", "position", "phone_number")
    search_fields = ("user__username", "phone_number")
    list_filter = ("sites", "prefix", "position")

    def get_sites(self, obj):
        return ", ".join([s.name for s in obj.sites.all()])
    get_sites.short_description = "Sites"


# -------------------------
# Inline and User Admin
# -------------------------

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

    list_display = (
        "username",
        "first_name",
        "last_name",
        "email",
        "get_zone",
        "get_sites",
        "get_position",
        "get_phone_number",
        "is_active",
        "is_staff",
    )

    list_select_related = (
        "profile__position",
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("profile__sites__district__region__zone")

    search_fields = (
        "username",
        "first_name",
        "last_name",
        "email",
        "profile__phone_number",
    )
    list_filter = (
        "is_staff",
        "is_active",
        "profile__sites__district__region__zone",
        "profile__position",
    )

    # -------------------------
    # Custom display functions
    # -------------------------

    def get_sites(self, obj):
        if hasattr(obj, "profile") and obj.profile:
            return ", ".join([s.name for s in obj.profile.sites.all()])
        return "-"
    get_sites.short_description = "Sites"

    def get_zone(self, obj):
        if hasattr(obj, "profile") and obj.profile:
            zones = set()
            for site in obj.profile.sites.all():
                try:
                    zones.add(site.district.region.zone.name)
                except AttributeError:
                    pass
            return ", ".join(zones) if zones else "-"
        return "-"
    get_zone.short_description = "Zone"

    def get_position(self, obj):
        return obj.profile.position.name if hasattr(obj, "profile") and obj.profile.position else "-"
    get_position.short_description = "Position"

    def get_phone_number(self, obj):
        return obj.profile.phone_number if hasattr(obj, "profile") else "-"
    get_phone_number.short_description = "Phone Number"


# Unregister and re-register User
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
