from django.contrib import admin
from .models import Profile, Prefix, Position

@admin.register(Prefix)
class PrefixAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'site', 'prefix', 'position', 'phone_number')
    search_fields = ('user__username', 'phone_number')
    list_filter = ('site', 'prefix', 'position')
